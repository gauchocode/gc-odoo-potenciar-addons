# Decisiones — GC Odoo Purchase Invoice Import API

## Contrato v0.1 (Radiant / "Looking for Trouble")

El contrato original (`comprobante`/`items`/`totales`/`document_id`) se
reemplazó por completo: era un prototipo sin remitente real. El nuevo
contrato lo define el integrador Radiant ("Looking for Trouble"): manda la
factura **ya mapeada** a IDs de Odoo por línea y por bloque, bajo la clave
`odoo` de cada sección (`partner.odoo.partner_id`,
`lines[].odoo.product_id/account_id/tax_ids/uom_id/analytic_distribution`,
`target.company_id/journal_id`, `document.odoo.document_type_id/currency_id`).

### Decisión: confiar en los IDs de Odoo, riesgo aceptado

Se decidió **no** resolver ni corregir esos IDs del lado de Odoo (no se
busca el producto por código, no se valida coherencia CUIT↔condición de
IVA, no se recalculan impuestos). Solo se verifica que cada id referenciado
EXISTA (`browse().exists()`); si falta alguno, `400 validation_error`
listando cuáles, sin crear nada.

**Riesgo aceptado explícitamente**: si el proveedor manda un `product_id`
o `account_id` que existe pero es semánticamente incorrecto (producto
equivocado, cuenta de otro rubro, impuesto con alícuota distinta a la
declarada), Odoo no lo detecta — la factura se crea igual. La única red de
seguridad indirecta es el chequeo `odoo_total` post-creación (ver más
abajo): si el error de mapeo cambia el total de la factura, ahí sí se nota
la diferencia contra `totals.total_amount` y se aplica la política de
tolerancia. Un error que no cambie el total (ej. account_id de otro rubro
con el mismo importe) **no se detecta**. Esto es una decisión de negocio
tomada explícitamente por el cliente, no un descuido: el mapeo por reglas
(`lines[].odoo.mapping`) es responsabilidad del lado de Radiant.

### Política `policy_if_missing`

Si `partner.odoo.partner_id` no viene informado:

- `"create"`: se busca primero por CUIT normalizado entre los `res.partner`
  existentes (reusa la lógica de `PartnerResolver`, sin filtrar por
  `supplier_rank`, mismo hallazgo que en el prototipo anterior). Si hay
  match, se usa ese contacto (sin crear nada nuevo). Si no hay match, se
  crea un `res.partner` nuevo desde el bloque `partner` del payload y se
  agrega un warning `"Contacto creado: ..."`.
- cualquier otro valor (`"review"`, ausente, o cualquier string no
  reconocido): no se crea la factura ni el contacto. Se responde
  `422 pending_review` (nuevo estado de log `pending_review`). Se eligió
  422 sobre 202 porque la request no fue "aceptada para procesamiento
  asíncrono" (no hay cola): quedó bloqueada por una condición del negocio
  que requiere intervención humana, semánticamente más cerca de
  "Unprocessable Entity" que de "Accepted".

Campos verificados contra el código real de Odoo 16 de este entorno antes
de usarlos en la creación del contacto:
`res.partner.l10n_latam_identification_type_id` (vía `l10n_latam_base`,
confirmado en `l10n_latam_base/models/res_partner.py`) y
`res.partner.l10n_ar_afip_responsibility_type_id` (vía `l10n_ar`, confirmado
en `l10n_ar/models/res_partner.py`). El tipo de identificación se fija
siempre a `env.ref('l10n_ar.it_cuit')` (no se resuelve dinámicamente desde
`partner.odoo.identification_type`, que hoy solo trae `"CUIT"`).
`partner.odoo.state_id`, a diferencia del resto de los ids del payload, se
usa con degradación silenciosa (`if state.exists()`) en vez de bloquear con
400: es un dato secundario solo para la creación del contacto, no crítico
para la factura.

### Validación propia de montos vs. `validation.checks` del proveedor

`validation.checks` (y `is_clean`, `observations`) del payload son
**puramente informativos**: se guardan en el log (`provider_checks`) pero
nunca se usan para decidir nada. Esta API recalcula sus propios 5 chequeos
(`our_checks` en el log, `checks` en la respuesta):

