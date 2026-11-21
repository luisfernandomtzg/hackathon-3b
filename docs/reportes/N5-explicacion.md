N5 — Explicación de la regla 7 coherente con su código · rama carril/nucleo-sp3-explicacion · cuelga de aa85b57 · commit ac7e5bb · modelo claude-haiku-5-5 · esfuerzo no visible · ~10 min
Hecho: la explicación de la regla 7 dice «No se distingue con claridad el producto en la foto (captura lejana o poco nítida)» y conserva marca, descripción, contenido leídos y lo esperado. Código, decisión y confianza sin cambio.
Prueba de cierre: `py -3 -m unittest ml.validat3b.test_decidir -v` → Ran 19 tests, OK (incluye la nueva test_20, que falla con el texto viejo). `calibrar` → costo 103, precisión 100 % (11/11), sin cambio.
No hecho / simulado: nada simulado. La frase no se ha leído con un analista de precios.
Archivos fuera de mi carril que toqué: ninguno (solo decidir.py y test_decidir.py).
¿Tocó la base?: no.
Necesito de otro carril: nada.
