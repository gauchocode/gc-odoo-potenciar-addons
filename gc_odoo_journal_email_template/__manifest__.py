{
    'name': 'Template de Correo Electrónico segun diario',
    'version': '16.0.2.0.1',
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
