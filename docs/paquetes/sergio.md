# Paquete de Sergio — Hackatón 3B · Reto 2 Validat3B · todos tus sprints

> Generado 2026-11-21 10:19. **Pega este archivo completo a tu asistente de IA** y dile: «Lee todo. Ejecuta el sprint que te indique; empieza por el primero que no esté entregado». Es autocontenido.

## Cómo trabajamos (léelo tú, 1 minuto)

- **Tu carril:** datos. **Tus archivos, y solo esos:** `ml/validat3b/evaluar.py`, `test_evaluar.py`, `analisis.py`, `clasificador.py`, `marcador.py`. Nadie más los toca y tú no tocas los de nadie.
- **Tu cola del día:** D1 arnés de evaluación → D2 análisis de errores y clasificador de prueba → D3 marcador para el pitch → 15:00 pitch (llevas los números)
- **Al empezar CADA sprint:** `git fetch origin` y `git pull --rebase origin main`. Rama nueva por sprint: `carril/datos-sp<N>-<tema>` desde `main`. **Si tu PR anterior aún no está fusionado, crea la rama nueva desde tu rama anterior** y dilo en el reporte.
- **Al terminar CADA sprint:** corre la prueba de cierre → `git push` de tu rama → abre PR a `main` → escribe `docs/reportes/<id>-<tema>.md` (12 líneas: hecho, prueba de cierre con salida real, no hecho/simulado, archivos fuera de tu carril, qué necesitas de otro) → avisa en el chat del equipo «<id> listo, PR #n» → **empieza el siguiente sprint sin esperar la auditoría**. Si la auditoría devuelve algo, Fer te lo dice y lo arreglas en la misma rama.
- **A `main` solo entra Fer.** Nadie fusiona PRs ni empuja a `main`.
- **Nunca** `git add datos/` ni `salidas/`. La llave del endpoint nunca va en código ni en el repo.
- **Solo Fer llama al endpoint** (los tokens cuentan 10 % de la calificación y el límite por minuto es compartido). Fer corre el motor y comparte en el chat privado del equipo la carpeta `salidas/` (`extracciones.json`, `resultados.json`, `locales.csv`); tú la copias a tu `salidas/` y trabajas con eso.
- **Horario:** sprint 1 hasta 10:45 · sprint 2 hasta 13:15 · comida 13:30 · sprint 3 hasta **14:30 (congelamos)** · 15:00 pitch y preparación de la corrida ciega · set ciego entre 15:00 y 16:00 · presentaciones 17:00. Si un sprint va al 150 % de su tope, entrega lo que haya y sigue.

## Qué estamos construyendo (para la IA)

Motor por lotes en Python (`ml/validat3b/`) que, por cada captura de precio tomada en tiendas de la competencia (foto de producto, foto de etiqueta, foto de fachada y metadatos), decide `aprobada`, `rechazada` o `revision_manual`, con motivo, precio detectado y explicación. Tubería: `cargar` → `local` (señales sin tokens) → `extraer` (el modelo `claude-haiku-5-5` del endpoint de Azure AI Foundry **lee** campos, no juzga) → `decidir` (reglas puras) → `correr` (escribe el JSON oficial) → `evaluar` (mide el costo) → `visor` (HTML local).
Calificación: costo operativo 50 % (acierto 0 · revisión manual 1 · rechazar una válida 3 · aprobar una inválida 10) · calidad del dato 15 % (`reason_code`, precio, tipo de precio) · tokens por captura 10 % · pitch 25 %. Descalifica: precisión de aprobadas < 97 %, JSON válido < 99 %, entregar tarde. Cliente: Tiendas 3B (hard discount): quieren aprobar solo lo seguro, eliminar revisión manual y que sea barato de operar. Hoy reciben ~12,000 capturas por semana revisadas una por una.

---

# SPRINT 1 (hasta 10:45)

## D1 — Arnés de evaluación: el marcador del día

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

Nota: en `main` hay un `ml/evaluador.py` que subió Mau. Puedes dárselo a tu asistente como punto de partida, pero el archivo oficial es `ml/validat3b/evaluar.py`.

---

