# Contexto vigente — Hackathon Tiendas 3B

> Una página. Se actualiza al cerrar **cada fase**. Fuente: copia del proyecto de claude.ai; espejos en `documentacion/` y en `repo/docs/`.
> Última actualización: **2026-11-21 13:43 · S005 (en curso)** · siguiente **S006 si hace falta (set ciego y pitch)**.

## 🟢 S005 en curso — estado y relevo (escrito 2026-11-21 13:43; lo confirma S005 al cerrar)

**Si abres sesión nueva:** `S006 3B. Lee el prompt inicial` → instrucciones → este bloque. Lo de abajo es historia.

- **Regla de sesiones (Fer, 10:33 · rige todo el día):** **una sesión de claude.ai por sprint del equipo, no por tarea.** La sesión audita e integra las entregas de ese sprint y escribe la misión siguiente de Fer; cuando el sprint cierra se cierra con el **protocolo completo** de §4: relevo aquí (carpeta `documentacion/` + `repo/docs/` + copia del proyecto, verificado por contenido), `ESTADO` de cada carril tocado, bloque de git flanqueado por `git status --short` y la línea «Abre S00N+1 con: `S00N+1 3B. Lee el prompt inicial`». **Todo relevo nuevo copia esta regla tal cual.**
- **Instrucción de Fer (13:27 y 13:39):** el equipo ya no trabaja; el arquitecto tiene carta libre para mejorar y Fer corre los comandos. **El chat no tiene terminal en la laptop ni endpoint**: escribe archivos en la carpeta y Fer (o su Code) hace git y corre el motor.
- **PR #34 de Mau fusionado → `bb81810`** `[MEDIDO 13:34 en GitHub]` (U5.2: desborde de inputs de archivo, cifras de sp8 en la ficha, `docs/equipo/mau-viabilidad-propuestas.md`). Aprobado con anotaciones `[LEÍDO: diff completo; sin build]`. Sus módulos 5–7 **no entran**: el 5 (misiones GPS) falla el filtro 3B; 6 y 7 quedan como frase de «siguiente paso».
- **N7 · regla 7a en `decidir.py`** (escrita por el arquitecto en `repo-docs`, **sin commitear hasta que Fer corra el bloque de git**): si el contenido leído es el «(total: NNNg)» del propio nombre esperado, o la misma cantidad con g↔ml, va a `revision_manual` con `PRODUCTO_NO_COINCIDE` en vez de rechazarse. Nunca aprueba. 4 pruebas nuevas (2 se ponen rojas sin el cambio); 51 pruebas en verde `[MEDIDO 13:37 en el contenedor del chat]`.
- **sp9 = cifras vigentes** `[MEDIDO 13:38 con ml.validat3b.evaluar sobre salidas/sp9/resultados.json]`: **10 aprobadas · 0 falsas · 100 % · costo 92 pesimista / 35 optimista** (todo a revisión: 100 / 67) · **0 válidas rechazadas** (eran 2) · **44 de 100 sin persona** (eran 50) · JSON 100/100 · tokens sin cambio (**2,390 por captura**, medición de sp6: no hubo llamadas nuevas). Matriz real→decidido: aprob 10/0/23 · rech 0/22/12 · man 0/12/21. Cambiaron 6 capturas contra sp8 (2 aprobadas reales, 4 de revisión reales). sp9 se armó re-decidiendo las lecturas de sp8, **no** con `correr`: lo verifica I9.
- **Documentos ya con sp9 (en `repo-docs`, sin commitear):** `docs/pitch/guion.md` (92/35, 44 de 100, 5,280 por semana, «sin rechazar ninguna captura válida», rechazada = CAP-563575), `docs/pitch/cifras.md`, `docs/pitch/laminas.md`. **La ficha** corregida (sp9 + comando de `evaluar` que estaba mal) está en `Claude outputs\ficha-tecnica.html`: se copia a `docs/entrega/` **después** del `git pull` que trae #34.
- **Más aprobadas: medido y descartado** `[MEDIDO 13:36]`. Las dos falsas que el motor casi aprueba (CAP-489454, CAP-410562) las lee perfecto el modelo; el analista las rechazó por lejana/borrosa. Ni la nitidez local ni `capture_price == precio leído` (igual en 93 de 100) las distinguen. Cada aprobada extra vale 1 punto; una falsa cuesta 10 y descalifica. Único grupo limpio: 4 capturas en «zona gris» de descripción con todo lo demás claro (4 de 4 válidas), sin implementar.
- **Motivo de rechazo (calidad del dato):** sigue 8 de 22; la nitidez local no separa «borrosa» de «lejana» `[MEDIDO 13:40]`. Depende de la lista oficial de las 15:00.
- **Carriles:** Integrador sello **13:41**, siguiente **I9** (verificar sp9 desde caché, regenerar `pitch.html`, zip) → **I10** (consenso de 5 lecturas, aprobada por Fer; se corta si pasan las 14:25) → **I11** (set ciego, bloqueada hasta 15:00). Núcleo: BLOQUEADO hasta la lista oficial. UI, Datos, Pitch: cerrados; **Alan tiene que releer el guion: cambiaron 3 cifras y la rechazada.**
- **Riesgo vivo (S0 si ocurre):** una lejana se cuela ~1 de 8 con consenso de 3; I10 lo baja a ~1 de 32 si se alcanza a medir.
- **No verificado:** el bloque de git de S005 (lo primero que mide la sesión siguiente: `git log --oneline -3` en `repo-docs` debe mostrar el commit de N7 encima de `bb81810`) · `pitch.html` con sp9 · build de la consola tras #34 · I9/I10 · costo oficial cuando la real es revisión manual · precisión sobre el set ciego · video de respaldo.
- **Primera acción al volver Fer:** correr el bloque de git de S005 → en Code: `/model sonnet`, `/effort low`, «ejecuta el siguiente prompt de integrador, sello 13:41» (I9) → I10 si es antes de las 14:25 → avisar a Alan → a las 15:00 pegar el set ciego y la lista oficial.