| code | fórmula |
|---|---|
| `lines_vs_net` | Σ(`quantity * unit_price`) de todas las líneas vs. `totals.net_amount` |
| `line_subtotal[N]` | `quantity * unit_price` de la línea N vs. `lines[N].subtotal` (si vino informado) |
| `vat_total` | Σ(`taxes.vat[].amount`) vs. `totals.vat_amount` |
| `total` | ver fórmula abajo vs. `totals.total_amount` |
| `odoo_total` | `move.amount_total` (factura YA CREADA en Odoo) vs. `totals.total_amount` |

**Fórmula del check `total`** (decisión explícita, documentada porque el
payload no la deja 100% inequívoca): `totals.net_amount + totals.vat_amount
+ totals.perceptions_amount + totals.internal_taxes_amount +
taxes.exempt_amount + taxes.non_taxed_amount`. Los primeros cuatro salen del
bloque `totals` (que no tiene `exempt_amount`/`non_taxed_amount`); esos dos
últimos salen del bloque `taxes` (que sí los tiene, y no los duplica en
`totals`). Verificado contra el ejemplo del ticket: con `exempt_amount` y
`non_taxed_amount` en 0, `13130706.60 + 2757448.39 + 0 + 0 + 0 + 0 =
15888154.99 = totals.total_amount` exacto (diff 0), confirmado también por
test (`test_total_formula_matches_example_cleanly`).

**Tolerancia**: `validation.tolerance` del payload si es numérico; si no,
`ir.config_parameter` `gc_odoo_purchase_invoice_import_api.total_tolerance`
(default `1.0`). Regla uniforme para los 5 checks: diferencia `<= tolerancia`
→ el check pasa (`passed: true`), pero si la diferencia es `> 0` igual se
agrega una advertencia informativa (aunque pase). Diferencia `> tolerancia`
→ depende de `validation.action_if_exceeded`: `"observation"` (default)
agrega advertencia y marca `has_observations=true` en el log, pero crea la
factura igual; `"reject"` bloquea. Para los 4 checks pre-creación, "bloquear"
significa `400 validation_error` sin crear nada. Para `odoo_total`
(post-creación), significa **revertir** la factura recién creada.

### `odoo_total` post-creación: savepoint + rollback

El único chequeo que necesita la factura ya creada (`move.amount_total`,
que Odoo calcula según los impuestos REALES aplicados, no los declarados en
`taxes.vat`) se hace después del `account.move.create(...)`. Si
`action_if_exceeded == "reject"` y la diferencia supera la tolerancia, hace
falta deshacer la creación sin abortar toda la transacción HTTP (el log ya
escrito antes tiene que sobrevivir). Se resuelve con un savepoint explícito:

```python
with self.env.cr.savepoint():
    move = self.env['account.move'].with_company(...).sudo().create(move_vals)
    if attachment_data:
        attachment = self._create_attachment(move, attachment_data)
    # calcula el check odoo_total; si excede tolerancia y action_if_exceeded
    # == 'reject', levanta una excepción interna (_RejectedByTolerance)
```

Al levantar la excepción dentro del `with`, `cr.savepoint()` hace
`ROLLBACK TO SAVEPOINT` en su `__exit__` (comportamiento estándar de
`odoo/sql_db.py`) antes de repropagar; se captura afuera del `with` y se
escribe el log como `validation_error` sin `move`. El adjunto (creado
dentro del mismo savepoint) se revierte junto con la factura: no queda un
`ir.attachment` huérfano. Cubierto por
`test_odoo_total_mismatch_with_reject_rolls_back`.

### Duplicados: sigue el mismo mecanismo que el prototipo anterior

`l10n_latam_document_number` sigue siendo un campo `compute` **sin**
`store=True` en `l10n_latam_invoice_document/models/account_move.py`
(confirmado en este mismo entorno). Buscarlo por `domain` de `search()`
no filtra nada (Odoo lo reemplaza por un dominio vacío). `DuplicateChecker`
sigue trayendo los candidatos por los campos sí buscables
(`commercial_partner_id`, `move_type`, `l10n_latam_document_type_id`,
`state != cancel`) y filtra `l10n_latam_document_number` en memoria. La
diferencia con el prototipo anterior es que `move_type` ya no se deriva de
`document_type.internal_type`: viene directo y confiado desde
`target.move_type` (solo `in_invoice`/`in_refund` permitidos).

`source.idempotency_key` y `source.invoice_id` se guardan en el log
(`idempotency_key`, `source_invoice_id`) solo para trazabilidad; la regla
funcional de duplicado sigue siendo contacto + punto de venta + número, no
el idempotency_key (dos requests con distinto idempotency_key pero mismo
documento AR siguen detectándose como duplicados entre sí, que es lo
correcto).

