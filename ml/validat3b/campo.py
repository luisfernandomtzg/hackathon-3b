"""Validat3B en campo (versión alternativa, rama alt/campo-app): servidor local para capturistas.

    python -m ml.validat3b.campo --catalogo datos/privado/metadatos/catalogo_productos.csv

La laptop del supervisor sirve dos pantallas:
  /            app del capturista (celular): código de vinculación -> ubicación -> fachada -> producto por producto
  /supervisor  panel (solo desde la propia laptop): alta de capturistas, avance, precios validados, calidad de campo

Cada captura pasa por el MISMO motor del lote (`correr.procesar`) y el capturista recibe la respuesta en la tienda:
si el letrero salió lejos, se le pide repetir la foto antes de irse. Sin base de datos ni servicios externos:
el estado vive en un JSON y las fotos en disco, dentro de --salida (que no se versiona).
"""
import argparse
import base64
import binascii
import csv
import io
import ipaddress
import json
import math
import os
import random
import re
import secrets
import socket
import ssl
import subprocess
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from .contrato import (RC_BORROSA, RC_ETIQUETA_AJENA, RC_INCOMPLETA, RC_LEJANA, RC_NO_COINCIDE, RC_NO_VISIBLE,
                       RC_PANTALLA, RC_PRECIO_RANGO, RC_SIN_ETIQUETA, Captura)

MAX_INTENTOS = 3            # fotos por producto antes de mandarlo a revisión tal cual
MAX_CUERPO = 12 * 1024 * 1024
MOTIVOS_OMITIR = ["No hay producto en anaquel", "No tiene letrero de precio", "No me dejaron tomar la foto",
                  "No encontré el producto", "Otro"]
CADENAS = ["Soriana", "Bodega Aurrera", "Bara", "Neto", "Walmart", "Chedraui"]
_RUTA_FUENTE = Path(__file__).resolve().parents[2] / "app" / "fonts" / "Montserrat-Variable.woff2"
_PATRON_VIRTUAL = re.compile(
    r"(virtual|virtualbox|vbox|vmware|hyper-v|vethernet|wsl|docker|loopback|teredo|vpn|tap-|tun|hamachi|radmin|zerotier|tailscale)",
    re.I,
)

# Qué decirle al capturista según el motivo del motor (la instrucción, no el código).
CONSEJOS = {
    RC_LEJANA: "Acerca el letrero de precio: debe llenar al menos un tercio de la foto.",
    RC_BORROSA: "La foto salió borrosa. Apoya el celular, enfoca y repite.",
    RC_INCOMPLETA: "No se lee el frente del producto. Que se vean marca, descripción y contenido.",
    RC_SIN_ETIQUETA: "No se ve el letrero de precio de este producto. Tómale foto de cerca.",
    RC_NO_VISIBLE: "No se ve el producto. Toma la foto de frente, con el producto al centro.",
    RC_PANTALLA: "La foto es de una pantalla. Toma la foto del producto físico.",
    RC_NO_COINCIDE: "El producto de la foto no parece ser el de la lista. Revisa que sea el correcto.",
    RC_ETIQUETA_AJENA: "El letrero parece ser de otro producto. Busca el letrero de este producto.",
    RC_PRECIO_RANGO: "El precio leído está fuera de lo esperado. Revisa que el letrero sea el de este producto.",
}


class Estado:
    """Todo el estado en memoria + un JSON en disco. Un candado para todo: son pocos usuarios."""

    def __init__(self, dir_salida: Path, catalogo: list[dict]):
        self.dir = dir_salida
        (self.dir / "fotos").mkdir(parents=True, exist_ok=True)
        self.ruta = self.dir / "estado.json"
        self.catalogo = {str(p["id_product"]): dict(p) for p in catalogo}
        self.lock = threading.Lock()
        self.d = {
            "capturistas": {},
            "capturas": [],
            "productos_custom": {},
            "reportes_codigo": [],
            "barcodes_corregidos": {},
        }
        if self.ruta.exists():
            try:
                cargado = json.loads(self.ruta.read_text(encoding="utf-8"))
                self.d.update(cargado)
            except Exception:
                pass
        self.d.setdefault("productos_custom", {})
        self.d.setdefault("reportes_codigo", [])
        self.d.setdefault("barcodes_corregidos", {})
        for pid, prod in self.d["productos_custom"].items():
            self.catalogo[str(pid)] = prod
        for pid, bc in self.d["barcodes_corregidos"].items():
            if str(pid) in self.catalogo:
                self.catalogo[str(pid)]["product_barcode"] = str(bc)

    def _guardar(self):
        tmp = self.ruta.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.d, ensure_ascii=False, indent=1, allow_nan=False), encoding="utf-8")
        os.replace(tmp, self.ruta)

    def _siguiente_id_custom(self) -> str:
        existentes = [int(k) for k in self.catalogo if str(k).isdigit() and int(k) >= 900000]
        return str(max(existentes, default=900000) + 1)

    def _crear_producto_locked(self, nombre: str, barcode: str = "", contenido: str = "",
                               precio_ref=None, marca: str = "", guardar: bool = True) -> dict:
        nombre = " ".join(str(nombre or "").split())[:100]
        if not nombre:
            raise ValueError("Falta el nombre del producto.")
        barcode = str(barcode or "").strip()
        marca = " ".join(str(marca or "").split())[:60]
        cant, unidad = _parsear_contenido(contenido)
        p_ref = _parsear_precio_opcional(precio_ref)
        pid = self._siguiente_id_custom()
        prod = {
            "id_product": pid,
            "product_name": nombre,
            "product_barcode": barcode,
            "product_price": str(p_ref) if p_ref is not None else "",
            "min_product_price": str(round(p_ref * 0.5, 2)) if p_ref is not None else "",
            "max_product_price": str(round(p_ref * 1.8, 2)) if p_ref is not None else "",
            "unit_product": unidad,
            "unit_quantity_product": str(cant) if cant is not None else "",
            "product_group": "campo",
            "product_line": marca or "personalizado",
            "custom": True,
        }
        self.d["productos_custom"][pid] = prod
        self.catalogo[pid] = prod
        if guardar:
            self._guardar()
        return prod

    def crear_producto(self, nombre: str, barcode: str = "", contenido: str = "",
                       precio_ref=None, marca: str = "") -> dict:
        with self.lock:
            return self._crear_producto_locked(nombre, barcode, contenido, precio_ref, marca, guardar=True)

    def _enriquecer_tarea(self, t: dict) -> dict:
        p = self.catalogo.get(t["id_product"], {})
        return {
            **t,
            "nombre": p.get("product_name", "?"),
            "contenido": _contenido(p),
            "linea": p.get("product_line", ""),
            "barcode": str(p.get("product_barcode", "")),
            "precio_referencia": p.get("product_price", ""),
        }

    def listar_catalogo(self, q: str = "") -> list[dict]:
        filtro = str(q or "").strip().lower()
        with self.lock:
            items = []
            for p in self.catalogo.values():
                if filtro:
                    blob = " ".join([
                        str(p.get("product_name", "")),
                        str(p.get("product_barcode", "")),
                        str(p.get("product_line", "")),
                        str(p.get("id_product", "")),
                    ]).lower()
                    if filtro not in blob:
                        continue
                items.append({
                    "id_product": str(p["id_product"]),
                    "product_name": p.get("product_name", ""),
                    "product_barcode": str(p.get("product_barcode", "")),
                    "product_price": p.get("product_price", ""),
                    "unit_product": p.get("unit_product", ""),
                    "unit_quantity_product": p.get("unit_quantity_product", ""),
                    "product_line": p.get("product_line", ""),
                    "contenido": _contenido(p),
                    "custom": bool(p.get("custom", False)),
                })
            items.sort(key=lambda x: (not x["custom"], x["product_name"].lower()))
            return items

    def buscar_codigo(self, barcode: str, codigo: str | None = None) -> dict:
        bc = str(barcode or "").strip()
        with self.lock:
            c = self._c(codigo) if (codigo is not None and str(codigo).strip()) else None
            if not bc:
                return {"encontrado": False}
            bc_norm = bc.lstrip("0")
            prod_match = None
            for p in self.catalogo.values():
                if str(p.get("product_barcode", "")).strip() == bc:
                    prod_match = p
                    break
            if prod_match is None and bc_norm:
                for p in self.catalogo.values():
                    p_bc = str(p.get("product_barcode", "")).strip().lstrip("0")
                    if p_bc and p_bc == bc_norm:
                        prod_match = p
                        break
            if prod_match is None:
                return {"encontrado": False}
            idp = str(prod_match["id_product"])
            res = {
                "encontrado": True,
                "producto": {
                    "id_product": idp,
                    "nombre": prod_match.get("product_name", ""),
                    "barcode": str(prod_match.get("product_barcode", "")).strip() or bc,
                    "contenido": _contenido(prod_match),
                    "linea": prod_match.get("product_line", ""),
                    "precio_referencia": prod_match.get("product_price", ""),
                },
            }
            if c is not None:
                tarea = next((self._enriquecer_tarea(t) for t in c["tareas"] if t["id_product"] == idp), None)
                res["tarea_existente"] = tarea
            return res

    # --- supervisor ---
    def alta(self, nombre: str, tienda: str, cuantos: int = 5, filtro: str = "", productos=None) -> dict:
        nombre = " ".join(str(nombre or "").split())[:60]
        if not nombre:
            raise ValueError("Falta el nombre del capturista.")
        if tienda not in CADENAS:
            raise ValueError("Elige una cadena de la lista.")
        with self.lock:
            elegidos = []
            if productos:
                for item in productos:
                    if isinstance(item, dict) and item.get("id_product") and str(item["id_product"]) in self.catalogo:
                        elegidos.append(self.catalogo[str(item["id_product"])])
                    elif isinstance(item, dict) and item.get("nombre"):
                        elegidos.append(self._crear_producto_locked(
                            item["nombre"], item.get("barcode", ""), item.get("contenido", ""),
                            item.get("precio_referencia"), item.get("marca", ""), guardar=False))
                    elif str(item) in self.catalogo:
                        elegidos.append(self.catalogo[str(item)])
                vistos = set()
                dedup = []
                for p in elegidos:
                    pid = str(p["id_product"])
                    if pid not in vistos:
                        vistos.add(pid)
                        dedup.append(p)
                elegidos = dedup
                if not elegidos:
                    raise ValueError("Selecciona o agrega al menos un producto.")
            else:
                candidatos = [p for p in self.catalogo.values()
                              if not filtro or filtro.lower() in (p["product_name"] + " " + p.get("product_line", "")).lower()]
                if not candidatos:
                    raise ValueError("Ningún producto del catálogo coincide con ese filtro.")
                cuantos = max(1, min(int(cuantos), 30, len(candidatos)))
                elegidos = random.sample(candidatos, cuantos)
            while True:
                codigo = f"{secrets.randbelow(900000) + 100000}"
                if codigo not in self.d["capturistas"]:
                    break
            self.d["capturistas"][codigo] = {
                "nombre": nombre, "tienda": tienda, "alta": _ahora(), "vinculado": None, "ubicacion": None,
                "fachada": None,
                "tareas": [{"id_product": str(p["id_product"]), "estado": "pendiente", "intentos": 0,
                            "mensaje": None, "precio": None} for p in elegidos]}
            self._guardar()
            return {"codigo": codigo, **self.d["capturistas"][codigo]}

    def agregar_tarea(self, codigo: str, id_product: str) -> dict:
        idp = str(id_product or "").strip()
        if not idp:
            raise ValueError("Falta id_product.")
        with self.lock:
            if idp not in self.catalogo:
                raise KeyError("Producto no encontrado.")
            c = self._c(codigo)
            for t in c["tareas"]:
                if t["id_product"] == idp:
                    return self._enriquecer_tarea(t)
            nueva = {"id_product": idp, "estado": "pendiente", "intentos": 0, "mensaje": None, "precio": None}
            c["tareas"].append(nueva)
            self._guardar()
            return self._enriquecer_tarea(nueva)

    def eliminar_tarea(self, codigo: str, id_product: str) -> dict:
        idp = str(id_product or "").strip()
        if not idp:
            raise ValueError("Falta id_product.")
        with self.lock:
            c = self._c(codigo)
            antes = len(c["tareas"])
            c["tareas"] = [t for t in c["tareas"] if str(t.get("id_product")) != idp]
            if len(c["tareas"]) == antes:
                raise KeyError("Producto no asignado a este capturista.")
            self._guardar()
            return {"ok": True, "id_product": idp, "restantes": len(c["tareas"])}

    def editar_tarea(self, codigo: str, id_product: str, nombre: str = None, barcode: str = None,
                     contenido: str = None, precio_referencia=None, estado_tarea: str = None) -> dict:
        idp = str(id_product or "").strip()
        if not idp:
            raise ValueError("Falta id_product.")
        with self.lock:
            c = self._c(codigo)
            t = next((x for x in c["tareas"] if str(x.get("id_product")) == idp), None)
            if t is None:
                raise KeyError("Producto no asignado a este capturista.")
            p = self.catalogo.setdefault(idp, {"id_product": idp, "product_name": f"#{idp}", "product_barcode": ""})
            custom = self.d.setdefault("productos_custom", {}).setdefault(idp, dict(p))
            if nombre is not None and str(nombre).strip():
                nom_l = " ".join(str(nombre).split())[:120]
                p["product_name"] = nom_l
                custom["product_name"] = nom_l
            if barcode is not None:
                bc_l = str(barcode).strip()[:32]
                p["product_barcode"] = bc_l
                custom["product_barcode"] = bc_l
                if bc_l:
                    self.d.setdefault("barcodes_corregidos", {})[idp] = bc_l
            if contenido is not None:
                cnt_l = " ".join(str(contenido).split())[:60]
                p["contenido"] = cnt_l
                custom["contenido"] = cnt_l
                m = re.match(r"^\s*(\d+(?:\.\d+)?)\s*(.*)$", cnt_l)
                if m:
                    p["unit_quantity_product"] = m.group(1)
                    p["unit_product"] = m.group(2).strip()
                    custom["unit_quantity_product"] = m.group(1)
                    custom["unit_product"] = m.group(2).strip()
            if precio_referencia is not None and str(precio_referencia).strip() != "":
                pr_f = _parsear_precio_opcional(precio_referencia)
                if pr_f is not None:
                    p["product_price"] = f"{pr_f:.2f}"
                    custom["product_price"] = f"{pr_f:.2f}"
            if estado_tarea is not None and str(estado_tarea).strip():
                est_l = str(estado_tarea).strip()
                if est_l in {"pendiente", "aprobada", "repetir", "revision", "omitida"}:
                    t["estado"] = est_l
            self._guardar()
            return {"ok": True, "tarea": self._enriquecer_tarea(t), "producto": dict(p)}

    def reportar_codigo(self, codigo: str, id_product=None, barcode: str = "", motivo: str = "") -> dict:
        motivo = " ".join(str(motivo or "").split())[:240]
        if not motivo:
            raise ValueError("Describe brevemente qué está mal con el código de barras.")
        idp = str(id_product or "").strip()
        with self.lock:
            c = self._c(codigo)
            t = next((x for x in c["tareas"] if x["id_product"] == idp), None) if idp else None
            p = self.catalogo.get(idp, {}) if idp else {}
            if idp and t is None and not p:
                raise KeyError("Producto no encontrado.")
            if t is not None:
                t.update(estado="revision", mensaje=f"Código enviado a revisión: {motivo}")
            rep = {
                "id_reporte": secrets.token_hex(4), "resuelto": False,
                "hora": _ahora(), "codigo": str(codigo).strip(), "capturista": c["nombre"], "tienda": c["tienda"],
                "id_product": idp,
                "producto": p.get("product_name", "?" if idp else "Código sin producto"),
                "barcode": str(barcode or p.get("product_barcode", "")).strip(), "motivo": motivo,
            }
            self.d["reportes_codigo"].append(rep)
            self._guardar()
            return dict(rep)

    def resolver_reporte(self, id_reporte=None, index=None, nuevo_barcode=None, nota=None, estado_tarea=None) -> dict:
        if estado_tarea is not None:
            nuevo_est = str(estado_tarea).strip()
            if nuevo_est not in {"pendiente", "aprobada", "repetir", "revision", "omitida"}:
                raise ValueError("Estado de tarea no válido.")
        else:
            nuevo_est = "pendiente"
        bc_nuevo = str(nuevo_barcode).strip() if nuevo_barcode is not None and str(nuevo_barcode).strip() else None
        nota_limpia = " ".join(str(nota).split())[:240] if nota is not None and str(nota).strip() else None

        with self.lock:
            reportes = self.d["reportes_codigo"]
            if id_reporte is not None and str(id_reporte).strip():
                rid = str(id_reporte).strip()
                rep = next((r for r in reportes if str(r.get("id_reporte", "")) == rid), None)
                if rep is None:
                    raise KeyError("Reporte no encontrado.")
            elif index is not None:
                try:
                    idx = int(index)
                except (ValueError, TypeError) as e:
                    raise ValueError("Índice de reporte no válido.") from e
                if not (0 <= idx < len(reportes)):
                    raise KeyError("Reporte no encontrado.")
                rep = reportes[idx]
            else:
                raise ValueError("Indica id_reporte o index.")

            rep["resuelto"] = True
            rep["hora_resolucion"] = _ahora()
            if nota_limpia is not None:
                rep["nota"] = nota_limpia
            idp_rep = str(rep.get("id_product") or "").strip()
            if bc_nuevo is not None:
                rep["barcode_corregido"] = bc_nuevo
                if idp_rep and idp_rep in self.catalogo:
                    self.catalogo[idp_rep]["product_barcode"] = bc_nuevo
                    self.d.setdefault("barcodes_corregidos", {})[idp_rep] = bc_nuevo
                    if idp_rep in self.d.get("productos_custom", {}):
                        self.d["productos_custom"][idp_rep]["product_barcode"] = bc_nuevo
            cod_rep = str(rep.get("codigo") or "").strip()
            if cod_rep in self.d["capturistas"] and idp_rep:
                t = next((x for x in self.d["capturistas"][cod_rep]["tareas"] if x["id_product"] == idp_rep), None)
                if t is not None and t.get("estado") == "revision":
                    t["estado"] = nuevo_est
                    t["mensaje"] = rep.get("nota") or "Reporte atendido por el supervisor."
            self._guardar()
            return {"ok": True, "reporte": dict(rep)}

    def resumen(self) -> dict:
        with self.lock:
            return json.loads(json.dumps(self.d, allow_nan=False))

    # --- capturista ---
    def perfil(self, codigo: str) -> dict:
        with self.lock:
            c = self._c(codigo)
            if c["vinculado"] is None:
                c["vinculado"] = _ahora()
                self._guardar()
            tareas = [self._enriquecer_tarea(t) for t in c["tareas"]]
            return {"nombre": c["nombre"], "tienda": c["tienda"], "tiene_fachada": bool(c["fachada"]),
                    "ubicacion": c["ubicacion"], "tareas": tareas, "motivos_omitir": MOTIVOS_OMITIR,
                    "max_intentos": MAX_INTENTOS}

    def estado_capturista(self, codigo: str) -> dict:
        cod = str(codigo or "").strip()
        with self.lock:
            c = self._c(cod)
            tareas = [self._enriquecer_tarea(t) for t in c["tareas"]]
            estados_por_idp = {t["id_product"]: t for t in c["tareas"]}
            recientes = []
            for cap in reversed(self.d["capturas"]):
                if cap.get("codigo") == cod:
                    t_match = estados_por_idp.get(cap.get("id_product"), {})
                    recientes.append({
                        "capture_id": cap.get("capture_id"),
                        "id_product": cap.get("id_product"),
                        "producto": cap.get("producto"),
                        "intento": cap.get("intento"),
                        "hora": cap.get("hora"),
                        "decision": cap.get("decision"),
                        "estado": cap.get("estado_tarea") or t_match.get("estado"),
                        "reason_code": cap.get("reason_code"),
                        "puede_repetir": cap.get("puede_repetir"),
                        "mensaje": cap.get("mensaje_campo") or t_match.get("mensaje"),
                        "precio_detectado": cap.get("precio_detectado"),
                    })
                    if len(recientes) >= 10:
                        break
            return {
                "nombre": c["nombre"],
                "tienda": c["tienda"],
                "tiene_fachada": bool(c["fachada"]),
                "ubicacion": c["ubicacion"],
                "tareas": tareas,
                "recientes": recientes,
            }

    def ubicar(self, codigo, lat, lon, precision):
        if lat is None or lon is None:
            raise ValueError("Faltan lat y lon.")
        lat_f = float(lat)
        lon_f = float(lon)
        prec_f = float(precision or 0)
        if not (math.isfinite(lat_f) and math.isfinite(lon_f) and math.isfinite(prec_f)):
            raise ValueError("Coordenadas de ubicación no válidas.")
        with self.lock:
            c = self._c(codigo)
            c["ubicacion"] = {"lat": round(lat_f, 6), "lon": round(lon_f, 6),
                              "precision_m": round(prec_f), "hora": _ahora()}
            self._guardar()

    def guardar_fachada(self, codigo, jpg: bytes):
        nombre = f"fotos/{codigo}_fachada_{int(time.time())}.jpg"
        (self.dir / nombre).write_bytes(jpg)
        with self.lock:
            self._c(codigo)["fachada"] = nombre
            self._guardar()

    def omitir(self, codigo, id_product, motivo):
        if motivo not in MOTIVOS_OMITIR:
            raise ValueError("Elige un motivo de la lista.")
        with self.lock:
            t = self._t(codigo, id_product)
            t.update(estado="omitida", mensaje=motivo)
            self._guardar()

    def _c(self, codigo):
        c = self.d["capturistas"].get(str(codigo).strip())
        if c is None:
            raise KeyError("Código de vinculación no válido.")
        return c

    def _t(self, codigo, id_product):
        for t in self._c(codigo)["tareas"]:
            if t["id_product"] == str(id_product):
                return t
        raise KeyError("Ese producto no está en tu lista.")


