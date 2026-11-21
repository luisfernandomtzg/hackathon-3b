# Misiones — carril DATOS E IA

## ESTADO · 2026-11-21 12:36
Carril datos · dueño Sergio (chat web) · misiones 4 · hechas 4 · siguiente **NINGUNO**
Cola: ~~D1~~ ~~D2~~ ~~D3~~ (Devuelto) ~~D3.1~~
siguiente: **NINGUNO — carril cerrado; Sergio apoya el pitch** (cifras con `salidas-sp6.zip`)
Última auditoría: D3.1 → Aprobado ([REPORTADO 12:02: 10/0, 100 %, 99; tokens solo origen modelo 1,921] · PR #18 fusionado 12:05)
Qué cambió por esa auditoría: con sp6 las cifras son 104/39 y 2,390 tokens por captura
Reescrituras de este documento: 5
Siguiente con modelo: —

---

## D3.1 — Arreglo del marcador (misma rama `carril/datos-sp3-marcador`, tope 20 min)

**Hallazgo de la auditoría de D3 (PR #18, S1: el jurado lo ve)** `[LEÍDO 11:46 por el arquitecto]`:
1. `marcador.py` re-decide con `decidir()` y se salta las compuertas de I3.1 (lee `resultados.json` pero no lo usa): da 87.5 % y 118 cuando el motor real da 100 % y 99.
2. `tokens.csv` tiene varias filas por captura (las de caché valen 0) y el diccionario por `capture_id` se queda con la última: el total puede salir en ceros o a medias.
3. «(59 %)» está escrito a mano en el texto.

**Qué hacer:** usa las decisiones de `resultados.json` tal cual (sin volver a decidir); suma **todas** las filas de `tokens.csv` cuyo `origen` no termine en `cache`; usa el porcentaje calculado. **Si al leer el código concluyes que el hallazgo es falso, dilo y no toques nada.**

**Prueba de cierre:** con `salidas-sp4.zip`, el marcador dice **10 aprobadas, 0 falsas, 100 %, costo pesimista 99**, y los tokens por captura coinciden con lo que imprime `correr`. Esta prueba se pone roja con el código de hoy (que daría 87.5 %). Push a la misma rama; el PR #18 se actualiza solo.

---

## D2 [HECHA · Aprobado con anotaciones] — Dónde perdemos puntos, y si un clasificador le gana a las reglas

`rama: carril/datos-sp2-analisis · tope: 60 min`

**Archivos que comparte Fer en `salidas/`:** `extracciones.json` (lista de `Extraccion` del contrato), `resultados.json` (lista de `Resultado`), `locales.csv` (una fila por captura: `capture_id, codigo_barras_leido, codigo_coincide, nitidez_producto, nitidez_etiqueta, huella_fachada, decision_esperada, motivo_rechazo`). Las etiquetas reales están en `datos/privado/metadatos/capturas.csv` (`decision_esperada`, `motivo_rechazo`, `facade_url`).

**Qué construir:**
1. `ml/validat3b/analisis.py` — `python -m ml.validat3b.analisis --resultados salidas/resultados.json --extracciones salidas/extracciones.json --capturas datos/privado/metadatos/capturas.csv --salida salidas/analisis.md`. Escribe un reporte con: costo por cada par (real → predicha); los 20 errores más caros con lo que leyó el modelo; para cada campo leído (`nitidez`, `encuadre`, `varios_productos`, marca/descripción/contenido presentes o no, `hay_etiqueta`, `legible`) su tabla contra la decisión real — ahí se ve qué lectura separa aprobadas de rechazadas y de revisión manual; y costo por visita (`facade_url`).
2. `ml/validat3b/clasificador.py` (experimento; instala `pip install scikit-learn` en tu entorno; Fer lo agrega a `ml/requirements.txt`, tú no edites ese archivo): arma una tabla de señales por captura (campos de la lectura convertidos a 0/1, parecido de marca/descripción si viene, nitidez numérica de `locales.csv`), entrena una **regresión logística** que estime P(real = aprobada) y evalúala con **validación cruzada por grupos usando `facade_url` como grupo** (nunca la misma visita en entrenamiento y prueba). Para cada umbral de aprobación entre 0.5 y 0.99 reporta: aprobadas, aprobadas falsas, precisión y costo total. Compara contra el costo de las reglas de Mauski.
3. **Tu conclusión, en tres líneas, al inicio del reporte:** ¿el clasificador baja el costo sin ninguna aprobada falsa? Si sí, a qué umbral. Si no, se queda como evidencia de que las reglas bastan (también sirve para el pitch).

**Prueba de cierre:** los dos comandos corren sobre los archivos de `salidas/` y generan su reporte; pega en `docs/reportes/D2-analisis.md` tus tres líneas y la tabla umbral → costo.
**Importante:** con 100 ejemplos es fácil engañarse. Reporta siempre el resultado de validación cruzada, nunca el del conjunto con el que entrenaste. La decisión de usar el clasificador en el motor es de Fer.

**Hechos medidos que no puedes ver** (`[MEDIDO 11:05 por el arquitecto sobre salidas-sp2.zip + capturas.csv]`):
- Usa **`salidas-sp2.zip`** (lecturas v2 del modelo, `resultados.json` con las decisiones reales de `decidir()` y `locales.csv`). Descomprímelo dentro de `salidas/`. El de SP1 ya no sirve.
- Con v2, `decidir()` de N1 aprueba 16 y 14 son correctas: **precisión 87.5 % (descalifica; mínimo 97 %)**. Matriz real→predicha: aprobada 14/2 rech/17 manual · rechazada 1 aprob/24/9 manual · revisión manual 1 aprob/17 rech/15. Costo con `evaluar.py`: pesimista 118, optimista 52 (todo a revisión manual: 100 / 67).
- Las 2 aprobadas falsas: **CAP-206200** (real `revision_manual`) y **CAP-410562** (real rechazada «Capturas borrosas»; nitidez local de etiqueta 99). Válidas aprobadas con nitidez de etiqueta baja: 970141 (83) y 621992 (125).
- La regla 7 manda válidas a revisión porque mide el parecido sobre las palabras de la descripción leída (larga). Medir qué fracción de las palabras del **nombre esperado** aparece en lo leído. Cuando `product_name` trae «(total: NNNg)», cualquiera de los dos pesos vale.
- Fer agrega en I3 un **verificador después de `decidir()`**: una segunda mirada solo a las aprobadas, que baja a revisión manual lo que no pase. No lo toques ni lo dupliques.
- **Prioridad de D2:** ¿qué distingue a las 33 de `revision_manual`? (lectura del modelo, nitidez, precio contra su rango). Mándale la pista a Mauski por el grupo en cuanto la tengas, aunque sea parcial. No toques `decidir.py`; si usas scikit-learn, solo en tu entorno.

---

## D1 [HECHA · Aprobado con anotaciones] — Arnés de evaluación: el marcador del día

`carril: datos · dueño Sergio (chat web, cuota corta) · rama: carril/datos-sp1-evaluar desde main fresco · cuelga de: 1403ab0 · tope: 40 min · clasificación: autónoma · modelo: el de tu asistente`

**Paso 0, obligatorio y automático para tu agente, antes de leer o tocar nada:** `git fetch origin` y `git pull --rebase origin main`; luego crea tu rama desde ese `main`. Si el pull falla por cambios locales, **para y muéstralos**; no los descartes. Antes de cada push: `git fetch origin` + `git rebase origin/main`. Cada quien es dueño de sus archivos: **no edites archivos de otra persona**; si necesitas algo, pídelo.

**Para la persona.** Pega esta misión completa en tu chat y pide **el archivo completo**. Tu carpeta hoy: `ml/validat3b/evaluar.py` y `ml/validat3b/test_evaluar.py`.

**Hechos del reto que no puedes ver** (todos `[MEDIDO o LEÍDO por el arquitecto, 21-nov 09:16–09:36]`):
- Reto 2 · Validat3B: por cada captura (foto de fachada, foto de producto, foto de etiqueta + metadatos) se decide `aprobada`, `rechazada` o `revision_manual`. Entregable: un JSON con un `Resultado` por captura.
- Puntos de costo (gana el menor): acierto 0 · mandar a revisión manual 1 · rechazar una válida 3 · **aprobar una inválida 10**. Descalifica: precisión de aprobadas < 97 %, JSON válido < 99 %, o entregar tarde.
- Datos de desarrollo: 100 capturas (34 rechazadas, 33 aprobadas, 33 revisión manual) en `datos/privado/metadatos/capturas.csv` y `catalogo_productos.csv`; 300 imágenes en `datos/privado/imagenes/imagenes/`. Motivos de rechazo presentes: «Capturas lejanas» 18, «Capturas borrosas» 11, «Descripción de producto incompleta» 5.
- **Los metadatos no deciden nada:** en las 100, `capture_barcode == product_barcode` y `capture_price` cae en `[min_product_price, max_product_price]`. Todo está en las fotos.
- Negocio (Alfredo, 3B): una captura vale solo si de la foto de producto se leen **marca, descripción y contenido** (g/ml), de la etiqueta se lee el **precio**, y la etiqueta **es de ese producto**. Si no se alcanza a leer el contenido, es lejana/incompleta. Se juzga foto por foto. Prefieren aprobar menos con error casi cero.
- **Datos de 3B (respuesta del comité, 09:50):** tu asistente **sí puede leer** las imágenes y los metadatos de desarrollo para construir y afinar (prompts, umbrales, pruebas). Lo que **no** se vale: commitearlos (viven solo en `datos/privado/`, ignorado), usarlos fuera del reto, llamar a una IA externa **dentro de la solución** (solo el endpoint asignado), ni decidir el set ciego a mano.
- **El criterio de aprobar / rechazar / revisión manual lo diseñamos nosotros** (comité, 09:50). El set ciego, la lista oficial de `reason_code` y el esquema se liberan entre 15:00 y 16:00: los códigos de hoy son provisionales y se cambian por un mapa, sin tocar reglas.
- **Principio de decisión (todo o nada):** solo se aprueba con evidencia completa y clara; ante duda nunca se aprueba. Aprobar mal cuesta 10 y puede descalificar; mandar a revisión cuesta 1.

**Formato de `resultados.json`** (lista; un objeto por captura): `capture_id`, `decision` (`aprobada|rechazada|revision_manual`), `confidence_score` (0–1), `reason_code` (texto o null), `validaciones` (objeto con `tienda_fachada`, `producto`, `codigo_barras`, `evidencia_precio`, cada uno `ok|falla`), `precio_detectado` (número o null), `codigo_barras_detectado` (texto o null), `explicacion` (texto).
**Columnas de `capturas.csv` que usas:** `capture_id`, `decision_esperada`, `motivo_rechazo` (vacío salvo en rechazadas), `facade_url` (identifica la visita), `capture_price`.

**Qué construir** — `python -m ml.validat3b.evaluar --resultados salidas/resultados.json --capturas datos/privado/metadatos/capturas.csv` (solo biblioteca estándar; `csv` con `utf-8-sig`):
1. **JSON válido:** % de capturas del CSV que tienen exactamente una entrada con todas las llaves y valores permitidos. Lista los `capture_id` que fallan. `PASA/NO PASA` contra 99 %.
2. **Costo operativo.** Tabla `COSTO[real][predicha]` como constante al inicio: real `aprobada` → aprobada 0, revision_manual 1, rechazada 3 · real `rechazada` → rechazada 0, revision_manual 1, aprobada 10. **Para real `revision_manual` la regla oficial aún no la tenemos:** calcula y muestra **dos escenarios** — *pesimista* (aprobada 10, rechazada 3, revision_manual 1) y *optimista* (aprobada 10, rechazada 0, revision_manual 0) — y etiquétalos como SUPUESTO.
3. **Precisión de aprobadas** = aprobadas cuya real es `aprobada` / total aprobadas; `PASA/NO PASA` contra 97 %; si aprobó 0, dilo. Imprime también cuántas aprobó.
4. **Matriz 3×3** real × predicha, y costo por `motivo_rechazo`.
5. **Líneas base** calculadas ahí mismo: todo a revisión manual, todo aprobado, todo rechazado.
6. **Calidad del dato:** acierto de `reason_code` en las rechazadas reales con este mapa (constante): «Capturas lejanas»→`CAPTURA_LEJANA`, «Capturas borrosas»→`CAPTURA_BORROSA`, «Descripción de producto incompleta»→`DESCRIPCION_INCOMPLETA`; y % de `precio_detectado` igual a `capture_price` (±0.01) en las aprobadas reales (es referencia, no verdad: dilo en la salida).
7. **Los 15 errores más caros** (capture_id, real, predicha, costo, reason_code).
8. `--por-visita`: el mismo costo agrupado por `facade_url`.
9. `test_evaluar.py` con `unittest`: 6 capturas inventadas con costo calculado a mano.

**Segunda parte, a mano (20 min, mientras tu asistente escribe):** abre en tu máquina las 33 capturas con `decision_esperada = revision_manual` y anota en `datos/privado/notas-revision-manual.md` (ignorado por git) qué tienen en común frente a las aprobadas: ¿etiqueta con dos precios?, ¿promoción?, ¿producto sin contenido visible? Es la pregunta abierta más cara del día. Puedes apoyarte en tu asistente mostrándole algunas. Pásale a Fer tus conclusiones: de ahí sale la regla de revisión manual.

**Prueba de cierre:** `python -m unittest ml.validat3b.test_evaluar -v` en verde, y `python -m ml.validat3b.evaluar ...` sobre un `resultados.json` de «todo revisión manual» (lo genera I1; si aún no existe, constrúyelo con 5 líneas de Python) → costo pesimista 100, precisión «sin aprobadas».

**Lo que NO se toca:** nada fuera de tus dos archivos. **Entregable:** push + PR + `docs/reportes/D1-evaluar.md`. Commit: `feat(ml): arnes de evaluacion (costo, precision, linea base)`.

---

## Bitácora de reescrituras

- 2026-11-17 13:20 · creado en S000, sin misiones.
- 2026-11-17 14:54 · S000: ESTADO al formato v1.2 (sello del reloj, `BLOQUEADO hasta`).
- 2026-11-21 09:55 · S002: reto asignado = Reto 2 · Validat3B; giro a Python por lotes en `ml/validat3b/` (compuerta de Fer 09:16). Se escribe la misión 1 y se libera el carril; sin auditoría previa.
- 2026-11-21 11:23 · S003 · D1 auditada → se escribe D2 con los hechos de v2 y se sube el sello.
- 2026-11-21 11:47 · S003 · D2 fusionada (#15); D3 (#18) devuelta → D3.1. Se sube el sello.
- 2026-11-21 12:36 · S003 · D3.1 fusionada; carril cerrado.
