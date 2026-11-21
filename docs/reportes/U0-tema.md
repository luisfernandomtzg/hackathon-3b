U0 — componentes al sistema Tarima y página /tema · rama carril/ui-sp0-tema · cuelga de 2a6606a (la misión decía cdc2c6c; desciende de él, solo agrega docs) · commit ver PR · modelo Sonnet 5.5 · esfuerzo no visible para mí · ~25 min
Hecho: button.tsx → default h-11, sm h-9, icon size-11, icon-sm size-9; hover/active del primario con primary-hover/primary-active; destructivo en contorno danger sin relleno; sin clases dark:.
Hecho: input.tsx → h-11, bg-input-bg, text-base siempre, sin dark:.
Hecho: components/shell.tsx (Encabezado 56 px, «Prototipo» en font-heading + «Prototipo para Tiendas 3B», sin logotipo; main 16/24 de margen, máx. 1,200 px) y app/tema/page.tsx con Botón, Campo, Estatus, Cifra, Fila, Aviso, Banda, Vacío, Cargando y Error.
Prueba de cierre: npm run lint → sin salida (ok) · npm run build → compiló, TypeScript ok, rutas / /salud /tema generadas · git diff origin/main (solo líneas agregadas) | grep "#hex|bg-white|gray-|neutral-|red-|dark:" → vacío.
No hecho / simulado: no medí 44 px en navegador (sin Playwright local); se respalda en h-11 y lo confirma Fer en su celular. URL de vista previa de Vercel y revisión de /salud («base ok») pendientes: aparecen al abrir el PR. Datos de la página inventados.
Archivos fuera de mi carril que toqué: ninguno (button.tsx e input.tsx están nombrados en la misión).
¿Tocó la base?: no
Necesito de otro carril: nada
