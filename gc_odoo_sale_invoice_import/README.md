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