## Relevo para S005 (histórico) — escrito en S004 (2026-11-21 13:20; se confirma al congelar, 14:30)

**Abre con `S005 3B. Lee el prompt inicial`** → instrucciones del proyecto → `PROMPT-APERTURA-S003.md` (vale para S005 cambiando el número) → este relevo. Lo de abajo es historia.

- **Regla de sesiones (Fer, 10:33 · rige todo el día):** **una sesión de claude.ai por sprint del equipo, no por tarea.** La sesión audita e integra las entregas de ese sprint y escribe la misión siguiente de Fer; cuando el sprint cierra se cierra con el **protocolo completo** de §4: relevo aquí (carpeta `documentacion/` + `repo/docs/` + copia del proyecto, verificado por contenido), `ESTADO` de cada carril tocado, bloque de git flanqueado por `git status --short` y la línea «Abre S00N+1 con: `S00N+1 3B. Lee el prompt inicial`». Mapa: S004 = sprint 3 (congelar 14:30) · S005 = set ciego, entrega y pitch (15:00–17:00). **Todo relevo nuevo copia esta regla tal cual.**
- **Fase:** F3 cerrándose → F4/F5. Motor **congelado**. Reto 2 · Validat3B, Python local en `ml/validat3b/`; demo = `pitch.html` en la laptop de Fer, sin internet.
- **`main` = `8d1fd10`** `[MEDIDO 13:18 en la terminal de Fer]` (encima: #31 U5.1 → `1e2dd6b`, #33 N6, #32 I8, #30 I7, #29 N5, #28 P3.2, #27 N4, #26 U5). Árbol de `repo-docs` limpio.
- **Zip final de desarrollo: `..\salidas-sp8.zip`** `[MEDIDO 13:03 por el arquitecto]`: 10 aprobadas · 0 falsas · 100 % · costo **104 / 39** contra **100 / 67** de revisar todo · **50 de 100 sin persona** · **2,390 tokens por captura** (238,959 de 124 llamadas reales ÷ 100; criterio oficial del equipo, confirmado a Sergio 13:15) · JSON válido 100/100 · motivo correcto en 8 de 22 rechazadas correctas (antes 2; N4). Conteo de códigos: CAPTURA_LEJANA 21 · DESCRIPCION_INCOMPLETA 17 · PRODUCTO_NO_COINCIDE 12 (rev.) · ETIQUETA_NO_CORRESPONDE 6 (rev.) · CAPTURA_BORROSA 1 · SIN_ETIQUETA_PRECIO 1.
- **Pitch:** `pitch.html` con `--pitch CAP-434912,CAP-563575,CAP-350077` y sp8 `[MEDIDO 13:11, 1920×1080]`: lámina 1 = **0 falsas · 50 de 100 · 104/39 contra 100/67 · 2,390** (decisión de Fer 12:46). La rechazada es **CAP-563575** (Jalapeños La Costeña en Bara, `CAPTURA_LEJANA`); CAP-748989 ya no se usa (lejana real que N4 codifica como incompleta). Guion de Alan fusionado (#28) con 104/39 y 2,390; **falta** que cambie la rechazada a 563575. La consola Next.js y los 4 módulos nuevos del visor (U5.1, fuera de alcance) **no van en la demo**.
- **Carriles:** Integrador ~~I1–I8~~ NINGUNO · Núcleo ~~N1–N6~~ **BLOQUEADO hasta la lista oficial de reason_code** (Mauski llena `docs/entrega/codigos.md` y edita `mapa_codigos.json`; PR que aprueba Fer **antes** de correr el set ciego) · UI ~~U0–U5.1~~ congelado (Mau maneja la demo y graba el video de respaldo) · Datos cerrado (Sergio cuida cifras) · Pitch: Alan ensaya.
- **Set ciego (15:00–16:00), lo corren Fer y Mauski:** (1) pegar en S005 cómo llegó (carpeta, nombres, si trae etiquetas) y la lista oficial de `reason_code`; (2) PR del mapa de Mauski; (3) `.venv\Scripts\python -m ml.validat3b.entregar --datos <carpeta> --salida entrega/ [--reanudar]` (I4; ensayado 100/100 VALIDACIÓN OK; 100 capturas ≈ 70–90 s más las lecturas del consenso); (4) revisar `entrega/resumen.txt` y entregar por el canal que diga el comité. **Esto sí llama al endpoint**: tokens reales.
- **Riesgo vivo (S0 si ocurre):** el endpoint no acepta `temperature`; una lejana se cuela en ~1 de 8 con consenso de 3. Con ~10 aprobadas, una falsa = 91 % y descalifica. No hay señal local para lejanas.
- **Lecciones de S004:** `correr --desde-extracciones` **no sirve** con consenso (sin cliente baja las 10 aprobadas a revisión): se regenera desde el caché del cliente (`salidas/G/cache`, ya copiado en `salidas/sp7/cache` y `sp8/cache`). El chat audita PR con `git -C repo worktree add ..\audit-<x> origin/<rama>` y leyendo la carpeta; Chrome se desconectó a las 13:03 y no volvió. Antes de fusionar un PR, mirar si hubo force-push (pasó con #26).
- **Pendiente:** cifras dichas por Sergio en el chat corregidas (eran del desarrollo, no del set ciego; el pitch es a las 17:00, no a las 15:00) · commit `e84d3cf` de Sergio en `carril/datos-sp3-marcador` fuera de `main` (se le pidió PR nuevo solo si hace falta) · costo real de la revisión manual (Alan al comité).
- **No verificado:** el 100 % de precisión sobre el set ciego · costo de revisión manual real · tamaño y formato del set ciego · puntaje de Rival 3B · que el guion ya diga 563575 · el video de respaldo.
- **Primera acción de S005:** acuse §4 · `git log --oneline -3` en `repo-docs` · pedir el set ciego y la lista oficial con la plantilla de arriba · auditar el PR del mapa de Mauski · escribir **I9** (correr el set ciego con `entregar`) en `prompts-integrador.md` con sello y orden para el Code de Fer · auditar `entrega/` (100 % JSON válido, conteo de decisiones, ninguna aprobada sin consenso) · F4/F5: video de respaldo, capturas, tres ensayos.

## Relevo para S004 (histórico) — escrito al cerrar S003 (2026-11-21 12:36)

**Abre con `S004 3B. Lee el prompt inicial`** → instrucciones del proyecto → `PROMPT-APERTURA-S003.md` (vale para S004 cambiando el número) → este relevo. Lo de abajo es historia.

- **Regla de sesiones (Fer, 10:33 · rige todo el día):** **una sesión de claude.ai por sprint del equipo, no por tarea.** La sesión audita e integra las entregas de ese sprint y escribe la misión siguiente de Fer; cuando el sprint cierra se cierra con el **protocolo completo** de §4: relevo aquí (carpeta `documentacion/` + `repo/docs/` + copia del proyecto, verificado por contenido), `ESTADO` de cada carril tocado, bloque de git flanqueado por `git status --short` y la línea «Abre S00N+1 con: `S00N+1 3B. Lee el prompt inicial`». Mapa: S004 = sprint 3 (13:45–14:30, congelar 14:30) · S005 = set ciego, entrega y pitch (15:00–17:00). **Todo relevo nuevo copia esta regla tal cual.**
- **Fase:** F3, sprint 2 cerrado con el camino de punta a punta en verde. Reto 2 · Validat3B. Producto = Python local en `ml/validat3b/` (no se despliega: el entregable es un JSON y los datos son confidenciales; la demo es `salidas/visor.html` y `pitch.html` en la laptop de Fer, sin internet).
- **`main` = merge del PR #25 (I6)** `[MEDIDO 12:35 en GitHub]`; SHA: medirlo al abrir (`git log --oneline -3` en `repo-docs`). **`main` está tomada por el worktree `..\repo-docs`**: los documentos se commitean desde ahí; en `repo\` Code trabaja en ramas creadas con `git switch -c <rama> origin/main`.
- **Motor definitivo (`salidas-sp6.zip`, fuera del repo)** `[MEDIDO 12:35 por el arquitecto]`: lectura v2 (`extraer.py`) + señales locales (`local.py`) + `decidir()` de N2 + compuertas (`compuerta.py`: código de barras que no coincide → revisión; aprobada con nitidez de etiqueta < 100 → revisión) + **consenso unánime de 3 lecturas para aprobar** (`consenso.py`). Sobre las 100 de desarrollo: **10 aprobadas, 0 falsas (100 %), costo 104 pesimista / 39 optimista** (todo a revisión: 100 / 67), **2,390 tokens por captura** (124 llamadas), JSON válido 100/100. Matriz real→pred: aprobada 10/2 rech/21 man · rechazada 0/22/12 · manual 0/16/17.
- **Riesgo vivo (S0 si ocurre):** el endpoint **no acepta `temperature`**: las lecturas cambian entre corridas. CAP-489454 (lejana) se aprueba en ~1 de 2 lecturas; con 3 unánimes se cuela ~1 de 8. Con ~10 aprobadas, una falsa = descalificación. No hay señal local que detecte lejanas.
- **Entrega del set ciego:** `.venv\Scripts\python -m ml.validat3b.entregar --datos <carpeta> --salida entrega/ [--reanudar]` (I4): localiza archivos aunque cambien de nombre, manda a revisión las capturas sin fotos, aplica `mapa_codigos.json` si existe, valida una por `capture_id` y escribe `entrega/resumen.txt`. Ensayado con las 100 sin etiquetas: VALIDACIÓN OK. 100 capturas nuevas ≈ 70–90 s.
- **Carriles al cerrar S003:** Integrador ~~I1–I6~~, siguiente **NINGUNO** (I7 se escribe en S004 si hace falta). Núcleo **N4** en curso (Mauski, sello 12:26: motivo correcto en rechazadas —hoy 2/34 aciertan— y quitar `traducir()`). Datos ~~D3.1~~ (Sergio libre: apoya el pitch). UI **U5** pendiente (Mau, sello 11:54: `pitch.html` con Tarima; su #24 fue exportar CSV + ficha, **no** U5). Pitch ~~P3.1~~ (guion fusionado #22; falta poner 104/39, 2,390 y «una llamada; tres solo para aprobar»).
- **Auditorías de S003:** N1, P1, D1, U1–U4, N2, P2, D2, N3, D3.1, P3.1, I2, I3.1, I4, I5, I6 → aprobadas (con anotaciones) y fusionadas; I3 (verificador) y D3 devueltos y arreglados (I3.1, D3.1).
- **Pendiente del comité (cambia 14–61 puntos):** ¿cuánto cuesta si la real es revisión manual y la rechazamos o la mandamos a revisión? Hoy se reporta pesimista (rechazar=3, revisión=1) y optimista (0/0). Se lo pidió Fer a Alan.
- **Disciplina:** el historial del repo tiene datos de 3B (commit `e5aae17`): **nunca hacerlo público**. Los zips de salidas van fuera del repo (`Move-Item ..\`). Vercel no se usa (Hobby; no se invitó a nadie, decisión de Fer 10:47).
- **No verificado:** el 97 % sobre lecturas nuevas más allá de 3 corridas · costo real de la revisión manual · tamaño y formato del set ciego · puntaje de Rival 3B · `pitch.html` con Tarima.
- **Primera acción de S004:** acuse §4 · `git log --oneline -3` en `repo-docs` · auditar en orden N4 (Mauski) y U5 (Mau) si llegaron · regenerar el zip final con `correr --desde-extracciones` si N4 cambia códigos (las decisiones no deben cambiar: 10/0, 104/39) · confirmar cifras del guion y la ficha con Alan/Sergio/Mau · a las 14:30 congelar y escribir el relevo para S005 (set ciego).

## Relevo para S003 (histórico) — escrito al cerrar S002 (2026-11-21 10:34)

**Abre con `S003 3B. Lee el prompt inicial`** → lee instrucciones del proyecto → `PROMPT-APERTURA-S003.md` → este relevo. Lo de abajo de este bloque es historia anterior al sábado.

- **Regla de sesiones (Fer, 10:33 · rige todo el día):** **una sesión de claude.ai por sprint del equipo, no por tarea.** La sesión audita e integra las entregas de ese sprint y escribe la misión siguiente de Fer; cuando el sprint cierra (sus entregas auditadas o cortadas por el reloj) se cierra con el **protocolo completo** de §4: relevo aquí (carpeta `documentacion/` + `repo/docs/` + copia del proyecto, verificado por contenido), `ESTADO` de cada carril tocado, bloque de git flanqueado por `git status --short` y la línea «Abre S00N+1 con: `S00N+1 3B. Lee el prompt inicial`». Mapa: S003 = sprint 2 (11:00–13:15) · S004 = sprint 3 (13:45–14:30) · S005 = corrida del set ciego, entrega y pitch (15:00–17:00). **Todo relevo nuevo copia esta regla tal cual.**
- **Fase:** F3 · sprint 1 cerrándose (meta 10:45). Reto 2 · **Validat3B** (motor por lotes que decide `aprobada / rechazada / revision_manual` por captura de precio). Producto = **Python local en `ml/validat3b/`**; Next/Supabase/Vercel fuera. Repo **privado**.
- **Calificación:** costo 50 % (acierto 0 · manual 1 · rechazar válida 3 · aprobar inválida 10) · calidad del dato 15 % · tokens 10 % · pitch 25 % (3 min). Descalifica: precisión de aprobadas < 97 %, JSON válido < 99 %, tarde. **Congelar 14:30**; set ciego + lista oficial de `reason_code` entre 15:00 y 16:00 (comité, 09:50).
- **Endpoint:** Azure AI Foundry, SDK `anthropic` (`AnthropicFoundry`), modelo único `claude-haiku-5-5`, `thinking` desactivado (si no, agota tokens sin texto), llave en `.env.local` como `FOUNDRY_API_KEY`. **Solo Fer llama al endpoint** y comparte `salidas/` al equipo.
- **Datos `[MEDIDO]`:** 100 capturas (34 rech / 33 aprob / 33 manual), en `datos/privado/`. Metadatos sin señal. Motivos: lejanas 18, borrosas 11, descripción incompleta 5. Negocio (Alfredo): válida = se leen marca, descripción, contenido y precio y la etiqueta es de ese producto; foto por foto; ~800 capturistas, ~12,000 capturas/semana; prefieren menos aprobadas con error casi cero. Comité: los asistentes pueden leer los datos de desarrollo; el criterio de las tres decisiones lo diseñamos nosotros.
- **`main`:** contiene `c99c380` (misiones SP1 + contrato) y el merge del **PR #6 (I1)** hecho a las 10:32 `[MEDIDO en GitHub: «Merged»]`. SHA del merge: **medirlo al abrir** (`git log --oneline -3`).
- **Carriles (sprint 1):** Integrador ~~I1~~ **Aprobado con anotaciones** · Núcleo **N1** (Mauski) · Datos **D1** (Sergio) · UI **U1** (Mau, dijo haber terminado: **sin auditar**) · Pitch **P1** (Alan). Entregas llegan como PR + `docs/reportes/<id>-*.md`.
- **Paquetes por persona con los 3 sprints** (`docs/paquetes/{mauski,sergio,mau,alan}.md`): ya repartidos por chat a las 10:20; en el repo desde el commit de cierre de S002. Sprint 2 = N2 calibrar, D2 análisis + clasificador, U2 visor + modo pitch, P2 puerta local. Sprint 3 = N3 mapa de códigos, D3 marcador, U3 ficha técnica, P3 guion. 15:00: Alan narra, Mau maneja, Sergio números; Fer y Mauski corren el set ciego.
- **Auditoría I1 `[MEDIDO 10:28]`:** 1,865 tokens por captura (1,661 entrada fijos; ~1,180 son las dos imágenes); ~11 s por llamada; 5 lecturas cruzadas contra etiquetas: 0 aprobadas falsas. Anotaciones para I2/N2: «lejana» = contenido ilegible (el modelo dijo «cercano» en una lejana) · g vs ml misma cantidad no es rechazo · submarca (Carnation vs Nestle) + precio con varias cifras huele a revisión manual · reintentos más largos ante 429.
- **Lo pendiente en curso:** Fer corre las 100 con modelo (`correr --hilos 4`, ~5 min, ~187k tokens) y comparte `salidas/` sin `cache/`. `ml/evaluador.py` de Mau entró a `main` sin auditar y duplica D1 (se quita al integrar D1).
- **Disciplina:** dos veces se empujó directo a `main` (Mau 09:11–09:13, Alan `47995c4`). Regla: rama + PR, solo Fer fusiona. Fer puede activar la protección de `main` en GitHub.
- **No verificado:** U1 de Mau · tokens de las 100 · costo cuando la real es `revision_manual` · plazo y tamaño del set ciego · puntaje de Rival 3B · si la llave es compartida.
- **Primera acción de S003:** acuse §4 · `git log --oneline -3` para fijar el SHA de `main` · pedir a Fer la salida de la corrida de 100 (o correrla) · auditar en orden de llegada las entregas sin auditar (`docs/reportes/` sin tachar: U1 primero) · luego **escribir I2** en `prompts-integrador.md` con las lecturas reales y el resultado de N1+D1.

## 🟢 Si estás abriendo la sesión siguiente, lee esto primero

- El sábado es **S002**: abre con `S002 3B. Lee el prompt inicial` → `PROMPT-APERTURA-S002.md` + el relevo de abajo. Donde las instrucciones digan «S001» para el sábado, léase S002.
- Aún **no hay reto**: se conoce a las 9:00 y se elige por orden de llegada.
- El repo trae plantilla previa sin producto: I0, I0.1 y **U0** hechas y auditadas. Los cuatro carriles están en `NINGUNO — BLOQUEADO` hasta que S002 escriba sus misiones 1.
- Plan de horas en `plan-del-dia.md`. Arquitectura en `arquitectura-provisional.md`. Sistema de diseño en `repo/DESIGN.md`.

## Relevo para S002 (sábado)

Escrito al cerrar S001.5, 2026-11-20 21:00.
- **Fase:** antes de F0. Reto por elegir a las 9:00; ranking provisional por la pista de Data: J3 · J1 · J4 · J6 (ver «Reto» abajo). PA-000.4 sigue abierto: confirmarlo con el equipo en sede.
- **Carriles:** UI sellado 20:59, ~~U0~~, `BLOQUEADO hasta U1`. Integrador (16:32 del 17-nov), Núcleo y Datos (14:54 del 17-nov) `BLOQUEADO hasta I1/N1/D1`. Sin entregas sin auditar.
- **`main` = `c366e8d`** (merge del PR #1, U0) `[MEDIDO 20:58: origin/main en el clon del chat y git log de Fer]`. En producción `/tema` responde `[MEDIDO 20:59 en Chrome]`. **`/salud` de producción quedó en «Revisando…»** a las 20:59 (dos intentos, 3 y 8 s); a las 20:10 marcó `cdc2c6c · base ok 1050 ms` y la vista previa de U0, a las 20:51, `7ca3494 · base ok 669 ms`. **Primera medición del sábado: `/salud` con el SHA `c366e8d` y `base ok`** (abrirla en sede para despertar la base).
- **Auditoría U0 → Aprobado con anotaciones:** lint y build en verde, grep de colores vacío, 12 botones y 3 campos a 44 px, campo a 16 px `[MEDIDO 20:51]`. S2: `text-[13px]` y `text-[35px]` en `/tema` (iguales a los tokens `mono` y `figure`, sin clase de utilidad). **No verificado:** `/tema` en celular (Fer pidió integrar antes de verla).
- **S2 que sube de peso para el sábado:** `revisarBase()` (`lib/datos/servidor.ts`) no tiene tope de tiempo; si la base no contesta, la página espera sin fin. **Toda lectura a la base que escriba D1/I1 lleva tope de tiempo (≈3 s) y estado de error**: la demo no puede quedarse en «cargando».
- **Ensayo E0:** PR #2 Alan, PR #3 Mauski, rama `prueba/sergio` empujada (PR por abrir). **Falta Mau.** Los PR de ensayo no se integran. Sergio tiene `.env.local` y `base ok` en local `[REPORTADO: captura, 20:44]`; su invitación se reenvió a las 20:39 y ya empujó.
- **Decisiones de S001.5:** Mauski trabaja en **chat web** (no Claude Code): sus misiones van autocontenidas y pidiendo archivos completos, como las de Sergio; lo pesado de Núcleo va al Code de Fer. Mau usa Antigravity Pro (agente en el repo): es el respaldo para misiones de repo.
- **Primera acción de S002:** acuse de §4; medir `/salud` (SHA `c366e8d`, `base ok`); pedir el reto con la plantilla de `PROMPT-APERTURA-S002.md`. En F1, escribir los paquetes `docs/paquetes/<nombre>.md` según esa apertura.

## Evento `[LEÍDO: láminas de 3B, captura 17-nov-2026]`

Sábado 21-nov-2026 · registro 7:00 · retos, reglas y criterios 9:00 · desarrollo **9:30–17:00** · comida 13:30 · presentaciones 17:00 · premiación 19:00. Sede: `<<sin registrar>>`.

## Equipo y carriles

| Rol | Quién | Asistente / cuenta |
|---|---|---|
| Orquestador e integrador · **diseño y carril UI** | Fer | **Claude Max** (este proyecto, Claude Code y Claude Design con las skills de diseño): **el que más cuota tiene** |
| UI de apoyo y quien maneja la demo | Mau | **Antigravity Pro** (agente en el repo, todos los modelos de Gemini) `[dicho por Fer, 20-nov 19:15]`: puede recibir misiones de repo, no solo de chat · E0 pendiente |
| Carril Núcleo | Mauski | **Claude Pro, chat web** (Opus 5.5) `[E0 de Mauski y dicho por Fer, 20-nov 20:56]`: misiones autocontenidas, archivos completos |
| Carril Datos e IA | Sergio (lo pidió) | **Claude gratuito** → chat web en claude.ai (macOS), cuota corta: misiones chicas; lo pesado de Datos va al Claude Code de Fer. Tiene `.env.local` |
| Negocio y pitch | Alan | Antigravity con Google AI Pro (Gemini), toca el repo `[E0 de Alan]` |

Mau, Mauski y Alan los asignó Claude a petición del equipo; se pueden intercambiar entre ellos. Fer tomó diseño y UI (17-nov 13:46): él fija la dirección visual y construye las pantallas del camino dorado; Mau construye estados vacío/cargando/error, responsive y pantallas secundarias **sobre el tema de Fer**, y maneja la demo en el pitch.

**Riesgo aceptado:** Fer integra y diseña a la vez. Si a las 11:30 o a las 13:15 la integración se atrasa, el diseño cede: las pantallas pasan a Mau y Fer solo integra.

### Política de cuota (rige el sábado)

- Fer tiene Claude Max (Code); Mauski, Claude Pro en chat web; Sergio, Claude gratuito en chat web; Mau y Alan, Antigravity con Gemini. **La cuota es un recurso del día como el reloj.**
- Este chat: Opus en esfuerzo **medio**; **alto** solo para el plan de F1 y para auditar el diferenciador. Respuestas cortas; no releer documentos ya leídos.
- Misiones para Mau, Mauski y Sergio: **autocontenidas** (todo lo necesario va en el texto, sin «lee tal documento»), de 30–45 min, sin asumir qué asistente usan, pegables en cualquier chat.
- Lo de escalón fuerte (el diferenciador, un arreglo devuelto una vez, algo que cruza carriles) va al **Claude Code de Fer**, no a un compañero.
- Si a alguien se le acaba la cuota: push de su rama, su misión pasa al Claude Code de Fer y él toma trabajo manual (semilla en hoja de cálculo, pruebas en celular, capturas).

## Reto, alcance y camino dorado

`<<se llena en F1, sábado 9:30–10:00>>`

**Pista (S001.5, viernes 20-nov 19:15)** `[REPORTADO: Ivan, empleado de 3B, por Instagram a Sergio; no oficial]`: los retos «son más para el área de Data» y están enfocados en algo que 3B usa hoy. Consecuencia: el ranking de `retos-probables.md` §1 se reordena a **J3 pronóstico/pedido sugerido · J1 rutas · J4 merma · J6 ubicaciones**; probable que entreguen un archivo de datos (CSV/Excel) → `datos/privado/` hasta confirmar confidencialidad; Python por lotes queda más probable. Un tablero solo no gana: tiene que terminar en una decisión con pesos.

## Recursos

| Qué | Valor |
|---|---|
| Repo GitHub | `luisfernandomtzg/hackathon-3b` · **público** (Vercel Hobby despliega commits de todos; sin secretos ni datos de 3B) |
| Proyecto Supabase | `hackathon-3b` (ref `pshtomfqgbobxheehoij`) en la org **Hackathon 3B**, plan gratuito, RLS automático. Pausa tras 7 días sin uso: abrirlo el viernes |
| Proyecto Vercel / URL de la demo | `hackathon-3b` (equipo luisfernandomtzgDeploys, Hobby) · **https://hackathon-3b.vercel.app** · `/salud` `[MEDIDO 20-nov 20:10: commit cdc2c6c, rama main, base ok 1050 ms]` · vista previa por rama: `hackathon-3b-git-<rama>-luisfernandomtzg-deploys.vercel.app` · push→Ready ≈ 27 s · control remoto: `repo/remoto-hackathon-3b.ps1` |
| Llave de API de modelo | `<<sin crear>>` |
| Modelos por escalón (rápido · general · fuerte) | `<<anotar los nombres vigentes al crear las cuentas>>` |

## Decisiones cerradas (S000)

- Stack: Next.js + Tailwind + shadcn/ui · Supabase · Vercel · GitHub. Python solo si el reto lo exige, y por lotes.
- Varios programan en paralelo: carpetas = carriles; un solo integrador.
- Un entorno, sin login, datos solo desde servidor, web responsiva.
- **Plantilla previa sí** (S000, 17-nov): la IA está permitida y nada lo prohíbe. Andamiaje sin producto. Si a las 9:00 lo prohíben, se declara qué traía el repo.
- Roles asignados (ver tabla). Repo público.

## Método de trabajo del sábado (decidido en S001, 18-nov)

- **OpenSpec no se adopta** (lo propuso Mauski): duplica lo que ya hacen `prompts-<carril>.md` + `lib/contrato` + `CLAUDE.md`, agrega instalación y ceremonia por cambio, y choca con `ESTADO` y la regla de paro.
- **Una rama por sprint, desde `main` fresco** (`carril/<area>-sp<N>-<tema>`), y **PR hacia `main`**; solo Fer hace merge, después de auditar. Plantilla en `docs/pull_request_template.md`; el reporte va también en `docs/reportes/`.
- **Sprints de ~1 h, escalonados 15 min** (Datos :15 · Núcleo :30 · Mau :45 · Fer :00); ventanas exactas en `KIT-EQUIPO.md` §6. A las 15:30 se congela lo que haya: la cola de cada área va ordenada y lo de abajo se puede recortar.
- **Listón de auditoría: exprés S0/S1/S2 (§9).** Fable u Opus en esfuerzo alto solo para el plan de F1 y para el diferenciador. El chat audita PRs clonando el repo público (`git fetch origin pull/<n>/head`); la API de PRs de GitHub no está habilitada desde el chat (habría que adjuntar el repo).
- **Un kit universal para cualquier IA:** `docs/KIT-EQUIPO.md` (Parte A, escrita en S001). El sábado, F1 genera solo la Parte B por persona → `docs/paquetes/<nombre>.md` = kit + área, con detalle solo en SP0–SP1; el resto se recalibra tras cada auditoría.
- **Sistema de diseño «Tarima» (18-nov 18:16, Fer):** se continúa la identidad pública de 3B (rojo `#E31B23`, tinta `#04211F`, Montserrat; medidos en tiendas3b.com) en vez de un tema neutro. Precisa la regla de §11 de las instrucciones: **sí** su paleta y tipografía; **no** su logotipo ni una imitación de él, ni sus banners. `DESIGN.md` manda sobre cualquier pantalla. Sin extractor instalado: los agentes evaluaron ~25 repos (dembrandt, designlang, brandmd, impeccable, design.md de Google…) y se adoptó solo el formato `DESIGN.md` de Google.
- **Ensayo `E0` jueves o viernes:** cada compañero instala, le da el kit a su IA, hace un PR `prueba/<nombre>` con `docs/equipo/<nombre>.md` (qué IA y de qué tipo) y comprueba la vista previa de Vercel. Cierra PA-000.2 y PA-000.3.

## Respuestas de los organizadores (`checklist-previo.md` §4)

| Pregunta | Respuesta |
|---|---|
| ¿Se permite plantilla previa? | no lo prohíben ni lo mencionaron → se asume que sí |
| Criterios y pesos | sin respuesta |
| Minutos de presentación y formato | sin respuesta |
| Entregables · ¿repo público? | sin respuesta |
| ¿Dan datos? ¿confidenciales? | sin respuesta |
| Mentores | sin respuesta |

## Puntos abiertos

- ~~PA-000.2~~ · cerrado 20-nov: Alan, Mauski y Sergio empujaron ramas `prueba/*`; vista previa por rama medida en U0. (Antes:) Push de prueba de un compañero (`prueba/<nombre>`) y su vista previa en Vercel: cierra el paso 5 de I0.1 — Fer, al invitar a los cuatro — jueves.
- ~~PA-000.6 · Quitar `next/font/google` de `app/layout.tsx`~~ — cerrado en S001 con Tarima (build en verde sin Google Fonts). U0 hecha en S001.5.
- PA-000.5 · Vercel pide verificar identidad con código al correo de reenvío de Apple y no llega: revisar «Ocultar mi correo» en iCloud. Mientras, se despliega por push (funciona) — Fer.
- ~~PA-000.3~~ · cerrado 20-nov: los cuatro invitados (Sergio reenviado 20:39); falta el `docs/equipo/` de Mau. (Antes:) Invitar a los cuatro al repo con permiso de escritura y que cada uno anote su asistente aquí — Fer — jueves.
- PA-000.4 · Ranking de retos acordado por el equipo — todos — viernes.
- ~~PA-001.1~~ · cerrado 20-nov 19:15: Mau usa Antigravity Pro. (Antes:) Preguntar a Mau, Mauski y Sergio qué IA usarán y si toca el repo o es chat web (planes gratuitos cambiaron en 2026: Gemini CLI → Antigravity para cuentas gratuitas; altas nuevas a Copilot de estudiante pausadas desde el 20-abr) — Fer — miércoles; se confirma en el ensayo `E0`.
- ~~PA-001.2~~ · cerrado 20-nov 20:44 (captura de Sergio con base ok). (Antes:) Pasar `.env.local` en privado solo a Sergio (los demás trabajan con datos simulados) — Fer — viernes.

## No verificado

- `/salud` de producción con `c366e8d` (quedó en «Revisando…» a las 20:59).
- `/tema` vista en un celular.
- Vistas previas de Vercel de las ramas `prueba/*` de los compañeros.
- Retos, criterios, entregables y reglas de la edición de noviembre: no publicados.
