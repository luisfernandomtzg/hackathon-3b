# Misiones — carril INTEGRADOR

## ESTADO · 2026-11-21 14:46
Carril integrador · dueño Fer (Claude Code) · misiones 14 · hechas 12 · siguiente **I11**
Cola: ~~I0~~ ~~I0.1~~ ~~I1~~ ~~I2~~ ~~I3~~ (Devuelto) ~~I3.1~~ ~~I4~~ ~~I5~~ ~~I6~~ ~~I7~~ ~~I8~~ ~~I9~~ ~~I10~~ (descartada) → **I11**
siguiente: **I11** — BLOQUEADA hasta que Fer pegue en el chat cómo llegó el set ciego y la lista oficial de reason_code (15:00–16:00); el arquitecto ajusta `mapa_codigos.json` y sube el sello
Última auditoría: sp11–sp13 (fuera de cola, corridas de Code) → Aprobado ([MEDIDO 14:44 por el arquitecto: `salidas/sp13/pitch.html` en navegador, 0 falsas · 16 aprobadas · 55 de 100 · 84/27 · 3,192 tokens] · `main` = `e44e52e`)
Qué cambió por esa auditoría: motor final = lectura v3 + N8; `APROBAR_REDACCION_DISTINTA = True` (decisión de Fer 14:45, recomendada por el arquitecto); I10 (consenso de 5) descartada
Reescrituras de este documento: 17
Siguiente con modelo: Sonnet 5.5 · esfuerzo medium (recomendado) · clasificación requiere compuerta
Main: e44e52e [MEDIDO 14:43 en la terminal de Fer]

---

## I11 — Correr el set ciego y dejar la entrega validada

`carril: integrador · trabaja en repo\ sobre carril/integrador-sp4-etiqueta con origin/main fusionado (debe incluir e44e52e) · tope: 30 min · clasificación: requiere compuerta (BLOQUEADA hasta 15:00) · modelo: Sonnet 5.5 · esfuerzo: medium`

**Primer paso.** `git fetch origin && git merge origin/main`; `ml/validat3b/extraer.py` debe decir `PROMPT_VERSION = "v3"` y `ml/validat3b/decidir.py` debe contener `APROBAR_REDACCION_DISTINTA = True` y «5b. (S005)». Si no, **para**. **Esto llama al endpoint: tokens reales** (~3,200 por captura; 100 capturas ≈ 320 mil tokens, ≈ 2–4 min con 4 hilos).

**Hechos que no puedes ver:**
- `[MEDIDO sp13]` en desarrollo: 16 aprobadas · 0 falsas · 84/27 · JSON 100/100. El set ciego **no** trae `decision_esperada`: no hay forma de medir precisión; solo forma.
- `[LEÍDO entregar.py]` localiza `capturas.csv`/`.json` e imágenes aunque cambien de nombre o carpeta, manda a `revision_manual`/`SIN_LECTURA` lo que no tenga fotos y valida un resultado por `capture_id`.

**Qué hacer:**
1. `.venv\Scripts\python -m ml.validat3b.entregar --datos <carpeta del set ciego> --salida entrega/` (si se corta: el mismo comando con `--reanudar`; lo ya leído sale del caché).
2. Pega `entrega/resumen.txt` completo en tu respuesta.
3. **Para y pregunta** si: VALIDACIÓN no dice OK · alguna captura sin resultado · más de 5 % en `SIN_LECTURA` o «Error al procesar» · más de 25 % de aprobadas (en desarrollo fue 16 %) · algún `reason_code` fuera de la lista oficial.

**No se toca:** `decidir.py`, `consenso.py`, `compuerta.py`, `extraer.py`. Nada de ajustar reglas con el set ciego a la vista.

**Prueba de cierre:** VALIDACIÓN OK; una fila por `capture_id` del CSV del set ciego; conteo de decisiones y de `reason_code` en la respuesta.

**Entregable:** `entrega/resultados.json` listo para el canal del comité + `docs/reportes/I11-ciego.md` (≤ 12 líneas, sin datos de 3B). **El contenido de `entrega/` no se commitea.**

---

## I10 — Medir el consenso de 5 lecturas para aprobar (baja el riesgo de descalificación)

`carril: integrador · rama: carril/integrador-sp4-cinco desde origin/main (después del commit de N7) · tope: 20 min · clasificación: autónoma, aprobada por Fer 13:39 · llama al endpoint (≤ 25 llamadas, ~45 mil tokens) · modelo: Sonnet 5.5 · esfuerzo: medium`

**Primer paso.** `CLAUDE.md` §Disparador; acuse con el sello vigente. **Si son más de las 14:25, no la corras: dilo y queda cortada** (el motor se congela 14:30 con consenso de 3).

