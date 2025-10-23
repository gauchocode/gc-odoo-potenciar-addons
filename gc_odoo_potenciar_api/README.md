# GC Odoo Potenciar API

Módulo para recibir account.moves vía API REST y procesarlos en Odoo.

## Características

- **Endpoint API**: Recibe datos de account.moves vía JSON
- **Autenticación**: Valida usuario/contraseña contra la base de datos especificada
- **UUID único**: Cada llamada API tiene un identificador único para trazabilidad
- **Procesamiento automático**: Intenta crear los asientos automáticamente al recibir datos
- **Modelo intermedio**: Almacena datos recibidos con estado de procesamiento
- **Manejo de errores**: Si falla el procesamiento automático, guarda el error y permite reintento
- **Procesamiento manual**: Permite reprocesar manualmente después de resolver errores
- **Vistas completas**: Dashboard, listas y formularios para monitorear el estado
- **Seguimiento detallado**: Historial de errores, intentos y estados de procesamiento

## Instalación

1. Copiar el módulo a la carpeta de addons
2. Actualizar la lista de aplicaciones
3. Instalar el módulo `gc_odoo_potenciar_api`

## Uso del API

### Endpoint Principal

```
POST /api/v1/account_moves
Content-Type: application/json
```

### Formato de Datos

```json
{
    "database": "nombre_de_la_base_de_datos",
    "username": "usuario_odoo",
    "password": "contraseña_usuario",
    "moves": [
        {
            "name": "REF/001/2023",
            "move_type": "entry",
            "partner_name": "Cliente Ejemplo S.A.",
            "partner_vat": "20123456789",
            "journal_code": "MISC",
            "date": "2023-10-22",
            "lines": [
                {
                    "name": "Descripción línea 1",
                    "account_id": 123,
                    "debit": 1500.00,
                    "credit": 0.00,
                    "partner_name": "Cliente Ejemplo S.A."
                },
                {
                    "name": "Descripción línea 2",
                    "account_id": 456, 
                    "debit": 0.00,
                    "credit": 1500.00
                }
            ]
        }
    ]
}
```

### Campos Requeridos

#### Nivel Move:
- `name`: Referencia del movimiento
- `lines`: Array con al menos una línea

#### Nivel Line:
- `name`: Descripción de la línea
- `account_id`: ID de la cuenta contable (entero)
- `debit` o `credit`: Al menos uno debe ser mayor a 0

### Campos Opcionales

#### Nivel Move:
- `move_type`: Tipo de movimiento (default: 'entry')
- `partner_name`: Nombre del partner
- `partner_vat`: CUIT/VAT del partner
- `journal_code`: Código del diario
- `date`: Fecha del movimiento

#### Nivel Line:
- `partner_name`: Nombre del partner para la línea
- `analytic_account_code`: Código de cuenta analítica

### Tipos de Movimiento Soportados

- `entry`: Asiento contable (default)
- `out_invoice`: Factura de cliente
- `out_refund`: Nota de crédito de cliente
- `in_invoice`: Factura de proveedor
- `in_refund`: Nota de crédito de proveedor
- `out_receipt`: Recibo de venta
- `in_receipt`: Recibo de compra

## Ejemplo con curl

```bash
curl -X POST http://localhost:8069/api/v1/account_moves \\
  -H "Content-Type: application/json" \\
  -d '{
    "database": "mi_base_datos",
    "username": "admin",
    "password": "admin",
    "moves": [
      {
        "name": "API/001/2023",
        "move_type": "entry",
        "partner_name": "Test Cliente",
        "date": "2023-10-22",
        "lines": [
          {
            "name": "Línea débito",
            "account_id": 123,
            "debit": 1000.0,
            "credit": 0.0
          },
          {
            "name": "Línea crédito",
            "account_id": 456,
            "debit": 0.0,
            "credit": 1000.0
          }
        ]
      }
    ]
  }'
```

## Respuesta del API

### Respuesta Exitosa

