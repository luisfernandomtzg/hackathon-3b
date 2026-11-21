# Reporte U4 — Visor y pitch con datos reales (SP2)

- **Carril:** ui (`carril/ui-sp2-pitch-real`)
- **Dueño:** Mau
- **Hecho:** Descomprimido `salidas-sp2.zip` en `salidas/`, regenerado `salidas/visor.html` y `salidas/pitch.html`, y actualizadas las 6 candidatas (2 por categoría) en `docs/entrega/capturas-demo.md`.
- **Prueba de cierre:** `python -m ml.validat3b.visor --datos datos/privado --resultados salidas/resultados.json --salida salidas/visor.html --pitch CAP-763258,CAP-748989,CAP-350077` → `100 tarjetas, costo total=84`, `16 aprobadas, 14 correctas, 87.5% precisión`.
- **No hecho / simulado:** No se modificó `visor.py`; se esperan los datos finales de `salidas-sp3.zip` (~12:30) para las cifras definitivas del pitch.
- **Archivos fuera de carril:** Ninguno (`git status --short` sin `datos/` ni `salidas/`).
- **Qué necesito de otro:** De Alan, que tome el marcador actual (`84 pts`, `16 aprobadas`, `14 correctas`, `87.5%`) como referencia provisional; de Fer, `salidas-sp3.zip`.
