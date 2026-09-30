import json
import os

from odoo import http
from odoo.http import Response


class PurchaseInvoiceImportSwaggerController(http.Controller):
    """Documentación OpenAPI/Swagger específica de este módulo.

    Rutas propias (/api/v1/purchase-invoices/...) para no colisionar con
    /api/v1/docs y /api/v1/openapi.json de gc_odoo_potenciar_api.
    """

    @http.route('/api/v1/purchase-invoices/openapi.json', type='http', auth='none', methods=['GET'], csrf=False)
    def openapi_spec(self):
        module_path = os.path.dirname(os.path.dirname(__file__))
        openapi_file_path = os.path.join(module_path, 'static', 'openapi.json')
        try:
            with open(openapi_file_path, 'r', encoding='utf-8') as f:
                spec = json.load(f)
        except FileNotFoundError:
            return Response(
                json.dumps({'error': 'OpenAPI specification not found'}),
                status=404,
                headers=[('Content-Type', 'application/json')],
            )
        return Response(
            json.dumps(spec, indent=2, ensure_ascii=False),
            headers=[('Content-Type', 'application/json')],
        )

    @http.route('/api/v1/purchase-invoices/docs', type='http', auth='none', methods=['GET'], csrf=False)
    def swagger_ui(self):
        return Response(self._swagger_html(), headers=[('Content-Type', 'text/html')])

    def _swagger_html(self):
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GC Odoo Purchase Invoice Import API - Documentation</title>
    <link rel="stylesheet" type="text/css" href="/gc_odoo_purchase_invoice_import_api/static/swagger-ui/swagger-ui.css" />
    <style>
        html { box-sizing: border-box; overflow-y: scroll; }
        *, *:before, *:after { box-sizing: inherit; }
        body { margin: 0; background: #fafafa; }
        .swagger-ui .topbar { display: none; }
        .custom-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 20px; text-align: center;
        }
        .custom-header h1 { margin: 0; font-size: 2em; font-weight: 300; }
        .custom-footer {
            background: #2c3e50; color: white; padding: 20px; text-align: center;
        }
        .custom-footer a { color: #3498db; text-decoration: none; }
    </style>
</head>
<body>
    <div class="custom-header">
        <h1>Purchase Invoice Import API</h1>
        <p>Importación de facturas de compra desde proveedor externo (contrato v0.1)</p>
    </div>
    <div id="swagger-ui"></div>
    <div class="custom-footer">
        <p>
            <a href="/api/v1/purchase-invoices/openapi.json" target="_blank">OpenAPI JSON</a> |
            Desarrollado por <a href="https://gauchocode.com" target="_blank">Gauchocode</a>
        </p>
    </div>
    <script src="/gc_odoo_purchase_invoice_import_api/static/swagger-ui/swagger-ui-bundle.js"></script>
    <script src="/gc_odoo_purchase_invoice_import_api/static/swagger-ui/swagger-ui-standalone-preset.js"></script>
    <script>
        window.onload = function() {
            SwaggerUIBundle({
                url: '/api/v1/purchase-invoices/openapi.json',
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [SwaggerUIBundle.presets.apis, SwaggerUIStandalonePreset],
                plugins: [SwaggerUIBundle.plugins.DownloadUrl],
                layout: "StandaloneLayout",
                validatorUrl: null,
                tryItOutEnabled: true,
                requestInterceptor: function(request) {
                    request.headers['Accept'] = 'application/json';
                    if (request.method === 'POST') {
                        request.headers['Content-Type'] = 'application/json';
                    }
                    return request;
                }
            });
        };
    </script>
</body>
</html>
        """