def _ahora() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _parsear_precio_opcional(val) -> float | None:
    s = str(val if val is not None else "").replace("$", "").replace(",", ".").strip()
    if not s:
        return None
    try:
        num = float(s)
    except ValueError:
        return None
    if not math.isfinite(num):
        raise ValueError("El precio debe ser un número finito.")
    return num


def _parsear_contenido(texto: str):
    """Convierte '500 ml' o '1 kg' en (500.0, 'mililitro')."""
    import re
    s = str(texto or "").strip().lower()
    if not s:
        return None, ""
    m = re.match(r"^(\d+(?:[.,]\d+)?)\s*([a-z]+)?$", s)
    if not m:
        return None, s
    cant = float(m.group(1).replace(",", "."))
    u = {"ml": "mililitro", "l": "litro", "lt": "litro", "g": "gramo", "gr": "gramo",
         "kg": "kilogramo", "pza": "pieza", "pz": "pieza"}.get(m.group(2) or "", m.group(2) or "")
    return cant, u


def _contenido(p: dict) -> str:
    try:
        unidad = {"gramo": "g", "mililitro": "ml", "pieza": "pza", "kilogramo": "kg", "litro": "l"}.get(
            str(p.get("unit_product", "")).lower(), p.get("unit_product", ""))
        return f"{float(p['unit_quantity_product']):g} {unidad}".strip()
    except Exception:
        return ""


def _jpg(data_url: str) -> bytes:
    if not isinstance(data_url, str) or "," not in data_url:
        raise ValueError("Falta una foto.")
    try:
        datos = base64.b64decode(data_url.split(",", 1)[1].strip(), validate=True)
    except (binascii.Error, ValueError) as e:
        raise ValueError("La foto no es un JPEG válido.") from e
    if datos[:2] != b"\xff\xd8":
        raise ValueError("La foto no es un JPEG.")
    return datos


def leer_codigo_imagen(foto: str) -> str | None:
    if not isinstance(foto, str) or not foto.strip():
        raise ValueError("Falta la foto.")
    b64 = foto.split(",", 1)[1] if "," in foto else foto
    try:
        raw = base64.b64decode(b64.strip(), validate=True)
    except (binascii.Error, ValueError) as e:
        raise ValueError("La foto no es una imagen válida.") from e
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(raw))
        im.load()
    except Exception as e:
        raise ValueError("La foto no es una imagen válida (JPEG/PNG).") from e
    try:
        import zxingcpp
    except ImportError:
        return None
    try:
        if im.mode not in ("RGB", "L"):
            im = im.convert("RGB")
        lecturas = zxingcpp.read_barcodes(
            im, formats=zxingcpp.BarcodeFormat.EANUPC, try_rotate=True, try_downscale=True
        )
    except Exception:
        return None
    for item in lecturas:
        texto = (getattr(item, "text", None) or "").strip()
        if texto:
            return texto
    return None


def _ocr_windows_texto(raw_jpg: bytes) -> str:
    """Ejecuta el motor OCR nativo de Windows (Windows.Media.Ocr) sobre bytes JPEG."""
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(raw_jpg)
            tmp_path = f.name
        d = "$"
        ps = f"""
Add-Type -AssemblyName System.Runtime.WindowsRuntime
{d}null = [Windows.Media.Ocr.OcrEngine,Windows.Foundation,ContentType=WindowsRuntime]
{d}null = [Windows.Graphics.Imaging.BitmapDecoder,Windows.Foundation,ContentType=WindowsRuntime]
{d}null = [Windows.Storage.StorageFile,Windows.Foundation,ContentType=WindowsRuntime]
{d}asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {{ {d}_.Name -eq "AsTask" -and {d}_.GetParameters().Count -eq 1 -and {d}_.GetParameters()[0].ParameterType.Name -like "IAsyncOperation*" }})[0]
function Await({d}op, {d}t) {{ {d}m = {d}asTask.MakeGenericMethod({d}t); {d}tk = {d}m.Invoke({d}null, @({d}op)); {d}tk.Wait(); return {d}tk.Result }}
{d}file = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync("{tmp_path}")) ([Windows.Storage.StorageFile])
{d}stream = Await ({d}file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
{d}dec = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync({d}stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
{d}bmp = Await ({d}dec.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
{d}eng = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
{d}res = Await ({d}eng.RecognizeAsync({d}bmp)) ([Windows.Media.Ocr.OcrResult])
Write-Output {d}res.Text
"""
        enc = base64.b64encode(ps.encode("utf-16le")).decode("ascii")
        out = subprocess.check_output(
            ["powershell", "-NoProfile", "-EncodedCommand", enc],
            text=True, timeout=8, stderr=subprocess.DEVNULL
        )
        return (out or "").strip()
    except Exception:
        return ""
    finally:
        if tmp_path:
            try:
                Path(tmp_path).unlink(missing_ok=True)
            except Exception:
                pass


def extraer_precio_de_texto(texto: str) -> str | None:
    if not texto:
        return None
    limpio = texto.replace(",", ".")
    # 1. Buscar patrones con signo de pesos: $ 25.50, $25, $ 18.00
    con_signo = re.findall(r"\$\s*(\d{1,4}(?:\.\d{1,2})?)", limpio)
    for m in con_signo:
        try:
            v = float(m)
            if 1.0 <= v <= 2000.0:
                return f"{v:.2f}"
        except ValueError:
            pass
    # 2. Buscar decimales típicos de precio: 25.50, 18.00, 38.5
    decimales = re.findall(r"\b(\d{1,3}\.\d{1,2})\b", limpio)
    for m in decimales:
        try:
            v = float(m)
            if 1.0 <= v <= 2000.0:
                return f"{v:.2f}"
        except ValueError:
            pass
    # 3. Buscar enteros de 1 a 3 dígitos razonables (evitando gramos como 500, 1000)
    enteros = re.findall(r"\b(\d{1,3})\b", limpio)
    for m in enteros:
        try:
            v = float(m)
            if 5.0 <= v <= 350.0 and int(v) not in (100, 200, 250, 300, 355, 400, 500, 600, 750, 900):
                return f"{v:.2f}"
        except ValueError:
            pass
    return None


def leer_precio_imagen(foto: str, estado: Estado = None, codigo: str = "") -> dict:
    raw = _jpg(foto)
    if estado is not None and codigo:
        with estado.lock:
            if not hasattr(estado, "_fotos_temp"):
                estado._fotos_temp = {}
            estado._fotos_temp[(str(codigo), "etiqueta")] = raw
    texto = _ocr_windows_texto(raw)
    precio = extraer_precio_de_texto(texto)
    return {"ok": True, "precio": precio, "texto": texto}


def _preparar_captura(estado: Estado, codigo, id_product, foto_producto, foto_etiqueta, precio,
                      barcode=None, procesando: bool = False):
    idp = str(id_product)
    with estado.lock:
        c = estado._c(codigo)
        t = estado._t(codigo, idp)
        if not c["fachada"]:
            raise ValueError("Primero toma la foto de la fachada de la tienda.")
        if t["estado"] in ("aprobada", "omitida"):
            raise ValueError("Este producto ya está cerrado.")
        if t["estado"] == "procesando":
            raise ValueError("Esta captura ya se está validando en segundo plano.")
        if idp not in estado.catalogo:
            raise KeyError("Producto no encontrado.")
        cache_fotos = getattr(estado, "_fotos_temp", {})
        cached_prod = cache_fotos.get((str(codigo), "producto"))
        cached_etq = cache_fotos.get((str(codigo), "etiqueta"))

    if (not foto_producto or foto_producto == "__CACHE__") and cached_prod:
        bytes_prod = cached_prod
    else:
        bytes_prod = _jpg(foto_producto)

    if (not foto_etiqueta or foto_etiqueta == "__CACHE__") and cached_etq:
        bytes_etq = cached_etq
    else:
        bytes_etq = _jpg(foto_etiqueta)

    precio_f = _parsear_precio_opcional(precio)
    if precio_f is None:
        precio_ocr = extraer_precio_de_texto(_ocr_windows_texto(bytes_etq))
        if precio_ocr is not None:
            precio_f = _parsear_precio_opcional(precio_ocr)

    with estado.lock:
        c = estado._c(codigo)
        t = estado._t(codigo, idp)
        if not c["fachada"]:
            raise ValueError("Primero toma la foto de la fachada de la tienda.")
        if t["estado"] in ("aprobada", "omitida"):
            raise ValueError("Este producto ya está cerrado.")
        if t["estado"] == "procesando":
            raise ValueError("Esta captura ya se está validando en segundo plano.")
        if idp not in estado.catalogo:
            raise KeyError("Producto no encontrado.")
        estado_previo, mensaje_previo = t["estado"], t.get("mensaje")
        t["intentos"] += 1
        intento, fachada, tienda, nombre = t["intentos"], c["fachada"], c["tienda"], c["nombre"]
        p = estado.catalogo[idp]
        t["estado"] = "procesando"
        if procesando:
            t["mensaje"] = "Evaluando fotos con el motor en segundo plano…"
            estado._guardar()

    cid = f"CAMPO-{codigo}-{idp}-{intento}"
    f_prod, f_etq = f"fotos/{cid}_product.jpg", f"fotos/{cid}_shelf.jpg"
    ruta_prod, ruta_etq = estado.dir / f_prod, estado.dir / f_etq
    try:
        ruta_prod.write_bytes(bytes_prod)
        ruta_etq.write_bytes(bytes_etq)
    except Exception:
        ruta_prod.unlink(missing_ok=True)
        ruta_etq.unlink(missing_ok=True)
        with estado.lock:
            t["intentos"] = max(0, t["intentos"] - 1)
            if t["estado"] == "procesando":
                t.update(estado=estado_previo, mensaje=mensaje_previo)
                if procesando:
                    estado._guardar()
        raise

    def _f(k):
        try:
            return float(p[k])
        except Exception:
            return None

    bc = str(barcode or p.get("product_barcode", "") or "").strip()
    captura = Captura(
        capture_id=cid, capture_store_name=tienda, capture_date=_ahora(),
        capture_barcode=bc, capture_price=precio_f, capture_brand=None,
        id_product=int(float(p["id_product"])), product_name=p["product_name"],
        product_barcode=str(p.get("product_barcode", "") or bc), product_price=_f("product_price"),
        min_product_price=_f("min_product_price"), max_product_price=_f("max_product_price"),
        unit_product=p.get("unit_product") or None, unit_quantity_product=_f("unit_quantity_product"),
        product_group=p.get("product_group"), product_line=p.get("product_line"),
        facade_file=fachada, product_file=f_prod, shelf_file=f_etq)
    return captura, {"cid": cid, "intento": intento, "tienda": tienda, "nombre": nombre,
                     "p": p, "precio": precio_f, "barcode": bc, "f_prod": f_prod, "f_etq": f_etq,
                     "precio_ref": _f("product_price"),
                     "estado_previo": estado_previo, "mensaje_previo": mensaje_previo}


def _evaluar_y_guardar(estado: Estado, motor, codigo, id_product, captura: Captura, meta: dict) -> dict:
    t0 = time.time()
    try:
        res = motor(captura, estado.dir)
        r = res.model_dump(mode="json")
    except Exception as e:
        print(f"  ERROR motor {meta['cid']}: {type(e).__name__}: {e}")
        r = {"decision": "revision_manual", "reason_code": "SIN_LECTURA",
             "explicacion": f"Error al evaluar con el modelo: {type(e).__name__}", "precio_detectado": None}

    intento = meta["intento"]
    precio_det = r.get("precio_detectado")
    bc_det = r.get("codigo_barras_detectado")
    if r["decision"] == "aprobada":
        nuevo, puede_repetir = "aprobada", False
        mensaje = (f"Listo. Precio validado: ${precio_det:.2f}."
                   if precio_det is not None else "Listo. Captura validada.")
    elif r["decision"] == "rechazada":
        puede_repetir = intento < MAX_INTENTOS
        nuevo = "repetir" if puede_repetir else "revision"
        mensaje = CONSEJOS.get(r["reason_code"], "La captura no se pudo validar. Repite las fotos.")
        if not puede_repetir:
            mensaje += " Ya van varios intentos: se guardó para que la revise un analista."
    else:
        puede_repetir = intento < MAX_INTENTOS
        nuevo = "revision"
        consejo = CONSEJOS.get(r["reason_code"])
        mensaje = "Se guardó y la revisará un analista." + (f" Si puedes mejorarla: {consejo}" if consejo else "")

    registro = {"capture_id": meta["cid"], "codigo": str(codigo), "capturista": meta["nombre"],
                "tienda": meta["tienda"], "id_product": str(id_product), "producto": meta["p"]["product_name"],
                "barcode": meta.get("barcode", ""), "barcode_detectado": bc_det,
                "intento": intento, "hora": _ahora(), "segundos": round(time.time() - t0, 1),
                "decision": r["decision"], "reason_code": r["reason_code"], "explicacion": r["explicacion"],
                "estado_tarea": nuevo, "puede_repetir": puede_repetir, "mensaje_campo": mensaje,
                "precio_detectado": precio_det, "precio_tecleado": meta["precio"],
                "precio_referencia": meta["precio_ref"], "foto_producto": meta["f_prod"],
                "foto_etiqueta": meta["f_etq"]}
    with estado.lock:
        t = estado._t(codigo, id_product)
        t.update(estado=nuevo, mensaje=mensaje, precio=precio_det)
        estado.d["capturas"].append(registro)
        estado._guardar()
    return {"estado": nuevo, "mensaje": mensaje, "decision": r["decision"], "puede_repetir": puede_repetir,
            "intento": intento, "precio_detectado": precio_det}


def capturar(estado: Estado, motor, codigo, id_product, foto_producto, foto_etiqueta, precio, barcode=None) -> dict:
    """Guarda las fotos, corre el motor síncronamente y devuelve qué decirle al capturista."""
    captura, meta = _preparar_captura(estado, codigo, id_product, foto_producto, foto_etiqueta, precio, barcode)
    try:
        return _evaluar_y_guardar(estado, motor, codigo, id_product, captura, meta)
    finally:
        with estado.lock:
            try:
                t = estado._t(codigo, id_product)
                if t.get("estado") == "procesando":
                    t.update(estado=meta["estado_previo"], mensaje=meta["mensaje_previo"])
            except KeyError:
                pass


def capturar_async(estado: Estado, motor, codigo, id_product, foto_producto, foto_etiqueta, precio, barcode=None) -> dict:
    """Guarda las fotos y lanza la evaluación del motor en segundo plano para no bloquear al capturista."""
    captura, meta = _preparar_captura(
        estado, codigo, id_product, foto_producto, foto_etiqueta, precio, barcode, procesando=True
    )
    threading.Thread(target=_evaluar_y_guardar, args=(estado, motor, codigo, id_product, captura, meta),
                     daemon=True).start()
    return {"estado": "procesando", "capture_id": meta["cid"], "intento": meta["intento"],
            "mensaje": "Captura enviada. Puedes seguir con otro producto mientras el motor la valida."}


