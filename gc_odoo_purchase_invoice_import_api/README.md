# GC Odoo Purchase Invoice Import API

Módulo Odoo 16.0 que expone un endpoint para que el integrador **Radiant /
"Looking for Trouble"** envíe facturas de compra ya mapeadas a IDs de Odoo
(contrato v0.1) y el sistema cree la factura de proveedor **en borrador**.

## Por qué un módulo nuevo e independiente

Se creó como módulo nuevo, sin depender de `gc_odoo_potenciar_api`, porque ese
módulo tiene cambios locales sin commitear (trabajo en curso de otra persona)
que no debían leerse ni tocarse. El único acoplamiento con módulos existentes
es de **lectura como referencia de patrón**, no de dependencia en tiempo de
ejecución.

## Endpoint

```
POST /api/v1/purchase-invoices
```

### Documentación interactiva (Swagger)

```
GET /api/v1/purchase-invoices/docs           # Swagger UI
GET /api/v1/purchase-invoices/openapi.json   # Especificación OpenAPI 3.0
```

### Autenticación

HTTP Basic Auth con **las mismas credenciales que un usuario usa para entrar
al backend de Odoo** (`res.users.authenticate`, la misma validación que usa
el login web) — no hay token ni secreto separado que generar o rotar.

```
Authorization: Basic base64(usuario:contraseña)
```

**Recomendación de despliegue** (no impuesta por el módulo): crear un
usuario de servicio dedicado (ej. `servicio_proveedor`) con los permisos
mínimos, en vez de reusar la contraseña de un usuario humano. Requiere
HTTPS: Basic Auth manda la contraseña en cada request.

## Contrato de entrada (v0.1)

El proveedor manda la factura **ya mapeada** a IDs de Odoo (`partner_id`,
`product_id`, `account_id`, `tax_ids`, `uom_id`, `analytic_distribution`,
`journal_id`, `company_id`, `document_type_id`, `currency_id`, bajo la clave
`odoo` de cada bloque). Esta API **confía en esos IDs tal cual**: solo
verifica que cada uno EXISTA (`browse().exists()`), nunca los resuelve ni
corrige por su cuenta. Ver DECISIONES.md para el detalle y el riesgo
aceptado de esta decisión.

```json
{
  "schema_version": "0.1",
  "source": {
    "system": "radiant", "tenant_id": "<uuid tenant>", "invoice_id": "<uuid factura>",
    "idempotency_key": "33718285289-1-00002-00000018", "sent_at": "2026-06-23T14:05:00-03:00"
  },
  "target": {
    "company_id": 1, "journal_id": 12, "move_type": "in_invoice",
    "final_state": "draft", "final_state_reason": "tenant_config_always_draft"
  },
  "partner": {
    "cuit": "33718285289", "name": "WFLUCAR", "vat_condition": "IVA Responsable Inscripto",
    "address": "Belgrano 525", "city": "Canals", "province": "X", "postal_code": "2650",
    "odoo": {
      "partner_id": 581, "resolution": "matched", "policy_if_missing": "review",
      "afip_responsibility_code": "1", "identification_type": "CUIT", "state_id": 7
    }
  },
  "document": {
    "point_of_sale": 2, "invoice_number": 18, "invoice_date": "2026-06-23", "due_date": "2026-06-23",
    "cae": "86251025478576", "cae_due_date": "2026-07-03",
    "odoo": {
      "document_type_id": 1, "document_number": "00002-00000018",
      "accounting_date": "2026-06-23", "currency_id": 19,
      "narration": "CAE 86251025478576 (vto. 2026-07-03) · Radiant <uuid factura>"
    }
  },
  "lines": [{
    "sequence": 1, "product_code": "00001", "description": "SERVICIOS DE CONSULTORIA EXTERNA",
    "quantity": 1, "unit_price": 13130706.60, "subtotal": 13130706.60, "vat_rate": 21,
    "odoo": {
      "product_id": 345, "account_id": 210, "tax_ids": [7], "uom_id": 1,
      "analytic_distribution": {"33": 100}
    }
  }],
  "taxes": {"vat": [{"rate": 21, "base": 13130706.60, "amount": 2757448.39, "odoo_tax_id": 7}],
            "perceptions": [], "internal_taxes_amount": 0, "exempt_amount": 0, "non_taxed_amount": 0},
  "totals": {"net_amount": 13130706.60, "vat_amount": 2757448.39, "perceptions_amount": 0,
             "internal_taxes_amount": 0, "total_amount": 15888154.99},
  "validation": {"tolerance": 1.00, "action_if_exceeded": "observation"},
  "attachment": {"file_name": "33718285289_0002FCA00000018.pdf", "mime_type": "application/pdf",
                 "content_base64": "<PDF en base64>"}
}
```

Ver el ejemplo completo en `tests/fixtures/valid_v01_single_line.json` y el
detalle campo por campo en `static/openapi.json`.

### Partner ausente

Si `partner.odoo.partner_id` no viene informado, se usa
`partner.odoo.policy_if_missing`:

- `"create"`: busca por CUIT normalizado entre los contactos existentes; si
  no hay match, **crea el contacto** (`res.partner`) desde los datos del
  bloque `partner`. Se agrega un warning `"Contacto creado: ..."`.
- cualquier otro valor (incluido `"review"` o ausente): **no crea nada**,
  responde `422 pending_review`.

### Validación de montos

