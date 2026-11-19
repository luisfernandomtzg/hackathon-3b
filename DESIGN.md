---
version: alpha
name: Tarima
description: Sistema de diseño del equipo para el prototipo del Hackatón de Tiendas 3B. Toma la identidad pública de 3B (rojo plano, blanco, tinta casi negra, Montserrat muy pesada) y la ordena para pantallas de trabajo. No es material oficial de Tiendas 3B.
colors:
  brand-50: "#FEF3F1"
  brand-100: "#FFE4E0"
  brand-200: "#FECBC4"
  brand-300: "#FEA196"
  brand-400: "#FB6157"
  brand-500: "#E31B23"
  brand-600: "#C4101A"
  brand-700: "#9D0812"
  brand-800: "#76080D"
  brand-900: "#4F0A0A"
  ink-25: "#F9FAFA"
  ink-50: "#F4F6F6"
  ink-100: "#EAEEED"
  ink-200: "#DADFDF"
  ink-300: "#BFC6C5"
  ink-400: "#848F8D"
  ink-500: "#667170"
  ink-600: "#4C5857"
  ink-700: "#31413F"
  ink-800: "#1C2F2E"
  ink-900: "#04211F"
  white: "#FFFFFF"
  primary: "{colors.brand-500}"
  primary-hover: "{colors.brand-600}"
  primary-active: "{colors.brand-700}"
  on-primary: "{colors.white}"
  background: "{colors.white}"
  surface: "{colors.white}"
  surface-2: "{colors.ink-25}"
  muted: "{colors.ink-100}"
  input-bg: "{colors.ink-25}"
  text-primary: "{colors.ink-900}"
  text-secondary: "{colors.ink-700}"
  text-tertiary: "{colors.ink-600}"
  text-muted: "{colors.ink-500}"
  link: "{colors.brand-600}"
  border-strong: "{colors.ink-400}"
  focus: "{colors.ink-900}"
  success: "#1F7A4D"
  success-bg: "#E3F3EA"
  warning: "#8A5A12"
  warning-bg: "#FBF1DC"
  danger: "{colors.brand-700}"
  danger-bg: "{colors.brand-50}"
  info: "#1C244B"
  info-bg: "#E8EBF5"
  highlight: "#4BD811"
  chart-1: "#1C244B"
  chart-2: "#0E7C6B"
  chart-3: "#B4690E"
  chart-4: "#7A4E9C"
  chart-5: "#667170"
  chart-focus: "{colors.brand-500}"
typography:
  display:
    fontFamily: Montserrat
    fontSize: 42px
    fontWeight: 900
    lineHeight: 44px
    letterSpacing: -0.01em
  h1:
    fontFamily: Montserrat
    fontSize: 29px
    fontWeight: 800
    lineHeight: 36px
    letterSpacing: -0.01em
  h2:
    fontFamily: Montserrat
    fontSize: 24px
    fontWeight: 800
    lineHeight: 30px
  h3:
    fontFamily: Montserrat
    fontSize: 20px
    fontWeight: 700
    lineHeight: 26px
  figure:
    fontFamily: Montserrat
    fontSize: 35px
    fontWeight: 800
    lineHeight: 40px
    letterSpacing: -0.01em
    fontFeature: '"tnum"'
  h4:
    fontFamily: Geist
    fontSize: 17px
    fontWeight: 600
    lineHeight: 24px
  body:
    fontFamily: Geist
    fontSize: 16px
    fontWeight: 400
    lineHeight: 24px
  body-compact:
    fontFamily: Geist
    fontSize: 14px
    fontWeight: 400
    lineHeight: 20px
  label:
    fontFamily: Geist
    fontSize: 14px
    fontWeight: 500
    lineHeight: 20px
  caption:
    fontFamily: Geist
    fontSize: 12px
    fontWeight: 500
    lineHeight: 16px
  mono:
    fontFamily: Geist Mono
    fontSize: 13px
    fontWeight: 400
    lineHeight: 20px
rounded:
  sm: 4px
  md: 6px
  lg: 8px
  xl: 12px
  full: 9999px
