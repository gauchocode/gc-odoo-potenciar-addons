# Importador de facturas de venta (Excel)

## Nota funcional: Condición de cobro

- **No** se asigna `invoice_payment_term_id` desde el Excel en la creación de facturas.
- La condición de cobro se considera un dato del contacto y se gestiona en el campo:
  - `payment_condition_id` (partner/contacto)
- Por lo tanto, al asignar el contacto en la factura, la condición se hereda desde ese contacto.

Este criterio se dejó intencionalmente así para esta etapa.

