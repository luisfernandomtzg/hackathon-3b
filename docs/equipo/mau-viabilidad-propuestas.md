# Análisis de Viabilidad y Diagnóstico Técnico — Validat3B (Para Luis / Fer)

**Autor:** Mau (Carril UI)  
**Fecha:** 21 de noviembre de 2026  

---

## 1. Diagnóstico del Motor Actual (¿Está funcionando bien o solo memorizó?)

1. **No está memorizando datos (sin overfitting):**  
   `claude-haiku-5-5` corre en *zero-shot* sobre las 3 imágenes leyendo campos (`marca`, `descripcion`, `contenido`, `precio`, `nitidez`), y `decidir.py` aplica reglas deterministas puras que nunca vieron las etiquetas `decision_esperada`. Además, las pruebas recientes usan **consenso de 3 lecturas (`I6`)**, lo cual reduce varianza sin entrenar pesos sobre el dataset de desarrollo.

2. **Por qué es matemáticamente obligatorio tener 0 aprobadas falsas (`FP = 0`):**  
   - En el set de desarrollo solo existen **33 capturas `aprobada` reales**.  
   - Si el motor comete **1 solo Falso Positivo (`FP = 1`)**, incluso aprobando absolutamente todas las 33 válidas (`33 / 34 = 97.06 %`) queda al borde de ser descalificado; si aprueba 15 y falla 1 (`15 / 16 = 93.75 %`), **queda descalificado automáticamente (`< 97 %`)**.  
   - Además, en la matriz oficial, **1 FP cuesta 10 puntos**, mientras que mandar a `revision_manual` cuesta **1 punto**.

3. **Dónde está la mayor oportunidad de mejora antes del cierre:**  
   - De las **33 `aprobada` reales**, en `sp4` aprobamos **10** (`10/10 = 100 %`) y mandamos **21 a `revision_manual`**.  
   - Cada `aprobada` válida rescatada con certeza baja **1 pt** el costo pesimista sin sacrificar el `100 %` de precisión.

---

## 2. Evaluación de Viabilidad: Módulos de Inteligencia Competitiva y Campo (Módulos 5, 6 y 7)

| Propuesta / Módulo | Qué datos reales ya tenemos hoy | Qué falta / supuesto | Viabilidad hoy (antes de 17:00) | Impacto para Jurado (Pitch 25 %) |
| :--- | :--- | :--- | :---: | :--- |
| **Módulo 6: Comparador Multi-Tienda (`% vs. Ref 3B`)** | `id_product`, `product_name`, `product_price` (ref), `capture_price`, `precio_detectado`, `capture_store_name` (6 cadenas), fotos de evidencia | Ninguno: **100 % datos reales del CSV oficial** | **Alta (Implementable ya en UI sin tocar backend)** | **Muy alto:** demuestra valor comercial directo para *PriceCheck* |
| **Módulo 7: Monitor de Calidad en Campo por Visita** | `facade_url` (agrupa sucursal/visita física), `capture_store_name`, `reason_code`, `costo (0/1/3/10)` | Ninguno: **100 % datos reales del CSV oficial** | **Alta (Implementable ya en UI sin tocar backend)** | **Muy alto:** explica cómo reducir capturas borrosas/lejanas de raíz |
| **Módulo 5: Radar Geoespacial + «Misiones en Campo» (estilo Pokémon GO)** | `facade_url` + `capture_store_name` (para agrupar sucursales) | **Medido:** las 300 fotos tienen **0 datos EXIF/GPS**. Se requiere `navigator.geolocation` en vivo + coordenadas demo marcadas como `SUPUESTO` | **Media-Alta (como demo en vivo + Siguiente Paso)** | **Diferenciador clave:** conecta el motor por lotes de hoy con la app de ~800 capturistas en campo |

---

## 3. Recomendación para Decisión de Luis (Fer)

1. **En el motor (`ml/validat3b/`):** mantener la prioridad absoluta en `precisión ≥ 97 %` (`0 FP`) y seguir rescatando de `revision_manual` las válidas claras sin tocar el flujo de entrega ciega (`entregar.py`).
2. **En Frontend / Demo (UI):**
   - Ya quedaron implementados los **Módulos 1–4** (Resumen Ejecutivo, Cola HITL con rotación/zoom/atajos `A`/`R`/`S`, Explorador Tabla 52px + Export CSV + Modal JSON, e Ingesta client-side de Set Ciego por Carpeta/CSV/JSON).
   - **Propuesta inmediata sin riesgo:** si lo autorizas, agregamos en la misma consola de UI los **Módulos 6 y 7** con los **datos reales de `capturas.csv`** (sin inventar cifras y sin tocar ningún archivo de backend) y dejamos el **Módulo 5 (Misiones GPS en campo)** como demo interactiva claramente etiquetada como `SUPUESTO` + `navigator.geolocation`.
