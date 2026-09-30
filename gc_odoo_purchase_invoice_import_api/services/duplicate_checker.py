class DuplicateCheckResult:
    def __init__(self, duplicate_move=None):
        self.duplicate_move = duplicate_move

    @property
    def is_duplicate(self):
        return bool(self.duplicate_move)


class DuplicateChecker:
    """Regla funcional de duplicado vigente: contacto + punto de venta + número.

    Implementada sobre campos estándar de l10n_latam_invoice_document/l10n_ar
    (commercial_partner_id + move_type + l10n_latam_document_type_id +
    l10n_latam_document_number), no sobre `source.idempotency_key`/
    `source.invoice_id` (UUID) del proveedor, que se guardan aparte en el
    log solo para trazabilidad/idempotencia.
    """

    def __init__(self, env):
        self.env = env

    def find_duplicate(self, partner, move_type, document_type, document_number):
        if not partner or not document_type or not document_number:
            return DuplicateCheckResult()

        # l10n_latam_document_number es un Char compute SIN store=True en este
        # Odoo 16 (ver l10n_latam_invoice_document/models/account_move.py).
        # Buscarlo por domain no lanza excepción: Odoo lo detecta, loguea
        # "Non-stored field ... cannot be searched" y lo reemplaza por un
        # dominio vacío (equivalente a True), es decir CUALQUIER factura del
        # mismo partner+move_type+document_type pasaría como "duplicado" sin
        # mirar el número. Por eso se trae el universo candidato por los
        # campos sí buscables y se filtra el número en memoria (leer un
        # compute sí funciona, solo falla al usarlo en un domain de search).
        candidates = self.env['account.move'].sudo().search([
            ('commercial_partner_id', '=', partner.commercial_partner_id.id),
            ('move_type', '=', move_type),
            ('l10n_latam_document_type_id', '=', document_type.id),
            ('state', '!=', 'cancel'),
        ])
        duplicate = candidates.filtered(
            lambda move: move.l10n_latam_document_number == document_number
        )[:1]
        return DuplicateCheckResult(duplicate_move=duplicate or None)
