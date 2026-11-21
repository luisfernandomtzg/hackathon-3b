# Misiones — carril NUCLEO

## ESTADO · 2026-11-21 09:55
Carril nucleo · dueño Mauski (chat web) · misiones 1 · hechas 0 · siguiente **N1**
Cola: **N1** → N2 (ajuste de umbrales con los errores más caros que reporte D1)
siguiente: **N1**
Última auditoría: ninguna
Qué cambió por esa auditoría: nada
Reescrituras de este documento: 2
Siguiente con modelo: el del asistente de Mauski · clasificación autónoma

---

## N1 — `decidir()`: de la lectura del modelo a la decisión, con reglas puras

`carril: nucleo · dueño Mauski (chat web, archivos completos) · rama: carril/nucleo-sp1-decidir desde main fresco · cuelga de: 1403ab0 · tope: 45 min · clasificación: autónoma · modelo: el de tu asistente`

**Paso 0, obligatorio y automático para tu agente, antes de leer o tocar nada:** `git fetch origin` y `git pull --rebase origin main`; luego crea tu rama desde ese `main`. Si el pull falla por cambios locales, **para y muéstralos**; no los descartes. Antes de cada push: `git fetch origin` + `git rebase origin/main`. Cada quien es dueño de sus archivos: **no edites archivos de otra persona**; si necesitas algo, pídelo.

**Para la persona.** Pega esta misión completa en tu chat. Pídele **archivos completos**. Tú los guardas, corres la prueba y haces push + PR. Tu carpeta hoy: solo `ml/validat3b/decidir.py`, `ml/validat3b/normalizar.py` y `ml/validat3b/test_decidir.py`.

**Hechos del reto que no puedes ver** (todos `[MEDIDO o LEÍDO por el arquitecto, 21-nov 09:16–09:36]`):
- Reto 2 · Validat3B: por cada captura (foto de fachada, foto de producto, foto de etiqueta + metadatos) se decide `aprobada`, `rechazada` o `revision_manual`. Entregable: un JSON con un `Resultado` por captura.
- Puntos de costo (gana el menor): acierto 0 · mandar a revisión manual 1 · rechazar una válida 3 · **aprobar una inválida 10**. Descalifica: precisión de aprobadas < 97 %, JSON válido < 99 %, o entregar tarde.
- Datos de desarrollo: 100 capturas (34 rechazadas, 33 aprobadas, 33 revisión manual) en `datos/privado/metadatos/capturas.csv` y `catalogo_productos.csv`; 300 imágenes en `datos/privado/imagenes/imagenes/`. Motivos de rechazo presentes: «Capturas lejanas» 18, «Capturas borrosas» 11, «Descripción de producto incompleta» 5.
- **Los metadatos no deciden nada:** en las 100, `capture_barcode == product_barcode` y `capture_price` cae en `[min_product_price, max_product_price]`. Todo está en las fotos.
- Negocio (Alfredo, 3B): una captura vale solo si de la foto de producto se leen **marca, descripción y contenido** (g/ml), de la etiqueta se lee el **precio**, y la etiqueta **es de ese producto**. Si no se alcanza a leer el contenido, es lejana/incompleta. Se juzga foto por foto. Prefieren aprobar menos con error casi cero.
- **Datos de 3B (respuesta del comité, 09:50):** tu asistente **sí puede leer** las imágenes y los metadatos de desarrollo para construir y afinar (prompts, umbrales, pruebas). Lo que **no** se vale: commitearlos (viven solo en `datos/privado/`, ignorado), usarlos fuera del reto, llamar a una IA externa **dentro de la solución** (solo el endpoint asignado), ni decidir el set ciego a mano.
- **El criterio de aprobar / rechazar / revisión manual lo diseñamos nosotros** (comité, 09:50). El set ciego, la lista oficial de `reason_code` y el esquema se liberan entre 15:00 y 16:00: los códigos de hoy son provisionales y se cambian por un mapa, sin tocar reglas.
- **Principio de decisión (todo o nada):** solo se aprueba con evidencia completa y clara; ante duda nunca se aprueba. Aprobar mal cuesta 10 y puede descalificar; mandar a revisión cuesta 1.

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

