import datetime
from unittest.mock import Mock, patch

from odoo.tests.common import TransactionCase

from ..models import bna_rate_providers


class TestRateProviders(TransactionCase):
    def test_dolar_api_uses_casa_as_provider_currency(self):
        dolares = Mock()
        dolares.raise_for_status.return_value = None
        dolares.json.return_value = [{
            "compra": 1000.0,
            "venta": 1020.0,
            "casa": "oficial",
            "moneda": "USD",
            "fechaActualizacion": "2026-08-05T12:30:00.000Z",
        }]
        cotizaciones = Mock()
        cotizaciones.raise_for_status.return_value = None
        cotizaciones.json.return_value = [{
            "compra": 37.0,
            "venta": 38.0,
            "casa": "oficial",
            "moneda": "UYU",
            "fechaActualizacion": "2026-08-05T12:30:00.000Z",
        }]

        with patch.object(
            bna_rate_providers.requests,
            "get",
            side_effect=[dolares, cotizaciones],
        ):
            values = bna_rate_providers.DolarApiProvider().fetch()

        self.assertEqual(set(values), {"USD:oficial", "UYU:oficial"})
        self.assertEqual(values["USD:oficial"]["compra"], 1000.0)
        self.assertEqual(values["USD:oficial"]["venta"], 1020.0)
        self.assertEqual(values["UYU:oficial"]["fecha"], datetime.date(2026, 8, 5))

    def test_selected_rate(self):
        company_model = self.env["res.company"]
        data = {"compra": 10.0, "venta": 14.0}
        self.assertEqual(company_model._selected_rate(data, "compra"), 10.0)
        self.assertEqual(company_model._selected_rate(data, "venta"), 14.0)
        self.assertEqual(company_model._selected_rate(data, "promedio"), 12.0)

    def test_currency_configuration_selects_provider_key_and_value(self):
        company = self.env.company
        currency = self.env.ref("base.USD").with_company(company)
        provider_currency = self.env.ref(
            "gc_odoo_l10n_ar_bna.provider_currency_dolar_api_blue"
        )
        currency.write({
            "active": True,
            "l10n_ar_rate_provider": "dolar_api",
            "l10n_ar_provider_currency_id": provider_currency.id,
            "l10n_ar_rate_value": "promedio",
        })
        provider = Mock()
        provider.fetch.return_value = {
            "USD:blue": {
                "compra": 1000.0,
                "venta": 1100.0,
                "fecha": datetime.date(2026, 8, 5),
            }
        }

        with patch.object(bna_rate_providers, "get_provider", return_value=provider):
            company.update_currency_rates_from_providers()

        rate = self.env["res.currency.rate"].search([
            ("currency_id", "=", currency.id),
            ("company_id", "=", company.id),
            ("name", "=", datetime.date(2026, 8, 5)),
        ])
        self.assertTrue(rate)
        self.assertAlmostEqual(rate.company_rate, 1.0 / 1050.0)

    def test_legacy_dolar_api_identifier_is_resolved_with_currency_code(self):
        company = self.env.company
        currency = self.env.ref("base.USD")
        legacy_mapping = self.env["l10n_ar.rate.provider.currency"].create({
            "name": "Dólar oficial (anterior)",
            "code": "oficial",
            "provider": "dolar_api",
        })
        currency.write({
            "active": True,
            "l10n_ar_rate_provider": "dolar_api",
            "l10n_ar_provider_currency_id": legacy_mapping.id,
            "l10n_ar_rate_value": "venta",
        })
        provider = Mock()
        provider.fetch.return_value = {
            "USD:oficial": {
                "compra": 1470.0,
                "venta": 1520.0,
                "fecha": datetime.date(2026, 8, 5),
            }
        }

        with patch.object(bna_rate_providers, "get_provider", return_value=provider):
            company.update_currency_rates_from_providers()

        rate = self.env["res.currency.rate"].search([
            ("currency_id", "=", currency.id),
            ("company_id", "=", company.id),
            ("name", "=", datetime.date(2026, 8, 5)),
        ])
        self.assertAlmostEqual(rate.company_rate, 1.0 / 1520.0)
