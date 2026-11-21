"""calibrar: aplica decidir() a las lecturas reales y muestra dónde se equivoca.

Uso:
  python -m ml.validat3b.calibrar --extracciones salidas/extracciones.json --capturas datos/privado/metadatos/capturas.csv
"""
import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Optional

from ml.validat3b.contrato import Captura, Extraccion
from ml.validat3b.decidir import decidir_con_regla
from ml.validat3b.evaluar import costo


def _float(s: Optional[str]) -> Optional[float]:
    if s is None or str(s).strip() == "":
        return None
    return float(s)


def _int(s: Optional[str]) -> Optional[int]:
    v = _float(s)
    return None if v is None else int(v)


def a_captura(fila: dict) -> Captura:
    """Convierte una fila de capturas.csv (tolera BOM y cadenas vacías) en Captura."""
    f = {k.lstrip("﻿"): (v if v != "" else None) for k, v in fila.items()}
    return Captura(
        capture_id=f["capture_id"], capture_store_name=f["capture_store_name"] or "",
        capture_date=f["capture_date"] or "", capture_barcode=f["capture_barcode"] or "",
        capture_price=_float(f["capture_price"]), capture_brand=f["capture_brand"],
        id_product=_int(f["id_product"]) or 0, product_name=f["product_name"] or "",
        product_barcode=f["product_barcode"] or "",
        product_price=_float(f["product_price"]),
        min_product_price=_float(f["min_product_price"]), max_product_price=_float(f["max_product_price"]),
        unit_product=f["unit_product"], unit_quantity_product=_float(f["unit_quantity_product"]),
        product_group=f["product_group"], product_line=f["product_line"],
        facade_file=f["facade_file"] or "", product_file=f["product_file"] or "", shelf_file=f["shelf_file"] or "",
        decision_esperada=f["decision_esperada"], motivo_rechazo=f["motivo_rechazo"],
    )


def calibrar(extracciones: list[Extraccion], capturas: dict[str, Captura], escenario: str = "pesimista") -> dict:
    tabla: Counter = Counter()
    falsas, rechazadas_validas = [], []
    costo_total = 0
    aprobadas = aciertos_aprob = 0
    for x in extracciones:
        cap = capturas[x.capture_id]
        res, regla = decidir_con_regla(cap, x)
        real = cap.decision_esperada or ""
        tabla[(regla, real, res.decision)] += 1
        costo_total += costo(real, res.decision, escenario)
        if res.decision == "aprobada":
            aprobadas += 1
            if real == "aprobada":
                aciertos_aprob += 1
            else:
                falsas.append((cap, x, res, regla))
        if real == "aprobada" and res.decision == "rechazada":
            rechazadas_validas.append((cap, x, res, regla))
    return {
        "tabla": tabla, "falsas": falsas, "rechazadas_validas": rechazadas_validas,
        "costo": costo_total, "aprobadas": aprobadas, "aciertos_aprob": aciertos_aprob,
        "total": len(extracciones),
    }


def imprimir(r: dict) -> None:
    print(f"Capturas: {r['total']} · costo total ({'pesimista'}): {r['costo']}")
    pct = (r["aciertos_aprob"] / r["aprobadas"] * 100) if r["aprobadas"] else 0.0
    print(f"Aprobadas: {r['aprobadas']} · correctas: {r['aciertos_aprob']} · precisión {pct:.1f} % (mínimo 97 %)\n")

    print("(a) Regla que disparó × decisión real × decisión del motor:")
    for (regla, real, pred), n in sorted(r["tabla"].items()):
        print(f"   regla {regla:>2} · real {real or '—':<15} → motor {pred:<15} {n}")
    print()

    print(f"(b) Aprobadas falsas: {len(r['falsas'])}")
    for cap, x, res, regla in r["falsas"]:
        print(f"   {cap.capture_id} · real {cap.decision_esperada} · regla {regla} · "
              f"marca «{x.producto.marca}» vs «{cap.capture_brand}» · "
              f"desc «{x.producto.descripcion}» vs «{cap.product_name}» · "
              f"contenido {x.producto.contenido_cantidad} {x.producto.contenido_unidad} vs "
              f"{cap.unit_quantity_product} {cap.unit_product}")
    print()

    print(f"(c) Válidas rechazadas: {len(r['rechazadas_validas'])}")
    for cap, x, res, regla in r["rechazadas_validas"]:
        print(f"   {cap.capture_id} · regla {regla} · {res.reason_code} · {res.explicacion}")
    print()

    print("(d) Costo por escenario: ver evaluar.py (pesimista y optimista). Tabla: acierto 0 · revisión 1 · rechazar válida 3 · aprobar inválida 10.")


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Calibra decidir() contra lecturas reales.")
    ap.add_argument("--extracciones", required=True)
    ap.add_argument("--capturas", required=True)
    ap.add_argument("--escenario", default="pesimista", choices=["pesimista", "optimista"])
    args = ap.parse_args(argv)

    with open(args.capturas, encoding="utf-8-sig", newline="") as f:
        capturas = {fila["capture_id"].strip(): a_captura(fila) for fila in csv.DictReader(f)}
    with open(args.extracciones, encoding="utf-8") as f:
        extracciones = [Extraccion(**e) for e in json.load(f)]
    extracciones = [x for x in extracciones if x.capture_id in capturas]

    imprimir(calibrar(extracciones, capturas, args.escenario))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
