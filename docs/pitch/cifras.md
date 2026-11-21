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
| Precisión de aprobadas del motor | **100.00 % en las 100 capturas de desarrollo** (**10 aprobadas · 0 falsas**, cumple ≥ 97 %) | MEDIDO | `I6-tres.md` (`salidas-sp6.zip`, consenso unánime de 3 lecturas para aprobar) |
| Porcentaje de JSON válido | **100.00 %** (100 de 100 capturas válidas contra contrato Pydantic, cumple ≥ 99 %) | MEDIDO | `python -m ml.validat3b.entregar` (`I6-tres.md` / `I4-entrega.md`) |
| Costo operativo del motor (pesimista) | **104 puntos** (vs **100** de «todo a revisión manual» y **670** de «aprobar todo»; con 1 lectura era **99**) | MEDIDO + SUPUESTO | `I6-tres.md` (`salidas-sp6.zip`); asume SUPUESTO pesimista en `revision_manual` real (aprob=10, rech=3, man=1) |
| Costo operativo del motor (optimista) | **39 puntos** (vs **67** de «todo a revisión manual»; con 1 lectura era **38**) | MEDIDO + SUPUESTO | `I6-tres.md` (`salidas-sp6.zip`); asume SUPUESTO optimista en `revision_manual` real (aprob=10, rech=0, man=0) |
| Capturas resueltas sin persona | **50 de 100 (50 %)** (10 aprobadas + 40 rechazadas automáticamente; 50 a revisión manual; en sp4 era **49/100**) | MEDIDO | Matriz de `I6-tres.md` (`contexto-vigente-hackathon-3b.md`: aprob 10/2/21 · rech 0/22/12 · man 0/16/17) |
| Proyección de ahorro semanal de revisión | **6,000 capturas / semana** resueltas sin analista humano (5,880 con el 49 % previo a I6) | PROYECCIÓN | Proyecta el 50 % (o 49 %) medido en las 100 capturas de desarrollo sobre las 12,000 capturas/semana de 3B |
| Tokens por captura (motor final con consenso I6) | **2,390 tokens / captura** (238,959 tokens totales en 124 llamadas: 100 de 1ª lectura + 13 segundas + 11 terceras; **1,921** en 1ª lectura sola) | MEDIDO | `I6-tres.md` (`salidas/tokens.csv` en `salidas-sp6.zip` con `claude-haiku-5-5`) |
| Llamadas al modelo por captura | **1 llamada por captura, y 2 o 3 solo para las que se aprueban** (consenso unánime `LECTURAS_PARA_APROBAR = 3`) | MEDIDO | `ml/validat3b/consenso.py` (`I6-tres.md`) |
| Tiempo de corrida por lotes (4 hilos) | **~67.8 s** para 100 lecturas nuevas (~55 s para las 11 terceras lecturas de consenso en `I6`) | MEDIDO | `I2-lectura.md` y `I6-tres.md` (`correr.py --hilos 4`) |
| Señales locales sin tokens (`P1` / `P2`) | **20/100** códigos EAN/UPC leídos (7 coinciden) · **25** fachadas únicas (MD5) · **16/100** bajo umbral de nitidez 84/82 con 0 aprobadas reales | MEDIDO | `python -m ml.validat3b.local` (`P1-locales.md`) y `python -m ml.validat3b.puerta` (`P2-puerta.md`) |
| Horas de analista ahorradas por semana | **NO MEDIDO** (`[[segundos_analista_3b]]`) | NO MEDIDO | 3B no proporcionó segundos por captura de un analista humano (`marcador.py --segundos-analista`) |
| Costo en pesos de la API por captura | **NO MEDIDO** | NO MEDIDO | Sin tarifa oficial publicada por el comité para el endpoint de Azure AI Foundry |
| Puntaje de referencia «Rival 3B» | `[[puntaje_rival_3b]]` | PENDIENTE 14:30 | Se llena si el comité publica el puntaje de Rival 3B |
| Marcador final congelado (14:30 / set ciego) | `[[marcador_final_1430]]` | PENDIENTE 14:30 | Confirmación final de Sergio (`D3`) y Fer (`I6`) al congelar a las 14:30 / corrida del set ciego (15:00–16:00) |
