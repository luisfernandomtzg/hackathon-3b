# Guion del Pitch (3:00 min) — Validat3B · Tiendas 3B

> **Duración objetivo:** 2:45 – 3:00 (~420 palabras habladas a ~145 palabras/minuto).
> **Roles en escenario:** Alan narra · Mau opera `pitch.html` · Sergio respalda números y preguntas del jurado.

---

### [0:00–0:25] 1. El problema, en palabras de 3B (~60 palabras)

En Tiendas 3B, ochocientos capturistas recorren tiendas de la competencia tomando fotos de productos y etiquetas con prisa. Cada semana llegan doce mil capturas que hoy se revisan una por una, a mano. Como nos dijo Alfredo hoy: un peso de diferencia multiplicado por millones de ventas son millones de pesos, y prefieren validar con error casi cero antes que aprobar un precio equivocado.

---

### [0:25–1:40] 2. Demo en vivo sobre `pitch.html` (~165 palabras)

*(Mau muestra las tres tarjetas seleccionadas en `pitch.html`)*

Construimos **Validat3B** bajo un principio estricto: **el modelo lee, las reglas deciden, y todo queda explicado**.

Veamos tres capturas reales del lote de hoy:

1. **Aprobada (`CAP-434912`, Detergente Precissimo ochocientos gramos):** el modelo lee a ciegas marca, descripción, contenido neto y precio; verificamos en local nitidez y código de barras, y exigimos consenso unánime de tres lecturas antes de aprobar. Todo coincide y se aprueba con cero puntos de costo.
2. **Rechazada (`CAP-563575`, Chiles jalapeños La Costeña en Bara):** cuando el contenido o el frente no se alcanzan a leer por distancia o desenfoque, las reglas rechazan de inmediato como `CAPTURA_LEJANA` y citan la evidencia.
3. **Revisión manual (`CAP-350077`, Arroz SOS mil gramos en Walmart):** ante discrepancia parcial, varios precios o nitidez baja, nuestra compuerta local bloquea la aprobación. Aprobar una inválida cuesta diez puntos y descalifica debajo de noventa y siete por ciento; revisar cuesta uno. Ante la duda, nunca aprobamos.

En cada caso: **el modelo lee, las reglas deciden, y todo queda explicado**.

---

### [1:40–2:20] 3. El marcador (~105 palabras)

*(Mau cambia a la vista del marcador)*

En las cien capturas de desarrollo, todo se decidió por las fotos, porque los metadatos venían empatados en las cien. Nuestro motor logró **cien por ciento de precisión en aprobadas en las 100 capturas de desarrollo** —diez aprobadas, cero falsas, superando el noventa y siete por ciento obligatorio— y **cien por ciento de JSON válido**. El costo operativo quedó en **noventa y dos puntos** en el escenario pesimista y **treinta y cinco** en el optimista, frente a cien y sesenta y siete de mandar todo a revisión manual, **sin rechazar ninguna captura válida** y resolviendo **cuarenta y cuatro de cien capturas** sin persona —proyectado a **cinco mil doscientas ochenta por semana**— con **dos mil trescientos noventa tokens por captura** *(contra Rival 3B: `[[puntaje_rival_3b]]` · corte 14:30: `[[marcador_final_1430]]`)*.

---

### [2:20–2:45] 4. Por qué encaja en hard discount (~50 palabras)

Esta arquitectura encaja en hard discount: hace **una llamada por captura, y dos o tres solo para las que se aprueban**, a `claude-haiku-5-5`, y lo demás —señales locales de nitidez, lectura local de código de barras y doce reglas puras— corre en una laptop. Cero hardware nuevo y las mismas reglas en todas las regiones.

---

### [2:45–3:00] 5. Qué no hace todavía y siguiente paso (~40 palabras)

Hoy el motor corre por lotes y aún no alerta en celular ni mide tiempos de analista humano. El siguiente paso es llevar el filtro local a la app para avisar «foto borrosa, repítela» al capturar, y arrancar un piloto de cuatro semanas en una región.
