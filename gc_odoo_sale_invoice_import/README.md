# Importador de facturas de venta (Excel)

## Nota funcional: Condición de cobro

- **No** se asigna `invoice_payment_term_id` desde el Excel en la creación de facturas.
- La condición de cobro se considera un dato del contacto y se gestiona en el campo:
  - `payment_condition_id` (partner/contacto)
- Por lo tanto, al asignar el contacto en la factura, la condición se hereda desde ese contacto.

Este criterio se dejó intencionalmente así para esta etapa.

## Nota funcional: Analíticos

- Las columnas K, L, M y N del Excel determinan los analíticos de las líneas de factura.
- Si una de esas celdas está vacía, no se asigna nada para esa columna.
- Si tiene valor, el importador busca ese valor contra `account.analytic.account` por nombre, código o display name.
- Cuando el encabezado de la columna coincide con un plan analítico, la búsqueda se restringe a ese plan. Por ejemplo, `Analitico DOC` busca el valor de K dentro del plan `DOC`.
- Cuando encuentra los analíticos, los asigna al 100% en cada línea importada mediante `analytic_distribution`.

## Tipo de importación: CPD

El tipo **CPD** usa el formato corregido de 20 columnas: Fecha FC, Desde, Hasta, CUIT, Denominación, Comentario, Tipo Cambio, Moneda, Diario, Condición de Cobro, Analitico DOC, Analitico COME, Analitico CONV, Analitico ALYC, VALOR AVALADO, %, EXENTO Comision [000005], GRAVADO Liq Prod [000012], IVA (21%) y TOTAL.

Reglas CPD:

- Las filas de encabezado repetidas se omiten cuando la columna A es `Fecha FC`.
- El cliente se busca/crea con `CUIT` y `Denominación`.
- La fecha de factura se toma de `Fecha FC`.
- La columna Q crea una línea con producto `[000005]` **con IVA EXENTO**.
- La columna R crea una línea con producto `[000012]` **con IVA ventas 21%**.
- El importador valida que `EXENTO + GRAVADO + IVA = TOTAL` dentro de la tolerancia de redondeo de la moneda.
- `Condición de Cobro` mantiene el comportamiento general documentado arriba: no se asigna directamente en la factura.

Datos maestros requeridos para CPD: diario de ventas de la columna I, productos `000005`/`000012`, impuesto de venta del 21% y cuentas analíticas K-N cuando tengan valor.
