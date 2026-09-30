from .payload_validator import PayloadValidator


class PartnerResolutionResult:
    def __init__(self, partner=None, error=None):
        self.partner = partner
        self.error = error


class PartnerResolver:
    """Resuelve o crea el res.partner (contacto) para el contrato v0.1.

    Camino normal: el payload trae `partner.odoo.partner_id` (confiado tal
    cual, ver DECISIONES.md), así que este servicio no interviene.

    Este servicio se usa solo cuando `partner.odoo.partner_id` está vacío y
    `partner.odoo.policy_if_missing == 'create'`:
    1. Busca por CUIT normalizado entre TODOS los contactos con `vat`
       informado, sin filtrar por `supplier_rank` (un contacto que hoy solo
       es cliente sigue siendo válido para recibir una factura de compra;
       bug real encontrado en el prototipo anterior al filtrar por
       supplier_rank > 0).
    2. Si no hay match, crea un res.partner nuevo a partir del bloque
       `partner` del payload.

    Nota de performance: se compara el vat normalizado en Python porque el
    valor guardado en Odoo puede tener guiones/espacios. Aceptable para el
    volumen actual de contactos; si el padrón crece mucho, conviene migrar
    a una columna computada/normalizada indexada en BD.
    """

    def __init__(self, env):
        self.env = env

    def resolve(self, cuit_normalizado):
        if not cuit_normalizado:
            return PartnerResolutionResult(error="CUIT vacío, no se puede resolver el proveedor.")

        candidates = self.env['res.partner'].sudo().search([('vat', '!=', False)])
        for partner in candidates:
            if PayloadValidator.normalize_cuit(partner.vat) == cuit_normalizado:
                return PartnerResolutionResult(partner=partner)

        return PartnerResolutionResult(
            error="Proveedor no encontrado para CUIT %s." % cuit_normalizado
        )

    def create_from_payload(self, partner_block):
        """Crea un res.partner nuevo desde el bloque `partner` del payload.

        Solo se llama cuando `policy_if_missing == 'create'` y no hubo match
        por CUIT. Campos verificados contra el código real de Odoo 16 de
        este entorno (l10n_ar/models/res_partner.py, l10n_latam_base):
        `l10n_latam_identification_type_id` (res.partner, vía l10n_latam_base)
        y `l10n_ar_afip_responsibility_type_id` (res.partner, vía l10n_ar).
        """
        partner_odoo = partner_block.get('odoo') if isinstance(partner_block.get('odoo'), dict) else {}

        vals = {
            'name': partner_block.get('name') or partner_block.get('cuit'),
            'vat': partner_block.get('cuit'),
            'l10n_latam_identification_type_id': self.env.ref('l10n_ar.it_cuit').id,
            'street': partner_block.get('address'),
            'city': partner_block.get('city'),
            'zip': partner_block.get('postal_code'),
            'country_id': self.env.ref('base.ar').id,
            'is_company': True,
            'supplier_rank': 1,
        }

        state_id = partner_odoo.get('state_id')
        if state_id:
            state = self.env['res.country.state'].sudo().browse(int(state_id))
            if state.exists():
                vals['state_id'] = state.id

        resp_code = partner_odoo.get('afip_responsibility_code')
        if resp_code:
            resp_type = self.env['l10n_ar.afip.responsibility.type'].sudo().search(
                [('code', '=', str(resp_code))], limit=1,
            )
            if resp_type:
                vals['l10n_ar_afip_responsibility_type_id'] = resp_type.id

        return self.env['res.partner'].sudo().create(vals)
