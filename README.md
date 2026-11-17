# Hackathon Tiendas 3B — 21-nov-2026

Equipo: Fer, Mau, Sergio, Mauski y Alan.

> **Estado al 17-nov-2026:** plantilla previa — andamiaje Next.js + Supabase + reglas de frontera entre carriles y la ruta `/salud`. Sin código de producto: el producto se construye el día del evento. Qué trae exactamente: `docs/reportes/I0-andamiaje.md`.

## Cómo se trabaja

- `main` siempre desplegable. Ramas cortas `carril/<carril>-<tema>`. Integra una sola persona.
- Cada programador lee `CLAUDE.md` y el documento de misiones de su carril en `docs/`.
- Los reportes de entrega van a `docs/reportes/`.

## Comandos

```bash
npm install          # dependencias
cp .env.example .env.local   # y llena los valores (pídeselos a Fer, nunca por el chat del grupo)
npm run dev          # http://localhost:3000 · salud en /salud
npm run lint         # incluye las fronteras entre carriles
npm run build
```

Control remoto (máquina de Fer): `powershell -ExecutionPolicy Bypass -File .\remoto-hackathon-3b.ps1` · estado de los carriles sin lanzar nada: `... -Estado` (o `-Estado -Carril ui`).
Sembrar datos y probar: se agregan cuando existan.

## Herramientas y librerías usadas

Next.js 16 · React 19 · Tailwind 4 · Supabase · Vercel · fuente Geist. Asistentes de IA usados para programar: Claude (Anthropic) y los que use cada integrante; se declaran en la entrega.
