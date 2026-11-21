# Paquete de Mau — Hackatón 3B · Reto 2 Validat3B · todos tus sprints

> Generado 2026-11-21 10:19. **Pega este archivo completo a tu asistente de IA** y dile: «Lee todo. Ejecuta el sprint que te indique; empieza por el primero que no esté entregado». Es autocontenido.

## Cómo trabajamos (léelo tú, 1 minuto)

- **Tu carril:** ui. **Tus archivos, y solo esos:** `ml/validat3b/visor.py` y la carpeta `docs/entrega/`. Nadie más los toca y tú no tocas los de nadie.
- **Tu cola del día:** U1 visor local → U2 visor con lecturas y modo pitch → U3 ficha técnica de una página (entregable oficial) → 15:00 pitch (manejas el visor)
- **Al empezar CADA sprint:** `git fetch origin` y `git pull --rebase origin main`. Rama nueva por sprint: `carril/ui-sp<N>-<tema>` desde `main`. **Si tu PR anterior aún no está fusionado, crea la rama nueva desde tu rama anterior** y dilo en el reporte.
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

## U1 — Visor local de capturas (herramienta de análisis de errores y apoyo del pitch)

`carril: ui · dueño de la misión: Mau (Antigravity, agente en el repo) · rama: carril/ui-sp1-visor desde main fresco · cuelga de: 1403ab0 · tope: 45 min · clasificación: requiere pantalla · modelo: el de tu asistente`

**Paso 0, obligatorio y automático para tu agente, antes de leer o tocar nada:** `git fetch origin` y `git pull --rebase origin main`; luego crea tu rama desde ese `main`. Si el pull falla por cambios locales, **para y muéstralos**; no los descartes. Antes de cada push: `git fetch origin` + `git rebase origin/main`. Cada quien es dueño de sus archivos: **no edites archivos de otra persona**; si necesitas algo, pídelo.

**Antes de empezar, Mau:** `git pull origin main` (Fer sacó los datos del repo en `1403ab0`). Los datos viven en `datos/privado/` y **no se vuelven a agregar a git**. El repo ya es privado. 

**Hechos del reto que no puedes ver** (todos `[MEDIDO o LEÍDO por el arquitecto, 21-nov 09:16–09:36]`):
- Reto 2 · Validat3B: por cada captura (foto de fachada, foto de producto, foto de etiqueta + metadatos) se decide `aprobada`, `rechazada` o `revision_manual`. Entregable: un JSON con un `Resultado` por captura.
- Puntos de costo (gana el menor): acierto 0 · mandar a revisión manual 1 · rechazar una válida 3 · **aprobar una inválida 10**. Descalifica: precisión de aprobadas < 97 %, JSON válido < 99 %, o entregar tarde.
- Datos de desarrollo: 100 capturas (34 rechazadas, 33 aprobadas, 33 revisión manual) en `datos/privado/metadatos/capturas.csv` y `catalogo_productos.csv`; 300 imágenes en `datos/privado/imagenes/imagenes/`. Motivos de rechazo presentes: «Capturas lejanas» 18, «Capturas borrosas» 11, «Descripción de producto incompleta» 5.
- **Los metadatos no deciden nada:** en las 100, `capture_barcode == product_barcode` y `capture_price` cae en `[min_product_price, max_product_price]`. Todo está en las fotos.
- Negocio (Alfredo, 3B): una captura vale solo si de la foto de producto se leen **marca, descripción y contenido** (g/ml), de la etiqueta se lee el **precio**, y la etiqueta **es de ese producto**. Si no se alcanza a leer el contenido, es lejana/incompleta. Se juzga foto por foto. Prefieren aprobar menos con error casi cero.
- **Datos de 3B (respuesta del comité, 09:50):** tu asistente **sí puede leer** las imágenes y los metadatos de desarrollo para construir y afinar (prompts, umbrales, pruebas). Lo que **no** se vale: commitearlos (viven solo en `datos/privado/`, ignorado), usarlos fuera del reto, llamar a una IA externa **dentro de la solución** (solo el endpoint asignado), ni decidir el set ciego a mano.
- **El criterio de aprobar / rechazar / revisión manual lo diseñamos nosotros** (comité, 09:50). El set ciego, la lista oficial de `reason_code` y el esquema se liberan entre 15:00 y 16:00: los códigos de hoy son provisionales y se cambian por un mapa, sin tocar reglas.
- **Principio de decisión (todo o nada):** solo se aprueba con evidencia completa y clara; ante duda nunca se aprueba. Aprobar mal cuesta 10 y puede descalificar; mandar a revisión cuesta 1.

**Formato de `salidas/resultados.json`:** lista de objetos con `capture_id`, `decision`, `confidence_score`, `reason_code`, `validaciones` (`tienda_fachada`, `producto`, `codigo_barras`, `evidencia_precio` en `ok|falla`), `precio_detectado`, `codigo_barras_detectado`, `explicacion`. **`salidas/extracciones.json`** (opcional): lista con `capture_id`, `producto` {marca, descripcion, contenido_cantidad, contenido_unidad, nitidez, encuadre}, `etiqueta` {texto_producto, precio, tipo_precio, legible}, `tokens_entrada`, `tokens_salida`.

