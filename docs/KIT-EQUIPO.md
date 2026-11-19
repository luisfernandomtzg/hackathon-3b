# KIT DEL EQUIPO — Hackathon Tiendas 3B · sábado 21-nov-2026

> **v1.0 · 2026-11-18 17:05 · S001.** Es el mismo kit para las cinco personas y para cualquier IA (Claude, ChatGPT, Gemini, Copilot, Cursor, Codex, Antigravity…).
> **Parte A** (este archivo) no depende del reto y se escribió antes del evento. **Parte B** (tu área y tus misiones) se genera el sábado a las ~10:00 y llega como `docs/paquetes/<tu-nombre>.md`, que ya trae esta Parte A adentro: **ese único archivo es el que le das a tu IA.**
> Si algo de aquí contradice `docs/contexto-vigente-hackathon-3b.md`, manda el contexto vigente.

---

## 0 · Para la persona (léelo tú, 2 minutos)

**Qué hago con este archivo depende de qué tipo de IA uso:**

| Tu IA… | Cómo se usa |
|---|---|
| **toca la carpeta del repo** (Claude Code, Codex, Copilot en modo agente, Cursor, Antigravity/Gemini CLI) | Abre la IA **dentro de la carpeta del repo** y pégale el «prompt de arranque» de abajo. Ella lee los archivos, corre comandos y hace commits. Es la opción rápida. |
| **es un chat en el navegador** (ChatGPT, Gemini, Claude.ai) | Sube tu `docs/paquetes/<tu-nombre>.md` al chat y pégale el «prompt de arranque». Cada vez que pidas código, **pégale el archivo completo que va a cambiar** y pídele **el archivo completo de vuelta** (no fragmentos). Tú lo guardas, corres los comandos y haces el commit. Es más lento: ve en bloques chicos. |

**Prompt de arranque** (cópialo tal cual):

```
Eres implementador en un equipo de 5 en un hackathon de un día. Te adjunto (o tienes en el repo)
docs/paquetes/<MI-NOMBRE>.md. Léelo completo antes de hacer nada. Sigue sus reglas al pie de la letra,
en especial: solo tocas las carpetas de mi área, no cambias lib/contrato, no agregas dependencias sin
decirlo, y si algo no está claro PARAS y preguntas. Si vas a tocar una pantalla, primero lees DESIGN.md
(raíz del repo) y usas solo sus tokens. Ejecuta solo la misión que yo te diga por su id.
Antes de escribir código devuélveme el acuse de la sección 7 del kit. Si la misión toca interfaz, sigue la
sección 13: el sistema de diseño ya existe (DESIGN.md) y no se inventa nada.
```

---

## 1 · Qué estamos construyendo y por qué (para la IA)

- **Evento:** Hackathon de **Tiendas 3B**, sábado 21-nov-2026. Desarrollo de **9:30 a 17:00**; a las **17:00** se presenta **lo que esté desplegado** en la URL pública. Usar IA está permitido.
- **El cliente:** Tiendas 3B es una cadena mexicana de **hard discount**: surtido corto, marca propia dominante, tiendas chicas con **2–3 empleados sin un minuto libre**, costos al mínimo y crecimiento rápido por regiones. El jurado busca algo **que 3B podría pilotear** y gente que entendió su negocio.
- **Toda idea pasa por el filtro 3B.** Si falla dos, se descarta:
  1. ¿Baja un costo o sube la rotación? 2. ¿Funciona sin agregar trabajo al personal de tienda? 3. ¿Cero hardware nuevo y cero capacitación (celular, caja, navegador)? 4. ¿Aprovecha que el surtido es corto (lo simple alcanza)? 5. ¿Escala copiando de una tienda a mil? 6. ¿Se puede pilotear barato (10 tiendas, 4 semanas)?
- **El reto concreto, la solución y el «camino dorado»** (los 5–7 pasos exactos que verá el jurado) están en la **Parte B**. El camino dorado es la **única especificación del día**: lo que no aparece ahí no se construye.

## 2 · Reglas que no se negocian

