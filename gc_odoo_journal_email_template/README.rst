.. image:: https://img.shields.io/badge/github-gauchocode/gc--odoo--potenciar--addons-lightgray.png?logo=github
   :target: https://github.com/gauchocode/gc-odoo-potenciar-addons
   :alt: gauchocode/gc-odoo-potenciar-addons

gc-odoo-journal-email-template
==============================

Módulo Odoo para la gestión de plantillas de correo electrónico asociadas a diarios contables.

**Tabla de contenidos**

.. contents::
   :local:

Descripción
-----------

Este módulo permite definir y asociar plantillas de correo electrónico personalizadas a los diarios contables en Odoo. De esta manera, al enviar facturas o documentos desde un diario específico, se puede utilizar automáticamente la plantilla configurada para ese diario.

Características
-----------------

* Permite asignar una plantilla de correo electrónico a cada diario contable.
* Al enviar facturas desde un diario, se utiliza la plantilla asignada.
* Soporte multidioma (incluye traducción al español de Argentina).
* Integración transparente con el flujo estándar de envío de facturas.

Instalación
------------

#. Copiar el módulo a la carpeta de addons de Odoo.
#. Actualizar la lista de aplicaciones.
#. Instalar el módulo *gc-odoo-journal-email-template* desde el backend de Odoo.

Uso
---

#. Ir a **Contabilidad > Configuración > Diarios**.
#. Editar un diario y seleccionar la plantilla de correo electrónico deseada.
#. Al enviar una factura desde ese diario, se utilizará la plantilla configurada.

Bug Tracker
-----------

Bugs are tracked on `GitHub Issues <https://github.com/gauchocode/gc-odoo-potenciar-addons/issues>`_.

Créditos
---------

Autores
~~~~~~~

* GauchoCode
