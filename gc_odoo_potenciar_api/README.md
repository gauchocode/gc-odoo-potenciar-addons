# 🚀 GC Odoo Potenciar API

API REST para crear asientos contables en Odoo usando tipos de operación predefinidos con autenticación OAuth y documentación Swagger interactiva.

## 🌟 **Características**

- **📖 Documentación Interactiva**: Swagger UI completo con ejemplos
- **🔐 Autenticación OAuth**: Integración nativa con auth_oauth de Odoo
- **⚙️ Tipos de Operación**: Plantillas predefinidas para asientos contables comunes
- **📊 Múltiples Asientos**: Endpoint batch para procesar varios asientos en una llamada
- **👤 Partners por VAT**: Búsqueda y creación automática de partners usando CUIT/VAT
- **✅ Validación Robusta**: Manejo de errores y validaciones completas
- **📑 OpenAPI 3.0**: Especificación completa en formato JSON

---

## 📦 **Instalación**

1. Instalar dependencia Python:
   ```bash
   pip install PyJWT>=2.8.0
   ```

2. Instalar módulo `auth_oauth` en Odoo

3. Copiar este módulo a addons/

4. Actualizar lista de aplicaciones

5. Instalar `gc_odoo_potenciar_api`

6. Configurar OAuth Provider en Odoo

---

## 📖 **Documentación Interactiva**

### **🎯 Acceder a Swagger UI**
Visita la documentación interactiva en tu navegador:

```
http://tu-servidor-odoo:puerto/api/v1/docs
```

**Ejemplo:**
```
http://localhost:8069/api/v1/docs
```

### **📋 Especificación OpenAPI**
Obtén la especificación en formato JSON:

```
http://tu-servidor-odoo:puerto/api/v1/openapi.json
```

---

## 🎯 **Endpoints Disponibles**

### **📖 Documentación**
- **GET** `/api/v1/docs` - Documentación Swagger UI interactiva
- **GET** `/api/v1/openapi.json` - Especificación OpenAPI 3.0

### **💼 Asientos Contables**
- **POST** `/api/v1/account-moves` - Crear un asiento contable
- **POST** `/api/v1/account-moves/batch` - Crear múltiples asientos (hasta 100)
- **POST** `/api/v1/account_moves` - Endpoint legacy para compatibilidad

### **🔧 Sistema**
- **GET** `/api/v1/health` - Health check del servicio
- **GET/POST** `/api/v1/test` - Endpoint de prueba

---

## 📋 **Ejemplos Simples**

### **Ejemplo 1: Crear una Venta**

#### Request:
```bash
curl -X POST http://localhost:8069/api/v1/account-moves \
  -H "Content-Type: application/json" \
  -d '{
    "database": "mi_empresa",
    "oauth_access_token": "ya29.a0AfH6SMC...",
    "operation_type_code": "SALE_SIMPLE",
    "amount": 1000.00,
    "date": "2025-10-30",
    "partner_vat": "20123456789",
    "partner_name": "Cliente Ejemplo S.A.",
    "external_reference": "VENTA-2025-001",
    "description": "Venta de servicios"
  }'
```

#### Response:
```json
{
    "success": true,
    "move_id": 123,
    "move_name": "INV/2025/10/0001",
    "operation_type": "SALE_SIMPLE",
    "message": "Account move created successfully",
    "authenticated_user": "admin@empresa.com"
}
```

#### Asiento Generado:
```
Comprobante: INV/2025/10/0001
┌─────────────────────────────────┬─────────────┬─────────────┐
│ Cuenta                          │ Debe        │ Haber       │
├─────────────────────────────────┼─────────────┼─────────────┤
│ Cuentas por Cobrar             │ $ 1,000.00  │ -           │
│ Ingresos por Ventas            │ -           │ $ 1,000.00  │
└─────────────────────────────────┴─────────────┴─────────────┘
```

### **Ejemplo 2: Registrar un Gasto**

#### Request:
```bash
curl -X POST http://localhost:8069/api/v1/account-moves \
  -H "Content-Type: application/json" \
  -d '{
    "database": "mi_empresa",
    "oauth_access_token": "ya29.a0AfH6SMC...",
    "operation_type_code": "EXPENSE",
    "amount": 500.00,
    "date": "2025-10-30",
    "partner_vat": "30555666777",
    "partner_name": "Proveedor ABC S.R.L.",
    "external_reference": "COMPRA-2025-002",
    "description": "Compra de materiales de oficina"
  }'
```

