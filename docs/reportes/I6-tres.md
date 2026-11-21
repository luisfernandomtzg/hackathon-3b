I6 — Consenso unánime de tres lecturas para aprobar · rama carril/integrador-sp3-tres · cuelga de 1bfce55 · commit b8f7ee8 · modelo Sonnet 5.5 · esfuerzo high (pedido; en uso no visible) · ~15 min
Hecho: consenso.py con LECTURAS_PARA_APROBAR = 3 (unánime, no «2 de 3»); lecturas 2 y 3 con llaves de caché propias («-b», «-c»); la tercera solo se pide si la segunda aprueba; error o desacuerdo → revisión manual, nunca aprueba de más.
Pruebas: 70 en verde; test_consenso: una de tres que no aprueba → revisión; la tercera no se llama si la segunda no aprueba (se pone roja si se llama siempre; mutación comprobada); cableado en correr sigue rojo si se quita el consenso.
Corrida C: lectura 1 = A (I4), lectura 2 = B (I5, ya en caché), lectura 3 = 11 llamadas nuevas en frío (a las 11 que A y B aprobaron).
Tabla (aprobadas · falsas · precisión · costo pes/opt · tokens/captura): consenso de 2 → 11 · 0 · 100 % · 103/38 · 2,175 | consenso de 3 → 10 · 0 · 100 % · 104/39 · 2,390 (tope 2,600).
Frente al de 2 baja 1 válida (CAP-393879; tope 3); la falsa 489454 ya no entra. entregar --datos salidas/ensayo → VALIDACIÓN: OK (55 s con 11 llamadas nuevas).
Tokens: 124 llamadas = 238,959 (100 de lectura + 13 segundas + 11 terceras) → +24 % sobre 1,921 de la lectura sola; el 10 % de la nota por tokens pesa más con esto.
No hecho / simulado: sigue siendo UNA tercera lectura sobre dos muestras ya vistas; la unanimidad de 3 baja la probabilidad de colarse de ~1/4 a ~1/8 para una lejana que se aprueba una de cada dos veces, no la anula; no medí otra vez las 100 completas con 3 lecturas frías.
Archivos fuera de mi carril que toqué: ninguno · ¿Tocó la base?: no
zip: ..\salidas-sp6.zip (resultados.json, extracciones.json, locales.csv y tokens.csv con las 124 llamadas, sin prefijos).
Necesito de otro carril: una señal local o de prompt para «lejana» (Núcleo/Pitch); sin ella el riesgo sigue siendo muestreo.
