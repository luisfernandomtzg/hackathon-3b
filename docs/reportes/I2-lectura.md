I2 — Lectura v2, señales locales y re-decisión sin tokens · rama carril/integrador-sp2-lectura · cuelga de 689679d · commit c9e4f03 · modelo Sonnet 5.5 · esfuerzo high (pedido; en uso no visible) · ~25 min
Hecho: contrato v1.1 (contenido_legible, senales; 24 pruebas de N1/P1/D1 en verde sin tocarlas); prompt v2; señales locales en correr.procesar; `--desde-extracciones`; evaluador.py quitado (commit aparte). El caché ahora incluye el hash del prompt: editarlo ya no sirve lecturas viejas.
Prueba de cierre: 100 con modelo → 100/100 JSON válido · 192,080 tokens (1,921/captura; v1 1,753; entrada 1,733 vs 1,661 = +4.3 %) · 67.8 s.
Prueba de cierre: evaluar → aprobó 16, 14 correctas, 2 falsas = 87.5 % (NO PASA, mínimo 97 %) · costo pesimista 118 / optimista 52.
Matriz real→pred: aprobada 14/2 rech/17 manual · rechazada 1 aprob/24/9 · manual 1 aprob/17 rech/15.
Tabla v1 → v2: precisión 79 % (15/19) → 87.5 % · costo pesimista 151 → 118 · optimista 74 → 52 · «todo revisión» 100/67.
Lejanas reales (18): detectadas v1 0 → v2 6 (solo `lejano` 1; `contenido_legible=false` el resto). 489454 y 241497 siguen «cercano»+legible: v2 NO las detecta. Válidas (33): 0 contenido null y 0 marcadas lejano/ilegible, sin regresión.
`--desde-extracciones` da resultados.json idéntico y tokens.csv no crece (101 líneas). `git status` sin datos/ ni salidas/.
Las 2 falsas aprobadas: CAP-206200 (real manual) y CAP-410562 (real rechazada); no las analicé: son de N2.
No hecho / simulado: sigue sin pasar el 97 %; lejanas sin resolver con lectura (¿señal local de tamaño de texto o la fachada?); evaluar usa supuestos de D1 para costos; `salidas-sp2.zip` queda local (sin cache/), no commiteado.
Archivos fuera de mi carril que toqué: ml/evaluador.py (borrado por orden de la misión)
¿Tocó la base?: no · Necesito de otro carril: N2 sobre las lecturas v2 (descripción corta, aprobadas falsas)
