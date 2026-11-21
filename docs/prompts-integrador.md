# Misiones — carril INTEGRADOR

## ESTADO · 2026-11-21 09:55
Carril integrador · dueño Fer (Claude Code) · misiones 3 · hechas 2 · siguiente **I1**
Cola: ~~I0~~ ~~I0.1~~ → **I1** → I2 (prompt v2 + fachada con caché + calibración de umbrales con el arnés de D1)
siguiente: **I1**
Última auditoría: I0.1 → Aprobado con anotaciones (S000, 17-nov 16:32)
Qué cambió por esa auditoría: nada
Reescrituras de este documento: 5
Siguiente con modelo: Sonnet 5.5 · esfuerzo medium (recomendado) · clasificación autónoma

---

## I1 — Esqueleto del motor Validat3B: contrato, cargador, cliente del endpoint, extracción v1 y corrida de punta a punta

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
