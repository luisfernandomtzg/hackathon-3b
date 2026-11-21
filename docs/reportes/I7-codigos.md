I7 — Zip final con reason_code de N4, desde caché · rama carril/integrador-sp3-codigos · cuelga de 8211c45 · commit ver PR (solo el reporte) · modelo Sonnet 5.5 · esfuerzo medium (pedido; en uso no visible) · ~8 min
Hecho: motor normal (con cliente, 4 hilos, `--datos datos/privado`) sobre una copia del caché de lecturas; sin cambios de código.
Caché usado: salidas/G/cache (211 llaves: A en la llave base, B sembrada como «-b», 11 terceras «-c»), copiado a salidas/sp7/cache. salidas/sp6 no lo traía.
Tokens nuevos: 0 (cero filas origen=modelo en el tokens.csv de la corrida; 100 de origen cache).
Tabla sp6 → sp7 (aprobadas · falsas · precisión · costo pes/opt · reason_code correcto en rechazadas reales con motivo): 10 · 0 · 100 % · 104/39 · 2 → 10 · 0 · 100 % · 104/39 · 8 · JSON válido 100/100.
Decisiones: 0 distintas de sp6; las mismas 10 aprobadas por capture_id; cambian 34 reason_code.
Nota de cifra: evaluar.py mide 8 de 34 rechazadas reales (denominador de todas las reales con motivo); la misión decía 8/22 sobre las 22 rechazadas correctamente: son los mismos 8.
tokens.csv del zip = el de sp6 (124 llamadas reales, 2,390 tokens por captura), NO el de la corrida desde caché (0), como pide la misión.
No hecho / simulado: no regeneré extracciones ni locales (iguales a sp6); `correr --desde-extracciones` no sirve con consenso (sin cliente baja las aprobadas), por eso se usó el caché; la corrida leyó las imágenes de datos/privado (mismas bytes que el ensayo, mismas llaves).
Archivos fuera de mi carril que toqué: ninguno · ¿Tocó la base?: no
zip: ..\salidas-sp7.zip (resultados.json, extracciones.json, locales.csv, tokens.csv; sin cache/).
