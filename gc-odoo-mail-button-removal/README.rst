===============================
Limpieza de Layout de Correos
===============================

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
    :target: https://github.com/GauchoCode/gc-odoo-potenciar-addons/tree/16.0/gc-odoo-mail-button-removal
    :alt: GauchoCode/gc-odoo-potenciar-addons

|badge1| |badge2| |badge3|

Este módulo limpia el layout de las notificaciones por correo electrónico de Odoo eliminando elementos innecesarios de la plantilla estándar, proporcionando un diseño más limpio y profesional para las comunicaciones automáticas.

**Tabla de contenidos**

.. contents::
   :local:

Descripción General
===================

El módulo `gc-odoo-mail-button-removal` soluciona un problema común en las notificaciones por correo electrónico de Odoo donde aparecen elementos de interfaz innecesarios o mal formateados en los emails enviados automáticamente por el sistema.

Este módulo modifica la plantilla base `mail.mail_notification_layout` para eliminar bloques específicos que pueden causar problemas de renderizado o mostrar información no deseada en los correos electrónicos, mejorando así la presentación profesional de las comunicaciones automatizadas.

Características
===============

* **Limpieza del layout**: Elimina elementos innecesarios de la plantilla de notificaciones por correo
* **Mejora de la presentación**: Proporciona un diseño más limpio y profesional para los emails
* **Aplicación automática**: Se aplica automáticamente a todas las notificaciones por correo del sistema
* **No invasivo**: No afecta la funcionalidad, solo mejora la presentación visual
* **Compatible con personalizaciones**: Funciona junto con otras personalizaciones de email
* **Herencia limpia**: Utiliza herencia de plantillas QWeb estándar con prioridad específica

Problema Resuelto
=================

Layout Original
---------------

La plantilla estándar `mail.mail_notification_layout` de Odoo incluye un bloque con las siguientes características:

- Fila de tabla (`<tr>`) con elementos que pueden no renderizar correctamente
- Celda con estilo `white-space:nowrap;` que puede causar problemas de formato
- Elementos de interfaz que aparecen inadecuadamente en emails

Layout Mejorado
---------------

Después de la instalación:

- Se elimina completamente la fila problemática
- El layout se vuelve más limpio y consistente
- Mejor compatibilidad con diferentes clientes de correo
- Presentación más profesional en todas las notificaciones

Uso
===

Verificación de Mejoras
-----------------------

Una vez instalado el módulo, las mejoras se aplicarán automáticamente:

1. **Pruebe las notificaciones**: Realice cualquier acción que genere una notificación por correo (crear factura, enviar mensaje, etc.)
2. **Revise el email recibido**: Compare el formato con emails anteriores a la instalación
3. **Verifique en diferentes clientes**: Pruebe la visualización en Gmail, Outlook, clientes móviles, etc.

Tipos de Emails Afectados
-------------------------

El módulo mejora todos los emails que utilicen la plantilla base, incluyendo:

- Notificaciones de facturas
- Mensajes de seguimiento (chatter)
- Notificaciones de cambios de estado
- Comunicaciones automáticas del sistema
- Emails de workflow
- Notificaciones de documentos compartidos

Verificación Visual
------------------

Para verificar que el módulo funciona correctamente:

1. Envíe un email de prueba desde cualquier documento
2. El email debería verse más limpio sin elementos extraños
3. No debería haber problemas de formato o espaciado
4. La presentación debería ser consistente en diferentes clientes de correo

Aspectos Técnicos
=================

Implementación
--------------

El módulo utiliza herencia de plantillas QWeb para modificar el layout:

- **Plantilla objetivo**: `mail.mail_notification_layout`
- **Método**: XPath para localizar y eliminar elementos específicos
- **Prioridad**: 16 (para asegurar que se aplique después de otras modificaciones)

Elemento Eliminado
------------------

Específicamente elimina la fila de tabla que contiene:

.. code-block:: xml

   <tr>
     <td valign="center" style="white-space:nowrap;">
       <!-- Contenido problemático -->
     </td>
   </tr>

Compatibilidad
--------------

- **Herencia segura**: Utiliza XPath específico para minimizar conflictos
- **Prioridad controlada**: Configurada para aplicarse en el orden correcto
- **No destructiva**: Solo elimina elementos, no modifica estructura general

Instalación
===========

Para instalar este módulo:

1. Descargue o clone el repositorio en su directorio de addons de Odoo
2. Asegúrese de que el módulo base `mail` esté instalado (incluido por defecto)
3. Actualice la lista de aplicaciones en Odoo
4. Busque "Mail Layout Cleanup" en la lista de aplicaciones
5. Haga clic en "Instalar"

Requisitos
----------

* Odoo 16.0
* Módulo `mail` (incluido en Odoo core)

Configuración
=============

El módulo no requiere configuración adicional. Los cambios se aplican automáticamente después de la instalación a todas las notificaciones por correo electrónico.

Verificación Post-instalación
-----------------------------

Para verificar que la instalación fue exitosa:

1. Envíe un email de prueba desde cualquier documento
2. Revise el código fuente del email recibido
3. Confirme que el elemento problemático ya no está presente
4. Verifique la mejora visual en el cliente de correo

Desinstalación
==============

Si necesita desinstalar el módulo:

1. El layout volverá automáticamente al formato original de Odoo
2. No se requieren pasos adicionales de limpieza
3. Todos los emails existentes no se ven afectados retroactivamente

Seguimiento de Errores
======================

Los errores/problemas se rastrean en `GitHub Issues <https://github.com/GauchoCode/gc-odoo-potenciar-addons/issues>`_.
En caso de problemas, por favor verifique si su problema ya ha sido reportado.
Si fue el primero en descubrirlo, ayúdenos a solucionarlo proporcionando una descripción detallada
`aquí <https://github.com/GauchoCode/gc-odoo-potenciar-addons/issues/new?body=módulo:%20gc-odoo-mail-button-removal%0Aversión:%2016.0.1.0.0%0A%0A**Pasos%20para%20reproducir**%0A-%20...%0A%0A**Comportamiento%20actual**%0A%0A**Comportamiento%20esperado**>`_.

No olvide incluir:

* Descripción detallada del problema
* Cliente de correo donde se observa el problema
* Tipo de notificación afectada
* Screenshots del antes y después si es posible
* Información sobre otras personalizaciones de email instaladas

Problemas Conocidos / Hoja de Ruta
===================================

Limitaciones Actuales
---------------------

* **Cambio específico**: Solo elimina un elemento particular; pueden existir otros elementos problemáticos no cubiertos
* **Dependiente de estructura**: Si Odoo cambia la estructura de la plantilla base, puede requerir actualización

Compatibilidad
--------------

* **Otras personalizaciones**: Debería ser compatible con la mayoría de otras personalizaciones de email
* **Actualizaciones de Odoo**: Puede requerir ajustes en futuras versiones de Odoo

Hoja de Ruta
------------

* Identificación y eliminación de otros elementos problemáticos
* Opciones de configuración para personalizar qué elementos eliminar
* Herramientas de diagnóstico para identificar problemas de layout automáticamente

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
soluciones Odoo para empresas de América Latina, con experiencia en mejora 
de la experiencia de usuario y comunicaciones empresariales.