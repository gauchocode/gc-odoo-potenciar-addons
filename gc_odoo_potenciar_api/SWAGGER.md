# 📖 Documentación Swagger - GC Odoo Potenciar API

## 🎯 ¿Qué es Swagger UI?

Swagger UI es una interfaz interactiva que permite:
- 📋 **Explorar** todos los endpoints disponibles
- 🧪 **Probar** las APIs directamente desde el navegador  
- 📝 **Ver ejemplos** de requests y responses
- 🔍 **Entender** los parámetros requeridos y opcionales
- 📊 **Visualizar** los esquemas de datos

## 🚀 Acceso Rápido

### **Documentación Interactiva**
```
http://localhost:8069/api/v1/docs
```

### **Especificación OpenAPI JSON**
```  
http://localhost:8069/api/v1/openapi.json
```

> 💡 **Nota**: Reemplaza `localhost:8069` con la URL de tu servidor Odoo

## 🎮 Cómo usar Swagger UI

### **1. Navegar por los endpoints**
- Los endpoints están organizados por categorías (tags)
- **Account Moves**: Creación de asientos contables
- **System**: Endpoints del sistema (health, test)

### **2. Probar un endpoint**
1. **Expandir** el endpoint que quieres probar
2. Hacer clic en **"Try it out"**
3. **Completar** los parámetros requeridos
4. Hacer clic en **"Execute"**
5. **Ver** la respuesta en tiempo real

### **3. Ejemplos incluidos**
Cada endpoint incluye:
- ✅ **Ejemplo de request** completo
- ✅ **Ejemplo de response** exitoso
- ❌ **Ejemplos de errores** comunes

## 📋 Estructura de la API

### **Endpoints Principales**

#### **POST /api/v1/account-moves**
Crear un asiento contable individual

**Parámetros requeridos:**
- `database`: Nombre de la base de datos
- `oauth_access_token`: Token OAuth
- `operation_type_code`: Código del tipo de operación
- `amount`: Importe total
- `date`: Fecha (YYYY-MM-DD)

**Parámetros opcionales:**
- `partner_vat`: CUIT del partner
- `partner_name`: Nombre del partner
- `external_reference`: Referencia externa
- `description`: Descripción

#### **POST /api/v1/account-moves/batch**
Crear múltiples asientos contables (hasta 100)

Similar al anterior pero con un array `moves` conteniendo múltiples operaciones.

### **Tipos de Respuesta**

#### **✅ Respuesta Exitosa**
```json
{
  "success": true,
  "move_id": 123,
  "move_name": "MISC/2024/001",
  "api_move_id": 456,
  "api_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "operation_type": "SALE_INCOME",
  "message": "Account move created successfully",
  "authenticated_user": "admin"
}
```

#### **❌ Respuesta de Error**
```json
{
  "success": false,
  "error": "Missing required parameters: database, oauth_access_token, operation_type_code, amount, date"
}
```

## 🔧 Configuración OAuth

Para usar la API necesitas configurar OAuth en Odoo:

### **1. Crear OAuth Provider**
- Ir a **Configuración > Usuarios > Proveedores OAuth**
- Crear nuevo proveedor
- Configurar `client_id` y `client_secret`

### **2. Obtener Access Token**
- El usuario debe autenticarse via OAuth
- Odoo generará un `oauth_access_token`
- Este token se usa en todas las llamadas API

## 🛠️ Troubleshooting

### **Problemas Comunes**

#### **"Database not found"**
- Verificar que el nombre de la base de datos sea correcto
- La base debe existir y estar accesible

#### **"Invalid OAuth token"**
- Verificar que el token OAuth sea válido
- El token puede haber expirado
- El usuario debe estar activo

#### **"Operation type not found"**
- Verificar que el `operation_type_code` exista
- El tipo de operación debe estar activo
- Debe pertenecer a la compañía del usuario

#### **"Missing required parameters"**
- Verificar que todos los campos requeridos estén presentes
- La fecha debe estar en formato YYYY-MM-DD
- El amount debe ser un número válido

## 📚 Recursos Adicionales

### **OpenAPI Specification**
La especificación completa está disponible en:
```
http://localhost:8069/api/v1/openapi.json
```

Puedes usar este archivo con herramientas como:
- **Postman**: Importar colección automáticamente
- **Insomnia**: Generar requests de prueba
- **Swagger Codegen**: Generar SDKs cliente

### **Health Check**
Verificar que la API esté funcionando:
```
GET http://localhost:8069/api/v1/health
```

### **Test Endpoint**
Probar conectividad básica:
```
GET http://localhost:8069/api/v1/test
```

---

## 💡 Tips Útiles

1. **Usar el Try it Out**: La mejor forma de entender la API es probándola directamente
2. **Revisar los ejemplos**: Cada endpoint tiene ejemplos completos y funcionales
3. **Verificar auth primero**: Usar el health check para verificar conectividad
4. **Leer los errores**: Los mensajes de error son descriptivos y útiles
5. **Usar references externas**: Para asientos duplicados, usar `external_reference`

---

🎉 **¡Listo!** Ya tienes toda la información necesaria para usar la API con Swagger UI.