#### Response:
```json
{
    "success": true,
    "move_id": 124,
    "move_name": "BILL/2025/10/0002",
    "operation_type": "EXPENSE",
    "message": "Account move created successfully",
    "authenticated_user": "admin@empresa.com"
}
```

#### Asiento Generado:
```
Comprobante: BILL/2025/10/0002
┌─────────────────────────────────┬─────────────┬─────────────┐
│ Cuenta                          │ Debe        │ Haber       │
├─────────────────────────────────┼─────────────┼─────────────┤
│ Gastos Generales               │ $ 500.00    │ -           │
│ Cuentas por Pagar              │ -           │ $ 500.00    │
└─────────────────────────────────┴─────────────┴─────────────┘
```

### **Ejemplo 3: Registrar un Pago Recibido**

#### Request:
```bash
curl -X POST http://localhost:8069/api/v1/account-moves \
  -H "Content-Type: application/json" \
  -d '{
    "database": "mi_empresa",
    "oauth_access_token": "ya29.a0AfH6SMC...",
    "operation_type_code": "PAYMENT_IN",
    "amount": 1200.00,
    "date": "2025-10-30",
    "partner_vat": "27987654321",
    "partner_name": "Cliente XYZ S.A.",
    "external_reference": "PAGO-2025-003",
    "description": "Cobranza de factura pendiente"
  }'
```

#### Response:
```json
{
    "success": true,
    "move_id": 125,
    "move_name": "MISC/2025/10/0003",
    "operation_type": "PAYMENT_IN",
    "message": "Account move created successfully",
    "authenticated_user": "admin@empresa.com"
}
```

#### Asiento Generado:
```
Comprobante: MISC/2025/10/0003
┌─────────────────────────────────┬─────────────┬─────────────┐
│ Cuenta                          │ Debe        │ Haber       │
├─────────────────────────────────┼─────────────┼─────────────┤
│ Banco                          │ $ 1,200.00  │ -           │
│ Cuentas por Cobrar             │ -           │ $ 1,200.00  │
└─────────────────────────────────┴─────────────┴─────────────┘
```

---

## 🚀 **Múltiples Asientos en Una Llamada**

### **Ejemplo: Batch de Operaciones del Día**

#### Request:
```bash
curl -X POST http://localhost:8069/api/v1/account-moves/batch \
  -H "Content-Type: application/json" \
  -d '{
    "database": "mi_empresa",
    "oauth_access_token": "ya29.a0AfH6SMC...",
    "moves": [
        {
            "operation_type_code": "SALE_SIMPLE",
            "amount": 1500.00,
            "date": "2025-10-30",
            "partner_vat": "20111222333",
            "partner_name": "Cliente A S.A.",
            "description": "Venta matutina - Proyecto Alpha"
        },
        {
            "operation_type_code": "SALE_SIMPLE",
            "amount": 2200.00,
            "date": "2025-10-30",
            "partner_vat": "27444555666",
            "partner_name": "Cliente B S.R.L.",
            "description": "Venta vespertina - Licencias"
        },
        {
            "operation_type_code": "EXPENSE",
            "amount": 800.00,
            "date": "2025-10-30",
            "partner_vat": "30777888999",
            "partner_name": "Proveedor C S.A.",
            "description": "Compra de equipamiento"
        },
        {
            "operation_type_code": "PAYMENT_IN",
            "amount": 1200.00,
            "date": "2025-10-30",
            "partner_vat": "20555444333",
            "partner_name": "Cliente D S.A.",
            "description": "Cobranza factura anterior"
        }
    ]
  }'
```

