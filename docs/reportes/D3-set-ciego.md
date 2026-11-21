# D3 · Corrida del motor sobre el set ciego (en set ciego, sin etiquetas)

- **Hecho:** corrí `correr.py` con el modelo sobre las 50 capturas del set ciego, sin `--verificar` ni `--desde-extracciones`, con caché dentro de `salidas/ciego/`.
- **Resultado de la corrida (no es precisión):** 50 válidas de 50, 0 errores, 0 con confianza 0. Decisiones: 2 aprobadas, 20 rechazadas, 28 revision_manual.
- **Costo medido en esta corrida:** 95,658 tokens, 1,913 por captura, 19.2 s en total. Origen `modelo` en las 50.
- **Prueba de cierre (salida real):** `entradas: 50 · ids únicos: 50`, `errores: 0`, `confianza 0: 0`, `válidas: 50 de 50`.
- **No hecho / no medido:** precisión, falsas y % sin persona del set ciego (faltan etiquetas; las calcula Fer). Costo en pesos: NO MEDIDO.
- **Observación:** solo 2 aprobadas frente a 10 de 100 en desarrollo. No se interpreta sin etiquetas.
- **Criterio de tokens:** 1,913 es tokens por captura de esta corrida. El 2,390 de desarrollo suma las lecturas de consenso. No comparar directamente hasta confirmar el criterio con Luis.
- **Incidente:** una primera corrida sin `FOUNDRY_API_KEY` produjo 2 errores (revision_manual, confianza 0). Se descartó y se repitió con la clave solo en la sesión. La clave no está en ningún archivo.
- **Archivos fuera de mi área:** ninguno modificado. `salidas/ciego/` y `datos/privado/ciego/` quedan fuera de git (`datos/privado/` en `.gitignore`, línea 16).
- **Necesito de otra área:** Fer, etiquetas del set ciego para precisión y falsas. Luis, confirmar el criterio de tokens (1,913 vs 2,390) y el formato del archivo de envío.
- **Cuelga de:** PR #18 (`carril/datos-sp3-marcador`).