1. **El reloj manda.** A las 15:30 se congelan funciones; a las 16:15, el código. Tu misión tiene un **tope en minutos**: al 150 % se corta y se entrega lo que haya.
2. **Una demo que corre vale más que tres funciones a medias.** `main` siempre se puede desplegar. Nada a medias entra a `main`.
3. **Tu área, tus carpetas** (tabla §3). Necesitas algo de otra área: **lo pides, no lo editas.**
4. **`lib/contrato/` es el acuerdo entre áreas** (tipos y forma de los datos). Solo lo edita Fer. Si no te alcanza, para y avisa.
5. **Mientras otra área no te entrega, usas datos simulados** que cumplen el contrato. Nadie espera a nadie.
6. **Datos solo desde servidor.** Ningún componente de navegador importa Supabase ni llama a un modelo de IA. `lib/dominio/` no importa nada de Next ni de Supabase. (El lint lo revisa: `npm run lint`.)
7. **Cero secretos en el repo** (el repo es **público**). Llaves solo en `.env.local` (ignorado) y en Vercel. **Los datos que entregue 3B son confidenciales:** van a `datos/privado/` (ignorado), nunca al repo ni a un chat de IA que no esté autorizado.
8. **Ninguna cifra inventada.** En pantalla o en el pitch, un número es de 3B con fuente, una medición hecha en la demo, o un supuesto dicho como supuesto.
9. **Sin login, sin panel de administración, sin refactors de paso, sin funciones fuera de tu misión.**
10. **Dependencias nuevas:** solo si la misión las nombra. Si necesitas otra, avisa a Fer **antes**: `package.json` y su lockfile son el archivo donde más chocan los PRs.
11. **Verifica antes de arreglar:** si lo que te piden ya está hecho, dilo y no lo toques. Si crees que la misión está mal planteada, dilo antes de programar.
12. **Nada destructivo** (borrar datos, `--force` sobre `main`, reescribir historia ajena) sin que Fer lo apruebe.
13. **Interfaz en español de México**, sin texto de relleno ni «Lorem ipsum»; productos, colonias y tiendas plausibles. **Sin logotipo de 3B**: su nombre va en texto.
14. **Diseño: `DESIGN.md` es la regla.** El sistema «Tarima» toma la paleta y la tipografía de 3B (rojo `#E31B23`, tinta `#04211F`, Montserrat) y las ordena para pantallas de trabajo. Todo color, tipografía, radio y espacio sale de ahí, con clases semánticas (`bg-primary`, `text-foreground`, `text-text-tertiary`). Nunca un hex, `bg-white` ni `text-gray-500`. Si algo no está, se pide a Fer; el tema (`app/globals.css`) solo lo cambia él.

## 3 · Equipo, áreas y carpetas

| Persona | Área | Carpetas que SÍ toca | No toca |
|---|---|---|---|
| **Fer** | Integrador + diseño y pantallas del camino dorado | `lib/contrato/`, `app/globals.css` (tema), `app/`, `components/`, merges a `main` | — |
| **Mau** | UI de apoyo · maneja la demo | `app/`, `components/` **sobre el tema de Fer**: estados vacío/cargando/error, responsive, pantallas secundarias | el tema, `lib/` |
| **Mauski** | Núcleo (lógica de negocio) | `lib/dominio/`: funciones puras con pruebas, sin base ni Next | pantallas, base |
| **Sergio** | Datos e IA | `supabase/` (migraciones), `datos/`, `lib/datos/`, `lib/ia/`, `ml/` | diseño visual |
| **Alan** | Negocio y pitch | láminas, guion, cifras con fuente, mentores, cronómetro, recorrer la demo tras cada merge | código |

Dentro de `app/` y `components/` Fer y Mau se reparten **archivos**, no carpetas: la Parte B dice cuáles son de cada uno.

## 4 · Stack y repo

- Repo: **https://github.com/luisfernandomtzg/hackathon-3b** (público). Demo: **https://hackathon-3b.vercel.app** · `/salud` muestra qué commit está desplegado.
- **Next.js 16.4 (App Router, TypeScript) · React 19 · Tailwind 4 · shadcn/ui (sobre Base UI) · Supabase (Postgres) · Vercel.**
- **Sistema de diseño: `DESIGN.md`** en la raíz (tokens, componentes y reglas). Fuentes autoalojadas: Montserrat en títulos y cifras, Geist en texto, Geist Mono en claves. Un solo tema claro; no se usa modo oscuro.
- ⚠️ **Next 16 trae cambios que tu IA probablemente no conoce.** Antes de escribir código de Next, la IA debe leer la guía de `node_modules/next/dist/docs/` (si toca el repo) o tú le pegas lo relevante. Si una API «no existe», no la inventes: revisa la documentación.
- Componentes de shadcn ya instalados: button, card, input, table, badge, dialog, select, tabs, skeleton, sonner. Uno nuevo se agrega con `npx shadcn@latest add <nombre>` **y se avisa** (toca archivos compartidos).
- Cliente de base **solo de servidor**: `lib/datos/servidor.ts`.

