{
    'name': 'Template de Correo Electrónico segun diario',
    'version': '16.0.1.0.3',
    'summary': 'Permite definir un template de correo electrónico por diario',
    'author': 'GauchoCode',
    'depends': ['account','account_ux'],
    'data': [
        'views/account_journal_views.xml',
        'data/mail_templates.xml',
    ],
    'installable': True,
    'license': 'AGPL-3',
}