**Por qué:** `[MEDIDO S003]` el endpoint no acepta `temperature`; una lejana (CAP-489454) aprueba en ~1 de 2 lecturas, así que con 3 unánimes se cuela ~1 de 8 veces y con ~10 aprobadas una sola falsa descalifica (< 97 %). Con 5 unánimes baja a ~1 de 32. `[MEDIDO S005 13:36]` no hay señal local ni de metadatos que la distinga (nitidez de producto 285, precio igual al tecleado). El costo es tokens (10 % de la nota) y quizá 1–2 aprobadas válidas (1 punto cada una).

**Qué hacer:**
1. `ml/validat3b/consenso.py`: `LECTURAS_PARA_APROBAR = 5` (ya hay 4 variantes de caché). Ajusta `test_consenso.py` (hoy afirma 3) y agrega un caso: aprueban las lecturas 1–4 y la 5ª no → `revision_manual`.
2. Copia `salidas/sp8/cache` a `salidas/sp10/cache` y corre el motor normal: `--datos datos/privado --salida salidas/sp10/resultados.json --hilos 4`. Solo deben salir llamadas nuevas para las lecturas 4 y 5 de las aprobadas. **Para y pregunta** si hay más de 25 filas `origen == "modelo"`.
3. `python -m ml.validat3b.evaluar --resultados salidas/sp10/resultados.json`.

**Regla de decisión (ya aprobada):** si quedan **≥ 8 aprobadas y 0 falsas**, el 5 se queda → PR. Si quedan menos de 8, o aparece una falsa, **no se fusiona**: reporta y el motor sigue con 3.

**Prueba de cierre:** tabla sp9 → sp10: aprobadas · falsas · costo pesimista/optimista · llamadas nuevas · tokens nuevos · tokens por captura nuevos (= 2,390 + tokens nuevos ÷ 100). Pruebas en verde.

**Entregable:** PR + `docs/reportes/I10-cinco.md` (≤ 10 líneas). El arquitecto actualiza guion, cifras, láminas y ficha con lo medido; **no los toques**.

---

## I9 — Verificar sp9 por el camino oficial, regenerar pitch.html y armar el zip

`carril: integrador · rama: carril/integrador-sp4-sp9 desde origin/main (después del commit de N7 del bloque de git de S005) · tope: 10 min · clasificación: autónoma · 0 tokens · modelo: Sonnet 5.5 · esfuerzo: low`

**Primer paso.** `CLAUDE.md` §Disparador; acuse con **sello `13:41`**; `ml/validat3b/decidir.py` de `origin/main` debe contener «7a. (S005)». Si no, **para**: falta el commit de N7.

**Hechos que no puedes ver:**
- `[MEDIDO 13:38 por el arquitecto]` `salidas/sp9/resultados.json` ya existe: lo armó el arquitecto re-decidiendo las lecturas de sp8 con la regla 7a, **sin** pasar por `correr`. Contra sp8 cambian exactamente 6 capturas, todas de `rechazada` a `revision_manual` con `PRODUCTO_NO_COINCIDE`: CAP-368433, CAP-635506, CAP-387384, CAP-847183, CAP-586021, CAP-659322. `evaluar`: 10 aprobadas · 0 falsas · 92 pesimista / 35 optimista · matriz aprob 10/0/23 · rech 0/22/12 · man 0/12/21.
- `[MEDIDO S004]` `correr --desde-extracciones` no sirve con consenso: se regenera desde el caché del cliente.

**Qué hacer:**
1. Copia `salidas/sp8/cache` a `salidas/sp9r/cache` y corre el motor normal (`--datos datos/privado --salida salidas/sp9r/resultados.json --hilos 4`). **Para y pregunta** si aparece alguna fila `origen == "modelo"`.
2. Compara `salidas/sp9r/resultados.json` contra `salidas/sp9/resultados.json`: **0 diferencias** en `decision`, `reason_code` y `explicacion`. **Para y pregunta** si hay alguna.
3. `python -m ml.validat3b.visor --datos datos/privado --resultados salidas/sp9/resultados.json --salida salidas/sp9/visor.html --pitch CAP-434912,CAP-563575,CAP-350077`.
4. Arma `..\salidas-sp9.zip` (resultados json y csv, extracciones, tokens; sin `cache/`).

**No se toca:** código, `datos/`, `docs/pitch/`.

**Prueba de cierre:** la tabla del paso 2 = 0 · 0 · 0; `evaluar` sobre sp9r = 92 / 35, 10 aprobadas, 0 falsas; `salidas/sp9/pitch.html` abre y su lámina de marcador dice 92/35 y 44 de 100.

**Entregable:** `docs/reportes/I9-sp9.md` (≤ 8 líneas) + `..\salidas-sp9.zip`.

Mensaje de commit sugerido: `docs: I9 sp9 verificado desde caché y pitch regenerado`

---


## I8 [HECHA · Aprobado] — Repetir I7 sobre main con N5 (explicaciones nuevas), desde caché

