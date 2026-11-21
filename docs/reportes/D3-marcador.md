D3 — Marcador para el pitch · rama carril/datos-sp3-marcador · sale de b0320a0 (main) · IA Claude (chat web, plan gratuito) · 40 min
Hecho: marcador.py genera salidas/marcador.md con costo, líneas base, precisión, sin persona, tokens y segundos; cada cifra lleva su etiqueta (MEDIDO, DATO 3B, PROYECCIÓN, SUPUESTO o NO MEDIDO).
Prueba de cierre: python -m ml.validat3b.marcador ... → costo 118 · base manual 100 · precisión 87.50 % · sin persona 59/100 · tokens 171,396 entrada + 20,684 salida · segundos promedio 2.2 (rango 1.0–21.7).
No hecho / simulado: horas ahorradas SIN DATO (falta segundos de analista de 3B, se pasa con --segundos-analista); la proyección de 7,080/semana asume 59 % en producción (PROYECCIÓN, no medida).
Archivos fuera de mi área: ninguno.
¿Tocó la base?: no.
Necesito de otra área: de 3B, segundos por captura de un analista; de Fer, confirmar el 59 % con el set ciego.
Cuelga de: main
