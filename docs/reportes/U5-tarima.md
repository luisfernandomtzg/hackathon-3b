# Reporte U5 — Pantalla del pitch y encabezado del visor con Tarima

- **Carril:** ui (`carril/ui-sp3-tarima`)
- **Dueño:** Mau
- **Hecho:** Aplicados los tokens de `DESIGN.md` (Tarima) a `ml/validat3b/visor.py` (visor normal + `pitch.html`), sin CDN ni Google Fonts, sin logo de 3B, con lámina 0 de marcador calculado dinámicamente desde `resultados.json` y `tokens.csv` (`origen == "modelo"`), láminas 1–3 con las 3 fotos en fila, chip de decisión, `reason_code`, `explicacion`, tabla de 4 filas Esperado vs. Leído y tecla `F` para pantalla completa.
- **Prueba de cierre:** `python -m ml.validat3b.visor --datos datos/privado --resultados salidas/resultados.json --salida salidas/visor.html --pitch CAP-434912,CAP-748989,CAP-350077` → `100 tarjetas, costo total=99` y `Pitch generado en salidas\pitch.html (3 capturas)` (`100 %`, `99 vs 100`, `1,921`).
- **No hecho / simulado:** Nada simulado; resta captura visual en proyector 1920×1080.
- **Archivos fuera de carril:** Ninguno (`git status --short` sin `datos/` ni `salidas/`).
- **Qué necesito de otro:** De Fer, merge del PR de U5.