## 5 · Instalación (se hace ANTES del sábado, en el ensayo §12)

Necesitas: **Git**, **Node 22 LTS** (mínimo 20.9; medido con 22.23 el 18-nov), una cuenta de GitHub **invitada al repo con permiso de escritura** (Fer te invita; acepta el correo), y tu IA ya funcionando y con sesión iniciada.

```bash
git clone https://github.com/luisfernandomtzg/hackathon-3b.git
cd hackathon-3b
npm ci                  # instala exactamente lo del lockfile (no uses npm install salvo que la misión lo diga)
npm run lint            # debe salir sin errores
npm run dev             # http://localhost:3000 · y http://localhost:3000/salud
```

- **`.env.local`:** solo lo necesita quien lee la base (Sergio y Fer). Fer te pasa los valores **en privado**, nunca en el grupo. Sin él, `/salud` dice que la base falla: es normal y puedes trabajar con datos simulados.
- `npm run build` hoy puede fallar sin internet (la fuente se descarga de Google); se arregla el viernes (misión `U0`). El sábado debe pasar.
- El día del evento, en sede: `git pull` antes de las 9:30 y `npm ci` si cambió el lockfile.

## 6 · El día: fases y sprints escalonados

| Hora | Qué pasa | Tú |
|---|---|---|
| 9:00–9:30 | Presentan los retos; elegimos | Fotos de las láminas, preguntas a mentores |
| 9:30–10:00 | **F1** · Fer y Claude deciden solución, camino dorado y misiones | Alan + uno con mentores; los demás: `git pull`, `npm ci`, IA abierta. **Nadie programa producto todavía** |
| ~10:00 | Llega tu `docs/paquetes/<nombre>.md` (Parte B) | Se lo das a tu IA |
| 10:00–10:45 | **SP0 · esqueleto**: Fer sube el contrato a `main` primero (~10:10); cada área entrega su pieza mínima | Ventana de PR: Sergio 10:30 · Mauski 10:35 · Mau 10:40 · Fer 10:45 |
| 10:45–15:30 | **SP1–SP4**, un sprint ≈ una hora por área | Ventanas de la tabla de abajo |
| 13:15 | **Camino dorado de punta a punta** (feo pero vivo) | Se recorre la demo completa |
| 13:30–14:00 | Comida: antes de levantarte, tu IA queda con una misión larga | — |
| **15:30** | **Congelar funciones.** Solo se arreglan defectos visibles | — |
| 16:15 | Congelar código, video de respaldo, ensayos | Mau maneja la demo, Alan narra |

**Ventanas de entrega (hora límite para abrir tu PR):** escalonadas 15 min para que Fer integre **uno a la vez**.

| Sprint | Sergio · Datos | Mauski · Núcleo | Mau · UI apoyo | Fer · UI |
|---|---|---|---|---|
| SP1 | 11:15 | 11:30 | 11:45 | 12:00 |
| SP2 | 12:15 | 12:30 | 12:45 | 13:00 |
| SP3 (cruza la comida) | 14:15 | 14:30 | 14:45 | 15:00 |
| SP4 (último) | 15:15 | 15:20 | 15:25 | 15:30 |

- Tu cola de misiones (Parte B) va **en orden de importancia**: lo del camino dorado primero. Lo de abajo se puede recortar sin culpa. **No es «hasta terminar el 100 %»: es hasta las 15:30.**
- Si terminas antes de tu ventana, abre el PR antes. Si llegas a tu ventana sin terminar, **abre el PR con lo que funcione** y di qué faltó.
- Si te quedas sin nada: **avísale a Fer de inmediato**; tu Parte B trae misiones de reserva.

## 7 · Acuse: lo primero que tu IA devuelve en cada misión

