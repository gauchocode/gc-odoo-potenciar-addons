# -*- coding: utf-8 -*-

from odoo import fields, models

from .bna_rate_providers import PROVIDER_SELECTION


class RateProviderCurrency(models.Model):
    _name = "l10n_ar.rate.provider.currency"
    _description = "Moneda disponible en proveedor de cotización"
    _order = "provider, name"

    name = fields.Char(string="Nombre", required=True)
    code = fields.Char(string="Código del proveedor", required=True)
    provider = fields.Selection(
        selection=PROVIDER_SELECTION,
        string="Proveedor",
        required=True,
        index=True,
    )

    _sql_constraints = [
        (
            "provider_code_unique",
            "unique(provider, code)",
            "El código de moneda debe ser único por proveedor.",
        ),
    ]

    def name_get(self):
        return [(record.id, "%s (%s)" % (record.name, record.code)) for record in self]
