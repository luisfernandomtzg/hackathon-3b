"""Puerta local (P2): evalúa y aplica umbrales seguros de rechazo sin gastar tokens.

Pregunta que responde con datos:
Usando solo señales locales (nitidez de producto y nitidez de etiqueta), ¿cuántas capturas
se pueden rechazar sin llamar al modelo sin equivocarnos en ninguna (`aprobada` real = 0)?

Uso CLI:
    python -m ml.validat3b.puerta --locales salidas/locales.csv
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any, Optional

from ml.validat3b.contrato import RC_BORROSA

# Umbrales seguros fijados con las 100 capturas de desarrollo (salidas/locales.csv, 21-nov):
# - Mínimo de nitidez_producto en aprobadas reales: 84.4753 (CAP-970141) -> umbral seguro = 84.0
#   (debajo caen 6 capturas: 3 rechazadas y 3 revision_manual; 0 aprobadas reales).
# - Mínimo de nitidez_etiqueta en aprobadas reales: 83.0180 (CAP-970141) -> umbral seguro = 82.0
#   (debajo caen 14 capturas: 9 rechazadas y 5 revision_manual; 0 aprobadas reales).
# - Combinando ambas (nitidez_producto < 84.0 o nitidez_etiqueta < 82.0) caen 16 capturas (16.0 %):
#   10 rechazadas reales y 6 revision_manual reales, con 0 aprobadas reales rechazadas.
UMBRAL_SEGURO_PRODUCTO: float = 84.0
UMBRAL_SEGURO_ETIQUETA: float = 82.0

UMBRALES_EXPLORACION: tuple[float, ...] = (
    25.0,
    40.0,
    50.0,
    60.0,
    70.0,
    76.0,
    79.0,
    82.0,
    84.0,
    90.0,
    100.0,
    120.0,
    150.0,
    200.0,
)


def _a_float(valor: Any) -> Optional[float]:
    """Convierte un valor a float o devuelve None si es nulo/inválido."""
    if valor is None or isinstance(valor, bool):
        return None
    if isinstance(valor, (int, float)):
        return float(valor)
    texto = str(valor).strip()
    if not texto or texto.lower() in ("none", "null", "nan"):
        return None
    try:
        return float(texto)
    except ValueError:
        return None


def puerta(senales: Optional[dict[str, Any]]) -> Optional[str]:
    """Evalúa si una captura puede rechazarse en local sin llamar al modelo.

    Devuelve `"CAPTURA_BORROSA"` (`RC_BORROSA`) si alguna nitidez presente cae bajo su
    umbral seguro (`nitidez_producto < UMBRAL_SEGURO_PRODUCTO` o
    `nitidez_etiqueta < UMBRAL_SEGURO_ETIQUETA`), o `None` si debe ir al modelo.
    Ante valores `None` o ausencia de señales, devuelve `None` (ante la duda, va al modelo).
    """
    if not senales or not isinstance(senales, dict):
        return None

    nit_prod = _a_float(senales.get("nitidez_producto"))
    nit_etiq = _a_float(senales.get("nitidez_etiqueta"))

    if nit_prod is not None and nit_prod < UMBRAL_SEGURO_PRODUCTO:
        return RC_BORROSA
    if nit_etiq is not None and nit_etiq < UMBRAL_SEGURO_ETIQUETA:
        return RC_BORROSA

    return None


def _cargar_locales(ruta_csv: Path) -> list[dict[str, Any]]:
    with open(ruta_csv, mode="r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _contar_bajo_umbral(
    filas: list[dict[str, Any]],
    campo: str,
    umbral: float,
) -> dict[str, int]:
    conteo = {"total": 0, "aprobada": 0, "rechazada": 0, "revision_manual": 0, "otra": 0}
    for r in filas:
        val = _a_float(r.get(campo))
        if val is not None and val < umbral:
            conteo["total"] += 1
            dec = (r.get("decision_esperada") or "").strip()
            if dec in ("aprobada", "rechazada", "revision_manual"):
                conteo[dec] += 1
            else:
                conteo["otra"] += 1
    return conteo


def _umbral_maximo_seguro(filas: list[dict[str, Any]], campo: str) -> tuple[float, dict[str, int]]:
    """Encuentra el umbral más alto (entero hacia abajo del mínimo aprobado) con 0 aprobadas reales."""
    valores_aprobadas = [
        _a_float(r.get(campo))
        for r in filas
        if (r.get("decision_esperada") or "").strip() == "aprobada"
    ]
    validos = [v for v in valores_aprobadas if v is not None]
    if not validos:
        return 0.0, {"total": 0, "aprobada": 0, "rechazada": 0, "revision_manual": 0, "otra": 0}

    min_aprobada = min(validos)
    # Buscamos el valor máximo entre las capturas no aprobadas que sea estrictamente menor a min_aprobada
    bajo_min = [
        _a_float(r.get(campo))
        for r in filas
        if _a_float(r.get(campo)) is not None and _a_float(r.get(campo)) < min_aprobada  # type: ignore[operator]
    ]
    if not bajo_min:
        return 0.0, {"total": 0, "aprobada": 0, "rechazada": 0, "revision_manual": 0, "otra": 0}

    # Fijamos el umbral entero seguro justo por debajo de min_aprobada (o punto medio)
    max_no_aprob = max(v for v in bajo_min if v is not None)
    umbral_seguro = float(int(min_aprobada)) if int(min_aprobada) > max_no_aprob else round((max_no_aprob + min_aprobada) / 2.0, 2)
    return umbral_seguro, _contar_bajo_umbral(filas, campo, umbral_seguro)


def analizar_puerta(ruta_csv: str | Path) -> dict[str, Any]:
    """Ejecuta el barrido de umbrales sobre `locales.csv` e imprime las tablas de resultados."""
    filas = _cargar_locales(Path(ruta_csv))
    n_total = len(filas)

    for campo, titulo in (
        ("nitidez_producto", "NITIDEZ DE PRODUCTO (nitidez_producto)"),
        ("nitidez_etiqueta", "NITIDEZ DE ETIQUETA (nitidez_etiqueta)"),
    ):
        print(f"=== Barrido de umbrales: {titulo} ===")
        print(f"{'Umbral':>8} | {'Total < U':>9} | {'% Ahorro':>8} | {'rechazada':>9} | {'rev_manual':>10} | {'aprobada':>8} | {'Seguro':>6}")
        print("-" * 76)
        for u in UMBRALES_EXPLORACION:
            c = _contar_bajo_umbral(filas, campo, u)
            pct = (100.0 * c["total"] / n_total) if n_total else 0.0
            seguro = "SI" if c["aprobada"] == 0 else "NO"
            print(
                f"{u:8.1f} | {c['total']:9d} | {pct:7.1f}% | "
                f"{c['rechazada']:9d} | {c['revision_manual']:10d} | {c['aprobada']:8d} | {seguro:>6}"
            )
        u_max, c_max = _umbral_maximo_seguro(filas, campo)
        pct_max = (100.0 * c_max["total"] / n_total) if n_total else 0.0
        print(
            f"-> Umbral máximo seguro ({campo} < {u_max:.1f}): "
            f"ahorra {c_max['total']}/{n_total} capturas ({pct_max:.1f}% tokens) "
            f"[rechazadas={c_max['rechazada']}, revision_manual={c_max['revision_manual']}, aprobadas={c_max['aprobada']}]\n"
        )

    # Evaluación de la función puerta() combinada con las constantes del módulo
    filtradas = {"total": 0, "aprobada": 0, "rechazada": 0, "revision_manual": 0}
    for r in filas:
        motivo = puerta(r)
        if motivo is not None:
            filtradas["total"] += 1
            dec = (r.get("decision_esperada") or "").strip()
            if dec in filtradas:
                filtradas[dec] += 1

    pct_comb = (100.0 * filtradas["total"] / n_total) if n_total else 0.0
    print(
        f"=== Puerta combinada (nitidez_producto < {UMBRAL_SEGURO_PRODUCTO:.1f} "
        f"OR nitidez_etiqueta < {UMBRAL_SEGURO_ETIQUETA:.1f}) ==="
    )
    print(
        f"Capturas rechazadas sin modelo: {filtradas['total']}/{n_total} ({pct_comb:.1f}% ahorro de tokens) | "
        f"Reales: rechazada={filtradas['rechazada']}, revision_manual={filtradas['revision_manual']}, "
        f"aprobada={filtradas['aprobada']}"
    )
    recomendacion = "ACTIVAR" if (pct_comb >= 10.0 and filtradas["aprobada"] == 0) else "NO ACTIVAR"
    print(f"Recomendación (regla >= 10% ahorro con 0 aprobadas reales rechazadas): {recomendacion}")

    return {
        "total_capturas": n_total,
        "filtradas": filtradas,
        "pct_ahorro": pct_comb,
        "recomendacion": recomendacion,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analiza umbrales de nitidez en locales.csv para puerta local sin tokens."
    )
    parser.add_argument(
        "--locales",
        required=True,
        help="Ruta al archivo CSV de señales locales (ej. salidas/locales.csv)",
    )
    args = parser.parse_args()
    analizar_puerta(args.locales)


if __name__ == "__main__":
    main()
