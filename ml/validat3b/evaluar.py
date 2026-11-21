"""Arnés de evaluación · Reto 2 Validat3B (D1).

Mide un resultados.json contra las etiquetas de desarrollo (decision_esperada):
JSON válido, costo operativo, precisión de aprobadas, matriz 3x3, costo por motivo,
líneas base, acierto de reason_code, errores más caros y, con --por-visita,
costo por visita.

Solo biblioteca estándar. Uso:
    python -m ml.validat3b.evaluar --resultados salidas/resultados.json \
        --capturas datos/privado/metadatos/capturas.csv [--por-visita]
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

DECISIONES = ("aprobada", "rechazada", "revision_manual")
OK_FALLA = ("ok", "falla")
VALIDACIONES = ("tienda_fachada", "producto", "codigo_barras", "evidencia_precio")
LLAVES = (
    "capture_id", "decision", "confidence_score", "reason_code", "validaciones",
    "precio_detectado", "codigo_barras_detectado", "explicacion",
)
SIN_PREDICCION = "sin_prediccion"
ESCENARIOS = ("pesimista", "optimista")

# COSTO[escenario][real][predicha]. Para real "revision_manual" la regla oficial
# aún no está; por eso hay dos escenarios y ambos son SUPUESTO.
COSTO = {
    "pesimista": {
        "aprobada":        {"aprobada": 0,  "rechazada": 3, "revision_manual": 1},
        "rechazada":       {"aprobada": 10, "rechazada": 0, "revision_manual": 1},
        "revision_manual": {"aprobada": 10, "rechazada": 3, "revision_manual": 1},
    },
    "optimista": {
        "aprobada":        {"aprobada": 0,  "rechazada": 3, "revision_manual": 1},
        "rechazada":       {"aprobada": 10, "rechazada": 0, "revision_manual": 1},
        "revision_manual": {"aprobada": 10, "rechazada": 0, "revision_manual": 0},
    },
}
# Captura sin predicción válida: penalización conservadora (SUPUESTO, igual que evaluador.py).
COSTO_SIN_PREDICCION = 10

MINIMO_JSON = 0.99
MINIMO_PRECISION = 0.97
TOLERANCIA_PRECIO = 0.01

# Códigos PROVISIONALES: se cambian por este mapa cuando llegue la lista oficial.
MAPA_MOTIVO = {
    "Capturas lejanas": "CAPTURA_LEJANA",
    "Capturas borrosas": "CAPTURA_BORROSA",
    "Descripción de producto incompleta": "DESCRIPCION_INCOMPLETA",
}


def costo(real: str, pred: str | None, escenario: str = "pesimista") -> int:
    """Costo operativo de una captura según la matriz de la misión."""
    if pred is None:
        return COSTO_SIN_PREDICCION
    return COSTO[escenario][real][pred]


def _es_numero(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def entrada_valida(e: Any) -> bool:
    """True si la entrada tiene todas las llaves y valores permitidos por el contrato v1."""
    if not isinstance(e, dict) or any(k not in e for k in LLAVES):
        return False
    if not isinstance(e["capture_id"], str) or not e["capture_id"]:
        return False
    if e["decision"] not in DECISIONES:
        return False
    if not _es_numero(e["confidence_score"]) or not 0 <= e["confidence_score"] <= 1:
        return False
    if e["reason_code"] is not None and not isinstance(e["reason_code"], str):
        return False
    v = e["validaciones"]
    if not isinstance(v, dict) or any(v.get(k) not in OK_FALLA for k in VALIDACIONES):
        return False
    if e["precio_detectado"] is not None and not _es_numero(e["precio_detectado"]):
        return False
    if e["codigo_barras_detectado"] is not None and not isinstance(e["codigo_barras_detectado"], str):
        return False
    return isinstance(e["explicacion"], str)


def _float(s: Any) -> float | None:
    if s in (None, ""):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def leer_capturas(ruta: str | Path) -> dict[str, dict[str, str]]:
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        filas = {fila["capture_id"]: fila for fila in csv.DictReader(f)}
    for cid, fila in filas.items():
        if fila["decision_esperada"] not in DECISIONES:
            raise ValueError(f"decision_esperada inválida en {cid}: {fila['decision_esperada']!r}")
    return filas


def leer_resultados(ruta: str | Path) -> list[Any]:
    with open(ruta, encoding="utf-8") as f:
        datos = json.load(f)
    if not isinstance(datos, list):
        raise ValueError("resultados.json debe ser una lista de objetos")
    return datos


def evaluar(capturas: dict[str, dict[str, str]], resultados: list[Any]) -> dict[str, Any]:
    """Cálculo puro (sin archivos): recibe capturas y resultados ya leídos."""
    por_id: dict[str, list[Any]] = defaultdict(list)
    for e in resultados:
        if isinstance(e, dict) and isinstance(e.get("capture_id"), str):
            por_id[e["capture_id"]].append(e)

    # Solo cuenta una predicción si hay EXACTAMENTE una entrada y es válida.
    entradas: dict[str, dict[str, Any]] = {}
    fallan: list[str] = []
    for cid in capturas:
        candidatas = por_id.get(cid, [])
        if len(candidatas) == 1 and entrada_valida(candidatas[0]):
            entradas[cid] = candidatas[0]
        else:
            fallan.append(cid)

    pred = {cid: (entradas[cid]["decision"] if cid in entradas else None) for cid in capturas}
    total = len(capturas)
    json_ok = len(entradas)

    costos = {
        esc: {cid: costo(capturas[cid]["decision_esperada"], pred[cid], esc) for cid in capturas}
        for esc in ESCENARIOS
    }
    costo_total = {esc: sum(costos[esc].values()) for esc in ESCENARIOS}

    aprobadas = [cid for cid in capturas if pred[cid] == "aprobada"]
    tp = sum(1 for cid in aprobadas if capturas[cid]["decision_esperada"] == "aprobada")
    precision = tp / len(aprobadas) if aprobadas else None

    matriz = {r: {c: 0 for c in (*DECISIONES, SIN_PREDICCION)} for r in DECISIONES}
    for cid, fila in capturas.items():
        matriz[fila["decision_esperada"]][pred[cid] or SIN_PREDICCION] += 1

    por_motivo: dict[str, dict[str, int]] = defaultdict(
        lambda: {"n": 0, **{esc: 0 for esc in ESCENARIOS}}
    )
    for cid, fila in capturas.items():
        m = fila.get("motivo_rechazo") or "(sin motivo)"
        por_motivo[m]["n"] += 1
        for esc in ESCENARIOS:
            por_motivo[m][esc] += costos[esc][cid]

    lineas_base = {}
    for nombre, pred_fija in (
        ("todo revision_manual", "revision_manual"),
        ("todo aprobado", "aprobada"),
        ("todo rechazado", "rechazada"),
    ):
        lineas_base[nombre] = {
            esc: sum(costo(f["decision_esperada"], pred_fija, esc) for f in capturas.values())
            for esc in ESCENARIOS
        }

    rc_total = rc_ok = 0
    sin_mapa: dict[str, int] = defaultdict(int)
    precio_total = precio_ok = 0
    for cid, fila in capturas.items():
        real = fila["decision_esperada"]
        e = entradas.get(cid)
        motivo = fila.get("motivo_rechazo") or ""
        if real == "rechazada" and motivo:
            esperado = MAPA_MOTIVO.get(motivo)
            if esperado is None:
                sin_mapa[motivo] += 1
            else:
                rc_total += 1
                if e is not None and e["reason_code"] == esperado:
                    rc_ok += 1
        ref = _float(fila.get("capture_price"))
        if real == "aprobada" and ref is not None:
            precio_total += 1
            if e is not None and e["precio_detectado"] is not None:
                if abs(float(e["precio_detectado"]) - ref) <= TOLERANCIA_PRECIO:
                    precio_ok += 1

    errores = []
    for cid in sorted(capturas, key=lambda c: (-costos["pesimista"][c], c)):
        if costos["pesimista"][cid] == 0 or len(errores) == 15:
            break
        e = entradas.get(cid)
        errores.append({
            "capture_id": cid,
            "real": capturas[cid]["decision_esperada"],
            "pred": pred[cid] or SIN_PREDICCION,
            "costo": costos["pesimista"][cid],
            "reason_code": e["reason_code"] if e else None,
        })

    visitas: dict[str, dict[str, int]] = defaultdict(
        lambda: {"n": 0, **{esc: 0 for esc in ESCENARIOS}}
    )
    for cid, fila in capturas.items():
        v = fila.get("facade_url") or "(sin visita)"
        visitas[v]["n"] += 1
        for esc in ESCENARIOS:
            visitas[v][esc] += costos[esc][cid]

    return {
        "total": total,
        "json_ok": json_ok,
        "pct_json": json_ok / total if total else 0.0,
        "json_fallan": fallan,
        "costo": costo_total,
        "aprobadas": len(aprobadas),
        "tp": tp,
        "fp": len(aprobadas) - tp,
        "precision": precision,
        "matriz": matriz,
        "por_motivo": dict(por_motivo),
        "lineas_base": lineas_base,
        "rc": (rc_ok, rc_total),
        "rc_sin_mapa": dict(sin_mapa),
        "precio": (precio_ok, precio_total),
        "errores": errores,
        "visitas": dict(visitas),
    }


def _estado(ok: bool) -> str:
    return "PASA" if ok else "NO PASA"


def imprimir(r: dict[str, Any], por_visita: bool) -> None:
    print("=== Evaluación Validat3B · D1 ===")
    print(f"Capturas en el CSV: {r['total']}\n")

    print("1) JSON válido")
    print(f"   {r['json_ok']}/{r['total']} = {r['pct_json']:.2%} -> {_estado(r['pct_json'] >= MINIMO_JSON)} (mínimo 99 %)")
    if r["json_fallan"]:
        print("   Capturas que fallan:", ", ".join(r["json_fallan"]))
    print()

    print("2) Costo operativo (real revision_manual = SUPUESTO en ambos escenarios)")
    for esc in ESCENARIOS:
        print(f"   {esc:<10}: {r['costo'][esc]}")
    print(f"   Sin predicción válida cuenta {COSTO_SIN_PREDICCION} (SUPUESTO).\n")

    print("3) Precisión de aprobadas")
    if r["aprobadas"] == 0:
        print("   Aprobó 0 capturas: sin aprobadas, precisión NO MEDIBLE.\n")
    else:
        print(
            f"   Aprobó {r['aprobadas']}: {r['tp']} correctas, {r['fp']} falsas "
            f"-> {r['precision']:.2%} -> {_estado(r['precision'] >= MINIMO_PRECISION)} (mínimo 97 %)\n"
        )

    print("4) Matriz real (filas) x predicha (columnas)")
    cols = (*DECISIONES, SIN_PREDICCION)
    print("   " + f"{'real':<16}" + "".join(f"{c:>18}" for c in cols))
    for real in DECISIONES:
        print("   " + f"{real:<16}" + "".join(f"{r['matriz'][real][c]:>18}" for c in cols))
    print()

    print("5) Costo por motivo_rechazo (según decision_esperada)")
    for m, v in sorted(r["por_motivo"].items()):
        print(f"   {m:<36} n={v['n']:<4} pesimista={v['pesimista']:<5} optimista={v['optimista']}")
    print()

    print("6) Líneas base")
    for nombre, v in r["lineas_base"].items():
        print(f"   {nombre:<22} pesimista={v['pesimista']:<5} optimista={v['optimista']}")
    print()

    print("7) Calidad del dato (referencia, no verdad)")
    ok, tot = r["rc"]
    print(f"   reason_code acertado en rechazadas reales con motivo mapeado: {ok}/{tot}")
    for motivo, n in r["rc_sin_mapa"].items():
        print(f"   Motivo sin mapa: «{motivo}» ({n})")
    pok, ptot = r["precio"]
    print(f"   precio_detectado = capture_price (±0.01) en aprobadas reales: {pok}/{ptot}")
    print("   capture_price es una referencia del CSV, no la verdad del precio.\n")

    print("8) Los 15 errores más caros (ranking por costo pesimista)")
    if not r["errores"]:
        print("   Ninguno.")
    for e in r["errores"]:
        print(
            f"   {e['capture_id']:<12} real={e['real']:<16} pred={e['pred']:<16} "
            f"costo={e['costo']:<3} reason_code={e['reason_code']}"
        )
    print()

    if por_visita:
        print("9) Costo por visita (facade_url)")
        for v, d in sorted(r["visitas"].items(), key=lambda kv: -kv[1]["pesimista"]):
            print(f"   {v:<60} n={d['n']:<4} pesimista={d['pesimista']:<5} optimista={d['optimista']}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Arnés de evaluación Validat3B (D1)")
    p.add_argument("--resultados", required=True, help="Ruta a salidas/resultados.json")
    p.add_argument("--capturas", default="datos/privado/metadatos/capturas.csv")
    p.add_argument("--por-visita", action="store_true", help="Agrega el costo por facade_url")
    args = p.parse_args(argv)

    if not Path(args.resultados).exists():
        print(f"No existe {args.resultados}. Genera el de 'todo revision_manual' (ver paso 3).", file=sys.stderr)
        return 1

    capturas = leer_capturas(args.capturas)
    resultados = leer_resultados(args.resultados)
    imprimir(evaluar(capturas, resultados), args.por_visita)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
