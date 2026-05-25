# Importador de Facturas de Venta (Excel)

Importa facturas de cliente en estado borrador desde archivos Excel (.xlsx),
con previsualización de filas, detección de duplicados y soporte para múltiples
tipos de operación (Protectores, CPD, Préstamos, Pagarés, ON).

## Table of contents

* [Installation](#installation)
* [Configuration](#configuration)
* [Usage](#usage)
* [Excel layout](#excel-layout)
* [Import types](#import-types)
* [Known Issues / Roadmap](#known-issues--roadmap)
* [Credits](#credits)

## Installation

Requiere la librería Python **openpyxl** instalada en el entorno de Odoo:

```bash
pip install openpyxl
```

## Configuration

No requiere configuración adicional más allá de tener los datos maestros necesarios
para cada tipo de importación (ver sección [Import types](#import-types)).

## Usage

El módulo agrega la acción **Importar facturas de venta** disponible desde la lista
y el formulario de `Facturas de cliente` (menú Contabilidad → Clientes → Facturas).

Pasos:

1. Seleccionar el archivo Excel (.xlsx).
2. Elegir el **tipo de importación** según el formato del archivo.
3. Seleccionar la **hoja** a procesar (se listan automáticamente al cargar el archivo).
4. Revisar el **preview**: cada fila muestra su estado (`Lista`, `Duplicada`, `Error`).
5. Presionar **Importar** para crear las facturas en borrador.

El resultado se muestra en un log con el detalle de cada fila procesada.

### Creación automática de clientes

La opción **Crear clientes faltantes** (activa por defecto) crea el partner si no
existe ninguno con el CUIT indicado. El partner se crea como empresa argentina con
tipo de identificación CUIT.

### Detección de duplicados

Una fila se considera duplicada si ya existe una factura de venta (no cancelada) con:

- El mismo **CUIT** (partner).
- El mismo **Comentario** (ref).
- La misma **Fecha de factura**.

Si la fila no tiene comentario, nunca se marca como duplicada.

### Condición de cobro

La columna `Condición de Cobro` (J) **no se asigna** directamente en la factura.
La condición se gestiona en el contacto (`payment_condition_id`) y se hereda
automáticamente al asignar el partner.

### Analíticos

Las columnas K–N determinan las cuentas analíticas de las líneas:

- El encabezado de cada columna identifica el **plan analítico** (ej. `Analítico DOC` → plan `DOC`).
- El valor de la celda se busca en `account.analytic.account` por nombre exacto, código o display name.
  Si el plan está identificado, la búsqueda se restringe a ese plan.
- Los analíticos encontrados se asignan al **100%** en cada línea (`analytic_distribution`).

## Excel layout

Todas las variantes comparten las primeras 16 columnas:

| Col | Letra | Campo              |
|-----|-------|--------------------|
| 1   | A     | Fecha FC           |
| 2   | B     | Desde              |
| 3   | C     | Hasta              |
| 4   | D     | CUIT               |
| 5   | E     | Denominación       |
| 6   | F     | Comentario         |
| 7   | G     | Tipo Cambio        |
| 8   | H     | Moneda             |
| 9   | I     | Diario             |
| 10  | J     | Condición de Cobro |
| 11  | K     | Analítico DOC      |
| 12  | L     | Analítico COME     |
| 13  | M     | Analítico CONV     |
| 14  | N     | Analítico ALYC     |
| 15  | O     | Base / Valor       |
| 16  | P     | %                  |

Las columnas Q en adelante varían según el tipo. Ver detalle en la sección siguiente.

## Import types

### Protectores

20 columnas. Lógica base del importador.

| Col | Letra | Campo                          | Tax         |
|-----|-------|--------------------------------|-------------|
| 17  | Q     | Línea [código producto]        | IVA 21%     |
| 18  | R     | Línea [código producto]        | IVA 21%     |
| 19  | S     | IVA (21%)                      | —           |
| 20  | T     | TOTAL                          | —           |

Los códigos de producto se extraen automáticamente del encabezado de la columna
entre corchetes (ej. `Comisión [000010]` → producto `000010`).

Datos maestros requeridos: diario de ventas, productos por código, impuesto IVA 21%.

---

### CPD

20 columnas. Filas con columna A igual a `Fecha FC` se omiten automáticamente.

| Col | Letra | Campo                          | Tax         |
|-----|-------|--------------------------------|-------------|
| 17  | Q     | EXENTO Comision [000005]       | IVA Exento  |
| 18  | R     | GRAVADO Liq Prod [000012]      | IVA 21%     |
| 19  | S     | IVA (21%)                      | —           |
| 20  | T     | TOTAL                          | —           |

- La columna Q genera una línea con IVA **Exento** (se busca un impuesto de venta con nombre `IVA EXENTO`).
- La columna R genera una línea con IVA **21%**.
- Se valida que `EXENTO + GRAVADO + IVA = TOTAL` dentro de la tolerancia de redondeo de la moneda.
- Fallback de productos si el encabezado no trae código: `000005` (col Q) y `000012` (col R).

Datos maestros requeridos: diario de ventas, productos `000005` y `000012`,
impuesto IVA 21%, impuesto IVA Exento, cuentas analíticas K–N.

---

### ON (Obligaciones Negociables)

20 columnas. Misma estructura que CPD.

| Col | Letra | Campo                          | Tax         |
|-----|-------|--------------------------------|-------------|
| 17  | Q     | EXENTO Comision [000005]       | IVA Exento  |
| 18  | R     | GRAVADO Liq Prod [000012]      | IVA 21%     |
| 19  | S     | IVA (21%)                      | —           |
| 20  | T     | TOTAL                          | —           |

Comparte toda la lógica de CPD (validación de total incluida).

Datos maestros requeridos: ídem CPD.

---

### Préstamos

21 columnas. Filas con columna A igual a `Fecha FC` se omiten automáticamente.

| Col | Letra | Campo                          | Tax         |
|-----|-------|--------------------------------|-------------|
| 17  | Q     | Precio Neto Grav Anual         | IVA 21%     |
| 18  | R     | Precio Neto Grav Mensual       | IVA 21%     |
| 19  | S     | Precio L Producto [000012]     | IVA 21%     |
| 20  | T     | IVA (21%)                      | —           |
| 21  | U     | TOTAL                          | —           |

- Columnas Q y R tienen fallback de producto `000003` y `000004` respectivamente.
- El código de producto de la columna S se extrae del encabezado.
- Las tres columnas generan líneas con IVA **21%**.
- No se valida la suma de importes; se confía en los datos del Excel.

Datos maestros requeridos: diario de ventas, productos `000003`, `000004` y el
código que figure en el encabezado de S, impuesto IVA 21%, cuentas analíticas K–N.

---

### Pagarés

21 columnas. Filas con columna A igual a `Fecha FC` se omiten automáticamente.

| Col | Letra | Campo                          | Tax         |
|-----|-------|--------------------------------|-------------|
| 17  | Q     | EXENTO Comision [código]       | IVA Exento  |
| 18  | R     | GRAVADO Liq Prod [código]      | IVA 21%     |
| 19  | S     | GRAVADO Rpro Gtos [código]     | IVA 21%     |
| 20  | T     | IVA (21%)                      | —           |
| 21  | U     | TOTAL                          | —           |

- La columna Q genera una línea con IVA **Exento**.
- Las columnas R y S generan líneas con IVA **21%** (la S solo se procesa si tiene importe > 0).
- Los códigos de producto se extraen del encabezado de cada columna.
- No se valida la suma de importes; se confía en los datos del Excel.

Datos maestros requeridos: diario de ventas, productos por código de encabezado,
impuesto IVA 21%, impuesto IVA Exento, cuentas analíticas K–N.

---

## Known Issues / Roadmap

- La condición de cobro (col J) está parseada pero no se asigna en la factura;
  se hereda del contacto. Esta decisión fue intencional para esta etapa.
- El importador no confirma (valida) las facturas; las deja siempre en borrador.

## Credits

### Authors

* [GauchoCode](https://github.com/gaucho-gc)

### Maintainers

* GauchoCode