`carril: integrador · rama: carril/integrador-sp3-n5 desde origin/main (git fetch origin && git switch -c carril/integrador-sp3-n5 origin/main) · cuelga de 4bf23de · tope: 10 min · clasificación: autónoma · modelo: Sonnet 5.5 · esfuerzo: low`

**Primer paso.** `CLAUDE.md` §Disparador; acuse con **sello `12:58`**; `origin/main` debe ser `4bf23de` o posterior y `ml/validat3b/decidir.py` debe contener «No se distingue con claridad». Si ya está hecho, dilo y no lo toques.

**Por qué:** I7 corrió antes de que N5 (#29) entrara a `main`. Las decisiones y los códigos de sp7 son los buenos `[MEDIDO 12:56]`, pero la explicación de la regla 7 todavía dice «…no coincide con lo esperado». Es justo lo que se va a proyectar en la rechazada del pitch.

**Qué hacer** (es el procedimiento de I7; el caché ya está en `salidas/sp7/cache`):
1. Copia `salidas/sp7/cache` a `salidas/sp8/cache`.
2. Corre el motor normal (con cliente, `--hilos 4`, `--salida salidas/sp8/resultados.json`, `--datos datos/privado`). **Para y pregunta** si aparece alguna fila `origen == "modelo"`.
3. Compara contra sp7: **0 decisiones y 0 `reason_code` distintos**; solo cambian explicaciones. **Para y pregunta** si cambia algo más.
4. Copia el `tokens.csv` de sp6 a sp8 y arma `..\salidas-sp8.zip` (resultados, extracciones, locales, tokens; sin `cache/`).

**No se toca:** código, `datos/`.

**Prueba de cierre:** tabla sp7 → sp8 (decisiones distintas · códigos distintos · explicaciones distintas · tokens nuevos) = 0 · 0 · n · 0, y la explicación de CAP-563575 empieza con «No se distingue con claridad». `evaluar` en sp8: JSON válido 100/100.

**Entregable:** push + PR (solo el reporte) + `docs/reportes/I8-n5.md` (≤ 8 líneas) + `..\salidas-sp8.zip`.

Mensaje de commit sugerido: `docs: I8 zip final con explicaciones de N5 desde caché`

---

## I7 [HECHA · Aprobado] — Regenerar el zip final con los códigos de N4, desde caché (0 tokens)

`carril: integrador · rama: carril/integrador-sp3-codigos desde origin/main (git fetch origin && git switch -c carril/integrador-sp3-codigos origin/main; main la tiene ..\repo-docs) · cuelga de 074ad38 [MEDIDO 12:50] · tope: 20 min · clasificación: autónoma · modelo: Sonnet 5.5 · esfuerzo: medium`

**Primer paso.** `CLAUDE.md` §Disparador; acuse con **sello `12:51`**; `git log --oneline -1 origin/main` debe ser `074ad38` o posterior. Si ya está hecho, dilo y no lo toques.

**Por qué:** N4 (ya en `main`) corrige el `reason_code` de las rechazadas (calidad del dato, 15 %) sin cambiar decisiones. El zip que vale para el pitch y el visor (`salidas-sp6.zip`) trae los códigos viejos. Hay que regenerarlo **sin gastar tokens**, desde el caché del cliente.

**Hechos que no puedes ver:**
- `[MEDIDO 12:41 por el arquitecto]` `correr --desde-extracciones salidas/sp6/extracciones.json` re-decide sin cliente: el consenso no puede pedir las lecturas 2 y 3 y **baja las 10 aprobadas a revisión**. **No lo uses para esto.**
- `[LEÍDO cliente.py]` El caché vive en `<carpeta de --salida>/cache/` y su llave depende de la versión del prompt + variante (`-b`, `-c`) + imágenes. `salidas/sp6/` **no tiene** `cache/` `[MEDIDO 12:50 en disco]`; las lecturas de I4/I5/I6 están en el `cache/` de la carpeta que usó la corrida C de I6 (revísalo en tu historial o busca cuál de `salidas/{A,B,F,G,ensayo,corte,...}/cache/` o `salidas/cache/` tiene llaves de las tres variantes).
- `[MEDIDO 12:41]` Con las extracciones de sp6 y `decidir()` de N4: decisiones **idénticas** a sp6; motivo correcto en 8 de 22 rechazadas correctas (antes 2).

**Qué hacer:**
1. Identifica la carpeta de caché con las lecturas de sp6. Copia esa carpeta `cache/` a `salidas/sp7/cache/` (copia, no muevas).
2. Corre el motor normal (con cliente, `--hilos 4`) con `--salida salidas/sp7/resultados.json` sobre `datos/privado`.
3. **Para y pregunta** si `tokens.csv` de sp7 registra alguna fila `origen == "modelo"`, o sea, una llamada nueva (corta con Ctrl+C a la primera: el caché no está completo). Esperado: 0 tokens nuevos.
4. Compara contra `salidas/sp6/resultados.json`: mismas 100 decisiones, mismas 10 aprobadas (por `capture_id`), 0 falsas, costo 104/39; cuántos `reason_code` cambian; motivo correcto en rechazadas correctas (esperado 8/22). **Para y pregunta** si cambia una sola decisión.
5. Para que el visor y el marcador sigan dando 2,390 tokens por captura, `tokens.csv` de sp7 tiene que ser **el de sp6** (las 124 llamadas reales), no el de esta corrida desde caché, que sale con 0: cópialo y dilo en el reporte.
6. `..\salidas-sp7.zip` con `resultados.json`, `extracciones.json`, `locales.csv` y `tokens.csv` (sin prefijos, sin `cache/`).

**No se toca:** código (nada en `ml/`), `datos/`. Esta misión no cambia archivos versionados salvo el reporte.

**Prueba de cierre:** tabla en el reporte, sp6 contra sp7 (aprobadas · falsas · precisión · costo pesimista/optimista · `reason_code` correctos en rechazadas · tokens nuevos de la corrida) con **decisiones idénticas, 0 tokens nuevos, 8/22**. `python -m ml.validat3b.evaluar` sobre sp7: JSON válido 100/100.

**Entregable:** push + PR (solo el reporte) + `docs/reportes/I7-codigos.md` (12 líneas, con «no hecho / simulado» y la carpeta de caché que usaste) + `..\salidas-sp7.zip`.

Mensaje de commit sugerido: `docs: I7 zip final con reason_code de N4 desde caché`

---

## I6 [HECHA · Aprobado con anotaciones] — Consenso unánime de tres lecturas para aprobar

`carril: integrador · rama: carril/integrador-sp3-tres desde origin/main (git switch -c carril/integrador-sp3-tres origin/main) · tope: 25 min · clasificación: autónoma · modelo: Sonnet 5.5 · esfuerzo: high`

**Primer paso.** `CLAUDE.md` §Disparador; acuse con **sello `12:25`**. Si ya está hecho, dilo y no lo toques.

**Por qué** (decisión de Fer, 12:24): la falsa CAP-489454 (real «Capturas lejanas») se aprueba en una de cada dos lecturas y ninguna señal local la distingue. Con 2 lecturas unánimes pasa ~1 de cada 4 veces; con 3, ~1 de cada 8. Con ~11 aprobadas, una falsa = 91 % y descalifica. **«2 de 3» NO sirve**: es más permisivo que lo actual; tienen que aprobar las tres.

**Qué construir:**
1. En `consenso.py`, el número de lecturas que deben aprobar es una constante (`LECTURAS_PARA_APROBAR = 3`); la tercera lectura solo se pide si las dos primeras aprueban (si la segunda ya no aprueba, cero llamadas extra). Cada lectura con su propia versión de caché.
2. Corrida C nueva (caché frío para la tercera lectura; reusa A y B): mide con `evaluar.py` el motor completo (lectura + `decidir()` + compuertas + consenso de 3).
3. `test_consenso.py`: una de tres que no aprueba → revisión manual; la tercera no se llama si la segunda no aprueba (se pone roja si la llamas siempre).

**No se toca:** `decidir.py`, `normalizar.py`, `mapa_codigos.json`.

**Prueba de cierre:** pruebas en verde; tabla en el reporte (consenso de 2 · consenso de 3 → aprobadas, falsas, precisión, costo pesimista/optimista, tokens por captura); **0 falsas**. **Para y pregunta** si bajan más de 3 válidas frente al consenso de 2 o si los tokens por captura pasan de 2,600. `entregar --datos salidas/ensayo` sigue dando VALIDACIÓN: OK.

**Entregable:** push + PR + `docs/reportes/I6-tres.md` (12 líneas) y `..\salidas-sp6.zip` con **nombres sin prefijo** (`resultados.json`, `extracciones.json`, `tokens.csv`, `locales.csv`): el visor busca `extracciones.json` junto a `resultados.json`.

Mensaje de commit sugerido: `feat(ml): consenso unánime de tres lecturas para aprobar (I6)`

---

## I5 — Estabilidad: que el 97 % aguante lecturas nuevas [HECHA · Aprobado con anotaciones]

`carril: integrador · rama: carril/integrador-sp3-estable desde origin/main (git switch -c carril/integrador-sp3-estable origin/main; main la tiene ..\repo-docs) · tope: 45 min · clasificación: autónoma · modelo: Sonnet 5.5 · esfuerzo: high (obligatorio)`

**Primer paso.** `CLAUDE.md` §Disparador; acuse con **sello `12:10`** y la punta de `origin/main`. Si ya está hecho, dilo y no lo toques.

**Hallazgo (tuyo, en I4):** con 100 lecturas nuevas del modelo (temperatura por omisión) el motor dio 13 aprobadas con 1 falsa = **92.3 %**: descalifica. En el set ciego **todas** las lecturas son nuevas. La calibración de N2 y las compuertas se midieron sobre un solo sorteo de lecturas.

**Qué hacer, en este orden, midiendo cada paso con `evaluar.py`:**
1. **Identifica la aprobada falsa** de la corrida nueva de I4 (o vuelve a correrla): `capture_id`, real, qué leyó, qué regla aprobó, nitidez local de etiqueta. Una línea en el reporte.
2. **`temperature=0`** en `cliente.py` (y en el verificador), con su propia versión de caché (`v2-t0`) para no mezclar lecturas. Corre las 100 dos veces seguidas en caché frío (dos carpetas de caché distintas): ¿las lecturas coinciden? Reporta cuántas capturas cambian de decisión entre corrida A y B.
3. **Mide el motor actual** (`decidir()` de N2 + compuertas) sobre A y sobre B: aprobadas, falsas, precisión, costo.
4. **Si en A o en B hay una aprobada falsa**, agrega la defensa más barata que la quite **sin tocar `decidir.py`**, en `compuerta.py`, en este orden de preferencia: (a) **consenso**: una aprobada solo queda aprobada si la lectura A y la lectura B la aprueban las dos (cuesta una segunda llamada **solo a las que salen aprobadas**, ~10–15 % de llamadas); (b) un endurecimiento con una señal local que la explique. Mide la defensa sobre A y B.
5. **Criterio de cierre:** 0 aprobadas falsas en A **y** en B. Si para lograrlo bajan más de 4 válidas adicionales, o los tokens por captura suben más de 20 % sobre 1,921, **para y pregunta**.

**No se toca:** `decidir.py`, `normalizar.py`, `mapa_codigos.json`. `datos/`, `salidas/`, `entrega/` no se commitean. Las corridas gastan ~190k tokens cada una: son dos o tres, no más.

**Prueba de cierre:** pruebas en verde (más una de consenso con cliente falso: si una de las dos lecturas no aprueba, sale revisión manual; se pone roja si quitas el consenso); tabla en el reporte: corrida A · corrida B · (A∩B con consenso) → aprobadas, falsas, precisión, costo pesimista/optimista, tokens por captura; `entregar --datos salidas/ensayo` sigue dando VALIDACIÓN: OK.

**Entregable:** push + PR + `docs/reportes/I5-estable.md` (12 líneas) + `salidas-sp5.zip` fuera del repo (`..\salidas-sp5.zip`), con las salidas de la versión final.

Mensaje de commit sugerido: `feat(ml): temperatura 0 y consenso en aprobadas para estabilizar la precisión (I5)`

---

## I4 — Ensayo general del set ciego: un comando, una entrega válida [HECHA · Aprobado con anotaciones]

`carril: integrador · rama: carril/integrador-sp3-entrega desde main fresco (47c97a4 o posterior) · tope: 45 min · clasificación: autónoma · modelo: Sonnet 5.5 · esfuerzo: high`

**Primer paso.** `CLAUDE.md` §Disparador: `git fetch origin`; como `main` está tomada por el worktree `..\repo-docs`, crea la rama con `git switch -c carril/integrador-sp3-entrega origin/main`; `-Estado -Carril integrador`; acuse con **sello `11:54`**. Si ya está hecho, dilo y no lo toques.

**Por qué:** entre las 15:00 y las 16:00 el comité libera el set ciego y la lista oficial de `reason_code`. Descalifica entregar tarde o con JSON válido < 99 %. Ese momento no se improvisa: hoy se ensaya con las 100 de desarrollo haciéndonos pasar por el set ciego.

**Hechos que no puedes ver** (`[MEDIDO 11:49 por el arquitecto sobre salidas/ de main 7023b06]`): motor = lectura v2 + `decidir()` de N2 + compuertas → 10 aprobadas, 0 falsas, 100 %, costo 99 / 38, 1,921 tokens por captura; corrida de 100 con modelo ≈ 40 s con 4 hilos. El set ciego **no traerá** `decision_esperada` ni `motivo_rechazo`, puede traer otro nombre de carpeta y de archivo, y su tamaño no se conoce. Mauski está escribiendo `ml/validat3b/mapa_codigos.json` en N3 (no lo toques; si no existe aún, el comando corre sin mapa y lo dice).

**Qué construir**
1. `python -m ml.validat3b.entregar --datos <carpeta> --salida entrega/` que, en este orden: (a) localiza `capturas.csv` o `capturas.json` y la carpeta de imágenes aunque cambien de nombre o anidación, y **para** con un mensaje claro si falta algo; (b) cuenta capturas y comprueba que cada una tiene sus 3 fotos (las que no, van a `revision_manual` con `SIN_LECTURA`, nunca se omiten); (c) corre `correr` con el modelo y `--mapa-codigos ml/validat3b/mapa_codigos.json` si existe; (d) valida la salida: **exactamente un `Resultado` por `capture_id`**, todos validan contra el contrato, todo `reason_code` está en la lista del mapa (si hay mapa); (e) escribe `entrega/resultados.json` y un `entrega/resumen.txt` con conteos por decisión, tokens totales y por captura, segundos, y la lista de lo que falló; (f) si algo de (d) falla, **no** borra nada: lo dice y sale con código distinto de 0.
2. Funciona sin columnas de etiquetas (ensáyalo con una copia de `capturas.csv` sin `decision_esperada` ni `motivo_rechazo`, en `salidas/ensayo/`, nunca en `datos/`).
3. Una bandera `--reanudar` que reusa el caché para que, si se corta a media corrida, se vuelva a lanzar sin repetir llamadas.

**No se toca:** `decidir.py`, `normalizar.py`, `mapa_codigos.json`, `visor.py`, `evaluar.py`, `marcador.py`. `datos/`, `salidas/` y `entrega/` no se commitean (agrega `entrega/` a `.gitignore`).

**Prueba de cierre:**
1. Pruebas en verde, más `test_entregar.py`: un `capture_id` duplicado o faltante hace que la validación falle (y se pone roja si quitas la validación); una captura sin foto sale en `revision_manual`.
2. Ensayo: `entregar --datos salidas/ensayo` sobre las 100 **sin etiquetas** → 100 resultados, 100 % válidos, resumen escrito; reporta los segundos de punta a punta (caché caliente) y estima los de 100 capturas nuevas.
3. Corta la corrida a la mitad (Ctrl+C) y relanza con `--reanudar`: termina sin repetir llamadas (`tokens.csv` lo muestra).
4. `git status --short` sin `datos/`, `salidas/` ni `entrega/`.

**Entregable:** push + PR + `docs/reportes/I4-entrega.md` (12 líneas) con los tiempos medidos y el «no hecho / simulado».

Mensaje de commit sugerido: `feat(ml): comando de entrega del set ciego con validación y reanudar (I4)`

---

## I3.1 — Arreglo de I3: compuertas locales de aprobación (sin tokens) en lugar del verificador [HECHA · Aprobado con anotaciones]

`carril: integrador · rama: la misma, carril/integrador-sp2-verificar (cuelga de 52c0762 [REPORTADO por Code 11:26]; rebasa sobre origin/main) · tope: 25 min · clasificación: autónoma · modelo: Sonnet 5.5 · esfuerzo: high (obligatorio)`

**Primer paso.** `CLAUDE.md` §Disparador: `git fetch origin`, quédate en `carril/integrador-sp2-verificar`, `git rebase origin/main` (trae solo docs), `-Estado -Carril integrador`, relee este ESTADO, acuse con **sello `11:28`**. Si al leer el código concluyes que el hallazgo es falso, dilo y no toques nada.

**Hallazgo textual de la auditoría de I3** (`[REPORTADO por Code 11:26]`): el verificador aprobó 7 (6 correctas, 85.7 %), bajó 8 válidas (726347, 847838, 170513, 621992, 275838 entre ellas), sumó ~358 tokens por captura (+19 %) y **no bajó CAP-206200**. No cumple la prueba de cierre de I3.

**Hechos que no puedes ver** (`[MEDIDO 11:27 por el arquitecto: decidir() de N1 sobre salidas-sp2.zip + locales.csv + capturas.csv]`)
- **CAP-206200**: el lector local leyó el código **0401013049343** y no coincide con `capture_barcode` 7501791626163.
- En las 100, «código leído y **no** coincide» (`senales["codigo_coincide"] is False`) aparece en: revisión manual 9 · aprobada 2 · rechazada 2. Es la señal más fuerte que tenemos de `revision_manual`.
- **CAP-410562** (falsa, borrosa): nitidez local de etiqueta 99. Entre las aprobadas correctas, solo 970141 (83) queda debajo de 100.
- Resultado medido de cada variante (aprobadas · correctas · precisión · costo pesimista / optimista):
  - decidir() tal cual: 16 · 14 · 87.5 % · 118 / 52
  - A) aprobada y código no coincide → revisión: 15 · 14 · 93.3 % · 109 / 42
  - B) A + aprobada con nitidez de etiqueta < 100 → revisión: **13 · 13 · 100 % · 101 / 34**
  - C) B + **cualquier** captura con código no coincide → revisión: **13 · 13 · 100 % · 96 / 35** ← la que se implementa

