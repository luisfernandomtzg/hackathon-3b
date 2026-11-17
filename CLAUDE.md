# CLAUDE.md — Hackathon Tiendas 3B (21-nov-2026)

Eres **implementador** en un hackathon de un día. Se presenta a las **17:00** lo que esté desplegado en `main`. Una demo que corre vale más que tres funciones a medias.

## Antes de cada misión

1. `git pull --rebase origin main`.
2. Abre el documento de **tu carril**: `docs/prompts-ui.md`, `docs/prompts-nucleo.md`, `docs/prompts-datos.md` o `docs/prompts-integrador.md`. Ejecuta **solo** la misión que su bloque `ESTADO` nombra como `siguiente` — no el número más bajo sin tachar.
3. **Regla de paro:** si la misión `siguiente` ya tiene reporte en `docs/reportes/`, el documento está viejo. No ejecutes nada: dilo y pide que lo actualicen.
4. Devuelve este acuse antes de tocar nada:

```
Carril: <ui|nucleo|datos|integrador> · ESTADO leído: <hora del sello> · siguiente: <id>
Voy a ejecutar: <id> — <título> · tope: <min>
```

## Reglas

- **Tu carril, tus carpetas.** UI (Fer diseña y lleva las pantallas del camino dorado; Mau, apoyo): `app/`, `components/`. El tema (`app/globals.css`) y la dirección visual son de Fer. Núcleo (Mauski): `lib/dominio/`. Datos e IA (Sergio): `supabase/`, `datos/`, `lib/datos/`, `lib/ia/`, `ml/`. Integrador (Fer): `lib/contrato/`, merges a `main`. Si necesitas algo de otro carril, **para y pídelo**; no lo edites.
- **`lib/contrato/` solo lo edita el integrador.** Si el contrato no te alcanza, para y dilo.
- **Datos solo desde servidor.** Ningún componente de cliente importa el cliente de Supabase ni llama a un modelo. `lib/dominio` no importa nada de Next ni de Supabase.
- **Sin login, sin funciones fuera de la misión, sin refactor de paso.** Lo que no está en el camino dorado no existe hoy.
- **Verifica antes de arreglar y antes de aplicar:** si lo que se pide ya está hecho, dilo y no lo toques. Si crees que la misión está mal planteada, dilo antes de programar.
- **Dependencias:** solo las que la misión nombra. Si necesitas otra, comprueba que el paquete existe, di para qué y agrégala con su archivo de bloqueo en el mismo commit.
- **Secretos:** jamás en el repo. Solo `.env.local` (ignorado) y variables de Vercel. `.env.example` lleva nombres sin valores.
- **Datos que entregue 3B:** confidenciales. Van en `datos/privado/` (ignorado por git) y a la base; nunca al repo.
- **Esquema de la base:** solo el carril Datos e IA lo cambia, y cada cambio es un archivo en `supabase/migrations/`.
- **Tiempo tope:** cada misión lo trae. Si vas al 150 % sin cerrar, para y reporta lo que hay.
- Confirmación obligatoria antes de cualquier cosa destructiva: borrar datos, `--force`, reescribir historia.

## Asistentes

Cada quien usa el asistente que prefiera (Claude Code, Cursor, Copilot, Codex, Gemini…). Si tu asistente no lee este archivo solo, pégale `CLAUDE.md` y tu misión al empezar. Si se te acaba la cuota a media misión: haz push de lo que haya en tu rama, avisa a Fer y él la termina con su Claude Code.

## Al terminar

1. Corre la **prueba de cierre** de la misión y pega su salida real.
2. Commit en tu rama `carril/<carril>-<tema>` y `git push`. No hagas merge a `main`: integra el orquestador.
3. Escribe `docs/reportes/<id>-<tema>.md` (máximo 12 líneas, al final, de una sola vez):

```
<id> — <título> · rama <nombre> · commit <sha corto> · modelo <X> · <min> min
Hecho: <qué quedó funcionando, en una línea por cosa>
Prueba de cierre: <comando o URL> → <salida real>
No hecho / simulado: <lo que quedó con datos falsos o a medias — sin esto el reporte no vale>
Archivos fuera de mi carril que toqué: <ninguno | cuáles y por qué>
Necesito de otro carril: <nada | qué>
```

## Dónde está el contexto

`docs/contexto-vigente-hackathon-3b.md` — el reto, el camino dorado, la URL de la demo y las decisiones. Si algo de aquí lo contradice, manda ese archivo.
