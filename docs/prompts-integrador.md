# Misiones — carril INTEGRADOR

## ESTADO · 2026-11-21 10:52
Carril integrador · dueño Fer (Claude Code) · misiones 4 · hechas 3 · siguiente **I2**
Cola: ~~I0~~ ~~I0.1~~ ~~I1~~ → **I2** → I3 (se escribe con el resultado de I2 + N2)
siguiente: **I2**
Última auditoría: I1 → Aprobado con anotaciones ([MEDIDO 10:28] · PR #6 fusionado 10:32). Sprint 1 completo auditado en S003 (10:45–10:52): #8 N1, #9 P1, #11 D1, #7 U2 y #10 U3 fusionados por el chat; `main` = `4c1cea7` [MEDIDO 10:52 en GitHub commits/main]
Qué cambió por esa auditoría: I2 nace de medir N1 sobre las 100 lecturas reales v1 (precisión de aprobadas 15/19 = 79 % → descalifica; costo D1 pesimista 151 / optimista 74 contra 100 / 67 de «todo revisión manual») y de las señales locales de P1
Reescrituras de este documento: 7
Siguiente con modelo: Sonnet 5.5 · esfuerzo high (recomendado: cruza carriles y toca el contrato) · clasificación requiere compuerta (contrato v1.1: la compuerta la da Fer al mandar la orden)

---

## I2 — Lectura v2, señales locales en la tubería y re-decisión sin tokens

`carril: integrador · rama: carril/integrador-sp2-lectura desde main fresco · cuelga de: 4c1cea7 [MEDIDO 10:52 en GitHub: merge del PR #10] · tope: 50 min · clasificación: requiere compuerta (contrato v1.1 — la da Fer al mandar la orden) · modelo: Sonnet 5.5 · esfuerzo: high`

**Primer paso.** `CLAUDE.md` §Disparador completo: `git fetch origin`, `git pull --rebase origin main`, `-Estado -Carril integrador`, relee este ESTADO y devuelve el acuse con **sello `10:52`** y la punta de `origin/main`, que debe ser `4c1cea7` (si hay algo encima, lístalo). Corre todo con `.venv\Scripts\python`. Si ya está hecho, dilo y no lo toques.

**Hechos que no puedes ver**
- `[MEDIDO 10:44 por el arquitecto, sobre salidas/extracciones.json v1 + capturas.csv]` `decidir()` de N1 aplicado a las 100 lecturas reales: aprobó 19, **15 correctas → precisión 79 % (descalifica, mínimo 97 %)**. Matriz real→pred: aprobada 15/3 rech/15 manual · rechazada 2 aprob/22/10 · manual 2 aprob/23 rech/8. Costo con `evaluar.py` de D1: pesimista 151, optimista 74; «todo revisión manual» = 100 / 67.
- **Ojo:** `correr.py` ya importa `decidir.py` de N1 en cuanto existe (está en `main` desde 10:49). Hoy cualquier corrida produce esas cifras.
- Las 4 aprobadas falsas: 489454 y 241497 (reales «Capturas lejanas») el modelo las leyó `nitida`+`cercano` con marca, descripción y contenido completos → **el prompt v1 no distingue lejana**. 206200 (Aurrera chocolate) y 568678 (esperado Purina, leído «Purina Felix»: submarca) son reales `revision_manual`.
- 8 válidas caen a revisión por la regla 7 porque el modelo copia la descripción entera del empaque («Leche entera 100 % de vaca, ultrapasteurizada…» contra «Leche entera UHT»). 3 válidas se rechazan por contenido: `product_name` trae «485g (total: 820g)» y el modelo lee el total; en 621992 empaque 560 g vs catálogo 290 g y aun así es válida. **Esas reglas son de Núcleo (N2); tú no tocas `decidir.py`.**
- `[REPORTADO P1, Alan]` `ml/validat3b/local.py` → `senales_locales(captura, dir_datos) -> dict` sin tokens: nitidez del producto mediana 160 en borrosas vs 310 en válidas; nitidez de etiqueta 46 en «descripción incompleta» vs 281; código de barras leído solo 20/100 (coincide 7); 25 fachadas distintas en 100. En lejanas la nitidez es igual o mayor: **no las detecta**.
- `[LEÍDO]` `ml/requirements.txt` ya trae numpy, pillow y zxing-cpp.
- Tokens v1: 1,661 de entrada fijos + ~200 de salida por captura; la corrida de las 100 fue 175,259 tokens en 40 s con 4 hilos.

**Qué construir**
1. **Contrato v1.1** (`ml/validat3b/contrato.py`, compatible hacia atrás; todo campo nuevo con valor por omisión): `LecturaProducto.contenido_legible: Optional[bool] = None` («¿alcanzas a leer el número de contenido impreso en el empaque?») y `Extraccion.senales: dict[str, Any] = {}` (las señales de `senales_locales`). Nada más. Las 14 pruebas de N1, las de P1 y las de D1 tienen que seguir en verde sin tocarlas.
2. **Prompt v2** en `extraer.py` (`PROMPT_VERSION = "v2"`, así no lee caché v1):
   - `encuadre` se define por legibilidad: «lejano» si el texto del frente (marca, descripción y contenido) no se lee con claridad, aunque la foto sea nítida; pide `contenido_legible`.
   - `descripcion`: el nombre corto del producto tal como dice el frente, máximo 6 palabras, sin ingredientes ni leyendas.
   - `marca`: la marca principal; si hay submarca, `"Marca Submarca"`.
   - `contenido_*`: el contenido neto que dice el frente; si hay dos (drenado y total), el **drenado**, y pon el otro en la descripción.
   - Mantén el formato JSON y `max_tokens=400`. No subas la resolución: los tokens cuentan 10 %.
3. **Señales en la tubería:** en `correr.procesar`, `ext.senales = senales_locales(captura, dir_datos)` antes de `decidir()`. Nunca lanza; si falla, `{}`.
4. **Re-decisión sin tokens:** `correr --desde-extracciones salidas/extracciones.json` vuelve a aplicar `decidir()` sobre lecturas guardadas sin llamar al endpoint (para que N2 y D2 iteren gratis). Si una lectura guardada no tiene `senales`, las calcula en local.
5. Quita `ml/evaluador.py` (de Mau, entró sin auditar y lo sustituye `evaluar.py` de D1) en un commit aparte, mensaje `chore(ml): quitar evaluador.py duplicado (lo sustituye evaluar.py de D1)`.

**Contrato que consumes / produces:** `contrato.py` v1.1 (lo produces tú, eres el dueño). Datos simulados: ninguno; corre contra `datos/privado`.

**No se toca:** `decidir.py`, `normalizar.py`, `local.py`, `evaluar.py`, `visor.py` ni sus pruebas (son de Núcleo, Pitch, Datos y UI). `datos/` y `salidas/` no se commitean.

**Prueba de cierre (ejecutable):**
1. `.venv\Scripts\python -m unittest ml.validat3b.test_decidir ml.validat3b.test_local ml.validat3b.test_evaluar -v` → todo OK.
2. `.venv\Scripts\python -m ml.validat3b.correr --datos datos/privado --salida salidas/resultados.json --hilos 4` (llama al endpoint: ~100 llamadas, ~180k tokens).
3. `.venv\Scripts\python -m ml.validat3b.evaluar --resultados salidas/resultados.json --capturas datos/privado/metadatos/capturas.csv` → copia en el reporte JSON válido, aprobadas/falsas/precisión, costo pesimista y optimista, y la matriz.
4. Contra v1: cuántas de las 18 lejanas reales salen ahora con `encuadre="lejano"` o `contenido_legible=false` (antes 489454 y 241497 salían «cercano»). Es la medición que decide si v2 sirve.
5. `--desde-extracciones` sobre el archivo recién generado da exactamente los mismos `resultados.json` (compáralos) y no gasta tokens (`tokens.csv` no crece).
6. `git status --short` sin `datos/` ni `salidas/`.

**Para y pregunta** si el prompt v2 sube los tokens de entrada más de 10 % o si algo pide tocar `decidir.py`. Si v2 empeora la lectura de las válidas (más `null` en contenido), dilo con números y no lo compenses.

**Entregable:** push de la rama + `docs/reportes/I2-lectura.md` de 12 líneas (al final y de una vez), con modelo y esfuerzo, la tabla v1 vs v2 (tokens por captura, lejanas detectadas, precisión, costo) y su «no hecho / simulado». Además, comprime `salidas/extracciones.json`, `resultados.json`, `tokens.csv` y `locales.csv` (de `python -m ml.validat3b.local --datos datos/privado --salida salidas/locales.csv`) en `salidas-sp2.zip`, sin `cache/`, para que Fer lo comparta con Mauski (N2) y Sergio (D2).

Mensaje de commit sugerido: `feat(ml): lectura v2, señales locales en la tubería y re-decisión sin tokens (I2)`

---


## I1 — Esqueleto del motor Validat3B: contrato, cargador, cliente del endpoint, extracción v1 y corrida de punta a punta [HECHA · Aprobado con anotaciones]

`carril: integrador · rama: carril/integrador-sp1-motor desde main fresco · cuelga de: 1403ab0 [REPORTADO: salida de git push de Fer, 09:36; refs/heads/main leído del disco 09:38] · tope: 45 min · clasificación: autónoma · modelo: Sonnet 5.5 · esfuerzo: medium (recomendado)`

**Paso 0, obligatorio y automático para tu agente, antes de leer o tocar nada:** `git fetch origin` y `git pull --rebase origin main`; luego crea tu rama desde ese `main`. Si el pull falla por cambios locales, **para y muéstralos**; no los descartes. Antes de cada push: `git fetch origin` + `git rebase origin/main`. Cada quien es dueño de sus archivos: **no edites archivos de otra persona**; si necesitas algo, pídelo.

**Primer paso.** `CLAUDE.md` §Disparador completo (fetch, pull --rebase, `-Estado -Carril integrador`, relee este ESTADO, acuse con sello `09:55` y punta de `origin/main`: debe ser el commit «docs: misiones SP1…» que cuelga directo de `1403ab0`; si hay algo más, lístalo).

**Giro del día (compuerta de Fer, 09:16):** el reto es una competencia por lotes, no una app. El producto es **Python local en `ml/validat3b/`**. Next.js, Supabase y Vercel NO se tocan en esta misión. El repo ahora es privado.

**Hechos del reto que no puedes ver** (todos `[MEDIDO o LEÍDO por el arquitecto, 21-nov 09:16–09:36]`):
- Reto 2 · Validat3B: por cada captura (foto de fachada, foto de producto, foto de etiqueta + metadatos) se decide `aprobada`, `rechazada` o `revision_manual`. Entregable: un JSON con un `Resultado` por captura.
- Puntos de costo (gana el menor): acierto 0 · mandar a revisión manual 1 · rechazar una válida 3 · **aprobar una inválida 10**. Descalifica: precisión de aprobadas < 97 %, JSON válido < 99 %, o entregar tarde.
- Datos de desarrollo: 100 capturas (34 rechazadas, 33 aprobadas, 33 revisión manual) en `datos/privado/metadatos/capturas.csv` y `catalogo_productos.csv`; 300 imágenes en `datos/privado/imagenes/imagenes/`. Motivos de rechazo presentes: «Capturas lejanas» 18, «Capturas borrosas» 11, «Descripción de producto incompleta» 5.
- **Los metadatos no deciden nada:** en las 100, `capture_barcode == product_barcode` y `capture_price` cae en `[min_product_price, max_product_price]`. Todo está en las fotos.
- Negocio (Alfredo, 3B): una captura vale solo si de la foto de producto se leen **marca, descripción y contenido** (g/ml), de la etiqueta se lee el **precio**, y la etiqueta **es de ese producto**. Si no se alcanza a leer el contenido, es lejana/incompleta. Se juzga foto por foto. Prefieren aprobar menos con error casi cero.
- **Datos de 3B (respuesta del comité, 09:50):** tu asistente **sí puede leer** las imágenes y los metadatos de desarrollo para construir y afinar (prompts, umbrales, pruebas). Lo que **no** se vale: commitearlos (viven solo en `datos/privado/`, ignorado), usarlos fuera del reto, llamar a una IA externa **dentro de la solución** (solo el endpoint asignado), ni decidir el set ciego a mano.
- **El criterio de aprobar / rechazar / revisión manual lo diseñamos nosotros** (comité, 09:50). El set ciego, la lista oficial de `reason_code` y el esquema se liberan entre 15:00 y 16:00: los códigos de hoy son provisionales y se cambian por un mapa, sin tocar reglas.
- **Principio de decisión (todo o nada):** solo se aprueba con evidencia completa y clara; ante duda nunca se aprueba. Aprobar mal cuesta 10 y puede descalificar; mandar a revisión cuesta 1.

- Endpoint: Azure AI Foundry con el SDK `anthropic` (`from anthropic import AnthropicFoundry`), `base_url="https://softwaredevelopment-resource.services.ai.azure.com/anthropic"`, modelo único `claude-haiku-5-5`, llave en la variable `FOUNDRY_API_KEY` (Fer la pone en `.env.local`; tú **no la imprimes, no la escribes en ningún archivo versionado**). `[LEÍDO: página del reto, 09:19]`
- Los tokens por captura cuentan 10 % de la calificación y el límite por minuto es compartido: cada llamada se cachea y se registra.
- Puedes mirar algunas imágenes de desarrollo para afinar el prompt de lectura; en el reporte van conteos, no filas.

**Contrato v1 — `ml/validat3b/contrato.py`, YA ESTÁ EN `main`: impórtalo, no lo edites ni lo recrees.** Va aquí completo para que tu asistente lo conozca. Pydantic v2.

```python
from typing import Literal, Optional
from pydantic import BaseModel, Field

Decision = Literal["aprobada", "rechazada", "revision_manual"]
OkFalla = Literal["ok", "falla"]

# Códigos PROVISIONALES: la lista oficial aún no nos la entregan. Se usan SOLO por estas constantes.
RC_BORROSA = "CAPTURA_BORROSA"; RC_LEJANA = "CAPTURA_LEJANA"; RC_INCOMPLETA = "DESCRIPCION_INCOMPLETA"
RC_NO_COINCIDE = "PRODUCTO_NO_COINCIDE"; RC_NO_VISIBLE = "PRODUCTO_NO_VISIBLE"; RC_PANTALLA = "FOTO_DE_PANTALLA"
RC_SIN_ETIQUETA = "SIN_ETIQUETA_PRECIO"; RC_ETIQUETA_AJENA = "ETIQUETA_NO_CORRESPONDE"
RC_PRECIO_RANGO = "PRECIO_FUERA_DE_RANGO"; RC_FACHADA = "FACHADA_INCORRECTA"; RC_SIN_LECTURA = "SIN_LECTURA"

class Captura(BaseModel):                      # una fila de capturas.csv
    capture_id: str; capture_store_name: str; capture_date: str
    capture_barcode: str; capture_price: Optional[float] = None; capture_brand: Optional[str] = None
    id_product: int; product_name: str; product_barcode: str
    product_price: Optional[float] = None; min_product_price: Optional[float] = None; max_product_price: Optional[float] = None
    unit_product: Optional[str] = None; unit_quantity_product: Optional[float] = None   # p. ej. "gramo", 1000.0
    product_group: Optional[str] = None; product_line: Optional[str] = None
    facade_file: str; product_file: str; shelf_file: str                                # rutas "imagenes/CAP-..._x.jpg"
    decision_esperada: Optional[str] = None; motivo_rechazo: Optional[str] = None       # solo en desarrollo

class LecturaProducto(BaseModel):              # lo que el modelo LEE en la foto del producto
    hay_producto: bool
    marca: Optional[str] = None; descripcion: Optional[str] = None
    contenido_cantidad: Optional[float] = None; contenido_unidad: Optional[str] = None  # "g","kg","ml","l","pza"
    nitidez: Literal["nitida", "dudosa", "borrosa"] = "dudosa"
    encuadre: Literal["cercano", "medio", "lejano"] = "medio"
    varios_productos: bool = False; foto_de_pantalla: bool = False

class LecturaEtiqueta(BaseModel):              # lo que el modelo LEE en la foto de la etiqueta
    hay_etiqueta: bool
    texto_producto: Optional[str] = None       # el nombre del producto tal como lo dice la etiqueta
    precio: Optional[float] = None             # el precio unitario vigente
    tipo_precio: Optional[Literal["regular", "oferta", "volumen"]] = None
    otros_precios: list[float] = Field(default_factory=list)
    legible: bool = False

class Extraccion(BaseModel):
    capture_id: str
    producto: LecturaProducto; etiqueta: LecturaEtiqueta
    codigo_barras_leido: Optional[str] = None; cadena_en_fachada: Optional[str] = None
    tokens_entrada: int = 0; tokens_salida: int = 0
    origen: Literal["modelo", "cache", "sin_modelo", "error"] = "sin_modelo"

class Validaciones(BaseModel):
    tienda_fachada: OkFalla = "ok"; producto: OkFalla = "ok"; codigo_barras: OkFalla = "ok"; evidencia_precio: OkFalla = "ok"

class Resultado(BaseModel):                    # FORMATO OFICIAL de salida, una por captura
    capture_id: str; decision: Decision
    confidence_score: float = Field(ge=0, le=1)
    reason_code: Optional[str] = None
    validaciones: Validaciones
    precio_detectado: Optional[float] = None; codigo_barras_detectado: Optional[str] = None
    explicacion: str
```

Firmas entre carriles: `cargar.cargar_capturas(dir_metadatos) -> list[Captura]` (Integrador) · `extraer.extraer(captura, dir_datos) -> Extraccion` (Integrador) · `decidir.decidir(captura, extraccion) -> Resultado` (Núcleo, función pura) · `evaluar.py` (Datos) · `visor.py` (UI).

**Qué construir** (todo en `ml/validat3b/`; dependencias ya listadas en `ml/requirements.txt`; entorno en `.venv`, ya ignorado):
1. `contrato.py`, `ml/requirements.txt`, los `__init__.py`, `salidas/` en `.gitignore` y `FOUNDRY_API_KEY=` en `.env.example` **ya están en `main`** (los subió Fer con estas misiones): no los recrees; el contrato solo cambia con compuerta de Fer.
2. `cargar.py` — `cargar_capturas(dir_metadatos)` lee `capturas.csv` (BOM utf-8; códigos de barras como **texto**), NaN → `None`.
3. `cliente.py` — cliente `AnthropicFoundry`; reintentos con espera exponencial ante 429/5xx (máx. 5); **caché en disco** `salidas/cache/<sha1(prompt_version + bytes de imágenes)>.json`; registro `salidas/tokens.csv` (capture_id, tokens_entrada, tokens_salida, segundos, origen).
4. `extraer.py` — `extraer(captura, dir_datos)`: **una** llamada por captura con la foto de producto y la de etiqueta (NO la fachada en v1), reducidas a 768 px de lado mayor en JPEG calidad 80; prompt en español, corto, que pide **solo leer** (no juzgar) y devolver JSON con la forma de `LecturaProducto` + `LecturaEtiqueta`; `max_tokens` 400; si el JSON no valida, un reintento y luego `origen="error"`. `PROMPT_VERSION = "v1"`. No le pases al modelo el producto esperado en v1 (lectura a ciegas: evita que «lea» lo que le dices).
5. `decidir.py` — **solo si no existe** (lo entrega Núcleo en N1): provisional que manda todo a `revision_manual` con `reason_code=RC_SIN_LECTURA`.
6. `correr.py` — `python -m ml.validat3b.correr --datos datos/privado --salida salidas/resultados.json [--limite N] [--sin-modelo] [--hilos 4] [--mapa-codigos mapa.json]` (el mapa traduce códigos provisionales a los oficiales al escribir; además exporta `salidas/resultados.csv` con las mismas columnas para analistas): carga, extrae (o salta con `--sin-modelo`), decide, **valida cada `Resultado`** y escribe una lista JSON; guarda también `salidas/extracciones.json`. **Cualquier excepción por captura se atrapa y esa captura sale como `revision_manual`**: el archivo siempre trae una entrada válida por captura. Al final imprime: capturas, válidas, tokens totales, tokens por captura, segundos.
7. `ml/README.md`: cómo instalar y correr (6 líneas): es parte del entregable oficial («código ejecutable con instrucciones»).

**Lo que NO se toca:** `app/`, `components/`, `lib/`, `supabase/`, `datos/privado/` (solo lectura), `docs/prompts-*.md`.

**Prueba de cierre.**
- `python -m ml.validat3b.correr --datos datos/privado --salida salidas/resultados.json --sin-modelo` → `100 capturas · 100 válidas · 0 tokens`.
- `python -m ml.validat3b.correr --datos datos/privado --salida salidas/prueba5.json --limite 5` → 5 extracciones con `origen=modelo`, tokens por captura impresos; segunda corrida idéntica → `origen=cache` y 0 tokens nuevos.
- `git status --short` no muestra nada de `datos/` ni de `salidas/`; `git grep -n "FOUNDRY_API_KEY" -- . ":!*.md" ":!.env.example"` solo muestra lecturas de entorno, ningún valor.

**Para y pregunta** si el endpoint responde 401/403/404, si `claude-haiku-5-5` no acepta imágenes, o si algo exige tocar otra carpeta. Si ya existe algo de esto, dilo y no lo rehagas.

**Entregable:** push de la rama + PR + `docs/reportes/I1-motor.md` (12 líneas, al final), con **tokens por captura medidos** y el apartado «no hecho / simulado». Commit sugerido: `feat(ml): esqueleto del motor Validat3B (contrato, extraccion v1, corrida)`.

---

## I0.1 — shadcn, Supabase y Vercel conectados [HECHA · Aprobado con anotaciones]

`carril: integrador · rama: main · tope: 30 min · clasificación: requiere pantalla · modelo: general · esfuerzo: medium`
`cuándo: jueves o viernes; a más tardar el sábado 9:30`

**Hechos que no puedes ver.** I0 ya está en `main`: Next 16.4.6, ESLint con fronteras probadas en rojo, `/salud` funcionando en local `[MEDIDO S000]`. shadcn no se pudo instalar desde donde se generó. El repo es **público** (así Vercel Hobby despliega commits de todos); jamás entran secretos ni datos de 3B.

1. `npx shadcn@latest init` (base neutral, sin cambiar la carpeta de componentes) y `npx shadcn@latest add button card input table badge dialog select tabs skeleton sonner`. Confirma que no reescribió `app/globals.css` de forma que rompa el build.
2. `npm run lint` y `npm run build` en verde.
3. Fer crea el proyecto de Supabase `hackathon-3b` y copia URL y llave secreta a `.env.local` (no al repo). `npm run dev` → `/salud` dice `base ok`.
4. Fer importa el repo en Vercel, pone `NEXT_PUBLIC_SUPABASE_URL` y `SUPABASE_SECRET_KEY` en el proyecto y despliega. En el celular, `/salud` de la URL pública muestra el SHA de `main` y `base ok`.
5. Un compañero hace push de una rama `prueba/<nombre>` y se comprueba que Vercel genera su vista previa.
6. Anota URL, proyecto de Supabase y tiempo push→URL en `docs/contexto-vigente-hackathon-3b.md` (sección Recursos).

7. **Probar el candado en las dos direcciones** (desde la raíz del repo): `powershell -NoProfile -ExecutionPolicy Bypass -File .\remoto-hackathon-3b.ps1 -Estado -Carril integrador` debe decir **SIGUE · I0.1**. Después de escribir y commitear el reporte `docs/reportes/I0.1-conexion.md`, la misma orden debe decir **PARO** (contenido: I0.1 ya tiene reporte; pierna 2). Pega las dos salidas en el reporte. Una corrida sin el `-Carril` muestra los cuatro carriles: UI, Núcleo y Datos deben decir NADA QUE EJECUTAR.

**Prueba de cierre:** captura de `/salud` pública con SHA y `base ok`, y el tiempo push→URL. Más las dos salidas de `-Estado` del paso 7.
**Reporte:** `docs/reportes/I0.1-conexion.md`. **Commit:** `chore: shadcn y conexión a Supabase/Vercel (I0.1)`

---

## I0 — Andamiaje [HECHA en S000] y tubería de despliegue

`carril: integrador · rama: main (repo recién creado) · tope: 30 min · clasificación: requiere pantalla (verificar la URL)`
`modelo: general · esfuerzo: medium`

**Contexto.** Repo sin código de producto. Stack decidido: Next.js (App Router, TypeScript) + Tailwind + shadcn/ui, Supabase (Postgres), Vercel. Arquitectura en `docs/arquitectura-provisional.md` si está copiada; si no, lo esencial está aquí. Usa las versiones estables vigentes: consulta la documentación oficial en vez de asumir de memoria.

**Qué hacer**

1. Crea la app con `create-next-app` (TypeScript, App Router, Tailwind, ESLint, sin carpeta `src/`). El directorio ya tiene `CLAUDE.md`, `README.md`, `docs/` y otros: genera en una carpeta temporal y mueve el contenido a la raíz **sin pisar** los archivos existentes (fusiona `.gitignore`).
2. Inicializa shadcn/ui y agrega solo: button, card, input, table, badge, dialog, select, tabs, skeleton, sonner.
3. Crea la estructura vacía, con un `README.md` de una línea en cada carpeta que diga de qué carril es:
   `app/` · `components/` · `lib/contrato/` · `lib/dominio/` · `lib/datos/` · `lib/ia/` · `supabase/migrations/` · `datos/semilla/` · `datos/privado/` (ignorada) · `ml/`
4. `lib/datos/servidor.ts`: cliente de Supabase **solo de servidor** (`import "server-only"`), con `NEXT_PUBLIC_SUPABASE_URL` y `SUPABASE_SECRET_KEY`.
5. Ruta `/salud` (componente de servidor): muestra el SHA corto del commit desplegado (variable de sistema de Vercel; «local» si no existe), la hora del servidor y el resultado de una consulta trivial a la base (`ok` o el motivo del fallo, sin filtrar secretos).
6. Regla ESLint `no-restricted-imports`: `app/**` y `components/**` no importan `@supabase/*` ni `lib/ia`; `lib/dominio/**` no importa `next/*`, `@supabase/*` ni `app/`. **Demuestra que se pone roja:** mete una violación en cada grupo, corre el lint, pega la salida, quita la violación y vuelve a correr.
7. Página de inicio mínima con el nombre provisional del proyecto y una liga a `/salud`. Nada más.
8. Completa la sección «Comandos» del `README.md` con los que hayas ejecutado de verdad.

**Lo que NO se hace:** login, base de datos con tablas de negocio, componentes de producto, landing, pruebas de más. No se toca `CLAUDE.md`.

**Para y pregunta si:** `create-next-app` o shadcn piden una decisión que no está aquí; falta una variable de entorno; algo exige borrar un archivo existente.

**Prueba de cierre**

- `npm run lint` y `npm run build` en verde (pega la salida), más las dos corridas en rojo del punto 6.
- En local, `/salud` responde y dice `ok` para la base (o el motivo exacto si no hay variables).
- El orquestador conecta el repo a Vercel, pone las variables y verifica en un celular que `/salud` de la URL pública muestra el SHA de `main`.

**Reporte:** `docs/reportes/I0-andamiaje.md`, con el formato de `CLAUDE.md`. Incluye cuánto tardó de push a URL actualizada.

**Commit sugerido:** `chore: andamiaje Next + Supabase + reglas de frontera (I0)`

---

## Bitácora de reescrituras

- 2026-11-17 13:20 · creado en S000 con I0.
- 2026-11-17 13:55 · I0 hecha en S000 (plantilla previa); se agrega I0.1.
- 2026-11-17 14:54 · S000: ESTADO al formato v1.2 (sello del reloj, campos que lee `-Estado`); I0.1 gana el paso 7 (probar el candado en las dos direcciones).
- 2026-11-17 16:32 · auditoría de I0.1 (Aprobado con anotaciones); candado probado en las dos direcciones: PARO a las 16:32 con el ESTADO viejo, liberado por esta reescritura.
- 2026-11-21 09:55 · S002: reto asignado = Reto 2 · Validat3B; giro a Python por lotes en `ml/validat3b/` (compuerta de Fer 09:16). Se escribe la misión 1 y se libera el carril; sin auditoría previa.
- 2026-11-21 10:34 · S002: auditoría de I1 (PR #6) → Aprobado con anotaciones; fusionado; carril bloqueado hasta I2 (S003).
- 2026-11-21 10:52 · S003 · auditoría del sprint 1 (N1 medido sobre las 100 lecturas reales: 79 % de precisión) → se escribe I2 (lectura v2, contrato v1.1, señales locales en la tubería, re-decisión sin tokens) y se quita el BLOQUEADO.
