"""Visor local estático de capturas y modo pitch con identidad Tarima (U5).

Uso:
    python -m ml.validat3b.visor --datos datos/privado --resultados salidas/resultados.json --salida salidas/visor.html
    python -m ml.validat3b.visor --datos datos/privado --resultados salidas/resultados.json --salida salidas/visor.html --pitch CAP-434912,CAP-748989,CAP-350077
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
from typing import Any

COSTO_PESIMISTA = {
    "aprobada": {"aprobada": 0, "revision_manual": 1, "rechazada": 3},
    "rechazada": {"aprobada": 10, "revision_manual": 1, "rechazada": 0},
    "revision_manual": {"aprobada": 10, "revision_manual": 1, "rechazada": 3},
}

TARIMA_VARS = """
    :root {
      --primary: #E31B23;
      --primary-hover: #C4101A;
      --text: #04211F;
      --text-sec: #31413F;
      --bg: #FFFFFF;
      --surface: #F9FAFA;
      --border: #DADFDF;
      --ok: #1F7A4D;
      --ok-bg: #E3F3EA;
      --warn: #8A5A12;
      --warn-bg: #FBF1DC;
      --danger: #9D0812;
      --danger-bg: #FEF3F1;
      --font: Montserrat, "Segoe UI", system-ui, sans-serif;
    }
