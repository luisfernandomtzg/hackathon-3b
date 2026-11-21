# Capturas seleccionadas para el Pitch (U1 · tarea de espera)

Selección de 3 capturas representativas para demostrar el flujo de decisión en `salidas/pitch.html`:

1. **`CAP-645667` — Aprobada clara**
   - **Producto esperado:** Selecto Brand · Frijoles negros refritos · 400 g (Chedraui)
   - **Por qué en el pitch:** Demuestra el caso ideal donde marca, descripción, contenido y etiqueta de precio son legibles y consistentes, aprobándose automáticamente con costo `0 pts`.

2. **`CAP-305088` — Rechazada evidente**
   - **Producto esperado:** McCormick · Mostaza preparada · 220 g (Bara)
   - **Motivo:** `Capturas borrosas`
   - **Por qué en el pitch:** Demuestra cómo las señales locales sin tokens (nitidez) y la validación de evidencia frenan capturas ilegibles antes de contaminar el sistema de precios.

3. **`CAP-350077` — Revisión manual interesante**
   - **Producto esperado:** SOS · Arroz grano largo super extra · 1000 g (Walmart)
   - **Por qué en el pitch:** Ilustra la zona de duda: en lugar de arriesgar un falso positivo (`10 pts` y riesgo de descalificación por `< 97%` precisión), el motor escala a `revision_manual` (`1 pt`) protegiendo la calidad del dato.
