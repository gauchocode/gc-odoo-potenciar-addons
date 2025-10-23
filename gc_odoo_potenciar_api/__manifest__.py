{
    'name': 'GC Odoo Potenciar API',
    'version': '16.0.1.1.0',
    'category': 'Accounting/Accounting',
    'summary': 'API endpoint for receiving account moves and creating them in Odoo',
    'author': 'Gauchocode',
    'depends': [
        'base',
        'account',
        'web',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/api_account_move_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}