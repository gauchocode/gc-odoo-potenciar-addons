.. image:: https://img.shields.io/badge/github-gauchocode/gc--odoo--potenciar--addons-lightgray.png?logo=github
   :target: https://github.com/gauchocode/gc-odoo-potenciar-addons
   :alt: gauchocode/gc-odoo-potenciar-addons

Account Move – Control Recalculo Automático de Impuestos
=============================================================

Módulo Odoo para el control y recálculo manual de impuestos en facturas.

**Tabla de contenidos**

.. contents::
   :local:

Descripción
-----------

Este módulo agrega controles adicionales en el formulario de facturas
(`account.move`) para permitir al usuario activar o desactivar el recálculo
automático de impuestos. Muestra un banner de advertencia cuando el recálculo
automático está desactivado.

Características
-----------------

* Campo booleano para activar/desactivar el recálculo automático.
* Banner de advertencia si el recálculo está desactivado.
* Integración nativa con la vista de facturas de Odoo.

Instalación
------------

#. Copiar el módulo a la carpeta de addons de Odoo.
#. Actualizar la lista de aplicaciones.
#. Instalar el módulo *gc-odoo-account-tax-recalc* desde el backend de Odoo.

Uso
---

#. Ingresar a una factura (`account.move`).
#. Utilizar el switch **Recalcular autom. de impuestos** para activar o desactivar el recálculo.
#. Si el recálculo está desactivado, aparecerá un banner de advertencia.

Bug Tracker
-----------

Bugs are tracked on `GitHub Issues <https://github.com/gauchocode/gc-odoo-potenciar-addons/issues>`_.

Créditos
---------

Autores
~~~~~~~

* GauchoCode