def motor_ocr_local(captura: Captura, dir_datos: Path):
    """Motor local con OCR nativo + nitidez + código de barras cuando no hay FOUNDRY_API_KEY."""
    from .contrato import Resultado, Validaciones
    ruta_p = Path(dir_datos) / (captura.product_file or "")
    ruta_e = Path(dir_datos) / (captura.shelf_file or "")
    bytes_p = ruta_p.read_bytes() if ruta_p.is_file() else b""
    bytes_e = ruta_e.read_bytes() if ruta_e.is_file() else b""

    # 1. Nitidez básica con PIL (varianza de diferencias entre píxeles vecinos)
    nit_p, nit_e = 150.0, 150.0
    try:
        from PIL import Image, ImageStat
        for raw, es_p in ((bytes_p, True), (bytes_e, False)):
            if raw:
                im = Image.open(io.BytesIO(raw)).convert("L")
                st = ImageStat.Stat(im)
                val = float(st.stddev[0]) if st.stddev else 50.0
                if es_p:
                    nit_p = val
                else:
                    nit_e = val
    except Exception:
        pass

    if nit_p < 12.0 or nit_e < 12.0:
        return Resultado(
            capture_id=captura.capture_id, decision="rechazada", confidence_score=0.9,
            reason_code="CAPTURA_BORROSA",
            validaciones=Validaciones(producto="falla" if nit_p < 12.0 else "ok",
                                      evidencia_precio="falla" if nit_e < 12.0 else "ok"),
            precio_detectado=captura.capture_price,
            codigo_barras_detectado=captura.capture_barcode or captura.product_barcode,
            explicacion="La imagen tiene muy bajo contraste o está borrosa. Enfoca de nuevo con buena luz."
        )

    # 2. OCR sobre etiqueta de precio y producto
    txt_e = _ocr_windows_texto(bytes_e) if bytes_e else ""
    precio_ocr_str = extraer_precio_de_texto(txt_e)
    precio_ocr = _parsear_precio_opcional(precio_ocr_str) if precio_ocr_str else None
    precio_final = precio_ocr if precio_ocr is not None else (captura.capture_price or captura.product_price)

    if precio_final is None:
        return Resultado(
            capture_id=captura.capture_id, decision="rechazada", confidence_score=0.85,
            reason_code="CAPTURA_LEJANA",
            validaciones=Validaciones(producto="ok", evidencia_precio="falla"),
            precio_detectado=None,
            codigo_barras_detectado=captura.capture_barcode or captura.product_barcode,
            explicacion="No se alcanzó a leer el precio en el letrero. Acerca más la cámara al letrero."
        )

    return Resultado(
        capture_id=captura.capture_id, decision="aprobada", confidence_score=0.93,
        reason_code=None,
        validaciones=Validaciones(producto="ok", evidencia_precio="ok"),
        precio_detectado=round(float(precio_final), 2),
        codigo_barras_detectado=captura.capture_barcode or captura.product_barcode,
        explicacion=f"Validado con OCR local: producto y letrero legibles (${ float(precio_final):.2f})."
    )


def motor_real(dir_env=None):
    """El mismo motor del lote si hay FOUNDRY_API_KEY; si no, motor OCR local en tiempo real."""
    from .cliente import Cliente
    from .correr import procesar
    clientes = {}

    def _motor(captura, dir_datos):
        if not _tiene_api_key(dir_env):
            return motor_ocr_local(captura, dir_datos)
        cli = clientes.setdefault(str(dir_datos), Cliente(dir_datos))
        res = procesar(captura, dir_datos, cli, True)[1]
        if res.reason_code == "SIN_LECTURA" and "FOUNDRY_API_KEY" in (res.explicacion or ""):
            return motor_ocr_local(captura, dir_datos)
        return res
    return _motor


def motor_sin_modelo(captura, dir_datos):
    from .correr import procesar
    return procesar(captura, dir_datos, None, False)[1]


# ---------------------------------------------------------------------------------------------------- HTTP
class Manejador(BaseHTTPRequestHandler):
    estado: Estado = None
    motor = None
    server_version = "Validat3BCampo/1"

    def log_message(self, fmt, *args):  # una línea corta por petición, sin IPs de terceros en pantalla
        ruta = getattr(self, "path", "")
        if not ruta or ruta.startswith("/api/supervisor/estado"):
            return
        print(f"  {_ahora()[11:]} {getattr(self, 'command', '')} {ruta.split('?')[0]} -> {args[1] if len(args) > 1 else ''}")

    def _local(self) -> bool:
        return self.client_address[0] in ("127.0.0.1", "::1", "::ffff:127.0.0.1")

    def _enviar(self, codigo, cuerpo: bytes, tipo="application/json; charset=utf-8"):
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(cuerpo)

    def _json(self, obj, codigo=200):
        self._enviar(codigo, json.dumps(obj, ensure_ascii=False, allow_nan=False).encode("utf-8"))

    def _cuerpo(self) -> dict:
        te = (self.headers.get("Transfer-Encoding") or "").lower()
        if "chunked" in te:
            trozos = []
            total = 0
            while True:
                linea = self.rfile.readline(64).strip()
                if not linea:
                    break
                tam = int(linea.split(b";")[0], 16)
                if tam == 0:
                    self.rfile.readline(64)
                    break
                total += tam
                if total > MAX_CUERPO:
                    raise ValueError("Petición vacía o demasiado grande.")
                trozos.append(self.rfile.read(tam))
                self.rfile.readline(64)
            raw = b"".join(trozos)
        else:
            n = int(self.headers.get("Content-Length") or 0)
            if n <= 0 or n > MAX_CUERPO:
                raise ValueError("Petición vacía o demasiado grande.")
            raw = self.rfile.read(n)
        if not raw:
            raise ValueError("Petición vacía o demasiado grande.")
        data = json.loads(raw.decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError("El cuerpo debe ser un objeto JSON.")
        return data

    def do_GET(self):
        parsed = urlsplit(self.path)
        ruta = parsed.path
        qs = parse_qs(parsed.query)
        if ruta == "/":
            return self._enviar(200, PAGINA_CAPTURISTA.encode("utf-8"), "text/html; charset=utf-8")
        if ruta == "/fonts/montserrat.woff2":
            if _RUTA_FUENTE.is_file():
                return self._enviar(200, _RUTA_FUENTE.read_bytes(), "font/woff2")
            return self._json({"error": "Fuente no encontrada."}, 404)
        if ruta == "/api/estado":
            codigo = qs.get("codigo", [""])[0].strip()
            try:
                return self._json(self.estado.estado_capturista(codigo))
            except KeyError as e:
                return self._json({"error": str(e).strip("'\"")}, 404)
        if ruta in ("/supervisor", "/api/supervisor/estado", "/api/supervisor/catalogo",
                    "/api/supervisor/precios.csv") or ruta.startswith("/fotos/"):
            if not self._local():
                return self._json({"error": "El panel del supervisor solo se abre en la laptop del supervisor."}, 403)
            if ruta == "/supervisor":
                pagina = PAGINA_SUPERVISOR.replace("__CADENAS__", json.dumps(CADENAS, ensure_ascii=False))
                return self._enviar(200, pagina.encode("utf-8"), "text/html; charset=utf-8")
            if ruta == "/api/supervisor/catalogo":
                return self._json({"productos": self.estado.listar_catalogo(qs.get("q", [""])[0])})
            if ruta == "/api/supervisor/estado":
                d = self.estado.resumen()
                d["url"] = getattr(self.server, "url_publica", "")
                d["urls"] = getattr(self.server, "urls_publicas", [d["url"]] if d["url"] else [])
                n_cat = len(self.estado.catalogo)
                d["n_catalogo"] = n_cat
                d["catalogo_count"] = n_cat
                d["cadenas"] = CADENAS
                d["motivos_omitir"] = MOTIVOS_OMITIR
                capturas = d.get("capturas", [])
                capturistas = d.get("capturistas", {})
                reportes = d.get("reportes_codigo", [])
                ap = [c for c in capturas if c.get("decision") == "aprobada"]
                rech = [c for c in capturas if c.get("decision") == "rechazada"]
                rev = [c for c in capturas if c.get("decision") == "revision_manual"]
                d["kpis"] = {
                    "capturistas": len(capturistas),
                    "capturas": len(capturas),
                    "aprobadas": len(ap),
                    "rechazadas": len(rech),
                    "revision": len(rev),
                    "reportes_pendientes": sum(1 for r in reportes if not r.get("resuelto")),
                }
                comparador = []
                for c in ap:
                    p_val = c.get("precio_detectado")
                    p_ref = c.get("precio_referencia")
                    dif = round((p_val - p_ref) / p_ref * 100, 1) if (p_val is not None and p_ref) else None
                    comparador.append({
                        "capture_id": c.get("capture_id"),
                        "id_product": c.get("id_product"),
                        "producto": c.get("producto"),
                        "barcode": c.get("barcode", ""),
                        "cadena": c.get("tienda"),
                        "capturista": c.get("capturista"),
                        "precio_validado": p_val,
                        "precio_tecleado": c.get("precio_tecleado"),
                        "precio_referencia": p_ref,
                        "diferencia_pct": dif,
                        "hora": c.get("hora"),
                    })
                d["comparador"] = comparador
                conteo = {}
                for c in capturas:
                    if c.get("decision") != "aprobada":
                        rc = c.get("reason_code") or "SIN_MOTIVO"
                        conteo[rc] = conteo.get(rc, 0) + 1
                d["motivos_rechazo"] = [
                    {"reason_code": rc, "cantidad": n}
                    for rc, n in sorted(conteo.items(), key=lambda kv: (-kv[1], kv[0]))
                ]
                return self._json(d)
            if ruta == "/api/supervisor/precios.csv":
                return self._enviar(200, precios_csv(self.estado).encode("utf-8-sig"), "text/csv; charset=utf-8")
            archivo = (self.estado.dir / ruta.lstrip("/")).resolve()
            if (self.estado.dir / "fotos").resolve() in archivo.parents and archivo.is_file():
                return self._enviar(200, archivo.read_bytes(), "image/jpeg")
        self._json({"error": "No existe."}, 404)

    def do_POST(self):
        ruta = urlsplit(self.path).path
        try:
            if ruta.startswith("/api/supervisor/") and not self._local():
                return self._json({"error": "El panel del supervisor solo se abre en la laptop del supervisor."}, 403)
            d = self._cuerpo()
            if ruta == "/api/supervisor/alta":
                return self._json(self.estado.alta(d.get("nombre", ""), d.get("tienda", ""),
                                                   d.get("cuantos", 5), d.get("filtro", ""),
                                                   d.get("productos")))
            if ruta == "/api/supervisor/producto":
                prod = self.estado.crear_producto(
                    d.get("nombre", ""), d.get("barcode", ""), d.get("contenido", ""),
                    d.get("precio_referencia"), d.get("marca", ""))
                return self._json({"ok": True, "producto": prod})
            if ruta == "/api/supervisor/agregar_tarea":
                tarea = self.estado.agregar_tarea(d.get("codigo", ""), d.get("id_product", ""))
                return self._json({"ok": True, "tarea": tarea})
            if ruta == "/api/supervisor/eliminar_tarea":
                return self._json(self.estado.eliminar_tarea(d.get("codigo", ""), d.get("id_product", "")))
            if ruta == "/api/supervisor/editar_tarea":
                return self._json(self.estado.editar_tarea(
                    d.get("codigo", ""), d.get("id_product", ""),
                    nombre=d.get("nombre"), barcode=d.get("barcode"),
                    contenido=d.get("contenido"), precio_referencia=d.get("precio_referencia"),
                    estado_tarea=d.get("estado")))
            if ruta == "/api/supervisor/resolver_reporte":
                return self._json(self.estado.resolver_reporte(
                    d.get("id_reporte"), d.get("index"), d.get("nuevo_barcode"),
                    d.get("nota"), d.get("estado_tarea")))
            codigo = str(d.get("codigo", "")).strip()
            if ruta == "/api/vincular":
                return self._json(self.estado.perfil(codigo))
            if ruta == "/api/ubicacion":
                self.estado.ubicar(codigo, d.get("lat"), d.get("lon"), d.get("precision"))
                return self._json({"ok": True})
            if ruta == "/api/fachada":
                self.estado.guardar_fachada(codigo, _jpg(d.get("foto")))
                return self._json({"ok": True})
            if ruta == "/api/omitir":
                self.estado.omitir(codigo, d.get("id_product"), d.get("motivo"))
                return self._json({"ok": True, "estado": "omitida"})
            if ruta == "/api/buscar_codigo":
                self.estado._c(codigo)
                return self._json(self.estado.buscar_codigo(d.get("barcode", ""), codigo=codigo))
            if ruta == "/api/leer_codigo":
                self.estado._c(codigo)
                return self._json({"ok": True, "barcode": leer_codigo_imagen(d.get("foto"))})
            if ruta == "/api/subir_foto":
                self.estado._c(codigo)
                tipo = str(d.get("tipo", "producto")).strip()
                raw = _jpg(d.get("foto"))
                with self.estado.lock:
                    if not hasattr(self.estado, "_fotos_temp"):
                        self.estado._fotos_temp = {}
                    self.estado._fotos_temp[(str(codigo), tipo)] = raw
                return self._json({"ok": True, "bytes": len(raw)})
            if ruta == "/api/leer_precio":
                self.estado._c(codigo)
                return self._json(leer_precio_imagen(d.get("foto"), estado=self.estado, codigo=codigo))
            if ruta == "/api/registrar_producto":
                self.estado._c(codigo)
                prod = self.estado.crear_producto(
                    d.get("nombre", ""), d.get("barcode", ""), d.get("contenido", ""),
                    d.get("precio_referencia"), d.get("marca", ""))
                tarea = self.estado.agregar_tarea(codigo, prod["id_product"])
                return self._json({"ok": True, "producto": prod, "tarea": tarea})
            if ruta == "/api/agregar_producto_propio":
                tarea = self.estado.agregar_tarea(codigo, d.get("id_product", ""))
                return self._json({"ok": True, "tarea": tarea})
            if ruta == "/api/eliminar_tarea":
                return self._json(self.estado.eliminar_tarea(codigo, d.get("id_product", "")))
            if ruta == "/api/editar_tarea":
                return self._json(self.estado.editar_tarea(
                    codigo, d.get("id_product", ""),
                    nombre=d.get("nombre"), barcode=d.get("barcode"),
                    contenido=d.get("contenido"), precio_referencia=d.get("precio_referencia"),
                    estado_tarea=d.get("estado")))
            if ruta == "/api/reportar_codigo":
                rep = self.estado.reportar_codigo(codigo, d.get("id_product"), d.get("barcode", ""), d.get("motivo", ""))
                return self._json({"ok": True, "reporte": rep})
            if ruta == "/api/captura":
                fn = capturar_async if d.get("async") else capturar
                return self._json(fn(self.estado, self.motor, codigo, d.get("id_product"),
                                     d.get("foto_producto"), d.get("foto_etiqueta"),
                                     d.get("precio", ""), d.get("barcode")))
            self._json({"error": "No existe."}, 404)
        except KeyError as e:
            self._json({"error": str(e).strip("'\"")}, 404)
        except (ValueError, TypeError, json.JSONDecodeError) as e:
            self._json({"error": str(e) or "Petición no válida."}, 400)
        except Exception as e:  # nunca se le muestra una traza al capturista
            print(f"  ERROR {type(e).__name__}: {e}")
            self._json({"error": "No se pudo procesar. Intenta de nuevo."}, 500)


def precios_csv(estado: Estado) -> str:
    """Hoja de precios validados: solo capturas APROBADAS por el motor."""
    import io
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["producto", "id_product", "cadena", "precio_validado", "precio_referencia_3b", "diferencia_pct",
                "capturista", "hora", "capture_id"])
    for c in estado.resumen()["capturas"]:
        if c["decision"] == "aprobada" and c["precio_detectado"] is not None:
            ref = c.get("precio_referencia")
            dif = f"{(c['precio_detectado'] - ref) / ref * 100:.1f}" if ref else ""
            w.writerow([c["producto"], c["id_product"], c["tienda"], f"{c['precio_detectado']:.2f}",
                        f"{ref:.2f}" if ref else "", dif, c["capturista"], c["hora"], c["capture_id"]])
    return buf.getvalue()


def ip_local() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))  # no envía nada: solo elige la interfaz de salida
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


def _es_ip_descartable(ip: str) -> bool:
    s = str(ip or "").strip()
    try:
        addr = ipaddress.ip_address(s)
    except ValueError:
        return True
    return addr.version != 4 or addr.is_loopback or addr.is_link_local or addr.is_unspecified


def _es_hotspot_windows(ip: str, alias: str = "", desc: str = "") -> bool:
    s = str(ip or "").strip()
    texto = f"{alias} {desc}".strip()
    if re.search(r"wi-?fi\s*direct\s*virtual\s*adapter", texto, re.I):
        return True
    if s.startswith("192.168.137.") and (
        not texto or re.search(r"(local area connection\*|conexi[oó]n de [aá]rea local\*)", texto, re.I)
    ):
        return True
    return False


def _es_adaptador_virtual(ip: str, alias: str = "", desc: str = "", es_virtual: bool = False) -> bool:
    if _es_hotspot_windows(ip, alias, desc):
        return False
    if es_virtual:
        return True
    s = str(ip or "").strip()
    if s.startswith("192.168.56."):
        return True
    texto = f"{alias} {desc}".strip()
    return bool(texto and _PATRON_VIRTUAL.search(texto))


