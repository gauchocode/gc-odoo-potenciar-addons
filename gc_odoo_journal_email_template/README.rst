======================================
Plantillas de Correo Electrónico por Diario
======================================

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
    :target: https://github.com/GauchoCode/gc-odoo-potenciar-addons/tree/16.0/gc_odoo_journal_email_template
    :alt: GauchoCode/gc-odoo-potenciar-addons

|badge1| |badge2| |badge3|

Este módulo permite definir y asociar plantillas de correo electrónico personalizadas a los diarios contables en Odoo. De esta manera, al enviar facturas o documentos desde un diario específico, se puede utilizar automáticamente la plantilla de correo configurada para ese diario.

**Tabla de contenidos**

.. contents::
   :local:

Descripción General
===================

El módulo `gc_odoo_journal_email_template` extiende la funcionalidad estándar de Odoo para permitir la asociación de plantillas de correo electrónico específicas a cada diario contable. Esto es especialmente útil para empresas que manejan múltiples líneas de negocio o tipos de servicios que requieren comunicaciones personalizadas con sus clientes.

Características
===============

* **Plantillas por diario**: Permite asignar una plantilla de correo electrónico específica a cada diario contable
* **Selección automática**: Al enviar facturas desde un diario, se utiliza automáticamente la plantilla asignada a ese diario
* **Plantillas predefinidas**: Incluye plantillas preconfiguratas para diferentes tipos de servicios:
  
  - Factura - Ventas #5 MAV
  - Factura - Ventas #6 PTMOS (con información bancaria detallada)
  - Factura - Ventas #7 PROT (para servicios de protesto)

* **Integración transparente**: Se integra perfectamente con el flujo estándar de envío de facturas de Odoo
* **Dominio específico**: Solo permite seleccionar plantillas válidas para el modelo `account.move`
* **Configuración sencilla**: Interfaz amigable para la configuración de plantillas por diario

Uso
===

Configuración de Plantillas por Diario
--------------------------------------

1. Vaya a **Contabilidad** > **Configuración** > **Diarios**
2. Seleccione el diario que desea configurar
3. En la pestaña de configuración, encontrará el campo "Default Email Template for Invoices"
4. Seleccione la plantilla de correo electrónico que desea usar para este diario
5. Guarde los cambios

Envío de Facturas con Plantilla Automática
-------------------------------------------

1. Vaya a **Contabilidad** > **Clientes** > **Facturas** (o cualquier vista de facturas)
2. Seleccione la factura que desea enviar
3. Haga clic en "Enviar & Imprimir" o "Enviar por correo"
4. El sistema automáticamente seleccionará la plantilla configurada para el diario de la factura
5. Puede modificar el contenido si es necesario antes de enviar
6. Confirme el envío

Plantillas Predefinidas
-----------------------

El módulo incluye tres plantillas predefinidas:

**Factura - Ventas #5 MAV**
  Plantilla básica para servicios de garantía con información de contacto estándar.

**Factura - Ventas #6 PTMOS**
  Plantilla específica para préstamos que incluye:
  
  - Información bancaria completa para pagos
  - Detalles sobre débitos automáticos
  - Información sobre exención de retenciones
  - Datos de CBU, alias y cuenta corriente

**Factura - Ventas #7 PROT**
  Plantilla para servicios de protesto con información bancaria básica.

Instalación
===========

Para instalar este módulo:

1. Descargue o clone el repositorio en su directorio de addons de Odoo
2. Asegúrese de que los módulos base `account` y `account_ux` estén instalados
3. Actualice la lista de aplicaciones en Odoo
4. Busque "Template de Correo Electrónico segun diario" en la lista de aplicaciones
5. Haga clic en "Instalar"

Requisitos
----------

* Odoo 16.0
* Módulo `account` (incluido en Odoo core)
* Módulo `account_ux` (OCA/account-financial-tools)

Configuración
=============

Después de la instalación:

1. Las plantillas predefinidas se crearán automáticamente
2. Configure cada diario con la plantilla deseada siguiendo las instrucciones de uso
3. Las plantillas pueden personalizarse desde **Configuración** > **Técnico** > **Correo electrónico** > **Plantillas**

Seguimiento de Errores
======================

Los errores/problemas se rastrean en `GitHub Issues <https://github.com/GauchoCode/gc-odoo-potenciar-addons/issues>`_.
En caso de problemas, por favor verifique si su problema ya ha sido reportado.
Si fue el primero en descubrirlo, ayúdenos a solucionarlo proporcionando una descripción detallada
`aquí <https://github.com/GauchoCode/gc-odoo-potenciar-addons/issues/new?body=módulo:%20gc_odoo_journal_email_template%0Aversión:%2016.0.1.0.3%0A%0A**Pasos%20para%20reproducir**%0A-%20...%0A%0A**Comportamiento%20actual**%0A%0A**Comportamiento%20esperado**>`_.

No olvide:

* proporcionar una descripción detallada del problema
* incluir los pasos para reproducir el error
* mencionar la versión de Odoo que está utilizando
* especificar qué plantilla y diario está usando
* adjuntar logs relevantes si es posible

Problemas Conocidos / Hoja de Ruta
===================================

* Las plantillas predefinidas están en español y están específicamente diseñadas para POTENCIAR SGR
* Para uso en otras empresas, será necesario personalizar las plantillas predefinidas

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
soluciones Odoo para empresas de América Latina.