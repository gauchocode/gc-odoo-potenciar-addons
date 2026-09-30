{
    "name": "GC Odoo Purchase Invoice Import API",
    "version": "16.0.2.0.0",
    "category": "Accounting/Accounting",
    "summary": "API para recibir facturas de compra ya mapeadas (contrato v0.1) y crear facturas de proveedor en borrador",
    "description": """
GC Odoo Purchase Invoice Import API
====================================

Expone POST /api/v1/purchase-invoices para recibir facturas de compra del
integrador Radiant / "Looking for Trouble" (contrato v0.1), ya mapeadas a
IDs de Odoo (partner_id, product_id, account_id, tax_ids, etc.). Valida la
forma del payload, verifica que los IDs referenciados existan, detecta
duplicados por documento AR estándar, valida montos con tolerancia propia y
crea la factura de proveedor **en borrador**. Puede crear el contacto
automáticamente si el proveedor no matchea por partner_id/CUIT y la política
`policy_if_missing` del payload lo indica; de lo contrario queda pendiente de
revisión manual. Nunca publica la factura (`action_post()` explícitamente
prohibido).

Ver README.md y DECISIONES.md en el módulo para el contrato completo, las
decisiones tomadas y las limitaciones vigentes.
    """,
    "author": "GauchoCode",
    "website": "https://gauchocode.com",
    "license": "LGPL-3",
    "depends": [
        "base",
        "account",
        "analytic",
        "l10n_ar",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/purchase_invoice_import_log_views.xml",
        "views/res_config_settings_views.xml",
        "views/menu_views.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": False,
}
