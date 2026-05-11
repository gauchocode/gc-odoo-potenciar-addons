====================
Botón Grupos de Cuentas
====================

.. !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
   !! Este archivo es generado por oca-gen-addon-readme !!
   !! los cambios serán sobrescritos.                   !!
   !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

.. |badge1| image:: https://img.shields.io/badge/maturity-Beta-yellow.png
    :target: https://odoo-community.org/page/development-status
    :alt: Beta
.. |badge2| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: Licencia: AGPL-3
.. |badge3| image:: https://img.shields.io/badge/github-gauchocode%2Fgc--odoo--potenciar--addons-lightgray.png?logo=github
    :target: https://github.com/gauchocode/gc-odoo-potenciar-addons/tree/16.0/gc_odoo_account_group_button
    :alt: gauchocode/gc-odoo-potenciar-addons

|badge1| |badge2| |badge3|

Este módulo agrega un elemento de menú para acceder al modelo Grupos de Cuentas (account.group) directamente desde el menú de configuración de Contabilidad, proporcionando un acceso más fácil a la gestión de grupos de cuentas.

**Tabla de contenidos**

.. contents::
   :local:

Descripción General
===================

El módulo Botón Grupos de Cuentas mejora la interfaz de contabilidad de Odoo agregando un elemento de menú dedicado para gestionar Grupos de Cuentas. Esto proporciona a los usuarios acceso directo al modelo account.group desde el menú de configuración de Contabilidad.

Características
===============

* Agrega el elemento de menú "Grupos de Cuentas" en Contabilidad > Configuración
* Proporciona acceso a vistas de árbol y formulario del modelo account.group
* Incluye descripción útil para la gestión de grupos de cuentas
* Posicionado apropiadamente en la secuencia del menú

Uso
===

Después de instalar este módulo, encontrará un nuevo elemento de menú:

1. Vaya a **Contabilidad** > **Configuración** > **Grupos de Cuentas**
2. Desde aquí puede:
   * Ver todos los grupos de cuentas existentes en una vista de árbol
   * Crear nuevos grupos de cuentas
   * Editar grupos de cuentas existentes
   * Definir grupos de cuentas utilizados para propósitos de informes

El elemento de menú está posicionado con secuencia 25 en el menú de configuración de cuentas para una organización óptima.

Instalación
===========

Para instalar este módulo, necesita:

1. Asegurarse de que el módulo ``account_ux`` esté instalado (dependencia)
2. Instalar este módulo a través del menú de Aplicaciones de Odoo o colocándolo en su ruta de addons

Seguimiento de Errores
======================

Los errores se rastrean en `GitHub Issues
<https://github.com/gauchocode/gc-odoo-potenciar-addons/issues>`_. En caso de problemas, por favor
verifique allí si su problema ya ha sido reportado. Si lo detectó primero,
ayúdenos a solucionarlo proporcionando un
`feedback <https://github.com/gauchocode/gc-odoo-potenciar-addons/issues/new?body=module:%20gc_odoo_account_group_button%0Aversion:%2016.0%0A%0A**Pasos%20para%20reproducir**%0A-%20...%0A%0A**Comportamiento%20actual**%0A%0A**Comportamiento%20esperado**>`_ detallado y bien recibido.

No contacte a los contribuidores directamente sobre soporte o ayuda con problemas técnicos.

Créditos
========

Autores
~~~~~~~

* GauchoCode

Contribuidores
~~~~~~~~~~~~~~

* Equipo GauchoCode

Mantenedores
~~~~~~~~~~~~

Este módulo es mantenido por GauchoCode.

.. image:: https://avatars.githubusercontent.com/u/gauchocode
   :alt: GauchoCode
   :target: https://github.com/gauchocode


Eres bienvenido a contribuir.