# -*- coding: utf-8 -*-

from odoo import models, fields, api

import logging
_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    l10n_ar_bna_rate_type = fields.Selection(related='company_id.l10n_ar_bna_rate_type',
                                             required=True,
                                             readonly=False)
    l10n_ar_bna_currency_value = fields.Selection(related='company_id.l10n_ar_bna_currency_value',
                                                  required=True,
                                                  readonly=False)