```
Misión: <id> — <título> · tope <min> · área <área>
Voy a tocar: <archivos o carpetas> · Fuera de mi área: <nada | qué y por qué>
Datos que uso: <reales del contrato | simulados — cuáles>
Rama: carril/<área>-sp<N>-<tema> · sale de main en <sha corto>
Dudas antes de empezar: <ninguna | cuáles>
```

Si hay dudas de alcance, **se resuelven antes de programar**.

## 8 · Git, sprint por sprint (copia y pega)

**Al empezar cada sprint** — siempre desde un `main` actualizado, nunca desde tu rama vieja:

```bash
git switch main
git pull
git switch -c carril/<area>-sp<N>-<tema>     # ej. carril/datos-sp1-semilla
```

> Excepción: si tu sprint nuevo **necesita** tu PR anterior y Fer todavía no lo integra, sal de tu rama anterior y escribe en el PR: «cuelga de #<número>».

**Al terminar** (antes de tu ventana):

```bash
git add <solo tus archivos>                  # nunca "git add ." a ciegas: revisa con git status
git commit -m "<área>: <qué hace> (<id de misión>)"
git fetch origin
git rebase origin/main                       # trae lo que ya integró Fer; si hay conflicto fuera de tu área, PARA y avisa
npm run lint && npm run build                # los dos en verde, o no hay PR
git push -u origin HEAD                      # si ya habías empujado y rebasaste: git push --force-with-lease (solo en TU rama)
```

Luego abre el **Pull Request hacia `main`** en GitHub (el formulario se llena solo con la plantilla) y **pega el enlace en el grupo**.

- **Nunca** empujas a `main`. **Nunca** haces merge de tu PR ni del de otro: integra Fer, después de la auditoría.
- Archivos que chocan entre todos: `package.json`, `package-lock.json`, `app/layout.tsx`, `app/globals.css`, `AGENTS.md`. **No los toques** salvo que tu misión lo diga. Si `npm run dev` reescribe `AGENTS.md`, déjalo fuera de tu commit (`git restore AGENTS.md`).

## 9 · El PR y el reporte

Escribe `docs/reportes/<id>-<tema>.md` (máximo 12 líneas, **al final y de una sola vez**), commitéalo en tu rama y **pega el mismo texto en la descripción del PR**:

```
<id> — <título> · rama <nombre> · sale de <sha de main> · IA <cuál y modelo> · <min> min
Hecho: <qué quedó funcionando, una línea por cosa>
Prueba de cierre: <comando o URL> → <salida REAL, pegada>
No hecho / simulado: <lo que quedó con datos falsos o a medias — obligatorio>
Archivos fuera de mi área: <ninguno | cuáles y por qué>
¿Tocó la base?: <no | qué tablas y cuántas filas>
Necesito de otra área: <nada | qué>
```

Un reporte sin «No hecho / simulado» no se audita.

## 10 · Cómo se audita tu PR (el listón del día)

Fer y Claude lo revisan en ~5 minutos: ¿hizo lo pedido?, ¿corre la prueba de cierre?, ¿tocó solo su área?, ¿sigue pasando el camino dorado?

| Severidad | Qué es | Qué pasa |
|---|---|---|
| **S0** | Rompe o pone en riesgo el camino dorado (build roto, secreto en el código, contrato cambiado) | **No entra.** Recibes el arreglo `<id>.1` y lo haces en **la misma rama** |
| **S1** | Lo vería el jurado (dato absurdo, pantalla rota en celular, texto de relleno) | Entra; se arregla antes de las 16:15 |
| **S2** | Todo lo demás (estilo, nombres, «podría ser más escalable») | Entra y se anota; **hoy no se arregla** |

Dos arreglos sobre la misma misión y se acabó: se recorta o se cambia el enfoque. **No se persigue la perfección: se persigue que corra a las 17:00.**

## 11 · Cuando algo sale mal

- **Tu IA se atora** o propone algo raro dos veces: para, abre el PR con lo que hay y avisa a Fer.
- **Se te acaba la cuota de tu IA:** `git push` de tu rama tal como esté, avísale a Fer (tu misión pasa a su Claude Code) y tomas trabajo manual: datos semilla en hoja de cálculo, probar en celular, capturas.
- **Conflicto de git fuera de tu área:** no lo resuelvas a ciegas; `git rebase --abort` y avisa.
- **La IA quiere instalar una librería, cambiar el contrato o tocar otra carpeta:** no. Avisa.