#### Response:
```json
{
    "success": true,
    "summary": {
        "total_requested": 4,
        "successful": 4,
        "failed": 0
    },
    "created_moves": [
        {
            "index": 0,
            "move_id": 126,
            "move_name": "INV/2025/10/0004",
            "operation_type": "SALE_SIMPLE",
            "amount": 1500.00,
            "partner_vat": "20111222333",
            "description": "Venta matutina - Proyecto Alpha"
        },
        {
            "index": 1,
            "move_id": 127,
            "move_name": "INV/2025/10/0005",
            "operation_type": "SALE_SIMPLE",
            "amount": 2200.00,
            "partner_vat": "27444555666",
            "description": "Venta vespertina - Licencias"
        },
        {
            "index": 2,
            "move_id": 128,
            "move_name": "BILL/2025/10/0006",
            "operation_type": "EXPENSE",
            "amount": 800.00,
            "partner_vat": "30777888999",
            "description": "Compra de equipamiento"
        },
        {
            "index": 3,
            "move_id": 129,
            "move_name": "MISC/2025/10/0007",
            "operation_type": "PAYMENT_IN",
            "amount": 1200.00,
            "partner_vat": "20555444333",
            "description": "Cobranza factura anterior"
        }
    ],
    "authenticated_user": "admin@empresa.com"
}
```

#### Resultado Contable:
```
📊 RESUMEN DEL BATCH:
✅ 4 asientos contables creados
✅ Total ventas: $3,700.00
✅ Total gastos: $800.00
✅ Total cobrado: $1,200.00
📈 Resultado neto: +$2,900.00
```

---

## 📚 **Parámetros de la API**

### **Endpoint Individual (`/api/v1/account-moves`)**

#### Campos Requeridos:
| Campo | Descripción |
|-------|-------------|
| `database` | Nombre de la base de datos |
| `oauth_access_token` | Token OAuth válido |
| `operation_type_code` | Código del tipo de operación |
| `amount` | Importe de la operación |
| `date` | Fecha del asiento (formato: YYYY-MM-DD o YYYY-MM-DD HH:MM:SS) |

#### Campos Opcionales:
| Campo | Descripción |
|-------|-------------|
| `partner_vat` | CUIT/VAT del partner (requerido si el tipo lo necesita) |
| `partner_name` | Nombre del partner |
| `external_reference` | Referencia externa o identificador del sistema externo (único por BD) |
| `description` | Descripción de la operación |

### **Endpoint Batch (`/api/v1/account-moves/batch`)**

#### Estructura:
```json
{
    "database": "nombre_db",
    "oauth_access_token": "token",
    "moves": [
        {
            "operation_type_code": "TIPO",
            "amount": 1000.00,
            "date": "2025-10-30",
            "partner_vat": "VAT",
            "partner_name": "Nombre",
            "description": "Descripción"
        }
    ]
}
```

#### Límites:
- **Máximo 100 movimientos** por batch
- **Timeout de 60 segundos**
- **Validación individual** de cada movimiento

---

## 🔄 **Tipos de Operación Incluidos**

### **SALE_SIMPLE** - Venta Simple
```
📝 Factura de Cliente
Líneas:
• Cuentas por Cobrar (Débito) ← Importe API
• Ingresos por Ventas (Crédito) ← Importe API
```

### **PAYMENT_IN** - Pago Recibido
```
📝 Asiento Manual
Líneas:
• Banco (Débito) ← Importe API
• Cuentas por Cobrar (Crédito) ← Importe API
```

### **EXPENSE** - Gasto Simple
```
📝 Factura de Proveedor
Líneas:
• Gastos Generales (Débito) ← Importe API
• Cuentas por Pagar (Crédito) ← Importe API
```

---

## ⚠️ **Manejo de Errores**

### **Errores Comunes**

#### Error de Autenticación:
```json
{
    "success": false,
    "error": "OAuth authentication failed: Invalid token"
}
```

#### Error de Parámetros:
```json
{
    "success": false,
    "error": "Missing required parameters: database, oauth_access_token, operation_type_code, amount, date"
}
```

#### Error de Formato de Fecha:
```json
{
    "success": false,
    "error": "Invalid date format. Expected YYYY-MM-DD or YYYY-MM-DD HH:MM:SS, got: 30/10/2025"
}
```

#### Error de Referencia Externa Duplicada:
```json
{
    "success": false,
    "error": "External reference 'VENTA-2025-001' already exists in database mi_empresa"
}
```

#### Error de Tipo de Operación:
```json
{
    "success": false,
    "error": "Operation type 'INVALID_CODE' not found or inactive"
}
```

