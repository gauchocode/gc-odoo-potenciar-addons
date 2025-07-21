{
    'name': 'Reportes Personalizados de Cuenta',
    'version': '16.0.1.0.1',
    'summary': 'Permite personalizar reportes de cuenta',
    'author': 'GauchoCode',
    'depends': ['account_financial_report'],
    'data': [
        "report/aged_partner_balance.xml",
        "views/res_partner.xml",
    ],
    'installable': True,
    'license': 'AGPL-3',
}
