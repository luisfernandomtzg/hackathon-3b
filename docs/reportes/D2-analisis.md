D2 — Análisis de errores y clasificador · rama carril/datos-sp2-analisis · sale de 689679d (main) · IA Claude (chat web, plan gratuito) · 60 min

1. Las reglas actuales (decidir.py) cuestan 118 con precisión 87.5 % (mínimo 97 %): descalificadas. Aprueban CAP-410562 y CAP-206200 por error.
2. El clasificador logístico no baja el costo de forma usable: con umbrales que aprueban más de 2 capturas, su precisión cae a 57 % (costo 253). El umbral 0.93 tiene costo 98 pero solo aprueba 2 capturas, no es evidencia.
3. Recomendación: no conectarlo al motor. Lo que mueve el número es calibrar las reglas (regla 12, dudosas), no un clasificador con estas señales.

Prueba de cierre: python -m ml.validat3b.analisis ... → costo 118, precisión 87.50 %, decidir() = resultados.json en 100 de 100. python -m ml.validat3b.clasificador ... → AUC 0.801, tabla en salidas/clasificador.md.
Tabla umbral → costo (fuera de muestra): 0.50 → 253 · 0.57 → 253 · 0.58 → 246 · 0.93 → 98 (2 aprobadas) · [completa con tus filas]
No hecho / simulado: la regla de revision_manual = SUPUESTO; muestra pequeña (n=100, 25 visitas); AUC de validación cruzada, no de producción.
Archivos fuera de mi área: ninguno (no toqué decidir.py ni locales.csv de otros)
¿Tocó la base?: no
Necesito de otra área: Mauski (calibrar regla 12 y dudosas), Fer (decidir si entra algún verificador).
