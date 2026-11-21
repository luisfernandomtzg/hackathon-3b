# Contexto vigente — Hackathon Tiendas 3B

> Una página. Se actualiza al cerrar **cada fase**. Fuente: copia del proyecto de claude.ai; espejos en `documentacion/` y en `repo/docs/`.
> Última actualización: **2026-11-18 18:30 · cierre de S001 (miércoles, adelantada: método de trabajo y sistema de diseño)** · siguiente **S001.5 (viernes 20-nov, corta: Supabase, U0 y ensayo)** · el sábado es **S002**.

## 🟢 Si estás abriendo la sesión siguiente, lee esto primero

- **Numeración:** S001 se adelantó al miércoles 18 (método); el viernes es **S001.5** (sesión corta, `PROMPT-APERTURA-S001.md`); el sábado arranca en **S002** (`PROMPT-APERTURA-S002.md`). Donde las instrucciones digan «S001» para el sábado, léase S002.
- Aún **no hay reto**: se conoce el sábado a las 9:00 y se elige por orden de llegada.
- El repo trae **plantilla previa** sin código de producto: I0 (Next + fronteras de carril + `/salud`) e I0.1 (shadcn, Supabase y Vercel) hechas y auditadas en S000. Los cuatro carriles están en `NINGUNO — BLOQUEADO` hasta que S002 (sábado) escriba sus misiones 1; el de UI se libera antes, en S001.5, para `U0`.
- Antes del sábado hay tareas de Fer y del equipo en `checklist-previo.md`. Lo que no esté palomeado ahí, se pregunta al abrir.
- Plan de horas en `plan-del-dia.md`. Arquitectura en `arquitectura-provisional.md`.

## Relevo para S001.5 (viernes)

Escrito al cerrar S001, 2026-11-18 17:10.
- **S001 se adelantó al miércoles** y solo trató el método. La agenda de `PROMPT-APERTURA-S001.md` (Supabase despierto, misión `U0`, puntos abiertos) **sigue pendiente completa**: es S001.5, y abre con `S001.5 3B. Lee el prompt inicial` → lee `PROMPT-APERTURA-S001.md` + este relevo.
- **Medido en S001:** `origin/main` = `5df6c6b`, desciende de `3506aa7` → cierre de S000 ✓ `[MEDIDO 17:01, git clone desde el chat]`. `git status` local no medido (sin shell). `/salud` no verificado (la lectura automática solo ve «Revisando…»: medir con navegador).
- **Hallazgo que sube de severidad:** `npm run build` **falla** sin acceso a Google Fonts (`next/font/google` en `app/layout.tsx`) `[MEDIDO 17:03 en el contenedor del chat; npm ci 12 s y lint en verde]`. Vercel compila porque tiene internet, pero el chat no puede auditar ejecutando y una sede sin internet rompe el build local. **`U0` es lo primero del viernes.**
- **Decisiones de S001 (Fer, 17:04):** ver «Método de trabajo del sábado» abajo.
- **Escrito en S001:** `repo/docs/KIT-EQUIPO.md` (kit universal, Parte A + ensayo `E0`), `repo/docs/pull_request_template.md`, `CLAUDE.md` (paso de PR), `AGENTS.md` (apunta al kit), `plan-del-dia.md` (F3a con ventanas). **Empujado en `d05f4f4`** `[MEDIDO en captura de Fer, 17:20: 5df6c6b..d05f4f4 main -> main; git status vacío]`. Después, tabla de equipo con la IA de cada quien (commit siguiente: verificar el viernes que está en `origin/main`).
- **Sistema de diseño «Tarima» (aprobado por Fer, 18:16):** `DESIGN.md` en la raíz (formato Google, linter `@google/design.md` 0.4.0: 0 errores), tema en `app/globals.css`, Montserrat autoalojada en `app/fonts/` (OFL), Geist del paquete `geist`; `next/font/google` eliminado de `app/layout.tsx`. `npm run lint` y `npm run build` en verde en el contenedor del chat `[MEDIDO 18:25]`: **el build ya no depende de Google Fonts**. Referencia visual: https://claude.ai/artifact/APcRRFs9CSu2Mh7X3aJVwv (privada de Fer). Por commitear: bloque de git en el chat de S001.
- **`U0` cambia:** ya no es «tema neutro» (lo sustituye Tarima). Ahora: botón y campo de shadcn a 44 px en celular, hover del primario a `primary-hover`, variante destructiva en contorno, y página `/tema` con todos los componentes; prueba de cierre: `/tema` en la URL pública vista en celular.
- **Primera acción de S001.5:** acuse; verificar que el commit de Tarima está en `origin/main` y que `/salud` sigue `base ok`; revisar los PR de ensayo `E0` que haya (`docs/equipo/<nombre>.md`) y anotar la IA de cada uno en la tabla de equipo; después escribir y correr `U0`.

