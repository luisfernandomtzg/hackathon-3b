"""D3 · marcador para el pitch (Validat3B), versión D3.1.

Lee las decisiones de resultados.json tal cual (sin volver a decidir), para medir
lo que entregó el motor, incluidas sus compuertas. Los tokens se suman solo de
las filas de origen modelo (las de caché y verificar no son parte del motor final).

Cada cifra lleva su etiqueta: MEDIDO, DATO 3B, PROYECCIÓN, SUPUESTO o NO MEDIDO.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

CAPTURAS_POR_SEMANA_3B = 12_000
FUENTE_3B = "Alfredo, 3B (cifra del paquete de Sergio)"

COSTO = {
    "aprobada":        {"aprobada": 0,  "rechazada": 3,  "revision_manual": 1},
    "rechazada":       {"aprobada": 10, "rechazada": 0,  "revision_manual": 1},
    "revision_manual": {"aprobada": 10, "rechazada": 3,  "revision_manual": 1},
}


def costo(real, pred):
    return COSTO[real][pred]


def main(argv=None):
    p = argparse.ArgumentParser(description="D3 · marcador Validat3B (D3.1)")
    p.add_argument("--resultados", default="salidas/resultados.json")
    p.add_argument("--capturas", default="datos/privado/metadatos/capturas.csv")
    p.add_argument("--tokens", default="salidas/tokens.csv")
    p.add_argument("--segundos-analista", type=float, default=None)
    p.add_argument("--salida", default="salidas/marcador.md")
    args = p.parse_args(argv)

    with open(args.capturas, encoding="utf-8-sig", newline="") as f:
        real_por_id = {r["capture_id"]: r["decision_esperada"] for r in csv.DictReader(f)}
    with open(args.resultados, encoding="utf-8") as f:
        pred_por_id = {r["capture_id"]: r["decision"] for r in json.load(f)}

    ids = [c for c in real_por_id if c in pred_por_id]
    n = len(ids)
    real = {c: real_por_id[c] for c in ids}
    pred = {c: pred_por_id[c] for c in ids}

    costo_motor = sum(costo(real[c], pred[c]) for c in ids)
    base_manual = sum(costo(real[c], "revision_manual") for c in ids)
    base_aprobar = sum(costo(real[c], "aprobada") for c in ids)
    aprob = [c for c in ids if pred[c] == "aprobada"]
    falsas = [c for c in aprob if real[c] != "aprobada"]
    precision = (len(aprob) - len(falsas)) / len(aprob) if aprob else None
    sin_persona = sum(1 for c in ids if pred[c] in ("aprobada", "rechazada"))
    pct_sin_persona = sin_persona / n if n else 0.0

    with open(args.tokens, encoding="utf-8", newline="") as f:
        filas_modelo = [r for r in csv.DictReader(f) if r["origen"] == "modelo"]
    tok_in = sum(int(r["tokens_entrada"] or 0) for r in filas_modelo)
    tok_out = sum(int(r["tokens_salida"] or 0) for r in filas_modelo)
    seg_total = sum(float(r["segundos"] or 0) for r in filas_modelo)
    capturas_modelo = len({r["capture_id"] for r in filas_modelo})
    tok_por_captura = (tok_in + tok_out) / capturas_modelo if capturas_modelo else 0.0
    seg_por_captura = seg_total / capturas_modelo if capturas_modelo else 0.0

    sin_persona_semana = CAPTURAS_POR_SEMANA_3B * pct_sin_persona
    prec_txt = f"{precision:.2%}" if precision is not None else "n/a (aprobó 0)"

    L = []
    L.append("# Marcador Validat3B · D3.1")
    L.append("")
    L.append("Decisiones tomadas de resultados.json (lo que entregó el motor, con sus compuertas).")
    L.append("Cada cifra lleva su etiqueta: MEDIDO, DATO 3B, PROYECCIÓN, SUPUESTO o NO MEDIDO.")
    L.append("")
    L.append("| Métrica | Valor | Etiqueta |")
    L.append("|---|---|---|")
    L.append(f"| Capturas en desarrollo | {n} | MEDIDO (capturas.csv) |")
    L.append(f"| Costo operativo del motor (pesimista) | {costo_motor} | MEDIDO (con revision_manual = SUPUESTO) |")
    L.append(f"| Línea base: todo a revisión manual | {base_manual} | MEDIDO |")
    L.append(f"| Línea base: aprobar todo | {base_aprobar} | MEDIDO |")
    L.append(f"| Precisión de aprobadas | {prec_txt} (mínimo 97 %) | MEDIDO |")
    L.append(f"| Aprobadas | {len(aprob)} · falsas {len(falsas)} | MEDIDO |")
    L.append(f"| Capturas resueltas sin persona (aprobadas + rechazadas) | {sin_persona} de {n} ({pct_sin_persona:.0%}) | MEDIDO |")
    L.append(f"| Tokens de entrada (total, solo modelo) | {tok_in:,} | MEDIDO (tokens.csv, origen modelo) |")
    L.append(f"| Tokens de salida (total, solo modelo) | {tok_out:,} | MEDIDO (tokens.csv, origen modelo) |")
    L.append(f"| Tokens por captura | {tok_por_captura:,.0f} | MEDIDO (tokens.csv, origen modelo) |")
    L.append(f"| Segundos por captura del motor | {seg_por_captura:.1f} | MEDIDO (tokens.csv, origen modelo) |")
    L.append("")
    L.append("## Proyección a 12,000 capturas por semana")
    L.append("")
    L.append(f"- Capturas por semana: {CAPTURAS_POR_SEMANA_3B:,} | DATO 3B: {FUENTE_3B}")
    L.append(f"- Capturas que dejarían de revisarse a mano por semana: {sin_persona_semana:,.0f} | "
             f"PROYECCIÓN: asume que el {pct_sin_persona:.0%} sin persona de desarrollo se mantiene en producción")
    if args.segundos_analista is None:
        L.append("- Horas ahorradas por semana: sin dato | falta «segundos por captura de un analista» (3B no lo dio). "
                 "Se pasa con --segundos-analista.")
    else:
        horas = sin_persona_semana * args.segundos_analista / 3600
        L.append(f"- Horas ahorradas por semana: {horas:,.0f} | SUPUESTO: {args.segundos_analista:g} s por captura de analista")
    L.append("")
    L.append("## Qué no medimos (decir en el pitch, no inventar)")
    L.append("")
    L.append("- Costo real en pesos del endpoint por captura: NO MEDIDO (no tenemos precios del proveedor).")
    L.append("- Revisión humana real por captura: NO MEDIDO (no tenemos segundos de analista de 3B).")
    L.append("- Regla oficial para real revision_manual: NO MEDIDO (SUPUESTO en el costo).")
    L.append("- Desempeño sobre el set ciego: NO MEDIDO (se libera entre 15:00 y 16:00).")
    L.append("")

    salida = Path(args.salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"Marcador escrito en {salida}")
    print(f"Costo motor: {costo_motor} · aprobadas: {len(aprob)} · falsas: {len(falsas)} · precisión: {prec_txt} · tokens/captura: {tok_por_captura:,.0f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