Nunca se confía en `validation.checks` del payload (se guarda en el log solo
como información). Esta API recalcula sus propios chequeos con la tolerancia
de `validation.tolerance` (o el parámetro de configuración si no viene):
suma de líneas vs. `totals.net_amount`, cada `subtotal` vs.
`quantity * unit_price`, suma de `taxes.vat[].amount` vs. `totals.vat_amount`,
la fórmula del total vs. `totals.total_amount`, y — ya con la factura creada
en Odoo — `move.amount_total` vs. `totals.total_amount`. Si la diferencia
supera la tolerancia, `validation.action_if_exceeded` decide: `"observation"`
(default) crea igual con advertencias y `has_observations=true`;
`"reject"` rechaza sin crear nada (o revierte la factura recién creada, si
el chequeo que falla es el último, post-creación).

### Adjunto PDF

Si `attachment.content_base64` viene informado, se valida que decodifique
como Base64 válido y que sea un PDF real (`mime_type == "application/pdf"` +
magic bytes `%PDF`). Se crea un `ir.attachment` vinculado a la factura y se
setea como `message_main_attachment_id`. El base64 **nunca** se guarda en el
log crudo (`raw_payload`): se redacta a `"<omitted N bytes>"`.

### Contrato de salida

`success` y `status` siempre presentes. `document_id` es ahora
`source.invoice_id` del payload (puede ser `null`). `warnings`, `details` y
`checks` son siempre listas (vacías si no aplica).

**201 — creada en borrador**
```json
{
  "success": true, "status": "created",
  "document_id": "b6f6c1d2-1e3a-4a3f-9c1e-000000000002",
  "idempotency_key": "33718285289-1-00002-00000018",
  "message": "Factura FA-A 00002-00000018 creada en borrador.",
  "move_id": 123, "move_name": "FA-A 00002-00000018", "log_id": 45,
  "warnings": [], "details": [],
  "checks": [{"code": "total", "expected": 15888154.99, "actual": 15888154.99, "diff": 0, "passed": true}]
}
```

**200 — duplicado** (idempotente, no es error técnico) — misma forma, `status: "duplicate"`.

**400 — validation_error**: payload inválido/incompleto, id de Odoo
referenciado inexistente, adjunto inválido, o montos fuera de tolerancia con
`action_if_exceeded: "reject"`. Cada mensaje en `details` incluye el path
JSON del campo (ej. `"lines[0].unit_price"`).

**401**: falta o es inválido el header `Authorization`. No genera log.

**422 — pending_review**: proveedor no resuelto y `policy_if_missing`
distinto de `"create"`. No crea la factura.

**500 — processing_error**: excepción inesperada; nunca incluye traceback.

## Configuración (`ir.config_parameter`)

Editable desde Ajustes → Contabilidad → sección "Importación de Facturas de
Compra (API)", o directamente:

| Clave | Obligatoria | Descripción |
|---|---|---|
| `gc_odoo_purchase_invoice_import_api.total_tolerance` | No (default `1.0`) | Tolerancia de diferencia de montos, en la moneda del comprobante, usada solo si `validation.tolerance` no viene en el payload. |

Nota operativa: `ir.config_parameter` cachea sus valores en memoria; un
cambio hecho por SQL directo (fuera del ORM) no se refleja hasta que se
invalide el caché o se reinicie el proceso.

## Cómo correr los tests

Entorno real (`docker-compose.yml`/`entrypoint.sh` en la raíz del proyecto):
contenedor Odoo `gauchocode/docker-odoo:16.0`, Postgres accesible como host
`postgres` (usuario/clave `odoo`/`odoo` en este entorno de desarrollo), config
en `/var/lib/odoo/odoo.conf` (con `db_host=localhost`, por lo que hay que
sobrescribirlo con `--db_host=postgres` al ejecutar `odoo` a mano, ya que el
`entrypoint.sh` lo hace automáticamente al arrancar el contenedor).

Contenedor observado en este entorno: `potenciar_qwerty_dev-odoo-1`, base
`qwerty_dev`.

```bash
docker exec <contenedor_odoo> odoo \
  -c /var/lib/odoo/odoo.conf \
  --db_host=postgres --db_port=5432 --db_user=odoo --db_password=odoo \
  -d <nombre_base> \
  -u gc_odoo_purchase_invoice_import_api \
  --test-enable \
  --test-tags /gc_odoo_purchase_invoice_import_api \
  --stop-after-init \
  --no-http --workers=0 \
  --log-level=test
```

Usar `-i` en vez de `-u` la primera vez (módulo no instalado todavía).
`--no-http --workers=0` evita el conflicto de puerto con el proceso Odoo que
ya está corriendo en el contenedor.

`test_payload_validator.py` corre como `unittest.TestCase` puro (sin acceso a
Odoo, usa ids ficticios de `tests/fixtures/valid_v01_single_line.json` tal
cual) y `test_invoice_importer.py` como `TransactionCase` (crea sus propios
records en `setUpClass` e inyecta esos ids reales en una copia del fixture);
ambos se descubren y ejecutan con el mismo comando de arriba.

## Ejemplo `curl`

```bash
curl -X POST http://localhost:8069/api/v1/purchase-invoices \
  -u "servicio_proveedor:<contraseña>" \
  -H "Content-Type: application/json" \
  -d @tests/fixtures/valid_v01_single_line.json
```

(Ajustar los ids bajo `odoo.*` a records reales de la base destino antes de
probar contra un servidor real.)

Ver `DECISIONES.md` para el detalle de decisiones técnicas, limitaciones y
puntos pendientes de confirmación con el cliente.
