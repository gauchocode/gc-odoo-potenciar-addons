import json
import os
from odoo import http
from odoo.http import request, Response


class SwaggerController(http.Controller):
    """Controlador específico para servir la documentación Swagger UI y OpenAPI"""

    @http.route('/api/v1/openapi.json', type='http', auth='none', methods=['GET'], csrf=False)
    def openapi_spec(self):
        """Endpoint que devuelve la especificación OpenAPI 3.0 en formato JSON"""
        try:
            # Obtener la ruta del archivo openapi.json
            module_path = os.path.dirname(os.path.dirname(__file__))
            openapi_file_path = os.path.join(module_path, 'static', 'openapi.json')
            
            # Leer el archivo JSON
            with open(openapi_file_path, 'r', encoding='utf-8') as f:
                openapi_spec = json.load(f)
            
            return Response(
                json.dumps(openapi_spec, indent=2),
                headers=[('Content-Type', 'application/json')]
            )
        except FileNotFoundError:
            return Response(
                json.dumps({'error': 'OpenAPI specification not found'}),
                status=404,
                headers=[('Content-Type', 'application/json')]
            )
        except Exception as e:
            return Response(
                json.dumps({'error': f'Error loading OpenAPI spec: {str(e)}'}),
                status=500,
                headers=[('Content-Type', 'application/json')]
            )

    @http.route('/api/v1/docs', type='http', auth='none', methods=['GET'], csrf=False)
    def swagger_ui(self):
        """Endpoint que sirve la documentación Swagger UI"""
        html_content = self._generate_swagger_html()
        return Response(
            html_content,
            headers=[('Content-Type', 'text/html')]
        )

    def _generate_swagger_html(self):
        """Genera el HTML de Swagger UI"""
        html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GC Odoo Potenciar API - Documentation</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui.css" />
    <style>
        html {
            box-sizing: border-box;
            overflow: -moz-scrollbars-vertical;
            overflow-y: scroll;
        }
        *, *:before, *:after {
            box-sizing: inherit;
        }
        body {
            margin:0;
            background: #fafafa;
        }
        .swagger-ui .topbar {
            background-color: #2c3e50;
        }
        .swagger-ui .topbar .download-url-wrapper {
            display: none;
        }
        .custom-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
            margin-bottom: 20px;
        }
        .custom-header h1 {
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }
        .custom-header p {
            margin: 10px 0 0 0;
            font-size: 1.2em;
            opacity: 0.9;
        }
        .custom-footer {
            background: #2c3e50;
            color: white;
            padding: 20px;
            text-align: center;
            margin-top: 40px;
        }
        .custom-footer a {
            color: #3498db;
            text-decoration: none;
        }
        .custom-footer a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="custom-header">
        <h1>🚀 GC Odoo Potenciar API</h1>
        <p>Documentación interactiva de la API para crear asientos contables en Odoo</p>
    </div>
    <div id="swagger-ui"></div>
    
    <div class="custom-footer">
        <p>
            📖 <strong>GC Odoo Potenciar API</strong> v1.2.0 | 
            🔗 <a href="/api/v1/openapi.json" target="_blank">OpenAPI JSON</a> | 
            ❤️ Desarrollado por <a href="https://gauchocode.com" target="_blank">Gauchocode</a>
        </p>
    </div>
    
    <script src="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-bundle.js"></script>
    <script src="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-standalone-preset.js"></script>
    <script>
        window.onload = function() {
            const ui = SwaggerUIBundle({
                url: '/api/v1/openapi.json',
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "StandaloneLayout",
                validatorUrl: null,
                tryItOutEnabled: true,
                requestInterceptor: function(request) {
                    // Agregar headers adicionales si es necesario
                    request.headers['Accept'] = 'application/json';
                    if (request.method === 'POST') {
                        request.headers['Content-Type'] = 'application/json';
                    }
                    console.log('Request intercepted:', request);
                    return request;
                },
                responseInterceptor: function(response) {
                    // Interceptar respuestas si es necesario
                    console.log('Response intercepted:', response);
                    return response;
                },
                onComplete: function() {
                    console.log('✅ Swagger UI loaded successfully');
                    
                    // Personalizar algunos elementos después de cargar
                    setTimeout(function() {
                        // Ocultar el header por defecto de Swagger UI
                        const topbar = document.querySelector('.swagger-ui .topbar');
                        if (topbar) {
                            topbar.style.display = 'none';
                        }
                        
                        // Agregar información adicional
                        const infoDiv = document.querySelector('.swagger-ui .info');
                        if (infoDiv) {
                            const additionalInfo = document.createElement('div');
                            additionalInfo.innerHTML = `
                                <div style="background: #e8f4fd; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #1976d2;">
                                    <h4 style="margin-top: 0; color: #1976d2;">💡 Información importante</h4>
                                    <ul style="margin-bottom: 0;">
                                        <li><strong>Base URL:</strong> Todos los endpoints están bajo <code>/api/v1/</code></li>
                                        <li><strong>Autenticación:</strong> Se requiere OAuth token en el body de las peticiones POST</li>
                                        <li><strong>Formato de fecha:</strong> Usar formato YYYY-MM-DD</li>
                                        <li><strong>Límite batch:</strong> Máximo 100 movimientos por llamada batch</li>
                                        <li><strong>Referencia externa:</strong> Usar <code>external_reference</code> para evitar duplicados</li>
                                    </ul>
                                </div>
                                
                                <div style="background: #f0f9ff; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #0ea5e9;">
                                    <h4 style="margin-top: 0; color: #0ea5e9;">🎯 Endpoints de prueba rápida</h4>
                                    <p style="margin-bottom: 0;">
                                        Antes de usar los endpoints principales, puedes probar la conectividad:
                                    </p>
                                    <ul style="margin-bottom: 0;">
                                        <li><strong>Health Check:</strong> <code>GET /api/v1/health</code></li>
                                        <li><strong>Test básico:</strong> <code>GET /api/v1/test</code></li>
                                    </ul>
                                </div>
                            `;
                            infoDiv.appendChild(additionalInfo);
                        }
                    }, 1000);
                },
                onFailure: function(error) {
                    console.error('❌ Failed to load Swagger UI:', error);
                    
                    // Mostrar error en la interfaz
                    const swaggerDiv = document.getElementById('swagger-ui');
                    if (swaggerDiv) {
                        swaggerDiv.innerHTML = `
                            <div style="padding: 40px; text-align: center; color: #e74c3c;">
                                <h2>❌ Error cargando la documentación</h2>
                                <p>No se pudo cargar la especificación OpenAPI.</p>
                                <p><strong>Error:</strong> ${error.message || error}</p>
                                <p>
                                    <a href="/api/v1/openapi.json" target="_blank" style="color: #3498db;">
                                        🔗 Ver especificación OpenAPI directamente
                                    </a>
                                </p>
                            </div>
                        `;
                    }
                }
            });
        };
    </script>
</body>
</html>
        """
        return html_content