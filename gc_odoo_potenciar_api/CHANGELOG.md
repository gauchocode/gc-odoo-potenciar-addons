# 📝 Changelog - GC Odoo Potenciar API

## [1.2.3] - 2024-11-10

### 🧹 **Limpieza de Endpoints Legacy**

#### 🗑️ **Endpoint Eliminado**
- **Eliminado**: `POST /api/v1/account_moves` (endpoint legacy)
- **Razón**: Simplificar la API y mantener solo los endpoints modernos
- **Alternativa**: Usar `POST /api/v1/account-moves` o `POST /api/v1/account-moves/batch`

#### 📋 **Documentación Actualizada**
- **OpenAPI spec**: Eliminados esquemas `LegacyCreateAccountMovesRequest` y `LegacyCreateAccountMovesResponse`
- **Manifest**: Descripción actualizada sin referencias al endpoint legacy
- **Swagger UI**: Ya no muestra el endpoint eliminado

#### ✅ **Beneficios**
- **API más limpia**: Menos confusión con múltiples endpoints similares
- **Mantenimiento reducido**: Menos código que mantener
- **Documentación clara**: Solo endpoints activos y recomendados
- **Mejor UX**: Desarrollo más directo sin opciones legacy

---

## [1.2.2] - 2024-11-10

### ✂️ **Eliminación de Dependencias Externas**

#### 🎯 **Simplificación de Autenticación**
- **Eliminado PyJWT**: Ya no requerimos dependencias externas
- **Solo OAuth nativo**: Utilizamos únicamente el sistema OAuth de Odoo
- **Código más limpio**: Menos complejidad en la autenticación
- **Sin dependencias Python externas**: Instalación más simple

#### 🔄 **Cambios en la API**
- **Parámetro cambiado**: `jwt_token` → `oauth_access_token`
- **Autenticación simplificada**: Directamente con tokens OAuth de Odoo
- **Compatibilidad mantenida**: Username/password sigue funcionando
- **Documentación actualizada**: OpenAPI spec actualizada

#### ✅ **Beneficios**
- **Instalación más fácil**: Sin pip install PyJWT
- **Menos dependencias**: Menos puntos de falla
- **OAuth nativo**: Mejor integración con Odoo
- **Mantenimiento reducido**: Menos código que mantener

---

## [1.2.1] - 2024-11-10

### 🔧 **Refactorización y Organización del Código**

#### 📁 **Separación de Responsabilidades**
- **Controlador principal (`main.py`)**: Solo contiene endpoints funcionales de la API
- **Controlador Swagger (`swagger.py`)**: Dedicado exclusivamente a la documentación
- **Especificación OpenAPI (`static/openapi.json`)**: Archivo JSON independiente y reutilizable

#### 🏗️ **Estructura Mejorada**
```
controllers/
├── __init__.py            # ✨ Actualizado - imports ambos controladores
├── main.py               # 🔧 Limpiado - solo endpoints funcionales  
└── swagger.py            # ✨ Nuevo - endpoints de documentación

static/
└── openapi.json          # ✨ Nuevo - especificación OpenAPI 3.0
```

#### 🎯 **Beneficios de la Refactorización**
- **Código más limpio**: Separación clara de responsabilidades
- **Mantenimiento fácil**: Especificación OpenAPI en archivo independiente
- **Reutilización**: El `openapi.json` puede usarse con otras herramientas
- **Performance**: Menor carga de memoria al cargar controladores
- **Escalabilidad**: Fácil agregar nuevos endpoints de documentación

#### 🔄 **Sin Cambios en Funcionalidad**
- ✅ Todos los endpoints siguen funcionando igual
- ✅ URLs de documentación mantienen la misma ruta
- ✅ Swagger UI funciona exactamente igual
- ✅ Compatibilidad total con versiones anteriores

---

## [1.2.0] - 2024-11-10

### ✨ **Nuevas Funcionalidades**

#### 📖 **Documentación Swagger Completa**
- **GET `/api/v1/docs`**: Interfaz Swagger UI interactiva y completamente funcional
- **GET `/api/v1/openapi.json`**: Especificación OpenAPI 3.0 en formato JSON
- Documentación completa de todos los endpoints existentes
- Ejemplos de request/response para cada endpoint
- Esquemas de datos detallados con validaciones
- Interfaz visual moderna y responsive

#### 🔧 **Mejoras Técnicas**
- Especificación OpenAPI 3.0 completa y estándar
- Integración con CDN de Swagger UI (v5.9.0) para mejor rendimiento
- Soporte para `Try it out` directo desde la documentación
- Validación automática de requests en la interfaz
- Headers y content-types configurados automáticamente

#### 📚 **Documentación Adicional**
- **SWAGGER.md**: Guía completa de uso de Swagger UI
- **SETUP.md**: Instrucciones detalladas de instalación y configuración
- **requirements.txt**: Dependencias Python específicas del módulo
- README actualizado con enlaces a documentación interactiva