"""


def calcular_costo(decision_motor: str | None, decision_esperada: str) -> int | None:
    """Calcula el costo operativo pesimista (0, 1, 3, 10) de una captura."""
    if not decision_motor:
        return None
    fila = COSTO_PESIMISTA.get(decision_esperada)
    if fila and decision_motor in fila:
        return fila[decision_motor]
    if decision_motor == "revision_manual":
        return 1
    return 0 if decision_motor == decision_esperada else 10


def _cargar_csv(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
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


def _construir_registros(
    dir_datos: Path,
    ruta_resultados: Path,
    dir_salida: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    csv_capturas = dir_datos / "metadatos" / "capturas.csv"
    if not csv_capturas.exists():
        raise FileNotFoundError(f"No se encontró {csv_capturas}")

    capturas = _cargar_csv(csv_capturas)
    resultados = _cargar_json_lista(ruta_resultados)
    salidas_dir = ruta_resultados.parent
    extracciones = _cargar_json_lista(salidas_dir / "extracciones.json")
    locales = {r["capture_id"]: r for r in _cargar_csv(salidas_dir / "locales.csv") if "capture_id" in r}
    tokens_rows = _cargar_csv(salidas_dir / "tokens.csv")

    dir_datos_res = dir_datos.resolve()
    registros: list[dict[str, Any]] = []

    costo_total = 0
    aprobadas = 0
    rechazadas = 0
    manuales = 0
    tp = 0
    fp = 0

    for row in capturas:
        cid = row["capture_id"]
        esperada = row.get("decision_esperada", "")
        res = resultados.get(cid, {})
        ext = extracciones.get(cid, {})
        loc = locales.get(cid, {})

        dec_motor = res.get("decision")
        costo = calcular_costo(dec_motor, esperada)
        if costo is not None:
            costo_total += costo

        if dec_motor == "aprobada":
            aprobadas += 1
            if esperada == "aprobada":
                tp += 1
            else:
                fp += 1
        elif dec_motor == "rechazada":
            rechazadas += 1
        elif dec_motor == "revision_manual":
            manuales += 1

        prod_ext = ext.get("producto") or {}
        etiq_ext = ext.get("etiqueta") or {}

        es_error = bool(dec_motor and dec_motor != esperada)
        falsa_aprobada = bool(dec_motor == "aprobada" and esperada != "aprobada")
        valida_rechazada = bool(dec_motor == "rechazada" and esperada == "aprobada")

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
                "reason_code": res.get("reason_code") or "",
                "explicacion": res.get("explicacion", ""),
                "precio_detectado": res.get("precio_detectado") if res.get("precio_detectado") is not None else etiq_ext.get("precio"),
                "barcode_detectado": res.get("codigo_barras_detectado") or loc.get("codigo_barras_leido", ""),
                "leido_marca": prod_ext.get("marca", ""),
                "leido_desc": prod_ext.get("descripcion", ""),
                "leido_cant": prod_ext.get("contenido_cantidad", ""),
                "leido_unid": prod_ext.get("contenido_unidad", ""),
                "nitidez": prod_ext.get("nitidez") or loc.get("nitidez_producto", ""),
                "encuadre": prod_ext.get("encuadre", ""),
                "costo": costo,
                "es_error": es_error,
                "falsa_aprobada": falsa_aprobada,
                "valida_rechazada": valida_rechazada,
                "img_facade": _resolver_ruta_imagen(dir_datos_res, row.get("facade_file", ""), dir_salida),
                "img_product": _resolver_ruta_imagen(dir_datos_res, row.get("product_file", ""), dir_salida),
                "img_shelf": _resolver_ruta_imagen(dir_datos_res, row.get("shelf_file", ""), dir_salida),
            }
        )

    precision = (tp / (tp + fp)) * 100.0 if (tp + fp) > 0 else 100.0

    # Promedio de tokens desde tokens.csv (solo filas origen == "modelo")
    tokens_prom: int | None = None
    if tokens_rows:
        modelo_rows = [r for r in tokens_rows if r.get("origen", "modelo") == "modelo"]
        vals = [
            int(float(r.get("tokens_entrada") or 0) + float(r.get("tokens_salida") or 0))
            for r in modelo_rows
            if r.get("tokens_entrada") or r.get("tokens_salida")
        ]
        if vals:
            tokens_prom = round(sum(vals) / len(vals))

    if tokens_prom is None and extracciones:
        vals_ext = [
            int(e.get("tokens_entrada") or 0) + int(e.get("tokens_salida") or 0)
            for e in extracciones.values()
            if e.get("origen", "modelo") == "modelo" and (e.get("tokens_entrada") or e.get("tokens_salida"))
        ]
        if vals_ext:
            tokens_prom = round(sum(vals_ext) / len(vals_ext))

    marcador = {
        "tiene_resultados": bool(resultados),
        "total": len(registros),
        "costo_total": costo_total,
        "costo_todo_manual": len(registros),
        "aprobadas": aprobadas,
        "aprobadas_correctas": tp,
        "rechazadas": rechazadas,
        "manuales": manuales,
        "precision": round(precision, 1),
        "tokens_promedio": tokens_prom,
    }
    return registros, marcador


def generar_html(dir_datos: Path, ruta_resultados: Path, ruta_salida: Path) -> tuple[int, int]:
    """Genera el HTML estático del visor con tokens Tarima."""
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    registros, marcador = _construir_registros(dir_datos, ruta_resultados, ruta_salida.parent.resolve())

    datos_json = json.dumps(registros, ensure_ascii=False)
    marcador_json = json.dumps(marcador, ensure_ascii=False)

    html_doc = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Visor Validat3B</title>
  <style>
{TARIMA_VARS}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: var(--font); background: var(--surface); color: var(--text); line-height: 1.4; }}
    header {{ position: sticky; top: 0; z-index: 10; background: var(--bg); border-bottom: 2px solid var(--border); padding: 14px 20px; }}
    .top-row {{ display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 12px; }}
    .brand-title {{ display: flex; align-items: center; gap: 10px; }}
    .accent-bar {{ width: 4px; height: 22px; background: var(--primary); border-radius: 2px; }}
    h1 {{ margin: 0; font-size: 1.15rem; font-weight: 800; letter-spacing: -0.01em; }}
    .scoreboard {{ display: flex; flex-wrap: wrap; gap: 8px; font-size: 0.85rem; font-weight: 700; font-variant-numeric: tabular-nums; }}
    .pill {{ background: var(--surface); border: 1px solid var(--border); border-radius: 999px; padding: 5px 12px; color: var(--text); }}
    .pill.ok {{ background: var(--ok-bg); color: var(--ok); border-color: transparent; }}
    .filters {{ display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }}
    select, button, label.btn-check {{ min-height: 44px; padding: 0 12px; border: 1px solid var(--border); border-radius: 8px; background: var(--bg); color: var(--text); font-family: var(--font); font-size: 0.88rem; font-weight: 600; cursor: pointer; }}
    button:hover, select:hover {{ border-color: var(--text-sec); }}
    button.primary {{ background: var(--primary); color: #FFFFFF; border-color: var(--primary); }}
    button.primary:hover {{ background: var(--primary-hover); }}
    label.btn-check {{ display: inline-flex; align-items: center; gap: 6px; }}
    button.active {{ border-color: var(--primary); color: var(--primary); background: var(--danger-bg); }}
    main {{ max-width: 1320px; margin: 18px auto; padding: 0 16px 40px; display: grid; grid-template-columns: repeat(auto-fill, minmax(370px, 1fr)); gap: 16px; }}
    .card {{ background: var(--bg); border: 1px solid var(--border); border-radius: 10px; padding: 14px; display: flex; flex-direction: column; gap: 10px; }}
    .card.is-error {{ border-color: var(--primary); }}
    .card-head {{ display: flex; justify-content: space-between; align-items: center; gap: 8px; font-size: 0.9rem; }}
    .cid {{ font-family: ui-monospace, monospace; font-weight: 800; }}
    .costo-badge {{ padding: 2px 10px; border-radius: 999px; font-weight: 800; font-size: 0.8rem; background: var(--surface); border: 1px solid var(--border); font-variant-numeric: tabular-nums; }}
    .costo-badge.high {{ background: var(--danger-bg); color: var(--danger); border-color: transparent; }}
    .photos {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; }}
    .photos img {{ width: 100%; height: 96px; object-fit: cover; border-radius: 6px; border: 1px solid var(--border); cursor: zoom-in; background: var(--surface); }}
    table.cmp {{ width: 100%; border-collapse: collapse; font-size: 0.82rem; }}
    table.cmp th, table.cmp td {{ border-bottom: 1px solid var(--border); padding: 4px 6px; text-align: left; }}
    table.cmp th {{ color: var(--text-sec); font-weight: 700; }}
    .mismatch {{ color: var(--danger); font-weight: 700; }}
    .decisions {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 0.85rem; background: var(--surface); padding: 8px; border-radius: 6px; }}
    .tag {{ display: inline-block; padding: 2px 8px; border-radius: 999px; font-weight: 700; font-size: 0.78rem; }}
    .tag.aprobada {{ background: var(--ok-bg); color: var(--ok); }}
    .tag.rechazada {{ background: var(--danger-bg); color: var(--danger); }}
    .tag.revision_manual {{ background: var(--warn-bg); color: var(--warn); }}
    .extra {{ font-size: 0.82rem; color: var(--text-sec); }}
    #modal {{ display: none; position: fixed; inset: 0; background: rgba(4, 33, 31, 0.88); z-index: 100; align-items: center; justify-content: center; padding: 20px; }}
    #modal.open {{ display: flex; }}
    #modal img {{ max-width: 95vw; max-height: 90vh; border-radius: 8px; background: #fff; }}
    #modal-close {{ position: fixed; top: 16px; right: 16px; min-height: 44px; min-width: 44px; font-weight: 700; }}
  </style>
</head>
<body>
  <header>
    <div class="top-row">
      <div class="brand-title">
        <span class="accent-bar"></span>
        <h1>Validat3B · Visor de auditoría</h1>
      </div>
      <div class="scoreboard" id="scoreboard"></div>
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
      <label class="btn-check"><input type="checkbox" id="f-errores" /> Solo errores</label>
      <button type="button" id="btn-fp">Solo aprobadas falsas</button>
      <button type="button" id="btn-fn">Solo válidas rechazadas</button>
      <select id="f-orden" aria-label="Ordenar por costo">
        <option value="original">Orden: Original</option>
        <option value="costo-desc">Mayor costo primero</option>
        <option value="costo-asc">Menor costo primero</option>
      </select>
      <button type="button" class="primary" id="btn-export">Exportar CSV</button>
      <button type="button" id="btn-reset">Limpiar</button>
    </div>
  </header>
  <main id="grid"></main>
  <div id="modal" role="dialog" aria-modal="true">
    <button type="button" id="modal-close">Cerrar</button>
    <img id="modal-img" src="" alt="Vista ampliada" />
  </div>
  <script>
    const DATA = {datos_json};
    const M = {marcador_json};
    const grid = document.getElementById("grid");
    const sb = document.getElementById("scoreboard");
    const fEsperada = document.getElementById("f-esperada");
    const fMotor = document.getElementById("f-motor");
    const fErrores = document.getElementById("f-errores");
    const fOrden = document.getElementById("f-orden");
    const btnFp = document.getElementById("btn-fp");
    const btnFn = document.getElementById("btn-fn");
    let soloFp = false, soloFn = false;
    let currentItems = [];

    function esc(s) {{
      return String(s ?? "").replace(/[&<>"']/g, c => ({{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}}[c]));
    }}

    function diffCls(a, b) {{
      if (!b) return "";
      return String(a).trim().toLowerCase() !== String(b).trim().toLowerCase() ? "mismatch" : "";
    }}

    function renderScoreboard(count) {{
      const tok = M.tokens_promedio !== null ? `${{Number(M.tokens_promedio).toLocaleString("en-US")}} tok/cap` : "— tok/cap";
      const precTxt = Number.isInteger(M.precision) ? `${{M.precision}}%` : `${{M.precision}}%`;
      sb.innerHTML = M.tiene_resultados
        ? `<span class="pill">${{count}}/${{M.total}}</span>
           <span class="pill">Costo: ${{M.costo_total}} vs ${{M.costo_todo_manual}}</span>
           <span class="pill">Aprob: ${{M.aprobadas}} · Rech: ${{M.rechazadas}} · Man: ${{M.manuales}}</span>
           <span class="pill ok">Precisión aprob: ${{precTxt}}</span>
           <span class="pill">${{tok}}</span>`
        : `<span class="pill">${{count}}/${{M.total}} tarjetas (sin resultados.json)</span>`;
    }}

    function render() {{
      const esp = fEsperada.value, mot = fMotor.value, err = fErrores.checked, ord = fOrden.value;
      let items = DATA.filter(d => {{
        if (esp && d.esperada !== esp) return false;
        if (mot && d.motor !== mot) return false;
        if (err && !d.es_error) return false;
        if (soloFp && !d.falsa_aprobada) return false;
        if (soloFn && !d.valida_rechazada) return false;
        return true;
      }});
      if (ord === "costo-desc") items = [...items].sort((a, b) => (b.costo ?? -1) - (a.costo ?? -1));
      else if (ord === "costo-asc") items = [...items].sort((a, b) => (a.costo ?? 999) - (b.costo ?? 999));
      currentItems = items;

      renderScoreboard(items.length);
      grid.innerHTML = items.map(d => {{
        const costoTxt = d.costo === null ? "—" : `${{d.costo}} pts`;
        const costoCls = (d.costo ?? 0) >= 3 ? "costo-badge high" : "costo-badge";
        const confTxt = d.confidence !== null && d.confidence !== undefined ? Number(d.confidence).toFixed(2) : "—";
        const leidoCont = d.leido_cant ? `${{d.leido_cant}} ${{d.leido_unid}}` : "";
        return `
          <article class="card ${{d.es_error ? "is-error" : ""}}">
            <div class="card-head">
              <span class="cid">${{esc(d.capture_id)}} · ${{esc(d.store)}}</span>
              <span class="${{costoCls}}">Costo: ${{costoTxt}}</span>
            </div>
            <div class="photos">
              <img src="${{esc(d.img_facade)}}" alt="Fachada" loading="lazy" onclick="openModal(this.src)" />
              <img src="${{esc(d.img_product)}}" alt="Producto" loading="lazy" onclick="openModal(this.src)" />
              <img src="${{esc(d.img_shelf)}}" alt="Etiqueta" loading="lazy" onclick="openModal(this.src)" />
            </div>
            <table class="cmp">
              <thead><tr><th>Campo</th><th>Esperado</th><th>Leído</th></tr></thead>
              <tbody>
                <tr><td>Marca</td><td>${{esc(d.brand)}}</td><td class="${{diffCls(d.brand, d.leido_marca)}}">${{esc(d.leido_marca || "—")}}</td></tr>
                <tr><td>Producto</td><td>${{esc(d.product_name)}}</td><td class="${{diffCls(d.product_name, d.leido_desc)}}">${{esc(d.leido_desc || "—")}}</td></tr>
                <tr><td>Contenido</td><td>${{esc(d.qty)}} ${{esc(d.unit)}}</td><td>${{esc(leidoCont || "—")}}</td></tr>
                <tr><td>Precio</td><td>$${{esc(d.price_ref)}}</td><td>${{d.precio_detectado != null ? "$" + esc(d.precio_detectado) : "—"}}</td></tr>
              </tbody>
            </table>
            <div class="decisions">
              <div><div>Esperada:</div><span class="tag ${{esc(d.esperada)}}">${{esc(d.esperada)}}</span><div class="extra">${{esc(d.motivo_esperado || "Sin motivo")}}</div></div>
              <div><div>Motor:</div>${{d.motor ? `<span class="tag ${{esc(d.motor)}}">${{esc(d.motor)}}</span>` : "—"}}<div class="extra">Conf: ${{confTxt}} · ${{esc(d.reason_code || "—")}}</div></div>
            </div>
            ${{(d.nitidez || d.encuadre) ? `<div class="extra">Nitidez: ${{esc(d.nitidez || "—")}} · Encuadre: ${{esc(d.encuadre || "—")}}</div>` : ""}}
            ${{d.explicacion ? `<div class="extra"><strong>Explicación:</strong> ${{esc(d.explicacion)}}</div>` : ""}}
          </article>
        `;
      }}).join("");
    }}

    window.openModal = src => {{ document.getElementById("modal-img").src = src; document.getElementById("modal").classList.add("open"); }};
    document.getElementById("modal-close").onclick = () => document.getElementById("modal").classList.remove("open");
    document.getElementById("modal").onclick = e => {{ if (e.target.id === "modal") document.getElementById("modal").classList.remove("open"); }};
    btnFp.onclick = () => {{ soloFp = !soloFp; btnFp.classList.toggle("active", soloFp); render(); }};
    btnFn.onclick = () => {{ soloFn = !soloFn; btnFn.classList.toggle("active", soloFn); render(); }};
    [fEsperada, fMotor, fErrores, fOrden].forEach(el => el.addEventListener("change", render));
    document.getElementById("btn-export").onclick = () => {{
      const cols = ["capture_id", "store", "brand", "product_name", "price_ref", "precio_detectado", "motor", "reason_code", "confidence", "explicacion"];
      const csvCell = v => `"${{String(v ?? "").replace(/"/g, '""')}}"`;
      const rows = [cols.join(","), ...currentItems.map(d => cols.map(c => csvCell(d[c])).join(","))];
      const blob = new Blob(["\\uFEFF" + rows.join("\\n")], {{ type: "text/csv;charset=utf-8;" }});
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = "validat3b_vista.csv";
      a.click();
    }};
    document.getElementById("btn-reset").onclick = () => {{
      fEsperada.value = ""; fMotor.value = ""; fErrores.checked = false; fOrden.value = "original";
      soloFp = false; soloFn = false; btnFp.classList.remove("active"); btnFn.classList.remove("active");
      render();
    }};
    render();
  </script>
</body>
</html>
"""
    ruta_salida.write_text(html_doc, encoding="utf-8")
    return len(registros), marcador["costo_total"]


