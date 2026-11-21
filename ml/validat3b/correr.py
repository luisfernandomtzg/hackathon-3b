"""Corrida por lotes: python -m ml.validat3b.correr --datos datos/privado --salida salidas/resultados.json"""
import argparse
import csv
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .cargar import cargar_capturas
from .cliente import Cliente
from .contrato import RC_SIN_LECTURA, Captura, Extraccion, Resultado, Validaciones
try:
    from .decidir import decidir
except ImportError:  # Núcleo aún no entrega decidir.py
    from .decidir_provisional import decidir
from .extraer import extraer, sin_modelo

COLUMNAS = ["capture_id", "decision", "confidence_score", "reason_code", "tienda_fachada", "producto",
            "codigo_barras", "evidencia_precio", "precio_detectado", "codigo_barras_detectado", "explicacion"]


def _respaldo(captura: Captura, motivo: str) -> Resultado:
    return Resultado(capture_id=captura.capture_id, decision="revision_manual", confidence_score=0.0,
                     reason_code=RC_SIN_LECTURA, validaciones=Validaciones(),
                     explicacion=f"Error al procesar la captura; a revisión manual. ({motivo[:120]})")


def procesar(captura: Captura, dir_datos, cliente, usar_modelo: bool):
    """Nunca lanza: cualquier falla deja la captura en revision_manual."""
    ext = None
    try:
        ext = extraer(captura, dir_datos, cliente) if usar_modelo else sin_modelo(captura)
        res = Resultado.model_validate(decidir(captura, ext).model_dump())
    except Exception as e:
        res = _respaldo(captura, f"{type(e).__name__}: {e}")
    return ext, res


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--datos", required=True)
    p.add_argument("--salida", required=True)
    p.add_argument("--limite", type=int)
    p.add_argument("--sin-modelo", action="store_true")
    p.add_argument("--hilos", type=int, default=4)
    p.add_argument("--mapa-codigos")
    a = p.parse_args(argv)

    t0 = time.time()
    datos = Path(a.datos)
    salida = Path(a.salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    mapa = json.loads(Path(a.mapa_codigos).read_text(encoding="utf-8")) if a.mapa_codigos else {}

    capturas = cargar_capturas(datos / "metadatos")
    if a.limite:
        capturas = capturas[: a.limite]
    cliente = None if a.sin_modelo else Cliente(salida.parent)
    with ThreadPoolExecutor(max_workers=max(1, a.hilos)) as ex:
        pares = list(ex.map(lambda c: procesar(c, datos, cliente, not a.sin_modelo), capturas))

    resultados, extracciones = [], []
    for ext, res in pares:
        if res.reason_code in mapa:
            res.reason_code = mapa[res.reason_code]
        resultados.append(res.model_dump(mode="json"))
        if ext is not None:
            extracciones.append(ext.model_dump(mode="json"))

    # validación final de lo que se escribe
    validas = sum(1 for r in resultados if Resultado.model_validate(r))
    salida.write_text(json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")
    (salida.parent / "extracciones.json").write_text(json.dumps(extracciones, ensure_ascii=False, indent=2),
                                                     encoding="utf-8")
    with open(salida.with_suffix(".csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS)
        w.writeheader()
        for r in resultados:
            fila = {k: r.get(k) for k in COLUMNAS}
            fila.update(r["validaciones"])
            w.writerow(fila)

    tok = sum(e["tokens_entrada"] + e["tokens_salida"] for e in extracciones)
    n = len(capturas)
    origenes = {}
    for e in extracciones:
        origenes[e["origen"]] = origenes.get(e["origen"], 0) + 1
    print(f"{n} capturas · {validas} válidas · {tok} tokens")
    print(f"tokens/captura: {tok / n if n else 0:.0f} · origenes: {origenes} · {time.time() - t0:.1f} s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
