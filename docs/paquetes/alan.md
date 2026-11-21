# Paquete de Alan — Hackatón 3B · Reto 2 Validat3B · todos tus sprints

> Generado 2026-11-21 10:19. **Pega este archivo completo a tu asistente de IA** y dile: «Lee todo. Ejecuta el sprint que te indique; empieza por el primero que no esté entregado». Es autocontenido.

## Cómo trabajamos (léelo tú, 1 minuto)

- **Tu carril:** pitch. **Tus archivos, y solo esos:** `ml/validat3b/local.py`, `test_local.py`, `puerta.py`, `test_puerta.py` y la carpeta `docs/pitch/`. Nadie más los toca y tú no tocas los de nadie.
- **Tu cola del día:** P1 señales locales sin tokens → P2 puerta local (¿qué capturas pueden saltarse el modelo?) → P3 guion y láminas → 15:00 pitch (tú narras)
- **Al empezar CADA sprint:** `git fetch origin` y `git pull --rebase origin main`. Rama nueva por sprint: `carril/pitch-sp<N>-<tema>` desde `main`. **Si tu PR anterior aún no está fusionado, crea la rama nueva desde tu rama anterior** y dilo en el reporte.
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

## P1 — Señales locales sin tokens: código de barras, nitidez y huella de fachada

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

Mientras esperas la auditoría de P1: crea `docs/pitch/notas.md` con las cifras de Alfredo y su fuente («Alfredo, negocio 3B, 21-nov»): ~800 capturistas en campo; ~12,000 capturas por semana revisadas una por una; «un peso de diferencia por millones de ventas son millones de pesos»; «preferimos validar 80 de 100 con error casi cero que las 100 con errores»; «no queremos revisión manual».

---

# SPRINT 2 (11:00–13:15) · P2 — Puerta local: qué capturas se pueden resolver sin gastar tokens

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

# SPRINT 3 (13:45–14:30) · P3 — Guion de 3 minutos y tres láminas

`rama: carril/pitch-sp3-guion · tope: 45 min` · carpeta `docs/pitch/`

`guion.md` (unas 420 palabras, 3:00 hablado) con esta estructura:
- **0:00–0:25 · El problema, en palabras de 3B:** capturistas en tiendas de la competencia, fotos con prisa, ~12,000 capturas por semana revisadas una por una; un precio mal validado mueve decisiones de precio.
- **0:25–1:40 · Demo** (Mau maneja `pitch.html`): una aprobada («leyó marca, descripción, contenido y precio; todo coincide»), una rechazada con su motivo, una de revisión manual. La frase que se repite: *el modelo lee, las reglas deciden, y todo queda explicado*.
- **1:40–2:20 · El marcador** (números de Sergio): costo contra «todo a revisión manual» y contra Rival 3B si nos dan su puntaje; precisión de aprobadas; tokens por captura.
- **2:20–2:45 · Por qué encaja en hard discount:** una sola llamada barata por captura, lo demás corre en una laptop; cero hardware; mismas reglas en todas las regiones.
- **2:45–3:00 · Qué no hace todavía y siguiente paso:** avisar «foto borrosa, repítela» en la app al momento de capturar; piloto de cuatro semanas en una región.
`laminas.md`: contenido de 3 láminas (problema · cómo decide · marcador), máximo 20 palabras cada una. `cifras.md`: tabla **cifra → fuente** (dato de 3B con nombre, medición nuestra, o SUPUESTO). Deja `[[huecos]]` para los números que da Sergio a las 14:30.

**Prueba de cierre:** leído en voz alta con cronómetro dura entre 2:45 y 3:00; ninguna cifra sin fuente.

---

# 15:00 — Pitch

Tú narras, Mau maneja, Sergio responde números. Tres ensayos con cronómetro antes de las 16:45. Si preguntan algo que no medimos, la respuesta es «no lo medimos todavía».