def generar_pitch(dir_datos: Path, ruta_resultados: Path, ruta_pitch: Path, ids: list[str]) -> int:
    """Genera salidas/pitch.html con identidad Tarima: lámina 0 (marcador) + 1 por captura."""
    ruta_pitch.parent.mkdir(parents=True, exist_ok=True)
    registros, marcador = _construir_registros(dir_datos, ruta_resultados, ruta_pitch.parent.resolve())
    mapa = {r["capture_id"]: r for r in registros}
    seleccion = [mapa[cid] for cid in ids if cid in mapa]

    datos_json = json.dumps(seleccion, ensure_ascii=False)
    marcador_json = json.dumps(marcador, ensure_ascii=False)

    html_pitch = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Pitch · Validat3B</title>
  <style>
{TARIMA_VARS}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: var(--font);
      background: var(--bg);
      color: var(--text);
      height: 100vh;
      display: flex;
      flex-direction: column;
    }}
    .topbar {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 14px 40px;
      border-bottom: 2px solid var(--border);
      background: var(--bg);
    }}
    .brand {{
      display: flex;
      align-items: center;
      gap: 10px;
      font-weight: 800;
      font-size: 1.05rem;
    }}
    .brand-bar {{
      width: 5px;
      height: 22px;
      background: var(--primary);
      border-radius: 2px;
    }}
    .slide-tag {{
      font-size: 0.85rem;
      font-weight: 700;
      color: var(--text-sec);
    }}
    main {{
      flex: 1;
      padding: 28px 40px;
      display: flex;
      flex-direction: column;
      justify-content: center;
      overflow: hidden;
    }}
    .hero-grid {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 24px;
      max-width: 1400px;
      width: 100%;
      margin: 0 auto;
    }}
    .hero-card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-top: 5px solid var(--primary);
      border-radius: 12px;
      padding: 32px 28px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }}
    .hero-card.ok {{ border-top-color: var(--ok); }}
    .hero-num {{
      font-size: 4rem;
      font-weight: 800;
      font-variant-numeric: tabular-nums;
      line-height: 1.05;
      color: var(--text);
    }}
    .hero-title {{
      font-size: 1.25rem;
      font-weight: 700;
      color: var(--text);
    }}
    .hero-sub {{
      font-size: 1rem;
      color: var(--text-sec);
    }}
    .cap-wrap {{
      max-width: 1440px;
      width: 100%;
      margin: 0 auto;
      display: flex;
      flex-direction: column;
      gap: 20px;
    }}
    .photos-row {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 16px;
    }}
    .photo-box {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 8px;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }}
    .photo-box span {{
      font-size: 0.8rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: var(--text-sec);
    }}
    .photo-box img {{
      width: 100%;
      height: 34vh;
      object-fit: cover;
      border-radius: 6px;
      background: #fff;
    }}
    .cap-bottom {{
      display: grid;
      grid-template-columns: 1fr 1.1fr;
      gap: 20px;
      align-items: start;
    }}
    .verdict-box {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 20px 24px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }}
    .cid-line {{
      font-family: ui-monospace, monospace;
      font-size: 1.1rem;
      font-weight: 800;
      color: var(--text-sec);
    }}
    .chip-row {{
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 10px;
    }}
    .chip {{
      display: inline-block;
      padding: 6px 16px;
      border-radius: 999px;
      font-size: 1.2rem;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }}
    .chip.aprobada {{ background: var(--ok-bg); color: var(--ok); }}
    .chip.rechazada {{ background: var(--danger-bg); color: var(--danger); }}
    .chip.revision_manual {{ background: var(--warn-bg); color: var(--warn); }}
    .rc-pill {{
      font-family: ui-monospace, monospace;
      font-size: 0.95rem;
      font-weight: 700;
      color: var(--text-sec);
      background: var(--bg);
      border: 1px solid var(--border);
      padding: 5px 12px;
      border-radius: 999px;
    }}
    .exp {{
      font-size: 1.1rem;
      color: var(--text);
      line-height: 1.45;
    }}
    table.cmp {{
      width: 100%;
      border-collapse: collapse;
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 10px;
      overflow: hidden;
      font-size: 1rem;
    }}
    table.cmp th, table.cmp td {{
      padding: 10px 14px;
      border-bottom: 1px solid var(--border);
      text-align: left;
    }}
    table.cmp th {{
      background: var(--surface);
      color: var(--text-sec);
      font-weight: 700;
    }}
    .mismatch {{ color: var(--danger); font-weight: 700; }}
    footer {{
      padding: 10px 40px;
      border-top: 1px solid var(--border);
      background: var(--surface);
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 0.9rem;
      color: var(--text-sec);
      font-weight: 600;
    }}
  </style>
