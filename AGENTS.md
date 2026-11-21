# AGENTS.md

**Regla 0 (sábado 21-nov):** antes de cualquier cosa, `git fetch origin` y `git pull --rebase origin main`. Hoy el producto es Python en `ml/validat3b/` (Reto 2 · Validat3B); tu misión está en `docs/prompts-<carril>.md`. Nunca `git add datos/` ni `salidas/`.

Las reglas de este repo para cualquier asistente de código están en [`CLAUDE.md`](./CLAUDE.md). Léelo completo antes de trabajar: carriles por carpeta, documento de misiones por carril en `docs/`, y formato del reporte de entrega. Si eres el asistente de un compañero del equipo, lee además `docs/KIT-EQUIPO.md` (o su `docs/paquetes/<nombre>.md` el sábado). Antes de tocar cualquier pantalla, lee [`DESIGN.md`](./DESIGN.md): es el sistema de diseño obligatorio.

<!-- BEGIN:nextjs-agent-rules -->

## This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->
