================================
Tasas de Cambio para Argentina
================================

Sincroniza diariamente las tasas de cambio de Odoo desde distintos
proveedores. La configuración se realiza directamente en cada moneda.

Proveedores
===========

* BNA - Cotizador Histórico
* BCRA - Estadísticas Cambiarias
* DolarAPI

Configuración
=============

En **Contabilidad > Configuración > Monedas**, abra la moneda que desea
sincronizar y complete:

* **Proveedor de cotización**.
* **Moneda en el proveedor**: opción disponible para el proveedor seleccionado.
* **Valor a utilizar**: compra, venta o promedio compra/venta.

Ejemplos de identificadores:

* BNA: ``Dolar U.S.A``, ``Euro`` o ``YENES``.
* BCRA: código ISO como ``USD`` o ``EUR``.
* DolarAPI: combinación moneda/mercado como ``USD:oficial``, ``USD:blue`` o
  ``EUR:oficial``.

La acción programada **Actualizar cotizaciones de monedas** obtiene cada
proveedor una sola vez y actualiza todas las monedas configuradas.
