N6 — Tabla de reason_code internos y procedimiento de 15:00 · rama carril/nucleo-sp3-codigos-oficiales · cuelga de f39f48a · commit (ver PR) · modelo claude-haiku-5-5 · esfuerzo no visible · ~15 min
Hecho: docs/entrega/codigos.md con los 11 códigos, la regla que los emite (o «ninguna» para FACHADA_INCORRECTA) y el procedimiento de 15:00 en 4 pasos. Sin código ni mapa tocados.
Prueba de cierre: tabla con 11 filas, cada una nombra su regla; git diff --stat main muestra solo docs/.
No hecho / simulado: columna «veces en sp7» sin medir (no hay salidas-sp7). Columna «código oficial probable» vacía hasta las 15:00.
Archivos fuera de mi carril que toqué: ninguno.
¿Tocó la base?: no.
Necesito de otro carril: Fer: docs/entrega/ está en .gitignore (regla entrega/); el archivo se agregó con git add -f igual que sus hermanos ya versionados. Confirmar que está bien o ajustar el .gitignore.