**Qué construir**
1. `ml/validat3b/compuerta.py` con `compuerta(resultado, senales) -> Resultado`, pura y con constantes arriba (`UMBRAL_NITIDEZ_ETIQUETA = 100.0`, con comentario «fijado con las 100 de desarrollo, 21-nov 11:27»):
   - si `senales.get("codigo_coincide") is False` → `revision_manual`, `reason_code=None`, `confidence_score=0.5`, la explicación añade «El código de barras de la foto (<leído>) no coincide con el registrado (<esperado>).»;
   - si no, y el resultado es `aprobada` y `nitidez_etiqueta` es `None` o < umbral → `revision_manual`, con la explicación «La etiqueta no se ve con nitidez suficiente para aprobar.»;
   - en otro caso, el resultado sin cambios. Nunca convierte nada en `aprobada`.
2. En `correr.procesar`: `compuerta()` va después de `decidir()`. El **verificador queda en el código pero apagado**: solo corre con la bandera `--verificar`; por omisión, cero llamadas extra.
3. `test_compuerta.py`: los tres casos, más `senales={}` (sin señales) con una aprobada → revisión. La prueba de «código no coincide» se pone roja si quitas la compuerta de `correr`.

**No se toca:** `decidir.py` y las demás de otros carriles; el contrato.

