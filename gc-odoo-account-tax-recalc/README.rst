================================================
Control de Recálculo Automático de Impuestos
================================================

.. !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
   !! Este archivo es generado por oca-gen-addon-readme !!
   !! cambios sobre escribirse.                         !!
   !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

.. |badge1| image:: https://img.shields.io/badge/maturity-Beta-yellow.png
    :target: https://odoo-community.org/page/development-status
    :alt: Beta
.. |badge2| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3
.. |badge3| image:: https://img.shields.io/badge/github-GauchoCode%2Fgc--odoo--potenciar--addons-lightgray.png?logo=github
    :target: https://github.com/GauchoCode/gc-odoo-potenciar-addons/tree/16.0/gc-odoo-account-tax-recalc
    :alt: GauchoCode/gc-odoo-potenciar-addons

|badge1| |badge2| |badge3|

Este módulo permite a los usuarios controlar el recálculo automático de impuestos en las facturas de Odoo, proporcionando la flexibilidad de editar manualmente los montos de impuestos cuando sea necesario, especialmente útil para facturas de proveedores y casos especiales.

**Tabla de contenidos**

.. contents::
   :local:

Descripción General
===================

El módulo `gc-odoo-account-tax-recalc` soluciona una limitación común en Odoo donde los usuarios no pueden modificar manualmente los montos de impuestos calculados automáticamente. Esto es especialmente problemático cuando se necesita:

- Ajustar impuestos en facturas de proveedores que no coinciden exactamente con los cálculos automáticos
- Corregir diferencias por redondeo
- Aplicar ajustes específicos requeridos por la contabilidad
- Manejar casos especiales donde el cálculo automático no es apropiado

El módulo introduce un control de toggle que permite activar/desactivar el recálculo automático por documento, manteniendo un snapshot de los valores editados manualmente.

Características
===============

* **Control granular por documento**: Toggle para habilitar/deshabilitar el recálculo automático en cada factura individual
* **Configuración por defecto inteligente**:
  
  - Facturas de cliente: Recálculo automático **activado** (comportamiento estándar)
  - Facturas de proveedor: Recálculo automático **desactivado** (permite edición manual)

* **Sistema de snapshot**: Preserva los valores editados manualmente mediante un sistema de instantáneas JSON
* **Integración transparente**: Funciona con el widget tax_totals existente sin romper la funcionalidad estándar
* **Banner de advertencia**: Recordatorio visual para guardar cambios cuando el recálculo automático está desactivado
* **Preservación de datos**: Los valores editados manualmente se mantienen al reabrir el documento
* **Compatible con workflows existentes**: No interfiere con procesos automáticos cuando está activado

Uso
===

Control del Recálculo Automático
--------------------------------

1. Abra cualquier factura (cliente o proveedor)
2. En la parte superior derecha, junto al campo "Para verificar", verá el toggle "Recalcular autom. de impuestos"
3. **Estado ON (activado)**: Comportamiento estándar de Odoo - los impuestos se recalculan automáticamente
4. **Estado OFF (desactivado)**: Permite edición manual de los montos de impuestos

Edición Manual de Impuestos
---------------------------

Para editar manualmente los impuestos:

1. **Desactive** el toggle "Recalcular autom. de impuestos"
2. Aparecerá un banner de advertencia recordando guardar los cambios
3. **Guarde** el documento (Ctrl+S o botón Guardar)
4. Edite los montos de impuestos en el widget tax_totals
5. **Guarde nuevamente** para preservar los cambios

.. warning::
   Es fundamental guardar el documento antes y después de modificar los impuestos cuando el recálculo automático está desactivado.

Comportamiento por Tipo de Documento
------------------------------------

**Facturas de Cliente** (por defecto):
- Recálculo automático: **Activado**
- Comportamiento: Estándar de Odoo
- Uso típico: Mantener activado para cálculos automáticos precisos

**Facturas de Proveedor** (por defecto):
- Recálculo automático: **Desactivado**
- Comportamiento: Permite edición manual
- Uso típico: Ajustar impuestos para que coincidan con la factura del proveedor

Casos de Uso Típicos
====================

Facturas de Proveedores
-----------------------

**Problema**: La factura del proveedor muestra $100 + $21 IVA = $121, pero Odoo calcula $100 + $21.50 IVA = $121.50

**Solución**:
1. La factura de proveedor abre con recálculo automático OFF
2. Edite el monto del IVA de $21.50 a $21.00
3. El total se ajusta automáticamente a $121.00

Ajustes por Redondeo
-------------------

**Problema**: Diferencias mínimas por redondeo que afectan la conciliación

