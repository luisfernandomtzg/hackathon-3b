# Misiones — carril DATOS E IA

## ESTADO · 2026-11-21 09:55
Carril datos · dueño Sergio (chat web) · misiones 1 · hechas 0 · siguiente **D1**
Cola: **D1** → D2 (partición por visita y curva costo-umbral)
siguiente: **D1**
Última auditoría: ninguna
Qué cambió por esa auditoría: nada
Reescrituras de este documento: 2
Siguiente con modelo: el del asistente de Sergio · clasificación autónoma

---

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

---

## Bitácora de reescrituras

- 2026-11-17 13:20 · creado en S000, sin misiones.
- 2026-11-17 14:54 · S000: ESTADO al formato v1.2 (sello del reloj, `BLOQUEADO hasta`).
- 2026-11-21 09:55 · S002: reto asignado = Reto 2 · Validat3B; giro a Python por lotes en `ml/validat3b/` (compuerta de Fer 09:16). Se escribe la misión 1 y se libera el carril; sin auditoría previa.
