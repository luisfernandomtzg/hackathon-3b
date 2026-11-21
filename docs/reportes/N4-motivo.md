N4 — Motivo correcto en las rechazadas · rama carril/nucleo-sp3-motivo · cuelga de 1bfce55 · commit b3c1277 · modelo claude-haiku-5-5 · esfuerzo no visible · ~30 min
Hecho: la regla 6 (contenido faltante) emite DESCRIPCION_INCOMPLETA en vez de LEJANA; la regla 7 (producto no coincide) emite CAPTURA_LEJANA; `traducir()` y su prueba quitados. Decisiones sin cambio.
Prueba de cierre: `py -3 -m unittest ml.validat3b.test_decidir -v` → Ran 18 tests, OK. `calibrar` → costo 103, precisión 100 % (11/11), sin cambio.
No hecho / simulado: NO medí con salidas-sp5.zip: no está en Descargas. Medí con salidas-sp2 (mismo set de 100 capturas, lecturas v2): sección 7 pasa de 2/34 a 11/34. Falta correrlo con sp5. La regla 4 y la regla 8 no cambié: la 4 tiene una sola captura medida y la 8 no tiene motivo lógico en 3B.
Archivos fuera de mi carril que toqué: ninguno.
¿Tocó la base?: no.
Necesito de otro carril: Sergio o Fer: el zip salidas-sp5 para medir de verdad. La explicación de la regla 7 aún dice «no coincide» aunque el código sea CAPTURA_LEJANA.
