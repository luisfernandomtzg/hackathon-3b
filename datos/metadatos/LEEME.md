# Validat3B · Datos del reto (desarrollo)

100 capturas etiquetadas para explorar, construir y medir tu motor.

Contenido:
- capturas.csv / capturas.json: una fila por captura, con la decisión esperada.
- catalogo_productos.csv: catálogo de referencia de productos.
- Las imágenes vienen en el zip **Validat3B_desarrollo_imagenes.zip**; descomprímelo junto a este archivo para que las rutas `imagenes/...` funcionen.

## Etiquetas

| Campo | Valores |
|---|---|
| decision_esperada | aprobada, rechazada, revision_manual |
| motivo_rechazo | Motivo registrado por el analista cuando la captura fue rechazada |

## Diccionario de datos (capturas.csv / capturas.json)

| Campo | Descripción |
|---|---|
| capture_id | Identificador de la captura (usar este mismo valor en el JSON de salida) |
| capture_store_name | Cadena/tienda seleccionada en la app |
| capture_date | Fecha y hora de la captura |
| capture_barcode | Código de barras capturado en campo |
| capture_price | Precio capturado por el usuario en campo |
| capture_brand | Marca capturada |
| id_product | SKU esperado (ver catalogo_productos.csv) |
| product_name | Descripción del producto esperado |
| product_barcode | Código de barras del producto esperado |
| product_price | Precio de referencia |
| min_product_price / max_product_price | Rango de precio de referencia |
| unit_product / unit_quantity_product | Unidad y contenido del producto esperado |
| product_group / product_line | Categoría del producto |
| facade_file / product_file / shelf_file | Ruta de la imagen dentro del zip de imágenes |
| facade_url / product_url / shelf_url | La misma imagen en línea |

Imágenes por captura: `facade` (fachada de la tienda), `product` (foto del producto), `shelf` (etiqueta de precio en anaquel).
Varias capturas de la misma tienda pueden compartir la misma foto de fachada.