**Prueba de cierre:**
1. Todas las pruebas en verde (`test_decidir`, `test_local`, `test_evaluar`, `test_verificar`, `test_compuerta`).
2. `correr --desde-extracciones salidas/extracciones.json` (cero tokens: compruébalo en `tokens.csv`) y `evaluar` → deben salir **13 aprobadas, 13 correctas, 100 %, costo 96 / 35**. Si sale otra cosa, para y muestra la diferencia.
3. La prueba de cierre de I2 sigue pasando: `--desde-extracciones` es reproducible.
4. `git status --short` sin `datos/` ni `salidas/`.

**Entregable:** push de la misma rama + PR + `docs/reportes/I3.1-compuerta.md` (12 líneas, al final y de una vez; incluye la tabla del verificador de I3 como antecedente), y `salidas-sp3.zip` (resultados, extracciones, tokens, locales; sin `cache/`), que se saca del repo con `Move-Item` después de compartirlo.

Mensaje de commit sugerido: `feat(ml): compuertas locales de aprobación y verificador apagado por omisión (I3.1)`

---

## I3 — Verificador de aprobadas: segunda mirada solo a lo que va a salir «aprobada» [hecho · Devuelto → I3.1]

`carril: integrador · rama: carril/integrador-sp2-verificar desde main fresco · cuelga de: e492dbf [MEDIDO 11:06 en GitHub: merge del PR #12] · tope: 45 min · clasificación: autónoma · modelo: Sonnet 5.5 · esfuerzo: high`

