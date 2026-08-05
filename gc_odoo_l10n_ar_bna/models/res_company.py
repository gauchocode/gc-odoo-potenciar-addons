# -*- coding: utf-8 -*-

import logging

from odoo import models

from . import bna_rate_providers

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = "res.company"

    def _configured_rate_currencies(self):
        self.ensure_one()
        currencies = self.env["res.currency"].with_company(self).search([])
        return currencies.filtered(
            lambda currency: currency.l10n_ar_rate_provider
            and currency.l10n_ar_provider_currency_id
        )

    @staticmethod
    def _selected_rate(data, value_type):
        compra = data.get("compra")
        venta = data.get("venta")
        if value_type == "compra":
            return compra
        if value_type == "venta":
            return venta
        if compra is None or venta is None:
            return None
        return (compra + venta) / 2.0

    def _generate_currency_rate(self, currency, data):
        self.ensure_one()
        rate_value = self._selected_rate(data, currency.l10n_ar_rate_value)
        if not rate_value or rate_value <= 0:
            _logger.warning(
                "No hay una cotización %s válida para %s (%s)",
                currency.l10n_ar_rate_value,
                currency.name,
                currency.l10n_ar_provider_currency_id.code,
            )
            return

        rate_model = self.env["res.currency.rate"]
        domain = [
            ("currency_id", "=", currency.id),
            ("company_id", "=", self.id),
            ("name", "=", data["fecha"]),
        ]
        rate = rate_model.search(domain, limit=1)
        values = {
            "currency_id": currency.id,
            "company_id": self.id,
            "company_rate": 1.0 / rate_value,
            "name": data["fecha"],
        }
        if rate:
            rate.write({"company_rate": values["company_rate"]})
        else:
            rate_model.create(values)

        _logger.info(
            "Cotización actualizada para %s con %s/%s: %s",
            currency.name,
            currency.l10n_ar_rate_provider,
            currency.l10n_ar_provider_currency_id.code,
            rate_value,
        )

    def update_currency_rates_from_providers(self):
        """Update every configured currency, fetching each provider only once."""
        for company in self:
            currencies = company._configured_rate_currencies()
            provider_results = {}
            for currency in currencies:
                provider_name = currency.l10n_ar_rate_provider
                if provider_name not in provider_results:
                    try:
                        provider_results[provider_name] = (
                            bna_rate_providers.get_provider(provider_name).fetch()
                        )
                    except Exception:
                        configured = currencies.filtered(
                            lambda item: item.l10n_ar_rate_provider == provider_name
                        )
                        _logger.exception(
                            "Falló la consulta al proveedor %s para la empresa %s. "
                            "Monedas configuradas: %s",
                            provider_name,
                            company.name,
                            ", ".join(configured.mapped("name")),
                        )
                        raise

                    _logger.info(
                        "Proveedor %s consultado para %s: %d cotizaciones recibidas",
                        provider_name,
                        company.name,
                        len(provider_results[provider_name]),
                    )

                provider_currency = currency.l10n_ar_provider_currency_id.code
                available_rates = provider_results[provider_name]
                data = available_rates.get(provider_currency)

                # Compatibility with DolarAPI catalog records created before
                # identifiers became unambiguous ("oficial" -> "USD:oficial").
                if not data and provider_name == "dolar_api" and ":" not in provider_currency:
                    composite_key = "%s:%s" % (currency.name, provider_currency)
                    data = available_rates.get(composite_key)
                    if data:
                        _logger.warning(
                            "La moneda %s usa el identificador anterior de DolarAPI '%s'. "
                            "Se resolvió automáticamente como '%s'. Actualice el módulo "
                            "para migrar el catálogo.",
                            currency.name,
                            provider_currency,
                            composite_key,
                        )

                if not data:
                    currency_options = sorted(
                        key for key in available_rates
                        if key == currency.name or key.startswith("%s:" % currency.name)
                    )
                    available_preview = sorted(available_rates)[:20]
                    _logger.warning(
                        "No se pudo actualizar %s para la empresa %s. Proveedor=%s; "
                        "identificador configurado='%s'; opciones compatibles=%s; "
                        "primeros identificadores recibidos=%s; total recibido=%d. "
                        "Revise la configuración de 'Moneda en el proveedor'.",
                        currency.name,
                        company.name,
                        provider_name,
                        provider_currency,
                        currency_options or "ninguna",
                        available_preview or "ninguno",
                        len(available_rates),
                    )
                    continue
                company._generate_currency_rate(currency, data)

    def update_bna_currency_rates(self):
        """Backward-compatible entry point used by older integrations."""
        return self.update_currency_rates_from_providers()
