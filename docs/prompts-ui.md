# Misiones — carril UI

## ESTADO · 2026-11-20 20:59
Carril ui · dueño Fer (diseño, tema y pantallas del camino dorado) · apoyo Mau · misiones 1 · hechas 1 · siguiente **NINGUNO**
Cola: ~~U0~~ → (U1 se escribe en S002, ~10:00 del sábado, con el reto)
siguiente: **NINGUNO — BLOQUEADO hasta que S002 escriba U1** (lo libera Fer al elegir el reto)
Última auditoría: U0 → Aprobado con anotaciones ([MEDIDO 20:51] PR #1 `7ca3494` sobre `2a6606a`; npm ci, lint y build en verde en el contenedor del chat; grep de colores fuera del tema vacío; vista previa: `/salud` 7ca3494 · base ok 669 ms; `/tema` en Chrome de escritorio: 12 botones a 44 px, 3 campos a 44 px y 16 px) · integrada en `main` como `c366e8d` (merge del PR #1, 20:58)
Qué cambió por esa auditoría: S2 — `app/tema/page.tsx` usa `text-[13px]` (mono) y `text-[35px]` (figure): valores iguales a los tokens de DESIGN.md pero sin clase de utilidad; si U1 los necesita, se agregan clases `text-mono`/`text-figure` al tema. Pendiente de Fer: ver `/tema` en su celular (clasificación requiere pantalla).
Reescrituras de este documento: 4
Siguiente con modelo: — (se fija en S002)

---

## U0 — componentes al sistema Tarima y página `/tema` [HECHA · Aprobado con anotaciones]

`carril: ui · rama: carril/ui-sp0-tema desde main fresco · cuelga de: cdc2c6c [MEDIDO 20-nov 19:16, clon de origin/main] · tope: 40 min · clasificación: requiere pantalla · modelo: Sonnet · esfuerzo: medium`

**Primer paso.** Sigue `CLAUDE.md` §Disparador completo: `git fetch`, `git pull --rebase origin main`, `-Estado -Carril ui` con su salida pegada, relee este `ESTADO` y devuelve el acuse con el sello que leíste (`19:21`) y la punta de `origin/main` contra `cdc2c6c`. Si la punta es otra, dilo y sigue solo si desciende de `cdc2c6c`.

**Hechos que no puedes ver.**
- El tema Tarima ya está en `main` (`22080db`): `app/globals.css` define las clases `bg-primary-hover`, `bg-primary-active`, `bg-input-bg`, `text-danger`, `border-danger`, `bg-danger-bg`, `text-success bg-success-bg`, `text-warning bg-warning-bg`, `text-info bg-info-bg`, `text-text-tertiary`, `text-text-muted`, `text-link`, `font-heading`, `font-mono` `[LEÍDO app/globals.css y DESIGN.md, 19:20]`. **No toques `app/globals.css`.**
- `components/ui/button.tsx` hoy: alto por defecto `h-8`, hover del primario `hover:bg-primary/80`, destructivo con relleno `bg-destructive/10`, y clases `dark:` `[LEÍDO 19:20]`. `components/ui/input.tsx`: `h-8`, `bg-transparent`, `md:text-sm`, clases `dark:`.
- `DESIGN.md` dice: un solo tema claro, **sin `dark:`**; 44 px o no se toca; texto de campo a 16 px; destructivo en contorno `danger`, nunca relleno rojo.

**Qué construir.**
1. `components/ui/button.tsx`:
   - talla `default` → `h-11` (44 px), `sm` → `h-9` (36 px, densidad compacta de escritorio), `icon` → `size-11`, `icon-sm` → `size-9`. Deja `xs`, `lg`, `icon-xs`, `icon-lg` como están.
   - variante `default`: `hover:bg-primary-hover active:bg-primary-active` en vez de `hover:bg-primary/80`.
   - variante `destructive`: `border-danger bg-transparent text-danger hover:bg-danger-bg`, sin relleno.
   - quita todas las clases `dark:` del archivo.
2. `components/ui/input.tsx`: `h-11`, `bg-input-bg`, `text-base` siempre (quita `md:text-sm`), sin clases `dark:`.
3. `components/shell.tsx`: shell vacío y responsivo = **Encabezado** de `DESIGN.md` (nombre del producto en `font-heading` —usa «Prototipo» como nombre provisional— y el texto «Prototipo para Tiendas 3B»; **sin logotipo**) + `<main>` de una columna con margen 16 en celular y máximo 1,200 px con margen 24 en escritorio.
4. `app/tema/page.tsx`: dentro del shell, todos los componentes de `DESIGN.md` §Components, cada uno con sus estados:
   - Botón: primario, secundario, contorno, fantasma, destructivo, enlace; en reposo, deshabilitado, y una nota en texto de que hover, foco y presionado se prueban con el dedo o el teclado.
   - Campo: con etiqueta visible arriba, con error (causa y salida, `aria-invalid`) y deshabilitado.
   - Estatus: los cuatro tonos con punto y palabra (`rounded-full`).
   - Cifra: una sola, `font-heading tabular-nums`, subrayada en rojo.
   - Fila: 52 px con nombre, SKU en `font-mono`, cantidad a la derecha y estatus.
   - Aviso: contorno completo del tono, el de error con `role="alert"`.
   - Banda: una, roja con texto blanco.
   - Vacío, cargando (esqueleto en `muted`) y error.
   Datos de ejemplo inventados y verosímiles (productos de despensa, tiendas con número); ninguna cifra de 3B.

**Lo que NO se toca.** `app/globals.css`, `app/salud/`, `lib/`, `supabase/`, `datos/`, carpetas de otros carriles, y el resto de `components/ui/`. Nada de producto ni de reto. No se escribe en la base.

**Prueba de cierre (ejecutable).**
1. `npm run lint` y `npm run build` en verde (pega el final de cada salida).
2. Sin colores fuera del tema en lo que cambiaste: `git diff origin/main --stat` y `git diff origin/main | grep -nE "#[0-9a-fA-F]{6}|bg-white|gray-|neutral-|red-|dark:"` **no devuelve nada** (pega la salida vacía).
3. Push de la rama y PR a `main` con `docs/pull_request_template.md`. En la vista previa de Vercel del PR, `/tema` abre; Fer la ve **en su celular** (por eso `requiere pantalla`) y el botón y el campo miden 44 px.
4. `/salud` de esa misma vista previa sigue mostrando `base ok`.

**Para y pregunta** si algo de `DESIGN.md` no alcanza para una pieza (un color, un radio, un estatus que no está): no lo inventes. Si al abrir un archivo ya está como se pide, dilo y no lo toques.

**Entregable.** Rama `carril/ui-sp0-tema` empujada + PR + reporte de 12 líneas en `docs/reportes/U0-tema.md`, escrito al final y de una vez, con modelo y esfuerzo con que corrió, la URL de la vista previa y su apartado «no hecho / simulado».
**Commit sugerido:** `feat(ui): componentes a 44 px y página /tema con Tarima (U0)`

---

## Bitácora de reescrituras

- 2026-11-17 13:20 · creado en S000, sin misiones.
- 2026-11-17 14:54 · S000: ESTADO al formato v1.2 (sello del reloj, `BLOQUEADO hasta`).
- 2026-11-20 19:21 · S001.5: se escribe `U0` (agenda de `PROMPT-APERTURA-S001.md` §3) y se libera el carril; sin auditoría previa.
- 2026-11-20 20:51 · S001.5: auditoría de U0 (PR #1) → Aprobado con anotaciones; carril bloqueado hasta U1.
- 2026-11-20 20:59 · S001.5: resellado después del merge de U0 (`c366e8d`).
