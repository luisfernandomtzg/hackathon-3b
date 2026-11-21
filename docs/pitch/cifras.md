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
| Precisión de aprobadas del motor | **100.00 % en las 100 capturas de desarrollo** (**10 aprobadas · 0 falsas**, cumple ≥ 97 %) | MEDIDO | `python -m ml.validat3b.marcador` sobre `salidas-sp4.zip` (`D3-marcador.md`, `I3.1-compuerta.md`) |
| Porcentaje de JSON válido | **100.00 %** (100 de 100 capturas válidas contra contrato Pydantic, cumple ≥ 99 %) | MEDIDO | `python -m ml.validat3b.evaluar` (`I3.1-compuerta.md` / `I4-entrega.md`) |
| Costo operativo del motor (pesimista) | **99 puntos** (vs **100** de «todo a revisión manual» y **670** de «aprobar todo») | MEDIDO + SUPUESTO | `marcador.py` (`D3.1`); asume SUPUESTO pesimista en `revision_manual` real (aprob=10, rech=3, man=1) |
| Costo operativo del motor (optimista) | **38 puntos** (vs **67** de «todo a revisión manual») | MEDIDO + SUPUESTO | `evaluar.py` (`I3.1-compuerta.md`); asume SUPUESTO optimista en `revision_manual` real (aprob=10, rech=0, man=0) |
| Capturas resueltas sin persona | **49 de 100 (49 %)** (10 aprobadas + 39 rechazadas automáticamente; 51 a revisión manual) | MEDIDO | `marcador.py` (`D3.1`) sobre `resultados.json` del motor final (`decidir()` de N2 + `compuerta()` de I3.1) |
| Proyección de ahorro semanal de revisión | **5,880 capturas / semana** resueltas sin analista humano | PROYECCIÓN | `marcador.py` (`D3.1`): proyecta el 49 % medido en las 100 capturas de desarrollo sobre las 12,000 capturas/semana de 3B |
| Tokens por captura (motor final) | **1,921 tokens / captura** (171,396 entrada + 20,684 salida en 100 capturas con `claude-haiku-5-5`) | MEDIDO | `salidas/tokens.csv` (origen `modelo`, lectura v2 a 768 px JPEG q80; `D3-marcador.md`) |
| Tiempo de corrida por lotes (4 hilos) | **~67.8 s** con llamadas al endpoint (~18.1 s desde caché con señales locales) | MEDIDO | `I2-lectura.md` y `I4-entrega.md` (`correr.py --hilos 4`) |
| Señales locales sin tokens (`P1` / `P2`) | **20/100** códigos EAN/UPC leídos (7 coinciden) · **25** fachadas únicas (MD5) · **16/100** bajo umbral de nitidez 84/82 con 0 aprobadas reales | MEDIDO | `python -m ml.validat3b.local` (`P1-locales.md`) y `python -m ml.validat3b.puerta` (`P2-puerta.md`) |
| Horas de analista ahorradas por semana | **NO MEDIDO** (`[[segundos_analista_3b]]`) | NO MEDIDO | 3B no proporcionó segundos por captura de un analista humano (`marcador.py --segundos-analista`) |
| Costo en pesos de la API por captura | **NO MEDIDO** | NO MEDIDO | Sin tarifa oficial publicada por el comité para el endpoint de Azure AI Foundry |
| Puntaje de referencia «Rival 3B» | `[[puntaje_rival_3b]]` | PENDIENTE 14:30 | Se llena si el comité publica el puntaje de Rival 3B |
| Marcador final congelado (14:30 / set ciego) | `[[marcador_final_1430]]` | PENDIENTE 14:30 | Confirmación final de Sergio (`D3`) y Fer (`I4`) al congelar a las 14:30 / corrida del set ciego (15:00–16:00) |
