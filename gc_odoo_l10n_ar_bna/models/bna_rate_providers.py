# -*- coding: utf-8 -*-

import datetime
import logging

import requests
from lxml import etree

from odoo import exceptions, _

_logger = logging.getLogger(__name__)

BNA_HISTORICO_URL = "https://bna.com.ar/Cotizador/MonedasHistorico"
BCRA_API_URL = "https://api.bcra.gob.ar/estadisticascambiarias/v1.0/Cotizaciones"
DOLAR_API_URLS = (
    "https://dolarapi.com/v1/dolares",
    "https://dolarapi.com/v1/cotizaciones",
)

REQUEST_TIMEOUT = 10
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64)"


class BnaRateProvider:
    """Base interface for BNA exchange rate search methods.

    fetch() returns a dict keyed by the provider's own currency identifier:
        {
            'provider-code': {
                'compra': float, 'venta': float,
                'fecha': datetime.date,
            },
            ...
        }
    """

    def fetch(self):
        raise NotImplementedError


class BnaHistoricoProvider(BnaRateProvider):
    """Scrapes https://bna.com.ar/Cotizador/MonedasHistorico ("Valor Hoy").

    The page publishes compra and venta for each provider-specific currency.
    """

    def fetch(self):
        try:
            response = requests.get(
                BNA_HISTORICO_URL,
                timeout=REQUEST_TIMEOUT,
                headers={"User-Agent": USER_AGENT},
            )
            response.raise_for_status()
        except Exception as e:
            _logger.error("Error accediendo al Cotizador Histórico del BNA: %s", e)
            raise exceptions.UserError(_("No se pudo conectar al Cotizador Histórico del Banco Nación."))

        page = etree.HTML(response.text)
        rows = page.xpath("//table[contains(@class, 'cotizador')]//tbody/tr")

        fecha_nodes = page.xpath("//div[@class='titulo-cotizador']")
        fecha_cotizacion = datetime.date.today()
        if fecha_nodes and fecha_nodes[0].text:
            try:
                fecha_str = fecha_nodes[0].text.split(":")[-1].strip()
                fecha_cotizacion = datetime.datetime.strptime(fecha_str, "%d/%m/%Y").date()
            except ValueError:
                pass

        values = {}
        for row in rows:
            cols = row.xpath(".//td")
            if len(cols) != 3:
                continue
            raw_nombre = (cols[0].text or "").strip()
            nombre_moneda = raw_nombre.replace("(*)", "").strip()

            # "(*)" marks currencies the page itself quotes per 100 units (e.g. JPY);
            # normalize to a per-unit rate here so every provider speaks the same unit.
            factor = 100.0 if raw_nombre.endswith("(*)") else 1.0
            compra = float((cols[1].text or "0").strip().replace(",", ".")) / factor
            venta = float((cols[2].text or "0").strip().replace(",", ".")) / factor

            values[nombre_moneda] = {
                "compra": compra,
                "venta": venta,
                "fecha": fecha_cotizacion,
            }

        return values


class BcraApiProvider(BnaRateProvider):
    """Fetches https://api.bcra.gob.ar/estadisticascambiarias/v1.0/Cotizaciones.

    The API publishes one reference value per currency, used for both compra
    and venta.
    """

    def fetch(self):
        try:
            response = requests.get(
                BCRA_API_URL,
                timeout=REQUEST_TIMEOUT,
                headers={"User-Agent": USER_AGENT},
            )
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            _logger.error("Error accediendo a la API de Estadísticas Cambiarias del BCRA: %s", e)
            raise exceptions.UserError(_("No se pudo conectar a la API de Estadísticas Cambiarias del BCRA."))

        results = data.get("results", {})
        fecha_cotizacion = datetime.date.today()
        if results.get("fecha"):
            try:
                fecha_cotizacion = datetime.datetime.strptime(results["fecha"], "%Y-%m-%d").date()
            except ValueError:
                pass

        values = {}
        for item in results.get("detalle", []):
            currency_code = item.get("codigoMoneda")
            rate = item.get("tipoCotizacion") or 0.0
            if not currency_code or currency_code == "ARS" or not rate:
                continue

            values[currency_code] = {
                "compra": rate,
                "venta": rate,
                "fecha": fecha_cotizacion,
            }

        return values


class DolarApiProvider(BnaRateProvider):
    """Fetch current dollar markets and other currencies from DolarAPI.

    Records are keyed by ``moneda:casa`` (for example ``USD:oficial`` or
    ``EUR:oficial``). ``casa`` alone is not unique in ``/v1/cotizaciones``.
    """

    @staticmethod
    def _parse_date(value):
        if not value:
            return datetime.date.today()
        try:
            return datetime.datetime.fromisoformat(value.replace("Z", "+00:00")).date()
        except (TypeError, ValueError):
            return datetime.date.today()

    def fetch(self):
        values = {}
        try:
            for url in DOLAR_API_URLS:
                response = requests.get(
                    url,
                    timeout=REQUEST_TIMEOUT,
                    headers={"User-Agent": USER_AGENT},
                )
                response.raise_for_status()
                for item in response.json():
                    currency_code = item.get("moneda")
                    market = item.get("casa")
                    if not currency_code or not market:
                        continue
                    provider_currency = "%s:%s" % (currency_code, market)
                    compra = item.get("compra")
                    venta = item.get("venta")
                    if compra is None and venta is None:
                        continue
                    values[provider_currency] = {
                        "compra": compra,
                        "venta": venta,
                        "fecha": self._parse_date(item.get("fechaActualizacion")),
                    }
        except Exception as e:
            _logger.error("Error accediendo a DolarAPI: %s", e)
            raise exceptions.UserError(_("No se pudo conectar a DolarAPI."))
        return values


PROVIDERS = {
    "bna_historico": BnaHistoricoProvider,
    "bcra_api": BcraApiProvider,
    "dolar_api": DolarApiProvider,
}

PROVIDER_SELECTION = [
    ("bna_historico", "BNA - Cotizador Histórico"),
    ("bcra_api", "BCRA - Estadísticas Cambiarias"),
    ("dolar_api", "DolarAPI"),
]


def get_provider(method):
    provider_class = PROVIDERS.get(method)
    if not provider_class:
        raise exceptions.UserError(_("Método de búsqueda de cotización BNA no soportado: %s") % method)
    return provider_class()
