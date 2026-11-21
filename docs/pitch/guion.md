# Guion del Pitch (3:00 min) — Validat3B · Tiendas 3B

> **Duración objetivo:** 2:45 – 3:00 (~420 palabras habladas a ~145 palabras/minuto).
> **Roles en escenario:** Alan narra · Mau opera `pitch.html` · Sergio respalda números y preguntas del jurado.

---

### [0:00–0:25] 1. El problema, en palabras de 3B (~60 palabras)

En Tiendas 3B, ochocientos capturistas recorren tiendas de la competencia tomando fotos de productos y etiquetas con prisa. Cada semana llegan doce mil capturas que hoy se revisan una por una, a mano. Como nos dijo Alfredo hoy: un peso de diferencia multiplicado por millones de ventas son millones de pesos, y prefieren validar con error casi cero antes que aprobar un precio equivocado.

---

### [0:25–1:40] 2. Demo en vivo sobre `pitch.html` (~165 palabras)

*(Mau muestra las tres tarjetas seleccionadas en `pitch.html`)*

Construimos **Validat3B** bajo un principio estricto: **el modelo lee, las reglas deciden, y todo queda explicado**. Y en los datos de hoy encontramos algo: cuando el analista dice «captura lejana» o «borrosa» no habla del producto, habla del letrero de precio. El motor mide justo eso.

Veamos tres capturas reales del lote de hoy:

1. **Aprobada (`CAP-434912`, Detergente Precissimo ochocientos gramos):** el modelo lee a ciegas marca, descripción, contenido neto y precio, y qué tan cerca y nítido sale el letrero; solo aprueba si tres lecturas independientes coinciden. Todo coincide y se aprueba con cero puntos de costo.
2. **Rechazada (`CAP-489454`, Leche entera Valley Foods en Soriana):** la foto del producto es impecable, pero el letrero de precio ocupa apenas doce por ciento de la foto. Las reglas la rechazan como `CAPTURA_LEJANA` y dicen por qué.
3. **Revisión manual (`CAP-350077`, Arroz SOS mil gramos en Walmart):** ante discrepancia parcial, varios precios o nitidez baja, nuestra compuerta local bloquea la aprobación. Aprobar una inválida cuesta diez puntos y descalifica debajo de noventa y siete por ciento; revisar cuesta uno. Ante la duda, nunca aprobamos.

---

### [1:40–2:20] 3. El marcador (~105 palabras)

*(Mau cambia a la vista del marcador)*

En las cien capturas de desarrollo, nuestro motor logró **cien por ciento de precisión en aprobadas en las 100 capturas de desarrollo** —dieciséis aprobadas, cero falsas, superando el noventa y siete por ciento obligatorio— y **cien por ciento de JSON válido**. El costo operativo quedó en **ochenta y cinco puntos** en el escenario pesimista y **veintiocho** en el optimista, frente a cien y sesenta y siete de mandar todo a revisión manual, resolviendo **cincuenta y cuatro de cien capturas** sin persona —proyectado a **seis mil cuatrocientas ochenta por semana**— con **unos tres mil cien tokens por captura** *(contra Rival 3B: `[[puntaje_rival_3b]]` · corte 14:30: `[[marcador_final_1430]]`)*.

---

### [2:20–2:45] 4. Por qué encaja en hard discount (~50 palabras)

Esta arquitectura encaja en hard discount: hace **una llamada por captura, y dos más solo para las que se van a aprobar**, a `claude-haiku-5-5`, y lo demás —señales locales de nitidez, lectura local de código de barras y doce reglas puras— corre en una laptop. Cero hardware nuevo y las mismas reglas en todas las regiones.

---

### [2:45–3:00] 5. Qué no hace todavía y siguiente paso (~40 palabras)

Hoy el motor corre por lotes y aún no alerta en celular ni mide tiempos de analista humano. El siguiente paso es llevar el filtro local a la app para avisar «foto borrosa, repítela» al capturar, y arrancar un piloto de cuatro semanas en una región.
