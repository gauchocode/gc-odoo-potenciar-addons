# -*- coding: utf-8 -*-

from odoo import models, fields, api

import logging
_logger = logging.getLogger(__name__)


class AccountBNACurrencies(models.Model):
    _name = 'account.bna.currencies'
    _description = 'Account BNA Currencies'
    _order = 'name'

    name = fields.Char('BNA Currency', required=True)
    currency_id = fields.Many2one('res.currency', 'Odoo Currency', required=True)
    bna_units = fields.Integer('Units listed in BNA', default=1, required=True)
    property_read_rate = fields.Boolean('Read Rate?', company_dependent=True, default=True)