## Relevo anterior (S000 → S001), ya consumido

Escrito al cerrar S000, 2026-11-17 16:35.
- **Fase:** antes del evento. Reto: por elegir el sábado a las 9:00. S001 (viernes) es corta: Supabase despierto, misión `U0` (tema base) y puntos abiertos.
- **Carriles** (`ESTADO` en `repo/docs/prompts-<carril>.md`): integrador sellado 16:32, ~~I0~~ ~~I0.1~~, `siguiente: NINGUNO — BLOQUEADO hasta I1`. UI, Núcleo y Datos sellados 14:54, `BLOQUEADO hasta U1/N1/D1`.
- **Demo:** https://hackathon-3b.vercel.app · `/salud` `[MEDIDO 15:26: commit ec20083 · base ok 482 ms]`.
- **Auditorías:** I0 → Aprobado. I0.1 → Aprobado con anotaciones: S2, `next/font/google` reintroducido por shadcn en `app/layout.tsx`, va a la misión de tema de Fer; el paso 5 queda en PA-000.2.
- **Candado probado en las dos direcciones** con `remoto-hackathon-3b.ps1 -Estado`: SIGUE a las 14:58; PARO a las 16:32 (pierna 2 y contenido) con el `ESTADO` viejo; liberado por la reescritura de las 16:32.
- **Cierre de S000:** `3506aa7` empujado (`prompts-integrador.md` y el script) `[MEDIDO en captura de Fer, 16:36]`. Después van los documentos de la renumeración y este contexto: por verificar en S001 que `origin/main` está en un commit posterior a `3506aa7` y que `git status` está limpio.
- **Primera acción de S001 (viernes):** acuse, verificar el cierre de S000 y `/salud`; después escribir y correr `U0` (`PROMPT-APERTURA-S001.md`). **S002 (sábado):** acuse con la plantilla del reto (`PROMPT-APERTURA-S002.md`).

## Evento `[LEÍDO: láminas de 3B, captura 17-nov-2026]`

Sábado 21-nov-2026 · registro 7:00 · retos, reglas y criterios 9:00 · desarrollo **9:30–17:00** · comida 13:30 · presentaciones 17:00 · premiación 19:00. Sede: `<<sin registrar>>`.

## Equipo y carriles

| Rol | Quién | Asistente / cuenta |
|---|---|---|
| Orquestador e integrador · **diseño y carril UI** | Fer | **Claude Max** (este proyecto, Claude Code y Claude Design con las skills de diseño): **el que más cuota tiene** |
| UI de apoyo y quien maneja la demo | Mau | **Antigravity Pro** (agente en el repo, todos los modelos de Gemini) `[dicho por Fer, 20-nov 19:15]`: puede recibir misiones de repo, no solo de chat |
| Carril Núcleo | Mauski | **Claude Pro** → Claude Code (agente en el repo) `[dicho por Fer, 18-nov 17:26]` |
| Carril Datos e IA | Sergio (lo pidió) | **Claude gratuito** → chat web en claude.ai, cuota corta: misiones chicas; lo pesado de Datos va al Claude Code de Fer `[dicho por Fer, 18-nov 17:20]` |
| Negocio y pitch | Alan | Gemini de pago (no programa) |

Mau, Mauski y Alan los asignó Claude a petición del equipo; se pueden intercambiar entre ellos. Fer tomó diseño y UI (17-nov 13:46): él fija la dirección visual y construye las pantallas del camino dorado; Mau construye estados vacío/cargando/error, responsive y pantallas secundarias **sobre el tema de Fer**, y maneja la demo en el pitch.

