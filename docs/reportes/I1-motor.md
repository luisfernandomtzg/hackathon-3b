I1 — Esqueleto del motor Validat3B · rama carril/integrador-sp1-motor · cuelga de 47995c4 · commit ver PR · modelo Sonnet 5.5 · esfuerzo medium · ~50 min
Hecho: cargar.py, cliente.py (reintentos 429/5xx, caché en disco, tokens.csv), extraer.py v1 (1 llamada, 768 px, JPEG 80), correr.py (JSON+CSV+extracciones, excepción por captura -> revision_manual), README de ml.
Hecho: decidir_provisional.py; correr.py importa .decidir si existe y si no .decidir_provisional (pedido de Fer).
Hallazgo: claude-haiku-5-5 piensa por defecto y agotaba max_tokens sin texto; el cliente manda thinking={"type":"disabled"}.
Prueba de cierre: --sin-modelo -> "100 capturas · 100 válidas · 0 tokens".
Prueba de cierre: --limite 5 -> "5 válidas · 9324 tokens · 1865 tokens/captura · origenes {'modelo': 5}"; segunda corrida -> "0 tokens · origenes {'cache': 5}".
git status sin datos/ ni salidas/; FOUNDRY_API_KEY solo se lee del entorno en cliente.py.
No hecho / simulado: decisión = provisional (todo revision_manual); fachada no se envía en v1; codigo_barras_leido y cadena_en_fachada quedan null; corrida de 100 con modelo no hecha; sin evaluar precisión; 2 de 5 lecturas sin contenido (g/ml) en la muestra.
Archivos fuera de mi carril que toqué: ninguno
¿Tocó la base?: no
Necesito de otro carril: Núcleo entrega decidir.py (N1); Datos evalúa con evaluar.py.
