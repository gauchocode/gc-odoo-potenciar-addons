# Ejemplos para Postman - GC Odoo Potenciar API

## Configuración Base
- **Base URL**: `http://localhost:8069` (cambiar según tu configuración)
- **Content-Type**: `application/json`

## 1. Health Check

**Método**: GET  
**URL**: `{{base_url}}/api/v1/health`  
**Headers**: Ninguno especial  

**Respuesta esperada**:
```json
{
    "status": "ok",
    "service": "Potenciar API",
    "databases": ["db1", "db2", "..."],
    "timestamp": "2023-10-23 10:30:00"
}
```

## 2. Test Endpoint

**Método**: GET o POST  
**URL**: `{{base_url}}/api/v1/test`  
**Headers**: Ninguno especial  

**Respuesta esperada**:
```json
{
    "status": "ok",
    "message": "Test endpoint working with GET method",
    "module": "gc_odoo_potenciar_api"
}
```

## 3. Consultar Estado por UUID

**Método**: GET  
**URL**: `{{base_url}}/api/v1/status/{{uuid}}`  
**Parámetros Query**:
- `database`: nombre de la base de datos
- `username`: usuario  
- `password`: contraseña

**Ejemplo URL**: `{{base_url}}/api/v1/status/550e8400-e29b-41d4-a716-446655440000?database={{database}}&username={{username}}&password={{password}}`

**Respuesta esperada**:
```json
{
    "status": "success",
    "uuid_searched": "550e8400-e29b-41d4-a716-446655440000",
    "moves_found": 2,
    "moves": [
        {
            "id": 123,
            "uuid": "550e8400-e29b-41d4-a716-446655440000-1",
            "name": "API/001/2023",
            "state": "done",
            "move_type": "entry",
            "partner_name": "Cliente Test",
            "date": "2023-10-23",
            "auto_process_attempted": true,
            "auto_process_success": true,
            "error_count": 0,
            "error_message": null,
            "last_error_date": null,
            "processed_date": "2023-10-23 10:30:00",
            "created_move_id": 456,
            "created_move_name": "MISC/2023/10/0001",
            "database_name": "mi_db",
            "api_user": "admin",
            "create_date": "2023-10-23 10:25:00"
        }
    ]
}
```

## 4. Account Moves - Ejemplo Básico

**Método**: POST  
**URL**: `{{base_url}}/api/v1/account_moves`  
**Headers**: `Content-Type: application/json`  

**Body (JSON)**:
```json
{
    "database": "tu_base_de_datos",
    "username": "admin",
    "password": "admin",
    "moves": [
        {
            "name": "API/001/2023",
            "move_type": "entry",
            "partner_name": "Cliente Test API",
            "date": "2023-10-23",
            "lines": [
                {
                    "name": "Débito - Cuenta por cobrar",
                    "account_id": 123,
                    "debit": 1500.00,
                    "credit": 0.00
                },
                {
                    "name": "Crédito - Ventas",
                    "account_id": 456,
                    "debit": 0.00,
                    "credit": 1500.00
                }
            ]
        }
    ]
}
```

## 5. Account Moves - Ejemplo Complejo

**Método**: POST  
**URL**: `{{base_url}}/api/v1/account_moves`  
**Headers**: `Content-Type: application/json`  

**Body (JSON)**:
```json
{
    "database": "tu_base_de_datos",
    "username": "admin",
    "password": "admin",
    "moves": [
        {
            "name": "FACT/001/2023",
            "move_type": "out_invoice",
            "partner_name": "Cliente SA",
            "partner_vat": "20123456789",
            "journal_code": "SAL",
            "date": "2023-10-23",
            "lines": [
                {
                    "name": "Producto A",
                    "account_id": 123,
                    "debit": 1210.00,
                    "credit": 0.00,
                    "partner_name": "Cliente SA"
                },
                {
                    "name": "Ventas Producto A",
                    "account_id": 456,
                    "debit": 0.00,
                    "credit": 1000.00
                },
                {
                    "name": "IVA 21%",
                    "account_id": 789,
                    "debit": 0.00,
                    "credit": 210.00
                }
            ]
        },
        {
            "name": "FACT/002/2023",
            "move_type": "out_invoice",
            "partner_name": "Otro Cliente",
            "date": "2023-10-23",
            "lines": [
                {
                    "name": "Servicio B",
                    "account_id": 124,
                    "debit": 605.00,
                    "credit": 0.00
                },
                {
                    "name": "Servicios",
                    "account_id": 457,
                    "debit": 0.00,
                    "credit": 500.00
                },
                {
                    "name": "IVA 21%",
                    "account_id": 789,
                    "debit": 0.00,
                    "credit": 105.00
                }
            ]
        }
    ]
}
```

