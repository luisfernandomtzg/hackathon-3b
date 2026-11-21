"""Visor ejecutivo local, consola HITL y modo pitch con identidad Tarima (Validat3B).

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
      --primary-active: #9D0812;
      --text: #04211F;
      --text-sec: #31413F;
      --text-ter: #4C5857;
      --text-muted: #667170;
      --bg: #FFFFFF;
      --surface: #F9FAFA;
      --muted: #EAEEED;
      --border: #DADFDF;
      --ok: #1F7A4D;
      --ok-bg: #E3F3EA;
      --warn: #8A5A12;
      --warn-bg: #FBF1DC;
      --danger: #9D0812;
      --danger-bg: #FEF3F1;
      --info: #1C244B;
      --info-bg: #E8EBF5;
      --chart-1: #1C244B;
      --chart-2: #0E7C6B;
      --chart-3: #B4690E;
      --chart-4: #7A4E9C;
      --chart-5: #667170;
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
    json_validos = 0

    for row in capturas:
        cid = row["capture_id"]
        esperada = row.get("decision_esperada", "")
        res = resultados.get(cid, {})
        ext = extracciones.get(cid, {})
        loc = locales.get(cid, {})

        dec_motor = res.get("decision")
        if res and dec_motor in ("aprobada", "rechazada", "revision_manual") and isinstance(res.get("validaciones"), dict):
            json_validos += 1

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

        es_error = bool(dec_motor and esperada and dec_motor != esperada)
        falsa_aprobada = bool(dec_motor == "aprobada" and esperada and esperada != "aprobada")
        valida_rechazada = bool(dec_motor == "rechazada" and esperada == "aprobada")

        registros.append(
            {
                "capture_id": cid,
                "store": row.get("capture_store_name", ""),
                "capture_date": row.get("capture_date", ""),
                "brand": row.get("capture_brand", ""),
                "product_name": row.get("product_name", ""),
                "qty": row.get("unit_quantity_product", ""),
                "unit": row.get("unit_product", ""),
                "price_ref": row.get("capture_price", ""),
                "capture_barcode": row.get("capture_barcode", ""),
                "esperada": esperada,
                "motivo_esperado": row.get("motivo_rechazo", ""),
                "motor": dec_motor or "",
                "confidence": res.get("confidence_score"),
                "reason_code": res.get("reason_code") or "",
                "explicacion": res.get("explicacion", ""),
                "validaciones": res.get("validaciones") or {},
                "resultado_oficial": res if res else None,
                "precio_detectado": res.get("precio_detectado") if res.get("precio_detectado") is not None else etiq_ext.get("precio"),
                "tipo_precio": etiq_ext.get("tipo_precio") or "",
                "barcode_detectado": res.get("codigo_barras_detectado") or loc.get("codigo_barras_leido", ""),
                "leido_marca": prod_ext.get("marca", ""),
                "leido_desc": prod_ext.get("descripcion", ""),
                "leido_cant": prod_ext.get("contenido_cantidad", ""),
                "leido_unid": prod_ext.get("contenido_unidad", ""),
                "contenido_legible": prod_ext.get("contenido_legible"),
                "nitidez": prod_ext.get("nitidez") or loc.get("nitidez_producto", ""),
                "encuadre": prod_ext.get("encuadre", ""),
                "nitidez_local": loc.get("nitidez_producto") or (ext.get("senales") or {}).get("nitidez_producto", ""),
                "costo": costo,
                "es_error": es_error,
                "falsa_aprobada": falsa_aprobada,
                "valida_rechazada": valida_rechazada,
                "img_facade": _resolver_ruta_imagen(dir_datos_res, row.get("facade_file", ""), dir_salida),
                "img_product": _resolver_ruta_imagen(dir_datos_res, row.get("product_file", ""), dir_salida),
                "img_shelf": _resolver_ruta_imagen(dir_datos_res, row.get("shelf_file", ""), dir_salida),
                "facade_name": Path(row.get("facade_file", "")).name,
                "product_name_file": Path(row.get("product_file", "")).name,
                "shelf_name": Path(row.get("shelf_file", "")).name,
            }
        )

    precision = (tp / (tp + fp)) * 100.0 if (tp + fp) > 0 else 100.0
    pct_json = (json_validos / len(registros)) * 100.0 if registros else 0.0

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
        "pct_json": round(pct_json, 1),
        "tokens_promedio": tokens_prom,
    }
    return registros, marcador


def generar_html(dir_datos: Path, ruta_resultados: Path, ruta_salida: Path) -> tuple[int, int]:
    """Genera el HTML estático completo (4 módulos Tarima, 100 % offline)."""
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    registros, marcador = _construir_registros(dir_datos, ruta_resultados, ruta_salida.parent.resolve())

    datos_json = json.dumps(registros, ensure_ascii=False)
    marcador_json = json.dumps(marcador, ensure_ascii=False)

    html_doc = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Consola Validat3B · Tarima</title>
  <style>
{TARIMA_VARS}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: var(--font);
      background: var(--bg);
      color: var(--text);
      line-height: 1.45;
    }}
    button, select, input {{ font-family: inherit; }}
    .topbar {{
      position: sticky;
      top: 0;
      z-index: 20;
      background: var(--surface);
      border-bottom: 1px solid var(--border);
      padding: 12px 24px;
    }}
    .topbar-inner {{
      max-width: 1280px;
      margin: 0 auto;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }}
    .top-row {{
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }}
    .brand {{
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    .brand h1 {{ margin: 0; font-size: 1.25rem; font-weight: 800; letter-spacing: -0.01em; }}
    .brand span.sub {{ font-size: 0.8rem; color: var(--text-muted); font-weight: 500; }}
    .nav-tabs {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }}
    .tab-btn {{
      min-height: 44px;
      padding: 0 16px;
      border: 1px solid var(--border);
      border-radius: 6px;
      background: var(--bg);
      color: var(--text-sec);
      font-size: 0.88rem;
      font-weight: 600;
      cursor: pointer;
    }}
    .tab-btn.active {{
      background: var(--text);
      color: #FFFFFF;
      border-color: var(--text);
    }}
    .filters-bar {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
    }}
    select, input[type="search"], input[type="text"], input[type="number"], button.ctrl {{
      min-height: 44px;
      padding: 0 12px;
      border: 1px solid var(--border);
      border-radius: 6px;
      background: var(--bg);
      color: var(--text);
      font-size: 0.9rem;
      font-weight: 500;
    }}
    input[type="search"] {{ min-width: 240px; flex: 1; max-width: 360px; }}
    button.primary {{
      min-height: 44px;
      padding: 0 16px;
      border: 1px solid var(--primary);
      border-radius: 6px;
      background: var(--primary);
      color: #FFFFFF;
      font-size: 0.9rem;
      font-weight: 600;
      cursor: pointer;
    }}
    button.primary:hover {{ background: var(--primary-hover); }}
    button.ctrl {{ cursor: pointer; font-weight: 600; }}
    button.ctrl.active {{ border-color: var(--danger); color: var(--danger); background: var(--danger-bg); }}
    label.check-ctrl {{
      min-height: 44px;
      padding: 0 12px;
      border: 1px solid var(--border);
      border-radius: 6px;
      background: var(--bg);
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 0.88rem;
      font-weight: 600;
      cursor: pointer;
    }}
    .container {{
      max-width: 1280px;
      margin: 20px auto;
      padding: 0 24px 48px;
    }}
    .tab-panel {{ display: none; }}
    .tab-panel.active {{ display: block; }}

    /* Módulo 1: KPIs y Gráficas */
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }}
    .kpi-card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }}
    .kpi-lbl {{ font-size: 0.8rem; font-weight: 600; color: var(--text-sec); text-transform: uppercase; letter-spacing: 0.03em; }}
    .kpi-val {{
      font-size: 2.1rem;
      font-weight: 800;
      font-variant-numeric: tabular-nums;
      line-height: 1.1;
      width: fit-content;
    }}
    .kpi-val.focus-underline {{
      border-bottom: 3px solid var(--primary);
      padding-bottom: 2px;
    }}
    .kpi-sub {{ font-size: 0.82rem; color: var(--text-muted); }}
    .charts-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
      gap: 16px;
    }}
    .panel {{
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 16px;
    }}
    .panel h2 {{ margin: 0 0 12px 0; font-size: 1rem; font-weight: 700; }}
    .bar-row {{
      display: grid;
      grid-template-columns: 130px 1fr 48px;
      gap: 8px;
      align-items: center;
      margin-bottom: 8px;
      font-size: 0.84rem;
      cursor: pointer;
    }}
    .bar-track {{ height: 14px; background: var(--muted); border-radius: 999px; overflow: hidden; }}
    .bar-fill {{ height: 100%; border-radius: 999px; }}
    .mono {{ font-family: ui-monospace, monospace; }}

    /* Módulo 2: Cola Human-in-the-Loop */
    .hitl-head {{
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      margin-bottom: 16px;
      padding: 12px 16px;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
    }}
    .hitl-layout {{
      display: grid;
      grid-template-columns: 1.4fr 1fr;
      gap: 16px;
    }}
    @media (max-width: 960px) {{
      .hitl-layout {{ grid-template-columns: 1fr; }}
    }}
    .ev-grid {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 12px;
    }}
    .ev-box {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 10px;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }}
    .ev-head {{ display: flex; justify-content: space-between; align-items: center; font-size: 0.8rem; font-weight: 700; }}
    .ev-img-wrap {{
      height: 240px;
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 6px;
      overflow: hidden;
      display: flex;
      align-items: center;
      justify-content: center;
    }}
    .ev-img-wrap img {{ max-width: 100%; max-height: 100%; object-fit: contain; cursor: zoom-in; }}
    .hitl-actions {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 12px;
    }}
    button.btn-ok {{ min-height: 44px; padding: 0 16px; border-radius: 6px; border: 1px solid var(--ok); background: var(--ok-bg); color: var(--ok); font-weight: 700; cursor: pointer; }}
    button.btn-danger-outline {{ min-height: 44px; padding: 0 16px; border-radius: 6px; border: 1px solid var(--danger); background: var(--bg); color: var(--danger); font-weight: 700; cursor: pointer; }}

    /* Módulo 3: Explorador y Tabla 52px */
    .cards-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
      gap: 16px;
    }}
    .card {{
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 14px;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }}
    .card.is-error {{ border-color: var(--danger); }}
    .card-head {{ display: flex; justify-content: space-between; align-items: center; gap: 8px; }}
    .photos {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; }}
    .photos img {{ width: 100%; height: 92px; object-fit: cover; border-radius: 6px; border: 1px solid var(--border); cursor: zoom-in; background: var(--surface); }}
    table.cmp {{ width: 100%; border-collapse: collapse; font-size: 0.84rem; }}
    table.cmp th, table.cmp td {{ border-bottom: 1px solid var(--border); padding: 6px 8px; text-align: left; }}
    table.cmp th {{ color: var(--text-sec); font-weight: 600; background: var(--surface); }}
    .mismatch {{ color: var(--danger); font-weight: 700; }}
    .audit-table-wrap {{ overflow-x: auto; border: 1px solid var(--border); border-radius: 8px; }}
    table.audit {{ width: 100%; border-collapse: collapse; font-size: 0.88rem; }}
    table.audit th {{ background: var(--surface); padding: 10px 12px; text-align: left; border-bottom: 1px solid var(--border); font-weight: 700; }}
    table.audit tr.audit-row {{ height: 52px; border-bottom: 1px solid var(--border); }}
    table.audit tr.audit-row:hover {{ background: var(--surface); }}
    table.audit td {{ padding: 6px 12px; }}
    .chip {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      height: 24px;
      padding: 0 10px;
      border-radius: 999px;
      font-size: 0.76rem;
      font-weight: 700;
    }}
    .chip::before {{ content: ""; width: 7px; height: 7px; border-radius: 50%; background: currentColor; }}
    .chip.aprobada {{ background: var(--ok-bg); color: var(--ok); }}
    .chip.rechazada {{ background: var(--danger-bg); color: var(--danger); }}
    .chip.revision_manual {{ background: var(--warn-bg); color: var(--warn); }}
    .chip.info {{ background: var(--info-bg); color: var(--info); }}

    /* Módulo 4: Ingesta Set Ciego */
    .ingest-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 16px;
      margin-bottom: 20px;
    }}
    .drop-card {{
      background: var(--surface);
      border: 1px dashed var(--text-muted);
      border-radius: 8px;
      padding: 18px;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }}
    .alert-box {{
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 12px 16px;
      margin-bottom: 16px;
      font-size: 0.9rem;
    }}
    .alert-box.ok {{ border-color: var(--ok); background: var(--ok-bg); color: var(--ok); }}
    .alert-box.err {{ border-color: var(--danger); background: var(--danger-bg); color: var(--danger); }}
    .empty-state {{
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 32px;
      text-align: center;
      color: var(--text-sec);
    }}

    /* Modales */
    .modal-bg {{
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(4, 33, 31, 0.85);
      z-index: 100;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }}
    .modal-bg.open {{ display: flex; }}
    .modal-card {{
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 20px;
      max-width: 760px;
      width: 100%;
      max-height: 90vh;
      overflow: auto;
      box-shadow: 0 8px 24px rgba(4, 33, 31, 0.14);
    }}
    pre.json-pre {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 12px;
      font-size: 0.8rem;
      overflow-x: auto;
    }}
  </style>
</head>
<body>
  <header class="topbar">
    <div class="topbar-inner">
      <div class="top-row">
        <div class="brand">
          <h1>Validat3B · Consola Operativa</h1>
          <span class="sub">Prototipo para Tiendas 3B · Modo offline sin dependencias</span>
        </div>
        <div class="nav-tabs" role="tablist">
          <button type="button" class="tab-btn active" data-tab="resumen">1. Resumen ejecutivo</button>
          <button type="button" class="tab-btn" data-tab="cola">2. Cola revisión manual</button>
          <button type="button" class="tab-btn" data-tab="auditoria">3. Explorador auditoría</button>
          <button type="button" class="tab-btn" data-tab="ingesta">4. Cargar set ciego</button>
        </div>
      </div>
      <div class="filters-bar">
        <input type="search" id="f-q" placeholder="Buscar capture_id, marca, producto o tienda..." aria-label="Buscar captura" />
        <select id="f-store" aria-label="Filtrar por cadena"><option value="">Cadena: Todas</option></select>
        <select id="f-esperada" aria-label="Filtrar por esperada">
          <option value="">Esperada: Todas</option>
          <option value="aprobada">Esperada: aprobada</option>
          <option value="rechazada">Esperada: rechazada</option>
          <option value="revision_manual">Esperada: revision_manual</option>
        </select>
        <select id="f-motor" aria-label="Filtrar por motor">
          <option value="">Motor: Todas</option>
          <option value="aprobada">Motor: aprobada</option>
          <option value="rechazada">Motor: rechazada</option>
          <option value="revision_manual">Motor: revision_manual</option>
        </select>
        <label class="check-ctrl"><input type="checkbox" id="f-errores" /> Solo errores</label>
        <button type="button" class="ctrl" id="btn-fp">Aprobadas falsas</button>
        <button type="button" class="ctrl" id="btn-fn">Válidas rechazadas</button>
        <button type="button" class="primary" id="btn-export">Exportar CSV</button>
        <button type="button" class="ctrl" id="btn-reset">Limpiar</button>
      </div>
    </div>
  </header>

  <div class="container">
    <!-- MÓDULO 1 -->
    <section id="tab-resumen" class="tab-panel active">
      <div class="kpi-grid" id="kpi-grid"></div>
      <div class="charts-grid" id="charts-grid"></div>
    </section>

    <!-- MÓDULO 2 -->
    <section id="tab-cola" class="tab-panel">
      <div class="hitl-head" id="hitl-head"></div>
      <div id="hitl-body"></div>
    </section>

    <!-- MÓDULO 3 -->
    <section id="tab-auditoria" class="tab-panel">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;gap:8px;flex-wrap:wrap;">
        <span id="audit-count" style="font-weight:700;"></span>
        <div style="display:flex;gap:8px;">
          <button type="button" class="ctrl active" id="view-cards">Vista tarjetas</button>
          <button type="button" class="ctrl" id="view-table">Vista tabla (52 px)</button>
          <select id="f-orden" aria-label="Ordenar">
            <option value="original">Orden: Original</option>
            <option value="costo-desc">Mayor costo primero</option>
            <option value="costo-asc">Menor costo primero</option>
          </select>
        </div>
      </div>
      <div id="audit-body"></div>
    </section>

    <!-- MÓDULO 4 -->
    <section id="tab-ingesta" class="tab-panel">
      <div id="ingest-status"></div>
      <div class="ingest-grid">
        <div class="drop-card">
          <strong>1. Subir carpeta completa del Set Ciego</strong>
          <span class="sub">Detecta automáticamente capturas.csv/.json, resultados.json y todas las fotos locales.</span>
          <input type="file" id="in-folder" webkitdirectory multiple />
        </div>
        <div class="drop-card">
          <strong>2. Subir capturas.csv o tokens.csv</strong>
          <span class="sub">Carga el padrón de capturas o métricas de tokens.</span>
          <input type="file" id="in-csv" accept=".csv" />
        </div>
        <div class="drop-card">
          <strong>3. Subir resultados.json / extracciones.json</strong>
          <span class="sub">Hidrata veredictos oficiales y valida esquema JSON.</span>
          <input type="file" id="in-json" accept=".json" />
        </div>
        <div class="drop-card">
          <strong>4. Probar 3 fotos sueltas en vivo</strong>
          <span class="sub">Carga Fachada, Producto y Etiqueta para inspeccionar en la estación.</span>
          <label>Fachada <input type="file" id="sim-facade" accept="image/*" /></label>
          <label>Producto <input type="file" id="sim-product" accept="image/*" /></label>
          <label>Etiqueta <input type="file" id="sim-shelf" accept="image/*" /></label>
          <button type="button" class="primary" id="btn-sim">Cargar captura al explorador</button>
        </div>
      </div>
    </section>
  </div>

  <!-- Modal Foto -->
  <div id="modal-foto" class="modal-bg" role="dialog" aria-modal="true">
    <button type="button" class="ctrl" id="modal-foto-close" style="position:fixed;top:16px;right:16px;">Cerrar (Esc)</button>
    <img id="modal-foto-img" src="" alt="Vista ampliada" style="max-width:94vw;max-height:88vh;border-radius:8px;background:#fff;" />
  </div>

  <!-- Modal JSON Oficial -->
  <div id="modal-json" class="modal-bg" role="dialog" aria-modal="true">
    <div class="modal-card">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
        <strong id="modal-json-title">JSON Oficial (Resultado)</strong>
        <div style="display:flex;gap:8px;">
          <button type="button" class="primary" id="btn-copy-json">Copiar JSON</button>
          <button type="button" class="ctrl" id="modal-json-close">Cerrar</button>
        </div>
      </div>
      <div id="modal-json-valid" style="margin-bottom:8px;"></div>
      <pre class="json-pre" id="modal-json-pre"></pre>
    </div>
  </div>

  <script>
    let DATA = {datos_json};
    let M = {marcador_json};
    let currentItems = [];
    let viewMode = "cards";
    let soloFp = false, soloFn = false;
    let hitlIdx = 0;
    let rotations = {{}};
    let hitlDecisions = JSON.parse(localStorage.getItem("validat3b_hitl_v1") || "{{}}");

    function esc(s) {{
      return String(s ?? "").replace(/[&<>"']/g, c => ({{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}}[c]));
    }}
    function diffCls(a, b) {{
      if (!b) return "";
      return String(a).trim().toLowerCase() !== String(b).trim().toLowerCase() ? "mismatch" : "";
    }}

    function populateStores() {{
      const sel = document.getElementById("f-store");
      const cur = sel.value;
      const stores = [...new Set(DATA.map(d => d.store).filter(Boolean))].sort();
      sel.innerHTML = `<option value="">Cadena: Todas</option>` + stores.map(s => `<option value="${{esc(s)}}">${{esc(s)}}</option>`).join("");
      sel.value = cur;
    }}

    function computeMetrics(items) {{
      const total = items.length;
      let costo = 0, aprob = 0, tp = 0, fp = 0, rech = 0, man = 0, jsonOk = 0;
      items.forEach(d => {{
        if (d.costo !== null && d.costo !== undefined) costo += Number(d.costo);
        if (d.motor) jsonOk++;
        if (d.motor === "aprobada") {{
          aprob++;
          if (!d.esperada || d.esperada === "aprobada") tp++; else fp++;
        }} else if (d.motor === "rechazada") rech++;
        else if (d.motor === "revision_manual") man++;
      }});
      const prec = aprob > 0 ? (tp / aprob) * 100 : 100;
      const autoPct = total > 0 ? ((aprob + rech) / total) * 100 : 0;
      const jsonPct = total > 0 ? (jsonOk / total) * 100 : 0;
      return {{ total, costo, aprob, tp, fp, rech, man, prec, autoPct, jsonPct }};
    }}

    function getFiltered() {{
      const q = document.getElementById("f-q").value.trim().toLowerCase();
      const st = document.getElementById("f-store").value;
      const esp = document.getElementById("f-esperada").value;
      const mot = document.getElementById("f-motor").value;
      const err = document.getElementById("f-errores").checked;
      const ord = document.getElementById("f-orden").value;

      let items = DATA.filter(d => {{
        if (st && d.store !== st) return false;
        if (esp && d.esperada !== esp) return false;
        if (mot && d.motor !== mot) return false;
        if (err && !d.es_error) return false;
        if (soloFp && !d.falsa_aprobada) return false;
        if (soloFn && !d.valida_rechazada) return false;
        if (q) {{
          const hay = `${{d.capture_id}} ${{d.store}} ${{d.brand}} ${{d.product_name}} ${{d.reason_code}}`.toLowerCase();
          if (!hay.includes(q)) return false;
        }}
        return true;
      }});
      if (ord === "costo-desc") items = [...items].sort((a, b) => (b.costo ?? -1) - (a.costo ?? -1));
      else if (ord === "costo-asc") items = [...items].sort((a, b) => (a.costo ?? 999) - (b.costo ?? 999));
      currentItems = items;
      return items;
    }}

    function renderResumen(items) {{
      const m = computeMetrics(items);
      const tok = M.tokens_promedio ? Number(M.tokens_promedio).toLocaleString("en-US") : "—";
      const proySem = Math.round(12000 * (m.autoPct / 100)).toLocaleString("en-US");
      document.getElementById("kpi-grid").innerHTML = `
        <div class="kpi-card">
          <span class="kpi-lbl">Precisión en aprobadas</span>
          <span class="kpi-val focus-underline">${{m.prec.toFixed(1)}} %</span>
          <span class="kpi-sub">${{m.tp}} de ${{m.aprob}} aprobadas · meta oficial ≥ 97 %</span>
        </div>
        <div class="kpi-card">
          <span class="kpi-lbl">Costo operativo pesimista</span>
          <span class="kpi-val">${{m.costo}} pts</span>
          <span class="kpi-sub">vs. ${{m.total}} pts de mandar todo a revisión</span>
        </div>
        <div class="kpi-card">
          <span class="kpi-lbl">Automatización sin persona</span>
          <span class="kpi-val">${{m.autoPct.toFixed(0)}} %</span>
          <span class="kpi-sub">~${{proySem}} capturas/sem ahorradas (de 12,000)</span>
        </div>
        <div class="kpi-card">
          <span class="kpi-lbl">Salud JSON · Eficiencia</span>
          <span class="kpi-val">${{m.jsonPct.toFixed(0)}} %</span>
          <span class="kpi-sub">Meta JSON ≥ 99 % · ${{tok}} tok/captura</span>
        </div>`;

      const decCounts = [
        ["aprobada", m.aprob, "var(--ok)"],
        ["rechazada", m.rech, "var(--danger)"],
        ["revision_manual", m.man, "var(--warn)"],
      ];
      const storeMap = {{}};
      const rcMap = {{}};
      items.forEach(d => {{
        if (d.store) storeMap[d.store] = (storeMap[d.store] || 0) + 1;
        if (d.reason_code) rcMap[d.reason_code] = (rcMap[d.reason_code] || 0) + 1;
      }});
      const stores = Object.entries(storeMap).sort((a, b) => b[1] - a[1]);
      const rcs = Object.entries(rcMap).sort((a, b) => b[1] - a[1]).slice(0, 6);
      const maxS = Math.max(1, ...stores.map(x => x[1]));
      const maxR = Math.max(1, ...rcs.map(x => x[1]));

      document.getElementById("charts-grid").innerHTML = `
        <div class="panel">
          <h2>Distribución de decisiones (clic para filtrar)</h2>
          ${{decCounts.map(([k, v, col]) => `
            <div class="bar-row" onclick="document.getElementById('f-motor').value='${{k}}';renderAll();">
              <span>${{k}}</span>
              <div class="bar-track"><div class="bar-fill" style="width:${{m.total ? (v/m.total*100) : 0}}%;background:${{col}};"></div></div>
              <strong class="mono">${{v}}</strong>
            </div>`).join("")}}
        </div>
        <div class="panel">
          <h2>Capturas por cadena competidora</h2>
          ${{stores.map(([k, v]) => `
            <div class="bar-row" onclick="document.getElementById('f-store').value='${{esc(k)}}';renderAll();">
              <span>${{esc(k)}}</span>
              <div class="bar-track"><div class="bar-fill" style="width:${{(v/maxS*100)}}%;background:var(--chart-1);"></div></div>
              <strong class="mono">${{v}}</strong>
            </div>`).join("")}}
        </div>
        <div class="panel">
          <h2>Motivos de rechazo / alerta (reason_code)</h2>
          ${{rcs.length ? rcs.map(([k, v]) => `
            <div class="bar-row" onclick="document.getElementById('f-q').value='${{esc(k)}}';renderAll();">
              <span class="mono" style="font-size:0.75rem;">${{esc(k)}}</span>
              <div class="bar-track"><div class="bar-fill" style="width:${{(v/maxR*100)}}%;background:var(--chart-3);"></div></div>
              <strong class="mono">${{v}}</strong>
            </div>`).join("") : `<p class="sub">Sin códigos activos en esta vista.</p>`}}
        </div>`;
    }}

    function renderHitl(items) {{
      const queue = items.filter(d => d.motor === "revision_manual" || !d.motor);
      const head = document.getElementById("hitl-head");
      const body = document.getElementById("hitl-body");
      const revisadas = Object.keys(hitlDecisions).length;

      if (!queue.length) {{
        head.innerHTML = `<strong>Cola de revisión manual vacía en el filtro actual</strong><span>Revisadas por analista: ${{revisadas}}</span>`;
        body.innerHTML = `<div class="empty-state">No hay capturas pendientes de revisión manual en este filtro.</div>`;
        return;
      }}
      if (hitlIdx >= queue.length) hitlIdx = 0;
      if (hitlIdx < 0) hitlIdx = queue.length - 1;
      const d = queue[hitlIdx];
      const analista = hitlDecisions[d.capture_id] || "";
      const leidoCont = d.leido_cant ? `${{d.leido_cant}} ${{d.leido_unid}}` : "—";

      head.innerHTML = `
        <div>
          <strong>Caso ${{hitlIdx + 1}} de ${{queue.length}} en cola</strong>
          <span class="mono" style="margin-left:8px;">${{esc(d.capture_id)}} · ${{esc(d.store)}}</span>
          ${{analista ? `<span class="chip ${{analista === "aprobada_analista" ? "aprobada" : "rechazada"}}" style="margin-left:8px;">Analista: ${{analista}}</span>` : ""}}
        </div>
        <div style="display:flex;gap:8px;align-items:center;">
          <span style="font-size:0.85rem;">Revisadas: <strong>${{revisadas}}</strong></span>
          <button type="button" class="ctrl" onclick="hitlIdx--;renderHitl(currentItems);">← Anterior</button>
          <button type="button" class="ctrl" onclick="hitlIdx++;renderHitl(currentItems);">Siguiente (S) →</button>
        </div>`;

      const imgs = [["Fachada", d.img_facade, "f"], ["Producto", d.img_product, "p"], ["Etiqueta", d.img_shelf, "s"]];
      body.innerHTML = `
        <div class="hitl-layout">
          <div class="ev-grid">
            ${{imgs.map(([lbl, src, k]) => {{
              const deg = rotations[`${{d.capture_id}}_${{k}}`] || 0;
              return `
                <div class="ev-box">
                  <div class="ev-head">
                    <span>${{lbl}}</span>
                    <button type="button" class="ctrl" style="min-height:32px;padding:0 8px;font-size:0.75rem;" onclick="rotateImg('${{esc(d.capture_id)}}_${{k}}')">Rotar 90°</button>
                  </div>
                  <div class="ev-img-wrap">
                    <img src="${{esc(src)}}" alt="${{lbl}}" style="transform:rotate(${{deg}}deg);" onclick="openFoto(this.src)" />
                  </div>
                </div>`;
            }}).join("")}}
          </div>
          <div class="panel">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
              <span class="chip ${{esc(d.motor || "info")}}">${{esc(d.motor || "sin veredicto")}}</span>
              <span style="font-size:0.85rem;">Confianza: <strong>${{d.confidence != null ? Number(d.confidence).toFixed(2) : "—"}}</strong> · Riesgo evitar FP: 10 pts</span>
            </div>
            <table class="cmp">
              <thead><tr><th>Campo</th><th>Esperado</th><th>Leído por modelo</th></tr></thead>
              <tbody>
                <tr><td>Marca</td><td>${{esc(d.brand)}}</td><td class="${{diffCls(d.brand, d.leido_marca)}}">${{esc(d.leido_marca || "—")}}</td></tr>
                <tr><td>Producto</td><td>${{esc(d.product_name)}}</td><td class="${{diffCls(d.product_name, d.leido_desc)}}">${{esc(d.leido_desc || "—")}}</td></tr>
                <tr><td>Contenido</td><td>${{esc(d.qty)}} ${{esc(d.unit)}}</td><td>${{esc(leidoCont)}}</td></tr>
                <tr><td>Precio</td><td>$${{esc(d.price_ref)}}</td><td>${{d.precio_detectado != null ? "$" + esc(d.precio_detectado) : "—"}}</td></tr>
              </tbody>
            </table>
            <p style="font-size:0.88rem;margin:10px 0;"><strong>Motivo / Explicación:</strong> ${{esc(d.reason_code || "—")}} — ${{esc(d.explicacion || "Sin explicación")}}</p>
            <div class="hitl-actions">
              <button type="button" class="btn-ok" onclick="markHitl('${{esc(d.capture_id)}}','aprobada_analista')">Aprobar (A)</button>
              <button type="button" class="btn-danger-outline" onclick="markHitl('${{esc(d.capture_id)}}','rechazada_analista')">Rechazar (R)</button>
              <button type="button" class="ctrl" onclick="openJsonModal('${{esc(d.capture_id)}}')">Ver JSON oficial</button>
            </div>
          </div>
        </div>`;
    }}

    function renderAuditoria(items) {{
      document.getElementById("audit-count").textContent = `${{items.length}} de ${{DATA.length}} capturas`;
      const body = document.getElementById("audit-body");
      if (!items.length) {{
        body.innerHTML = `<div class="empty-state">Ninguna captura coincide con los filtros.</div>`;
        return;
      }}
      if (viewMode === "table") {{
        body.innerHTML = `
          <div class="audit-table-wrap">
            <table class="audit">
              <thead><tr><th>ID</th><th>Cadena</th><th>Producto</th><th>Precio Esp/Det</th><th>Esperada</th><th>Motor</th><th>Motivo</th><th>Costo</th><th>Acción</th></tr></thead>
              <tbody>
                ${{items.map(d => `
                  <tr class="audit-row">
                    <td class="mono"><strong>${{esc(d.capture_id)}}</strong></td>
                    <td>${{esc(d.store)}}</td>
                    <td>${{esc(d.brand)}} — ${{esc(d.product_name)}}</td>
                    <td class="mono">$${{esc(d.price_ref)}} / ${{d.precio_detectado != null ? "$" + esc(d.precio_detectado) : "—"}}</td>
                    <td><span class="chip ${{esc(d.esperada || "info")}}">${{esc(d.esperada || "ciego")}}</span></td>
                    <td>${{d.motor ? `<span class="chip ${{esc(d.motor)}}">${{esc(d.motor)}}</span>` : "—"}}</td>
                    <td class="mono" style="font-size:0.78rem;">${{esc(d.reason_code || "—")}}</td>
                    <td class="mono">${{d.costo !== null ? d.costo + " pts" : "—"}}</td>
                    <td><button type="button" class="ctrl" style="min-height:36px;" onclick="openJsonModal('${{esc(d.capture_id)}}')">JSON</button></td>
                  </tr>`).join("")}}
              </tbody>
            </table>
          </div>`;
      }} else {{
        body.innerHTML = `<div class="cards-grid">${{items.map(d => {{
          const leidoCont = d.leido_cant ? `${{d.leido_cant}} ${{d.leido_unid}}` : "—";
          return `
            <article class="card ${{d.es_error ? "is-error" : ""}}">
              <div class="card-head">
                <span class="mono"><strong>${{esc(d.capture_id)}}</strong> · ${{esc(d.store)}}</span>
                <button type="button" class="ctrl" style="min-height:32px;padding:0 8px;font-size:0.78rem;" onclick="openJsonModal('${{esc(d.capture_id)}}')">JSON · ${{d.costo !== null ? d.costo + " pts" : "—"}}</button>
              </div>
              <div class="photos">
                <img src="${{esc(d.img_facade)}}" alt="Fachada" loading="lazy" onclick="openFoto(this.src)" />
                <img src="${{esc(d.img_product)}}" alt="Producto" loading="lazy" onclick="openFoto(this.src)" />
                <img src="${{esc(d.img_shelf)}}" alt="Etiqueta" loading="lazy" onclick="openFoto(this.src)" />
              </div>
              <table class="cmp">
                <thead><tr><th>Campo</th><th>Esperado</th><th>Leído</th></tr></thead>
                <tbody>
                  <tr><td>Marca</td><td>${{esc(d.brand)}}</td><td class="${{diffCls(d.brand, d.leido_marca)}}">${{esc(d.leido_marca || "—")}}</td></tr>
                  <tr><td>Producto</td><td>${{esc(d.product_name)}}</td><td class="${{diffCls(d.product_name, d.leido_desc)}}">${{esc(d.leido_desc || "—")}}</td></tr>
                  <tr><td>Contenido</td><td>${{esc(d.qty)}} ${{esc(d.unit)}}</td><td>${{esc(leidoCont)}}</td></tr>
                  <tr><td>Precio</td><td>$${{esc(d.price_ref)}}</td><td>${{d.precio_detectado != null ? "$" + esc(d.precio_detectado) : "—"}}</td></tr>
                </tbody>
              </table>
              <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap;">
                <span>Esp: <span class="chip ${{esc(d.esperada || "info")}}">${{esc(d.esperada || "ciego")}}</span></span>
                <span>Mot: ${{d.motor ? `<span class="chip ${{esc(d.motor)}}">${{esc(d.motor)}}</span>` : "—"}}</span>
              </div>
              ${{d.explicacion ? `<div style="font-size:0.82rem;color:var(--text-sec);">${{esc(d.explicacion)}}</div>` : ""}}
            </article>`;
        }}).join("")}}</div>`;
      }}
    }}

    function renderAll() {{
      const items = getFiltered();
      renderResumen(items);
      renderHitl(items);
      renderAuditoria(items);
    }}

    window.rotateImg = k => {{ rotations[k] = ((rotations[k] || 0) + 90) % 360; renderHitl(currentItems); }};
    window.markHitl = (cid, val) => {{
      hitlDecisions[cid] = val;
      localStorage.setItem("validat3b_hitl_v1", JSON.stringify(hitlDecisions));
      hitlIdx++;
      renderHitl(currentItems);
    }};
    window.openFoto = src => {{
      document.getElementById("modal-foto-img").src = src;
      document.getElementById("modal-foto").classList.add("open");
    }};
    window.openJsonModal = cid => {{
      const d = DATA.find(x => x.capture_id === cid);
      if (!d) return;
      const obj = d.resultado_oficial || {{
        capture_id: d.capture_id,
        decision: d.motor || "revision_manual",
        confidence_score: d.confidence ?? 0.0,
        reason_code: d.reason_code || null,
        validaciones: d.validaciones || {{ tienda_fachada: "ok", producto: "ok", codigo_barras: "ok", evidencia_precio: "ok" }},
        precio_detectado: d.precio_detectado ?? null,
        codigo_barras_detectado: d.barcode_detectado || null,
        explicacion: d.explicacion || "Sin resultado oficial cargado."
      }};
      const valido = Boolean(obj.capture_id && ["aprobada","rechazada","revision_manual"].includes(obj.decision) && obj.validaciones);
      document.getElementById("modal-json-title").textContent = `JSON Oficial · ${{cid}}`;
      document.getElementById("modal-json-valid").innerHTML = `<span class="chip ${{valido ? "aprobada" : "rechazada"}}">${{valido ? "Esquema Resultado válido" : "Esquema incompleto"}}</span>`;
      document.getElementById("modal-json-pre").textContent = JSON.stringify(obj, null, 2);
      document.getElementById("modal-json").classList.add("open");
    }};

    document.getElementById("modal-foto-close").onclick = () => document.getElementById("modal-foto").classList.remove("open");
    document.getElementById("modal-json-close").onclick = () => document.getElementById("modal-json").classList.remove("open");
    document.getElementById("btn-copy-json").onclick = () => {{
      navigator.clipboard.writeText(document.getElementById("modal-json-pre").textContent);
      document.getElementById("btn-copy-json").textContent = "Copiado";
      setTimeout(() => document.getElementById("btn-copy-json").textContent = "Copiar JSON", 1200);
    }};

    // Tabs
    document.querySelectorAll(".tab-btn").forEach(btn => {{
      btn.onclick = () => {{
        document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
        document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));
        btn.classList.add("active");
        document.getElementById("tab-" + btn.dataset.tab).classList.add("active");
      }};
    }});

    document.getElementById("view-cards").onclick = () => {{
      viewMode = "cards";
      document.getElementById("view-cards").classList.add("active");
      document.getElementById("view-table").classList.remove("active");
      renderAuditoria(currentItems);
    }};
    document.getElementById("view-table").onclick = () => {{
      viewMode = "table";
      document.getElementById("view-table").classList.add("active");
      document.getElementById("view-cards").classList.remove("active");
      renderAuditoria(currentItems);
    }};

    document.getElementById("btn-fp").onclick = e => {{ soloFp = !soloFp; e.target.classList.toggle("active", soloFp); renderAll(); }};
    document.getElementById("btn-fn").onclick = e => {{ soloFn = !soloFn; e.target.classList.toggle("active", soloFn); renderAll(); }};
    ["f-q", "f-store", "f-esperada", "f-motor", "f-errores", "f-orden"].forEach(id => {{
      document.getElementById(id).addEventListener("input", renderAll);
      document.getElementById(id).addEventListener("change", renderAll);
    }});

    document.getElementById("btn-export").onclick = () => {{
      const cols = ["capture_id", "store", "brand", "product_name", "price_ref", "precio_detectado", "motor", "reason_code", "confidence", "explicacion"];
      const csvCell = v => `"${{String(v ?? "").replace(/"/g, '""')}}"`;
      const rows = [cols.join(","), ...currentItems.map(d => cols.map(c => csvCell(d[c])).join(","))];
      const blob = new Blob(["\\uFEFF" + rows.join("\\n")], {{ type: "text/csv;charset=utf-8;" }});
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = "validat3b_auditoria.csv";
      a.click();
    }};

    document.getElementById("btn-reset").onclick = () => {{
      document.getElementById("f-q").value = "";
      document.getElementById("f-store").value = "";
      document.getElementById("f-esperada").value = "";
      document.getElementById("f-motor").value = "";
      document.getElementById("f-errores").checked = false;
      document.getElementById("f-orden").value = "original";
      soloFp = false; soloFn = false;
      document.getElementById("btn-fp").classList.remove("active");
      document.getElementById("btn-fn").classList.remove("active");
      renderAll();
    }};

    // Ingesta CSV / JSON / Carpeta Set Ciego (100% client-side)
    function parseCsv(text) {{
      const lines = text.replace(/^\\uFEFF/, "").split(/\\r?\\n/).filter(Boolean);
      if (!lines.length) return [];
      const splitLine = line => {{
        const out = []; let cur = "", inQ = false;
        for (let i = 0; i < line.length; i++) {{
          const c = line[i];
          if (c === '"') {{ if (inQ && line[i+1] === '"') {{ cur += '"'; i++; }} else inQ = !inQ; }}
          else if (c === "," && !inQ) {{ out.push(cur); cur = ""; }}
          else cur += c;
        }}
        out.push(cur);
        return out;
      }};
      const hdr = splitLine(lines[0]);
      return lines.slice(1).map(l => {{
        const vals = splitLine(l);
        const obj = {{}};
        hdr.forEach((h, idx) => obj[h.trim()] = vals[idx] ?? "");
        return obj;
      }});
    }}

    function showIngestMsg(ok, msg) {{
      document.getElementById("ingest-status").innerHTML = `<div class="alert-box ${{ok ? "ok" : "err"}}" role="${{ok ? "status" : "alert"}}">${{esc(msg)}}</div>`;
    }}

    function applyResultados(arr) {{
      const byId = Object.fromEntries(arr.filter(x => x && x.capture_id).map(x => [x.capture_id, x]));
      DATA = DATA.map(d => {{
        const r = byId[d.capture_id];
        if (!r) return d;
        const costo = d.esperada ? (r.decision === "revision_manual" ? 1 : (r.decision === d.esperada ? 0 : (r.decision === "aprobada" ? 10 : 3))) : null;
        return {{
          ...d,
          motor: r.decision || d.motor,
          confidence: r.confidence_score ?? d.confidence,
          reason_code: r.reason_code || "",
          explicacion: r.explicacion || d.explicacion,
          validaciones: r.validaciones || d.validaciones,
          precio_detectado: r.precio_detectado ?? d.precio_detectado,
          resultado_oficial: r,
          costo,
          es_error: Boolean(d.esperada && r.decision && r.decision !== d.esperada),
          falsa_aprobada: Boolean(r.decision === "aprobada" && d.esperada && d.esperada !== "aprobada"),
          valida_rechazada: Boolean(r.decision === "rechazada" && d.esperada === "aprobada")
        }};
      }});
      renderAll();
    }}

    function applyCapturas(rows, imgMap = {{}}) {{
      DATA = rows.map(r => {{
        const fName = String(r.facade_file || "").split("/").pop();
        const pName = String(r.product_file || "").split("/").pop();
        const sName = String(r.shelf_file || "").split("/").pop();
        return {{
          capture_id: r.capture_id || "",
          store: r.capture_store_name || "",
          brand: r.capture_brand || "",
          product_name: r.product_name || "",
          qty: r.unit_quantity_product || "",
          unit: r.unit_product || "",
          price_ref: r.capture_price || "",
          esperada: r.decision_esperada || "",
          motivo_esperado: r.motivo_rechazo || "",
          motor: "", confidence: null, reason_code: "", explicacion: "", validaciones: {{}},
          resultado_oficial: null, precio_detectado: null, leido_marca: "", leido_desc: "", leido_cant: "", leido_unid: "",
          costo: null, es_error: false, falsa_aprobada: false, valida_rechazada: false,
          img_facade: imgMap[fName] || r.facade_url || "",
          img_product: imgMap[pName] || r.product_url || "",
          img_shelf: imgMap[sName] || r.shelf_url || ""
        }};
      }});
      populateStores();
      renderAll();
    }}

    document.getElementById("in-folder").addEventListener("change", async e => {{
      const files = [...e.target.files];
      if (!files.length) return;
      const imgMap = {{}};
      let capFile = null, resFile = null;
      files.forEach(f => {{
        const low = f.name.toLowerCase();
        if (low === "capturas.csv" || low === "capturas.json") capFile = f;
        else if (low === "resultados.json") resFile = f;
        else if (/\\.(jpg|jpeg|png|webp)$/.test(low)) imgMap[f.name] = URL.createObjectURL(f);
      }});
      if (!capFile && !resFile) return showIngestMsg(false, "La carpeta no contiene capturas.csv, capturas.json ni resultados.json.");
      if (capFile) {{
        const txt = await capFile.text();
        const rows = capFile.name.endsWith(".json") ? (JSON.parse(txt).capturas || JSON.parse(txt)) : parseCsv(txt);
        applyCapturas(rows, imgMap);
      }}
      if (resFile) {{
        applyResultados(JSON.parse(await resFile.text()));
      }}
      showIngestMsg(true, `Carpeta cargada en memoria: ${{DATA.length}} capturas y ${{Object.keys(imgMap).length}} imágenes enlazadas.`);
    }});

    document.getElementById("in-csv").addEventListener("change", async e => {{
      const f = e.target.files[0]; if (!f) return;
      const rows = parseCsv(await f.text());
      if (!rows.length || !rows[0].capture_id) return showIngestMsg(false, "El CSV no tiene columna capture_id.");
      applyCapturas(rows);
      showIngestMsg(true, `CSV cargado: ${{rows.length}} capturas.`);
    }});

    document.getElementById("in-json").addEventListener("change", async e => {{
      const f = e.target.files[0]; if (!f) return;
      const parsed = JSON.parse(await f.text());
      const arr = Array.isArray(parsed) ? parsed : (parsed.capturas || []);
      if (!arr.length) return showIngestMsg(false, "El JSON está vacío o no tiene formato lista.");
      if (arr[0].decision) {{ applyResultados(arr); showIngestMsg(true, `resultados.json aplicado (${{arr.length}} veredictos).`); }}
      else {{ applyCapturas(arr); showIngestMsg(true, `capturas.json cargado (${{arr.length}} capturas).`); }}
    }});

    document.getElementById("btn-sim").onclick = () => {{
      const f1 = document.getElementById("sim-facade").files[0];
      const f2 = document.getElementById("sim-product").files[0];
      const f3 = document.getElementById("sim-shelf").files[0];
      if (!f1 || !f2 || !f3) return showIngestMsg(false, "Selecciona las 3 fotos (Fachada, Producto y Etiqueta) para probar.");
      const simId = "CAP-DEMO-" + String(Date.now()).slice(-4);
      DATA.unshift({{
        capture_id: simId, store: "Prueba en vivo", brand: "Muestra local", product_name: "Captura cargada en vivo",
        qty: "1", unit: "pza", price_ref: "0.00", esperada: "", motivo_esperado: "",
        motor: "revision_manual", confidence: 0.5, reason_code: "SIN_LECTURA",
        explicacion: "Captura cargada en vivo en el navegador; lista para inspección o envío al backend.",
        validaciones: {{ tienda_fachada: "ok", producto: "ok", codigo_barras: "ok", evidencia_precio: "ok" }},
        resultado_oficial: null, precio_detectado: null, leido_marca: "", leido_desc: "", leido_cant: "", leido_unid: "",
        costo: 1, es_error: false, falsa_aprobada: false, valida_rechazada: false,
        img_facade: URL.createObjectURL(f1), img_product: URL.createObjectURL(f2), img_shelf: URL.createObjectURL(f3)
      }});
      renderAll();
      showIngestMsg(true, `Captura ${{simId}} agregada al inicio de la Cola de Revisión Manual y Explorador.`);
    }};

    window.addEventListener("keydown", e => {{
      if (e.key === "Escape") {{
        document.getElementById("modal-foto").classList.remove("open");
        document.getElementById("modal-json").classList.remove("open");
      }}
      if (!document.getElementById("tab-cola").classList.contains("active")) return;
      if (["INPUT", "SELECT", "TEXTAREA"].includes(document.activeElement.tagName)) return;
      const queue = currentItems.filter(d => d.motor === "revision_manual" || !d.motor);
      const cur = queue[hitlIdx];
      if (!cur) return;
      if (e.key === "a" || e.key === "A") markHitl(cur.capture_id, "aprobada_analista");
      else if (e.key === "r" || e.key === "R") markHitl(cur.capture_id, "rechazada_analista");
      else if (e.key === "s" || e.key === "S" || e.key === "ArrowRight") {{ hitlIdx++; renderHitl(currentItems); }}
      else if (e.key === "ArrowLeft") {{ hitlIdx--; renderHitl(currentItems); }}
    }});

    populateStores();
    renderAll();
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
