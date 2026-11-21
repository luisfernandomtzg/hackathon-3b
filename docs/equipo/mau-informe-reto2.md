# Informe de Análisis · Reto 2 (Validat3B)

**Autor:** Mau  
**Fecha:** 21 de noviembre de 2026  
**Estado:** Datos descargados, descomprimidos y mergeados en `main` (`datos/`).

---

## 1. Qué ya tenemos en el repositorio (`main`)

En la carpeta `datos/` ya se encuentran los archivos oficiales de desarrollo del **Reto 2 · Validat3B** (descargados de `https://hackaton3b.com/validat3b.html`):

- `datos/Validat3B_desarrollo_imagenes.zip` (~97.4 MB)
- `datos/Validat3B_desarrollo_metadatos.zip` (~38.8 KB)
- `datos/imagenes/` — **300 imágenes** (`*_facade.jpg`, `*_product.jpg`, `*_shelf.jpg`).
- `datos/metadatos/`:
  - `LEEME.md`
  - `capturas.csv`
  - `capturas.json`
  - `catalogo_productos.csv`

---

## 2. Endpoint oficial de IA (Azure AI Foundry)

De la sección `#foundry` de `validat3b.html`:

- **Endpoint:** `https://softwaredevelopment-resource.services.ai.azure.com/anthropic`
- **Modelo:** `claude-haiku-5-5`
- **SDK:** `pip install anthropic` (`AnthropicFoundry`)
- **Seguridad:** Guardar la API key en la variable de entorno `FOUNDRY_API_KEY` (nunca hardcodearla ni subirla al repo).

```python
import os
from anthropic import AnthropicFoundry

client = AnthropicFoundry(
    api_key=os.environ["FOUNDRY_API_KEY"],
    base_url="https://softwaredevelopment-resource.services.ai.azure.com/anthropic",
)
```

---

## 3. Reglas clave y métrica del reto

- **Requisitos mínimos eliminatorios:**
  - Precisión de aprobaciones **≥ 97%** (`TP / (TP + FP) ≥ 0.97`).
  - JSON válido en **≥ 99%** de las capturas.
  - Entrega puntual sin prórrogas.
- **Matriz oficial de costo operativo (50% de la calificación):**
  - Aprobada o rechazada correctamente: **0 pts**
  - Enviada a `revision_manual`: **1 pt** (seguro barato para casos dudosos)
  - Rechazada siendo válida (Falso Negativo): **3 pts**
  - Aprobada siendo inválida (Falso Positivo): **10 pts** (crítico: 10x revisión manual)
- **Otros criterios:** Pitch (25%), Calidad del dato (`reason_code`, precio y tipo de precio: 15%), Eficiencia de tokens (10% + desempate).

---

## 4. Arquitectura propuesta (Cascada en 4 capas)

1. **Capa 0 — Reglas y catálogo (0 tokens):** Validar presencia de las 3 fotos, consistencia de metadatos (`cadena`, `tienda`, `codigo_barras`) y cruce contra `catalogo_productos.csv` para obtener el producto esperado y sus contratipos permitidos.
2. **Capa 1 — Visión local con OpenCV + Resize (0 tokens):** Detectar blur (Laplaciano), foto a pantalla de celular o capturas muy lejanas, y redimensionar imágenes antes de enviarlas a `claude-haiku-5-5` para ahorrar tokens.
3. **Capa 2 — Inferencia multimodal (`claude-haiku-5-5`):** Una sola llamada por `capture_id` con contexto mínimo y salida JSON estricta validada con **Pydantic** (fallback seguro a `revision_manual` si falla).
4. **Capa 3 — Calibración de umbrales:** Ajustar umbrales sobre validación para minimizar el costo total manteniendo precisión de aprobaciones ≥ 97.5%.

---

## 5. Pendientes por confirmar con Managers / Organizadores

1. Ubicación del **kit de inicio**, **lista oficial de `reason_code`** y **script oficial de costo operativo** (en `validat3b.html` solo estaban los dos `.zip` de desarrollo).
2. Límites exactos de **TPM/RPM** del endpoint compartido.
3. Formato y ventana de tiempo para ejecutar el **set ciego** al cierre.
4. Criterio fino entre `oferta` vs `por_volumen` y qué tan estricta es la validación de fachada.
