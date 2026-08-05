# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from .bna_rate_providers import PROVIDER_SELECTION


class ResCurrency(models.Model):
    _inherit = "res.currency"

    l10n_ar_rate_provider = fields.Selection(
        selection=PROVIDER_SELECTION,
        string="Proveedor de cotización",
    )
    l10n_ar_provider_currency_id = fields.Many2one(
        comodel_name="l10n_ar.rate.provider.currency",
        string="Moneda en el proveedor",
        ondelete="restrict",
        help="Moneda o mercado disponible para el proveedor seleccionado.",
    )
    l10n_ar_rate_value = fields.Selection(
        selection=[
            ("compra", "Compra"),
            ("venta", "Venta"),
            ("promedio", "Promedio compra/venta"),
        ],
        string="Valor a utilizar",
        default="venta",
        required=True,
    )

    @api.onchange("l10n_ar_rate_provider")
    def _onchange_l10n_ar_rate_provider(self):
        if (
            self.l10n_ar_provider_currency_id
            and self.l10n_ar_provider_currency_id.provider
            != self.l10n_ar_rate_provider
        ):
            self.l10n_ar_provider_currency_id = False

    @api.constrains("l10n_ar_rate_provider", "l10n_ar_provider_currency_id")
    def _check_rate_provider_currency(self):
        for currency in self:
            provider_currency = currency.l10n_ar_provider_currency_id
            if (
                provider_currency
                and provider_currency.provider != currency.l10n_ar_rate_provider
            ):
                raise ValidationError(
                    _("La moneda seleccionada no pertenece al proveedor de cotización.")
                )