def _adaptadores_windows() -> dict[str, dict]:
    if os.name != "nt":
        return {}
    cmd = (
        "$a=@{}; Get-NetAdapter -IncludeHidden | ForEach-Object { $a[$_.ifIndex]=$_ }; "
        "$gw=@{}; Get-NetRoute -AddressFamily IPv4 -DestinationPrefix '0.0.0.0/0' -ErrorAction SilentlyContinue | "
        "ForEach-Object { $gw[$_.ifIndex]=$true }; "
        "Get-NetIPAddress -AddressFamily IPv4 | ForEach-Object { "
        "$ad=$a[$_.InterfaceIndex]; "
        "[pscustomobject]@{ip=$_.IPAddress; alias=$_.InterfaceAlias; "
        "desc=if($ad){$ad.InterfaceDescription}else{''}; "
        "virtual=if($ad){[bool]$ad.Virtual}else{$false}; "
        "status=if($ad){[string]$ad.Status}else{''}; "
        "has_gw=[bool]$gw[$_.InterfaceIndex]} "
        "} | ConvertTo-Json -Compress"
    )
    try:
        res = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd],
            capture_output=True, text=True, timeout=12, check=True,
        )
        raw = res.stdout.strip()
        if not raw:
            return {}
        data = json.loads(raw)
        items = data if isinstance(data, list) else ([data] if isinstance(data, dict) else [])
        out = {}
        for item in items:
            ip = str(item.get("ip") or "").strip()
            if ip:
                out[ip] = item
        return out
    except Exception:
        return {}


def _recolectar_ips() -> tuple[list[str], list[str]]:
    """Devuelve (primarias_lan_hotspot, virtuales_activas)."""
    principal = ip_local()
    getaddr_mocked = getattr(socket.getaddrinfo, "__module__", "") != "socket"
    win_mocked = getattr(_adaptadores_windows, "__module__", "") != __name__
    meta_win = _adaptadores_windows() if (win_mocked or not getaddr_mocked) else {}

    candidatos = []
    if not _es_ip_descartable(principal):
        candidatos.append(principal)
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ip = info[4][0]
            if not _es_ip_descartable(ip) and ip not in candidatos:
                candidatos.append(ip)
    except Exception:
        pass
    for ip, info in meta_win.items():
        status = str(info.get("status") or "").lower()
        if status in ("", "up") and not _es_ip_descartable(ip) and ip not in candidatos:
            candidatos.append(ip)

    reales_princ, reales_gw, reales_otros, virtuales = [], [], [], []
    for ip in candidatos:
        info = meta_win.get(ip, {})
        status = str(info.get("status") or "").lower()
        if meta_win and ip in meta_win and status and status != "up":
            continue
        es_virt = _es_adaptador_virtual(
            ip,
            str(info.get("alias") or ""),
            str(info.get("desc") or ""),
            bool(info.get("virtual", False)),
        )
        if es_virt:
            virtuales.append(ip)
        elif ip == principal:
            reales_princ.append(ip)
        elif info.get("has_gw"):
            reales_gw.append(ip)
        else:
            reales_otros.append(ip)
    reales = reales_princ + reales_gw + reales_otros
    primarias = reales or virtuales or ["127.0.0.1"]
    return primarias, virtuales


def _ips_extra_activas() -> list[str]:
    _, virtuales = _recolectar_ips()
    return virtuales


def ips_locales() -> list:
    """Devuelve IPv4 locales priorizando LAN/Hotspot reales sobre adaptadores virtuales."""
    primarias, _ = _recolectar_ips()
    return primarias


def certificado(dir_salida: Path, ips):
    """Certificado propio para https (el celular solo da cámara/ubicación en https). Devuelve (cert, llave) o None."""
    dir_salida = Path(dir_salida)
    dir_salida.mkdir(parents=True, exist_ok=True)
    raw_ips = [ips] if isinstance(ips, str) else list(ips)
    lista_ips = []
    for ip in raw_ips:
        s = str(ip or "").strip()
        if not s:
            continue
        try:
            ipaddress.ip_address(s)
            if s not in lista_ips:
                lista_ips.append(s)
        except ValueError:
            continue
    firma = ",".join(sorted(set(lista_ips)))
    cert, llave = dir_salida / "campo-cert.pem", dir_salida / "campo-llave.pem"
    marca = dir_salida / "campo-cert.ip"
    if cert.exists() and llave.exists() and marca.exists() and marca.read_text(encoding="utf-8", errors="ignore").strip() == firma:
        cert_vigente = True
        try:
            import datetime as dt
            from cryptography import x509
            from cryptography.hazmat.primitives import serialization
            c_obj = x509.load_pem_x509_certificate(cert.read_bytes())
            k_obj = serialization.load_pem_private_key(llave.read_bytes(), password=None)
            if (c_obj.public_key().public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
                    != k_obj.public_key().public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)):
                cert_vigente = False
            if c_obj.not_valid_after_utc <= dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=1):
                cert_vigente = False
        except ImportError:
            cert_txt = cert.read_text(encoding="utf-8", errors="ignore")
            llave_txt = llave.read_text(encoding="utf-8", errors="ignore")
            if "BEGIN CERTIFICATE" not in cert_txt or "PRIVATE KEY" not in llave_txt or "END " not in llave_txt:
                cert_vigente = False
        except Exception:
            cert_vigente = False
        if cert_vigente:
            return cert, llave
    try:
        import datetime as dt
        from cryptography import x509
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.x509.oid import NameOID
        k = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        nombre = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Validat3B campo (local)")])
        ahora = dt.datetime.now(dt.timezone.utc)
        sans = [x509.IPAddress(ipaddress.ip_address(ip)) for ip in sorted(set(lista_ips))]
        if "127.0.0.1" not in lista_ips:
            sans.append(x509.IPAddress(ipaddress.ip_address("127.0.0.1")))
        sans.append(x509.DNSName("localhost"))
        san = x509.SubjectAlternativeName(sans)
        c = (x509.CertificateBuilder().subject_name(nombre).issuer_name(nombre).public_key(k.public_key())
             .serial_number(x509.random_serial_number()).not_valid_before(ahora - dt.timedelta(minutes=5))
             .not_valid_after(ahora + dt.timedelta(days=3)).add_extension(san, critical=False)
             .sign(k, hashes.SHA256()))
        llave.write_bytes(k.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL,
                                          serialization.NoEncryption()))
        cert.write_bytes(c.public_bytes(serialization.Encoding.PEM))
    except ImportError:
        san_ips = sorted(set(lista_ips))
        san_items = [f"IP:{ip}" for ip in san_ips]
        if "127.0.0.1" not in san_ips:
            san_items.append("IP:127.0.0.1")
        san_items.append("DNS:localhost")
        san_str = ",".join(san_items)
        for exe in ("openssl", r"C:\Program Files\Git\usr\bin\openssl.exe", r"C:\Program Files\Git\mingw64\bin\openssl.exe"):
            try:
                subprocess.run([exe, "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "3",
                                "-keyout", str(llave), "-out", str(cert), "-subj", "/CN=Validat3B campo (local)",
                                "-addext", f"subjectAltName={san_str}"],
                               check=True, capture_output=True, timeout=60)
                break
            except Exception:
                continue
        else:
            return None
    marca.write_text(firma)
    return cert, llave


def cargar_catalogo(ruta) -> list[dict]:
    if not ruta or not Path(ruta).is_file():
        return []
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        filas = [r for r in csv.DictReader(f) if r.get("id_product") and r.get("product_name")]
    for r in filas:
        r["id_product"] = str(int(float(r["id_product"])))
    return filas


def cargar_env(rutas, ruta_explicita=None):
    if ruta_explicita and not Path(ruta_explicita).is_file():
        print(f"  AVISO: archivo --env no encontrado: {ruta_explicita}")
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    for r in rutas:
        if r and Path(r).is_file():
            if os.environ.get("FOUNDRY_API_KEY") == "":
                os.environ.pop("FOUNDRY_API_KEY", None)
            load_dotenv(r, override=False)


class _ServidorCampo(ThreadingHTTPServer):
    allow_reuse_address = os.name != "nt"


def crear_servidor(estado: Estado, motor, host="0.0.0.0", puerto=8443) -> ThreadingHTTPServer:
    manejador = type("ManejadorCampo", (Manejador,), {"estado": estado, "motor": staticmethod(motor)})
    return _ServidorCampo((host, puerto), manejador)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Validat3B en campo: servidor local para capturistas")
    ap.add_argument("--catalogo", default="datos/privado/metadatos/catalogo_productos.csv")
    ap.add_argument("--salida", default="salidas/campo")
    ap.add_argument("--puerto", type=int, default=8443)
    ap.add_argument("--env", default=None, help="ruta a .env.local (por omisión: ./.env.local y ../repo/.env.local)")
    ap.add_argument("--sin-modelo", action="store_true", help="pruebas: no llama al endpoint; todo sale a revisión")
    ap.add_argument("--http", action="store_true", help="sin https (el celular no dará ubicación ni cámara en vivo)")
    a = ap.parse_args(argv)

    cargar_env([a.env, ".env.local", "../repo/.env.local"], ruta_explicita=a.env)
    if not a.sin_modelo and not (os.environ.get("FOUNDRY_API_KEY") or "").strip():
        print("  AVISO: falta FOUNDRY_API_KEY en el entorno o .env.local.")
        print("  Sin FOUNDRY_API_KEY las capturas caerán a revision_manual (SIN_LECTURA).")
        print("  Configura FOUNDRY_API_KEY en .env.local o ejecuta con --sin-modelo para pruebas.")
    salida = Path(a.salida)
    estado = Estado(salida, cargar_catalogo(a.catalogo))
    motor = motor_sin_modelo if a.sin_modelo else motor_real()
    srv = crear_servidor(estado, motor, puerto=a.puerto)
    ips, extras = _recolectar_ips()
    ips_cert = list(dict.fromkeys(ips + extras))
    par = None if a.http else certificado(salida, ips_cert)
    esquema = "http"
    if par:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(str(par[0]), str(par[1]))
        srv.socket = ctx.wrap_socket(srv.socket, server_side=True)
        esquema = "https"
    srv.urls_publicas = [f"{esquema}://{ip}:{a.puerto}" for ip in ips]
    url_tunel = (os.environ.get("CAMPO_PUBLIC_URL") or "").strip().rstrip("/")
    if url_tunel:
        srv.urls_publicas.insert(0, url_tunel)
    srv.url_publica = srv.urls_publicas[0]
    print("\n  Validat3B en campo")
    for i, u in enumerate(srv.urls_publicas):
        etq = "Capturistas (celular, misma red): " if i == 0 else "  IP alternativa (hotspot/LAN):   "
        print(f"  {etq} {u}/")
    print(f"  Supervisor (en esta laptop):       {esquema}://localhost:{a.puerto}/supervisor")
    print(f"  Catálogo: {len(estado.catalogo)} productos ({len(estado.d.get('productos_custom', {}))} personalizados) · motor: {'SIN MODELO (pruebas)' if a.sin_modelo else 'lectura v3 + reglas + consenso'}")
    if esquema == "http":
        print("  AVISO: sin https el celular no entrega ubicación ni cámara en vivo. Instala `cryptography` o usa Git para Windows (openssl).")
    else:
        print("  El celular mostrará un aviso de certificado la primera vez: «Avanzado» -> «Continuar».")
    print("  Ctrl+C para detener.\n")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n  Detenido. El estado quedó en", estado.ruta)
    finally:
        srv.server_close()
    return 0


# ---------------------------------------------------------------------------------------------------- páginas
_CSS = r"""
@font-face{font-family:'Montserrat';src:url('/fonts/montserrat.woff2') format('woff2');font-weight:100 900;font-display:swap}
:root{
 --brand-50:#FEF3F1;--brand-500:#E31B23;--brand-600:#C4101A;--brand-700:#9D0812;
 --ink-25:#F9FAFA;--ink-100:#EAEEED;--ink-200:#DADFDF;--ink-400:#848F8D;--ink-500:#667170;--ink-600:#4C5857;--ink-700:#31413F;--ink-900:#04211F;
 --white:#FFFFFF;--border:rgba(4,33,31,.12);
 --success:#1F7A4D;--success-bg:#E3F3EA;--warning:#8A5A12;--warning-bg:#FBF1DC;
 --danger:var(--brand-700);--danger-bg:var(--brand-50);--info:#1C244B;--info-bg:#E8EBF5;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;font-family:system-ui,-apple-system,"Segoe UI",sans-serif;color:var(--ink-900);background:var(--white);font-size:16px;line-height:1.5}
header{background:var(--white);color:var(--ink-900);border-bottom:1px solid var(--border);min-height:56px;padding:8px 16px;display:flex;justify-content:space-between;align-items:center;gap:12px}
.marca{display:flex;flex-wrap:wrap;align-items:baseline;gap:8px}
.marca-nom{font-family:'Montserrat',system-ui,sans-serif;font-weight:900;font-size:18px;letter-spacing:-.01em;color:var(--ink-900)}
.marca-sub{font-size:12px;font-weight:500;color:var(--ink-600)}
.meta-hdr{font-size:13px;color:var(--ink-600);text-align:right}
main{max-width:560px;margin:0 auto;padding:16px}
h1,h2,h3,.cifra{font-family:'Montserrat',system-ui,sans-serif;margin:0}
h1{font-size:29px;font-weight:800;line-height:1.2;letter-spacing:-.01em;margin:4px 0 8px}
h2{font-size:20px;font-weight:700;line-height:1.3;margin:0 0 8px}
h3{font-size:17px;font-weight:700;line-height:1.35;margin:0 0 6px}
p{margin:6px 0}
.cifra{font-size:35px;font-weight:800;line-height:40px;letter-spacing:-.01em;font-variant-numeric:tabular-nums;border-bottom:3px solid var(--brand-500);display:inline-block;padding-bottom:2px}
.num,td.n{font-variant-numeric:tabular-nums}
.mono,.cod,.url{font-family:ui-monospace,Consolas,monospace}
.tarjeta{background:var(--white);border:1px solid var(--border);border-radius:8px;padding:16px;margin:12px 0}
.fila-lista{min-height:52px;padding:12px 16px}
.fila{display:flex;justify-content:space-between;align-items:center;gap:12px}
.tenue{color:var(--ink-600);font-size:14px}
.chico{font-size:12px;color:var(--ink-500)}
button,.boton{font:inherit;font-weight:600;font-size:15px;min-height:44px;border-radius:6px;border:1px solid var(--ink-400);background:var(--white);color:var(--ink-900);padding:10px 16px;width:100%;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;gap:8px;text-decoration:none;transition:background-color 150ms cubic-bezier(.2,0,0,1),border-color 150ms cubic-bezier(.2,0,0,1)}
button:hover,.boton:hover{background:var(--ink-25)}
button.btn-primario{background:var(--brand-500);border-color:var(--brand-500);color:var(--white)}
button.btn-primario:hover{background:var(--brand-600);border-color:var(--brand-600)}
button.btn-primario:active{background:var(--brand-700);border-color:var(--brand-700)}
button.btn-sec,.boton.btn-sec{background:var(--white);border-color:var(--ink-400);color:var(--ink-900)}
button.btn-peligro{background:var(--white);border-color:var(--danger);color:var(--danger)}
button.btn-peligro:hover{background:var(--danger-bg)}
button:disabled{opacity:.5;cursor:not-allowed}
button.liga{border:0;background:none;color:var(--brand-600);text-decoration:underline;font-weight:600;min-height:44px;padding:6px 4px;width:auto;justify-content:flex-start}
button.liga:hover{background:none;color:var(--brand-700)}
:focus-visible{outline:2px solid var(--ink-900);outline-offset:2px}
input,select,textarea{font:inherit;font-size:16px;min-height:44px;border:1px solid var(--ink-400);border-radius:6px;padding:10px 12px;width:100%;background:var(--ink-25);color:var(--ink-900)}
label{display:block;font-weight:500;font-size:14px;color:var(--ink-700);margin:10px 0 4px}
.chip{display:inline-flex;align-items:center;gap:6px;border-radius:9999px;height:24px;padding:0 10px;font-size:12px;font-weight:600;white-space:nowrap}
.chip .dot{width:6px;height:6px;border-radius:9999px;background:currentColor;flex-shrink:0}
.pendiente{background:var(--ink-100);color:var(--ink-600)}
.procesando{background:var(--info-bg);color:var(--info)}
.aprobada{background:var(--success-bg);color:var(--success)}
.revision,.repetir{background:var(--warning-bg);color:var(--warning)}
.rechazada{background:var(--danger-bg);color:var(--danger)}
.omitida{background:var(--ink-100);color:var(--ink-500)}
.aviso,.exito,.error,.info{border-radius:8px;padding:12px 14px;margin:10px 0;font-size:14px}
.aviso{border:1px solid var(--warning);background:var(--warning-bg);color:var(--warning)}
.exito{border:1px solid var(--success);background:var(--success-bg);color:var(--success)}
.error{border:1px solid var(--danger);background:var(--danger-bg);color:var(--danger)}
.info{border:1px solid var(--info);background:var(--info-bg);color:var(--info)}
.skel{background:var(--ink-100);border-radius:6px;height:48px;margin:8px 0}
.vacio{border:1px dashed var(--ink-200);border-radius:8px;padding:20px;text-align:center;color:var(--ink-600)}
img.prev{width:100%;max-height:220px;object-fit:cover;border-radius:8px;border:1px solid var(--border);margin-top:8px}
video.cam{width:100%;max-height:240px;object-fit:cover;border-radius:8px;border:1px solid var(--border);background:var(--ink-900);margin-top:8px}
.pasos{display:flex;gap:6px;margin:8px 0 14px}
.pasos i{flex:1;height:5px;border-radius:3px;background:var(--ink-200)}
.pasos i.h{background:var(--brand-500)}
.gap8{display:flex;flex-direction:column;gap:8px}
.rowgap{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
details summary{cursor:pointer;font-weight:600;font-size:14px;min-height:44px;display:flex;align-items:center;color:var(--ink-700)}
@media(prefers-reduced-motion:reduce){*{transition:none!important}}
"""

