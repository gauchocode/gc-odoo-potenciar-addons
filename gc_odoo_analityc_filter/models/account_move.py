from odoo import models, fields, api, _

class AccountMove(models.Model):
    _inherit = "account.move"

    analytic_account_ids = fields.Many2many(
        "account.analytic.account",
        "account_move_analytic_account_rel",
        "move_id",
        "tag_id",
        string="Analytic Tags",
        store=True,
        readonly=True,
        copy=False,
        compute="_compute_analytic_tag_ids",
    )

    @api.depends('invoice_line_ids.analytic_account_ids')
    def _compute_analytic_tag_ids(self):
        for rec in self:
            rec.analytic_account_ids = rec.invoice_line_ids.mapped('analytic_account_ids')

    @api.onchange("invoice_line_ids")
    def _onchange_invoice_line_ids_analytic_filter(self):
        for rec in self:
            rec._compute_analytic_tag_ids()