#### Error de Partner (cuando es requerido):
```json
{
    "success": false,
    "error": "partner_vat is required for this operation type"
}
```

### **Errores en Batch**
```json
{
    "success": false,
    "summary": {
        "total_requested": 3,
        "successful": 2,
        "failed": 1
    },
    "created_moves": [...],
    "errors": [
        {
            "index": 1,
            "error": "Move 2: Operation type 'INVALID' not found"
        }
    ]
}
```

---

## 🔧 **Configuración OAuth**

### **1. Crear OAuth Provider en Odoo**
1. Ir a `Configuración > Usuarios y Compañías > OAuth Providers`
2. Crear nuevo proveedor (ej: Google)
3. Configurar Client ID y Client Secret

### **2. Obtener Token OAuth**
```python
# Ejemplo en Python
import requests

# Autenticarse con Google OAuth
auth_url = "https://accounts.google.com/o/oauth2/auth"
token_url = "https://oauth2.googleapis.com/token"

# Obtener token y usar en API calls
headers = {
    "Content-Type": "application/json"
}

data = {
    "database": "mi_empresa",
    "oauth_access_token": "ya29.a0AfH6SMC...",
    "operation_type_code": "SALE_SIMPLE",
    "amount": 1000.00,
    "partner_vat": "20123456789",
    "description": "Test desde Python"
}

response = requests.post(
    "http://localhost:8069/api/v1/account-moves",
    headers=headers,
    json=data
)

print(response.json())
```

---

## 📊 **Ejemplos de Scripts**

### **Script Bash Simple**
```bash
#!/bin/bash

# Configuración
BASE_URL="http://localhost:8069"
TOKEN="TU_TOKEN_OAUTH_AQUI"
DATABASE="mi_empresa"

# Crear venta
curl -X POST $BASE_URL/api/v1/account-moves \
  -H "Content-Type: application/json" \
  -d "{
    \"database\": \"$DATABASE\",
    \"oauth_access_token\": \"$TOKEN\",
    \"operation_type_code\": \"SALE_SIMPLE\",
    \"amount\": 1500.00,
    \"partner_vat\": \"20123456789\",
    \"partner_name\": \"Cliente Test\",
    \"description\": \"Venta desde script\"
  }"
```

### **Script Python Simple**
```python
#!/usr/bin/env python3
import requests

# Configuración
API_BASE = "http://localhost:8069/api/v1"
TOKEN = "TU_TOKEN_OAUTH_AQUI"
DATABASE = "mi_empresa"

def crear_venta(amount, partner_vat, partner_name, description):
    data = {
        "database": DATABASE,
        "oauth_access_token": TOKEN,
        "operation_type_code": "SALE_SIMPLE",
        "amount": amount,
        "partner_vat": partner_vat,
        "partner_name": partner_name,
        "description": description
    }
    
    response = requests.post(f"{API_BASE}/account-moves", json=data)
    return response.json()

# Usar la función
resultado = crear_venta(
    amount=2500.00,
    partner_vat="20111222333",
    partner_name="Cliente Python",
    description="Venta desde Python"
)

print(f"Resultado: {resultado}")
if resultado.get('success'):
    print(f"Asiento creado: {resultado['move_name']}")
```

---

## 🔍 **Debugging y Logs**

### **Health Check**
```bash
# Verificar que la API esté funcionando
curl http://localhost:8069/api/v1/health

# Respuesta esperada:
{
    "status": "OK",
    "message": "API is running",
    "timestamp": "2025-10-30T..."
}
```
---

## 🤝 **Soporte**

- **Documentación Técnica**: Ver archivos `README_*.md`
- **Scripts de Prueba**: Ver archivos `test_*.py`
- **Ejemplos Completos**: Ver `EJEMPLOS_COMPLETOS.md`
- **Soporte Técnico**: Contactar equipo Gauchocode

---

## 📝 **Notas Importantes**

1. **Partners**: La API busca por VAT primero, si no existe lo crea
2. **Tipos de Operación**: Deben estar configurados y activos en Odoo
3. **OAuth**: Configurar correctamente el proveedor OAuth
4. **Límites**: Máximo 100 asientos por batch
5. **Validación**: Cada asiento se valida independientemente

**¡La API está lista para usar!** 🚀
