from odoo import models, fields

class AccountMove(models.Model):
    _inherit = 'account.move'

    l10n_ar_afip_service_start = fields.Date(default=fields.Date.context_today)
    l10n_ar_afip_service_end = fields.Date(default=fields.Date.context_today)