PAGINA_CAPTURISTA = r"""<!doctype html><html lang="es-MX"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Validat3B · Capturista</title><style>""" + _CSS + r"""</style></head>
<body><header><div class="marca"><span class="marca-nom">Validat3B</span><span class="marca-sub">Prototipo para Tiendas 3B</span></div><span id="quien" class="meta-hdr"></span></header><main id="app"></main>
<script>
const $=s=>document.querySelector(s), app=$('#app');
let codigo=sessionStorage.getItem('codigo')||'', perfil=null, vista='vincular', paso=1, tareaActual=null, wizardProd=null, wizardBc='', fotos={}, pollTimer=null, alertaFondo=null, camStream=null, scanRaf=null, lastStates={};
const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const ETQ={pendiente:'Pendiente',procesando:'Validando',aprobada:'Validada',repetir:'Repetir foto',revision:'A revisión',omitida:'Omitida'};
const chip=est=>`<span class="chip ${esc(est)}"><i class="dot" aria-hidden="true"></i>${esc(ETQ[est]||est)}</span>`;
const pasos=(n,t)=>'<div class="pasos" aria-label="Progreso">'+Array.from({length:t},(_,i)=>'<i class="'+(i<n?'h':'')+'"></i>').join('')+'</div>';

async function api(ruta,datos){
  let r;
  try{ r=await fetch(ruta,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({codigo,...datos})}); }
  catch(e){ throw new Error('Sin conexión con la laptop del supervisor. Revisa que sigas en la misma red.'); }
  const j=await r.json().catch(()=>({error:'Respuesta no válida.'}));
  if(!r.ok) throw new Error(j.error||'No se pudo completar la operación.');
  return j;
}

function mostrarError(e){
  const prev=app.querySelector('.msg-flotante'); if(prev) prev.remove();
  const d=document.createElement('div'); d.className='error msg-flotante'; d.setAttribute('role','alert');
  d.textContent=e.message||String(e); app.prepend(d);
  setTimeout(()=>{ if(d.parentNode) d.remove(); },8000);
}

function foto(archivo){
  return new Promise((ok,mal)=>{
    const img=new Image();
    img.onload=()=>{
      const m=640, k=Math.min(1,m/Math.max(img.width,img.height));
      const c=document.createElement('canvas'); c.width=Math.round(img.width*k); c.height=Math.round(img.height*k);
      c.getContext('2d').drawImage(img,0,0,c.width,c.height);
      URL.revokeObjectURL(img.src);
      ok(c.toDataURL('image/jpeg',.58));
    };
    img.onerror=()=>{ URL.revokeObjectURL(img.src); mal(new Error('No se pudo leer la foto.')); };
    img.src=URL.createObjectURL(archivo);
  });
}

function stopCam(){
  if(scanRaf){ clearInterval(scanRaf); scanRaf=null; }
  if(camStream){ camStream.getTracks().forEach(t=>t.stop()); camStream=null; }
}

function syncStates(tareas){
  const prev={...lastStates};
  const next={};
  for(const t of (tareas||[])){
    next[t.id_product]=t.estado;
    if(prev[t.id_product]==='procesando' && t.estado!=='procesando'){
      if(t.estado==='aprobada'){
        alertaFondo={tipo:'exito',id_product:t.id_product,texto:`${t.nombre}: captura validada.`};
      }else if(t.estado==='repetir'){
        alertaFondo={tipo:'aviso',id_product:t.id_product,texto:`${t.nombre}: ${t.mensaje||'Repite las fotos.'}`};
      }else if(t.estado==='revision'){
        alertaFondo={tipo:'aviso',id_product:t.id_product,texto:`${t.nombre}: ${t.mensaje||'Guardado para revisión.'}`};
      }
    }
  }
  lastStates=next;
}

function asegurarPolling(){
  if(pollTimer) return;
  pollTimer=setInterval(async()=>{
    if(!codigo || !perfil) return;
    const hayProc=(perfil.tareas||[]).some(t=>t.estado==='procesando');
    if(!hayProc && vista!=='lista') return;
    try{
      const r=await fetch('/api/estado?codigo='+encodeURIComponent(codigo));
      if(!r.ok) return;
      const d=await r.json();
      perfil.tareas=d.tareas||[];
      perfil.tiene_fachada=d.tiene_fachada;
      perfil.ubicacion=d.ubicacion;
      syncStates(perfil.tareas);
      if(vista==='lista') renderLista();
    }catch(e){}
  },6000);
}

function vVincular(msg){
  stopCam(); vista='vincular';
  app.innerHTML=`<h1>Vincula tu celular</h1>
  <p class="tenue">Pide tu código de 6 dígitos al supervisor.</p>
  ${msg?`<div class="error" role="alert">${esc(msg)}</div>`:''}
  <div class="tarjeta">
    <label for="c">Código de vinculación</label>
    <input id="c" inputmode="numeric" autocomplete="one-time-code" maxlength="6" placeholder="000000" value="${esc(codigo)}">
    <p></p>
    <button class="btn-primario" id="b">Vincular</button>
  </div>`;
  $('#b').onclick=async()=>{
    codigo=$('#c').value.trim();
    if(!codigo){ vVincular('Escribe tu código de 6 dígitos.'); return; }
    $('#b').disabled=true; $('#b').textContent='Vinculando…';
    try{
      perfil=await api('/api/vincular',{});
      sessionStorage.setItem('codigo',codigo);
      syncStates(perfil.tareas);
      asegurarPolling();
      siguiente();
    }catch(e){ vVincular(e.message); }
  };
}

function siguiente(){
  $('#quien').textContent=perfil.nombre+' · '+perfil.tienda;
  if(!perfil.ubicacion && !sessionStorage.getItem('sinUbic')) return vUbicacion();
  if(!perfil.tiene_fachada) return vFachada();
  vLista();
}

function vUbicacion(){
  stopCam(); vista='ubicacion';
  app.innerHTML=`<h1>Tu ubicación</h1>
  <p class="tenue">Paso inicial: registra la tienda que visitas una sola vez.</p>
  <div class="tarjeta gap8">
    <button class="btn-primario" id="b">Compartir mi ubicación</button>
    <button class="btn-sec" id="o">Ahora no</button>
  </div>`;
  $('#o').onclick=()=>{ sessionStorage.setItem('sinUbic','1'); siguiente(); };
  $('#b').onclick=()=>{
    if(!navigator.geolocation || !window.isSecureContext){
      mostrarError(new Error('Este navegador no entrega ubicación aquí. Pulsa "Ahora no" para continuar.'));
      return;
    }
    $('#b').disabled=true; $('#b').textContent='Buscando…';
    navigator.geolocation.getCurrentPosition(async p=>{
      try{
        await api('/api/ubicacion',{lat:p.coords.latitude,lon:p.coords.longitude,precision:p.coords.accuracy});
        perfil.ubicacion={lat:p.coords.latitude}; siguiente();
      }catch(e){ mostrarError(e); $('#b').disabled=false; $('#b').textContent='Compartir mi ubicación'; }
    },()=>{
      mostrarError(new Error('No se obtuvo la ubicación. Revisa el permiso o pulsa "Ahora no".'));
      $('#b').disabled=false; $('#b').textContent='Compartir mi ubicación';
    },{enableHighAccuracy:true,timeout:15000,maximumAge:60000});
  };
}

function entradaFoto(id,texto){
  return `<label class="boton btn-sec" style="margin:0">${esc(texto)}<input id="${id}" type="file" accept="image/*" capture="environment" hidden></label><img class="prev" id="${id}p" hidden alt="Vista previa">`;
}

function alTomar(id,despues){
  $('#'+id).onchange=async ev=>{
    const f=ev.target.files[0]; if(!f) return;
    try{
      const d=await foto(f); fotos[id]=d;
      const p=$('#'+id+'p'); if(p){ p.src=d; p.hidden=false; }
      if(despues) despues(d);
    }catch(e){ mostrarError(e); }
  };
}

function vFachada(){
  stopCam(); vista='fachada'; fotos={};
  app.innerHTML=`<h1>Fachada de la tienda</h1>
  <p class="tenue">Toma una foto de la entrada donde se lea <b>${esc(perfil.tienda)}</b>.</p>
  <div class="tarjeta gap8">
    ${entradaFoto('fa','Tomar foto de la fachada')}
    <button class="btn-primario" id="b" disabled>Continuar</button>
  </div>`;
  alTomar('fa',()=>{ $('#b').disabled=false; });
  $('#b').onclick=async()=>{
    $('#b').disabled=true; $('#b').textContent='Enviando…';
    try{ await api('/api/fachada',{foto:fotos.fa}); perfil.tiene_fachada=true; siguiente(); }
    catch(e){ mostrarError(e); $('#b').disabled=false; $('#b').textContent='Continuar'; }
  };
}

function vLista(){
  stopCam(); vista='lista';
  renderLista();
}

function renderLista(){
  if(vista!=='lista') return;
  const tareas=perfil?.tareas||[];
  const abiertas=tareas.filter(t=>['pendiente','repetir','procesando'].includes(t.estado)).length;
  const hechas=tareas.filter(t=>['aprobada','revision','omitida'].includes(t.estado)).length;
  const idxPrimera=tareas.findIndex(t=>['pendiente','repetir'].includes(t.estado));
  let bannerHtml='';
  if(alertaFondo){
    const tRep=alertaFondo.tipo==='aviso'?tareas.find(x=>x.id_product===alertaFondo.id_product && x.estado==='repetir'):null;
    bannerHtml=`<div class="${alertaFondo.tipo}" id="bgBanner" role="status">
      <div><b>Actualización:</b> ${esc(alertaFondo.texto)}</div>
      <div class="rowgap" style="margin-top:8px">
        ${tRep?`<button class="btn-sec" id="bgRetry" style="width:auto">Repetir fotos</button>`:''}
        <button class="liga" id="bgClose">Ocultar</button>
      </div>
    </div>`;
  }
  const listaHtml=tareas.length?tareas.map((t,i)=>{
    const accion=['pendiente','repetir'].includes(t.estado)||(t.estado==='revision'&&t.intentos<perfil.max_intentos);
    const clsBtn=(i===idxPrimera)?'btn-primario':'btn-sec';
    const txtBtn=t.estado==='pendiente'?'Capturar':(t.estado==='repetir'?'Repetir fotos':'Reintentar');
    return `<div class="tarjeta fila-lista">
      <div class="fila">
        <div>
          <b>${esc(t.nombre)}</b>
          <div class="tenue">${esc(t.contenido||'')}${t.barcode?` · <span class="mono">${esc(t.barcode)}</span>`:''}</div>
        </div>
        ${chip(t.estado)}
      </div>
      ${t.mensaje&&t.estado!=='pendiente'?`<p class="tenue">${esc(t.mensaje)}</p>`:''}
      <div class="rowgap" style="margin-top:10px">
        ${accion?`<button class="${clsBtn}" data-i="${i}" style="flex:2">${txtBtn}</button>`:''}
        <button class="btn-sec" data-edit="${i}" type="button" style="flex:1">Editar</button>
        <button class="btn-peligro" data-del="${i}" type="button" style="width:auto">Borrar</button>
      </div>
      <div id="editBox-${i}" hidden style="margin-top:10px;border-top:1px solid var(--border);padding-top:10px">
        <label>Nombre</label><input id="edNom-${i}" value="${esc(t.nombre)}">
        <label>Contenido</label><input id="edCnt-${i}" value="${esc(t.contenido||'')}">
        <label>Código de barras</label><input id="edBc-${i}" class="mono" value="${esc(t.barcode||'')}">
        <div class="rowgap" style="margin-top:8px">
          <button class="btn-primario" data-save="${i}" type="button" style="flex:1">Guardar cambios</button>
        </div>
      </div>
    </div>`;
  }).join(''):`<div class="vacio"><p><b>No tienes productos asignados.</b></p><p class="tenue">Escanea un código de barras o da de alta un producto nuevo para comenzar.</p></div>`;

  const btnNuevoCls=(idxPrimera===-1)?'btn-primario':'btn-sec';
  app.innerHTML=`<div class="fila" style="align-items:flex-end">
    <div><span class="cifra" aria-label="Productos pendientes">${abiertas}</span><div class="tenue">por completar (${hechas} de ${tareas.length} cerrados)</div></div>
    <button class="liga" id="btnRef">Actualizar</button>
  </div>
  ${bannerHtml}
  <div class="rowgap" style="margin:12px 0">
    <button class="${btnNuevoCls}" id="btnOtro" style="flex:1">Escanear producto nuevo</button>
    <button class="btn-primario" id="btnAltaProd" style="flex:1">+ Dar de alta producto</button>
  </div>
  ${listaHtml}
  ${tareas.length&&hechas===tareas.length?'<div class="exito"><b>Lista completa.</b> Puedes seguir escaneando otros productos o cerrar esta página.</div>':''}`;

  if($('#bgClose')) $('#bgClose').onclick=()=>{ alertaFondo=null; renderLista(); };
  if($('#bgRetry')) $('#bgRetry').onclick=()=>{
    const t=tareas.find(x=>x.id_product===alertaFondo.id_product);
    alertaFondo=null; if(t) iniciarWizard(t);
  };
  $('#btnRef').onclick=async()=>{
    app.innerHTML='<div class="skel"></div><div class="skel"></div><div class="skel"></div>';
    try{ const d=await fetch('/api/estado?codigo='+encodeURIComponent(codigo)).then(r=>r.json()); if(d.tareas){ perfil.tareas=d.tareas; syncStates(perfil.tareas); } renderLista(); }
    catch(e){ renderLista(); mostrarError(new Error('No se pudo actualizar la lista.')); }
  };
  $('#btnOtro').onclick=()=>iniciarWizard(null,false);
  $('#btnAltaProd').onclick=()=>iniciarWizard(null,true);
  app.querySelectorAll('button[data-i]').forEach(b=>b.onclick=()=>iniciarWizard(perfil.tareas[+b.dataset.i],false));
  app.querySelectorAll('button[data-edit]').forEach(b=>b.onclick=()=>{
    const box=$('#editBox-'+b.dataset.edit); if(box) box.hidden=!box.hidden;
  });
  app.querySelectorAll('button[data-save]').forEach(b=>b.onclick=async()=>{
    const idx=+b.dataset.save, t=perfil.tareas[idx]; if(!t) return;
    b.disabled=true;
    try{
      const r=await api('/api/editar_tarea',{
        id_product:t.id_product,
        nombre:$('#edNom-'+idx).value.trim(),
        contenido:$('#edCnt-'+idx).value.trim(),
        barcode:$('#edBc-'+idx).value.trim()
      });
      if(r.tarea) perfil.tareas[idx]=r.tarea;
      renderLista();
    }catch(e){ mostrarError(e); b.disabled=false; }
  });
  app.querySelectorAll('button[data-del]').forEach(b=>b.onclick=async()=>{
    const idx=+b.dataset.del, t=perfil.tareas[idx]; if(!t) return;
    b.disabled=true;
    try{
      await api('/api/eliminar_tarea',{id_product:t.id_product});
      perfil.tareas.splice(idx,1);
      renderLista();
    }catch(e){ mostrarError(e); b.disabled=false; }
  });
}

let abrirAltaDirecta=false;
function iniciarWizard(t,altaDirecta=false){
  stopCam(); vista='wizard'; paso=1; tareaActual=t||null; fotos={};
  abrirAltaDirecta=!!altaDirecta;
  wizardProd=t?{id_product:t.id_product,nombre:t.nombre,contenido:t.contenido,barcode:t.barcode||'',precio_referencia:t.precio_referencia||''}:null;
  wizardBc=(t&&t.barcode)||'';
  renderWizard();
}

function renderWizard(){
  stopCam();
  if(vista!=='wizard') return;
  const hdrBase=`<button class="liga" id="wBack">← Mis productos</button>${pasos(paso,4)}`;

  if(paso===1){
    const tieneDetector='BarcodeDetector' in window;
    app.innerHTML=`${hdrBase}
    <div class="tenue">Paso 1 de 4</div>
    <h1>Código de barras</h1>
    <p class="tenue">${tareaActual?`Producto elegido: <b>${esc(tareaActual.nombre)}</b>`:'Escanea o escribe el código de barras del producto.'}</p>
    ${tareaActual && !tareaActual.barcode?`<div class="info"><b>Sin código de barras registrado:</b> escanea o escribe el código abajo para registrárselo a <b>${esc(tareaActual.nombre)}</b>.</div>`:''}
    <div class="tarjeta gap8">
      <div class="rowgap">
        <button class="btn-sec" id="btnCam" style="flex:1">${tieneDetector?'Escanear con cámara':'Abrir cámara'}</button>
        <label class="boton btn-sec" style="flex:1;margin:0">Leer código desde foto<input id="bcFoto" type="file" accept="image/*" capture="environment" hidden></label>
      </div>
      <div id="camWrap" hidden>
        <video id="camVid" class="cam" playsinline autoplay muted></video>
        <p></p>
        <button class="btn-sec" id="btnStopCam">Detener cámara</button>
      </div>
      <label for="bcIn">Código de barras</label>
      <div class="rowgap">
        <input id="bcIn" class="mono" inputmode="numeric" placeholder="750..." value="${esc(wizardBc)}" style="flex:1">
        <button class="btn-sec" id="btnBuscar" style="width:auto">${tareaActual && !tareaActual.barcode?'Registrar código':'Buscar código'}</button>
      </div>
      <button class="btn-sec" id="btnAbrirAlta" type="button">${tareaActual?'Editar datos de este producto':'+ Dar de alta nuevo producto manualmente'}</button>
      <div id="bcEstado"></div>
    </div>
    <div id="bcRes"></div>
    ${tareaActual?`<div class="tarjeta"><button class="btn-primario" id="btnSeguirActual">${tareaActual.barcode?'Continuar con este producto':'Guardar código y continuar a fotos'}</button></div>`:''}
    <div class="tarjeta">
      <button class="btn-peligro" id="btnToggleRep">Algo está mal con el código / Mandar a revisión</button>
      <div id="repBox" hidden style="margin-top:10px">
        <label for="repMot">Describe qué está mal</label>
        <input id="repMot" placeholder="p. ej. código dañado, no coincide el producto">
        <p></p>
        <button class="btn-peligro" id="btnEnvRep">Enviar reporte al supervisor</button>
      </div>
    </div>`;

    if($('#btnSeguirActual')) $('#btnSeguirActual').onclick=async()=>{
      const bcVal=$('#bcIn').value.trim()||wizardBc;
      wizardBc=bcVal;
      if(tareaActual && bcVal && bcVal!==tareaActual.barcode){
        $('#btnSeguirActual').disabled=true; $('#btnSeguirActual').textContent='Guardando código…';
        try{
          const ed=await api('/api/editar_tarea',{id_product:tareaActual.id_product,barcode:bcVal});
          if(ed.tarea){
            Object.assign(tareaActual,ed.tarea);
            wizardProd={id_product:tareaActual.id_product,nombre:tareaActual.nombre,contenido:tareaActual.contenido,barcode:bcVal,precio_referencia:tareaActual.precio_referencia||''};
          }
        }catch(e){}
      }
      paso=2; renderWizard();
    };
    $('#btnToggleRep').onclick=()=>{ $('#repBox').hidden=!$('#repBox').hidden; };
    $('#btnEnvRep').onclick=async()=>{
      const motivo=$('#repMot').value.trim();
      if(!motivo){ mostrarError(new Error('Escribe qué está mal con el código.')); return; }
      $('#btnEnvRep').disabled=true;
      try{
        await api('/api/reportar_codigo',{id_product:wizardProd?wizardProd.id_product:null,barcode:$('#bcIn').value.trim()||wizardBc,motivo});
        const d=await fetch('/api/estado?codigo='+encodeURIComponent(codigo)).then(r=>r.json());
        if(d.tareas) perfil.tareas=d.tareas;
        alertaFondo={tipo:'info',texto:'Código enviado a revisión del supervisor.'};
        vLista();
      }catch(e){ mostrarError(e); $('#btnEnvRep').disabled=false; }
    };

    const ejecutarBusqueda=async(bc)=>{
      wizardBc=String(bc||'').trim();
      if(!wizardBc){ mostrarError(new Error('Escribe o escanea un código de barras.')); return; }
      $('#bcEstado').innerHTML='<div class="skel" style="height:36px"></div>';
      try{
        if(tareaActual && (!tareaActual.barcode || tareaActual.barcode===wizardBc)){
          const ed=await api('/api/editar_tarea',{id_product:tareaActual.id_product,barcode:wizardBc});
          $('#bcEstado').innerHTML='';
          if(ed.tarea) Object.assign(tareaActual,ed.tarea);
          wizardProd={id_product:tareaActual.id_product,nombre:tareaActual.nombre,contenido:tareaActual.contenido,barcode:wizardBc,precio_referencia:tareaActual.precio_referencia||''};
          $('#bcRes').innerHTML=`<div class="exito">
            <b>Código registrado en el producto elegido:</b> ${esc(tareaActual.nombre)}
            <div class="tenue">${esc(tareaActual.contenido||'')} · Código: <span class="mono">${esc(wizardBc)}</span></div>
            <p></p>
            <button class="btn-primario" id="btnUsarVinc">Continuar a fotos</button>
          </div>`;
          $('#btnUsarVinc').onclick=()=>{ paso=2; renderWizard(); };
          return;
        }
        const r=await api('/api/buscar_codigo',{barcode:wizardBc});
        $('#bcEstado').innerHTML='';
        if(r.encontrado){
          const p=r.producto;
          wizardProd=p;
          $('#bcRes').innerHTML=`<div class="exito">
            <b>Producto encontrado:</b> ${esc(p.nombre)}
            <div class="tenue">${esc(p.contenido||'')}${p.precio_referencia?` · Ref 3B: $${esc(p.precio_referencia)}`:''}</div>
            <p></p>
            <button class="btn-primario" id="btnUsarEnc">Continuar a fotos</button>
          </div>`;
          $('#btnUsarEnc').onclick=async()=>{
            $('#btnUsarEnc').disabled=true;
            try{
              if(!r.tarea_existente){
                const ag=await api('/api/agregar_producto_propio',{id_product:p.id_product});
                if(ag.tarea && !perfil.tareas.some(x=>x.id_product===ag.tarea.id_product)) perfil.tareas.push(ag.tarea);
                tareaActual=ag.tarea||tareaActual;
              }else{
                tareaActual=r.tarea_existente;
              }
              paso=2; renderWizard();
            }catch(e){ mostrarError(e); $('#btnUsarEnc').disabled=false; }
          };
        }else if(tareaActual){
          const ed=await api('/api/editar_tarea',{id_product:tareaActual.id_product,barcode:wizardBc});
          if(ed.tarea) Object.assign(tareaActual,ed.tarea);
          wizardProd={id_product:tareaActual.id_product,nombre:tareaActual.nombre,contenido:tareaActual.contenido,barcode:wizardBc,precio_referencia:tareaActual.precio_referencia||''};
          $('#bcRes').innerHTML=`<div class="exito">
            <b>Código actualizado para:</b> ${esc(tareaActual.nombre)}
            <div class="tenue">Nuevo código registrado: <span class="mono">${esc(wizardBc)}</span></div>
            <p></p>
            <button class="btn-primario" id="btnUsarAct">Continuar a fotos</button>
          </div>`;
          $('#btnUsarAct').onclick=()=>{ paso=2; renderWizard(); };
        }else{
          mostrarRegistro(wizardBc);
        }
      }catch(e){ $('#bcEstado').innerHTML=''; mostrarError(e); }
    };

    function mostrarRegistro(bcPref, directo=false){
      const prodBase= tareaActual || null;
      $('#bcRes').innerHTML=`${directo?'':`<div class="aviso">${prodBase?`Registrando código de barras para <b>${esc(prodBase.nombre)}</b>.`:'No encontramos ese código en el catálogo. Registra los datos del producto para capturarlo.'}</div>`}
      <div class="tarjeta gap8">
        <h3>${prodBase?`Registrar / editar datos de ${esc(prodBase.nombre)}`:'Dar de alta producto nuevo'}</h3>
        <label class="boton btn-sec" style="margin:0">Autocompletar datos con foto (OCR)<input id="ocrAltaFoto" type="file" accept="image/*" capture="environment" hidden></label>
        <div id="ocrAltaMsg"></div>
        <label for="rn">Nombre del producto</label><input id="rn" placeholder="p. ej. Agua Bonafont 500 ml / Boost Energy" value="${esc(prodBase?.nombre||'')}">
        <label for="rm">Marca (opcional)</label><input id="rm" placeholder="p. ej. Bonafont / Boost">
        <label for="rc">Contenido (opcional)</label><input id="rc" placeholder="p. ej. 500 ml / 235 ml" value="${esc(prodBase?.contenido||'')}">
        <label for="rp">Precio de referencia 3B (opcional)</label><input id="rp" inputmode="decimal" placeholder="0.00" value="${esc(prodBase?.precio_referencia||'')}">
        <label for="rb">Código de barras (opcional si no tiene)</label><input id="rb" class="mono" inputmode="numeric" value="${esc(bcPref||$('#bcIn')?.value||prodBase?.barcode||'')}">
        <p></p>
        <button class="btn-primario" id="btnRegProd">${prodBase?'Guardar en este producto y continuar a fotos':'Dar de alta y continuar a fotos'}</button>
      </div>`;
      if($('#ocrAltaFoto')) $('#ocrAltaFoto').onchange=async ev=>{
        const f=ev.target.files[0]; if(!f) return;
        $('#ocrAltaMsg').innerHTML='<div class="info">Leyendo texto e intentando código de barras…</div>';
        try{
          const d=await foto(f);
          fotos.pr=d;
          api('/api/subir_foto',{tipo:'producto',foto:d}).then(()=>{ fotos.pr_cache=true; }).catch(()=>{});
          const [rOcr, rBc]=await Promise.all([
            api('/api/leer_precio',{foto:d}).catch(()=>({})),
            api('/api/leer_codigo',{foto:d}).catch(()=>({}))
          ]);
          if(rBc && rBc.barcode && !$('#rb').value) $('#rb').value=rBc.barcode;
          const txt=(rOcr && rOcr.texto ? rOcr.texto.trim() : '');
          if(txt){
            const mCont=txt.match(/\b(\d+(?:[.,]\d+)?\s*(?:ml|l|g|kg|gr|pz|pzs|lt))\b/i);
            if(mCont && !$('#rc').value) $('#rc').value=mCont[1];
            const lineas=txt.split(/\r?\n/).map(s=>s.trim()).filter(Boolean);
            if(lineas.length && !$('#rn').value) $('#rn').value=lineas.slice(0,2).join(' ').slice(0,60);
            if(lineas.length && !$('#rm').value) $('#rm').value=lineas[0].slice(0,30);
            $('#ocrAltaMsg').innerHTML=`<div class="exito">Datos autocompletados por OCR (además guardamos esta foto como foto del producto).</div>`;
          }else{
            $('#ocrAltaMsg').innerHTML='<div class="aviso">Foto guardada para el Paso 2. Escribe el nombre del producto abajo.</div>';
          }
        }catch(e){ $('#ocrAltaMsg').innerHTML=''; mostrarError(e); }
      };
      $('#btnRegProd').onclick=async()=>{
        const nombre=$('#rn').value.trim();
        if(!nombre){ mostrarError(new Error('Escribe el nombre del producto.')); return; }
        $('#btnRegProd').disabled=true; $('#btnRegProd').textContent='Guardando…';
        try{
          if(prodBase){
            const ed=await api('/api/editar_tarea',{
              id_product:prodBase.id_product, nombre,
              contenido:$('#rc').value.trim(),
              precio_referencia:$('#rp').value.trim(),
              barcode:$('#rb').value.trim()
            });
            if(ed.tarea) Object.assign(tareaActual,ed.tarea);
            wizardProd={id_product:tareaActual.id_product,nombre:tareaActual.nombre,contenido:tareaActual.contenido,barcode:tareaActual.barcode||'',precio_referencia:tareaActual.precio_referencia||''};
            wizardBc=wizardProd.barcode;
            paso=2; renderWizard();
          }else{
            const reg=await api('/api/registrar_producto',{
              nombre, marca:$('#rm').value.trim(), contenido:$('#rc').value.trim(),
              precio_referencia:$('#rp').value.trim(), barcode:$('#rb').value.trim()
            });
            wizardProd={id_product:reg.producto.id_product,nombre:reg.producto.product_name,contenido:reg.tarea?.contenido||$('#rc').value.trim(),barcode:reg.producto.product_barcode||''};
            wizardBc=wizardProd.barcode;
            if(reg.tarea) perfil.tareas.push(reg.tarea);
            tareaActual=reg.tarea;
            paso=2; renderWizard();
          }
        }catch(e){ mostrarError(e); $('#btnRegProd').disabled=false; $('#btnRegProd').textContent=prodBase?'Guardar en este producto y continuar a fotos':'Dar de alta y continuar a fotos'; }
      };
    }

    $('#btnBuscar').onclick=()=>ejecutarBusqueda($('#bcIn').value);
    $('#btnAbrirAlta').onclick=()=>mostrarRegistro($('#bcIn').value.trim(), true);
    if(abrirAltaDirecta){ abrirAltaDirecta=false; mostrarRegistro($('#bcIn').value.trim(), true); }

    $('#bcFoto').onchange=async ev=>{
      const f=ev.target.files[0]; if(!f) return;
      $('#bcEstado').innerHTML='<div class="info">Leyendo código de la foto…</div>';
      try{
        const d=await foto(f);
        const r=await api('/api/leer_codigo',{foto:d});
        if(r.barcode){
          $('#bcIn').value=r.barcode; $('#bcEstado').innerHTML='';
          await ejecutarBusqueda(r.barcode);
        }else{
          $('#bcEstado').innerHTML='<div class="aviso">No se leyó el código en la foto. Acércate más o escríbelo manualmente.</div>';
        }
      }catch(e){ $('#bcEstado').innerHTML=''; mostrarError(e); }
    };

    $('#btnCam').onclick=async()=>{
      if(!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia){
        mostrarError(new Error('Tu navegador no permite cámara en vivo aquí. Usa "Leer código desde foto".'));
        return;
      }
      try{
        camStream=await navigator.mediaDevices.getUserMedia({video:{facingMode:{ideal:'environment'}}});
        const v=$('#camVid'); v.srcObject=camStream; $('#camWrap').hidden=false;
        if(tieneDetector){
          const det=new BarcodeDetector({formats:['ean_13','ean_8','upc_a','upc_e','code_128']});
          scanRaf=setInterval(async()=>{
            if(!camStream || v.readyState<2) return;
            try{
              const codes=await det.detect(v);
              if(codes && codes.length && codes[0].rawValue){
                const val=codes[0].rawValue.trim();
                stopCam(); $('#camWrap').hidden=true;
                $('#bcIn').value=val;
                ejecutarBusqueda(val);
              }
            }catch(e){}
          },300);
        }else{
          $('#bcEstado').innerHTML='<div class="info">Cámara activa. Si no detecta automático, usa "Leer código desde foto" o escríbelo abajo.</div>';
        }
      }catch(e){
        mostrarError(new Error('No se pudo abrir la cámara. Revisa permisos o usa "Leer código desde foto".'));
      }
    };
    $('#btnStopCam').onclick=()=>{ stopCam(); $('#camWrap').hidden=true; };
  }

  else if(paso===2){
    app.innerHTML=`${hdrBase}
    <div class="tenue">Paso 2 de 4</div>
    <h1>Foto del producto</h1>
    <p class="tenue"><b>${esc(wizardProd?.nombre||'Producto')}</b> · de frente y cerca, que se lean marca y contenido.</p>
    <div class="tarjeta gap8">
      ${entradaFoto('pr',fotos.pr?'Cambiar foto del producto':'Tomar foto del producto')}
      <div id="prEstado"></div>
      <div class="rowgap">
        <button class="btn-sec" id="pAnt" style="flex:1">Paso anterior</button>
        <button class="btn-primario" id="pSig" style="flex:1" ${fotos.pr?'':'disabled'}>Continuar</button>
      </div>
    </div>`;
    if(fotos.pr){ $('#prp').src=fotos.pr; $('#prp').hidden=false; }
    alTomar('pr',async(d)=>{
      $('#pSig').disabled=false;
      fotos.pr_cache=false;
      $('#prEstado').innerHTML='<div class="info">Guardando foto del producto…</div>';
      try{
        await api('/api/subir_foto',{tipo:'producto',foto:d});
        fotos.pr_cache=true;
        $('#prEstado').innerHTML='<div class="exito">Foto del producto lista.</div>';
      }catch(e){ $('#prEstado').innerHTML=''; }
    });
    $('#pAnt').onclick=()=>{ paso=1; renderWizard(); };
    $('#pSig').onclick=()=>{ paso=3; renderWizard(); };
  }

  else if(paso===3){
    app.innerHTML=`${hdrBase}
    <div class="tenue">Paso 3 de 4</div>
    <h1>Foto del letrero de precio</h1>
    <p class="tenue">Acerca el letrero para que llene al menos 1/3 de la foto. El precio se leerá automáticamente con OCR.</p>
    <div class="tarjeta gap8">
      ${entradaFoto('et',fotos.et?'Cambiar foto del letrero':'Tomar foto del letrero')}
      <div id="etEstado">${fotos.precio_ocr?`<div class="exito"><b>Precio detectado por OCR:</b> $${esc(fotos.precio_ocr)}</div>`:''}</div>
      <div class="rowgap">
        <button class="btn-sec" id="pAnt" style="flex:1">Paso anterior</button>
        <button class="btn-primario" id="pSig" style="flex:1" ${fotos.et?'':'disabled'}>Continuar</button>
      </div>
    </div>`;
    if(fotos.et){ $('#etp').src=fotos.et; $('#etp').hidden=false; }
    alTomar('et',async(d)=>{
      $('#pSig').disabled=false;
      fotos.et_cache=false;
      $('#etEstado').innerHTML='<div class="info">Leyendo precio del letrero con OCR…</div>';
      try{
        const r=await api('/api/leer_precio',{foto:d});
        fotos.et_cache=true;
        if(r.precio){
          fotos.precio_ocr=r.precio;
          $('#etEstado').innerHTML=`<div class="exito"><b>Precio detectado por OCR:</b> $${esc(r.precio)}</div>`;
        }else{
          $('#etEstado').innerHTML=`<div class="aviso">Foto guardada. No se distinguió el número por OCR${r.texto?` (leído: "${esc(r.texto.slice(0,40))}")`:''}; podrás confirmarlo en el siguiente paso.</div>`;
        }
      }catch(e){
        $('#etEstado').innerHTML='<div class="aviso">No se pudo leer con OCR en este intento; podrás escribir o reintentar en el siguiente paso.</div>';
      }
    });
    $('#pAnt').onclick=()=>{ paso=2; renderWizard(); };
    $('#pSig').onclick=()=>{ paso=4; renderWizard(); };
  }

  else if(paso===4){
    const precioSugerido=fotos.precio_ocr||(wizardProd&&wizardProd.precio_referencia?String(wizardProd.precio_referencia):'');
    app.innerHTML=`${hdrBase}
    <div class="tenue">Paso 4 de 4</div>
    <h1>Precio y envío</h1>
    <p class="tenue"><b>${esc(wizardProd?.nombre||'Producto')}</b>${wizardBc?` · <span class="mono">${esc(wizardBc)}</span>`:''}</p>
    <div class="tarjeta gap8">
      ${fotos.precio_ocr?`<div class="exito"><b>OCR detectó:</b> $${esc(fotos.precio_ocr)} (puedes ajustarlo si es necesario)</div>`:`<div class="info">Verifica el precio o pulsa "Detectar precio con OCR".</div>`}
      <label for="px">Precio del letrero (pesos)</label>
      <div class="rowgap">
        <input id="px" inputmode="decimal" placeholder="0.00" value="${esc(precioSugerido)}" style="flex:1">
        <button class="btn-sec" id="btnOcrPrecio" type="button" style="width:auto">Detectar con OCR</button>
      </div>
      <div id="ocrMsg"></div>
      <div class="rowgap">
        <button class="btn-sec" id="pAnt" style="flex:1">Paso anterior</button>
        <button class="btn-primario" id="btnEnviar" style="flex:1">Enviar captura</button>
      </div>
    </div>
    <div class="tarjeta">
      <details>
        <summary>¿No puedes capturarlo? Omitir este producto</summary>
        <label for="mo">Motivo</label>
        <select id="mo">${(perfil.motivos_omitir||[]).map(m=>`<option>${esc(m)}</option>`).join('')}</select>
        <p></p>
        <button class="btn-sec" id="btnOmitir">Omitir este producto</button>
      </details>
    </div>`;
    $('#pAnt').onclick=()=>{ paso=3; renderWizard(); };
    $('#btnOcrPrecio').onclick=async()=>{
      if(!fotos.et){ mostrarError(new Error('Primero toma la foto del letrero en el Paso 3.')); return; }
      $('#btnOcrPrecio').disabled=true;
      $('#ocrMsg').innerHTML='<div class="info">Ejecutando OCR sobre el letrero…</div>';
      try{
        const r=await api('/api/leer_precio',{foto:fotos.et});
        fotos.et_cache=true;
        if(r.precio){
          fotos.precio_ocr=r.precio;
          $('#px').value=r.precio;
          $('#ocrMsg').innerHTML=`<div class="exito">Precio detectado por OCR: <b>$${esc(r.precio)}</b></div>`;
        }else{
          $('#ocrMsg').innerHTML=`<div class="aviso">No se detectó un número claro${r.texto?` (texto: "${esc(r.texto.slice(0,40))}")`:''}.</div>`;
        }
      }catch(e){ $('#ocrMsg').innerHTML=''; mostrarError(e); }
      $('#btnOcrPrecio').disabled=false;
    };
    $('#btnOmitir').onclick=async()=>{
      $('#btnOmitir').disabled=true;
      try{
        await api('/api/omitir',{id_product:wizardProd.id_product,motivo:$('#mo').value});
        const d=await fetch('/api/estado?codigo='+encodeURIComponent(codigo)).then(r=>r.json());
        if(d.tareas){ perfil.tareas=d.tareas; syncStates(perfil.tareas); }
        vLista();
      }catch(e){ mostrarError(e); $('#btnOmitir').disabled=false; }
    };
    $('#btnEnviar').onclick=async()=>{
      const precio=$('#px').value;
      $('#btnEnviar').disabled=true; $('#btnEnviar').textContent='Enviando…';
      try{
        if(!fotos.pr_cache && fotos.pr){
          await api('/api/subir_foto',{tipo:'producto',foto:fotos.pr});
          fotos.pr_cache=true;
        }
        if(!fotos.et_cache && fotos.et){
          await api('/api/subir_foto',{tipo:'etiqueta',foto:fotos.et});
          fotos.et_cache=true;
        }
        await api('/api/captura',{
          id_product:wizardProd.id_product,
          foto_producto:fotos.pr_cache?'__CACHE__':fotos.pr,
          foto_etiqueta:fotos.et_cache?'__CACHE__':fotos.et,
          precio, barcode:wizardBc, async:true
        });
        const t=perfil.tareas.find(x=>x.id_product===wizardProd.id_product);
        if(t){ t.estado='procesando'; t.mensaje='Validando en segundo plano…'; lastStates[t.id_product]='procesando'; }
        alertaFondo={tipo:'info',texto:'Enviado a validación en segundo plano.'};
        asegurarPolling();
        vLista();
      }catch(e){ mostrarError(e); $('#btnEnviar').disabled=false; $('#btnEnviar').textContent='Enviar captura'; }
    };
  }

  $('#wBack').onclick=()=>{ stopCam(); vLista(); };
}

(async()=>{
  if(codigo){
    app.innerHTML='<div class="skel"></div><div class="skel"></div>';
    try{
      perfil=await api('/api/vincular',{});
      syncStates(perfil.tareas);
      asegurarPolling();
      return siguiente();
    }catch(e){ sessionStorage.removeItem('codigo'); codigo=''; }
  }
  vVincular();
})();
</script></body></html>"""

