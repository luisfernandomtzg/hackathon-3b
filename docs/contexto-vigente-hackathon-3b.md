# Contexto vigente — Hackathon Tiendas 3B

> Una página. Se actualiza al cerrar **cada fase**. Fuente: copia del proyecto de claude.ai; espejos en `documentacion/` y en `repo/docs/`.
> Última actualización: **2026-11-17 14:00 · cierre de S000 (segunda pasada: roles, plantilla y repo)** · Sesiones: S000 cerrada · siguiente **S001 (sábado 21-nov)**.

## 🟢 Si estás abriendo la sesión siguiente, lee esto primero

- Aún **no hay reto**: se conoce el sábado a las 9:00 y se elige por orden de llegada.
- El repo trae **plantilla previa** (I0 hecha en S000: Next + fronteras de carril + `/salud`), sin código de producto. Lo siguiente es `I0.1` (shadcn + Supabase + Vercel): mirar en disco si ya tiene reporte.
- Antes del sábado hay tareas de Fer y del equipo en `checklist-previo.md`. Lo que no esté palomeado ahí, se pregunta al abrir.
- Plan de horas en `plan-del-dia.md`. Arquitectura en `arquitectura-provisional.md`.

## Relevo para S001

Sin sesión del día todavía. Primera acción de S001: acuse + plantilla del reto (`PROMPT-APERTURA-S001.md`); si `I0.1` no tiene reporte, Fer la cierra a las 9:30 en paralelo con F1.

## Evento `[LEÍDO: láminas de 3B, captura 17-nov-2026]`

Sábado 21-nov-2026 · registro 7:00 · retos, reglas y criterios 9:00 · desarrollo **9:30–17:00** · comida 13:30 · presentaciones 17:00 · premiación 19:00. Sede: `<<sin registrar>>`.

## Equipo y carriles

| Rol | Quién | Asistente / cuenta |
|---|---|---|
| Orquestador e integrador · **diseño y carril UI** | Fer | Claude de pago (este proyecto, Claude Code y Claude Design con las skills de diseño): **el que más cuota tiene** |
| UI de apoyo y quien maneja la demo | Mau | el de su preferencia (`<<anotar>>`) |
| Carril Núcleo | Mauski | el de su preferencia (`<<anotar>>`) |
| Carril Datos e IA | Sergio (lo pidió) | el de su preferencia (`<<anotar>>`) |
| Negocio y pitch | Alan | — |

Mau, Mauski y Alan los asignó Claude a petición del equipo; se pueden intercambiar entre ellos. Fer tomó diseño y UI (17-nov 13:46): él fija la dirección visual y construye las pantallas del camino dorado; Mau construye estados vacío/cargando/error, responsive y pantallas secundarias **sobre el tema de Fer**, y maneja la demo en el pitch.

**Riesgo aceptado:** Fer integra y diseña a la vez. Si a las 11:30 o a las 13:15 la integración se atrasa, el diseño cede: las pantallas pasan a Mau y Fer solo integra.

### Política de cuota (rige en S001)

- Solo Fer tiene Claude de pago; los demás usan cuentas propias, posiblemente gratuitas. **La cuota es un recurso del día como el reloj.**
- Este chat: Opus en esfuerzo **medio**; **alto** solo para el plan de F1 y para auditar el diferenciador. Respuestas cortas; no releer documentos ya leídos.
- Misiones para Mau, Mauski y Sergio: **autocontenidas** (todo lo necesario va en el texto, sin «lee tal documento»), de 30–45 min, sin asumir qué asistente usan, pegables en cualquier chat.
- Lo de escalón fuerte (el diferenciador, un arreglo devuelto una vez, algo que cruza carriles) va al **Claude Code de Fer**, no a un compañero.
- Si a alguien se le acaba la cuota: push de su rama, su misión pasa al Claude Code de Fer y él toma trabajo manual (semilla en hoja de cálculo, pruebas en celular, capturas).

## Reto, alcance y camino dorado

`<<se llena en F1, sábado 9:30–10:00>>`

## Recursos

| Qué | Valor |
|---|---|
| Repo GitHub | `luisfernandomtzg/hackathon-3b` · **público** (Vercel Hobby despliega commits de todos; sin secretos ni datos de 3B) |
| Proyecto Supabase | `hackathon-3b` (ref `pshtomfqgbobxheehoij`) en la org **Hackathon 3B**, plan gratuito, RLS automático. Pausa tras 7 días sin uso: abrirlo el viernes |
| Proyecto Vercel / URL de la demo | `hackathon-3b` (equipo luisfernandomtzgDeploys, Hobby) · **https://hackathon-3b.vercel.app** · `/salud` `[MEDIDO 17-nov 14:43: commit f84e398, rama main, base ok 847 ms]` · push→Ready ≈ 27 s |
| Llave de API de modelo | `<<sin crear>>` |
| Modelos por escalón (rápido · general · fuerte) | `<<anotar los nombres vigentes al crear las cuentas>>` |

## Decisiones cerradas (S000)

- Stack: Next.js + Tailwind + shadcn/ui · Supabase · Vercel · GitHub. Python solo si el reto lo exige, y por lotes.
- Varios programan en paralelo: carpetas = carriles; un solo integrador.
- Un entorno, sin login, datos solo desde servidor, web responsiva.
- **Plantilla previa sí** (S000, 17-nov): la IA está permitida y nada lo prohíbe. Andamiaje sin producto. Si a las 9:00 lo prohíben, se declara qué traía el repo.
- Roles asignados (ver tabla). Repo público.

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

- PA-000.2 · Resto de `I0.1`: shadcn y el push de prueba de un compañero (Supabase y Vercel ya conectados) — Fer — jueves o viernes.
- PA-000.5 · Vercel pide verificar identidad con código al correo de reenvío de Apple y no llega: revisar «Ocultar mi correo» en iCloud. Mientras, se despliega por push (funciona) — Fer.
- PA-000.3 · Invitar a los cuatro al repo con permiso de escritura y que cada uno anote su asistente aquí — Fer — jueves.
- PA-000.4 · Ranking de retos acordado por el equipo — todos — viernes.

## No verificado

- Lint y build pasaron en la máquina de Fer; `/salud` pública en verde. Sin probar todavía: push de un colaborador y vistas previas por rama.
- Retos, criterios, entregables y reglas de la edición de noviembre: no publicados.
