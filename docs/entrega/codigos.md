# Códigos de motivo (reason_code) · Núcleo · N6

Estado: **antes de las 15:00**. Los códigos internos son provisionales. Se llena la última columna con la lista oficial del comité y se edita `ml/validat3b/mapa_codigos.json` (solo los valores).

| # | Código interno | Qué regla lo emite (`decidir.py`) | Qué significa en 3B | Veces en sp7 | Código oficial probable |
|---|---|---|---|---|---|
| 1 | `CAPTURA_BORROSA` | Regla 4 (nitidez borrosa de la foto de producto) | Foto de producto borrosa; no se lee | sin medir | |
| 2 | `CAPTURA_LEJANA` | Regla 5 (encuadre lejano); regla 7 (producto no coincide, rechazo) | Producto muy lejos o no se distingue con claridad; en desarrollo, motivo «Capturas lejanas» | sin medir | |
| 3 | `DESCRIPCION_INCOMPLETA` | Regla 6 (falta marca/descripción, o falta contenido) | Descripción o contenido del producto no se leen completos | sin medir | |
| 4 | `PRODUCTO_NO_COINCIDE` | Solo en revisión manual (zona gris de la regla 7) | Dudas sobre si el producto es el esperado; **no sale en rechazos** | sin medir | |
| 5 | `PRODUCTO_NO_VISIBLE` | Regla 3 (no hay producto en la foto) | No se ve el producto | sin medir | |
| 6 | `FOTO_DE_PANTALLA` | Regla 2 (la foto es de una pantalla) | Foto de pantalla, no del producto físico | sin medir | |
| 7 | `SIN_ETIQUETA_PRECIO` | Regla 8 (sin etiqueta, sin precio o ilegible) | No hay etiqueta de precio legible | sin medir | |
| 8 | `ETIQUETA_NO_CORRESPONDE` | Regla 9 (la etiqueta es de otro producto), en revisión manual | La etiqueta no es de este producto | sin medir | |
| 9 | `PRECIO_FUERA_DE_RANGO` | Regla 10 (precio fuera del rango mín–máx), en revisión manual | Precio fuera de lo esperado | sin medir | |
| 10 | `FACHADA_INCORRECTA` | **Ninguna regla de `decidir.py`** (reservado; la fachada no se evalúa hoy) | Fachada de tienda incorrecta | 0 (no se emite) | |
| 11 | `SIN_LECTURA` | Regla 1 (sin lectura del modelo: origen error o sin_modelo), en revisión manual | No se pudo leer la captura | sin medir | |

Notas:
- `reason_code` es `null` en aprobadas y en revisiones sin motivo (regla 11).
- Las compuertas de Fer (`compuerta.py`) emiten `reason_code=None`; no necesitan entrada en el mapa.
- Motivos reales del set de desarrollo: lejanas 18, borrosas 11, descripción incompleta 5. Ninguno corresponde a `PRODUCTO_NO_COINCIDE`.
- «Veces en sp7»: no hay `salidas-sp7` en este equipo; se llena cuando llegue el zip.

## Procedimiento a las 15:00 (con la lista oficial)

1. Llenar la última columna con el código oficial que corresponda a cada fila. Si una fila no tiene equivalente claro, va al código más cercano y se anota aquí. **Nunca se inventa un código que no esté en la lista oficial.**
2. Editar `ml/validat3b/mapa_codigos.json`: cambiar solo los valores (la llave se queda igual).
3. Correr la prueba de `entregar` con el mapa nuevo y confirmar que todos los códigos emitidos están en la lista oficial.
4. Abrir el PR y avisar a Fer para que lo apruebe antes de correr el set ciego.