### 🔄 **Cambios en Endpoints Existentes**

#### **Endpoints Documentados**
- `POST /api/v1/account-moves` - Crear asiento individual
- `POST /api/v1/account-moves/batch` - Crear múltiples asientos  
- `POST /api/v1/account_moves` - Endpoint legacy
- `GET /api/v1/health` - Health check
- `GET/POST /api/v1/test` - Endpoint de prueba

#### **Mejoras en Responses**
- Responses más consistentes y documentadas
- Mejores mensajes de error con códigos HTTP apropiados
- Ejemplos realistas en toda la documentación

### 🔧 **Cambios Técnicos**

#### **Dependencias**
- Agregada dependencia `PyJWT>=2.8.0` para manejo de tokens JWT
- Import condicional de JWT para evitar errores si no está instalado
- `external_dependencies` declaradas correctamente en `__manifest__.py`

#### **Manifest**
- Version bumped to `16.0.1.2.0`
- Descripción extendida con todas las funcionalidades
- Website y license agregados
- Dependencias Python especificadas

#### **Estructura de Archivos**
```
gc_odoo_potenciar_api/
├── controllers/
│   └── main.py                 # ✨ Nuevos endpoints Swagger
├── SWAGGER.md                  # ✨ Nuevo - Guía Swagger UI  
├── SETUP.md                    # ✨ Nuevo - Guía instalación
├── requirements.txt            # ✨ Nuevo - Deps Python
├── README.md                   # 🔄 Actualizado
└── __manifest__.py             # 🔄 Actualizado
```

### 🎯 **Acceso Rápido**

#### **Documentación Interactiva**
```
http://localhost:8069/api/v1/docs
```

#### **Especificación OpenAPI**
```
http://localhost:8069/api/v1/openapi.json
```

### 🔧 **Instalación**

#### **Dependencia Requerida**
```bash
pip install PyJWT>=2.8.0
```

#### **Para Docker/Contenedores**
```bash
docker exec -it tu_contenedor pip install PyJWT>=2.8.0
```

### 📋 **Compatibilidad**

- ✅ **Backwards Compatible**: Todos los endpoints existentes funcionan igual
- ✅ **Odoo 16.0**: Totalmente compatible
- ✅ **Existing Integrations**: No requiere cambios en clientes existentes
- ✅ **OAuth Authentication**: Sin cambios en el flujo de autenticación

### 🔍 **Notas para Desarrolladores**

#### **OpenAPI Spec Features**
- Especificación OpenAPI 3.0 completa
- Esquemas reutilizables para requests/responses
- Validaciones de tipos de datos
- Ejemplos realistas para todos los endpoints
- Tags organizacionales para mejor navegación

#### **Swagger UI Features**
- Try it out funcional para todos los endpoints
- Syntax highlighting de JSON
- Auto-complete para parámetros
- Response previews en tiempo real
- Diseño responsive y moderno

#### **Technical Improvements**
- Manejo robusto de errores en generación de OpenAPI
- Import condicional de PyJWT para evitar crashes
- HTML template optimizado para Swagger UI
- CDN usage para mejor performance

#### 🌟 **Resumen de la Versión 1.2.3**
Eliminación del endpoint legacy `/api/v1/account_moves` para simplificar la API y reducir confusión. La API queda más limpia con solo los endpoints modernos y recomendados.

#### 🌟 **Resumen de la Versión 1.2.2**
Eliminación completa de la dependencia PyJWT y simplificación de la autenticación para usar únicamente OAuth nativo de Odoo. Esto reduce la complejidad del módulo y elimina dependencias externas.

#### 🌟 **Resumen de la Versión 1.2.1**
Refactorización arquitectónica que mejora la organización del código, separando la documentación Swagger del controlador principal y externalizando la especificación OpenAPI en un archivo JSON independiente para mejor mantenibilidad y reutilización.

---

## [1.1.0] - Versión Anterior

### **Funcionalidades Base**
- Endpoints REST para crear asientos contables
- Autenticación OAuth con Odoo
- Tipos de operación predefinidos
- Batch processing hasta 100 asientos
- Validación robusta de datos
- Health check y test endpoints
- Manejo de partners por VAT
- Procesamiento automático de movimientos

---

### 🎉 **Próximas Funcionalidades Planeadas**

- **Rate Limiting**: Protección contra abuse
- **API Keys**: Alternativa a OAuth para casos simples  
- **Webhooks**: Notificaciones de eventos
- **Bulk Operations**: Operaciones masivas optimizadas
- **Async Processing**: Procesamiento asíncrono para grandes volúmenes
- **Audit Trail**: Logging detallado de operaciones API

---

**¡Disfruta de la nueva documentación interactiva!** 🚀📖