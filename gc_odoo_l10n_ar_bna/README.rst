===========================================
Tasas de Cambio del Banco de la Nación Argentina
===========================================

.. !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
   !! Este archivo es generado por oca-gen-addon-readme !!
   !! cambios sobre escribirse.                         !!
   !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

.. |badge1| image:: https://img.shields.io/badge/maturity-Beta-yellow.png
    :target: https://odoo-community.org/page/development-status
    :alt: Beta
.. |badge2| image:: https://img.shields.io/badge/licence-LGPL--3-blue.png
    :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3
.. |badge3| image:: https://img.shields.io/badge/github-GauchoCode%2Fgc--odoo--potenciar--addons-lightgray.png?logo=github
    :target: https://github.com/GauchoCode/gc-odoo-potenciar-addons/tree/16.0/gc_odoo_l10n_ar_bna
    :alt: GauchoCode/gc-odoo-potenciar-addons

|badge1| |badge2| |badge3|

Este módulo permite la sincronización automática de las tasas de cambio desde el sitio web oficial del Banco de la Nación Argentina (BNA), manteniendo las cotizaciones actualizadas automáticamente para las principales divisas internacionales.

**Tabla de contenidos**

.. contents::
   :local:

Descripción General
===================

El módulo `gc_odoo_l10n_ar_bna` proporciona una integración completa con las cotizaciones oficiales del Banco de la Nación Argentina. Este módulo es especialmente útil para empresas argentinas que necesitan mantener sus tipos de cambio actualizados con las cotizaciones oficiales del BNA para cumplir con las regulaciones locales y tener información financiera precisa.