---

## 12 · ENSAYO (antes del sábado) — misión `E0`

Objetivo: que el sábado a las 10:00 nadie pierda media hora instalando. **Tope: 30 min. Fecha: jueves 19 o viernes 20.**

1. Acepta la invitación al repo; instala lo de §5; `npm ci`, `npm run lint`, `npm run dev` y abre `/salud`.
2. Abre tu IA como la vas a usar el sábado y dale **este archivo** con el prompt de arranque. Pídele el acuse de §7 para la misión `E0`.
3. Rama `prueba/<tu-nombre>` (desde `main`, §8). Con tu IA crea **un solo archivo** `docs/equipo/<tu-nombre>.md` con:
   ```
   Nombre: · Área:
   IA que usaré: <producto y plan: gratuito / estudiante / pago> · Tipo: <toca el repo | chat web>
   Modelo que me da: · ¿Leyó el kit y me dio el acuse?: <sí/no, qué falló>
   Sistema operativo: · node --version: · npm run lint: <ok | error>
   ¿Algo de este kit no se entendió?:
   ```
4. Commit, push y **abre el PR hacia `main`** con la plantilla. Revisa que en el PR aparezca el **enlace de vista previa de Vercel** y ábrelo en tu celular.
5. Pega el enlace del PR en el grupo. **No hagas merge.**

Si algún paso falla, anótalo en tu archivo y avisa: **para eso es el ensayo.**

---

## 13 · SISTEMA DE DISEÑO — instrucción obligatoria para la IA

> **Para la IA que lee esto:** el sistema de diseño de este proyecto **ya existe**. Se llama **Tarima** y está en el archivo `DESIGN.md` de la raíz del repo. **No diseñes uno nuevo, no propongas otra paleta ni otra tipografía, no inventes componentes, colores, tamaños, radios ni sombras.** Úsalo como regla, sin excepciones.

1. **Antes de crear o cambiar cualquier pantalla o componente, lee `DESIGN.md` completo.** Si tu persona trabaja en un chat web y no puedes ver el repo, pídele que te pegue `DESIGN.md` antes de escribir una sola línea de interfaz.
2. **Solo clases semánticas del tema** (`app/globals.css`): `bg-primary`, `text-primary-foreground`, `bg-background`, `text-foreground`, `text-text-tertiary`, `bg-success-bg text-success`, `border-input`, `font-heading`… **Prohibido:** hex (`#E31B23`), `bg-white`, `bg-red-500`, `text-gray-500`, `rounded-[7px]`, `shadow-lg` en tarjetas, estilos en línea con colores.
3. **Usa los componentes que ya están** en `components/ui/` (shadcn): Button, Input, Card, Badge, Table, Dialog, Select, Tabs, Skeleton, Sonner. No instales otra librería de interfaz ni copies componentes de otro lado.
4. **Lo que no se negocia:** un botón rojo (`primary`) por vista; el rojo de error es `danger`, nunca el de acción; estatus con punto y palabra, nunca solo color; controles táctiles de 44 px; Montserrat solo en títulos y cifras, Geist en el texto; sin modo oscuro; sin degradados; sin emojis; **sin logotipo de 3B** (su nombre va en texto).
5. **Si algo que necesitas no está en `DESIGN.md`** (un color, un tamaño, un estatus, un componente): **PARA y avísale a tu persona** para que se lo pida a Fer. No lo resuelvas «a ojo» ni con un valor parecido.
6. **No edites `app/globals.css`, `DESIGN.md` ni `app/fonts/`:** son de Fer.
7. En tu acuse (§7), si la misión toca interfaz, agrega una línea: `DESIGN.md leído: sí · tokens que voy a usar: <lista corta>`.

---

## Parte B — tu área (se agrega el sábado)

`<<El sábado ~10:00, tu docs/paquetes/<nombre>.md trae aquí: reto y solución en 5 líneas · camino dorado · contrato (lib/contrato) · tu área y tus archivos · tu cola de misiones SP0–SP4 con tope, prueba de cierre y datos simulados · misiones de reserva. Los paquetes de quien toca interfaz (Fer y Mau) llevan además DESIGN.md completo pegado al final, para que una IA de chat web lo tenga sin abrir el repo.>>`
