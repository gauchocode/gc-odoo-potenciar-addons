# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
import requests
from lxml import etree
import datetime
import logging
from bs4 import BeautifulSoup


_logger = logging.getLogger(__name__)

class ResCompany(models.Model):
    _inherit = "res.company"

    l10n_ar_bna_rate_type = fields.Selection(
        selection=[('billete', 'Billete'), ('divisa', 'Divisa')],
        string='Rate',
        required=True,
        default='billete'
    )
    l10n_ar_bna_currency_value = fields.Selection(
        selection=[('compra', 'Compra'), ('venta', 'Venta'), ('promedio', 'Promedio Compra-Venta')],
        string='Value',
        required=True,
        default='venta'
        )
    def _parse_bna_data(self, available_currencies):
        from lxml import etree
        import requests
        import datetime

        # Mapeo de nombres en la tabla BNA a código Odoo
        MAPEO_BNA = {
            "Dolar U.S.A": "USD",
            "Euro": "EUR",
            "Real": "BRL",
            "Libra Esterlina": "GBP",
            "Franco Suizo": "CHF",
            "Yen": "JPY",
            "Dólar Canadiense": "CAD",
            "Corona Danesa": "DKK",
            "Corona Noruega": "NOK",
            "Corona Sueca": "SEK",
            "Yuan": "CNY",
            "Dólar Australiano": "AUD",
        }

        POR_100 = ["JPY", "CHF", "CAD", "DKK", "NOK", "SEK", "CNY"]

        url = "https://www.bna.com.ar/Personas"
        try:
            response = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64)'
            })
            response.raise_for_status()
        except Exception as e:
            _logger.error(f"Error accediendo a la web del BNA: {e}")
            raise exceptions.UserError("No se pudo conectar al sitio del Banco Nación.")

        page = etree.HTML(response.text)

        def extract_table_data(div_id):
            values = {}
            div = page.xpath(f"//div[@id='{div_id}']")
            if not div:
                return {}

            table = div[0].xpath(".//table")[0]
            rows = table.xpath(".//tbody/tr")

            for row in rows:
                cols = row.xpath(".//td")
                if len(cols) != 3:
                    continue
                nombre_moneda = cols[0].text.strip()
                compra = float(cols[1].text.strip().replace(",", "."))
                venta = float(cols[2].text.strip().replace(",", "."))

                values[nombre_moneda] = {
                    "compra": compra,
                    "venta": venta
                }
            return values

        billete_data = extract_table_data("billetes")
        divisa_data = extract_table_data("divisas")

        # Fecha = hoy (BNA no publica la fecha en esta página)
        fecha_cotizacion = datetime.date.today()

        codigos_odoo = set(moneda.name for moneda in available_currencies)
        values = {}

        for nombre_bna, currency_code in MAPEO_BNA.items():
            if currency_code not in codigos_odoo:
                continue

            compra_billete = billete_data.get(nombre_bna, {}).get("compra")
            venta_billete = billete_data.get(nombre_bna, {}).get("venta")
            compra_divisa = divisa_data.get(nombre_bna, {}).get("compra")
            venta_divisa = divisa_data.get(nombre_bna, {}).get("venta")

            factor = 100.0 if currency_code in POR_100 else 1.0

            values[currency_code] = {
                "billete_compra": (compra_billete or 0.0) / factor,
                "billete_venta": (venta_billete or 0.0) / factor,
                "divisa_compra": (compra_divisa or 0.0) / factor,
                "divisa_venta": (venta_divisa or 0.0) / factor,
                "fecha": fecha_cotizacion
            }

        return values or False


    def _generate_currency_rates(self, parsed_data):
        currency_rate_obj = self.env['res.currency.rate']
        bna_currency_model = self.env['account.bna.currencies']

        for company in self:
            rate_type = company.l10n_ar_bna_rate_type
            _logger.info(f"Processing BNA rates for company {company.name} with rate type {rate_type}")
            currency_value = company.l10n_ar_bna_currency_value
            _logger.info(f"Currency value selected: {currency_value}")
            _logger.info(f"parsed_data.items(): {parsed_data.items()}")
            for currency_name, data in parsed_data.items():
                bna_currency = bna_currency_model.search([
                    ('name', '=', currency_name),
                ], limit=1)
                if not bna_currency or not bna_currency.property_read_rate:
                    continue

                if currency_value == 'venta':
                    rate = data[f'{rate_type}_venta']
                elif currency_value == 'compra':
                    rate = data[f'{rate_type}_compra']
                else:
                    rate = (data[f'{rate_type}_venta'] + data[f'{rate_type}_compra']) / 2

                units = bna_currency.bna_units or 1.0
                rate_value = rate / units
                _logger.info(f"Processing {currency_name} with rate {rate_value} and units {units}")

                currency_id = bna_currency.currency_id
                existing_rate = currency_rate_obj.search([
                    ('currency_id', '=', currency_id.id),
                    ('name', '=', data['fecha'])
                ], limit=1)
                vals = {
                    'currency_id': currency_id.id,
                    'company_rate': 1.0 / rate_value,
                    'name': data['fecha'],
                }
                if existing_rate:
                    existing_rate.write({'company_rate': 1.0 / rate_value})
                else:
                    currency_rate_obj.create(vals)
                _logger.info(f"Updated rate for {currency_name} on {data['fecha']}: {1.0 / rate_value}")

            # Asegurar que ARS esté siempre a 1

    def update_bna_currency_rates(self):
        for company in self:
            currencies = self.env['res.currency'].search([('name', 'in', ['USD', 'EUR', 'BRL'])])
            parsed_data = company._parse_bna_data(currencies)
            _logger.info(f"Parsed data for {company.name}: {parsed_data}")
            if not parsed_data:
                _logger.warning('No parsed data from BNA!')
                continue
            company._generate_currency_rates(parsed_data)