### `final_state`: siempre se crea en borrador

Se ignora el valor de `target.final_state`: la factura **siempre** se crea
en `draft`, nunca se llama `action_post()`. Si `final_state != "draft"`, se
agrega un warning explicando que el posteo automático está deshabilitado en
esta integración, para que quien mire la respuesta no asuma que se posteó
solo porque el proveedor lo pidió.

### PDF: validación y redacción

Si `attachment.content_base64` viene informado, se valida (Python puro,
sin Odoo) que decodifique como Base64 válido (`base64.b64decode(...,
validate=True)`) y que sea un PDF real: `mime_type == "application/pdf"` Y
los bytes decodificados empiezan con `b'%PDF'` (magic bytes). Cualquier
falla → `400 validation_error` antes de crear nada. Si es válido, se crea
un `ir.attachment` (`res_model='account.move'`, `res_id=move.id`) y se
setea `move.message_main_attachment_id`; el log guarda el `Many2one` al
adjunto (`attachment_id`).

**El base64 completo nunca se guarda en `raw_payload`**: `InvoiceImporter`
redacta el payload antes de loguearlo (`content_base64` →
`"<omitted N bytes>"`, con N = tamaño real decodificado) para no duplicar el
archivo (ya vive en `ir.attachment`) ni inflar el log. Cubierto por
`test_raw_payload_redacts_base64_content`.

## Decisiones heredadas del prototipo original (siguen vigentes)

### Auth: usuario y contraseña de Odoo (no OAuth)
Sin cambios: `res.users.authenticate(db, login, password, {'interactive':
False})`, sin `database` en el body (siempre `request.db`/`request.env`).
Ver README para el trade-off documentado (rotar contraseña de usuario humano
rompe la integración) y la recomendación de usuario de servicio dedicado.

### Códigos HTTP
`201` creada / `200` duplicado / `400` validation_error / `401` auth /
`422` **ahora también** cubre `pending_review` (antes era exclusivo de
`configuration_error`, que se eliminó — ver abajo) / `500` processing_error.
**`404` se eliminó**: ya no hay ningún caso que lo devuelva (antes era
"proveedor no encontrado", que ahora es `pending_review` 422 o creación
automática, según `policy_if_missing`).

## Limitaciones vigentes

- **`taxes.perceptions` no se mapea a impuestos de Odoo**: el contrato v0.1
  trae un arreglo `perceptions` en el bloque `taxes`, pero como el mapeo de
  percepciones no está definido todavía (no hay `odoo_tax_id` ni línea de
  impuesto asociada), esta API **no genera líneas de percepción en la
  factura**. Si `perceptions_amount`/`taxes.perceptions` viene con importe
  no-cero, el check `total` lo va a incluir en el monto ESPERADO, pero
  `move.amount_total` (el check `odoo_total`) no lo va a tener, porque Odoo
  nunca vio esa percepción. Esto hace divergir sistemáticamente el check
  `odoo_total` en cualquier factura con percepciones. **Tratamiento
  elegido**: se deja que el check `odoo_total` lo reporte como observación
  (comportamiento estándar de la tolerancia), no se bloquea ni se oculta.
  Pendiente de definición con el cliente: si hay que mapear percepciones a
  líneas de impuesto/cuenta específicas antes de ir a producción con
  proveedores que las usen.
- No hay journal explícito más allá del que manda `target.journal_id`
  (confiado, no se valida que sea de tipo `purchase`).
- No se valida país/compañía del `l10n_latam.document.type` contra la
  compañía activa (`target.company_id`).
- Sin reintentos asíncronos ni colas: cada request se procesa de forma
  síncrona en la misma transacción HTTP.

## Fuera de alcance (pendiente de confirmación con el cliente)

- **Pruebas con los 4 JSON reales de Looking for Trouble**: al momento de
  este cambio todavía no se recibieron, ver `tests/fixtures/`. Los fixtures
  actuales son fieles al ejemplo del ticket pero no fueron validados contra
  payloads reales del integrador. Antes de ir a producción, correr al menos
  los 4 JSON reales contra un ambiente de staging y ajustar lo que
  corresponda.
- Percepciones no mapeadas a impuestos de Odoo (ver Limitaciones).
- Sin publicación automática de la factura (`action_post()` explícitamente
  prohibido).
- Sin política definitiva sobre qué hacer cuando `odoo_total` diverge de
  forma sistemática por percepciones no mapeadas (hoy: observación).
