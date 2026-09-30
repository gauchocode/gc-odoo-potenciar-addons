from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    purchase_invoice_import_total_tolerance = fields.Float(
        string='Tolerancia de totales',
        config_parameter='gc_odoo_purchase_invoice_import_api.total_tolerance',
        help=(
            'Diferencia máxima aceptada, en la moneda del comprobante, entre los montos '
            'informados por el proveedor y los propios (suma de líneas, IVA, total y total '
            'de la factura ya creada en Odoo) antes de aplicar la política de '
            "'validation.action_if_exceeded' del payload (observación o rechazo)."
        ),
    )
