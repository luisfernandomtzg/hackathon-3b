"""D2 · clasificador experimental (regresión logística, validación por visita).

Estima P(real = aprobada) con señales de la lectura del modelo y de locales.csv.
Validación cruzada por grupos: facade_url es el grupo, así que una visita nunca
está en entrenamiento y prueba a la vez. Solo se reportan predicciones fuera de
muestra (out-of-fold).

Experimento: no se conecta al motor. La decisión de usarlo es de Fer.
Limitación: el clasificador solo decide aprobar o no aprobar; lo que no aprueba
cuenta como revision_manual (costo 1). No modela rechazos, así que su costo no
es comparable 1 a 1 con decidir().

Uso:
    python -m ml.validat3b.clasificador --extracciones salidas/extracciones.json \
        --locales salidas/locales.csv --capturas datos/privado/metadatos/capturas.csv \
        --salida salidas/clasificador.md
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from ml.validat3b.contrato import Captura, Extraccion
from ml.validat3b.decidir import decidir
from ml.validat3b.normalizar import parecido

COSTO = {
    "aprobada":        {"aprobada": 0,  "rechazada": 3,  "revision_manual": 1},
    "rechazada":       {"aprobada": 10, "rechazada": 0,  "revision_manual": 1},
    "revision_manual": {"aprobada": 10, "rechazada": 3,  "revision_manual": 1},
}

NOMBRES = [
    "nitida", "dudosa", "borrosa",
    "cercano", "medio", "lejano",
    "varios_productos", "foto_de_pantalla",
    "marca_presente", "descripcion_presente", "contenido_leido",
    "parecido_marca", "parecido_descripcion",
    "hay_etiqueta", "etiqueta_legible", "precio_leido",
    "oferta", "otros_precios", "precio_en_rango", "texto_etiqueta_presente",
    "log_nitidez_producto", "log_nitidez_etiqueta",
]


def a_captura(fila: dict[str, str]) -> Captura:
    return Captura(**{k: (v if v != "" else None) for k, v in fila.items() if k in Captura.model_fields})


def cargar_capturas(ruta: str | Path) -> dict[str, dict[str, str]]:
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        return {fila["capture_id"]: fila for fila in csv.DictReader(f)}


def cargar_locales(ruta: str | Path) -> dict[str, dict[str, str]]:
    with open(ruta, encoding="utf-8", newline="") as f:
        return {fila["capture_id"]: fila for fila in csv.DictReader(f)}


def cargar_extracciones(ruta: str | Path) -> dict[str, Extraccion]:
    with open(ruta, encoding="utf-8") as f:
        return {e["capture_id"]: Extraccion(**e) for e in json.load(f)}


def vector(captura: Captura, e: Extraccion, loc: dict[str, str]) -> list[float]:
    p, et = e.producto, e.etiqueta
    marca = p.marca or ""
    desc = p.descripcion or ""
    par_marca = parecido(marca, captura.capture_brand) if (marca and captura.capture_brand) else 0.0
    par_desc = parecido(desc, captura.product_name) if (desc and captura.product_name) else 0.0
    en_rango = 0.0
    if et.precio is not None and captura.min_product_price and captura.max_product_price:
        en_rango = float(captura.min_product_price <= et.precio <= captura.max_product_price)
    nit_p = float(loc.get("nitidez_producto") or 0)
    nit_e = float(loc.get("nitidez_etiqueta") or 0)
    return [
        float(p.nitidez == "nitida"), float(p.nitidez == "dudosa"), float(p.nitidez == "borrosa"),
        float(p.encuadre == "cercano"), float(p.encuadre == "medio"), float(p.encuadre == "lejano"),
        float(p.varios_productos), float(p.foto_de_pantalla),
        float(bool(marca.strip())), float(bool(desc.strip())), float(p.contenido_cantidad is not None),
        float(par_marca), float(par_desc),
        float(et.hay_etiqueta), float(et.legible), float(et.precio is not None),
        float(et.tipo_precio == "oferta"), float(len(et.otros_precios) > 0), en_rango,
        float(bool(et.texto_producto and et.texto_producto.strip())),
        float(np.log1p(nit_p)), float(np.log1p(nit_e)),
    ]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="D2 · clasificador experimental Validat3B")
    p.add_argument("--extracciones", default="salidas/extracciones.json")
    p.add_argument("--locales", default="salidas/locales.csv")
    p.add_argument("--capturas", default="datos/privado/metadatos/capturas.csv")
    p.add_argument("--salida", default="salidas/clasificador.md")
    args = p.parse_args(argv)

    filas = cargar_capturas(args.capturas)
    ext = cargar_extracciones(args.extracciones)
    loc = cargar_locales(args.locales)
    ids = sorted(c for c in filas if c in ext and c in loc)
    n = len(ids)

    X = np.array([vector(a_captura(filas[c]), ext[c], loc[c]) for c in ids], dtype=float)
    y = np.array([1 if filas[c]["decision_esperada"] == "aprobada" else 0 for c in ids])
    visitas = [filas[c].get("facade_url") or c for c in ids]
    _, grupos = np.unique(visitas, return_inverse=True)
    n_splits = min(5, len(set(grupos.tolist())))

    modelo = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000, class_weight="balanced"))
    oof = np.zeros(n)
    for tr, te in GroupKFold(n_splits=n_splits).split(X, y, grupos):
        modelo.fit(X[tr], y[tr])
        oof[te] = modelo.predict_proba(X[te])[:, 1]
    auc = roc_auc_score(y, oof)

    reglas = {c: decidir(a_captura(filas[c]), ext[c]).decision for c in ids}
    costo_reglas = sum(COSTO[filas[c]["decision_esperada"]][reglas[c]] for c in ids)

    tabla = []
    for t in np.round(np.arange(0.50, 0.995, 0.01), 2):
        aprueba = oof >= t
        n_ap = int(aprueba.sum())
        ok = int((aprueba & (y == 1)).sum())
        falsas = n_ap - ok
        costo_t = 10 * falsas + (n - n_ap)
        precision = ok / n_ap if n_ap else None
        tabla.append((float(t), n_ap, ok, falsas, precision, costo_t))

    seguras = [r for r in tabla if r[3] == 0 and r[1] > 0]
    mejor_segura = max(seguras, key=lambda r: r[1]) if seguras else None
    mejor_costo = min(tabla, key=lambda r: (r[5], -r[1]))

    L: list[str] = []
    L.append("# Clasificador experimental · D2")
    L.append("")
    L.append(f"- Capturas: {n} · visitas (grupos): {len(set(grupos.tolist()))} · pliegues: {n_splits}")
    if n < 150:
        L.append(f"- AVISO: muestra pequeña (n={n}). Cualquier umbral es tentativo.")
    L.append(f"- Validación: GroupKFold por facade_url. AUC fuera de muestra: {auc:.3f}")
    L.append(f"- Costo de decidir() (pesimista, mismas capturas): {costo_reglas}")
    L.append(f"- Costo de revisar todo a mano: {n}")
    L.append("- Limitación: el clasificador solo aprueba o no aprueba; lo que no aprueba cuenta como revision_manual.")
    L.append("")
    if mejor_segura:
        L.append(
            f"- Umbral sin aprobadas falsas con más aprobadas: t={mejor_segura[0]:.2f} "
            f"(aprobadas {mejor_segura[1]}, costo {mejor_segura[5]})"
        )
    else:
        L.append("- Ningún umbral entre 0.50 y 0.99 produce cero aprobadas falsas.")
    L.append(f"- Umbral de costo mínimo: t={mejor_costo[0]:.2f} (costo {mejor_costo[5]}, aprobadas {mejor_costo[1]}, falsas {mejor_costo[3]})")
    L.append("")
    L.append("## Tabla umbral → costo (fuera de muestra)")
    L.append("")
    L.append("| umbral | aprobadas | correctas | falsas | precisión | costo |")
    L.append("|---|---|---|---|---|---|")
    for t, n_ap, ok, falsas, precision, costo_t in tabla:
        prec = f"{precision:.2%}" if precision is not None else "n/a"
        L.append(f"| {t:.2f} | {n_ap} | {ok} | {falsas} | {prec} | {costo_t} |")
    L.append("")

    modelo.fit(X, y)
    coef = modelo[-1].coef_[0]
    orden = np.argsort(-np.abs(coef))
    L.append("## Coeficientes (modelo entrenado con todas las capturas, solo referencia)")
    L.append("")
    L.append("| señal | coeficiente |")
    L.append("|---|---|")
    for i in orden:
        L.append(f"| {NOMBRES[i]} | {coef[i]:+.3f} |")
    L.append("")

    salida = Path(args.salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"Reporte escrito en {salida}")
    print(f"AUC fuera de muestra: {auc:.3f} · costo decidir(): {costo_reglas}")
    print(f"Umbral costo mínimo: t={mejor_costo[0]:.2f} costo {mejor_costo[5]} falsas {mejor_costo[3]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