**Riesgo aceptado:** Fer integra y diseña a la vez. Si a las 11:30 o a las 13:15 la integración se atrasa, el diseño cede: las pantallas pasan a Mau y Fer solo integra.

### Política de cuota (rige el sábado)

- Fer tiene Claude Max y Mauski Claude Pro (Claude Code); Sergio usa Claude gratuito y Mau está por confirmar. **La cuota es un recurso del día como el reloj.**
- Este chat: Opus en esfuerzo **medio**; **alto** solo para el plan de F1 y para auditar el diferenciador. Respuestas cortas; no releer documentos ya leídos.
- Misiones para Mau, Mauski y Sergio: **autocontenidas** (todo lo necesario va en el texto, sin «lee tal documento»), de 30–45 min, sin asumir qué asistente usan, pegables en cualquier chat.
- Lo de escalón fuerte (el diferenciador, un arreglo devuelto una vez, algo que cruza carriles) va al **Claude Code de Fer**, no a un compañero.
- Si a alguien se le acaba la cuota: push de su rama, su misión pasa al Claude Code de Fer y él toma trabajo manual (semilla en hoja de cálculo, pruebas en celular, capturas).

## Reto, alcance y camino dorado

`<<se llena en F1, sábado 9:30–10:00>>`

**Pista (S001.5, viernes 20-nov 19:15)** `[REPORTADO: Ivan, empleado de 3B, por Instagram a Sergio; no oficial]`: los retos «son más para el área de Data» y están enfocados en algo que 3B usa hoy. Consecuencia: el ranking de `retos-probables.md` §1 se reordena a **J3 pronóstico/pedido sugerido · J1 rutas · J4 merma · J6 ubicaciones**; probable que entreguen un archivo de datos (CSV/Excel) → `datos/privado/` hasta confirmar confidencialidad; Python por lotes queda más probable. Un tablero solo no gana: tiene que terminar en una decisión con pesos.

## Recursos

| Qué | Valor |
|---|---|
| Repo GitHub | `luisfernandomtzg/hackathon-3b` · **público** (Vercel Hobby despliega commits de todos; sin secretos ni datos de 3B) |
| Proyecto Supabase | `hackathon-3b` (ref `pshtomfqgbobxheehoij`) en la org **Hackathon 3B**, plan gratuito, RLS automático. Pausa tras 7 días sin uso: abrirlo el viernes |
| Proyecto Vercel / URL de la demo | `hackathon-3b` (equipo luisfernandomtzgDeploys, Hobby) · **https://hackathon-3b.vercel.app** · `/salud` `[MEDIDO 17-nov 15:26: commit ec20083, rama main, base ok 482 ms]` · push→Ready ≈ 27 s · control remoto: `repo/remoto-hackathon-3b.ps1` |
| Llave de API de modelo | `<<sin crear>>` |
| Modelos por escalón (rápido · general · fuerte) | `<<anotar los nombres vigentes al crear las cuentas>>` |

## Decisiones cerradas (S000)

- Stack: Next.js + Tailwind + shadcn/ui · Supabase · Vercel · GitHub. Python solo si el reto lo exige, y por lotes.
- Varios programan en paralelo: carpetas = carriles; un solo integrador.
- Un entorno, sin login, datos solo desde servidor, web responsiva.
- **Plantilla previa sí** (S000, 17-nov): la IA está permitida y nada lo prohíbe. Andamiaje sin producto. Si a las 9:00 lo prohíben, se declara qué traía el repo.
- Roles asignados (ver tabla). Repo público.

## Método de trabajo del sábado (decidido en S001, 18-nov)

