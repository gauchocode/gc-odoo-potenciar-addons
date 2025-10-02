==================================
Filtro de Cuentas Analíticas en Facturas
==================================

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
    :target: https://github.com/GauchoCode/gc-odoo-potenciar-addons/tree/16.0/gc_odoo_analityc_filter
    :alt: GauchoCode/gc-odoo-potenciar-addons

|badge1| |badge2| |badge3|

Este módulo permite filtrar y visualizar las cuentas analíticas en las facturas de Odoo, 
mejorando la gestión de la contabilidad analítica y facilitando el seguimiento de proyectos
y centros de costos.

**Tabla de contenidos**

.. contents::
   :local:

Descripción General
===================

El módulo `gc_odoo_analityc_filter` extiende la funcionalidad estándar de Odoo para 
proporcionar capacidades mejoradas de filtrado y visualización de cuentas analíticas 
en las facturas. Esto permite a los usuarios tener un mejor control sobre la contabilidad 
analítica y facilita el análisis de costos por proyecto o departamento.

Características
===============

* **Campo computed de cuentas analíticas**: Agrega un campo Many2many que recopila automáticamente todas las cuentas analíticas de las líneas de factura
* **Filtrado en vista de lista**: Permite filtrar facturas por cuentas analíticas directamente desde la vista de lista
* **Búsqueda mejorada**: Incluye las cuentas analíticas en los criterios de búsqueda de facturas
* **Visualización con etiquetas**: Muestra las cuentas analíticas como etiquetas en la vista de lista para una mejor visualización
* **Actualización automática**: Se actualiza automáticamente cuando se modifican las líneas de factura

Uso
===

Visualización en Vista de Lista
-------------------------------

1. Vaya a **Contabilidad** > **Clientes** > **Facturas** o **Proveedores** > **Facturas**
2. En la vista de lista, verá una nueva columna "Etiquetas analíticas" que muestra todas las cuentas analíticas asociadas a cada factura
3. Por defecto, esta columna está oculta. Puede mostrarla usando el menú de opciones de columnas

Filtrado por Cuentas Analíticas
-------------------------------

1. En la vista de lista de facturas, haga clic en el icono de búsqueda/filtro
2. En el campo "Etiquetas analíticas", escriba el nombre de la cuenta analítica por la que desea filtrar
3. El sistema mostrará solo las facturas que contengan esa cuenta analítica en cualquiera de sus líneas

Comportamiento Automático
-------------------------

* Cuando se crean o modifican líneas de factura con cuentas analíticas, el campo se actualiza automáticamente
* El campo es de solo lectura y se calcula en base a las cuentas analíticas de todas las líneas de la factura
* No se copia cuando se duplica una factura para evitar inconsistencias

Instalación
===========

Para instalar este módulo:

1. Descargue o clone el repositorio en su directorio de addons de Odoo
2. Asegúrese de que el módulo base `account` esté instalado
3. Actualice la lista de aplicaciones en Odoo
4. Busque "Filtro segun cuentas analiticas en facturas" en la lista de aplicaciones
5. Haga clic en "Instalar"

Requisitos
----------

* Odoo 16.0
* Módulo `account` (incluido en Odoo core)

Seguimiento de Errores
======================

Los errores/problemas se rastrean en `GitHub Issues <https://github.com/GauchoCode/gc-odoo-potenciar-addons/issues>`_.
En caso de problemas, por favor verifique si su problema ya ha sido reportado.
Si fue el primero en descubrirlo, ayúdenos a solucionarlo proporcionando una descripción detallada
`aquí <https://github.com/GauchoCode/gc-odoo-potenciar-addons/issues/new?body=módulo:%20gc_odoo_analityc_filter%0Aversión:%2016.0.1.0.1%0A%0A**Pasos%20para%20reproducir**%0A-%20...%0A%0A**Comportamiento%20actual**%0A%0A**Comportamiento%20esperado**>`_.

No olvide:

* proporcionar una descripción detallada del problema
* incluir los pasos para reproducir el error
* mencionar la versión de Odoo que está utilizando
* adjuntar logs relevantes si es posible

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