**Qué construir** (solo biblioteca estándar + pydantic; sin red, sin leer archivos: funciones puras):
1. `normalizar.py` — `texto(s)` (minúsculas, sin acentos, sin signos), `parecido(a, b) -> float` 0–1 (proporción de palabras de la más corta contenidas en la otra, apoyado en `difflib` para faltas de ortografía), `a_base(cantidad, unidad) -> (float, "g"|"ml"|"pza")|None` (kg→g, l→ml; acepta «gramo», «gr», «mililitro», «lt», «pieza»…).
2. `decidir.py` — `decidir(captura: Captura, x: Extraccion) -> Resultado`. Umbrales como constantes arriba del archivo. Reglas **en este orden; la primera que se cumple decide**:
   1. `x.origen` es `error` o `sin_modelo` → `revision_manual` · `RC_SIN_LECTURA`.
   2. `foto_de_pantalla` → `rechazada` · `RC_PANTALLA` (`producto=falla`).
   3. `not hay_producto` → `rechazada` · `RC_NO_VISIBLE`.
   4. `nitidez == "borrosa"` → `rechazada` · `RC_BORROSA`.
   5. `encuadre == "lejano"` → `rechazada` · `RC_LEJANA`.
   6. falta `marca` o `descripcion` → `rechazada` · `RC_INCOMPLETA`. Falta el contenido y el producto esperado sí lo tiene → `RC_LEJANA` si `encuadre != "cercano"` o `varios_productos`; si no, `RC_INCOMPLETA`.
   7. Coincidencia con lo esperado: marca contra `capture_brand`, descripción contra `product_name`, contenido contra `unit_quantity_product`/`unit_product` (tolerancia 2 %). Marca claramente distinta (parecido < 0.4) o contenido distinto → `rechazada` · `RC_NO_COINCIDE`. Zona gris (0.4–0.7) → `revision_manual` · `RC_NO_COINCIDE`.
   8. `not hay_etiqueta`, o `precio is None`, o `not legible` → `rechazada` · `RC_SIN_ETIQUETA` (`evidencia_precio=falla`).
   9. `texto_producto` de la etiqueta presente y con parecido < 0.3 contra `product_name` + marca → `revision_manual` · `RC_ETIQUETA_AJENA`.
   10. precio fuera de `[min_product_price, max_product_price]` (solo si ambos > 0) → `revision_manual` · `RC_PRECIO_RANGO`.
   11. `nitidez == "dudosa"` o `encuadre == "medio"` o `varios_productos` → `revision_manual` · sin código.
   12. todo lo anterior pasa → `aprobada`, `reason_code=None`.
   En todos: `precio_detectado = x.etiqueta.precio`, `codigo_barras_detectado = x.codigo_barras_leido or captura.capture_barcode`, `validaciones` coherentes con la regla que disparó, `confidence_score` 0.95 (reglas 2–5, 8 y 12 con todo nítido), 0.8 (6–7 claras), 0.5 (toda `revision_manual`), y `explicacion` en una frase en español que **cite lo leído** («La etiqueta dice 430 g y el producto esperado es de 580 g.»).
3. `test_decidir.py` — con `unittest`, un caso por regla (12) construyendo `Captura` y `Extraccion` a mano con datos inventados, más uno donde la marca viene con acento y mayúsculas distintas y debe aprobar.

**Lo que NO se toca:** `contrato.py` (si no te alcanza, para y pídeselo a Fer), nada fuera de tus tres archivos.

**Prueba de cierre:** `python -m unittest ml.validat3b.test_decidir -v` → 13 pruebas OK.

**Para y pregunta** si una regla te parece contradictoria con lo que dijo negocio. **Entregable:** push + PR + `docs/reportes/N1-decidir.md` (12 líneas). Commit: `feat(ml): decidir() con reglas puras y pruebas`.

---

## Bitácora de reescrituras

- 2026-11-17 13:20 · creado en S000, sin misiones.
- 2026-11-17 14:54 · S000: ESTADO al formato v1.2 (sello del reloj, `BLOQUEADO hasta`).
- 2026-11-21 09:55 · S002: reto asignado = Reto 2 · Validat3B; giro a Python por lotes en `ml/validat3b/` (compuerta de Fer 09:16). Se escribe la misión 1 y se libera el carril; sin auditoría previa.
