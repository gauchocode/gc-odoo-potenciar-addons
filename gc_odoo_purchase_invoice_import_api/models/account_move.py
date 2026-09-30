from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    gc_import_source_invoice_id = fields.Char(
        string='UUID Factura origen (Import API)',
        readonly=True,
        copy=False,
        help=(
            "source.invoice_id del payload de importación (Radiant / Looking for Trouble). "
            "Trazabilidad hacia el documento original del proveedor externo."
        ),
    )
    gc_import_idempotency_key = fields.Char(
        string='Idempotency Key (Import API)',
        readonly=True,
        copy=False,
        help='source.idempotency_key del payload de importación, usado para detectar reintentos.',
    )
