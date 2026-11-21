# Contexto vigente — Hackathon Tiendas 3B

> Una página. Se actualiza al cerrar **cada fase**. Fuente: copia del proyecto de claude.ai; espejos en `documentacion/` y en `repo/docs/`.
> Última actualización: **2026-11-20 21:00 · cierre de S001.5 (viernes)** · siguiente **S002 (sábado 21-nov, el día del hackatón)**.

## 🟢 Si estás abriendo la sesión siguiente, lee esto primero

- El sábado es **S002**: abre con `S002 3B. Lee el prompt inicial` → `PROMPT-APERTURA-S002.md` + el relevo de abajo. Donde las instrucciones digan «S001» para el sábado, léase S002.
- Aún **no hay reto**: se conoce a las 9:00 y se elige por orden de llegada.
- El repo trae plantilla previa sin producto: I0, I0.1 y **U0** hechas y auditadas. Los cuatro carriles están en `NINGUNO — BLOQUEADO` hasta que S002 escriba sus misiones 1.
- Plan de horas en `plan-del-dia.md`. Arquitectura en `arquitectura-provisional.md`. Sistema de diseño en `repo/DESIGN.md`.

## Relevo para S002 (sábado)

Escrito al cerrar S001.5, 2026-11-20 21:00.
- **Fase:** antes de F0. Reto por elegir a las 9:00; ranking provisional por la pista de Data: J3 · J1 · J4 · J6 (ver «Reto» abajo). PA-000.4 sigue abierto: confirmarlo con el equipo en sede.
- **Carriles:** UI sellado 20:59, ~~U0~~, `BLOQUEADO hasta U1`. Integrador (16:32 del 17-nov), Núcleo y Datos (14:54 del 17-nov) `BLOQUEADO hasta I1/N1/D1`. Sin entregas sin auditar.
- **`main` = `c366e8d`** (merge del PR #1, U0) `[MEDIDO 20:58: origin/main en el clon del chat y git log de Fer]`. En producción `/tema` responde `[MEDIDO 20:59 en Chrome]`. **`/salud` de producción quedó en «Revisando…»** a las 20:59 (dos intentos, 3 y 8 s); a las 20:10 marcó `cdc2c6c · base ok 1050 ms` y la vista previa de U0, a las 20:51, `7ca3494 · base ok 669 ms`. **Primera medición del sábado: `/salud` con el SHA `c366e8d` y `base ok`** (abrirla en sede para despertar la base).
- **Auditoría U0 → Aprobado con anotaciones:** lint y build en verde, grep de colores vacío, 12 botones y 3 campos a 44 px, campo a 16 px `[MEDIDO 20:51]`. S2: `text-[13px]` y `text-[35px]` en `/tema` (iguales a los tokens `mono` y `figure`, sin clase de utilidad). **No verificado:** `/tema` en celular (Fer pidió integrar antes de verla).
- **S2 que sube de peso para el sábado:** `revisarBase()` (`lib/datos/servidor.ts`) no tiene tope de tiempo; si la base no contesta, la página espera sin fin. **Toda lectura a la base que escriba D1/I1 lleva tope de tiempo (≈3 s) y estado de error**: la demo no puede quedarse en «cargando».
- **Ensayo E0:** PR #2 Alan, PR #3 Mauski, rama `prueba/sergio` empujada (PR por abrir). **Falta Mau.** Los PR de ensayo no se integran. Sergio tiene `.env.local` y `base ok` en local `[REPORTADO: captura, 20:44]`; su invitación se reenvió a las 20:39 y ya empujó.
- **Decisiones de S001.5:** Mauski trabaja en **chat web** (no Claude Code): sus misiones van autocontenidas y pidiendo archivos completos, como las de Sergio; lo pesado de Núcleo va al Code de Fer. Mau usa Antigravity Pro (agente en el repo): es el respaldo para misiones de repo.
- **Primera acción de S002:** acuse de §4; medir `/salud` (SHA `c366e8d`, `base ok`); pedir el reto con la plantilla de `PROMPT-APERTURA-S002.md`. En F1, escribir los paquetes `docs/paquetes/<nombre>.md` según esa apertura.

## Evento `[LEÍDO: láminas de 3B, captura 17-nov-2026]`

Sábado 21-nov-2026 · registro 7:00 · retos, reglas y criterios 9:00 · desarrollo **9:30–17:00** · comida 13:30 · presentaciones 17:00 · premiación 19:00. Sede: `<<sin registrar>>`.

## Equipo y carriles

| Rol | Quién | Asistente / cuenta |
|---|---|---|
| Orquestador e integrador · **diseño y carril UI** | Fer | **Claude Max** (este proyecto, Claude Code y Claude Design con las skills de diseño): **el que más cuota tiene** |
| UI de apoyo y quien maneja la demo | Mau | **Antigravity Pro** (agente en el repo, todos los modelos de Gemini) `[dicho por Fer, 20-nov 19:15]`: puede recibir misiones de repo, no solo de chat · E0 pendiente |
| Carril Núcleo | Mauski | **Claude Pro, chat web** (Opus 5.5) `[E0 de Mauski y dicho por Fer, 20-nov 20:56]`: misiones autocontenidas, archivos completos |
| Carril Datos e IA | Sergio (lo pidió) | **Claude gratuito** → chat web en claude.ai (macOS), cuota corta: misiones chicas; lo pesado de Datos va al Claude Code de Fer. Tiene `.env.local` |
| Negocio y pitch | Alan | Antigravity con Google AI Pro (Gemini), toca el repo `[E0 de Alan]` |

Mau, Mauski y Alan los asignó Claude a petición del equipo; se pueden intercambiar entre ellos. Fer tomó diseño y UI (17-nov 13:46): él fija la dirección visual y construye las pantallas del camino dorado; Mau construye estados vacío/cargando/error, responsive y pantallas secundarias **sobre el tema de Fer**, y maneja la demo en el pitch.

**Riesgo aceptado:** Fer integra y diseña a la vez. Si a las 11:30 o a las 13:15 la integración se atrasa, el diseño cede: las pantallas pasan a Mau y Fer solo integra.

### Política de cuota (rige el sábado)

- Fer tiene Claude Max (Code); Mauski, Claude Pro en chat web; Sergio, Claude gratuito en chat web; Mau y Alan, Antigravity con Gemini. **La cuota es un recurso del día como el reloj.**
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
| Proyecto Vercel / URL de la demo | `hackathon-3b` (equipo luisfernandomtzgDeploys, Hobby) · **https://hackathon-3b.vercel.app** · `/salud` `[MEDIDO 20-nov 20:10: commit cdc2c6c, rama main, base ok 1050 ms]` · vista previa por rama: `hackathon-3b-git-<rama>-luisfernandomtzg-deploys.vercel.app` · push→Ready ≈ 27 s · control remoto: `repo/remoto-hackathon-3b.ps1` |
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

- ~~PA-000.2~~ · cerrado 20-nov: Alan, Mauski y Sergio empujaron ramas `prueba/*`; vista previa por rama medida en U0. (Antes:) Push de prueba de un compañero (`prueba/<nombre>`) y su vista previa en Vercel: cierra el paso 5 de I0.1 — Fer, al invitar a los cuatro — jueves.
- ~~PA-000.6 · Quitar `next/font/google` de `app/layout.tsx`~~ — cerrado en S001 con Tarima (build en verde sin Google Fonts). U0 hecha en S001.5.
- PA-000.5 · Vercel pide verificar identidad con código al correo de reenvío de Apple y no llega: revisar «Ocultar mi correo» en iCloud. Mientras, se despliega por push (funciona) — Fer.
- ~~PA-000.3~~ · cerrado 20-nov: los cuatro invitados (Sergio reenviado 20:39); falta el `docs/equipo/` de Mau. (Antes:) Invitar a los cuatro al repo con permiso de escritura y que cada uno anote su asistente aquí — Fer — jueves.
- PA-000.4 · Ranking de retos acordado por el equipo — todos — viernes.
- ~~PA-001.1~~ · cerrado 20-nov 19:15: Mau usa Antigravity Pro. (Antes:) Preguntar a Mau, Mauski y Sergio qué IA usarán y si toca el repo o es chat web (planes gratuitos cambiaron en 2026: Gemini CLI → Antigravity para cuentas gratuitas; altas nuevas a Copilot de estudiante pausadas desde el 20-abr) — Fer — miércoles; se confirma en el ensayo `E0`.
- ~~PA-001.2~~ · cerrado 20-nov 20:44 (captura de Sergio con base ok). (Antes:) Pasar `.env.local` en privado solo a Sergio (los demás trabajan con datos simulados) — Fer — viernes.

## No verificado

- `/salud` de producción con `c366e8d` (quedó en «Revisando…» a las 20:59).
- `/tema` vista en un celular.
- Vistas previas de Vercel de las ramas `prueba/*` de los compañeros.
- Retos, criterios, entregables y reglas de la edición de noviembre: no publicados.