## Respuestas Esperadas

### Éxito (Auto-procesado):
```json
{
    "api_call_uuid": "550e8400-e29b-41d4-a716-446655440000",
    "status": "success",
    "created_moves": [
        {
            "id": 123,
            "uuid": "550e8400-e29b-41d4-a716-446655440000-1",
            "name": "API/001/2023",
            "state": "done",
            "auto_processed": true,
            "account_move_id": 456,
            "error": null
        }
    ],
    "auto_processed_moves": [
        {
            "id": 123,
            "uuid": "550e8400-e29b-41d4-a716-446655440000-1",
            "name": "API/001/2023",
            "state": "done",
            "auto_processed": true,
            "account_move_id": 456,
            "error": null
        }
    ],
    "errors": [],
    "total_processed": 1,
    "successful_created": 1,
    "auto_processed_count": 1,
    "failed": 0,
    "summary": {
        "received": 0,
        "processed": 1,
        "errors": 0,
        "total_errors": 0
    }
}
```

### Éxito parcial (algunos auto-procesados, otros con error):
```json
{
    "api_call_uuid": "550e8400-e29b-41d4-a716-446655440001",
    "status": "partial_success",
    "created_moves": [
        {
            "id": 123,
            "uuid": "550e8400-e29b-41d4-a716-446655440001-1",
            "name": "API/001/2023",
            "state": "done",
            "auto_processed": true,
            "account_move_id": 456,
            "error": null
        },
        {
            "id": 124,
            "uuid": "550e8400-e29b-41d4-a716-446655440001-2",
            "name": "API/002/2023",
            "state": "error",
            "auto_processed": false,
            "account_move_id": null,
            "error": "Account with ID 999999 does not exist"
        }
    ],
    "auto_processed_moves": [
        {
            "id": 123,
            "uuid": "550e8400-e29b-41d4-a716-446655440001-1",
            "name": "API/001/2023",
            "state": "done",
            "auto_processed": true,
            "account_move_id": 456,
            "error": null
        }
    ],
    "errors": [],
    "total_processed": 2,
    "successful_created": 2,
    "auto_processed_count": 1,
    "failed": 0,
    "summary": {
        "received": 0,
        "processed": 1,
        "errors": 1,
        "total_errors": 1
    }
}
```

### Error de autenticación:
```json
{
    "status": "error",
    "message": "Authentication failed",
    "code": 401
}
```

### Error de datos:
```json
{
    "status": "partial_success",
    "created_moves": [],
    "errors": [
        {
            "move_data": {...},
            "error": "Account with ID 999999 does not exist"
        }
    ],
    "total_processed": 1,
    "successful": 0,
    "failed": 1
}
```

## Variables de Postman Sugeridas

1. Crear un Environment en Postman con:
   - `base_url`: `http://localhost:8069`
   - `database`: `tu_base_de_datos`
   - `username`: `admin`
   - `password`: `admin`

2. Usar `{{base_url}}`, `{{database}}`, etc. en las requests

## Troubleshooting

1. **404 Error**: 
   - Verificar que Odoo esté ejecutándose
   - Verificar que el módulo esté instalado
   - Probar primero el health check

2. **500 Error**:
   - Revisar logs de Odoo
   - Verificar sintaxis JSON
   - Verificar que las cuentas contables existan

3. **Authentication Failed**:
   - Verificar nombre de base de datos
   - Verificar credenciales de usuario
   - Verificar que el usuario tenga permisos

4. **Account not found**:
   - Verificar que los IDs de cuenta sean correctos
   - Usar IDs numéricos válidos (enteros positivos)
   - Verificar que las cuentas existan en la base de datos especificada
   - Consultar el plan de cuentas para obtener los IDs correctos