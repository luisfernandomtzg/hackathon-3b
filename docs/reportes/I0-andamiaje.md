# Reporte I0 — Andamiaje y tubería

`carril: integrador · hecho en S000 por Claude (contenedor de la sesión), 2026-11-17 · rama: main`

**Hecho**
- Next.js 16.4.6 (App Router, TS, Tailwind 4, ESLint 9) generado con `create-next-app` y fusionado sin pisar `CLAUDE.md`, `README.md`, `docs/`, `.gitignore`, `.env.example`. A `AGENTS.md` se le agregó el bloque que Next reescribe al correr `next dev`, para que no ensucie el árbol.
- Carpetas de carril con su README: `components/` · `lib/contrato/` · `lib/dominio/` · `lib/datos/` · `lib/ia/` · `supabase/migrations/` · `datos/semilla/` · `ml/` (`datos/privado/` ignorada).
- `lib/datos/servidor.ts`: cliente de Supabase solo servidor (`server-only`) + `revisarBase()`.
- `/salud`: SHA corto (`VERCEL_GIT_COMMIT_SHA`, «local» si no hay), rama, hora CDMX y estado de la base.
- Fuente Geist desde el paquete `geist` (local): no depende de Google Fonts, funciona sin internet.
- ESLint `no-restricted-imports` por carril (`eslint.config.mjs`).

**Medido** `[MEDIDO en el contenedor de S000, 2026-11-17 ~13:50]`
- `npm run lint` → 0 problemas. `npm run build` → OK; `/` estática, `/salud` prerender parcial.
- Rojo demostrado: `components/violacion.tsx` importando `@supabase/supabase-js` y `lib/dominio/violacion.ts` importando `next/navigation` → 2 errores `no-restricted-imports`. Se borraron; lint en verde otra vez.
- `next start` → `/` 200; `/salud` muestra `commit local` y `faltan NEXT_PUBLIC_SUPABASE_URL o SUPABASE_SECRET_KEY`.

**No hecho / simulado** → pasa a **I0.1**
- shadcn/ui: su registro no se alcanza desde el contenedor. Se instala en la máquina de Fer.
- Supabase y Vercel sin conectar: `/salud` aún no ha dicho `ok` contra una base real ni se ha visto la URL pública.
- `npm audit` reporta avisos de dependencias de create-next-app; no se tocaron.
