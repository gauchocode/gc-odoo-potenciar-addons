{
    'name': 'Personalización de Reportes de Cuenta',
    'version': '16.0.3.0.1',
    'summary': 'Permite personalizar reportes de cuenta',
    'author': 'GauchoCode',
    'depends': ['account_financial_report','base','account'],
    'data': [
        "report/aged_partner_balance.xml",
        "views/res_partner.xml",
        "views/account_move_tree.xml",
        "report/report_aged_partner_balance_inherit.xml",
    ],
    'installable': True,
    'license': 'AGPL-3',
}
