# -*- coding: utf-8 -*-

{
    'name': "Gauchocode BNA Currencies",
    'version': '16.0.4.0.0',
    'summary': "Sincronización de tasas de cambio desde múltiples proveedores",
    'author': 'GauchoCode',
    'website': 'https://www.gauchocode.com/',
    'category': "Accounting",
    'depends': ['base', 'account'],
    'data': [
        "data/bna_data.xml",
        "security/ir.model.access.csv",
        "data/rate_provider_currency_data.xml",
        "views/res_currency_views.xml",
        "data/ir_cron.xml",
    ],
    'application': False,
    'installable': True,
    'license': 'LGPL-3',
}
