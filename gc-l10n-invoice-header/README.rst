=====================================
Encabezado Personalizado de Facturas Argentinas
=====================================

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
    :target: https://github.com/GauchoCode/gc-odoo-potenciar-addons/tree/16.0/gc-l10n-invoice-header
    :alt: GauchoCode/gc-odoo-potenciar-addons

|badge1| |badge2| |badge3|

Este módulo personaliza el encabezado de las facturas argentinas para mejorar la presentación y organización de la información fiscal requerida por la legislación argentina, optimizando el layout y agregando campos adicionales relevantes.

**Tabla de contenidos**

.. contents::
   :local:

Descripción General
===================

El módulo `gc-l10n-invoice-header` extiende y personaliza el encabezado estándar de las facturas argentinas de Odoo, reorganizando la información para cumplir mejor con los requisitos locales y proporcionar una presentación más clara y profesional de los documentos fiscales.

Este módulo es especialmente útil para empresas argentinas que necesitan un formato de factura más completo y organizado, con todos los datos fiscales claramente presentados en el encabezado del documento.

Características
===============

* **Reorganización del encabezado**: Mejora la disposición de la información fiscal en el encabezado de las facturas
* **Información fiscal completa**: Incluye todos los datos requeridos por AFIP de forma organizada:
  
  - Número de factura
  - Fecha de emisión
  - Tipo de responsabilidad ante AFIP
  - CUIT de la empresa
  - Número de Ingresos Brutos (o estado de exención)
  - Fecha de inicio de actividades

* **Campos comerciales adicionales**:
  
  - Plazos de pago
  - Fecha de vencimiento
  - Referencia del documento

* **Estilo mejorado**: 
  
  - Fuente de 13px para mejor legibilidad
  - Uso del color secundario de la empresa para etiquetas
  - Eliminación de información redundante (website y email)

* **Limpieza de duplicados**: Elimina campos que aparecían duplicados en otras secciones del documento
* **Compatible con reportes preimpresos**: Respeta la configuración de reportes preimpresos
* **Integración perfecta**: Se integra seamlessly con el módulo de localización argentina estándar

Uso
===

Visualización de Facturas
-------------------------

Una vez instalado el módulo, todas las facturas argentinas mostrarán automáticamente el nuevo formato de encabezado:

1. Vaya a **Contabilidad** > **Clientes** > **Facturas**
2. Seleccione cualquier factura
3. Haga clic en "Imprimir" o visualice la vista preliminar
4. El encabezado mostrará la información reorganizada con el nuevo formato

Información Mostrada en el Encabezado
------------------------------------

**Lado izquierdo**: Información de la empresa (sin cambios)

**Lado derecho** (reorganizado):

* **Nro**: Número de la factura
* **Fecha**: Fecha de emisión
* **Responsabilidad AFIP - CUIT**: Tipo de responsabilidad y CUIT formateado
* **IIBB**: Número de Ingresos Brutos o "Exento"
* **Inicio de las actividades**: Fecha de inicio de actividades ante AFIP
* **Plazos de pago**: Términos de pago configurados
* **Fecha de vencimiento**: Fecha límite de pago
* **Referencia**: Referencia del documento

Configuración de Colores
------------------------

El módulo utiliza automáticamente el color secundario configurado en la empresa:

1. Vaya a **Configuración** > **Empresas** > **Empresas**
2. Seleccione su empresa
3. En la pestaña "General", configure el "Color Secundario"
4. Este color se aplicará automáticamente a las etiquetas del encabezado

Comparación con el Formato Estándar
===================================

Cambios Implementados
--------------------

**Eliminaciones**:

* Website de la empresa en el encabezado
* Email de la empresa en el encabezado
* Campos duplicados de fecha de vencimiento y plazos de pago en el cuerpo del documento

**Mejoras**:

* Tamaño de fuente consistente (13px)
* Organización lógica de la información fiscal
* Uso del color corporativo para etiquetas
* Mejor espaciado entre elementos
* Información más completa en el encabezado

**Adiciones**:

* Campo de referencia en el encabezado
* Mejor formato para el CUIT
* Manejo del estado de exención de IIBB

Instalación
===========

Para instalar este módulo:

1. Descargue o clone el repositorio en su directorio de addons de Odoo
2. Asegúrese de que los módulos base estén instalados:
   
   - `l10n_ar` (Localización Argentina)
   - `l10n_ar_ux` (Argentina UX)

3. Actualice la lista de aplicaciones en Odoo
4. Busque "Custom AR Invoice Header" en la lista de aplicaciones
5. Haga clic en "Instalar"

Requisitos
----------

* Odoo 16.0
* Módulo `l10n_ar` (Localización Argentina - incluido en Odoo)
* Módulo `l10n_ar_ux` (Argentina UX - OCA/l10n-argentina)

Configuración
=============

El módulo no requiere configuración adicional después de la instalación. Los cambios se aplican automáticamente a todas las facturas.

Para obtener mejores resultados:

1. Configure el color secundario de su empresa
2. Asegúrese de que todos los datos fiscales estén completos en la configuración de la empresa:
   
   - Tipo de responsabilidad ante AFIP
   - CUIT
   - Número de Ingresos Brutos
   - Fecha de inicio de actividades

3. Configure los términos de pago para que aparezcan en las facturas

Compatibilidad
==============

* **Reportes preimpresos**: Compatible con la funcionalidad de reportes preimpresos
* **Múltiples empresas**: Funciona correctamente en entornos multi-empresa
* **Personalizaciones**: Puede coexistir con otras personalizaciones de reportes
* **Actualizaciones**: Diseñado para ser compatible con futuras actualizaciones del core

Seguimiento de Errores
======================

Los errores/problemas se rastrean en `GitHub Issues <https://github.com/GauchoCode/gc-odoo-potenciar-addons/issues>`_.
En caso de problemas, por favor verifique si su problema ya ha sido reportado.
Si fue el primero en descubrirlo, ayúdenos a solucionarlo proporcionando una descripción detallada
`aquí <https://github.com/GauchoCode/gc-odoo-potenciar-addons/issues/new?body=módulo:%20gc-l10n-invoice-header%0Aversión:%2016.0.1.0.0%0A%0A**Pasos%20para%20reproducir**%0A-%20...%0A%0A**Comportamiento%20actual**%0A%0A**Comportamiento%20esperado**>`_.

No olvide incluir:

* Descripción detallada del problema
* Tipo de documento (factura, nota de crédito, etc.)
* Configuración de la empresa (tipo de responsabilidad, etc.)
* Screenshot del problema si es visual
* Logs de Odoo si hay errores técnicos

Problemas Conocidos / Hoja de Ruta
===================================

Limitaciones Actuales
---------------------

* Las personalizaciones están específicamente diseñadas para facturas argentinas
* Requiere que los datos fiscales estén correctamente configurados para una presentación óptima

Hoja de Ruta
------------

* Soporte para otros tipos de documentos fiscales argentinos
* Opciones de configuración para personalizar qué campos mostrar
* Soporte para layouts alternativos según el tipo de industria

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
en localización argentina y cumplimiento de requisitos fiscales locales.