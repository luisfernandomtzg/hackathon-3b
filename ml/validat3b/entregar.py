"""Entrega del set ciego en un comando (I4).

    python -m ml.validat3b.entregar --datos <carpeta> --salida entrega/ [--reanudar]

Localiza capturas e imágenes aunque cambien de nombre o anidación, corre el motor, valida la salida
(exactamente un Resultado por capture_id, todos válidos, códigos dentro del mapa) y escribe
`resultados.json` + `resumen.txt`. Si algo falla no borra nada: lo dice y sale con código 1.
"""
import argparse
import csv
import json
import os
import time
from collections import Counter
from pathlib import Path

from . import correr
from .cargar import cargar_capturas, localizar_capturas
from .contrato import RC_SIN_LECTURA, Captura, Resultado, Validaciones
from .extraer import resolver_imagen

MAPA_POR_OMISION = Path(__file__).with_name("mapa_codigos.json")
_EXT = {".jpg", ".jpeg", ".png", ".webp"}


# ---------- (a) localizar -------------------------------------------------------------------------
def localizar_imagenes(datos: Path, capturas: list[Captura]) -> Path:
    """Carpeta raíz R tal que resolver_imagen(R, ruta_relativa) encuentre las fotos."""
    todas = [p for p in datos.rglob("*") if p.suffix.lower() in _EXT]
    if not todas:
        raise FileNotFoundError(f"No hay imágenes (jpg/png) bajo {datos}")
    por_nombre = {}
    for p in todas:
        por_nombre.setdefault(p.name, p)
    candidatos = [datos]
    for c in capturas:
        for rel in (c.product_file, c.shelf_file, c.facade_file):
            hit = por_nombre.get(Path(rel or "").name)
            if hit:
                candidatos += [q for q in hit.parents if datos == q or datos in q.parents]
        if len(candidatos) > 1:
            break
    mejor, mejor_n = None, 0
    for r in dict.fromkeys(candidatos):
        n = sum(1 for c in capturas if resolver_imagen(r, c.product_file))
        if n > mejor_n:
            mejor, mejor_n = r, n
    if mejor is None:
        raise FileNotFoundError("Ninguna ruta de foto del CSV coincide con las imágenes encontradas")
    return mejor


def fotos_faltantes(captura: Captura, raiz: Path) -> list[str]:
    return [n for n, rel in (("fachada", captura.facade_file), ("producto", captura.product_file),
                             ("etiqueta", captura.shelf_file)) if resolver_imagen(raiz, rel) is None]


# ---------- (d) validar ---------------------------------------------------------------------------
def validar(ids_esperados: list[str], resultados: list[dict], codigos_permitidos: set[str] | None) -> list[str]:
    """Lista de problemas (vacía = entrega válida)."""
    problemas = []
    vistos = Counter(r.get("capture_id") for r in resultados)
    for cid in ids_esperados:
        if vistos.get(cid, 0) == 0:
            problemas.append(f"falta el resultado de {cid}")
    for cid, n in vistos.items():
        if n > 1:
            problemas.append(f"{cid} aparece {n} veces")
        if cid not in set(ids_esperados):
            problemas.append(f"resultado de {cid}, que no está en las capturas")
    for r in resultados:
        try:
            Resultado.model_validate(r)
        except Exception as e:
            problemas.append(f"{r.get('capture_id')} no valida contra el contrato ({str(e).splitlines()[0]})")
            continue
        rc = r.get("reason_code")
        if codigos_permitidos is not None and rc is not None and rc not in codigos_permitidos:
            problemas.append(f"{r['capture_id']}: reason_code {rc!r} no está en el mapa oficial")
    return problemas


def _codigos_permitidos(mapa_ruta: Path | None):
    if not mapa_ruta or not mapa_ruta.is_file():
        return None, {}
    m = json.loads(mapa_ruta.read_text(encoding="utf-8"))
    m = m.get("mapa", m) if isinstance(m.get("mapa", m), dict) else m
    return set(m.values()), m


def _sin_lectura(captura_id: str, motivo: str, mapa: dict) -> dict:
    r = Resultado(capture_id=captura_id, decision="revision_manual", confidence_score=0.0,
                  reason_code=RC_SIN_LECTURA, validaciones=Validaciones(),
                  explicacion=f"Falta material de la captura ({motivo}); a revisión manual.")
    d = r.model_dump(mode="json")
    d["reason_code"] = mapa.get(d["reason_code"], d["reason_code"])
    return d


def _filas_tokens(ruta: Path) -> list[list[str]]:
    if not ruta.is_file():
        return []
    with open(ruta, encoding="utf-8", newline="") as f:
        return list(csv.reader(f))[1:]


