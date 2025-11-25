{
    'name': 'GC Odoo Potenciar API',
    'version': '16.0.2.2.3',  # Eliminación de endpoint legacy
    'category': 'Accounting/Accounting',
    'summary': 'API endpoint for receiving account moves and creating them in Odoo with OAuth support and Swagger documentation',
    'description': """
GC Odoo Potenciar API
====================

Este módulo proporciona endpoints REST API para crear asientos contables en Odoo
utilizando tipos de operación predefinidos.

Características principales:
---------------------------
* Autenticación OAuth con tokens de acceso
* Creación de asientos individuales y en lote
* Tipos de operación predefinidos para automatizar la contabilización
* Documentación interactiva con Swagger UI
* Especificación OpenAPI 3.0 completa
* Procesamiento automático de movimientos
* Validación robusta de datos de entrada

Endpoints disponibles:
---------------------
* GET /api/v1/docs - Documentación Swagger UI interactiva
* GET /api/v1/openapi.json - Especificación OpenAPI en formato JSON
* POST /api/v1/account-moves - Crear un asiento contable
* POST /api/v1/account-moves/batch - Crear múltiples asientos (hasta 100)
* GET /api/v1/health - Health check del servicio
* GET/POST /api/v1/test - Endpoint de prueba

Accede a /api/v1/docs para ver la documentación completa e interactiva.
    """,
    'author': 'GauchoCode',
    'website': 'https://gauchocode.com',
    'depends': [
        'base',
        'account',
        'web',
        'auth_oauth',  # Para soporte OAuth usando el módulo nativo de Odoo
    ],

    'data': [
        'security/ir.model.access.csv',
        'views/api_account_move_views.xml',
        'views/api_operation_type_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}