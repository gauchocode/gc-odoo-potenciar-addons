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
        import requests
        from bs4 import BeautifulSoup
        import datetime

        # Mapeo de nombres en la tabla BNA a código Odoo
        MAPEO_BNA = {
            "Dolar U.S.A": "USD",
            "Euro": "EUR",
            "Real": "BRL",
            "Libra Esterlina": "GBP",
            "Franco Suizos (*)": "CHF",
            "YENES (*)": "JPY",
            "Dolares Canadienses (*)": "CAD",
            "Coronas Danesas (*)": "DKK",
            "Coronas Noruegas (*)": "NOK",
            "Coronas Suecas (*)": "SEK",
            "Yuan (*)": "CNY",
            "Dolar Australiano": "AUD",
        }
        # Monedas que cotizan cada 100 unidades
        POR_100 = ["JPY", "CHF", "CAD", "DKK", "NOK", "SEK", "CNY"]

        url = "https://www.bna.com.ar/Cotizador/MonedasHistorico"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
        except Exception as e:
            _logger.error(f"Error accediendo a la web del BNA: {e}")
            raise exceptions.UserError("No se pudo conectar al sitio del Banco Nación.")

        soup = BeautifulSoup(response.text, "html.parser")
        fecha_texto = soup.find("div", class_="titulo-cotizador")
        if not fecha_texto:
            raise exceptions.UserError("No se pudo encontrar la fecha de cotización en el sitio del BNA.")
        # Ejemplo: "Fecha: 21/7/2025"
        fecha_str = fecha_texto.text.split(":")[1].strip()
        fecha_partes = fecha_str.split("/")
        fecha_cotizacion = datetime.date(int(fecha_partes[2]), int(fecha_partes[1]), int(fecha_partes[0]))

        tabla = soup.find("table", class_="cotizador")
        if not tabla:
            raise exceptions.UserError("No se encontró la tabla de cotizaciones del BNA.")

        # Generar lista de códigos de monedas a buscar en Odoo
        codigos_odoo = set(moneda.name for moneda in available_currencies)
        values = {}
        for tr in tabla.find_all("tr"):
            tds = tr.find_all("td")
            if len(tds) != 3:
                continue
            nombre_moneda = tds[0].text.strip()
            compra = float(tds[1].text)
            venta = float(tds[2].text)
            currency_code = MAPEO_BNA.get(nombre_moneda)
            if currency_code and currency_code in codigos_odoo:
                # Si la moneda cotiza cada 100 unidades, ajustamos el valor
                factor = 100.0 if currency_code in POR_100 else 1.0
                values[currency_code] = {
                    "compra": compra / factor,
                    "venta": venta / factor,
                    "fecha": fecha_cotizacion
                }
        return values or False

    def update_bna_currency_rates(self):
        '''Main method to update rates, compatible Community.'''
        for company in self:
            currencies = self.env['res.currency'].search([('name', 'in', ['USD', 'EUR', 'BRL'])])
            parsed_data = company._parse_bna_data(currencies)
            if not parsed_data:
                _logger.warning('No parsed data from BNA!')
                continue

            rate_type = company.l10n_ar_bna_rate_type
            currency_value = company.l10n_ar_bna_currency_value
            currency_rate_obj = self.env['res.currency.rate']

            for currency in currencies:
                data = parsed_data.get(currency.name)
                if not data:
                    continue
                if currency_value == 'venta':
                    rate_value = data['venta']
                elif currency_value == 'compra':
                    rate_value = data['compra']
                else:
                    rate_value = (data['venta'] + data['compra']) / 2

                # Buscar si ya existe
                existing_rate = currency_rate_obj.search([
                    ('currency_id', '=', currency.id),
                    ('company_id', '=', company.id),
                    ('name', '=', data['fecha'])
                ], limit=1)
                vals = {
                    'currency_id': currency.id,
                    'company_rate': rate_value,
                    'name': data['fecha'],
                    'company_id': company.id,
                }
                if existing_rate:
                    existing_rate.write({'company_rate': 1.0 / rate_value})
                else:
                    currency_rate_obj.create(vals)
                _logger.info(f"Updated rate for {currency.name} ({currency_value}) on {data['fecha']}: {rate_value}")
"""
            fecha_de_hoy = fields.Date.context_today(self)
            # Peso Argentino (ARS) siempre debe valer 1
            ars = self.env['res.currency'].search([('name', '=', 'ARS')], limit=1)
            if ars:
                self.env['res.currency.rate'].create({
                    'currency_id': ars.id,
                    'rate': 1.0,
                    'name':fecha_de_hoy,
                    'company_id': company.id,
                })
"""