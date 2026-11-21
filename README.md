# Validat3B — motor de validación de capturas de precio

Hackatón Tiendas 3B · 21-nov-2026 · Reto 2 (Validat3B) · Equipo: Fer, Mau, Sergio, Mauski y Alan.

Por cada captura de campo (foto de fachada, foto del producto y foto de la etiqueta de precio) el motor decide
`aprobada`, `rechazada` o `revision_manual`, con su `reason_code`, nivel de confianza, precio detectado y una
explicación en español. El modelo solo **lee**; las decisiones las toman reglas deterministas.

## Cómo decide

1. **Señales locales, sin tokens** (`local.py`): código de barras leído de la foto, nitidez, fachadas repetidas.
2. **Lectura** (`extraer.py`): una llamada a `claude-haiku-5-5` en el endpoint asignado, con la foto del producto y la de
   la etiqueta. Devuelve marca, descripción, contenido, precio, y qué tan cerca y nítido sale el letrero de precio.
3. **Reglas** (`decidir.py`): comparan lo leído contra el producto esperado. La etiqueta lejana o borrosa se rechaza;
   sin letrero cerca y nítido no se aprueba.
4. **Compuertas** (`compuerta.py`): código de barras que no coincide o etiqueta poco nítida → revisión.
5. **Consenso** (`consenso.py`): solo se aprueba si tres lecturas independientes coinciden.

## Resultado medido (100 capturas de desarrollo)

16 aprobadas · 0 aprobadas falsas · costo operativo 84 (pesimista) / 27 (optimista) contra 100 / 67 de revisar todo ·
55 de 100 sin persona · 3,192 tokens por captura · JSON válido 100 de 100. Fuentes en `docs/pitch/cifras.md`.

## Instalar

```
python -m venv .venv
.venv\Scripts\pip install -r ml/requirements.txt        (Linux/Mac: .venv/bin/pip)
```

Pon la llave del endpoint en `.env.local` como `FOUNDRY_API_KEY=<llave>` (no se versiona).

## Correr

Entrega de un lote (set ciego): localiza `capturas.csv` y las imágenes dentro de la carpeta, corre el motor, valida la
salida y escribe `resultados.json` (lista), `por_captura/<capture_id>.json` (un archivo por captura), `resultados.csv`
y `resumen.txt`.

```
.venv\Scripts\python -m ml.validat3b.entregar --datos <carpeta del lote> --salida entrega/
```

Con etiquetas (desarrollo): correr, medir y ver.

```
.venv\Scripts\python -m ml.validat3b.correr  --datos datos/privado --salida salidas/resultados.json
.venv\Scripts\python -m ml.validat3b.evaluar --resultados salidas/resultados.json
.venv\Scripts\python -m ml.validat3b.visor   --datos datos/privado --resultados salidas/resultados.json --salida salidas/visor.html
```

Prueba de humo sin gastar tokens: agrega `--sin-modelo` a `correr`. Pruebas: `python -m unittest discover -s ml/validat3b -t . -p "test_*.py"`.

## Qué hay en el repositorio

- `ml/validat3b/` — el motor (Python). Es lo que se entrega.
- `docs/entrega/ficha-tecnica.html` — ficha técnica de una página.
- `docs/pitch/` — guion, láminas y tabla de cifras con su fuente.
- `app/`, `components/`, `lib/`, `supabase/` — andamiaje web previo al evento (Next.js). **No forma parte del motor** ni de la demo.

## Reglas del reto que este repositorio respeta

- Solo se usa el endpoint asignado; lo demás (lectura de códigos de barras, nitidez, reglas) corre en la laptop.
- Los datos de 3B no se versionan: `datos/privado/`, `salidas/` y `entrega/` están en `.gitignore`.
- Las decisiones del set ciego salen del motor, sin revisión humana.

Asistentes de IA usados para programar: Claude (Anthropic) y Gemini (Google).
