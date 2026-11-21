# Misiones — carril NUCLEO

## ESTADO · 2026-11-21 13:15
Carril nucleo · dueño Mauski (chat web) · misiones 6 · hechas 6 · siguiente **NINGUNO**
Cola: ~~N1~~ ~~N2~~ ~~N3~~ ~~N4~~ ~~N5~~ ~~N6~~ (parte de 15:00 pendiente)
siguiente: **NINGUNO — BLOQUEADO hasta que el comité publique la lista oficial de reason_code (15:00–16:00)** (la libera Fer al pegarla; entonces Mauski llena `docs/entrega/codigos.md` y edita `mapa_codigos.json`, PR que aprueba Fer)
Última auditoría: N6 → Aprobado ([LEÍDO 13:11: solo docs; decidir.py y mapa idénticos a main; 11 códigos con su regla] · PR #33 fusionado → 96fa65f). Conteos en sp8 [MEDIDO 13:11]: CAPTURA_LEJANA 21 · DESCRIPCION_INCOMPLETA 17 · PRODUCTO_NO_COINCIDE 12 (revisión) · ETIQUETA_NO_CORRESPONDE 6 (revisión) · CAPTURA_BORROSA 1 · SIN_ETIQUETA_PRECIO 1 · resto 0
Qué cambió por esa auditoría: nada en el motor
Reescrituras de este documento: 8
Siguiente con modelo: el del asistente de Mauski · requiere compuerta

---

## N6 [HECHA (parte 1) · Aprobado] — Dejar listo el cambio a la lista oficial de `reason_code`

`rama: carril/nucleo-sp3-codigos-oficiales desde main fresco (f39f48a o posterior) · tope: 20 min ahora + 10 min a las 15:00 · clasificación: autónoma ahora; requiere compuerta a las 15:00`

**Por qué:** entre 15:00 y 16:00 el comité publica la **lista oficial de `reason_code`** junto con el set ciego (comité, 09:50). La entrega aplica `ml/validat3b/mapa_codigos.json` (`entregar` lo carga si existe). Ese mapa se cambia en esa hora y con el reloj encima. Lo que se pueda decidir antes, se decide ahora.

**Hechos que no puedes ver** `[LEÍDO decidir.py y mapa_codigos.json en main, 13:00]`: el motor emite 11 códigos internos: `CAPTURA_BORROSA`, `CAPTURA_LEJANA`, `DESCRIPCION_INCOMPLETA`, `PRODUCTO_NO_COINCIDE`, `PRODUCTO_NO_VISIBLE`, `FOTO_DE_PANTALLA`, `SIN_ETIQUETA_PRECIO`, `ETIQUETA_NO_CORRESPONDE`, `PRECIO_FUERA_DE_RANGO`, `FACHADA_INCORRECTA`, `SIN_LECTURA`. Hoy el mapa los deja iguales (identidad). `reason_code` es `null` en aprobadas y en revisión manual. Los motivos reales del set de desarrollo son solo tres: lejanas 18, borrosas 11, descripción incompleta 5.

**Qué construir ahora (solo documentación):** `docs/entrega/codigos.md`, una página con una tabla de los 11 códigos: **qué regla de `decidir.py` (o `compuerta.py`) lo emite** · **qué significa en palabras de 3B** · **cuántas veces sale en sp7** (si no lo puedes medir, escribe «sin medir») · **con qué código oficial probable se empata** (columna vacía, para las 15:00). Abajo: el procedimiento de 15:00 en 4 pasos (editar el mapa, correr la prueba de `entregar`, PR, avisar a Fer). Agrega la regla: **un código oficial que no tenga equivalente claro va al más cercano y se anota; nunca se inventa uno que no esté en la lista**.

**A las 15:00 (con la lista en mano):** llenas la columna, editas `mapa_codigos.json` (solo los valores) y abres un PR. Fer lo aprueba antes de correr el set ciego.

**No se toca ahora:** código, `mapa_codigos.json`, reglas.

**Prueba de cierre ahora:** la tabla tiene los 11 códigos y cada uno nombra la regla que lo emite; `git diff --stat` muestra solo `docs/`. PR + reporte `docs/reportes/N6-codigos.md` (≤ 8 líneas).

**Commit sugerido:** `docs: tabla de reason_code internos y procedimiento para la lista oficial (N6)`

---

## N5 [HECHA · Aprobado] — Que la explicación de la regla 7 diga lo mismo que su código

`rama: carril/nucleo-sp3-explicacion desde main fresco (aa85b57 o posterior) · tope: 15 min · clasificación: autónoma · solo ml/validat3b/decidir.py y test_decidir.py`

**Por qué:** desde N4 la regla 7 (producto que no coincide) emite `CAPTURA_LEJANA`, pero su `explicacion` sigue diciendo «…no coincide con lo esperado». El jurado lee código y explicación juntos (calidad del dato, 15 %): tienen que contar la misma historia.

**Hecho que no puedes ver** `[MEDIDO 12:41 por el arquitecto con sp6]`: de las 22 rechazadas correctas, 9 salen con `CAPTURA_LEJANA` tras N4; de esas 9, 4 son lejanas reales, 4 borrosas y 1 descripción incompleta. Por eso la frase no debe afirmar «está lejos», sino que **no se distingue bien el producto**.

**Qué construir:** en la regla 7 cambia solo el texto de la explicación, conservando los datos que ya cita (marca, descripción y contenido leídos; lo esperado). Forma: «No se distingue con claridad el producto en la foto (captura lejana o poco nítida): se lee marca «…», descripción «…» y …; se esperaba (…).» El código, la decisión y la confianza **no cambian**. Una prueba en `test_decidir.py` que verifica que la explicación de la regla 7 contiene «No se distingue» (se pone roja con el texto viejo).

**No se toca:** ninguna otra regla, `reason_code`, decisión ni umbral; nada fuera de esos dos archivos. Si ya está hecho, dilo y no lo toques.

**Prueba de cierre:** `python -m unittest ml.validat3b.test_decidir -v` → todo OK, con la prueba nueva. PR + reporte `docs/reportes/N5-explicacion.md` (12 líneas, con «no hecho / simulado»).

**Commit sugerido:** `fix(ml): explicación de la regla 7 coherente con CAPTURA_LEJANA (N5)`

---

## N4 [HECHA · Aprobado con anotaciones] — Que las rechazadas traigan el motivo correcto

`rama: carril/nucleo-sp3-motivo desde main fresco · tope: 40 min · clasificación: autónoma`

**Hechos medidos** (`[MEDIDO 12:00 por el arquitecto sobre salidas-sp4.zip]`): de las 23 capturas rechazadas correctamente, **solo 2** traen el `reason_code` que corresponde a su `motivo_rechazo` real (sección 7 de `evaluar.py`: 2/34). En desarrollo solo existen tres motivos: «Capturas lejanas» 18, «Capturas borrosas» 11, «Descripción de producto incompleta» 5. Hoy la mayoría sale como `PRODUCTO_NO_COINCIDE` (regla 7), que **no aparece nunca** en los datos de 3B. Con `CAPTURA_LEJANA` por omisión en las rechazadas se pasaría de 2 a ~12. La calidad del dato vale 15 % de la calificación.

**Qué hacer:**
1. Mide primero, con `calibrar.py` + `evaluar.py` sección 7 sobre `salidas-sp5.zip` (renombra `sp5_resultados.json`→`resultados.json` y `sp5_extracciones.json`→`extracciones.json`): por cada regla que rechaza, qué código emite y qué motivo real tienen esas capturas.
2. Ajusta **solo el `reason_code` de las rechazadas** (no la decisión): cuando la regla que rechaza no tenga un motivo claro de los tres de 3B, emite el de mayor acierto medido (probablemente `CAPTURA_LEJANA`). No cambies ninguna decisión; la precisión y el costo deben quedar idénticos (compruébalo: 11 aprobadas, 0 falsas, costo 103/38 con lecturas sp5).
3. Quita `traducir()` de `decidir.py` (duplica `correr --mapa-codigos`) y su prueba.
4. Una prueba por cada código que cambies.

**No se toca:** las decisiones, el contrato, `correr.py`, `compuerta.py`, `consenso.py`.

**Prueba de cierre:** pruebas en verde; sección 7 de `evaluar.py` antes y después (de 2/34 a lo que dé); costo y precisión sin cambio. PR + reporte de 12 líneas.

---

## N3 [HECHA · Aprobado con anotaciones] — Códigos oficiales, tipo de precio y explicación

`rama: carril/nucleo-sp3-codigos · tope: 40 min`

1. `ml/validat3b/mapa_codigos.json`: diccionario `{"CODIGO_PROVISIONAL": "CODIGO_OFICIAL"}` con los 11 códigos del contrato mapeados a sí mismos. Cuando el comité libere la lista oficial (15:00–16:00) solo se edita este archivo. Incluye en `test_decidir.py` una prueba de que todo código que emite `decidir()` es llave del mapa.
2. **Precio y tipo de precio** (cuenta en el 15 % de calidad): si la etiqueta trae `otros_precios`, `precio_detectado` es el precio unitario **vigente** que leyó el modelo; si `tipo_precio` es `oferta` o `volumen`, dilo en la `explicacion` («Precio de oferta $24; regular $28»). Si hay dos precios y no se sabe cuál aplica → `revision_manual`.
3. Repasa las 12 `explicacion`: una frase, en español, que cite lo leído y lo esperado. Sin tecnicismos: la va a leer un analista de precios.

**Prueba de cierre:** pruebas en verde y `calibrar` sin cambios de costo a peor.

**Hechos nuevos** (`[MEDIDO 11:40 por el arquitecto]`): con tu N2 + las compuertas de Fer (I3.1, en `main` desde 11:49) el motor da **10 aprobadas, 10 correctas, 100 %, costo 99 / 38**. Después de `decidir()` corre `compuerta.py` (de Fer): código de barras que no coincide → revisión manual, y aprobada con nitidez de etiqueta < 100 → revisión. **No lo dupliques en `decidir.py`.** Las compuertas emiten `reason_code=None`: el mapa de códigos no necesita entrada para ellas. Usa `python -m ml.validat3b.correr --desde-extracciones salidas/extracciones.json ...` para medir sin gastar tokens (llega en `salidas-sp4.zip`).

---

## N2 [HECHA · Aprobado con anotaciones] — Calibrar `decidir()` contra las lecturas reales

`rama: carril/nucleo-sp2-calibrar · tope: 60 min`

**Archivos que comparte Fer en `salidas/`:** `extracciones.json` (lista de `Extraccion` del contrato), `resultados.json` (lista de `Resultado`), `locales.csv` (una fila por captura: `capture_id, codigo_barras_leido, codigo_coincide, nitidez_producto, nitidez_etiqueta, huella_fachada, decision_esperada, motivo_rechazo`). Las etiquetas reales están en `datos/privado/metadatos/capturas.csv` (`decision_esperada`, `motivo_rechazo`, `facade_url`).

**Objetivo medible:** sobre las 100 capturas de desarrollo, **cero aprobadas falsas** (ninguna aprobada cuya real no sea `aprobada`) y el menor costo posible.

**Qué construir:**
1. `ml/validat3b/calibrar.py` — `python -m ml.validat3b.calibrar --extracciones salidas/extracciones.json --capturas datos/privado/metadatos/capturas.csv`: aplica `decidir()` a cada lectura y muestra (a) una tabla **regla que disparó × decisión real** con conteos; (b) la lista de **aprobadas falsas** con lo leído y lo esperado; (c) la lista de **válidas rechazadas** (real `aprobada`, motor `rechazada`) con la regla culpable; (d) costo total con la tabla 0/1/3/10. Para saber qué regla disparó, `decidir()` puede exponer `decidir_con_regla(captura, x) -> (Resultado, int)` y `decidir()` la envuelve.
2. Ajusta en `decidir.py` **solo constantes de umbral y el orden de reglas**, guiado por esa tabla. Prioridad: primero eliminar aprobadas falsas (cuestan 10 y descalifican), luego rescatar válidas rechazadas (3), al final reducir revisión manual (1).
3. **Regla de revisión manual:** con las notas de Sergio sobre las 33 capturas `revision_manual` (te las pasa Fer), redacta la condición que las distingue y agrégala como regla explícita, con su prueba. Si no hay notas a las 12:00, usa lo que muestre tu tabla.
4. Actualiza `test_decidir.py`: cada umbral que cambies lleva un caso que lo fija.

**Prueba de cierre:** `python -m unittest ml.validat3b.test_decidir -v` en verde; la salida de `calibrar` con **0 aprobadas falsas**; en el reporte, costo antes y después.
**No se toca:** el contrato, `extraer.py`, `correr.py`. Si una lectura del modelo viene mal (p. ej. siempre dice «dudosa»), **no lo compenses con reglas raras**: anótalo para Fer, que ajusta el prompt.

**Hechos medidos que no puedes ver** (`[MEDIDO 11:05 por el arquitecto sobre salidas-sp2.zip + capturas.csv]`):
- Usa **`salidas-sp2.zip`** (lecturas v2 del modelo, `resultados.json` con las decisiones reales de `decidir()` y `locales.csv`). Descomprímelo dentro de `salidas/`. El de SP1 ya no sirve.
- Con v2, `decidir()` de N1 aprueba 16 y 14 son correctas: **precisión 87.5 % (descalifica; mínimo 97 %)**. Matriz real→predicha: aprobada 14/2 rech/17 manual · rechazada 1 aprob/24/9 manual · revisión manual 1 aprob/17 rech/15. Costo con `evaluar.py`: pesimista 118, optimista 52 (todo a revisión manual: 100 / 67).
- Las 2 aprobadas falsas: **CAP-206200** (real `revision_manual`) y **CAP-410562** (real rechazada «Capturas borrosas»; nitidez local de etiqueta 99). Válidas aprobadas con nitidez de etiqueta baja: 970141 (83) y 621992 (125).
- La regla 7 manda válidas a revisión porque mide el parecido sobre las palabras de la descripción leída (larga). Medir qué fracción de las palabras del **nombre esperado** aparece en lo leído. Cuando `product_name` trae «(total: NNNg)», cualquiera de los dos pesos vale.
- Fer agrega en I3 un **verificador después de `decidir()`**: una segunda mirada solo a las aprobadas, que baja a revisión manual lo que no pase. No lo toques ni lo dupliques.

---

## N1 [HECHA · Aprobado con anotaciones] — `decidir()`: de la lectura del modelo a la decisión, con reglas puras

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
- 2026-11-21 11:23 · S003 · N1 auditada (79 % sobre lecturas reales v1) → se escribe N2 con los hechos de v2 y se sube el sello.
- 2026-11-21 11:47 · S003 · N2 auditada y fusionada (#16) → se escribe N3 y se sube el sello.
- 2026-11-21 12:26 · S003 · N3 fusionada (#19) → N4 (reason_code de las rechazadas; quitar traducir). Se sube el sello.
- 2026-11-21 12:48 · S004 · N4 auditada y fusionada (#27 → aa85b57; decisiones idénticas, motivo 2/22 → 8/22) → N5 (explicación de la regla 7). Se sube el sello.
- 2026-11-21 13:01 · S004 · N5 aprobada y fusionada (#29) → N6 (preparar el mapa a la lista oficial de reason_code de las 15:00). Se sube el sello.
- 2026-11-21 13:15 · S004 · N6 aprobada y fusionada (#33). Carril bloqueado hasta la lista oficial.
