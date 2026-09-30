from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    gc_import_product_code = fields.Char(
        string='Código de producto (Import API)',
        readonly=True,
        copy=False,
        help=(
            "'product_code' de la línea del payload de importación, para trazabilidad "
            "aunque el nombre de la línea (que también lo incluye como prefijo) cambie."
        ),
    )