**Qué construir** — `ml/validat3b/visor.py`: `python -m ml.validat3b.visor --datos datos/privado --resultados salidas/resultados.json --salida salidas/visor.html` genera **un HTML estático** (sin servidor, sin CDN, sin dependencias; CSS y JS dentro del archivo) que referencia las imágenes por ruta relativa:
- Una tarjeta por captura: las tres fotos (clic para ampliar), producto esperado (marca, nombre, contenido), lo leído por el modelo, decisión esperada **junto a** decisión del motor, `reason_code`, explicación, confianza y costo en puntos (0/1/3/10).
- Filtros arriba: por decisión esperada, por decisión del motor, «solo errores», y orden por costo. Contador de costo total visible.
- Si falta `resultados.json`, muestra solo lo esperado (sirve desde ya para estudiar los datos).
- Estilo sobrio: fondo claro, tinta `#04211F`, acento `#E31B23` solo para errores, tipografía del sistema, botones de 44 px. Sin logotipo de 3B.

**Lo que NO se toca:** nada fuera de `ml/validat3b/visor.py`; `salidas/` no se commitea (I1 lo agrega al `.gitignore`; si aún no está, **no hagas `git add salidas`**).

**Prueba de cierre:** el comando genera `salidas/visor.html`; al abrirlo se ven 100 tarjetas con sus fotos y el filtro «revision_manual» deja 33. `git status --short` no muestra `datos/` ni `salidas/`.

**Entregable:** push + PR + `docs/reportes/U1-visor.md`. Commit: `feat(ml): visor local de capturas`.

Mientras esperas la auditoría de U1: con tu visor elige **3 capturas para el pitch** (una aprobada clara, una rechazada evidente, una de revisión manual interesante) y anota sus `capture_id` y por qué en `docs/entrega/capturas-demo.md`.

---

# SPRINT 2 (11:00–13:15) · U2 — Visor con lo que leyó el motor y «modo pitch»

`rama: carril/ui-sp2-visor2 · tope: 60 min`

**Archivos que comparte Fer en `salidas/`:** `extracciones.json` (lista de `Extraccion` del contrato), `resultados.json` (lista de `Resultado`), `locales.csv` (una fila por captura: `capture_id, codigo_barras_leido, codigo_coincide, nitidez_producto, nitidez_etiqueta, huella_fachada, decision_esperada, motivo_rechazo`). Las etiquetas reales están en `datos/privado/metadatos/capturas.csv` (`decision_esperada`, `motivo_rechazo`, `facade_url`).

Amplía `visor.py`:
1. **Encabezado de marcador:** costo total, costo de «todo a revisión manual», aprobadas / rechazadas / revisión, precisión de aprobadas, tokens por captura (si existe `salidas/tokens.csv`).
2. **En cada tarjeta:** tabla «esperado | leído» con marca, descripción, contenido y precio, marcando en rojo lo que no coincide; nitidez y encuadre leídos; el `reason_code` y la explicación; puntos de costo.
3. **Vista de errores:** botón «solo aprobadas falsas» (lo más grave) y «solo válidas rechazadas».
4. **Modo pitch:** `--pitch CAP-xxx,CAP-yyy,CAP-zzz` genera `salidas/pitch.html` con solo esas capturas, a pantalla completa, una por vista, navegables con flechas del teclado, letra grande (se va a proyectar): fotos a la izquierda; a la derecha «lo que leyó el motor», la decisión en grande y la explicación.
Estilo: fondo claro, tinta `#04211F`, rojo `#E31B23` solo para errores y rechazos, verde sobrio para aprobadas, tipografía del sistema, sin logotipo de 3B. Todo en un solo HTML, sin internet.

**Prueba de cierre:** se generan `salidas/visor.html` y `salidas/pitch.html`; el modo pitch se navega con flechas; `git status --short` sin `datos/` ni `salidas/`.

---

# SPRINT 3 (13:45–14:30) · U3 — Ficha técnica de una página (ENTREGABLE OFICIAL)

`rama: carril/ui-sp3-ficha · tope: 40 min`

`docs/entrega/ficha-tecnica.html`: **una sola página tamaño carta al imprimir** (Ctrl+P → PDF), sin datos ni fotos de 3B. Contenido, en este orden: (1) qué es, en una frase; (2) diagrama de la tubería en cajas: señales locales sin tokens → lectura con `claude-haiku-5-5` (una llamada por captura, imágenes reducidas, con caché) → reglas de decisión → JSON oficial; (3) **cómo decide**: aprobar solo con marca, descripción, contenido y precio legibles y coincidentes; rechazar con motivo cuando la evidencia falla con claridad; revisión manual solo en la zona de duda; (4) tecnologías: Python, endpoint de Azure AI Foundry, zxing-cpp, Pillow, pydantic; (5) resultados: deja **huecos marcados `[[COSTO]]`, `[[PRECISION]]`, `[[TOKENS]]`, `[[SEGUNDOS]]`** que se llenan con `salidas/marcador.md` de Sergio a las 14:30; (6) cómo correrlo: 3 comandos; (7) siguiente paso para 3B: avisar «foto borrosa, repítela» en el momento de la captura.
Una cifra sin medición no entra: va el hueco.

**Prueba de cierre:** la vista de impresión cabe en una página; no hay ninguna imagen ni dato de 3B en el archivo.

---

# 15:00 — Pitch (con Alan y Sergio)

Tú manejas `salidas/pitch.html` mientras Alan narra. Ensayen tres veces con cronómetro (3:00). Ten a la mano capturas de pantalla del modo pitch por si la laptop falla.
