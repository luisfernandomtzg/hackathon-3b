# Validat3B en campo — versión alternativa (rama `alt/campo-app`)

> **Estado: experimento.** No está en `main` ni forma parte de la entrega. El equipo decide si se muestra.
> Probado con pruebas automáticas y con el servidor en modo sin modelo. **No probado todavía** con el endpoint real ni desde un celular: en la laptop de Fer el celular no logró conectarse (ver «Problema abierto»).

## Qué es

Un servidor local que corre en la laptop del supervisor y sirve dos pantallas:

| Pantalla | Dirección | Quién |
|---|---|---|
| App del capturista | `https://<IP de la laptop>:8443/` | Celular, en la misma red |
| Panel del supervisor | `https://localhost:8443/supervisor` | Solo desde la propia laptop |

Flujo del capturista: código de vinculación de 6 dígitos → ubicación → foto de fachada (una vez) → producto por producto (foto del producto, foto del letrero, precio) → respuesta del motor en la tienda. Si el letrero salió lejos, la app le dice «acerca el letrero» y lo deja repetir hasta 3 veces; después va a revisión. Cada producto se puede omitir con motivo.

Panel del supervisor: alta de capturistas (nombre, cadena, cuántos productos del catálogo), avance y ubicación de cada uno, precios validados contra la referencia de 3B con exportación a CSV, motivos por los que no se validó cada foto y las últimas capturas con sus fotos.

Cada captura pasa por **el mismo motor del lote** (`correr.procesar`: lectura v3, reglas, compuertas y consenso). No hay base de datos ni servicios externos: el estado vive en `estado.json` y las fotos en disco, dentro de `--salida`.

## Archivos

- `ml/validat3b/campo.py` — servidor, estado, las dos páginas (HTML y JS dentro del mismo archivo).
- `ml/validat3b/test_campo.py` — 7 pruebas; no usan datos de 3B ni el endpoint.

No modifica ningún archivo existente del motor.

## Cómo correrlo

Desde la carpeta del repo en esta rama, con el entorno de Python del proyecto:

```
python -m pip install cryptography
python -m unittest ml.validat3b.test_campo
python -m ml.validat3b.campo --catalogo datos/privado/metadatos/catalogo_productos.csv --salida salidas/campo
```

Opciones:

- `--sin-modelo` — no llama al endpoint; todo sale a revisión. **Úsalo para probar el flujo sin gastar tokens.**
- `--env <ruta>` — dónde está `.env.local` con `FOUNDRY_API_KEY` (por omisión busca `./.env.local` y `../repo/.env.local`).
- `--puerto 8443` — puerto.
- `--http` — sin https (el celular no entregará ubicación).

Al arrancar imprime las dos direcciones. Necesita el catálogo del reto (`catalogo_productos.csv`), que **no está en el repo** porque es dato de 3B.

## Para que el celular se conecte

1. Laptop y celular en la **misma red**. El wifi de un evento suele aislar equipos: usar el hotspot de un teléfono.
2. Firewall de Windows: permitir el puerto 8443 de entrada.
3. Escribir la dirección completa, con `https://` y `:8443`.
4. El celular muestra un aviso de certificado la primera vez (es un certificado local propio): «Avanzado» → «Continuar».

## Problema abierto

En la prueba de las 14:30 el celular mostró «no se puede conectar al servidor» aun con la regla de firewall creada. Sin diagnosticar: no se confirmó qué IP tomó el servidor ni si ambos equipos estaban en la misma red. Lo primero a revisar es el punto 1 de arriba (hotspot) y, desde otra terminal de la laptop, `curl -k https://<IP>:8443/`.

## Límites conocidos

- Cada captura real gasta tokens: una lectura si se rechaza, tres si se aprueba.
- El panel del supervisor no tiene contraseña; se protege aceptando solo peticiones desde la propia laptop.
- La ubicación se guarda como coordenadas; no hay mapa.
- Los productos se asignan al azar del catálogo (con filtro opcional por texto), no por sucursal.
- Las fotos de campo quedan en `salidas/campo/fotos/`, que no se versiona.
