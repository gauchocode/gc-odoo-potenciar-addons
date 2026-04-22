{
    "name": "Importador de Facturas de Venta (Excel)",
    "version": "16.0.1.0.0",
    "summary": "Importa facturas de cliente en borrador desde la primera hoja de Excel",
    "author": "GauchoCode",
    "license": "AGPL-3",
    "depends": ["account", "product", "l10n_ar"],
    "external_dependencies": {
        "python": ["openpyxl"],
    },
    "data": [
        "security/ir.model.access.csv",
        "wizards/sale_invoice_import_wizard_views.xml",
        "views/menu_views.xml",
    ],
    "installable": True,
}

