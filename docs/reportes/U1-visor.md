# Reporte U1 — Visor local de capturas

- **Carril:** ui (`carril/ui-sp1-visor`)
- **Dueño:** Mau
- **Archivo entregado:** `ml/validat3b/visor.py`

## Qué se construyó
- Generador de HTML estático autocontenido (`salidas/visor.html`, sin servidor, sin CDN, sin dependencias externas).
- Tarjeta por cada captura con las 3 fotos (`facade`, `product`, `shelf`) con ampliación en modal al hacer clic.
- Muestra producto esperado, datos leídos por el motor (`resultados.json` / `extracciones.json`), decisión esperada vs. decisión del motor, `reason_code`, explicación, confianza y costo (`0/1/3/10`).
- Filtros por decisión esperada, decisión del motor, «solo errores», orden por costo y contador de costo total.
- Funciona también sin `resultados.json` mostrando solo lo esperado.

## Prueba de cierre
```text
python -m ml.validat3b.visor --datos datos/privado --resultados salidas/resultados.json --salida salidas/visor.html
Visor generado en salidas/visor.html (100 tarjetas, costo total=0)
```
- `git status --short`: no muestra `datos/` ni `salidas/`.
