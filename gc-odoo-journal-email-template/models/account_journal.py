from odoo import models, fields

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    invoice_mail_template_id = fields.Many2one(
        'mail.template',
        string="Default Email Template for Invoices",
        domain=[('model', '=', 'account.move')],
        help="This template will be used by default when sending invoices for this journal."
    )