spacing:
  "1": 4px
  "2": 8px
  "3": 12px
  "4": 16px
  "5": 20px
  "6": 24px
  "8": 32px
  "10": 40px
  "12": 48px
  control-touch: 44px
  control-compact: 36px
  row-touch: 52px
  row-compact: 36px
  header: 56px
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.label}"
    rounded: "{rounded.md}"
    height: 44px
    padding: 16px
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
    textColor: "{colors.on-primary}"
  button-primary-active:
    backgroundColor: "{colors.primary-active}"
    textColor: "{colors.on-primary}"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.md}"
    height: 44px
    padding: 16px
  button-danger:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.danger}"
    rounded: "{rounded.md}"
    height: 44px
  input:
    backgroundColor: "{colors.input-bg}"
    textColor: "{colors.text-primary}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    height: 44px
    padding: 12px
  chip-success:
    backgroundColor: "{colors.success-bg}"
    textColor: "{colors.success}"
    typography: "{typography.caption}"
    rounded: "{rounded.full}"
    height: 24px
  chip-warning:
    backgroundColor: "{colors.warning-bg}"
    textColor: "{colors.warning}"
    typography: "{typography.caption}"
    rounded: "{rounded.full}"
    height: 24px
  chip-danger:
    backgroundColor: "{colors.danger-bg}"
    textColor: "{colors.danger}"
    typography: "{typography.caption}"
    rounded: "{rounded.full}"
    height: 24px
  chip-info:
    backgroundColor: "{colors.info-bg}"
    textColor: "{colors.info}"
    typography: "{typography.caption}"
    rounded: "{rounded.full}"
    height: 24px
  chip-neutral:
    backgroundColor: "{colors.muted}"
    textColor: "{colors.text-tertiary}"
    typography: "{typography.caption}"
    rounded: "{rounded.full}"
    height: 24px
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.lg}"
    padding: 16px
  list-row:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text-primary}"
    height: 52px
    padding: 16px
  band:
    backgroundColor: "{colors.brand-500}"
    textColor: "{colors.white}"
    typography: "{typography.h2}"
    padding: 20px
  band-ink:
    backgroundColor: "{colors.ink-900}"
    textColor: "{colors.highlight}"
    typography: "{typography.h2}"
    padding: 20px
  header:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text-primary}"
    height: 56px
---

# Tarima — sistema de diseño

> **Regla para toda IA y toda persona del equipo:** lee este archivo completo antes de crear o cambiar una pantalla. Todo color, tamaño, radio y espacio sale de aquí. Si algo que necesitas no está, **para y pregunta a Fer**; no lo inventes.
> Referencia visual con ejemplos vivos: https://claude.ai/artifact/APcRRFs9CSu2Mh7X3aJVwv (privada de Fer). Este archivo manda sobre ella.

## Overview

Tarima continúa la identidad pública de Tiendas 3B —rojo plano, blanco, tinta casi negra, Montserrat muy pesada— y la vuelve una herramienta de trabajo. Su nombre viene de cómo vende 3B: el producto en su caja, sobre tarima, en el mismo orden en todas las tiendas. El sistema se comporta igual: cajas de borde fino, sin adorno, siempre en el mismo lugar.

**Para quién.** Personal de tienda, de pie, con el celular en una mano y entre dos tareas: pantallas de una sola decisión, controles de 44 px, texto de 16 px. Es el caso por defecto. Gerencia de distrito y región, en laptop: tablas compactas con los mismos tokens. La clienta, si el reto lo pide: teléfono modesto, lenguaje llano. Cero capacitación: si una pantalla necesita explicación, se rediseña.

**Las ocho reglas.**

1. Todo valor sale de un token. Nada de hex, `bg-white`, `text-gray-500` ni números sueltos en una pantalla.
2. Un rojo de acción (`primary`) por vista.
3. El rojo de acción no es el rojo de error: error y destructivo usan `danger`, en contorno o chip y con palabra.
4. Una cifra subrayada en rojo por vista: es la firma del sistema (componente Cifra).
5. Bordes, no sombras. La única sombra es la de lo que flota.
6. 44 px o no se toca.
7. El nombre de 3B va en texto; sin su logotipo y sin imitarlo.
8. Cada pantalla trae sus tres estados: vacío, cargando y error.