- **OpenSpec no se adopta** (lo propuso Mauski): duplica lo que ya hacen `prompts-<carril>.md` + `lib/contrato` + `CLAUDE.md`, agrega instalación y ceremonia por cambio, y choca con `ESTADO` y la regla de paro.
- **Una rama por sprint, desde `main` fresco** (`carril/<area>-sp<N>-<tema>`), y **PR hacia `main`**; solo Fer hace merge, después de auditar. Plantilla en `docs/pull_request_template.md`; el reporte va también en `docs/reportes/`.
- **Sprints de ~1 h, escalonados 15 min** (Datos :15 · Núcleo :30 · Mau :45 · Fer :00); ventanas exactas en `KIT-EQUIPO.md` §6. A las 15:30 se congela lo que haya: la cola de cada área va ordenada y lo de abajo se puede recortar.
- **Listón de auditoría: exprés S0/S1/S2 (§9).** Fable u Opus en esfuerzo alto solo para el plan de F1 y para el diferenciador. El chat audita PRs clonando el repo público (`git fetch origin pull/<n>/head`); la API de PRs de GitHub no está habilitada desde el chat (habría que adjuntar el repo).
- **Un kit universal para cualquier IA:** `docs/KIT-EQUIPO.md` (Parte A, escrita en S001). El sábado, F1 genera solo la Parte B por persona → `docs/paquetes/<nombre>.md` = kit + área, con detalle solo en SP0–SP1; el resto se recalibra tras cada auditoría.
- **Sistema de diseño «Tarima» (18-nov 18:16, Fer):** se continúa la identidad pública de 3B (rojo `#E31B23`, tinta `#04211F`, Montserrat; medidos en tiendas3b.com) en vez de un tema neutro. Precisa la regla de §11 de las instrucciones: **sí** su paleta y tipografía; **no** su logotipo ni una imitación de él, ni sus banners. `DESIGN.md` manda sobre cualquier pantalla. Sin extractor instalado: los agentes evaluaron ~25 repos (dembrandt, designlang, brandmd, impeccable, design.md de Google…) y se adoptó solo el formato `DESIGN.md` de Google.
- **Ensayo `E0` jueves o viernes:** cada compañero instala, le da el kit a su IA, hace un PR `prueba/<nombre>` con `docs/equipo/<nombre>.md` (qué IA y de qué tipo) y comprueba la vista previa de Vercel. Cierra PA-000.2 y PA-000.3.

## Respuestas de los organizadores (`checklist-previo.md` §4)

| Pregunta | Respuesta |
|---|---|
| ¿Se permite plantilla previa? | no lo prohíben ni lo mencionaron → se asume que sí |
| Criterios y pesos | sin respuesta |
| Minutos de presentación y formato | sin respuesta |
| Entregables · ¿repo público? | sin respuesta |
| ¿Dan datos? ¿confidenciales? | sin respuesta |
| Mentores | sin respuesta |

## Puntos abiertos

- PA-000.2 · Push de prueba de un compañero (`prueba/<nombre>`) y su vista previa en Vercel: cierra el paso 5 de I0.1 — Fer, al invitar a los cuatro — jueves.
- ~~PA-000.6 · Quitar `next/font/google` de `app/layout.tsx`~~ — cerrado en S001 con Tarima (build en verde sin Google Fonts). Lo que queda de `U0` (componentes a 44 px, `/tema`) — viernes.
- PA-000.5 · Vercel pide verificar identidad con código al correo de reenvío de Apple y no llega: revisar «Ocultar mi correo» en iCloud. Mientras, se despliega por push (funciona) — Fer.
- PA-000.3 · Invitar a los cuatro al repo con permiso de escritura y que cada uno anote su asistente aquí — Fer — jueves.
- PA-000.4 · Ranking de retos acordado por el equipo — todos — viernes.
- ~~PA-001.1~~ · cerrado 20-nov 19:15: Mau usa Antigravity Pro. (Antes:) Preguntar a Mau, Mauski y Sergio qué IA usarán y si toca el repo o es chat web (planes gratuitos cambiaron en 2026: Gemini CLI → Antigravity para cuentas gratuitas; altas nuevas a Copilot de estudiante pausadas desde el 20-abr) — Fer — miércoles; se confirma en el ensayo `E0`.
- PA-001.2 · Pasar `.env.local` en privado solo a Sergio (los demás trabajan con datos simulados) — Fer — viernes.

## No verificado

- `/salud` pública en verde con shadcn incluido. Sin probar todavía: push de un colaborador y vistas previas por rama. El lint de I0.1 es `[REPORTADO]`.
- Retos, criterios, entregables y reglas de la edición de noviembre: no publicados.