# SPRINT 2 (11:00–13:15) · D2 — Dónde perdemos puntos, y si un clasificador le gana a las reglas

`rama: carril/datos-sp2-analisis · tope: 60 min`

**Archivos que comparte Fer en `salidas/`:** `extracciones.json` (lista de `Extraccion` del contrato), `resultados.json` (lista de `Resultado`), `locales.csv` (una fila por captura: `capture_id, codigo_barras_leido, codigo_coincide, nitidez_producto, nitidez_etiqueta, huella_fachada, decision_esperada, motivo_rechazo`). Las etiquetas reales están en `datos/privado/metadatos/capturas.csv` (`decision_esperada`, `motivo_rechazo`, `facade_url`).

**Qué construir:**
1. `ml/validat3b/analisis.py` — `python -m ml.validat3b.analisis --resultados salidas/resultados.json --extracciones salidas/extracciones.json --capturas datos/privado/metadatos/capturas.csv --salida salidas/analisis.md`. Escribe un reporte con: costo por cada par (real → predicha); los 20 errores más caros con lo que leyó el modelo; para cada campo leído (`nitidez`, `encuadre`, `varios_productos`, marca/descripción/contenido presentes o no, `hay_etiqueta`, `legible`) su tabla contra la decisión real — ahí se ve qué lectura separa aprobadas de rechazadas y de revisión manual; y costo por visita (`facade_url`).
2. `ml/validat3b/clasificador.py` (experimento; instala `pip install scikit-learn` en tu entorno; Fer lo agrega a `ml/requirements.txt`, tú no edites ese archivo): arma una tabla de señales por captura (campos de la lectura convertidos a 0/1, parecido de marca/descripción si viene, nitidez numérica de `locales.csv`), entrena una **regresión logística** que estime P(real = aprobada) y evalúala con **validación cruzada por grupos usando `facade_url` como grupo** (nunca la misma visita en entrenamiento y prueba). Para cada umbral de aprobación entre 0.5 y 0.99 reporta: aprobadas, aprobadas falsas, precisión y costo total. Compara contra el costo de las reglas de Mauski.
3. **Tu conclusión, en tres líneas, al inicio del reporte:** ¿el clasificador baja el costo sin ninguna aprobada falsa? Si sí, a qué umbral. Si no, se queda como evidencia de que las reglas bastan (también sirve para el pitch).

**Prueba de cierre:** los dos comandos corren sobre los archivos de `salidas/` y generan su reporte; pega en `docs/reportes/D2-analisis.md` tus tres líneas y la tabla umbral → costo.
**Importante:** con 100 ejemplos es fácil engañarse. Reporta siempre el resultado de validación cruzada, nunca el del conjunto con el que entrenaste. La decisión de usar el clasificador en el motor es de Fer.

---

# SPRINT 3 (13:45–14:30) · D3 — El marcador para el pitch

`rama: carril/datos-sp3-marcador · tope: 40 min`

`ml/validat3b/marcador.py` — genera `salidas/marcador.md` con una tabla de una sola vista: nuestro costo en desarrollo · línea base «todo a revisión manual» (100) · «aprobar todo» · precisión de aprobadas · % de capturas resueltas sin persona (aprobadas + rechazadas) · tokens por captura y tokens totales (de `salidas/tokens.csv`) · segundos por captura. Y una proyección a **12,000 capturas por semana** (cifra de Alfredo, 3B): capturas que dejarían de revisarse a mano por semana. **Las horas ahorradas necesitan «segundos por captura de un analista», que 3B no nos dio: ponlo como parámetro `--segundos-analista` y escribe la palabra SUPUESTO junto al resultado.**

**Prueba de cierre:** el comando genera `salidas/marcador.md`; ninguna cifra sin su fuente (medición nuestra, dato de 3B con nombre, o SUPUESTO).

---

# 15:00 — Pitch (con Alan y Mau)

Tú llevas los números: la lámina de marcador y la respuesta a «¿cómo saben que no aprueban basura?» (validación por visita, cero aprobadas falsas en desarrollo, umbral estricto). Si el jurado pregunta una cifra que no medimos, se dice «no lo medimos».