# ---------- comando -------------------------------------------------------------------------------
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Entrega del set ciego: un comando, una entrega válida")
    ap.add_argument("--datos", required=True)
    ap.add_argument("--salida", default="entrega")
    ap.add_argument("--mapa-codigos", default=None, help=f"por omisión {MAPA_POR_OMISION.name} si existe")
    ap.add_argument("--hilos", type=int, default=4)
    ap.add_argument("--reanudar", action="store_true",
                    help="conserva tokens.csv acumulado de la corrida cortada (el caché de lecturas se reusa siempre)")
    ap.add_argument("--sin-modelo", action="store_true", help="solo para pruebas: no llama al endpoint")
    a = ap.parse_args(argv)
    t0 = time.time()
    datos, salida = Path(a.datos), Path(a.salida)

    # (a) localizar
    try:
        archivo = localizar_capturas(datos)
        capturas = cargar_capturas(archivo)
        raiz = localizar_imagenes(datos, capturas)
    except Exception as e:
        print(f"ERROR: {e}")
        return 2
    ids = [c.capture_id for c in capturas]
    dups = [k for k, n in Counter(ids).items() if n > 1]
    if dups:
        print(f"AVISO: capture_id repetido en el CSV ({len(dups)}): se procesa la primera fila de cada uno")
        vistos, unicas = set(), []
        for c in capturas:
            if c.capture_id not in vistos:
                vistos.add(c.capture_id)
                unicas.append(c)
        capturas, ids = unicas, [c.capture_id for c in unicas]
    print(f"capturas: {archivo} · {len(capturas)} capturas · imágenes: {raiz}")

    # (b) material faltante
    faltan = {c.capture_id: fotos_faltantes(c, raiz) for c in capturas}
    faltan = {k: v for k, v in faltan.items() if v}
    print(f"capturas con fotos faltantes: {len(faltan)} (irán a revision_manual / SIN_LECTURA)")

    # (c) correr el motor
    mapa_ruta = Path(a.mapa_codigos) if a.mapa_codigos else (MAPA_POR_OMISION if MAPA_POR_OMISION.is_file() else None)
    permitidos, mapa = _codigos_permitidos(mapa_ruta)
    print(f"mapa de códigos: {mapa_ruta if permitidos is not None else 'NO HAY (códigos provisionales)'}")
    salida.mkdir(parents=True, exist_ok=True)
    tokens_csv = salida / "tokens.csv"
    if tokens_csv.exists() and not a.reanudar:
        os.replace(tokens_csv, salida / "tokens.prev.csv")
    previas = len(_filas_tokens(tokens_csv))
    resultados_json = salida / "resultados.json"
    argv_correr = ["--datos", str(raiz), "--metadatos", str(archivo), "--salida", str(resultados_json),
                   "--hilos", str(a.hilos)]
    if mapa_ruta and permitidos is not None:
        argv_correr += ["--mapa-codigos", str(mapa_ruta)]
    if a.sin_modelo:
        argv_correr.append("--sin-modelo")
    try:
        correr.main(argv_correr)
    except KeyboardInterrupt:
        print("\nCorte manual. Relanza con --reanudar: lo ya leído está en el caché y no se repite.")
        return 130
    except Exception as e:
        print(f"ERROR al correr el motor: {type(e).__name__}: {e}")
        return 1

    # (d) validar: una por capture_id, material faltante a revisión, códigos del mapa
    resultados = json.loads(resultados_json.read_text(encoding="utf-8"))
    vistos, unicos = set(), []
    for r in resultados:  # correr procesó todas las filas del CSV; con ids repetidos se queda con la primera
        if r["capture_id"] not in vistos:
            vistos.add(r["capture_id"])
            unicos.append(r)
    resultados = unicos
    for i, r in enumerate(resultados):
        if r["capture_id"] in faltan:
            resultados[i] = _sin_lectura(r["capture_id"], "falta foto de " + ", ".join(faltan[r["capture_id"]]), mapa)
    problemas = validar(ids, resultados, permitidos)

    # (e) escribir
    resultados_json.write_text(json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")
    correr.escribir_csv(resultados, resultados_json.with_suffix(".csv"))
    # El reto pide «un JSON por captura»: además de la lista, se deja un archivo por capture_id.
    por_captura = salida / "por_captura"
    por_captura.mkdir(exist_ok=True)
    for viejo in por_captura.glob("*.json"):
        viejo.unlink()
    for r in resultados:
        nombre = "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in str(r["capture_id"]))
        (por_captura / f"{nombre}.json").write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
    nuevas = _filas_tokens(tokens_csv)[previas:]
    tok = sum(int(f[1]) + int(f[2]) for f in nuevas)
    llamadas = sum(1 for f in nuevas if f[4] == "modelo")
    cuentas = Counter(r["decision"] for r in resultados)
    fallos = [r["capture_id"] for r in resultados if "Error al procesar" in r["explicacion"]]
    seg = time.time() - t0
    n = len(resultados)
    lineas = [
        f"capturas: {n} · resultados válidos: {n - sum(1 for p in problemas if 'contrato' in p)}",
        "decisiones: " + " · ".join(f"{k} {cuentas.get(k, 0)}" for k in ("aprobada", "rechazada", "revision_manual")),
        f"tokens totales de esta corrida: {tok} · por captura: {tok / n if n else 0:.0f} · llamadas al modelo: {llamadas}",
        f"segundos: {seg:.1f}",
        f"fotos faltantes: {len(faltan)} · fallos al procesar: {len(fallos)}",
    ]
    if fallos:
        lineas.append("fallaron (a revisión manual): " + ", ".join(fallos))
    if faltan:
        lineas.append("sin fotos completas: " + ", ".join(f"{k} ({'/'.join(v)})" for k, v in faltan.items()))
    lineas.append("VALIDACIÓN: " + ("OK" if not problemas else f"FALLÓ ({len(problemas)} problemas)"))
    lineas += [f"  - {p}" for p in problemas]
    (salida / "resumen.txt").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print("\n".join(lineas))
    return 0 if not problemas else 1  # (f) nada se borra: los archivos quedan para inspección


if __name__ == "__main__":
    raise SystemExit(main())
