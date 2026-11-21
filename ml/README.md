Carril **Datos e IA**. Python por lotes. Sus salidas son archivos; la app no llama a Python en vivo.

## Validat3B — instalar y correr

1. `python -m venv .venv` y `.venv\Scripts\pip install -r ml/requirements.txt` (Linux/Mac: `.venv/bin/`).
2. Pon `FOUNDRY_API_KEY=<llave>` en `.env.local` (no se versiona).
3. Deja los datos en `datos/privado/` (`metadatos/capturas.csv` e `imagenes/imagenes/`).
4. Sin modelo (prueba de humo): `.venv\Scripts\python -m ml.validat3b.correr --datos datos/privado --salida salidas/resultados.json --sin-modelo`
5. Con modelo: quita `--sin-modelo` (opciones: `--limite N`, `--hilos 4`, `--mapa-codigos mapa.json`).
6. Salidas en `salidas/`: `resultados.json` (oficial), `resultados.csv`, `extracciones.json`, `tokens.csv`, `cache/` (una segunda corrida usa el caché y gasta 0 tokens).
