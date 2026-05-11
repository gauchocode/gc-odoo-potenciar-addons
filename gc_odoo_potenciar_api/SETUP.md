# ⚙️ Configuración del Módulo GC Odoo Potenciar API

## 📋 Checklist de Instalación

### ✅ **Paso 1: Dependencias Python**
```bash
# En el servidor/contenedor donde corre Odoo
pip install PyJWT>=2.8.0
```

### ✅ **Paso 2: Módulos Odoo Requeridos**
Asegúrate de que estos módulos estén instalados:
- `base` ✓ (viene por defecto)
- `account` ✓ (módulo de contabilidad)
- `web` ✓ (viene por defecto)
- `auth_oauth` ⚠️ (instalar si no está)

### ✅ **Paso 3: Instalar el Módulo**
1. Copiar la carpeta `gc_odoo_potenciar_api` a tu directorio de addons
2. Actualizar lista de aplicaciones en Odoo
3. Buscar e instalar "GC Odoo Potenciar API"

### ✅ **Paso 4: Verificar Instalación**
Acceder a:
```
http://tu-servidor:puerto/api/v1/health
```

Deberías ver:
```json
{
  "status": "ok",
  "service": "Potenciar API",
  "databases": ["db1", "db2"],
  "timestamp": "2024-11-10 15:30:00"
}
```

## 🔑 Configuración OAuth (Requerida)

### **Opción A: OAuth Provider Personalizado**

1. **Ir a Configuración > Usuarios y Compañías > Proveedores OAuth**

2. **Crear Nuevo Proveedor**:
   - **Nombre**: Mi API Provider
   - **Client ID**: `api_client_id`
   - **Client Secret**: `tu_secret_super_secreto`
   - **Cuerpo de autorización**: `web_server`
   - **URL de autorización**: `http://tu-servidor/oauth/authorize`
   - **URL de token de acceso**: `http://tu-servidor/oauth/access_token`
   - **Alcance**: `api_access`

3. **Configurar Usuario**:
   - Ir al usuario que usará la API
   - En la pestaña "OAuth" asignar un token manualmente
   - O configurar flujo OAuth completo

### **Opción B: Token Manual (Desarrollo)**

Para desarrollo rápido, puedes asignar un token directamente:

1. **Ir a Configuración > Usuarios y Compañías > Usuarios**
2. **Editar el usuario** que usará la API
3. **En la pestaña "Acceso"**, asignar:
   - **OAuth Provider**: (el que creaste)
   - **OAuth User ID**: `usuario_api`
   - **OAuth Access Token**: `tu_token_de_acceso_123456`

## 🏭 Configurar Tipos de Operación

Los tipos de operación definen cómo se crean los asientos automáticamente.

### **Acceder al Menú**
```
Contabilidad > Configuración > API Potenciar > Tipos de Operación
```

### **Ejemplo: Tipo de Operación "Venta"**

**Datos Principales**:
- **Nombre**: Ingreso por Ventas
- **Código**: `SALE_INCOME`
- **Tipo de Asiento**: `out_invoice` (Factura de Cliente)
- **Diario**: Ventas (o el que corresponda)
- **Activo**: ✓

**Líneas del Tipo de Operación**:

1. **Línea Cuenta por Cobrar**:
   - **Nombre**: Cuenta por Cobrar
   - **Cuenta**: 1.1.05.001 (Deudores por Ventas)
   - **Débito/Crédito**: Débito
   - **Tipo de Importe**: Monto Total
   - **Partner Requerido**: ✓

2. **Línea Ingreso por Ventas**:
   - **Nombre**: Ingreso por Ventas
   - **Cuenta**: 4.1.01.001 (Ventas)
   - **Débito/Crédito**: Crédito
   - **Tipo de Importe**: Calculado (se equilibra automáticamente)
   - **Partner Requerido**: ✗

### **Ejemplo: Tipo de Operación "Compra"**

**Datos Principales**:
- **Nombre**: Gasto por Compras
- **Código**: `PURCHASE_EXPENSE`
- **Tipo de Asiento**: `in_invoice` (Factura de Proveedor)

**Líneas**:

1. **Línea Gasto**:
   - **Cuenta**: 5.1.01.001 (Gastos)
   - **Débito/Crédito**: Débito
   - **Tipo de Importe**: Calculado

2. **Línea Cuenta por Pagar**:
   - **Cuenta**: 2.1.01.001 (Proveedores)
   - **Débito/Crédito**: Crédito
   - **Tipo de Importe**: Monto Total
   - **Partner Requerido**: ✓

## 🔧 Configuraciones Adicionales

### **Parámetros del Sistema**
Puedes configurar algunos parámetros en:
```
Configuración > Técnico > Parámetros > Parámetros del Sistema
```

- **`api_jwt_secret`**: Clave secreta para JWT (por defecto: `default_secret_change_me`)

### **Permisos de Usuario**
El usuario API debe tener permisos de:
- **Contabilidad**: Al menos "Usuario" o "Administrador de Facturas"
- **Contactos**: Para crear/modificar partners
- **API Access**: Si has configurado grupos específicos

## 🧪 Pruebas Básicas

### **1. Health Check**
```bash
curl -X GET http://localhost:8069/api/v1/health
```

### **2. Test Endpoint**
```bash
curl -X GET http://localhost:8069/api/v1/test
```

### **3. Documentación Swagger**
Abrir en navegador:
```
http://localhost:8069/api/v1/docs
```

### **4. Primer Asiento de Prueba**
```bash
curl -X POST http://localhost:8069/api/v1/account-moves \
  -H "Content-Type: application/json" \
  -d '{
    "database": "mi_base_datos",
    "oauth_access_token": "tu_token_aqui",
    "operation_type_code": "SALE_INCOME",
    "amount": 1000.0,
    "date": "2024-11-10",
    "partner_vat": "20123456789",
    "partner_name": "Cliente Test",
    "description": "Venta de prueba"
  }'
```

## ❗ Troubleshooting Común

### **Error: "Module not found"**
- Verificar que el módulo esté en el addons_path
- Reiniciar Odoo después de copiar archivos
- Actualizar lista de aplicaciones

### **Error: "PyJWT not found"**
```bash
# Instalar en el entorno de Python de Odoo
pip install PyJWT>=2.8.0

# O si usas contenedor Docker:
docker exec -it tu_contenedor_odoo pip install PyJWT>=2.8.0
```

### **Error: "OAuth token invalid"**
- Verificar que el usuario tenga un token OAuth válido
- El token debe estar activo y no expirado
- El usuario debe tener permisos adecuados

### **Error: "Operation type not found"**
- Crear al menos un tipo de operación
- Verificar que el código coincida exactamente
- El tipo de operación debe estar activo

### **Error: "Database not found"**
- Verificar nombre de base de datos
- La base debe estar disponible en la instancia
- Verificar permisos de acceso

## 📞 Soporte

Si tienes problemas:

1. **Revisar logs de Odoo** para errores detallados
2. **Usar Swagger UI** para probar endpoints interactivamente
3. **Verificar configuración** paso a paso con este checklist
4. **Probar con datos mínimos** antes de casos complejos

---

¡Listo! Con esta configuración tu API debería estar funcionando perfectamente. 🚀