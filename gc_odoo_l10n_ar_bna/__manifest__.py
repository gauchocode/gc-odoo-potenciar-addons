# -*- coding: utf-8 -*-

{
    'name': "Gauchocode BNA Currencies",
    'version': '16.0.0.1',
    'description': """Sincronización de tasas de cambio con el sitio del Banco de la Nación Argentina""",
    'summary': "Sincronización de tasas de cambio con el sitio del Banco de la Nación Argentina",
    'author': 'GauchoCode',
    'website': 'https://www.gauchocode.com/',
    'category': "Accounting",
    'depends': ['base', 'account'],
    'data': [
        "data/bna_data.xml",
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/res_config_settings_views.xml",
        "views/bna_menues_views.xml",
        "views/account_bna_currencies_views.xml",
        "data/ir_cron.xml",
    ],
    'application': False,
    'installable': True,
    'license': 'LGPL-3',
}
