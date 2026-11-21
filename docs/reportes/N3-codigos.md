N3 — Códigos oficiales, tipo de precio y explicación · rama carril/nucleo-sp3-codigos · cuelga de 47c97a4 · commit b1d02db · modelo claude-haiku-5-5 · esfuerzo no visible · ~25 min
Hecho: `mapa_codigos.json` con los 11 códigos del contrato mapeados a sí mismos; `traducir(resultado, mapa)` pura (solo cambia el código si hay entrada); la explicación de oferta y volumen dice el tipo de precio; la explicación de la regla 1 ya no muestra `origen`.
Prueba de cierre: `py -3 -m unittest ml.validat3b.test_decidir -v` → Ran 19 tests, OK. `calibrar` sobre salidas-sp2 → costo pesimista 103 (igual), precisión 100 % (11/11), sin cambio a peor.
No hecho / simulado: `traducir()` aún no lo llama `correr.py` (Integrador); hasta que lo haga, el mapa no altera la salida oficial. La prueba de «todo código es llave del mapa» revisa las constantes RC_* del contrato, no los códigos que emite cada regla. Las 12 explicaciones revisadas por lectura, no con un analista.
Archivos fuera de mi carril que toqué: ninguno. Compuertas de Fer no tocadas (no duplicadas en decidir).
¿Tocó la base?: no.
Necesito de otro carril: Integrador (Fer): que `correr.py` pase cada `Resultado` por `traducir()` con `mapa_codigos.json`.
