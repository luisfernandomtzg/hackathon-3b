# CLAUDE.md — Hackathon Tiendas 3B (21-nov-2026)

Eres **implementador** en un hackathon de un día. Se presenta a las **17:00** lo que esté desplegado en `main`. Una demo que corre vale más que tres funciones a medias.

## Disparador

La orden es **«ejecuta el siguiente prompt de `<carril>`»** (`ui`, `nucleo`, `datos` o `integrador`), a veces con el sello: «…, sello `HH:MM`». Si no dice el carril, **pregunta cuál** antes de abrir nada: en la máquina de Fer corren misiones de varios carriles.

## Antes de cada misión — en este orden, sin saltarte ninguno

1. `git fetch` y `git pull --rebase origin main`. Si falla por cambios locales, no los descartes ni los barras a tu commit: muéstralos y pregunta.
2. **Si existe `remoto-hackathon-3b.ps1` en la raíz** (máquina de Fer), corre
   `powershell -NoProfile -ExecutionPolicy Bypass -File .\remoto-hackathon-3b.ps1 -Estado -Carril <carril>`
   y pega su salida tal cual. Calcula el sello, el `siguiente`, el reporte más nuevo del carril y la regla de paro. Si dice **PARO**, te detienes.
3. Abre `docs/prompts-<carril>.md` y **relee el `ESTADO` aunque lo hayas leído antes**: se reescribe entre misión y misión. Ejecuta **solo** la misión que nombra `siguiente` — no el número más bajo sin tachar. Si `siguiente` es `NINGUNO…`, acúsalo y detente.
4. **Regla de paro — te detienes si se cumple CUALQUIERA:**
   - **Pierna 1:** tu entrega anterior en ESTA sesión es posterior al sello del `ESTADO`.
   - **Pierna 2:** el reporte más nuevo de tu carril en `docs/reportes/` es posterior al sello.
   - **Contenido:** la misión `siguiente` ya tiene reporte.
   - **Sello dado:** te dieron sello en la orden y no coincide con el del `ESTADO`.

   Al detenerte, enumera la evidencia y di: **«Para salir: el arquitecto reescribe el `ESTADO` (sube el sello) y reenvía la orden.»**
5. Devuelve este acuse antes de tocar nada:

```
Carril: <carril> · ESTADO leído: <sello tal cual> · siguiente: <id> · reescrituras: <n>
Voy a ejecutar: <id> — <título> · tope: <min> · clasificación: <autónomo | requiere compuerta | requiere pantalla>
Modelo en uso: <el de tu sesión> · pedido <X> → <coincide | NO coincide>
Esfuerzo: pedido <nivel> · en uso <el de tu sesión | no visible para mí>
Rama: <nombre> · cuelga de <SHA corto> (lo que dice la misión: <SHA esperado>)
```

Si el modelo no coincide y la misión lo marca `obligatorio`, te detienes. Si la punta de `main` no es el SHA que la misión espera, lista los commits nuevos y sus archivos; si tocan lo que vas a tocar, te detienes.

## Reglas

- **Tu carril, tus carpetas.** UI (Fer diseña y lleva las pantallas del camino dorado; Mau, apoyo): `app/`, `components/`. El tema (`app/globals.css`) y la dirección visual son de Fer. Núcleo (Mauski): `lib/dominio/`. Datos e IA (Sergio): `supabase/`, `datos/`, `lib/datos/`, `lib/ia/`, `ml/`. Integrador (Fer): `lib/contrato/`, merges a `main`. Si necesitas algo de otro carril, **para y pídelo**; no lo edites.
- **`lib/contrato/` solo lo edita el integrador.** Si el contrato no te alcanza, para y dilo.
- **Datos solo desde servidor.** Ningún componente de cliente importa el cliente de Supabase ni llama a un modelo. `lib/dominio` no importa nada de Next ni de Supabase.
- **Sin login, sin funciones fuera de la misión, sin refactor de paso.** Lo que no está en el camino dorado no existe hoy.
- **Verifica antes de arreglar y antes de aplicar:** si lo que se pide ya está hecho, dilo y no lo toques. Si crees que la misión está mal planteada, dilo antes de programar.
- **Si la misión es un arreglo (`<id>.1`) y al leer el código concluyes que el hallazgo es falso, dilo y no toques nada.**
- **Dependencias:** solo las que la misión nombra. Si necesitas otra, comprueba que el paquete existe, di para qué y agrégala con su archivo de bloqueo en el mismo commit.
- **Secretos:** jamás en el repo. Solo `.env.local` (ignorado) y variables de Vercel. `.env.example` lleva nombres sin valores.
- **Datos que entregue 3B:** confidenciales. Van en `datos/privado/` (ignorado por git) y a la base; nunca al repo.
- **Esquema de la base:** solo el carril Datos e IA lo cambia, y cada cambio es un archivo en `supabase/migrations/`. Correr algo que escribe en la base no es «solo lectura»: dilo en el reporte.
- **Tiempo tope:** cada misión lo trae. Si vas al 150 % sin cerrar, para y reporta lo que hay.
- **Un solo agente por carpeta del repo.** Si en tu máquina ya hay otra sesión de Claude Code sobre este mismo árbol, no abras otra: dilo.
- Confirmación obligatoria antes de cualquier cosa destructiva: borrar datos, `--force`, reescribir historia.

## Asistentes

Cada quien usa el asistente que prefiera (Claude Code, Cursor, Copilot, Codex, Gemini…). Si tu asistente no lee este archivo solo, pégale `CLAUDE.md` y tu misión al empezar. Si se te acaba la cuota a media misión: haz push de lo que haya en tu rama, avisa a Fer y él la termina con su Claude Code.

## Al terminar

1. Corre la **prueba de cierre** de la misión y pega su salida real.
2. Commit en la rama que diga la misión (`carril/<carril>-<tema>`) y `git push`. No hagas merge a `main`: integra el orquestador.
3. Escribe `docs/reportes/<id>-<tema>.md` **al final y de una sola vez** (un reporte a medias suelta la regla de paro antes de tiempo). Máximo 12 líneas. Commitéalo en tu misma rama.
4. En `docs/reportes/` **solo** escriben las entregas de los implementadores: nada más va ahí.

```
<id> — <título> · rama <nombre> · cuelga de <SHA padre> · commit <sha corto> · modelo <X> · esfuerzo <nivel> · <min> min
Hecho: <qué quedó funcionando, en una línea por cosa>
Prueba de cierre: <comando o URL> → <salida real>
No hecho / simulado: <lo que quedó con datos falsos o a medias — sin esto el reporte no vale>
Archivos fuera de mi carril que toqué: <ninguno | cuáles y por qué>
¿Tocó la base?: <no | qué tablas y cuántas filas>
Necesito de otro carril: <nada | qué>
```

## Dónde está el contexto

`docs/contexto-vigente-hackathon-3b.md` — el reto, el camino dorado, la URL de la demo y las decisiones. Si algo de aquí lo contradice, manda ese archivo.
