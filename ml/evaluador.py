"""Evaluador oficial local para Reto 2 · Validat3B.

Calcula:
- Costo operativo total (matriz 0 / 1 / 3 / 10)
- Precisión de aprobaciones: TP / (TP + FP) (requisito mínimo >= 0.97)
- Porcentaje de JSON válido (requisito mínimo >= 0.99)
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

DECISIONES_VALIDAS = {"aprobada", "rechazada", "revision_manual"}


def calcular_costo_fila(pred: str, real: str) -> int:
    """Devuelve el costo operativo de una captura según la matriz oficial."""
    if pred == "revision_manual":
        return 1
    if pred == real:
        return 0
    if pred == "aprobada" and real != "aprobada":
        return 10  # Falso Positivo (crítico)
    if pred == "rechazada" and real == "aprobada":
        return 3   # Falso Negativo
    # pred == "rechazada" y real == "revision_manual" -> 0 o 1 según criterio; conservador: 1
    return 1


def evaluar_predicciones(
    predicciones: list[dict[str, Any]],
    ground_truth_csv: str | Path = "datos/metadatos/capturas.csv",
) -> dict[str, Any]:
    """Evalúa una lista de predicciones JSON contra el CSV de etiquetas."""
    df_real = pd.read_csv(ground_truth_csv)
    mapa_real = dict(zip(df_real["capture_id"], df_real["decision_esperada"]))

    pred_por_id: dict[str, dict[str, Any]] = {}
    json_validos = 0

    for item in predicciones:
        if not isinstance(item, dict):
            continue
        cid = item.get("capture_id")
        dec = item.get("decision")
        if cid in mapa_real and dec in DECISIONES_VALIDAS:
            json_validos += 1
            pred_por_id[cid] = item

    total = len(mapa_real)
    costo_total = 0
    tp = 0
    fp = 0
    fn = 0
    manuales = 0

    for cid, real in mapa_real.items():
        if cid not in pred_por_id:
            # Si falta o es inválido, penalización conservadora
            costo_total += 10
            continue
        pred = pred_por_id[cid]["decision"]
        costo_total += calcular_costo_fila(pred, real)
        if pred == "aprobada":
            if real == "aprobada":
                tp += 1
            else:
                fp += 1
        elif pred == "rechazada" and real == "aprobada":
            fn += 1
        elif pred == "revision_manual":
            manuales += 1

    precision_aprob = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    pct_json_valido = json_validos / total if total > 0 else 0.0

    return {
        "total_capturas": total,
        "json_validos": json_validos,
        "pct_json_valido": round(pct_json_valido, 4),
        "cumple_json_99": pct_json_valido >= 0.99,
        "tp_aprobadas": tp,
        "fp_aprobadas": fp,
        "fn_rechazadas": fn,
        "enviadas_manual": manuales,
        "precision_aprobaciones": round(precision_aprob, 4),
        "cumple_precision_97": precision_aprob >= 0.97,
        "costo_operativo_total": costo_total,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluador local Validat3B")
    parser.add_argument("predicciones_json", help="Ruta al JSON con predicciones")
    parser.add_argument(
        "--gt",
        default="datos/metadatos/capturas.csv",
        help="Ruta al CSV de ground truth",
    )
    args = parser.parse_args()

    with open(args.predicciones_json, encoding="utf-8") as f:
        preds = json.load(f)

    res = evaluar_predicciones(preds, args.gt)
    print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