```json
{
    "api_call_uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "status": "success",
    "created_moves": [
        {
            "id": 123,
            "uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890-1",
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
            "uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890-1",
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

### Respuesta con Errores

```json
{
    "status": "partial_success",
    "created_moves": [],
    "errors": [
        {
            "move_data": {...},
            "error": "Account not found with code: 999999"
        }
    ],
    "total_processed": 1,
    "successful": 0,
    "failed": 1
}
```

## Procesamiento Automático y Manual

### Procesamiento Automático
- Al recibir datos vía API, se intenta crear automáticamente el account.move
- Si es exitoso, el estado cambia a "Done" y se crea el asiento
- Si falla, se guarda el error y se puede reprocesar manualmente

### Procesamiento Manual
1. Ir a **Potenciar API > Dashboard** para ver el estado general
2. Ir a **Potenciar API > API Moves > API Account Moves** para ver los movimientos recibidos
3. Filtrar por estado "Error" para ver los que fallaron en procesamiento automático
4. Abrir un movimiento en estado "Error" o "Received"
5. Resolver el problema (crear cuentas faltantes, corregir datos, etc.)
6. Hacer clic en "Retry Processing" para marcar como listo para reintento
7. Hacer clic en "Process Move" para procesar manualmente
8. Si persisten errores, aparecerán en la pestaña "Error Details"

## Estados de los Movimientos

- **Received**: Recibido vía API, en espera de procesamiento automático
- **Processing**: En proceso de conversión a account.move  
- **Done**: Procesado exitosamente (automático o manual)
- **Error**: Error durante el procesamiento automático
- **Retry**: Listo para reintento después de resolver errores

## Identificadores Únicos

- **API Call UUID**: Identificador único de la llamada API completa
- **Move UUID**: Identificador único de cada movimiento (API Call UUID + secuencia)
- Permite trazabilidad completa y evita duplicados

## Seguridad

- Los usuarios normales pueden ver y crear registros
- Los managers de contabilidad pueden modificar y eliminar
- La autenticación se valida contra la base de datos especificada
- No se requiere autenticación adicional para el endpoint (se valida en el payload)

## Health Check

```bash
GET /api/v1/health
```

Respuesta:
```json
{
    "status": "ok",
    "service": "Potenciar API"
}
```

## Troubleshooting

### Error 404 "Not Found"
- **Causa más común**: El módulo no está instalado o Odoo no reconoce las rutas
- **Solución**:
  1. Verificar que Odoo esté ejecutándose: `curl http://localhost:8069`
  2. Verificar que el módulo esté instalado en la base de datos
  3. Reiniciar Odoo después de instalar el módulo
  4. Probar primero el endpoint de health check: `GET /api/v1/health`
  5. Si health check funciona pero account_moves no, verificar instalación del módulo

### Error: "Account with ID XXXXX does not exist"
- Verificar que el ID de la cuenta contable sea correcto
- Verificar que la cuenta exista en el plan de cuentas de la base de datos
- Usar solo IDs numéricos válidos (enteros positivos)

### Error: "Journal not found with code: XXXXX" 
- Verificar que el diario exista
- Verificar que el código del diario sea correcto
- Si no se especifica journal_code, se usa el diario por defecto según el tipo

### Error: "Authentication failed"
- Verificar que la base de datos exista y esté en la lista del health check
- Verificar usuario y contraseña
- Verificar que el usuario tenga permisos en la base de datos
- Probar con credenciales de administrador primero

### Error: "Partner not found"
- El partner se crea automáticamente si no existe
- Verificar datos del VAT si se proporciona

### Múltiples Bases de Datos
- El módulo funciona con múltiples bases de datos en la misma instancia
- Cada request debe especificar la base de datos correcta
- Usar el health check para ver las bases disponibles

## Logs

Los logs se escriben en el log de Odoo con el prefijo del módulo.
Buscar por `gc_odoo_potenciar_api` en los logs para debugging.