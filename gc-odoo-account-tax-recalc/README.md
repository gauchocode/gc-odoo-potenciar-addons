# gc-odoo-account-tax-recalc

Módulo Odoo para el control y recálculo manual de impuestos en facturas.

## Descripción

Este módulo agrega controles adicionales en el formulario de facturas (`account.move`) para permitir al usuario activar o desactivar el recálculo automático de impuestos. Además, muestra un banner de advertencia cuando el recálculo automático está desactivado, recordando al usuario que debe guardar los cambios antes y después de modificar los impuestos manualmente.

## Características

- **Campo booleano**: Permite activar/desactivar el recálculo automático de impuestos en cada factura.
- **Banner de advertencia**: Se muestra cuando el recálculo automático está desactivado, indicando al usuario que debe guardar los cambios manualmente.
- **Integración nativa**: Hereda la vista estándar de facturas de Odoo, agregando los controles de manera no intrusiva.

## Instalación

1. Copiar el módulo a la carpeta de addons de Odoo.
2. Actualizar la lista de aplicaciones.
3. Instalar el módulo **gc-odoo-account-tax-recalc** desde el backend de Odoo.

## Uso

1. Ingresar a una factura (modelo `account.move`).
2. Utilizar el switch "Recalcular autom. de impuestos" para activar o desactivar el recálculo automático.
3. Si el recálculo está desactivado, aparecerá un banner de advertencia en la parte superior del formulario.

## Estructura