**Voz.** De tú, frases cortas, el dato primero: «Faltan 14 productos para completar la tienda». Sentence case en títulos y botones; sin exclamaciones, sin emojis, sin «¡Ups!». Los botones nombran la acción («Confirmar pedido») y la confirmación repite el nombre («Pedido confirmado»). Los errores dicen la causa y la salida: «No se pudo enviar el pedido. La tienda no tiene conexión; quedó guardado en este teléfono.» Formato `es-MX`: `$1,234.50`, `3,765 tiendas`, `21 nov 2026`, hora de 24 h. Palabras del negocio: tienda, CEDI, pedido, surtido, merma, marca propia, Irrepetibles, clienta; no «usuario», «ítem» ni «dashboard». Datos de ejemplo inventados; ninguna cifra de 3B en pantalla sin fuente.

## Colors

El lienzo es blanco. El rojo comunica marca y acción; la tinta escribe; los grises, teñidos de tinta, estructuran. Medido en tiendas3b.com el 18-nov-2026: rojo `#E31B23`, tinta `#04211F`, marino `#1C244B`, verde de resalte `#4BD811`.

| Para | Usa | Nunca |
|---|---|---|
| Página y tarjetas | `background`, `surface` | grises de fondo «para separar» |
| Texto, de más a menos importante | `text-primary`, `text-secondary`, `text-tertiary`, `text-muted` | `text-muted` sobre `muted` |
| La acción principal | `primary` con `on-primary`; hover `primary-hover`; presionado `primary-active` | dos rellenos rojos en una vista |
| Enlaces | `link`, siempre subrayado | `brand-500` como texto chico |
| Estatus | `success`, `warning`, `danger`, `info` sobre su `-bg`, con punto y palabra | color sin palabra |
| Foco | `focus`, 2 px sólidos a 2 px del control | quitar el contorno |
| Resalte verde | `highlight` solo sobre `ink-900` (8.96:1) | sobre rojo (2.50:1) o blanco (1.89:1) |
| Gráficas | `chart-1`…`chart-5`; `chart-focus` solo para la serie que importa | tintes de rojo por serie |

Contraste: 36 pares calculados con WCAG 2.x, cero fallan. Los más justos: `on-primary` sobre `primary` 4.72:1, `text-muted` sobre `input-bg` 4.83:1, `border-strong` sobre blanco 3.34:1. Sin degradados. **Un solo tema, claro: no se usa modo oscuro ni la clase `dark`.**

## Typography

Dos voces. **Montserrat** (la familia del sitio de 3B) habla por la marca: títulos `h1`–`h3`, `display` y cifras (`figure`), pesos 700–900. **Geist** hace el trabajo: cuerpo, etiquetas, tablas. **Geist Mono** para SKU, folios y números de tienda.

- Cuerpo `body` (16 px) en celular; `body-compact` (14 px) en tablas de escritorio. Piso: `caption`, 12 px.
- Jerarquía con tamaño, peso y color a la vez: valor 600 `text-primary`, etiqueta 500 `text-secondary`, meta 400 `text-tertiary`.
- Montserrat nunca en párrafos ni en celdas: es ancha y cansa. Mayúsculas solo en `display`.
- Toda cifra con `tabular-nums`.
- Las tres fuentes van autoalojadas (`app/fonts/` y el paquete `geist`, licencia OFL). Nunca se carga Google Fonts.

## Layout

- Rejilla de 4 px: solo los pasos `spacing.1`…`spacing.12`. Relleno de tarjeta 16; entre grupos 24; entre secciones 32.
- Dos densidades que no se mezclan en una pantalla: **táctil** (control 44, fila 52, cuerpo 16) y **compacta** (control 36, fila 36, cuerpo 14, solo escritorio con puntero).
- Celular: una columna, margen 16. Escritorio: contenido a 1,200 px máximo, margen 24.
- Primero celular si el usuario está de pie en una tienda.

## Elevation & Depth

Profundidad por bordes. Tarjetas, listas y barras se separan con `border` (tinta al 12 %), sin sombra. La única sombra, `0 8px 24px rgba(4,33,31,.14)`, es para diálogos, menús y hojas inferiores. Movimiento: 150 ms en botones y filas, 220 ms en menús y diálogos, curva `cubic-bezier(.2,0,0,1)`, solo `opacity` y `transform`, sin rebotes; con `prefers-reduced-motion` se quita el desplazamiento.

## Shapes

