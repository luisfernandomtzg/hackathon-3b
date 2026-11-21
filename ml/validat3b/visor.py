"""Visor local estático de capturas para Validat3B (U1).

Uso:
    python -m ml.validat3b.visor --datos datos/privado --resultados salidas/resultados.json --salida salidas/visor.html
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import os
from pathlib import Path
from typing import Any


def calcular_costo(decision_motor: str | None, decision_esperada: str) -> int | None:
    """Calcula el costo operativo (0, 1, 3, 10) de una captura."""
    if not decision_motor:
        return None
    if decision_motor == "revision_manual":
        return 1
    if decision_motor == decision_esperada:
        return 0
    if decision_motor == "aprobada" and decision_esperada != "aprobada":
        return 10
    if decision_motor == "rechazada" and decision_esperada == "aprobada":
        return 3
    return 1


def _cargar_capturas(dir_datos: Path) -> list[dict[str, Any]]:
    csv_path = dir_datos / "metadatos" / "capturas.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"No se encontró {csv_path}")
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _cargar_json_lista(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        return {}
    return {
        str(item["capture_id"]): item
        for item in data
        if isinstance(item, dict) and "capture_id" in item
    }


def _resolver_ruta_imagen(dir_datos: Path, rel_file: str, dir_salida: Path) -> str:
    """Resuelve la ruta relativa de la imagen respecto al HTML de salida."""
    candidato = dir_datos / "imagenes" / rel_file
    if not candidato.exists():
        candidato = dir_datos / rel_file
    return Path(os.path.relpath(candidato, start=dir_salida)).as_posix()


def generar_html(
    dir_datos: Path,
    ruta_resultados: Path,
    ruta_salida: Path,
) -> tuple[int, int]:
    """Genera el HTML estático del visor y devuelve (num_tarjetas, costo_total)."""
    capturas = _cargar_capturas(dir_datos)
    resultados = _cargar_json_lista(ruta_resultados)
    extracciones = _cargar_json_lista(ruta_resultados.parent / "extracciones.json")

    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    dir_salida = ruta_salida.parent.resolve()
    dir_datos_res = dir_datos.resolve()

    registros: list[dict[str, Any]] = []
    costo_total = 0

    for row in capturas:
        cid = row["capture_id"]
        esperada = row.get("decision_esperada", "")
        res = resultados.get(cid, {})
        ext = extracciones.get(cid, {})

        dec_motor = res.get("decision")
        costo = calcular_costo(dec_motor, esperada)
        if costo is not None:
            costo_total += costo

        es_error = bool(dec_motor and dec_motor != esperada)
        registros.append(
            {
                "capture_id": cid,
                "store": row.get("capture_store_name", ""),
                "brand": row.get("capture_brand", ""),
                "product_name": row.get("product_name", ""),
                "qty": row.get("unit_quantity_product", ""),
                "unit": row.get("unit_product", ""),
                "price_ref": row.get("capture_price", ""),
                "esperada": esperada,
                "motivo_esperado": row.get("motivo_rechazo", ""),
                "motor": dec_motor or "",
                "confidence": res.get("confidence_score"),
                "reason_code": res.get("reason_code", ""),
                "explicacion": res.get("explicacion", ""),
                "precio_detectado": res.get("precio_detectado"),
                "barcode_detectado": res.get("codigo_barras_detectado", ""),
                "extraccion": ext,
                "costo": costo,
                "es_error": es_error,
                "img_facade": _resolver_ruta_imagen(dir_datos_res, row.get("facade_file", ""), dir_salida),
                "img_product": _resolver_ruta_imagen(dir_datos_res, row.get("product_file", ""), dir_salida),
                "img_shelf": _resolver_ruta_imagen(dir_datos_res, row.get("shelf_file", ""), dir_salida),
            }
        )

    datos_json = json.dumps(registros, ensure_ascii=False)
    tiene_resultados = "true" if resultados else "false"

    html_doc = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Visor Validat3B</title>
  <style>
    :root {{
      --bg: #f6f7f6;
      --surface: #ffffff;
      --ink: #04211f;
      --muted: #4b5d5b;
      --border: #d5dedc;
      --error: #e31b23;
      --error-bg: #fdebec;
      --ok-bg: #e8f5ee;
      --ok-ink: #0e5a36;
      --warn-bg: #fff6e0;
      --warn-ink: #7a5200;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: var(--bg);
      color: var(--ink);
      line-height: 1.4;
    }}
    header {{
      position: sticky;
      top: 0;
      z-index: 10;
      background: var(--surface);
      border-bottom: 1px solid var(--border);
      padding: 12px 20px;
    }}
    .top-row {{
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 10px;
    }}
    h1 {{
      margin: 0;
      font-size: 1.15rem;
      font-weight: 700;
    }}
    .stats {{
      display: flex;
      gap: 16px;
      font-size: 0.95rem;
      font-weight: 600;
    }}
    .filters {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
    }}
    select, button, label.btn-check {{
      min-height: 44px;
      padding: 0 12px;
      border: 1px solid var(--border);
      border-radius: 8px;
      background: var(--surface);
      color: var(--ink);
      font-size: 0.9rem;
      cursor: pointer;
    }}
    label.btn-check {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }}
    button.active {{
      border-color: var(--ink);
      font-weight: 600;
    }}
    main {{
      max-width: 1280px;
      margin: 16px auto;
      padding: 0 16px 40px;
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
      gap: 16px;
    }}
    .card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 14px;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }}
    .card.is-error {{
      border-color: var(--error);
    }}
    .card-head {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 8px;
      font-size: 0.9rem;
    }}
    .cid {{ font-family: ui-monospace, monospace; font-weight: 700; }}
    .costo-badge {{
      padding: 2px 8px;
      border-radius: 999px;
      font-weight: 700;
      font-size: 0.8rem;
      background: #eef2f1;
    }}
    .costo-badge.high {{
      background: var(--error-bg);
      color: var(--error);
    }}
    .photos {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 6px;
    }}
    .photos img {{
      width: 100%;
      height: 96px;
      object-fit: cover;
      border-radius: 6px;
      border: 1px solid var(--border);
      cursor: zoom-in;
      background: #eceeed;
    }}
    .meta {{ font-size: 0.88rem; }}
    .meta strong {{ display: block; }}
    .decisions {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      font-size: 0.85rem;
      background: var(--bg);
      padding: 8px;
      border-radius: 6px;
    }}
    .tag {{
      display: inline-block;
      padding: 2px 8px;
      border-radius: 999px;
      font-weight: 600;
      font-size: 0.78rem;
    }}
    .tag.aprobada {{ background: var(--ok-bg); color: var(--ok-ink); }}
    .tag.rechazada {{ background: var(--error-bg); color: var(--error); }}
    .tag.revision_manual {{ background: var(--warn-bg); color: var(--warn-ink); }}
    .extra {{ font-size: 0.82rem; color: var(--muted); }}
    #modal {{
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(4, 33, 31, 0.85);
      z-index: 100;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }}
    #modal.open {{ display: flex; }}
    #modal img {{
      max-width: 95vw;
      max-height: 90vh;
      border-radius: 8px;
      background: #fff;
    }}
    #modal-close {{
      position: fixed;
      top: 16px;
      right: 16px;
      min-height: 44px;
      min-width: 44px;
      font-weight: 700;
    }}
  </style>
</head>
<body>
  <header>
    <div class="top-row">
      <h1>Visor local de capturas · Validat3B</h1>
      <div class="stats">
        <span id="stat-count">0 tarjetas</span>
        <span id="stat-cost">Costo total: {costo_total} pts</span>
      </div>
    </div>
    <div class="filters">
      <select id="f-esperada" aria-label="Filtrar por decisión esperada">
        <option value="">Esperada: Todas</option>
        <option value="aprobada">Esperada: aprobada</option>
        <option value="rechazada">Esperada: rechazada</option>
        <option value="revision_manual">Esperada: revision_manual</option>
      </select>
      <select id="f-motor" aria-label="Filtrar por decisión del motor">
        <option value="">Motor: Todas</option>
        <option value="aprobada">Motor: aprobada</option>
        <option value="rechazada">Motor: rechazada</option>
        <option value="revision_manual">Motor: revision_manual</option>
      </select>
      <label class="btn-check">
        <input type="checkbox" id="f-errores" />
        Solo errores
      </label>
      <select id="f-orden" aria-label="Ordenar por costo">
        <option value="original">Orden: Original</option>
        <option value="costo-desc">Orden: Mayor costo primero</option>
        <option value="costo-asc">Orden: Menor costo primero</option>
      </select>
      <button type="button" id="btn-reset">Limpiar filtros</button>
    </div>
  </header>

  <main id="grid"></main>

  <div id="modal" role="dialog" aria-modal="true">
    <button type="button" id="modal-close">Cerrar</button>
    <img id="modal-img" src="" alt="Vista ampliada" />
  </div>

  <script>
    const DATA = {datos_json};
    const TIENE_RESULTADOS = {tiene_resultados};

    const grid = document.getElementById("grid");
    const statCount = document.getElementById("stat-count");
    const statCost = document.getElementById("stat-cost");
    const fEsperada = document.getElementById("f-esperada");
    const fMotor = document.getElementById("f-motor");
    const fErrores = document.getElementById("f-errores");
    const fOrden = document.getElementById("f-orden");
    const btnReset = document.getElementById("btn-reset");
    const modal = document.getElementById("modal");
    const modalImg = document.getElementById("modal-img");

    function esc(s) {{
      return String(s ?? "").replace(/[&<>"']/g, c => ({{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}}[c]));
    }}

    function render() {{
      const esp = fEsperada.value;
      const mot = fMotor.value;
      const soloErr = fErrores.checked;
      const ord = fOrden.value;

      let items = DATA.filter(d => {{
        if (esp && d.esperada !== esp) return false;
        if (mot && d.motor !== mot) return false;
        if (soloErr && !d.es_error) return false;
        return true;
      }});

      if (ord === "costo-desc") {{
        items = [...items].sort((a, b) => (b.costo ?? -1) - (a.costo ?? -1));
      }} else if (ord === "costo-asc") {{
        items = [...items].sort((a, b) => (a.costo ?? 999) - (b.costo ?? 999));
      }}

      const costoVis = items.reduce((acc, d) => acc + (d.costo ?? 0), 0);
      statCount.textContent = `${{items.length}} de ${{DATA.length}} tarjetas`;
      statCost.textContent = TIENE_RESULTADOS ? `Costo visible: ${{costoVis}} pts` : "Sin resultados.json (solo esperado)";

      grid.innerHTML = items.map(d => {{
        const costoTxt = d.costo === null ? "—" : `${{d.costo}} pts`;
        const costoCls = (d.costo ?? 0) >= 3 ? "costo-badge high" : "costo-badge";
        const confTxt = d.confidence !== null && d.confidence !== undefined ? Number(d.confidence).toFixed(2) : "—";
        return `
          <article class="card ${{d.es_error ? "is-error" : ""}}">
            <div class="card-head">
              <span class="cid">${{esc(d.capture_id)}} · ${{esc(d.store)}}</span>
              <span class="${{costoCls}}">Costo: ${{costoTxt}}</span>
            </div>
            <div class="photos">
              <img src="${{esc(d.img_facade)}}" alt="Fachada ${{esc(d.capture_id)}}" loading="lazy" onclick="openModal(this.src)" />
              <img src="${{esc(d.img_product)}}" alt="Producto ${{esc(d.capture_id)}}" loading="lazy" onclick="openModal(this.src)" />
              <img src="${{esc(d.img_shelf)}}" alt="Etiqueta ${{esc(d.capture_id)}}" loading="lazy" onclick="openModal(this.src)" />
            </div>
            <div class="meta">
              <strong>${{esc(d.brand)}} — ${{esc(d.product_name)}}</strong>
              <span>Contenido: ${{esc(d.qty)}} ${{esc(d.unit)}} · Precio ref: $${{esc(d.price_ref)}}</span>
            </div>
            <div class="decisions">
              <div>
                <div>Esperada:</div>
                <span class="tag ${{esc(d.esperada)}}">${{esc(d.esperada)}}</span>
                <div class="extra">${{esc(d.motivo_esperado || "Sin motivo")}}</div>
              </div>
              <div>
                <div>Motor:</div>
                ${{d.motor ? `<span class="tag ${{esc(d.motor)}}">${{esc(d.motor)}}</span>` : "<span>—</span>"}}
                <div class="extra">Conf: ${{confTxt}} · ${{esc(d.reason_code || "—")}}</div>
              </div>
            </div>
            ${{d.explicacion ? `<div class="extra"><strong>Explicación:</strong> ${{esc(d.explicacion)}}</div>` : ""}}
            ${{d.precio_detectado !== null && d.precio_detectado !== undefined ? `<div class="extra"><strong>Leído:</strong> $${{esc(d.precio_detectado)}} · Barcode: ${{esc(d.barcode_detectado || "—")}}</div>` : ""}}
          </article>
        `;
      }}).join("");
    }}

    window.openModal = function(src) {{
      modalImg.src = src;
      modal.classList.add("open");
    }};
    document.getElementById("modal-close").onclick = () => modal.classList.remove("open");
    modal.onclick = (e) => {{ if (e.target === modal) modal.classList.remove("open"); }};

    [fEsperada, fMotor, fErrores, fOrden].forEach(el => el.addEventListener("change", render));
    btnReset.onclick = () => {{
      fEsperada.value = "";
      fMotor.value = "";
      fErrores.checked = false;
      fOrden.value = "original";
      render();
    }};

    render();
  </script>
</body>
</html>
"""
    ruta_salida.write_text(html_doc, encoding="utf-8")
    return len(registros), costo_total


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera el visor HTML estático de Validat3B")
    parser.add_argument("--datos", default="datos/privado", help="Directorio de datos")
    parser.add_argument("--resultados", default="salidas/resultados.json", help="JSON de resultados del motor")
    parser.add_argument("--salida", default="salidas/visor.html", help="Ruta del HTML de salida")
    args = parser.parse_args()

    total, costo = generar_html(Path(args.datos), Path(args.resultados), Path(args.salida))
    print(f"Visor generado en {args.salida} ({total} tarjetas, costo total={costo})")


if __name__ == "__main__":
    main()
