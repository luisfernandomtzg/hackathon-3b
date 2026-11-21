D1 — Arnés de evaluación · rama carril/datos-sp1-evaluar · sale de 47995c4 · IA Claude (chat web, plan gratuito) · 40 min
Hecho: evaluar.py con JSON válido, costo (2 escenarios SUPUESTO), precisión, matriz 3x3, costo por motivo, líneas base, calidad del dato, 15 errores más caros y --por-visita.
Hecho: test_evaluar.py con 6 capturas inventadas.
Prueba de cierre (unittest): Ran 7 tests · OK
Prueba de cierre (datos reales, todo revision_manual): 100/100 JSON válido · costo pesimista 100 · optimista 67 · precisión NO MEDIBLE (aprobó 0)
Matriz: real aprobada 33, rechazada 34, revision_manual 33 → todas predichas revision_manual.
Calidad del dato: 0/34 reason_code y 0/33 precio (sin predicciones de esos campos, esperado).
No hecho / simulado: regla de revision_manual = SUPUESTO (pesimista y optimista); reason_code provisionales; la segunda parte a mano (33 capturas) sigue pendiente.
Archivos fuera de mi área: ninguno · ¿Tocó la base?: no
Necesito de otra área: regla oficial de revision_manual y lista oficial de reason_code (comité / Fer).