Radios chicos, como una caja: `sm` 4 px (casillas), `md` 6 px (botones y campos), `lg` 8 px (tarjetas, listas, avisos), `xl` 12 px (diálogos, hojas), `full` solo en chips de estatus. Iconos: Lucide (`lucide-react`), trazo 2, 20 px junto a texto y 24 px solos; un botón de solo icono lleva `aria-label`. Nunca emojis como iconos.

## Components

| Componente | Qué es | Reglas que no se rompen |
|---|---|---|
| Botón | Dispara una acción | Primario uno por vista. Destructivo en contorno `danger`, nunca relleno rojo, y confirma en diálogo. Alto 44 en celular. |
| Campo | Captura un dato | Etiqueta visible arriba; error junto al campo con causa y salida; texto a 16 px; nunca bloquear pegar. |
| Estatus | Estado de una cosa | Punto + palabra, siempre visible. Los nombres de estatus salen de un catálogo único en `lib/contrato`. |
| Cifra | El número de la pantalla | `figure` con `tabular-nums`. El subrayado rojo va bajo UNA cifra por vista, la que pide acción. |
| Fila | Una cosa por renglón | 52 px tocable; nombre, SKU en mono, cantidad a la derecha, estatus. Nombre cortado lleva `title`. |
| Aviso | Algo que pasó y qué hacer | Contorno completo del tono, nunca franja a la izquierda. `role="alert"` para errores. |
| Banda | Franja de marca con un dato | Roja con texto blanco, o de tinta con resalte verde. Una por pantalla como máximo. |
| Vacío | Lugar sin datos | Qué va a aparecer y una sola acción. Sin ilustración. |
| Encabezado | Barra superior | Nombre del producto en Montserrat y «Prototipo para Tiendas 3B» en texto. Sin logotipo de 3B salvo archivo oficial de los organizadores. |

**En el código (Next.js + Tailwind v4 + shadcn).** El tema vive en `app/globals.css`; los componentes de `components/ui/` ya lo toman. Usa siempre la clase semántica:

| Token | Clase |
|---|---|
| `background` / `text-primary` | `bg-background text-foreground` |
| `primary` / `on-primary` | `bg-primary text-primary-foreground`; hover `hover:bg-primary-hover` |
| `surface-2` | `bg-secondary` o `bg-surface-2` |
| `muted` / `text-secondary` | `bg-muted text-muted-foreground` |
| `text-tertiary` / `text-muted` | `text-text-tertiary` / `text-text-muted` |
| `danger` | `text-destructive` o `text-danger`; fondo `bg-danger-bg` |
| `success`, `warning`, `info` | `text-success bg-success-bg`, `text-warning bg-warning-bg`, `text-info bg-info-bg` |
| `highlight`, `brand-*`, `ink-*` | `text-highlight`, `bg-brand-500`, `bg-ink-900`… |
| `link` | `text-link underline` |
| `border-strong` / `focus` | `border-input` / `ring-ring` |
| Montserrat / Geist / Geist Mono | `font-heading` / `font-sans` / `font-mono` (`h1`–`h3` ya van en Montserrat) |
| Radios | control `rounded-lg` (6 px) · tarjeta `rounded-xl` (8 px) · diálogo `rounded-2xl` (12 px) · chip `rounded-full` |

Pendiente en la misión `U0` (carril UI): botón y campo de shadcn a 44 px en celular, hover del primario a `primary-hover` (hoy baja opacidad), variante destructiva en contorno, y la página `/tema` con todos los componentes.

## Do's and Don'ts

- Do: una acción roja por vista; el resto, tinta sobre blanco.
- Do: subrayar en rojo la única cifra que pide acción.
- Do: cajas con borde fino y radios chicos.
- Do: estados vacío, cargando (esqueleto en `muted`) y error en cada pantalla del camino de la demo.
- Don't: usar el logotipo de 3B, dibujar una imitación o copiar sus banners.
- Don't: verde sobre rojo; rojo de acción para errores; color sin palabra.
- Don't: degradados, sombras en tarjetas, franja de color a la izquierda, tres tarjetas de métrica iguales por costumbre, emojis.
- Don't: Montserrat en párrafos; texto por debajo de 12 px; controles táctiles por debajo de 44 px.
- Don't: inventar un color, un radio o un estatus en una pantalla: se agrega aquí primero.
