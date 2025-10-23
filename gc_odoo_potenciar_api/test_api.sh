#!/bin/bash

# Script para probar los endpoints del API

ODOO_URL="http://localhost:8069"

echo "=== Probando Health Check ==="
curl -s -X GET "${ODOO_URL}/api/v1/health" | jq '.'
echo ""

echo "=== Probando Test Endpoint ==="
curl -s -X GET "${ODOO_URL}/api/v1/test" | jq '.'
echo ""

# Ejemplo UUID (cambiar por un UUID real después de crear movimientos)
EXAMPLE_UUID="550e8400-e29b-41d4-a716-446655440000"

echo "=== Probando Status Endpoint (con UUID de ejemplo) ==="
curl -s -X GET "${ODOO_URL}/api/v1/status/${EXAMPLE_UUID}?database=tu_base_de_datos&username=admin&password=admin" | jq '.'
echo ""

echo "=== Probando Account Moves Endpoint (con datos de prueba) ==="
curl -s -X POST "${ODOO_URL}/api/v1/account_moves" \
  -H "Content-Type: application/json" \
  -d '{
    "database": "tu_base_de_datos",
    "username": "admin",
    "password": "admin",
    "moves": [
      {
        "name": "TEST/001/2023",
        "move_type": "entry",
        "partner_name": "Test Cliente API",
        "date": "2023-10-23",
        "lines": [
          {
            "name": "Línea de prueba débito",
            "account_id": 123,
            "debit": 1000.0,
            "credit": 0.0
          },
          {
            "name": "Línea de prueba crédito",
            "account_id": 456,
            "debit": 0.0,
            "credit": 1000.0
          }
        ]
      }
    ]
  }' | jq '.'

echo ""
echo "=== Instrucciones ==="
echo "1. Cambiar 'tu_base_de_datos' por el nombre real de tu base de datos"
echo "2. Cambiar las credenciales de usuario si es necesario"
echo "3. Cambiar los account_id (123, 456) por IDs reales de cuentas de tu base de datos"
echo "4. Si el health check funciona pero account_moves da 404, verificar que el módulo esté instalado"