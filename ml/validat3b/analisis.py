"""D2 · análisis de errores del motor Validat3B.

Recalcula decidir() sobre extracciones.json, lo compara con resultados.json y
escribe un reporte con costo, matriz, errores más caros, lecturas por clase y
costo por visita. Solo usa biblioteca estándar y los módulos del repo.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable

from ml.validat3b.contrato import Captura, Extraccion
from ml.validat3b.decidir import decidir

DECISIONES = ("aprobada", "rechazada", "revision_manual")

# Costo PESIMISTA. Para real revision_manual la regla oficial no está: SUPUESTO.
COSTO = {
    "aprobada":        {"aprobada": 0,  "rechazada": 3,  "revision_manual": 1},
    "rechazada":       {"aprobada": 10, "rechazada": 0,  "revision_manual": 1},
    "revision_manual": {"aprobada": 10, "rechazada": 3,  "revision_manual": 1},
}

CAMPOS: list[tuple[str, Callable[[Extraccion], Any]]] = [
    ("nitidez_producto", lambda e: e.producto.nitidez),
    ("encuadre", lambda e: e.producto.encuadre),
    ("varios_productos", lambda e: e.producto.varios_productos),
    ("foto_de_pantalla", lambda e: e.producto.foto_de_pantalla),
    ("marca_presente", lambda e: bool(e.producto.marca and e.producto.marca.strip())),
    ("descripcion_presente", lambda e: bool(e.producto.descripcion and e.producto.descripcion.strip())),
    ("contenido_leido", lambda e: e.producto.contenido_cantidad is not None),
    ("hay_etiqueta", lambda e: e.etiqueta.hay_etiqueta),
    ("etiqueta_legible", lambda e: e.etiqueta.legible),
    ("precio_leido", lambda e: e.etiqueta.precio is not None),
    ("tipo_precio", lambda e: e.etiqueta.tipo_precio),
    ("otros_precios", lambda e: len(e.etiqueta.otros_precios) > 0),
]


def costo(real: str, pred: str) -> int:
    return COSTO[real][pred]


def pct(n: int, d: int) -> str:
    return f"{n / d:.2%}" if d else "n/a"


def cargar_capturas(ruta: str | Path) -> dict[str, dict[str, str]]:
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        return {fila["capture_id"]: fila for fila in csv.DictReader(f)}


def a_captura(fila: dict[str, str]) -> Captura:
    return Captura(**{k: (v if v != "" else None) for k, v in fila.items() if k in Captura.model_fields})


def cargar_extracciones(ruta: str | Path) -> dict[str, Extraccion]:
    with open(ruta, encoding="utf-8") as f:
        return {e["capture_id"]: Extraccion(**e) for e in json.load(f)}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="D2 · análisis de errores Validat3B")
    p.add_argument("--resultados", default="salidas/resultados.json")
    p.add_argument("--extracciones", default="salidas/extracciones.json")
    p.add_argument("--capturas", default="datos/privado/metadatos/capturas.csv")
    p.add_argument("--salida", default="salidas/analisis.md")
    args = p.parse_args(argv)

    filas = cargar_capturas(args.capturas)
    ext = cargar_extracciones(args.extracciones)
    with open(args.resultados, encoding="utf-8") as f:
        res = {r["capture_id"]: r for r in json.load(f)}

    ids = [cid for cid in filas if cid in ext]
    faltan = [cid for cid in filas if cid not in ext]
    real = {cid: filas[cid]["decision_esperada"] for cid in ids}
    pred = {cid: decidir(a_captura(filas[cid]), ext[cid]).decision for cid in ids}
    costos = {cid: costo(real[cid], pred[cid]) for cid in ids}
    coinciden = sum(1 for cid in ids if res.get(cid, {}).get("decision") == pred[cid])

    total = sum(costos.values())
    base_manual = sum(costo(real[c], "revision_manual") for c in ids)
    base_aprobar = sum(costo(real[c], "aprobada") for c in ids)
    base_rechazar = sum(costo(real[c], "rechazada") for c in ids)
    aprob = [c for c in ids if pred[c] == "aprobada"]
    falsas = [c for c in aprob if real[c] != "aprobada"]
    ok_aprob = len(aprob) - len(falsas)

    L: list[str] = []
    L.append("# Análisis D2 · motor Validat3B")
    L.append("")
    L.append(f"- Resultados de referencia: `{args.resultados}`")
    L.append(f"- Extracciones: `{args.extracciones}`")
    L.append(f"- Capturas evaluadas: {len(ids)} (sin extracción: {len(faltan)})")
    L.append(f"- decidir() coincide con resultados.json en {coinciden} de {len(ids)} capturas")
    L.append("- Costo con real revision_manual = SUPUESTO (pesimista)")
    L.append("")

    L.append("## 1. Costo y precisión")
    L.append("")
    L.append("| Línea | Costo pesimista |")
    L.append("|---|---|")
    L.append(f"| decidir() (reglas actuales) | {total} |")
    L.append(f"| todo revision_manual | {base_manual} |")
    L.append(f"| todo aprobado | {base_aprobar} |")
    L.append(f"| todo rechazado | {base_rechazar} |")
    L.append("")
    L.append(f"Aprobadas: {len(aprob)} · falsas: {len(falsas)} · precisión: {pct(ok_aprob, len(aprob))} (mínimo 97 %)")
    L.append("")

    mat = Counter((real[c], pred[c]) for c in ids)
    L.append("## 2. Matriz real × predicha")
    L.append("")
    L.append("| real \\ pred | " + " | ".join(DECISIONES) + " |")
    L.append("|---|---|---|---|")
    for r_ in DECISIONES:
        L.append(f"| {r_} | " + " | ".join(str(mat[(r_, p_)]) for p_ in DECISIONES) + " |")
    L.append("")

    L.append("## 3. Costo por par (real → predicha)")
    L.append("")
    L.append("| real → predicha | n | costo total |")
    L.append("|---|---|---|")
    for (r_, p_), n in sorted(mat.items()):
        L.append(f"| {r_} → {p_} | {n} | {costo(r_, p_) * n} |")
    L.append("")

    L.append("## 4. Los 20 errores más caros, con lo que leyó el modelo")
    L.append("")
    errores = sorted((c for c in ids if costos[c] > 0), key=lambda c: (-costos[c], c))[:20]
    for cid in errores:
        e = ext[cid]
        f = filas[cid]
        L.append(f"### {cid} · real {real[cid]} → pred {pred[cid]} · costo {costos[cid]}")
        L.append(f"- Motivo real: {f['motivo_rechazo'] or '—'}")
        L.append(
            f"- Producto leído: marca {e.producto.marca} · descripción {e.producto.descripcion} · "
            f"contenido {e.producto.contenido_cantidad} {e.producto.contenido_unidad or ''}"
        )
        L.append(
            f"- Foto: nitidez {e.producto.nitidez} · encuadre {e.producto.encuadre} · "
            f"varios {e.producto.varios_productos}"
        )
        L.append(
            f"- Etiqueta: texto «{e.etiqueta.texto_producto}» · precio {e.etiqueta.precio} · "
            f"tipo {e.etiqueta.tipo_precio} · otros {e.etiqueta.otros_precios}"
        )
        L.append(
            f"- Referencia en metadatos: rango {f.get('min_product_price') or '—'}–"
            f"{f.get('max_product_price') or '—'} · capture_price {f.get('capture_price') or '—'}"
        )
        L.append(f"- Explicación de decidir(): {decidir(a_captura(f), e).explicacion}")
        L.append("")

    L.append("## 5. Lecturas por clase real (cuántas capturas de cada clase tienen cada valor)")
    L.append("")
    for nombre, fn in CAMPOS:
        valores = sorted({str(fn(ext[c])) for c in ids})
        L.append(f"### {nombre}")
        L.append("")
        L.append("| valor | " + " | ".join(DECISIONES) + " |")
        L.append("|---|---|---|---|")
        for valor in valores:
            celdas = [
                str(sum(1 for c in ids if real[c] == clase and str(fn(ext[c])) == valor))
                for clase in DECISIONES
            ]
            L.append(f"| {valor} | " + " | ".join(celdas) + " |")
        L.append("")

    L.append("## 6. Costo por visita (facade_url)")
    L.append("")
    L.append("| visita | n | costo |")
    L.append("|---|---|---|")
    por_visita: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for c in ids:
        vis = filas[c].get("facade_url") or "(sin visita)"
        por_visita[vis][0] += 1
        por_visita[vis][1] += costos[c]
    for vis, (n, co) in sorted(por_visita.items(), key=lambda kv: -kv[1][1]):
        L.append(f"| {vis} | {n} | {co} |")
    L.append("")

    salida = Path(args.salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"Reporte escrito en {salida}")
    print(f"Costo decidir(): {total} · aprobadas: {len(aprob)} · falsas: {len(falsas)} · precisión: {pct(ok_aprob, len(aprob))}")
    print(f"decidir() = resultados.json en {coinciden} de {len(ids)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