**Solución**:
1. Desactive el recálculo automático
2. Ajuste los montos para que coincidan exactamente
3. Los valores se preservan automáticamente

Casos Especiales de Impuestos
-----------------------------

**Problema**: Aplicación de exenciones o tratamientos fiscales especiales

**Solución**:
1. Configure los impuestos base con el recálculo activado
2. Desactive el recálculo para ajustes finales
3. Edite manualmente según los requisitos específicos

Aspectos Técnicos
=================

Sistema de Snapshot
------------------

El módulo utiliza un campo `tax_totals_snapshot` que almacena en formato JSON los valores de impuestos:

- Se actualiza automáticamente cuando el recálculo está activado
- Se preserva cuando el recálculo está desactivado
- Permite restaurar valores editados manualmente

Integración con tax_totals
-------------------------

- Extiende los métodos `_compute_tax_totals()` e `_inverse_tax_totals()`
- No modifica la estructura de datos original
- Mantiene compatibilidad con widgets y funcionalidades existentes

Campos Agregados
---------------

- `automatic_tax_recalculation`: Boolean toggle para controlar el recálculo
- `tax_totals_snapshot`: Text field para almacenar el snapshot JSON

Instalación
===========

Para instalar este módulo:

1. Descargue o clone el repositorio en su directorio de addons de Odoo
2. Asegúrese de que el módulo base `account` esté instalado
3. Actualice la lista de aplicaciones en Odoo
4. Busque "Account Move – Control Recalculo Automático de Impuestos" en la lista de aplicaciones
5. Haga clic en "Instalar"

Requisitos
----------

* Odoo 16.0
* Módulo `account` (incluido en Odoo core)

Configuración
=============

El módulo no requiere configuración adicional después de la instalación. Los valores por defecto se aplicarán automáticamente:

- Facturas de cliente: Recálculo automático activado
- Facturas de proveedor: Recálculo automático desactivado

Post-instalación
----------------

Después de la instalación, se ejecuta automáticamente un hook que establece los valores por defecto para documentos existentes.

Migración de Datos Existentes
-----------------------------

Los documentos existentes mantendrán su comportamiento actual. El toggle estará:

- **Activado** para facturas de cliente existentes
- **Desactivado** para facturas de proveedor existentes

Seguimiento de Errores
======================

Los errores/problemas se rastrean en `GitHub Issues <https://github.com/GauchoCode/gc-odoo-potenciar-addons/issues>`_.
En caso de problemas, por favor verifique si su problema ya ha sido reportado.
Si fue el primero en descubrirlo, ayúdenos a solucionarlo proporcionando una descripción detallada
`aquí <https://github.com/GauchoCode/gc-odoo-potenciar-addons/issues/new?body=módulo:%20gc-odoo-account-tax-recalc%0Aversión:%2016.0.1.0%0A%0A**Pasos%20para%20reproducir**%0A-%20...%0A%0A**Comportamiento%20actual**%0A%0A**Comportamiento%20esperado**>`_.

No olvide incluir:

* Descripción detallada del problema
* Tipo de documento (factura cliente/proveedor)
* Estado del toggle de recálculo automático
* Pasos para reproducir el error
* Screenshots si el problema es visual
* Logs de Odoo si hay errores técnicos

Problemas Conocidos / Hoja de Ruta
===================================

Limitaciones Actuales
---------------------

* **Requiere guardar manualmente**: Es necesario guardar antes y después de editar impuestos cuando el recálculo está desactivado
* **Solo facturas**: Actualmente solo funciona con documentos tipo factura (account.move)

Buenas Prácticas
----------------

* Siempre guarde el documento antes de modificar impuestos con recálculo desactivado
* Use el recálculo automático desactivado solo cuando sea necesario
* Documente los ajustes manuales en las notas internas del documento

Hoja de Ruta
------------

* Mejora de la UX para eliminar la necesidad de guardar manualmente
* Soporte para otros tipos de documentos contables
* Registro de auditoría para cambios manuales en impuestos
* Configuración global por empresa para valores por defecto

Créditos
========

Autores
-------

* GauchoCode

Contribuidores
--------------

* GauchoCode <info@gauchocode.com>

Mantenedores
------------

Este módulo es mantenido por GauchoCode.

.. image:: https://avatars.githubusercontent.com/u/gauchocode
   :alt: GauchoCode
   :target: https://github.com/GauchoCode

GauchoCode es una empresa especializada en el desarrollo y personalización de 
soluciones Odoo para empresas de América Latina, con experiencia particular 
en localización contable y fiscal.