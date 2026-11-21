"""D3 · marcador para el pitch (Validat3B).

Una tabla de una sola vista. Cada cifra lleva su etiqueta:
- MEDIDO: calculado aquí desde los archivos de salidas/ y datos de desarrollo.
- DATO 3B: cifra entregada por 3B, con su fuente.
- SUPUESTO: no medido; depende de un parámetro que se pasa por línea de comandos.
- NO MEDIDO: no tenemos el dato; se dice en el pitch, no se inventa.

Uso:
    python -m ml.validat3b.marcador --resultados salidas/resultados.json \
        --extracciones salidas/extracciones.json \
        --capturas datos/privado/metadatos/capturas.csv \
        --tokens salidas/tokens.csv \
        [--segundos-analista 120] \
        --salida salidas/marcador.md
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

from ml.validat3b.contrato import Captura, Extraccion
from ml.validat3b.decidir import decidir

# DATO 3B: cifra de Alfredo (3B), según docs/paquetes/sergio.md.
CAPTURAS_POR_SEMANA_3B = 12_000
FUENTE_3B = "Alfredo, 3B (cifra del paquete de Sergio)"

# Costo PESIMISTA. Para real revision_manual la regla oficial no está.
COSTO = {
    "aprobada":        {"aprobada": 0,  "rechazada": 3,  "revision_manual": 1},
    "rechazada":       {"aprobada": 10, "rechazada": 0,  "revision_manual": 1},
    "revision_manual": {"aprobada": 10, "rechazada": 3,  "revision_manual": 1},
}


def costo(real: str, pred: str) -> int:
    return COSTO[real][pred]


def a_captura(fila: dict[str, str]) -> Captura:
    return Captura(**{k: (v if v != "" else None) for k, v in fila.items() if k in Captura.model_fields})


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="D3 · marcador Validat3B")
    p.add_argument("--resultados", default="salidas/resultados.json")
    p.add_argument("--extracciones", default="salidas/extracciones.json")
    p.add_argument("--capturas", default="datos/privado/metadatos/capturas.csv")
    p.add_argument("--tokens", default="salidas/tokens.csv")
    p.add_argument("--segundos-analista", type=float, default=None,
                   help="Segundos por captura de un analista. No lo dio 3B: SUPUESTO.")
    p.add_argument("--salida", default="salidas/marcador.md")
    args = p.parse_args(argv)

    with open(args.capturas, encoding="utf-8-sig", newline="") as f:
        filas = {r["capture_id"]: r for r in csv.DictReader(f)}
    with open(args.extracciones, encoding="utf-8") as f:
        ext = {e["capture_id"]: Extraccion(**e) for e in json.load(f)}
    with open(args.resultados, encoding="utf-8") as f:
        res = {r["capture_id"]: r for r in json.load(f)}
    with open(args.tokens, encoding="utf-8", newline="") as f:
        tokens = {r["capture_id"]: r for r in csv.DictReader(f)}

    ids = [c for c in filas if c in ext]
    real = {c: filas[c]["decision_esperada"] for c in ids}
    pred = {c: decidir(a_captura(filas[c]), ext[c]).decision for c in ids}
    n = len(ids)

    costo_motor = sum(costo(real[c], pred[c]) for c in ids)
    base_manual = sum(costo(real[c], "revision_manual") for c in ids)
    base_aprobar = sum(costo(real[c], "aprobada") for c in ids)
    aprob = [c for c in ids if pred[c] == "aprobada"]
    falsas = [c for c in aprob if real[c] != "aprobada"]
    precision = (len(aprob) - len(falsas)) / len(aprob) if aprob else None
    sin_persona = sum(1 for c in ids if pred[c] in ("aprobada", "rechazada"))

    # Tokens y segundos: de tokens.csv (medidos por el motor).
    tok_in = sum(int(tokens[c]["tokens_entrada"] or 0) for c in ids if c in tokens)
    tok_out = sum(int(tokens[c]["tokens_salida"] or 0) for c in ids if c in tokens)
    seg_total = sum(float(tokens[c]["segundos"] or 0) for c in ids if c in tokens)
    seg_por_captura = seg_total / n if n else 0.0

    # Proyección: capturas/semana que dejarían de revisarse a mano.
    pct_sin_persona = sin_persona / n if n else 0.0
    sin_persona_semana = CAPTURAS_POR_SEMANA_3B * pct_sin_persona

    L: list[str] = []
    L.append("# Marcador Validat3B · D3")
    L.append("")
    L.append("Cada cifra lleva su etiqueta: MEDIDO, DATO 3B, SUPUESTO o NO MEDIDO.")
    L.append("")
    L.append("| Métrica | Valor | Etiqueta |")
    L.append("|---|---|---|")
    L.append(f"| Capturas en desarrollo | {n} | MEDIDO (capturas.csv) |")
    L.append(f"| Costo operativo del motor (pesimista) | {costo_motor} | MEDIDO (con revision_manual = SUPUESTO) |")
    L.append(f"| Línea base: todo a revisión manual | {base_manual} | MEDIDO |")
    L.append(f"| Línea base: aprobar todo | {base_aprobar} | MEDIDO |")
    prec_txt = f"{precision:.2%}" if precision is not None else "n/a (aprobó 0)"
    L.append(f"| Precisión de aprobadas | {prec_txt} (mínimo 97 %) | MEDIDO |")
    L.append(f"| Aprobadas falsas | {len(falsas)} de {len(aprob)} | MEDIDO |")
    L.append(f"| Capturas resueltas sin persona (aprobadas + rechazadas) | {sin_persona} de {n} ({pct_sin_persona:.0%}) | MEDIDO |")
    L.append(f"| Tokens de entrada (total) | {tok_in:,} | MEDIDO (tokens.csv) |")
    L.append(f"| Tokens de salida (total) | {tok_out:,} | MEDIDO (tokens.csv) |")
    L.append(f"| Tokens por captura | {(tok_in + tok_out) / n:,.0f} | MEDIDO (tokens.csv) |")
    L.append(f"| Segundos por captura del motor | {seg_por_captura:.1f} | MEDIDO (tokens.csv) |")
    L.append("")

    L.append("## Proyección a 12,000 capturas por semana")
    L.append("")
    L.append(f"- Capturas por semana: {CAPTURAS_POR_SEMANA_3B:,} | DATO 3B: {FUENTE_3B}")
    L.append(f"- Capturas que dejarían de revisarse a mano por semana: {sin_persona_semana:,.0f} | "
             f"PROYECCIÓN: asume que el % sin persona de desarrollo (59 %) se mantiene en producción")
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
    print(f"Costo motor: {costo_motor} · base manual: {base_manual} · precisión: {prec_txt} · sin persona: {sin_persona}/{n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
