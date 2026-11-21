D3.1 — Marcador para el pitch (corrección de auditoría) · rama carril/datos-sp3-marcador · IA Claude (chat web, plan gratuito) · 20 min
Hecho: marcador.py lee resultados.json tal cual (sin volver a decidir, incluye compuertas); tokens solo de origen modelo, sumados todos; caché = 0 tokens; el % sin persona y la proyección se calculan, no se escriben a mano.
Cifras (salidas-sp6.zip, motor definitivo): todas son de las 100 capturas de DESARROLLO. Costo 104 (pesimista) / 39 (optimista) contra 100 / 67 de revisar a mano · 10 aprobadas, 0 falsas, 100 % · 50 de 100 sin persona · 2,390 tokens por captura · 4.3 s por captura.
Proyección: 6,000 capturas/semana de 12,000 (Alfredo, 3B); PROYECCIÓN, asume el 50 % de desarrollo en producción.
Set ciego: PENDIENTE (lo corre Fer entre 15:00 y 16:00); ninguna cifra de arriba es del set ciego.
Prueba de cierre: python -m ml.validat3b.marcador --resultados salidas/resultados.json --capturas datos/privado/metadatos/capturas.csv --tokens salidas/tokens.csv → costo 104 · aprobadas 10 · falsas 0 · precisión 100.00 % · tokens/captura 2,390.
No hecho / simulado: horas ahorradas SIN DATO (falta segundos de analista de 3B; se pasa con --segundos-analista); la proyección es PROYECCIÓN, no medida.
Archivos fuera de mi área: ninguno.
¿Tocó la base?: no.
Necesito de otra área: de 3B, segundos por captura de un analista; de Fer, el set ciego y confirmar el criterio de tokens (2,390 vs 2,175 que dijo Luis antes).
Cuelga de: main
