# Misiones — carril PITCH Y SEÑALES LOCALES (Alan)

## ESTADO · 2026-11-21 12:36
Carril pitch · dueño Alan (Antigravity, agente en el repo) · misiones 3 · hechas 3 · siguiente **NINGUNO**
Cola: ~~P1~~ ~~P2~~ ~~P3~~ (P3.1)
siguiente: **NINGUNO — ajustar cifras finales a mano** (104/39, 2,390 tokens, «una llamada por captura; tres solo para las que se aprueban») y ensayar
Última auditoría: P3 → Devuelto (cifras viejas) → P3.1 Aprobado ([LEÍDO 12:30: 434912, 49/100, 5,880, sin caché de fachada, «en desarrollo»] · PR #22 fusionado 12:31)
Qué cambió por esa auditoría: el motor final cambia costo y tokens; el guion se actualiza con sp6
Reescrituras de este documento: 4
Siguiente con modelo: —

---

## P2 [HECHA · Aprobado con anotaciones] — Puerta local: qué capturas se pueden resolver sin gastar tokens

`rama: carril/pitch-sp2-puerta · tope: 60 min`

**Archivos que comparte Fer en `salidas/`:** `extracciones.json` (lista de `Extraccion` del contrato), `resultados.json` (lista de `Resultado`), `locales.csv` (una fila por captura: `capture_id, codigo_barras_leido, codigo_coincide, nitidez_producto, nitidez_etiqueta, huella_fachada, decision_esperada, motivo_rechazo`). Las etiquetas reales están en `datos/privado/metadatos/capturas.csv` (`decision_esperada`, `motivo_rechazo`, `facade_url`).

**Pregunta que respondes con datos:** usando solo señales locales (nitidez, tamaño, código de barras leído), ¿cuántas capturas se pueden **rechazar sin llamar al modelo** sin equivocarnos en ninguna?

1. `ml/validat3b/puerta.py`:
   - `python -m ml.validat3b.puerta --locales salidas/locales.csv`: para la nitidez de producto y la de etiqueta, recorre umbrales y reporta, por umbral, cuántas capturas quedan por debajo y cuáles son sus decisiones reales. Busca el umbral más alto por debajo del cual **ninguna** captura real es `aprobada` (rechazo seguro). Reporta cuántas capturas ahorra y qué % de tokens.
   - `puerta(senales: dict) -> str | None`: devuelve `"CAPTURA_BORROSA"` si la captura cae bajo el umbral seguro, o `None` si debe ir al modelo. El umbral es una constante arriba del archivo, con un comentario que diga con qué datos se fijó.
2. `test_puerta.py`: casos por encima y por debajo del umbral, y señales con `None` (debe devolver `None`: ante la duda, va al modelo).
3. En tu reporte, una recomendación clara: **«activar»** si ahorra ≥ 10 % de las llamadas con cero aprobadas reales rechazadas, o **«no activar»**. Antecedente medido por Fer: la nitidez sola se traslapa mucho (mediana 182 en borrosas contra 399 en el resto), así que «no activar» es un resultado válido y honesto; igual lo usamos en el pitch.

**Prueba de cierre:** `python -m unittest ml.validat3b.test_puerta -v` en verde y la tabla de umbrales pegada en el reporte. Integrarla al motor es decisión de Fer.

---

## P1 [HECHA · Aprobado con anotaciones] — Señales locales sin tokens: código de barras, nitidez y huella de fachada

`carril: pitch · dueño Alan · rama: carril/pitch-sp1-locales desde main fresco · cuelga de: 1403ab0 · tope: 45 min · clasificación: autónoma · modelo: el de tu asistente`

**Paso 0, obligatorio y automático para tu agente, antes de leer o tocar nada:** `git fetch origin` y `git pull --rebase origin main`; luego crea tu rama desde ese `main`. Si el pull falla por cambios locales, **para y muéstralos**; no los descartes. Antes de cada push: `git fetch origin` + `git rebase origin/main`. Cada quien es dueño de sus archivos: **no edites archivos de otra persona**; si necesitas algo, pídelo.

**Para la persona.** Primero `git pull origin main`. Tu agente escribe código en `ml/validat3b/local.py` y `ml/validat3b/test_local.py`, nada más. 

**Hechos del reto que no puedes ver** (todos `[MEDIDO o LEÍDO por el arquitecto, 21-nov 09:16–09:36]`):
- Reto 2 · Validat3B: por cada captura (foto de fachada, foto de producto, foto de etiqueta + metadatos) se decide `aprobada`, `rechazada` o `revision_manual`. Entregable: un JSON con un `Resultado` por captura.
- Puntos de costo (gana el menor): acierto 0 · mandar a revisión manual 1 · rechazar una válida 3 · **aprobar una inválida 10**. Descalifica: precisión de aprobadas < 97 %, JSON válido < 99 %, o entregar tarde.
- Datos de desarrollo: 100 capturas (34 rechazadas, 33 aprobadas, 33 revisión manual) en `datos/privado/metadatos/capturas.csv` y `catalogo_productos.csv`; 300 imágenes en `datos/privado/imagenes/imagenes/`. Motivos de rechazo presentes: «Capturas lejanas» 18, «Capturas borrosas» 11, «Descripción de producto incompleta» 5.
- **Los metadatos no deciden nada:** en las 100, `capture_barcode == product_barcode` y `capture_price` cae en `[min_product_price, max_product_price]`. Todo está en las fotos.
- Negocio (Alfredo, 3B): una captura vale solo si de la foto de producto se leen **marca, descripción y contenido** (g/ml), de la etiqueta se lee el **precio**, y la etiqueta **es de ese producto**. Si no se alcanza a leer el contenido, es lejana/incompleta. Se juzga foto por foto. Prefieren aprobar menos con error casi cero.
- **Datos de 3B (respuesta del comité, 09:50):** tu asistente **sí puede leer** las imágenes y los metadatos de desarrollo para construir y afinar (prompts, umbrales, pruebas). Lo que **no** se vale: commitearlos (viven solo en `datos/privado/`, ignorado), usarlos fuera del reto, llamar a una IA externa **dentro de la solución** (solo el endpoint asignado), ni decidir el set ciego a mano.
- **El criterio de aprobar / rechazar / revisión manual lo diseñamos nosotros** (comité, 09:50). El set ciego, la lista oficial de `reason_code` y el esquema se liberan entre 15:00 y 16:00: los códigos de hoy son provisionales y se cambian por un mapa, sin tocar reglas.
- **Principio de decisión (todo o nada):** solo se aprueba con evidencia completa y clara; ante duda nunca se aprueba. Aprobar mal cuesta 10 y puede descalificar; mandar a revisión cuesta 1.

**Por qué importa:** cada token cuenta 10 % de la calificación. Lo que se pueda saber sin llamar al modelo, se calcula en la máquina.

**Qué construir** — `ml/validat3b/local.py` (dependencias `pillow`, `numpy`, `zxing-cpp`: ya están en `ml/requirements.txt`; no lo edites):
- `senales_locales(captura, dir_datos) -> dict` con:
  - `codigo_barras_leido`: intenta decodificar un código EAN/UPC en la foto de producto y luego en la de etiqueta (`zxingcpp.read_barcodes`); texto o `None`.
  - `codigo_coincide`: `True/False/None` contra `captura.capture_barcode` (ignora ceros a la izquierda).
  - `nitidez_producto`, `nitidez_etiqueta`: varianza del laplaciano sobre la imagen en grises reducida a 640 px de ancho (con numpy; sin OpenCV).
  - `ancho`, `alto` de cada foto; `huella_fachada`: md5 de los bytes de la foto de fachada (varias capturas de una visita comparten fachada: sirve para cachear, **no** para decidir).
  - Nunca lanza excepción: ante cualquier error, ese campo sale `None`.
- `python -m ml.validat3b.local --datos datos/privado --salida salidas/locales.csv`: una fila por captura con esas columnas más `decision_esperada` y `motivo_rechazo`, y al final imprime **solo conteos**: en cuántas capturas leyó código, en cuántas coincide, y mediana de nitidez por `motivo_rechazo`.
- `test_local.py` (`unittest`): genera en memoria una imagen nítida y la misma desenfocada (Pillow `GaussianBlur`) y comprueba que la nitidez baja; y que una ruta inexistente devuelve `None` sin romper.

**Lo que NO se toca:** nada fuera de tus dos archivos. `salidas/` y `datos/` no se commitean.

**Prueba de cierre:** `python -m unittest ml.validat3b.test_local -v` en verde; el comando imprime los conteos sobre las 100 capturas; `git status --short` sin `datos/` ni `salidas/`.

**Entregable:** push + PR + `docs/reportes/P1-locales.md` (12 líneas, con los conteos). Commit: `feat(ml): senales locales sin tokens (codigo de barras, nitidez)`.

---

## P3 — Pitch de 3 minutos y ficha técnica de una página (arranca 15:00 · Alan narra, Mau maneja el visor, Sergio lleva los números)

Se escribe completa a las 14:45 con el marcador real. Desde ya, Alan guarda en `docs/pitch/notas.md`: las respuestas de Alfredo (800 capturistas, ~12,000 capturas por semana, «un peso por millones de ventas», «preferimos 80 de 100 con error casi cero», «no queremos revisión manual») y cada cifra con su fuente.

---

## Bitácora de reescrituras

- 2026-11-21 09:55 · S002: creado con P1 (Alan pide tareas de programación) y P2 en espera.
- 2026-11-21 11:23 · S003 · P1 auditada → se escribe P2 (puerta local, del paquete de Alan); el pitch pasa a P3. Se sube el sello.
- 2026-11-21 11:47 · S003 · P2 fusionada (#14), no conectada → P3 (pitch). Se sube el sello.
- 2026-11-21 12:36 · S003 · P3.1 fusionada; quedan cifras finales y ensayo.
