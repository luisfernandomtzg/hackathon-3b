# Tabla de Cifras y Fuentes — Pitch Validat3B

> **Regla (`KIT-EQUIPO.md` §2.8 y `paquetes/alan.md`):** ninguna cifra inventada. Cada número en pantalla o en el guion es un **DATO 3B** con nombre, una **MEDICIÓN** nuestra en el repo, una **PROYECCIÓN / SUPUESTO** explícito, o un hueco `[[...]]` para el corte de las 14:30 / set ciego.

| Cifra | Valor en el pitch | Tipo | Fuente exacta |
|---|---|---|---|
| Capturistas en campo | **~800 capturistas** | DATO 3B | Alfredo, negocio Tiendas 3B (sesión Q&A, 21-nov-2026) |
| Volumen semanal de capturas | **~12,000 capturas / semana** revisadas una por una | DATO 3B | Alfredo, negocio Tiendas 3B (sesión Q&A, 21-nov-2026) |
| Meta de negocio (calidad vs volumen) | **«Preferimos 80 de 100 con error casi cero»** / **«Un peso por millones de ventas son millones»** | DATO 3B | Alfredo, negocio Tiendas 3B (sesión Q&A, 21-nov-2026) |
| Matriz oficial de puntos de costo | **0** acierto · **1** revisión manual · **3** rechazar válida · **10** aprobar inválida | REGLA DEL RETO | Página oficial del Reto 2 · Validat3B (`hackaton3b.com/validat3b.html`, leído 21-nov 09:16) |
| Umbrales de descalificación | **< 97 %** precisión en aprobadas · **< 99 %** JSON válido · entrega tarde | REGLA DEL RETO | Página oficial del Reto 2 · Validat3B (`hackaton3b.com/validat3b.html`, leído 21-nov 09:16) |
| Pesos de evaluación del reto | **50 %** costo operativo · **15 %** calidad del dato · **10 %** tokens · **25 %** pitch (3 min) | REGLA DEL RETO | Página oficial del Reto 2 · Validat3B (`hackaton3b.com/validat3b.html`, leído 21-nov 09:16) |
| Lote de desarrollo | **100 capturas** (33 aprobadas, 34 rechazadas, 33 revisión manual) y **300 imágenes** | MEDIDO | `datos/privado/metadatos/capturas.csv` (`D1-evaluar.md` / `D3-marcador.md`) |
| Motivos de rechazo en desarrollo | **18** capturas lejanas · **11** capturas borrosas · **5** descripción incompleta | MEDIDO | `datos/privado/metadatos/capturas.csv` (`D1-evaluar.md`) |
| Señal en metadatos de desarrollo | **0 % poder discriminante** (`capture_barcode == product_barcode` y precio en rango en 100/100) | MEDIDO | Arquitecto sobre `capturas.csv` (21-nov 09:16) |
| Precisión de aprobadas del motor | **100.00 % en las 100 capturas de desarrollo** (**16 aprobadas · 0 falsas**, cumple ≥ 97 %; con las reglas anteriores eran 10) | MEDIDO | `ml.validat3b.evaluar` sobre `salidas/sp12/resultados.json` (S005, 21-nov 13:59: lectura v3 + reglas N8, consenso unánime de 3 lecturas) |
| Porcentaje de JSON válido | **100.00 %** (100 de 100 capturas válidas contra contrato Pydantic, cumple ≥ 99 %) | MEDIDO | `python -m ml.validat3b.entregar` (`I6-tres.md` / `I4-entrega.md`) |
| Costo operativo del motor (pesimista) | **85 puntos** (vs **100** de «todo a revisión manual» y **670** de «aprobar todo»; sp8 era **104**, sp9 **92**) | MEDIDO + SUPUESTO | `evaluar` sobre `salidas/sp12` (S005 13:59); asume SUPUESTO pesimista en `revision_manual` real (aprob=10, rech=3, man=1) |
| Costo operativo del motor (optimista) | **28 puntos** (vs **67** de «todo a revisión manual»; sp8 era **39**, sp9 **35**) | MEDIDO + SUPUESTO | `evaluar` sobre `salidas/sp12` (S005 13:59); asume SUPUESTO optimista en `revision_manual` real (aprob=10, rech=0, man=0) |
| Capturas resueltas sin persona | **54 de 100 (54 %)** (16 aprobadas + 38 rechazadas automáticamente; 46 a revisión manual) | MEDIDO | Matriz de `salidas/sp12` (real→decidido: aprob 16 aprob / 1 rech / 16 man · rech 0/25/9 · man 0/12/21) |
| Capturas válidas rechazadas por el motor | **1 de 33** (CAP-170513; en sp8 eran 2) | MEDIDO | Matriz de `salidas/sp12` (S005) |
| Hallazgo: «lejana» y «borrosa» describen la FOTO DEL LETRERO | Las **33** aprobadas reales tienen el letrero nítido y a **≥ 25 %** del ancho de la foto; con ≤ 20 %, «lejano» o «borroso» hay **16** rechazadas reales, **4** de revisión y **0** aprobadas | MEDIDO | Lectura v3 de `salidas/sp11/extracciones.json` cruzada con `capturas.csv` (S005, 13:55) |
| Motivo de rechazo correcto | **11 de 25** rechazadas correctas (antes 8 de 22) | MEDIDO | `salidas/sp12` contra `motivo_rechazo` (S005) |
| Proyección de ahorro semanal de revisión | **6,480 capturas / semana** resueltas sin analista humano | PROYECCIÓN | Proyecta el 54 % medido en las 100 capturas de desarrollo sobre las 12,000 capturas/semana de 3B |
| Tokens por captura (motor final: lectura v3 + consenso) | **~3,100 tokens / captura** (139 llamadas para 100 capturas × 2,261 tokens por llamada) | MEDIDO + CÁLCULO | 2,261 = 282,609 tokens ÷ 125 llamadas reales en `salidas/sp11/tokens.csv`; 139 llamadas = filas de `salidas/sp12/tokens.csv` (100 primeras lecturas + 39 de consenso). Con v2 eran 2,390 |
| Llamadas al modelo por captura | **1 llamada por captura, y 2 más solo para las que se van a aprobar** (consenso unánime `LECTURAS_PARA_APROBAR = 3`) | MEDIDO | `ml/validat3b/consenso.py`; en sp12: 20 candidatas, 16 aprobadas, 4 bajadas por el consenso |
| Tiempo de corrida por lotes (4 hilos) | **~67.8 s** para 100 lecturas nuevas (~55 s para las 11 terceras lecturas de consenso en `I6`) | MEDIDO | `I2-lectura.md` y `I6-tres.md` (`correr.py --hilos 4`) |
| Señales locales sin tokens (`P1` / `P2`) | **20/100** códigos EAN/UPC leídos (7 coinciden) · **25** fachadas únicas (MD5) · **16/100** bajo umbral de nitidez 84/82 con 0 aprobadas reales | MEDIDO | `python -m ml.validat3b.local` (`P1-locales.md`) y `python -m ml.validat3b.puerta` (`P2-puerta.md`) |
| Horas de analista ahorradas por semana | **NO MEDIDO** (`[[segundos_analista_3b]]`) | NO MEDIDO | 3B no proporcionó segundos por captura de un analista humano (`marcador.py --segundos-analista`) |
| Costo en pesos de la API por captura | **NO MEDIDO** | NO MEDIDO | Sin tarifa oficial publicada por el comité para el endpoint de Azure AI Foundry |
| Puntaje de referencia «Rival 3B» | `[[puntaje_rival_3b]]` | PENDIENTE 14:30 | Se llena si el comité publica el puntaje de Rival 3B |
| Marcador final congelado (14:30 / set ciego) | `[[marcador_final_1430]]` | PENDIENTE 14:30 | Confirmación final de Sergio (`D3`) y Fer (`I6`) al congelar a las 14:30 / corrida del set ciego (15:00–16:00) |