**Primer paso.** `CLAUDE.md` §Disparador completo: `git checkout main`, `git fetch origin`, `git pull --rebase origin main`, `-Estado -Carril integrador`, relee este ESTADO y devuelve el acuse con **sello `11:07`** y la punta de `origin/main` (debe ser `e492dbf` o el commit de docs que Fer suba encima con este documento; si hay algo más, lístalo). Corre todo con `.venv\Scripts\python`. Si ya está hecho, dilo y no lo toques.

**Hechos que no puedes ver** (`[MEDIDO 11:05 por el arquitecto sobre salidas-sp2.zip + capturas.csv]`)
- Con lecturas v2 y `decidir()` de N1: aprobó 16, **14 correctas (87.5 %, descalifica)**. Las 2 falsas: **CAP-206200** (real `revision_manual`) y **CAP-410562** (real rechazada, «Capturas borrosas»; nitidez local de etiqueta 99).
- Nitidez local de etiqueta de las 16 aprobadas: 83 · 195 · 368 · 319 · 384 · 326 · 298 · 543 · **99 (410562, falsa)** · 407 · 326 · 245 · 208 · 125 · 190 · 402. Un corte en nitidez sola tira también a la válida de 83 (970141): no sirve como regla única.
- La lectura única (producto + etiqueta en una llamada a 768 px) no detecta 489454 ni 241497 como lejanas: hay que mirar distinto, no más fuerte en las 100.
- Una revisión manual cuesta 1; una aprobada falsa, 10, y abajo de 97 % descalifica. Pasar 2–3 válidas a revisión para quitar todas las falsas **es buen negocio**.
- `decidir()` y su calibración son de Mauski (N2, corriendo ahora sobre `salidas-sp2.zip`). **Tú no tocas `decidir.py`**: el verificador va después de decidir, en la tubería.