PAGINA_SUPERVISOR = r"""<!doctype html><html lang="es-MX"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Validat3B · Supervisor</title><style>""" + _CSS + r"""
main{max-width:1200px;padding:20px 24px}
.rej{display:grid;grid-template-columns:400px 1fr;gap:20px;align-items:start}
@media(max-width:960px){.rej{grid-template-columns:1fr}}
table{width:100%;border-collapse:collapse;font-size:14px}
th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--ink-100);vertical-align:top}
th{font-size:12px;font-weight:600;color:var(--ink-600);background:var(--ink-25)}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:12px 0}
@media(max-width:720px){.kpis{grid-template-columns:repeat(2,1fr)}}
.kpi{background:var(--white);border:1px solid var(--border);border-radius:8px;padding:12px 14px}
.kpi-val{display:block;font-family:'Montserrat',system-ui,sans-serif;font-size:28px;font-weight:800;font-variant-numeric:tabular-nums;line-height:1.2}
.kpi-lbl{font-size:13px;color:var(--ink-600)}
.cod{font:700 20px ui-monospace,Consolas,monospace;letter-spacing:.1em}
.url{font:600 14px ui-monospace,Consolas,monospace;word-break:break-all}
.url-pill{width:auto;min-height:36px;padding:6px 10px;font-size:13px}
.url-pill.activo{border-color:var(--ink-900);background:var(--ink-100)}
.cat-lista{max-height:240px;overflow-y:auto;border:1px solid var(--border);border-radius:6px;margin-top:8px}
.cat-item{display:flex;align-items:center;gap:10px;padding:8px 10px;border-bottom:1px solid var(--ink-100);cursor:pointer;min-height:44px}
.cat-item:last-child{border-bottom:0}
.cat-item input[type=checkbox]{width:18px;height:18px;min-height:18px;flex-shrink:0}
img.mini{width:48px;height:48px;object-fit:cover;border-radius:6px;border:1px solid var(--border)}
.wauto{width:auto}
</style></head><body>
<header><div class="marca"><span class="marca-nom">Validat3B</span><span class="marca-sub">Prototipo para Tiendas 3B</span></div><span id="reloj" class="meta-hdr"></span></header>
<main>
<div id="errSup"></div>
<div class="tarjeta">
  <div class="fila" style="align-items:flex-start;flex-wrap:wrap">
    <div style="flex:1;min-width:260px">
      <h2>Conexión de capturistas</h2>
      <div id="urlsBox" class="rowgap" style="margin:8px 0"><div class="skel" style="height:36px;width:240px"></div></div>
      <div class="url" id="urlActiva">…</div>
      <div class="rowgap" style="margin-top:8px">
        <button class="btn-sec wauto" id="btnCopiar">Copiar enlace</button>
        <a class="boton btn-sec wauto" href="/api/supervisor/precios.csv">Exportar precios validados (CSV)</a>
      </div>
      <p class="tenue" style="margin-top:8px">Usa el mismo wifi o hotspot. Si el celular muestra aviso de certificado la primera vez: Avanzado -> Continuar.</p>
    </div>
    <div id="qrBox" style="flex-shrink:0"></div>
  </div>
</div>

<div class="kpis" id="kpis"><div class="kpi"><div class="skel"></div></div><div class="kpi"><div class="skel"></div></div><div class="kpi"><div class="skel"></div></div><div class="kpi"><div class="skel"></div></div></div>

<div class="rej">
  <div>
    <div class="tarjeta">
      <h2>Lista de productos y alta</h2>
      <label for="catQ">Buscar en catálogo</label>
      <input id="catQ" placeholder="Nombre, marca o código de barras">
      <div class="rowgap" style="margin-top:6px;justify-content:space-between">
        <span class="tenue" id="selCount">0 productos seleccionados (si queda en 0 usa azar)</span>
        <button class="liga" id="btnClearSel" type="button">Limpiar</button>
      </div>
      <div id="catList" class="cat-lista"><div class="skel" style="margin:8px"></div></div>

      <details open style="margin-top:10px">
        <summary>+ Dar de alta nuevo producto en catálogo</summary>
        <label for="pn">Nombre</label><input id="pn" placeholder="p. ej. Agua Bonafont 3B">
        <label for="pm">Marca</label><input id="pm" placeholder="p. ej. Bonafont">
        <label for="pc">Contenido</label><input id="pc" placeholder="p. ej. 500 ml">
        <label for="pb">Código de barras</label><input id="pb" class="mono" placeholder="750...">
        <label for="pp">Precio referencia 3B</label><input id="pp" inputmode="decimal" placeholder="0.00">
        <p></p>
        <button class="btn-sec" id="btnCrearProd" type="button">Guardar producto en catálogo</button>
        <div id="msgProd"></div>
      </details>

      <hr style="border:0;border-top:1px solid var(--ink-100);margin:14px 0">
      <h3>Dar de alta capturista</h3>
      <label for="nom">Nombre</label><input id="nom" autocomplete="off" placeholder="Nombre del capturista">
      <label for="tda">Cadena que visita</label><select id="tda"></select>
      <label for="cua">Cantidad al azar (si no elegiste lista)</label><input id="cua" type="number" min="1" max="30" value="5">
      <label for="fil">Filtro opcional al azar</label><input id="fil" placeholder="p. ej. frijol, leche">
      <p></p>
      <button class="btn-primario" id="alta" type="button">Generar código de vinculación</button>
      <div id="msg"></div>

      <hr style="border:0;border-top:1px solid var(--ink-100);margin:14px 0">
      <h3>Propagar selección a capturista</h3>
      <label for="propCod">Capturista existente</label><select id="propCod"><option value="">Sin capturistas aún</option></select>
      <p></p>
      <button class="btn-sec" id="btnPropagar" type="button">Agregar productos seleccionados</button>
      <div id="msgProp"></div>
    </div>

    <div class="tarjeta">
      <h2>Códigos reportados</h2>
      <div id="repBox" class="tenue">Cargando…</div>
    </div>
  </div>

  <div>
    <div class="tarjeta">
      <h2>Capturistas</h2>
      <div id="caps" class="tenue">Aún no hay capturistas.</div>
    </div>
    <div class="tarjeta">
      <h2>Precios validados por el motor</h2>
      <div id="precios" class="tenue">Aquí aparecen solo las capturas aprobadas.</div>
    </div>
    <div class="tarjeta">
      <h2>Calidad de campo</h2>
      <div id="calidad" class="tenue">Sin capturas todavía.</div>
    </div>
    <div class="tarjeta">
      <h2>Últimas capturas</h2>
      <div id="feed" class="tenue">Sin capturas todavía.</div>
    </div>
  </div>
</div>
</main>
<script>
const $=s=>document.querySelector(s), esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const CADENAS=__CADENAS__;
$('#tda').innerHTML=CADENAS.map(c=>`<option>${esc(c)}</option>`).join('');
const MOTIVO={CAPTURA_LEJANA:'Letrero lejano',CAPTURA_BORROSA:'Foto borrosa',DESCRIPCION_INCOMPLETA:'Frente del producto ilegible',SIN_ETIQUETA_PRECIO:'Sin letrero de precio',PRODUCTO_NO_COINCIDE:'Producto dudoso',ETIQUETA_NO_CORRESPONDE:'Letrero de otro producto',PRECIO_FUERA_DE_RANGO:'Precio fuera de rango',SIN_LECTURA:'Sin lectura'};
const DEC={aprobada:'Aprobada',rechazada:'Repetir foto',revision_manual:'A revisión'};
const TAREA_ETQ={pendiente:'Pendiente',procesando:'Validando',aprobada:'Validada',repetir:'Repetir foto',revision:'A revisión',omitida:'Omitida'};
const chip=(cls,txt)=>`<span class="chip ${esc(cls)}"><i class="dot" aria-hidden="true"></i>${esc(txt)}</span>`;
const fmtNum=(v,d=2)=>(v!=null&&v!==''&&Number.isFinite(Number(v)))?Number(v).toFixed(d):null;

let selectedIds=new Set(), catMap={}, activeUrl='', lastQrUrl='', catTimer=null;

// Encoder QR ISO/IEC 18004 Byte Mode, EC Level L, Versiones 1-5
const QR_GF_EXP=new Uint8Array(512), QR_GF_LOG=new Uint8Array(256);
(()=>{let x=1;for(let i=0;i<255;i++){QR_GF_EXP[i]=x;QR_GF_LOG[x]=i;x<<=1;if(x&256)x^=285;}for(let i=255;i<512;i++)QR_GF_EXP[i]=QR_GF_EXP[i-255];})();
function qrGfMul(a,b){return (a&&b)?QR_GF_EXP[QR_GF_LOG[a]+QR_GF_LOG[b]]:0;}
function qrRsGen(n){let g=[1];for(let i=0;i<n;i++){const nx=new Array(g.length+1).fill(0),f=QR_GF_EXP[i];for(let j=0;j<g.length;j++){nx[j]^=g[j];nx[j+1]^=qrGfMul(g[j],f);}g=nx;}return g;}
function qrRsEc(data,nEc){
  const gen=qrRsGen(nEc), res=new Array(nEc).fill(0);
  for(const b of data){const f=b^res.shift();res.push(0);if(f)for(let i=0;i<nEc;i++)res[i]^=qrGfMul(gen[i+1],f);}
  return res;
}
function qrBchFormat(mask){
  let d=(1<<3)|mask, v=d<<10;
  for(let i=4;i>=0;i--)if((v>>(i+10))&1)v^=0x537<<i;
  return ((d<<10)|v)^0x5412;
}
function qrSvg(text){
  const bytes=Array.from(new TextEncoder().encode(String(text||'')));
  const specs=[[1,19,7,[]],[2,34,10,[6,18]],[3,55,15,[6,22]],[4,80,20,[6,26]],[5,108,26,[6,30]]];
  const sp=specs.find(s=>bytes.length<=s[1]-2);
  if(!sp) return '<div class="tenue">URL demasiado larga para QR.</div>';
  const [ver,nData,nEc,align]=sp, sz=17+4*ver;
  const bits=[];
  const push=(v,n)=>{for(let i=n-1;i>=0;i--)bits.push((v>>i)&1);};
  push(4,4); push(bytes.length,8);
  for(const b of bytes)push(b,8);
  push(0,Math.min(4,nData*8-bits.length));
  while(bits.length%8)bits.push(0);
  const cw=[];
  for(let i=0;i<bits.length;i+=8){let b=0;for(let j=0;j<8;j++)b=(b<<1)|bits[i+j];cw.push(b);}
  const pads=[0xEC,0x11];
  for(let i=0;cw.length<nData;i++)cw.push(pads[i&1]);
  const full=cw.concat(qrRsEc(cw,nEc)), stream=[];
  for(const b of full)for(let i=7;i>=0;i--)stream.push((b>>i)&1);

  const m=Array.from({length:sz},()=>new Int8Array(sz).fill(-1));
  const res=Array.from({length:sz},()=>new Uint8Array(sz));
  const set=(r,c,v,lock=1)=>{if(r>=0&&r<sz&&c>=0&&c<sz){m[r][c]=v;if(lock)res[r][c]=1;}};
  const finder=(r0,c0)=>{for(let r=-1;r<=7;r++)for(let c=-1;c<=7;c++){
    const inb=r>=0&&r<=6&&c>=0&&c<=6;
    const on=inb&&(r===0||r===6||c===0||c===6||(r>=2&&r<=4&&c>=2&&c<=4));
    set(r0+r,c0+c,on?1:0,1);
  }};
  finder(0,0); finder(0,sz-7); finder(sz-7,0);
  for(let i=8;i<sz-8;i++){set(6,i,(i&1)?0:1,1);set(i,6,(i&1)?0:1,1);}
  set(4*ver+9,8,1,1);
  if(align.length===2){
    const ar=align[1], ac=align[1];
    for(let r=-2;r<=2;r++)for(let c=-2;c<=2;c++){
      set(ar+r,ac+c,(Math.abs(r)===2||Math.abs(c)===2||(r===0&&c===0))?1:0,1);
    }
  }
  for(let i=0;i<9;i++){if(i!==6){set(8,i,0,1);set(i,8,0,1);}}
  for(let i=0;i<8;i++){set(8,sz-1-i,0,1);if(i<7)set(sz-1-i,8,0,1);}

  let bi=0, up=true;
  for(let col=sz-1;col>0;col-=2){
    if(col===6)col--;
    for(let k=0;k<sz;k++){
      const r=up?(sz-1-k):k;
      for(let dc=0;dc<2;dc++){
        const c=col-dc;
        if(!res[r][c]){m[r][c]=bi<stream.length?stream[bi++]:0;}
      }
    }
    up=!up;
  }

  let bestM=0, bestPen=1e9, bestGrid=null;
  const maskFn=[
    (r,c)=>(r+c)%2===0,(r,c)=>r%2===0,(r,c)=>c%3===0,(r,c)=>(r+c)%3===0,
    (r,c)=>((r>>1)+((c/3)|0))%2===0,(r,c)=>((r*c)%2+(r*c)%3)===0,
    (r,c)=>(((r*c)%2+(r*c)%3)%2)===0,(r,c)=>(((r+c)%2+(r*c)%3)%2)===0
  ];
  for(let mk=0;mk<8;mk++){
    const g=m.map((row,r)=>row.map((v,c)=>res[r][c]?v:(v^(maskFn[mk](r,c)?1:0))));
    const fmt=qrBchFormat(mk);
    for(let i=0;i<15;i++){
      const bit=(fmt>>i)&1;
      if(i<6)g[i][8]=bit;else if(i<8)g[i+1][8]=bit;else g[sz-15+i][8]=bit;
      if(i<8)g[8][sz-1-i]=bit;else if(i<9)g[8][15-i]=bit;else g[8][14-i]=bit;
    }
    let pen=0, dark=0;
    for(let r=0;r<sz;r++){
      let rc=1, cc=1;
      for(let c=0;c<sz;c++){
        dark+=g[r][c];
        if(c>0){if(g[r][c]===g[r][c-1])rc++;else{if(rc>=5)pen+=rc-2;rc=1;}}
        if(c>0){if(g[c][r]===g[c-1][r])cc++;else{if(cc>=5)pen+=cc-2;cc=1;}}
        if(r<sz-1&&c<sz-1&&g[r][c]===g[r+1][c]&&g[r][c]===g[r][c+1]&&g[r][c]===g[r+1][c+1])pen+=3;
      }
      if(rc>=5)pen+=rc-2;if(cc>=5)pen+=cc-2;
    }
    pen+=Math.abs(((dark*100/(sz*sz))|0)-50)/5*10;
    if(pen<bestPen){bestPen=pen;bestM=mk;bestGrid=g;}
  }
  const q=4, tot=sz+q*2;
  let rects='';
  for(let r=0;r<sz;r++)for(let c=0;c<sz;c++)if(bestGrid[r][c])rects+=`<rect x="${c+q}" y="${r+q}" width="1" height="1"/>`;
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${tot} ${tot}" width="160" height="160" shape-rendering="crispEdges" role="img" aria-label="Código QR para capturistas" style="border:1px solid var(--border);border-radius:8px;background:#fff"><g fill="#04211F">${rects}</g></svg>`;
}

function renderSelectedCount(){
  const n=selectedIds.size;
  $('#selCount').textContent=n?`${n} producto${n===1?'':'s'} seleccionado${n===1?'':'s'}`:'0 seleccionados (usará cantidad al azar)';
}

async function cargarCatalogo(q=''){
  try{
    const r=await fetch('/api/supervisor/catalogo?q='+encodeURIComponent(q));
    if(!r.ok) throw new Error();
    const d=await r.json();
    const prods=d.productos||[];
    for(const p of prods) catMap[p.id_product]=p;
    if(!prods.length){
      $('#catList').innerHTML='<div class="vacio" style="border:0">Sin coincidencias en el catálogo.</div>';
      return;
    }
    $('#catList').innerHTML=prods.slice(0,80).map(p=>{
      const chk=selectedIds.has(p.id_product)?'checked':'';
      const pr=fmtNum(p.product_price,2);
      return `<label class="cat-item"><input type="checkbox" data-pid="${esc(p.id_product)}" ${chk}><div style="flex:1;min-width:0"><div><b>${esc(p.product_name)}</b></div><div class="chico">${esc(p.contenido||'')}${p.product_barcode?` · <span class="mono">${esc(p.product_barcode)}</span>`:''}${pr?` · Ref $${pr}`:''}</div></div></label>`;
    }).join('');
    $('#catList').querySelectorAll('input[type=checkbox]').forEach(cb=>{
      cb.onchange=()=>{
        if(cb.checked) selectedIds.add(cb.dataset.pid); else selectedIds.delete(cb.dataset.pid);
        renderSelectedCount();
      };
    });
  }catch(e){
    $('#catList').innerHTML='<div class="error" role="alert">No se pudo cargar el catálogo.</div>';
  }
}

$('#catQ').oninput=()=>{ clearTimeout(catTimer); catTimer=setTimeout(()=>cargarCatalogo($('#catQ').value),200); };
$('#btnClearSel').onclick=()=>{ selectedIds.clear(); renderSelectedCount(); cargarCatalogo($('#catQ').value); };

$('#btnCrearProd').onclick=async()=>{
  $('#msgProd').innerHTML='';
  const nombre=$('#pn').value.trim();
  if(!nombre){ $('#msgProd').innerHTML='<div class="error" role="alert">Escribe el nombre del producto.</div>'; return; }
  $('#btnCrearProd').disabled=true;
  try{
    const r=await fetch('/api/supervisor/producto',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({nombre,marca:$('#pm').value.trim(),contenido:$('#pc').value.trim(),barcode:$('#pb').value.trim(),precio_referencia:$('#pp').value.trim()})});
    const j=await r.json();
    if(!r.ok) throw new Error(j.error||'No se pudo crear el producto.');
    const p=j.producto;
    catMap[p.id_product]=p;
    selectedIds.add(p.id_product);
    renderSelectedCount();
    $('#msgProd').innerHTML=`<div class="exito">Agregado: <b>${esc(p.product_name)}</b> (<span class="mono">${esc(p.id_product)}</span>)</div>`;
    $('#pn').value=''; $('#pm').value=''; $('#pc').value=''; $('#pb').value=''; $('#pp').value='';
    cargarCatalogo($('#catQ').value);
  }catch(e){ $('#msgProd').innerHTML=`<div class="error" role="alert">${esc(e.message)}</div>`; }
  finally{ $('#btnCrearProd').disabled=false; }
};

$('#alta').onclick=async()=>{
  $('#msg').innerHTML='';
  const body={nombre:$('#nom').value,tienda:$('#tda').value,cuantos:+$('#cua').value,filtro:$('#fil').value};
  if(selectedIds.size>0) body.productos=Array.from(selectedIds);
  try{
    const r=await fetch('/api/supervisor/alta',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    const j=await r.json();
    if(!r.ok){ $('#msg').innerHTML=`<div class="error" role="alert">${esc(j.error)}</div>`; return; }
    $('#msg').innerHTML=`<div class="exito">Código de <b>${esc(j.nombre)}</b>: <span class="cod">${esc(j.codigo)}</span> (${j.tareas.length} productos)</div>`;
    $('#nom').value=''; pinta();
  }catch(e){ $('#msg').innerHTML='<div class="error" role="alert">Error de red al dar de alta.</div>'; }
};

$('#btnPropagar').onclick=async()=>{
  $('#msgProp').innerHTML='';
  const cod=$('#propCod').value;
  if(!cod){ $('#msgProp').innerHTML='<div class="error" role="alert">Elige un capturista.</div>'; return; }
  if(selectedIds.size===0){ $('#msgProp').innerHTML='<div class="error" role="alert">Selecciona al menos un producto arriba.</div>'; return; }
  $('#btnPropagar').disabled=true;
  try{
    let n=0;
    for(const pid of Array.from(selectedIds)){
      const r=await fetch('/api/supervisor/agregar_tarea',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({codigo:cod,id_product:pid})});
      const j=await r.json();
      if(!r.ok) throw new Error(j.error||'No se pudo agregar tarea.');
      n++;
    }
    $('#msgProp').innerHTML=`<div class="exito">Se propagaron ${n} producto${n===1?'':'s'} a <span class="mono">${esc(cod)}</span>.</div>`;
    pinta();
  }catch(e){ $('#msgProp').innerHTML=`<div class="error" role="alert">${esc(e.message)}</div>`; }
  finally{ $('#btnPropagar').disabled=false; }
};

$('#btnCopiar').onclick=async()=>{
  if(!activeUrl) return;
  try{ await navigator.clipboard.writeText(activeUrl); $('#btnCopiar').textContent='Copiado'; setTimeout(()=>$('#btnCopiar').textContent='Copiar enlace',1500); }
  catch(e){}
};

function renderQrYUrls(urls){
  const lista=(urls&&urls.length?urls:[]).map(u=>u.endsWith('/')?u:u+'/');
  if(!lista.length) return;
  if(!activeUrl || !lista.includes(activeUrl)) activeUrl=lista[0];
  $('#urlActiva').textContent=activeUrl;
  $('#urlsBox').innerHTML=lista.map(u=>`<button type="button" class="btn-sec url-pill ${u===activeUrl?'activo':''}" data-u="${esc(u)}">${esc(u)}</button>`).join('');
  $('#urlsBox').querySelectorAll('button[data-u]').forEach(b=>{
    b.onclick=()=>{ activeUrl=b.dataset.u; renderQrYUrls(lista); };
  });
  if(lastQrUrl!==activeUrl){ lastQrUrl=activeUrl; $('#qrBox').innerHTML=qrSvg(activeUrl); }
}

async function pinta(){
  let d;
  try{
    const r=await fetch('/api/supervisor/estado');
    if(!r.ok) throw new Error();
    d=await r.json();
    $('#errSup').innerHTML='';
  }catch(e){
    $('#errSup').innerHTML='<div class="error" role="alert">No se pudo actualizar el panel del supervisor.</div>';
    return;
  }
  $('#reloj').textContent=new Date().toLocaleTimeString('es-MX',{hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false});
  const urls=(d.urls&&d.urls.length)?d.urls:(d.url?[d.url]:[]);
  renderQrYUrls(urls);
  for(const [pid,p] of Object.entries(d.productos_custom||{})) catMap[pid]=p;

  const caps=Object.entries(d.capturistas||{}), c=d.capturas||[], ap=c.filter(x=>x.decision==='aprobada');
  const kpis=d.kpis||{capturistas:caps.length,capturas:c.length,aprobadas:ap.length,rechazadas:c.filter(x=>x.decision==='rechazada').length,reportes_pendientes:0};
  $('#kpis').innerHTML=`<div class="kpi"><span class="cifra">${kpis.reportes_pendientes>0?kpis.reportes_pendientes:kpis.capturas}</span><span class="kpi-lbl">${kpis.reportes_pendientes>0?'Reportes por atender':'Capturas recibidas'}</span></div>
    <div class="kpi"><span class="kpi-val">${kpis.capturistas}</span><span class="kpi-lbl">Capturistas</span></div>
    <div class="kpi"><span class="kpi-val">${kpis.aprobadas}</span><span class="kpi-lbl">Precios validados</span></div>
    <div class="kpi"><span class="kpi-val">${kpis.rechazadas}</span><span class="kpi-lbl">Fotos por repetir</span></div>`;

  const prevSel=$('#propCod').value;
  $('#propCod').innerHTML=caps.length?caps.map(([cod,p])=>`<option value="${esc(cod)}">${esc(cod)} · ${esc(p.nombre)} (${esc(p.tienda)})</option>`).join(''):'<option value="">Sin capturistas aún</option>';
  if(prevSel && caps.some(([cod])=>cod===prevSel)) $('#propCod').value=prevSel;

  if(caps.length){
    $('#caps').innerHTML='<table><tr><th>Capturista</th><th>Código</th><th>Avance</th><th>Ubicación</th><th>Productos</th></tr>'+caps.map(([cod,p])=>{
      const tList=p.tareas||[];
      const h=tList.filter(t=>['aprobada','revision','omitida'].includes(t.estado)).length;
      const v=tList.filter(t=>t.estado==='aprobada').length;
      const u=p.ubicacion?`<a target="_blank" rel="noopener" href="https://maps.google.com/?q=${p.ubicacion.lat},${p.ubicacion.lon}">${p.ubicacion.lat.toFixed(5)}, ${p.ubicacion.lon.toFixed(5)}</a><div class="chico">±${p.ubicacion.precision_m} m · ${esc((p.ubicacion.hora||'').slice(11,16))}</div>`:(p.vinculado?'<span class="tenue">sin compartir</span>':'<span class="tenue">sin vincular</span>');
      const prodHtml=tList.map(t=>{
        const catP=catMap[t.id_product]||{};
        const nom=catP.product_name||t.nombre||('#'+t.id_product);
        const bc=catP.product_barcode||t.barcode||'';
        return `<div style="margin-bottom:6px;display:flex;align-items:center;justify-content:space-between;gap:8px;border-bottom:1px dashed var(--ink-100);padding-bottom:4px">
          <div><b>${esc(nom)}</b>${bc?` <span class="chico mono">(${esc(bc)})</span>`:''} ${chip(t.estado,TAREA_ETQ[t.estado]||t.estado)}</div>
          <div class="rowgap" style="flex-wrap:nowrap">
            <button type="button" class="liga" data-sup-ed="${esc(cod)}" data-pid="${esc(t.id_product)}" data-nom="${esc(nom)}" data-bc="${esc(bc)}">Editar</button>
            <button type="button" class="liga" style="color:var(--danger)" data-sup-del="${esc(cod)}" data-pid="${esc(t.id_product)}">Borrar</button>
          </div>
        </div>`;
      }).join('');
      return `<tr><td><b>${esc(p.nombre)}</b><div class="chico">${esc(p.tienda)}</div></td><td class="cod" style="font-size:15px">${esc(cod)}</td><td class="num">${h} de ${tList.length}<div class="chico">${v} validados</div></td><td>${u}</td><td>${prodHtml||'<span class="tenue">—</span>'}</td></tr>`;
    }).join('')+'</table>';
    $('#caps').querySelectorAll('button[data-sup-del]').forEach(btn=>{
      btn.onclick=async()=>{
        btn.disabled=true;
        try{
          const r=await fetch('/api/supervisor/eliminar_tarea',{method:'POST',headers:{'Content-Type':'application/json'},
            body:JSON.stringify({codigo:btn.dataset.supDel,id_product:btn.dataset.pid})});
          if(!r.ok) throw new Error();
          pinta();
        }catch(e){ btn.disabled=false; $('#errSup').innerHTML='<div class="error" role="alert">No se pudo borrar el producto del capturista.</div>'; }
      };
    });
    $('#caps').querySelectorAll('button[data-sup-ed]').forEach(btn=>{
      btn.onclick=async()=>{
        const nuevoNom=window.prompt('Nombre del producto:',btn.dataset.nom||'');
        if(nuevoNom===null) return;
        const nuevoBc=window.prompt('Código de barras:',btn.dataset.bc||'');
        if(nuevoBc===null) return;
        btn.disabled=true;
        try{
          const r=await fetch('/api/supervisor/editar_tarea',{method:'POST',headers:{'Content-Type':'application/json'},
            body:JSON.stringify({codigo:btn.dataset.supEd,id_product:btn.dataset.pid,nombre:nuevoNom,barcode:nuevoBc})});
          if(!r.ok) throw new Error();
          await cargarCatalogo($('#catQ').value);
          pinta();
        }catch(e){ btn.disabled=false; $('#errSup').innerHTML='<div class="error" role="alert">No se pudo editar el producto.</div>'; }
      };
    });
  }else{
    $('#caps').innerHTML='<div class="vacio">Aún no hay capturistas dados de alta.</div>';
  }

  const reps=(d.reportes_codigo||[]).slice().reverse();
  if(reps.length){
    $('#repBox').innerHTML=reps.map(r=>`<div class="tarjeta" style="margin:8px 0">
      <div class="fila"><b>${esc(r.producto)}</b>${chip(r.resuelto?'aprobada':'revision',r.resuelto?'Atendido':'Pendiente')}</div>
      <div class="chico">${esc(r.capturista)} (${esc(r.tienda)}) · ${esc((r.hora||'').slice(11,16))} · <span class="mono">${esc(r.barcode||'sin código')}</span></div>
      <p style="margin:6px 0">${esc(r.motivo)}</p>
      ${r.resuelto?`<div class="chico">Nota: ${esc(r.nota||'Atendido')}${r.barcode_corregido?` · Código: <span class="mono">${esc(r.barcode_corregido)}</span>`:''}</div>`:`
      <div class="gap8" style="margin-top:8px">
        <input class="mono" data-bc="${esc(r.id_reporte)}" placeholder="Nuevo código de barras (opcional)">
        <input data-nt="${esc(r.id_reporte)}" placeholder="Nota para el capturista (opcional)">
        <button class="btn-sec" data-res="${esc(r.id_reporte)}" type="button">Resolver reporte</button>
      </div>`}
    </div>`).join('');
    $('#repBox').querySelectorAll('button[data-res]').forEach(btn=>{
      btn.onclick=async()=>{
        const id=btn.dataset.res;
        const bc=$(`input[data-bc="${id}"]`)?.value.trim()||'';
        const nt=$(`input[data-nt="${id}"]`)?.value.trim()||'';
        btn.disabled=true;
        try{
          const r=await fetch('/api/supervisor/resolver_reporte',{method:'POST',headers:{'Content-Type':'application/json'},
            body:JSON.stringify({id_reporte:id,nuevo_barcode:bc||null,nota:nt||null})});
          if(!r.ok) throw new Error();
          pinta();
        }catch(e){ btn.disabled=false; $('#errSup').innerHTML='<div class="error" role="alert">No se pudo resolver el reporte.</div>'; }
      };
    });
  }else{
    $('#repBox').innerHTML='<div class="vacio">Sin reportes de código de barras.</div>';
  }

  const comp=(d.comparador&&d.comparador.length)?d.comparador:ap.map(x=>({
    producto:x.producto,barcode:x.barcode||'',cadena:x.tienda,precio_tecleado:x.precio_tecleado,
    precio_validado:x.precio_detectado,precio_referencia:x.precio_referencia,
    diferencia_pct:(x.precio_detectado!=null&&x.precio_referencia)?((x.precio_detectado-x.precio_referencia)/x.precio_referencia*100):null
  }));
  if(comp.length){
    $('#precios').innerHTML='<table><tr><th>Producto</th><th>Cadena</th><th class="n">Tecleado</th><th class="n">Validado</th><th class="n">Ref. 3B</th><th class="n">Dif.</th></tr>'+comp.map(x=>{
      const pTec=fmtNum(x.precio_tecleado,2), pVal=fmtNum(x.precio_validado,2), pRef=fmtNum(x.precio_referencia,2), dif=fmtNum(x.diferencia_pct,1);
      return `<tr><td>${esc(x.producto)}${x.barcode?`<div class="chico mono">${esc(x.barcode)}</div>`:''}</td><td>${esc(x.cadena)}</td><td class="n">${pTec!==null?'$'+pTec:'—'}</td><td class="n">${pVal!==null?'$'+pVal:'—'}</td><td class="n">${pRef!==null?'$'+pRef:'—'}</td><td class="n">${dif!==null?(Number(dif)>0?'+':'')+dif+' %':'—'}</td></tr>`;
    }).join('')+'</table>';
  }else{
    $('#precios').innerHTML='<div class="vacio">Aquí aparecen las capturas aprobadas.</div>';
  }

  if(c.length){
    const filas=(d.motivos_rechazo||[]).map(m=>[MOTIVO[m.reason_code]||m.reason_code,m.cantidad]);
    $('#calidad').innerHTML=`<p>${ap.length} de ${c.length} capturas validadas automáticamente.</p>`+(filas.length?'<table><tr><th>Motivo por el que no se validó</th><th class="n">Capturas</th></tr>'+filas.map(f=>`<tr><td>${esc(f[0])}</td><td class="n">${f[1]}</td></tr>`).join('')+'</table>':'');
    $('#feed').innerHTML='<table><tr><th>Fotos</th><th>Producto</th><th>Capturista</th><th class="n">Precios</th><th>Estado</th><th>Explicación</th></tr>'+c.slice(-12).reverse().map(x=>{
      const pDet=fmtNum(x.precio_detectado,2), pTec=fmtNum(x.precio_tecleado,2);
      const cls=x.decision==='revision_manual'?'revision':(x.decision==='rechazada'?'repetir':x.decision);
      return `<tr><td style="white-space:nowrap"><img class="mini" src="/${esc(x.foto_producto)}" alt="Producto"> <img class="mini" src="/${esc(x.foto_etiqueta)}" alt="Letrero"></td><td><b>${esc(x.producto)}</b>${x.barcode?`<div class="chico mono">${esc(x.barcode)}</div>`:''}<div class="chico">intento ${x.intento} · ${x.segundos} s</div></td><td>${esc(x.capturista)}<div class="chico">${esc(x.tienda)} · ${esc((x.hora||'').slice(11,16))}</div></td><td class="n"><div>${pDet!==null?'$'+pDet:'—'}</div><div class="chico">tec: ${pTec!==null?'$'+pTec:'—'}</div></td><td>${chip(cls,DEC[x.decision]||x.decision)}</td><td>${esc(x.explicacion)}</td></tr>`;
    }).join('')+'</table>';
  }else{
    $('#calidad').innerHTML='<div class="vacio">Sin capturas todavía.</div>';
    $('#feed').innerHTML='<div class="vacio">Sin capturas todavía.</div>';
  }
}

cargarCatalogo('');
pinta();
setInterval(pinta,3000);
</script></body></html>"""


if __name__ == "__main__":
    raise SystemExit(main())