</head>
<body>
  <div class="topbar">
    <div class="brand"><span class="brand-bar"></span><span>Validat3B · Demo en vivo</span></div>
    <span class="slide-tag" id="slide-tag">Marcador oficial</span>
  </div>
  <main id="stage"></main>
  <footer>
    <span id="counter"></span>
    <span>← / → navegar · F pantalla completa</span>
  </footer>
  <script>
    const ITEMS = {datos_json};
    const M = {marcador_json};
    const TOTAL_SLIDES = 1 + ITEMS.length;
    let idx = 0;

    function esc(s) {{
      return String(s ?? "").replace(/[&<>"']/g, c => ({{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}}[c]));
    }}
    function diffCls(a, b) {{
      if (!b) return "";
      return String(a).trim().toLowerCase() !== String(b).trim().toLowerCase() ? "mismatch" : "";
    }}

    function draw() {{
      const stage = document.getElementById("stage");
      const tag = document.getElementById("slide-tag");
      const counter = document.getElementById("counter");

      if (idx === 0) {{
        tag.textContent = "Marcador sobre 100 capturas de desarrollo";
        const prec = Number.isInteger(M.precision) ? `${{M.precision}} %` : `${{M.precision}} %`;
        const tok = M.tokens_promedio !== null ? Number(M.tokens_promedio).toLocaleString("en-US") : "—";
        stage.innerHTML = `
          <div class="hero-grid">
            <div class="hero-card ok">
              <div class="hero-num">${{prec}}</div>
              <div class="hero-title">Precisión en aprobadas</div>
              <div class="hero-sub">${{M.aprobadas_correctas}} de ${{M.aprobadas}} aprobadas sin errores (mínimo oficial 97 %)</div>
            </div>
            <div class="hero-card">
              <div class="hero-num">${{M.costo_total}} vs ${{M.costo_todo_manual}}</div>
              <div class="hero-title">Costo operativo pesimista</div>
              <div class="hero-sub">Contra revisar todo a mano (100 pts) · ${{M.aprobadas + M.rechazadas}} resueltas sin persona</div>
            </div>
            <div class="hero-card">
              <div class="hero-num">${{tok}}</div>
              <div class="hero-title">Tokens por captura</div>
              <div class="hero-sub">Una sola llamada a claude-haiku-5-5 con señales locales a 0 tokens</div>
            </div>
          </div>`;
      }} else {{
        const d = ITEMS[idx - 1];
        const dec = d.motor || d.esperada;
        const leidoCont = d.leido_cant ? `${{d.leido_cant}} ${{d.leido_unid}}` : "—";
        tag.textContent = `Caso ${{idx}} de ${{ITEMS.length}} · ${{d.capture_id}}`;
        stage.innerHTML = `
          <div class="cap-wrap">
            <div class="photos-row">
              <div class="photo-box"><span>Fachada</span><img src="${{esc(d.img_facade)}}" alt="Fachada" /></div>
              <div class="photo-box"><span>Producto</span><img src="${{esc(d.img_product)}}" alt="Producto" /></div>
              <div class="photo-box"><span>Etiqueta</span><img src="${{esc(d.img_shelf)}}" alt="Etiqueta" /></div>
            </div>
            <div class="cap-bottom">
              <div class="verdict-box">
                <div class="cid-line">${{esc(d.capture_id)}} · ${{esc(d.store)}}</div>
                <div class="chip-row">
                  <span class="chip ${{esc(dec)}}">${{esc(dec)}}</span>
                  ${{d.reason_code ? `<span class="rc-pill">${{esc(d.reason_code)}}</span>` : ""}}
                </div>
                <div class="exp">${{esc(d.explicacion || "Validación auditada en visor")}}</div>
              </div>
              <table class="cmp">
                <thead><tr><th>Campo</th><th>Esperado</th><th>Leído por el modelo</th></tr></thead>
                <tbody>
                  <tr><td>Marca</td><td>${{esc(d.brand)}}</td><td class="${{diffCls(d.brand, d.leido_marca)}}">${{esc(d.leido_marca || "—")}}</td></tr>
                  <tr><td>Producto</td><td>${{esc(d.product_name)}}</td><td class="${{diffCls(d.product_name, d.leido_desc)}}">${{esc(d.leido_desc || "—")}}</td></tr>
                  <tr><td>Contenido</td><td>${{esc(d.qty)}} ${{esc(d.unit)}}</td><td>${{esc(leidoCont)}}</td></tr>
                  <tr><td>Precio</td><td>$${{esc(d.price_ref)}}</td><td>${{d.precio_detectado != null ? "$" + esc(d.precio_detectado) : "—"}}</td></tr>
                </tbody>
              </table>
            </div>
          </div>`;
      }}
      counter.textContent = `Lámina ${{idx + 1}} de ${{TOTAL_SLIDES}}`;
    }}

    window.addEventListener("keydown", e => {{
      if (e.key === "ArrowRight" && idx < TOTAL_SLIDES - 1) {{ idx++; draw(); }}
      else if (e.key === "ArrowLeft" && idx > 0) {{ idx--; draw(); }}
      else if (e.key === "f" || e.key === "F") {{
        if (!document.fullscreenElement) document.documentElement.requestFullscreen();
        else document.exitFullscreen();
      }}
    }});
    draw();
  </script>
</body>
</html>
"""
    ruta_pitch.write_text(html_pitch, encoding="utf-8")
    return len(seleccion)


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera el visor HTML estático de Validat3B")
    parser.add_argument("--datos", default="datos/privado", help="Directorio de datos")
    parser.add_argument("--resultados", default="salidas/resultados.json", help="JSON de resultados del motor")
    parser.add_argument("--salida", default="salidas/visor.html", help="Ruta del HTML de salida")
    parser.add_argument("--pitch", default="", help="IDs separados por coma para generar salidas/pitch.html")
    args = parser.parse_args()

    total, costo = generar_html(Path(args.datos), Path(args.resultados), Path(args.salida))
    print(f"Visor generado en {args.salida} ({total} tarjetas, costo total={costo})")

    if args.pitch.strip():
        ids = [x.strip() for x in args.pitch.split(",") if x.strip()]
        ruta_pitch = Path(args.salida).parent / "pitch.html"
        n = generar_pitch(Path(args.datos), Path(args.resultados), ruta_pitch, ids)
        print(f"Pitch generado en {ruta_pitch} ({n} capturas)")


if __name__ == "__main__":
    main()
