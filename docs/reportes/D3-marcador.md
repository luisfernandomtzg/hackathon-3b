D3.1 — Marcador para el pitch (corrección de auditoría) · rama carril/datos-sp3-marcador · sale de 651f136 (main) · IA Claude (chat web, plan gratuito) · 20 min
Hecho: marcador.py lee resultados.json tal cual (sin volver a decidir, incluye compuertas de I3.1); tokens solo de origen modelo, sumados todos; el 59 % se calcula, no se escribe a mano.
Prueba de cierre: python -m ml.validat3b.marcador ... con salidas-sp4.zip → costo 99 · aprobadas 10 · falsas 0 · precisión 100.00 % · tokens por captura 1,921 (171,396 entrada + 20,684 salida, 100 capturas modelo).
No hecho / simulado: horas ahorradas SIN DATO (falta segundos de analista de 3B; se pasa con --segundos-analista); la proyección de 7,080/semana asume el 59 % en producción (PROYECCIÓN, no medida).
Archivos fuera de mi área: ninguno.
¿Tocó la base?: no.
Necesito de otra área: de 3B, segundos por captura de un analista; de Fer, confirmar el 59 % con el set ciego.
Cuelga de: main
