# Misiones — carril INTEGRADOR

## ESTADO · 2026-11-17 13:55
Dueño del carril: **Fer** (Claude Code)
Cola: ~~I0~~ (hecha en S000, ver `reportes/I0-andamiaje.md`) → **I0.1** → (las siguientes se escriben en S001)
siguiente: **I0.1**
Última auditoría: I0 · medido en el contenedor de S000 (lint, build, rojo de fronteras, /salud local)
Nota: se decidió llevar plantilla previa (S000): el uso de IA está permitido y nada en las reglas lo prohíbe. Si a las 9:00 dicen lo contrario, se declara en el pitch qué traía el repo.

---

## I0.1 — shadcn, Supabase y Vercel conectados

`carril: integrador · rama: main · tope: 30 min · clasificación: requiere pantalla · modelo: general · esfuerzo: medium`
`cuándo: jueves o viernes; a más tardar el sábado 9:30`

**Hechos que no puedes ver.** I0 ya está en `main`: Next 16.4.6, ESLint con fronteras probadas en rojo, `/salud` funcionando en local `[MEDIDO S000]`. shadcn no se pudo instalar desde donde se generó. El repo es **público** (así Vercel Hobby despliega commits de todos); jamás entran secretos ni datos de 3B.

1. `npx shadcn@latest init` (base neutral, sin cambiar la carpeta de componentes) y `npx shadcn@latest add button card input table badge dialog select tabs skeleton sonner`. Confirma que no reescribió `app/globals.css` de forma que rompa el build.
2. `npm run lint` y `npm run build` en verde.
3. Fer crea el proyecto de Supabase `hackathon-3b` y copia URL y llave secreta a `.env.local` (no al repo). `npm run dev` → `/salud` dice `base ok`.
4. Fer importa el repo en Vercel, pone `NEXT_PUBLIC_SUPABASE_URL` y `SUPABASE_SECRET_KEY` en el proyecto y despliega. En el celular, `/salud` de la URL pública muestra el SHA de `main` y `base ok`.
5. Un compañero hace push de una rama `prueba/<nombre>` y se comprueba que Vercel genera su vista previa.
6. Anota URL, proyecto de Supabase y tiempo push→URL en `docs/contexto-vigente-hackathon-3b.md` (sección Recursos).

**Prueba de cierre:** captura de `/salud` pública con SHA y `base ok`, y el tiempo push→URL.
**Reporte:** `docs/reportes/I0.1-conexion.md`. **Commit:** `chore: shadcn y conexión a Supabase/Vercel (I0.1)`

---

## I0 — Andamiaje [HECHA en S000] y tubería de despliegue

`carril: integrador · rama: main (repo recién creado) · tope: 30 min · clasificación: requiere pantalla (verificar la URL)`
`modelo: general · esfuerzo: medium`

**Contexto.** Repo sin código de producto. Stack decidido: Next.js (App Router, TypeScript) + Tailwind + shadcn/ui, Supabase (Postgres), Vercel. Arquitectura en `docs/arquitectura-provisional.md` si está copiada; si no, lo esencial está aquí. Usa las versiones estables vigentes: consulta la documentación oficial en vez de asumir de memoria.

**Qué hacer**

1. Crea la app con `create-next-app` (TypeScript, App Router, Tailwind, ESLint, sin carpeta `src/`). El directorio ya tiene `CLAUDE.md`, `README.md`, `docs/` y otros: genera en una carpeta temporal y mueve el contenido a la raíz **sin pisar** los archivos existentes (fusiona `.gitignore`).
2. Inicializa shadcn/ui y agrega solo: button, card, input, table, badge, dialog, select, tabs, skeleton, sonner.
3. Crea la estructura vacía, con un `README.md` de una línea en cada carpeta que diga de qué carril es:
   `app/` · `components/` · `lib/contrato/` · `lib/dominio/` · `lib/datos/` · `lib/ia/` · `supabase/migrations/` · `datos/semilla/` · `datos/privado/` (ignorada) · `ml/`
4. `lib/datos/servidor.ts`: cliente de Supabase **solo de servidor** (`import "server-only"`), con `NEXT_PUBLIC_SUPABASE_URL` y `SUPABASE_SECRET_KEY`.
5. Ruta `/salud` (componente de servidor): muestra el SHA corto del commit desplegado (variable de sistema de Vercel; «local» si no existe), la hora del servidor y el resultado de una consulta trivial a la base (`ok` o el motivo del fallo, sin filtrar secretos).
6. Regla ESLint `no-restricted-imports`: `app/**` y `components/**` no importan `@supabase/*` ni `lib/ia`; `lib/dominio/**` no importa `next/*`, `@supabase/*` ni `app/`. **Demuestra que se pone roja:** mete una violación en cada grupo, corre el lint, pega la salida, quita la violación y vuelve a correr.
7. Página de inicio mínima con el nombre provisional del proyecto y una liga a `/salud`. Nada más.
8. Completa la sección «Comandos» del `README.md` con los que hayas ejecutado de verdad.

**Lo que NO se hace:** login, base de datos con tablas de negocio, componentes de producto, landing, pruebas de más. No se toca `CLAUDE.md`.

**Para y pregunta si:** `create-next-app` o shadcn piden una decisión que no está aquí; falta una variable de entorno; algo exige borrar un archivo existente.

**Prueba de cierre**

- `npm run lint` y `npm run build` en verde (pega la salida), más las dos corridas en rojo del punto 6.
- En local, `/salud` responde y dice `ok` para la base (o el motivo exacto si no hay variables).
- El orquestador conecta el repo a Vercel, pone las variables y verifica en un celular que `/salud` de la URL pública muestra el SHA de `main`.

**Reporte:** `docs/reportes/I0-andamiaje.md`, con el formato de `CLAUDE.md`. Incluye cuánto tardó de push a URL actualizada.

**Commit sugerido:** `chore: andamiaje Next + Supabase + reglas de frontera (I0)`

---

## Bitácora de reescrituras

- 2026-11-17 13:20 · creado en S000 con I0.
- 2026-11-17 13:55 · I0 hecha en S000 (plantilla previa); se agrega I0.1.
