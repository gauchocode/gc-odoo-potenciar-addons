{
    'name': 'Account Move – Control Recalculo Automático de Impuestos',
    'version': '16.0.3.0',
    'summary': 'Permite al usuario deshabilitar el recálculo automático de tax_totals',
    'author': 'GauchoCode',
    'depends': ['account'],
    'data': [
        'views/account_move_views.xml',
    ],
    'installable': True,
    'license': 'AGPL-3',
    'post_init_hook': 'set_default_automatic_tax_recalculation',

}
