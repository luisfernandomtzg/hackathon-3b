# Misiones — carril UI

## ESTADO · 2026-11-21 11:54
Carril ui · dueño Fer (dirección) · ejecuta Mau · misiones 6 · hechas 5 · siguiente **U5**
Cola: ~~U0~~ ~~U1~~ ~~U2~~ ~~U3~~ ~~U4~~ → **U5**
siguiente: **U5**
Última auditoría: U4 → Aprobado con anotaciones (PR #13 fusionado)
Qué cambió por esa auditoría: Fer eligió la opción A (11:53): la pantalla del pitch se hace con Tarima
Reescrituras de este documento: 8
Siguiente con modelo: el del asistente de Mau (Antigravity) · clasificación requiere pantalla

---

## U5 — La pantalla del pitch con Tarima (`pitch.html` y el encabezado del visor)

`rama: carril/ui-sp3-tarima desde main fresco · tope: 45 min · clasificación: requiere pantalla · decisión A de Fer (11:53)`

**Por qué:** el pitch vale 25 % y el jurado juzga en diez segundos si esto se ve serio. Hoy `pitch.html` se ve como herramienta interna. Se le pone la identidad Tarima (`DESIGN.md`, que manda): continúa la identidad pública de 3B, **sin su logotipo ni una imitación**.

**Tokens que usas** (de `DESIGN.md`, en variables CSS arriba del HTML que genera `visor.py`): rojo `--primary: #E31B23` (hover `#C4101A`), tinta `--text: #04211F`, secundario `#31413F`, fondo `#FFFFFF`, superficie `#F9FAFA`, borde `#DADFDF`, éxito `#1F7A4D` / `#E3F3EA`, aviso `#8A5A12` / `#FBF1DC`, peligro `#9D0812` / `#FEF3F1`. Tipografía `font-family: Montserrat, "Segoe UI", system-ui, sans-serif` (**sin Google Fonts ni CDN**: la demo tiene que correr sin internet), cifras con peso 800 y `font-variant-numeric: tabular-nums`.

**Qué construir (solo en `visor.py`, modo `--pitch`):**
1. **Lámina de marcador** (la primera de `pitch.html`): tres cifras grandes — «100 % de precisión en aprobadas», «Costo 99 contra 100 de revisar todo a mano», «1,921 tokens por captura» — cada una con su línea chica de qué es. Las cifras salen de `salidas/resultados.json` y `tokens.csv` (solo filas `origen == "modelo"`), **nunca escritas a mano**. Costo con la tabla pesimista de `evaluar.py` (manual real → manual = 1, rechazar una manual = 3).
2. **Una lámina por captura** (las 3 del pitch: aprobada **434912** o **487774**, rechazada **748989**, revisión **350077**): las tres fotos grandes en fila (fachada · producto · etiqueta), debajo la decisión como **chip de color** (verde aprobada, rojo rechazada, ámbar revisión manual) con su `reason_code`, y la `explicacion` en una frase. Esperado contra leído en una tabla de 4 filas máximo.
3. Navegación con flechas que ya tienes; tecla `F` para pantalla completa. Sin animaciones.
4. Encabezado del visor normal con los mismos tokens (que no se vean dos productos distintos).

**No se toca:** nada fuera de `visor.py`; los datos y cifras salen de `salidas/`. Nada de logotipo de 3B.

**Prueba de cierre (requiere pantalla):** `python -m ml.validat3b.visor --datos datos/privado --resultados salidas/resultados.json --salida salidas/visor.html --pitch CAP-434912,CAP-748989,CAP-350077` con **`salidas-sp4.zip`** → la primera lámina dice 100 %, 99 contra 100 y 1,921; se ve bien a 1920×1080 y en el proyector; el HTML abre sin internet (prueba con el wifi apagado). Capturas de las 4 láminas en el PR + reporte de 12 líneas.

---

## U4 [HECHA · Aprobado con anotaciones] — El pitch con datos reales

`rama: carril/ui-sp2-pitch-real (solo si cambias código) · tope: 40 min`

1. Descomprime **`salidas-sp2.zip`** en `salidas/` y regenera el visor: `python -m ml.validat3b.visor --datos datos/privado --resultados salidas/resultados.json --salida salidas/visor.html`. El marcador debe decir **16 aprobadas, 14 correctas, 87.5 %**; si dice otra cosa, avisa antes de seguir.
2. **Cambia las capturas del pitch.** Con este motor, 645667 y 305088 salen en revisión manual. Escoge dos candidatas por categoría **entre los aciertos** (una aprobada correcta, una rechazada correcta —de preferencia borrosa o lejana—, una revisión manual correcta), con fotos que se vean bien proyectadas. Ponlas en `docs/entrega/capturas-demo.md` con su `capture_id` y por qué funcionan.
3. Revisa que el visor siga funcionando con los campos nuevos del contrato v1.1 (`contenido_legible`, `senales`); si quieres, muéstralos en la tabla comparativa.
4. Hacia las 12:30 llega `salidas-sp3.zip` (verificador de Fer + reglas de Mauski): ahí regeneras `pitch.html` con las candidatas que sigan siendo aciertos. **Las cifras del pitch salen de ese último zip.**

**Prueba de cierre:** el visor generado con `salidas-sp2.zip` muestra 87.5 % y `capturas-demo.md` lista seis candidatas que hoy son aciertos. PR + reporte de 12 líneas; pásale a Alan el marcador.

---

## U1 [HECHA · Aprobado con anotaciones] — Visor local de capturas (herramienta de análisis de errores y apoyo del pitch)

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

---

## U0 — componentes al sistema Tarima y página `/tema` [HECHA · Aprobado con anotaciones]

`carril: ui · rama: carril/ui-sp0-tema desde main fresco · cuelga de: cdc2c6c [MEDIDO 20-nov 19:16, clon de origin/main] · tope: 40 min · clasificación: requiere pantalla · modelo: Sonnet · esfuerzo: medium`

**Primer paso.** Sigue `CLAUDE.md` §Disparador completo: `git fetch`, `git pull --rebase origin main`, `-Estado -Carril ui` con su salida pegada, relee este `ESTADO` y devuelve el acuse con el sello que leíste (`19:21`) y la punta de `origin/main` contra `cdc2c6c`. Si la punta es otra, dilo y sigue solo si desciende de `cdc2c6c`.

**Hechos que no puedes ver.**
- El tema Tarima ya está en `main` (`22080db`): `app/globals.css` define las clases `bg-primary-hover`, `bg-primary-active`, `bg-input-bg`, `text-danger`, `border-danger`, `bg-danger-bg`, `text-success bg-success-bg`, `text-warning bg-warning-bg`, `text-info bg-info-bg`, `text-text-tertiary`, `text-text-muted`, `text-link`, `font-heading`, `font-mono` `[LEÍDO app/globals.css y DESIGN.md, 19:20]`. **No toques `app/globals.css`.**
- `components/ui/button.tsx` hoy: alto por defecto `h-8`, hover del primario `hover:bg-primary/80`, destructivo con relleno `bg-destructive/10`, y clases `dark:` `[LEÍDO 19:20]`. `components/ui/input.tsx`: `h-8`, `bg-transparent`, `md:text-sm`, clases `dark:`.
- `DESIGN.md` dice: un solo tema claro, **sin `dark:`**; 44 px o no se toca; texto de campo a 16 px; destructivo en contorno `danger`, nunca relleno rojo.

**Qué construir.**
1. `components/ui/button.tsx`:
   - talla `default` → `h-11` (44 px), `sm` → `h-9` (36 px, densidad compacta de escritorio), `icon` → `size-11`, `icon-sm` → `size-9`. Deja `xs`, `lg`, `icon-xs`, `icon-lg` como están.
   - variante `default`: `hover:bg-primary-hover active:bg-primary-active` en vez de `hover:bg-primary/80`.
   - variante `destructive`: `border-danger bg-transparent text-danger hover:bg-danger-bg`, sin relleno.
   - quita todas las clases `dark:` del archivo.
2. `components/ui/input.tsx`: `h-11`, `bg-input-bg`, `text-base` siempre (quita `md:text-sm`), sin clases `dark:`.
3. `components/shell.tsx`: shell vacío y responsivo = **Encabezado** de `DESIGN.md` (nombre del producto en `font-heading` —usa «Prototipo» como nombre provisional— y el texto «Prototipo para Tiendas 3B»; **sin logotipo**) + `<main>` de una columna con margen 16 en celular y máximo 1,200 px con margen 24 en escritorio.
4. `app/tema/page.tsx`: dentro del shell, todos los componentes de `DESIGN.md` §Components, cada uno con sus estados:
   - Botón: primario, secundario, contorno, fantasma, destructivo, enlace; en reposo, deshabilitado, y una nota en texto de que hover, foco y presionado se prueban con el dedo o el teclado.
   - Campo: con etiqueta visible arriba, con error (causa y salida, `aria-invalid`) y deshabilitado.
   - Estatus: los cuatro tonos con punto y palabra (`rounded-full`).
   - Cifra: una sola, `font-heading tabular-nums`, subrayada en rojo.
   - Fila: 52 px con nombre, SKU en `font-mono`, cantidad a la derecha y estatus.
   - Aviso: contorno completo del tono, el de error con `role="alert"`.
   - Banda: una, roja con texto blanco.
   - Vacío, cargando (esqueleto en `muted`) y error.
   Datos de ejemplo inventados y verosímiles (productos de despensa, tiendas con número); ninguna cifra de 3B.

**Lo que NO se toca.** `app/globals.css`, `app/salud/`, `lib/`, `supabase/`, `datos/`, carpetas de otros carriles, y el resto de `components/ui/`. Nada de producto ni de reto. No se escribe en la base.

**Prueba de cierre (ejecutable).**
1. `npm run lint` y `npm run build` en verde (pega el final de cada salida).
2. Sin colores fuera del tema en lo que cambiaste: `git diff origin/main --stat` y `git diff origin/main | grep -nE "#[0-9a-fA-F]{6}|bg-white|gray-|neutral-|red-|dark:"` **no devuelve nada** (pega la salida vacía).
3. Push de la rama y PR a `main` con `docs/pull_request_template.md`. En la vista previa de Vercel del PR, `/tema` abre; Fer la ve **en su celular** (por eso `requiere pantalla`) y el botón y el campo miden 44 px.
4. `/salud` de esa misma vista previa sigue mostrando `base ok`.

**Para y pregunta** si algo de `DESIGN.md` no alcanza para una pieza (un color, un radio, un estatus que no está): no lo inventes. Si al abrir un archivo ya está como se pide, dilo y no lo toques.

**Entregable.** Rama `carril/ui-sp0-tema` empujada + PR + reporte de 12 líneas en `docs/reportes/U0-tema.md`, escrito al final y de una vez, con modelo y esfuerzo con que corrió, la URL de la vista previa y su apartado «no hecho / simulado».
**Commit sugerido:** `feat(ui): componentes a 44 px y página /tema con Tarima (U0)`

---

## Bitácora de reescrituras

- 2026-11-17 13:20 · creado en S000, sin misiones.
- 2026-11-17 14:54 · S000: ESTADO al formato v1.2 (sello del reloj, `BLOQUEADO hasta`).
- 2026-11-20 19:21 · S001.5: se escribe `U0` (agenda de `PROMPT-APERTURA-S001.md` §3) y se libera el carril; sin auditoría previa.
- 2026-11-20 20:51 · S001.5: auditoría de U0 (PR #1) → Aprobado con anotaciones; carril bloqueado hasta U1.
- 2026-11-20 20:59 · S001.5: resellado después del merge de U0 (`c366e8d`).
- 2026-11-21 09:55 · S002: reto asignado = Reto 2 · Validat3B; giro a Python por lotes en `ml/validat3b/` (compuerta de Fer 09:16). Se escribe la misión 1 y se libera el carril; sin auditoría previa.
- 2026-11-21 11:23 · S003 · U1, U2 y U3 auditadas y fusionadas → se escribe U4 (pitch con datos reales) y se sube el sello.
- 2026-11-21 11:47 · S003 · U4 fusionada (#13) → carril en espera de la decisión A/B (pantalla del pitch con Tarima).
- 2026-11-21 11:54 · S003 · Fer elige A → U5 (pantalla del pitch con Tarima). Se sube el sello.