**Qué construir**
1. `ml/validat3b/verificar.py` con `verificar(captura, ext, dir_datos, cliente) -> tuple[bool, str]`: **una llamada más, solo si `decidir()` dijo `aprobada`**. Manda la foto del producto y la de la etiqueta a **más resolución que la lectura** (lado 1024; si los tokens de esa llamada pasan de 2,500, baja a 896) y un prompt de sí/no estricto: «¿Se leen con claridad, sin adivinar, la marca, la descripción, el contenido neto y el precio, y la etiqueta corresponde a este producto exacto (no a otro sabor, tamaño o submarca)? Responde JSON {"ok": bool, "motivo": str corto}». Le pasas como texto lo esperado (marca, `product_name`, contenido) y lo leído. Versión de prompt propia (`verificar-v1`), con caché igual que la lectura.
2. En `correr.procesar`: si `decidir()` aprueba y `verificar` dice `ok=false`, **error o JSON inválido** → el `Resultado` pasa a `revision_manual`, `reason_code=None`, `confidence_score=0.5`, y `explicacion` añade «Segunda revisión: <motivo>». Ante cualquier duda, nunca aprueba.
3. Tokens del verificador a `tokens.csv` con `origen="verificar"`, para que D1 los cuente.
4. `--desde-extracciones` también reusa las respuestas del verificador guardadas en caché (no gasta tokens en una segunda corrida).