El módulo realiza web scraping del sitio oficial del BNA (https://www.bna.com.ar/Personas) y actualiza automáticamente las tasas de cambio en Odoo según la configuración establecida.

Características
===============

* **Sincronización automática**: Actualización diaria automática de las tasas de cambio desde el BNA
* **Múltiples tipos de cotización**: Soporte para cotizaciones de billete y divisa
* **Múltiples valores**: Permite elegir entre precios de compra, venta o promedio
* **Monedas principales soportadas**:
  
  - USD (Dólar Estadounidense)
  - EUR (Euro)
  - GBP (Libra Esterlina)
  - BRL (Real Brasileño)
  - CHF (Franco Suizo)
  - JPY (Yen Japonés)
  - CAD (Dólar Canadiense)
  - DKK (Corona Danesa)
  - NOK (Corona Noruega)
  - SEK (Corona Sueca)
  - CNY (Yuan Chino)
  - AUD (Dólar Australiano)

* **Configuración por empresa**: Cada empresa puede configurar independientemente su tipo de cotización preferido
* **Gestión de unidades**: Manejo automático de las diferentes unidades utilizadas por el BNA (1 o 100 unidades)
* **Interfaz de configuración**: Panel de configuración integrado en las opciones de contabilidad
* **Gestión de monedas BNA**: Vista dedicada para administrar qué monedas sincronizar
* **Logs detallados**: Sistema de logging para monitorear las actualizaciones y detectar errores

Uso
===

Configuración Inicial
---------------------

1. Vaya a **Contabilidad** > **Configuración** > **Ajustes**
2. En la sección "Banco Nación Argentina (BNA)", configure:
   
   - **Rate**: Seleccione entre "Billete" o "Divisa"
   - **Value**: Seleccione entre "Compra", "Venta" o "Promedio Compra-Venta"

3. Guarde la configuración

Gestión de Monedas BNA
----------------------

1. Vaya a **Contabilidad** > **Configuración** > **BNA Currencies**
2. En esta vista puede:
   
   - Ver todas las monedas configuradas para sincronización
   - Activar/desactivar la sincronización por moneda usando el toggle "Read Rate?"
   - Verificar las unidades BNA para cada moneda
   - Editar la configuración directamente en la vista

Sincronización Manual
--------------------

Para ejecutar una sincronización manual:

1. Vaya a **Configuración** > **Técnico** > **Automatización** > **Acciones Programadas**
2. Busque "Actualizar Cotizaciones BNA"
3. Haga clic en "Ejecutar Manualmente"

Verificación de Tasas
--------------------

1. Vaya a **Contabilidad** > **Configuración** > **Monedas**
2. Seleccione una moneda (ej: USD)
3. En la pestaña "Tasas", verifique que se hayan creado nuevas tasas con la fecha actual

Configuración del Cron
======================

El módulo incluye una tarea programada que se ejecuta diariamente:

* **Nombre**: "Actualizar Cotizaciones BNA"
* **Frecuencia**: Diaria (cada 24 horas)
* **Estado**: Activo por defecto

Para modificar la frecuencia:

1. Vaya a **Configuración** > **Técnico** > **Automatización** > **Acciones Programadas**
2. Edite "Actualizar Cotizaciones BNA"
3. Modifique los campos "Interval Number" e "Interval Type" según sus necesidades

Instalación
===========

Para instalar este módulo:

1. Descargue o clone el repositorio en su directorio de addons de Odoo
2. Asegúrese de que los módulos base `account` estén instalados
3. Instale las dependencias de Python requeridas:

   .. code-block:: bash

      pip install requests lxml beautifulsoup4

4. Actualice la lista de aplicaciones en Odoo
5. Busque "Gauchocode BNA Currencies" en la lista de aplicaciones
6. Haga clic en "Instalar"

Requisitos
----------

* Odoo 16.0
* Módulo `account` (incluido en Odoo core)
* Dependencias de Python:
  
  - `requests` (para realizar peticiones HTTP)
  - `lxml` (para parsing XML/HTML)
  - `beautifulsoup4` (para web scraping)

* Acceso a internet para conectar con el sitio del BNA

Configuración
=============

Después de la instalación:

1. Las monedas BNA se crearán automáticamente con la configuración por defecto
2. Configure el tipo de cotización preferido en los ajustes de contabilidad
3. Verifique que la tarea programada esté activa
4. Ejecute una sincronización manual para verificar el funcionamiento

Datos Técnicos
==============

Mapeo de Monedas BNA
-------------------

El módulo utiliza el siguiente mapeo entre los nombres del BNA y los códigos ISO:

* "Dolar U.S.A" → USD
* "Euro" → EUR
* "Real" → BRL
* "Libra Esterlina" → GBP
* "Franco Suizo" → CHF
* "Yen" → JPY
* "Dólar Canadiense" → CAD
* "Corona Danesa" → DKK
* "Corona Noruega" → NOK
* "Corona Sueca" → SEK
* "Yuan" → CNY
* "Dólar Australiano" → AUD

Unidades BNA
-----------

Algunas monedas en el BNA se cotizan por 100 unidades:

* JPY, CHF, CAD, DKK, NOK, SEK, CNY: 100 unidades
* USD, EUR, GBP, BRL, AUD: 1 unidad

El módulo maneja estas diferencias automáticamente.

Seguimiento de Errores
======================

Los errores/problemas se rastrean en `GitHub Issues <https://github.com/GauchoCode/gc-odoo-potenciar-addons/issues>`_.
En caso de problemas, por favor verifique si su problema ya ha sido reportado.
Si fue el primero en descubrirlo, ayúdenos a solucionarlo proporcionando una descripción detallada
`aquí <https://github.com/GauchoCode/gc-odoo-potenciar-addons/issues/new?body=módulo:%20gc_odoo_l10n_ar_bna%0Aversión:%2016.0.0.1%0A%0A**Pasos%20para%20reproducir**%0A-%20...%0A%0A**Comportamiento%20actual**%0A%0A**Comportamiento%20esperado**>`_.

No olvide incluir:

* Descripción detallada del problema
* Pasos para reproducir el error
* Logs de Odoo relacionados con el error
* Configuración de BNA utilizada (tipo de cotización, valor)
* Versión de Odoo y dependencias de Python
* Estado de la conexión a internet

Problemas Conocidos / Hoja de Ruta
===================================

* **Dependencia de la estructura web del BNA**: El módulo depende de la estructura HTML del sitio del BNA, cambios en el sitio pueden requerir actualizaciones del módulo
* **Horarios de actualización**: El BNA actualiza las cotizaciones en horarios específicos, la sincronización muy temprana puede no obtener datos del día actual
* **Manejo de feriados**: En días feriados argentinos, el BNA no actualiza cotizaciones

Hoja de Ruta
------------

* Soporte para más monedas
* Configuración de horarios de sincronización
* Alertas automáticas en caso de fallos de sincronización
* Histórico de cambios en las cotizaciones

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
en localización argentina y integración con sistemas financieros locales.