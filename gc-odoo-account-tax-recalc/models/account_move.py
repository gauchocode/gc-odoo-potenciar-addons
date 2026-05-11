from odoo import api, fields, models
import json, logging

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'

    automatic_tax_recalculation = fields.Boolean(
        string="Recalcular autom. de impuestos",
        help="Activado: Recalcula automáticamente como el comportamiento nativo.\n"
             "Desactivado: Se pueden modificar los valores manualmente. Es indispensable guardar el registro antes de salir."
    )

    
    tax_totals_snapshot = fields.Text(
        string="Snapshot JSON de Tax Totals",
        copy=False,
        help="JSON del último tax_totals calculado o editado.",
    )


    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        # Valor por defecto general: True
        res.setdefault('automatic_tax_recalculation', True)

        # Si el tipo es factura de proveedor (in_invoice), poner False
        if res.get('move_type') == 'in_invoice':
            res['automatic_tax_recalculation'] = False

        return res
        
    @api.depends(
        'invoice_line_ids.product_id',
        'invoice_line_ids.quantity',
        'invoice_line_ids.price_unit',
        'line_ids.tax_line_id',
        'invoice_cash_rounding_id',
        'automatic_tax_recalculation',
    )
    def _compute_tax_totals(self):
        for move in self:
            # 1) Siempre corremos el compute original
            super(AccountMove, move)._compute_tax_totals()
            totals = move.tax_totals or {}

            # 2) Si el usuario tiene OFF, aplicamos overrides del snapshot
            if not move.automatic_tax_recalculation and move.tax_totals_snapshot:
                try:
                    snap = json.loads(move.tax_totals_snapshot)
                except Exception:
                    snap = {}
                old_map = {
                    og['group_key']: {
                        'tax_group_amount': og['tax_group_amount'],
                        'formatted_tax_group_amount': og['formatted_tax_group_amount'],
                    }
                    for grp_list in snap.get('groups_by_subtotal', {}).values()
                    for og in grp_list
                }
                # Inyectar solo montos manuales
                for grp_list in totals.get('groups_by_subtotal', {}).values():
                    for ng in grp_list:
                        key = ng.get('group_key')
                        if key in old_map:
                            ng['tax_group_amount']          = old_map[key]['tax_group_amount']
                            ng['formatted_tax_group_amount']= old_map[key]['formatted_tax_group_amount']

                move.tax_totals = totals

            # 3) Si el usuario tiene ON, guardamos el snapshot actualizado
            if move.automatic_tax_recalculation and move.tax_totals:
                try:
                    move.tax_totals_snapshot = json.dumps(move.tax_totals)
                except Exception:
                    _logger.exception("Error serializando tax_totals para snapshot")

    def _inverse_tax_totals(self):
        # Ejecutamos el inverse original para propagar cambios a líneas
        super(AccountMove, self)._inverse_tax_totals()
        # Ahora, tras aplicar el inverse, si el usuario editó tax_totals desde el widget,
        # actualizamos el snapshot con ese nuevo valor
        for move in self:
            # Sólo si usamos snapshot (o siempre, para simplificar)
            if move.tax_totals:
                try:
                    move.tax_totals_snapshot = json.dumps(move.tax_totals)
                except Exception as e:
                    _logger.error("Error updating snapshot in inverse: %s", e)