**No se toca:** `decidir.py`, `normalizar.py`, `local.py`, `evaluar.py`, `visor.py`, el contrato. `datos/` y `salidas/` no se commitean.

**Prueba de cierre (ejecutable):**
1. `.venv\Scripts\python -m unittest ml.validat3b.test_decidir ml.validat3b.test_local ml.validat3b.test_evaluar -v` en verde, más `test_verificar.py` con un cliente falso: `ok=false` → revisión; error del cliente → revisión; `ok=true` → sigue aprobada; captura no aprobada → **cero llamadas**. Esta última se pone roja si el verificador llama en todas.
2. `.venv\Scripts\python -m ml.validat3b.correr --datos datos/privado --salida salidas/resultados.json --hilos 4` (la lectura sale de caché; solo ~16 llamadas nuevas).
3. `.venv\Scripts\python -m ml.validat3b.evaluar --resultados salidas/resultados.json --capturas datos/privado/metadatos/capturas.csv` → en el reporte: aprobadas, falsas, precisión, costo pesimista/optimista antes (I2: 118/52) y después, y tokens por captura con verificador incluido.
4. Lista de lo que el verificador bajó a revisión, con su real: tiene que incluir **206200 y 410562**; si baja válidas, cuántas.
5. `git status --short` sin `datos/` ni `salidas/`.

**Para y pregunta** si el verificador baja más de 5 válidas, o si los tokens por captura (promedio en las 100) suben más de 15 % sobre 1,921.

**Entregable:** push de la rama + PR + `docs/reportes/I3-verificar.md` de 12 líneas (al final y de una vez), con modelo y esfuerzo, la tabla antes/después y su «no hecho / simulado». Deja `salidas-sp3.zip` (resultados, extracciones, tokens, locales; sin `cache/`) en la raíz del repo, sin commitear.

Mensaje de commit sugerido: `feat(ml): verificador de aprobadas con segunda mirada a mayor resolución (I3)`

---


## I2 — Lectura v2, señales locales en la tubería y re-decisión sin tokens [HECHA · Aprobado con anotaciones]

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
- 2026-11-21 11:07 · S003 · auditoría de I2 (PR #12, 87.5 % medido por el arquitecto sobre salidas-sp2.zip) → se escribe I3 (verificador de aprobadas).
- 2026-11-21 11:28 · S003 · I3 devuelto (85.7 %, 8 válidas bajadas, +19 % tokens; Code paró bien) → I3.1 cambia el verificador por compuertas locales medidas: 13/13 = 100 %, costo 96/35.
- 2026-11-21 11:54 · S003 · I3.1 aprobada y fusionada (#17; sp4 medido 10/10, 99/38) → se escribe I4 (ensayo del set ciego).
- 2026-11-21 12:10 · S003 · I4 aprobada y fusionada (#20); su hallazgo (92.3 % con lecturas nuevas) es S0 → I5 (temperatura 0 + consenso).
- 2026-11-21 12:25 · S003 · I5 aprobada y fusionada (#23; consenso de 2, 0 falsas, 103/38) → I6 (3 lecturas unánimes, decisión de Fer).
- 2026-11-21 12:51 · S004 · I6 ya estaba fusionada (#25); se tacha. N4 y U5 fusionadas → I7 (regenerar desde caché con los códigos de N4; `--desde-extracciones` no sirve, medido). Se sube el sello.
- 2026-11-21 12:58 · S004 · I7 aprobada y fusionada (#30 → 4bf23de; sp7 medido). N5 entró después → I8 repite el procedimiento con las explicaciones nuevas. Se sube el sello.
- 2026-11-21 13:15 · S004 · I8 aprobada y fusionada (#32). Motor congelado.
- 2026-11-21 13:41 · S005 · sin auditoría de carril: el arquitecto escribe N7 (regla 7a: contenido que explica el catálogo → revisión; sp9 medido 92/35, 10/0) y fusiona el PR #34 de Mau (bb81810). Se escriben I9 (verificar sp9 y regenerar pitch), I10 (consenso de 5, aprobada por Fer 13:39) e I11 (set ciego, bloqueada hasta las 15:00). Se sube el sello.
- 2026-11-21 14:46 · S005 · sp11–sp13 medidos (lectura v3 + N8: 16/0, 84/27, 3,192 tokens); I9 hecha, I10 descartada; I11 reescrita para el motor final y bloqueada hasta el set ciego. Se sube el sello.
