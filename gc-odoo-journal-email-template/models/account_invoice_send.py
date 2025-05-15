# models/account_invoice_send.py
from odoo import models, api, _
from odoo.exceptions import UserError

class AccountInvoiceSend(models.TransientModel):
    _inherit = 'account.invoice.send'

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        res_ids = self._context.get('active_ids')
        invoices = self.env['account.move'].browse(res_ids).filtered(lambda move: move.is_invoice(include_receipts=True))

        if not invoices:
            raise UserError(_("You can only send invoices."))

        journal_ids = invoices.mapped('journal_id')
        if len(journal_ids) == 1 and journal_ids.invoice_mail_template_id:
            res['template_id'] = journal_ids.invoice_mail_template_id.id

        composer = self.env['mail.compose.message'].create({
            'composition_mode': 'comment' if len(res_ids) == 1 else 'mass_mail',
        })

        res.update({
            'invoice_ids': res_ids,
            'composer_id': composer.id,
        })
        return res
