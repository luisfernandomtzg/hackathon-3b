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
import csv
import json
import os
import random
import secrets
import socket
import ssl
import subprocess
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .contrato import (RC_BORROSA, RC_ETIQUETA_AJENA, RC_INCOMPLETA, RC_LEJANA, RC_NO_COINCIDE, RC_NO_VISIBLE,
                       RC_PANTALLA, RC_PRECIO_RANGO, RC_SIN_ETIQUETA, Captura)

MAX_INTENTOS = 3            # fotos por producto antes de mandarlo a revisión tal cual
MAX_CUERPO = 12 * 1024 * 1024
MOTIVOS_OMITIR = ["No hay producto en anaquel", "No tiene letrero de precio", "No me dejaron tomar la foto",
                  "No encontré el producto", "Otro"]
CADENAS = ["Soriana", "Bodega Aurrera", "Bara", "Neto", "Walmart", "Chedraui"]

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
        self.catalogo = {str(p["id_product"]): p for p in catalogo}
        self.lock = threading.Lock()
        self.d = {"capturistas": {}, "capturas": []}
        if self.ruta.exists():
            try:
                self.d = json.loads(self.ruta.read_text(encoding="utf-8"))
            except Exception:
                pass

    def _guardar(self):
        tmp = self.ruta.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.d, ensure_ascii=False, indent=1), encoding="utf-8")
        os.replace(tmp, self.ruta)

    # --- supervisor ---
    def alta(self, nombre: str, tienda: str, cuantos: int, filtro: str = "") -> dict:
        nombre = " ".join(str(nombre).split())[:60]
        if not nombre:
            raise ValueError("Falta el nombre del capturista.")
        if tienda not in CADENAS:
            raise ValueError("Elige una cadena de la lista.")
        candidatos = [p for p in self.catalogo.values()
                      if not filtro or filtro.lower() in (p["product_name"] + " " + p.get("product_line", "")).lower()]
        if not candidatos:
            raise ValueError("Ningún producto del catálogo coincide con ese filtro.")
        cuantos = max(1, min(int(cuantos), 30, len(candidatos)))
        with self.lock:
            while True:
                codigo = f"{secrets.randbelow(900000) + 100000}"
                if codigo not in self.d["capturistas"]:
                    break
            elegidos = random.sample(candidatos, cuantos)
            self.d["capturistas"][codigo] = {
                "nombre": nombre, "tienda": tienda, "alta": _ahora(), "vinculado": None, "ubicacion": None,
                "fachada": None,
                "tareas": [{"id_product": str(p["id_product"]), "estado": "pendiente", "intentos": 0,
                            "mensaje": None, "precio": None} for p in elegidos]}
            self._guardar()
            return {"codigo": codigo, **self.d["capturistas"][codigo]}

    def resumen(self) -> dict:
        with self.lock:
            return json.loads(json.dumps(self.d))

    # --- capturista ---
    def perfil(self, codigo: str) -> dict:
        with self.lock:
            c = self.d["capturistas"].get(str(codigo).strip())
            if c is None:
                raise KeyError("Código de vinculación no válido.")
            if c["vinculado"] is None:
                c["vinculado"] = _ahora()
                self._guardar()
            tareas = []
            for t in c["tareas"]:
                p = self.catalogo.get(t["id_product"], {})
                tareas.append({**t, "nombre": p.get("product_name", "?"),
                               "contenido": _contenido(p), "linea": p.get("product_line", "")})
            return {"nombre": c["nombre"], "tienda": c["tienda"], "tiene_fachada": bool(c["fachada"]),
                    "ubicacion": c["ubicacion"], "tareas": tareas, "motivos_omitir": MOTIVOS_OMITIR,
                    "max_intentos": MAX_INTENTOS}

    def ubicar(self, codigo, lat, lon, precision):
        with self.lock:
            c = self._c(codigo)
            c["ubicacion"] = {"lat": round(float(lat), 6), "lon": round(float(lon), 6),
                              "precision_m": round(float(precision or 0)), "hora": _ahora()}
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
    datos = base64.b64decode(data_url.split(",", 1)[1])
    if datos[:2] != b"\xff\xd8":
        raise ValueError("La foto no es un JPEG.")
    return datos


def capturar(estado: Estado, motor, codigo, id_product, foto_producto, foto_etiqueta, precio) -> dict:
    """Guarda las fotos, corre el motor y devuelve qué decirle al capturista."""
    with estado.lock:
        c = estado._c(codigo)
        t = estado._t(codigo, id_product)
        if not c["fachada"]:
            raise ValueError("Primero toma la foto de la fachada de la tienda.")
        if t["estado"] in ("aprobada", "omitida"):
            raise ValueError("Este producto ya está cerrado.")
        t["intentos"] += 1
        intento, fachada, tienda, nombre = t["intentos"], c["fachada"], c["tienda"], c["nombre"]
    p = estado.catalogo[str(id_product)]
    cid = f"CAMPO-{codigo}-{id_product}-{intento}"
    f_prod, f_etq = f"fotos/{cid}_product.jpg", f"fotos/{cid}_shelf.jpg"
    (estado.dir / f_prod).write_bytes(_jpg(foto_producto))
    (estado.dir / f_etq).write_bytes(_jpg(foto_etiqueta))
    try:
        precio = float(str(precio).replace("$", "").replace(",", ".").strip()) if str(precio).strip() else None
    except ValueError:
        precio = None

    def _f(k):
        try:
            return float(p[k])
        except Exception:
            return None

    captura = Captura(
        capture_id=cid, capture_store_name=tienda, capture_date=_ahora(),
        capture_barcode=str(p.get("product_barcode", "")), capture_price=precio, capture_brand=None,
        id_product=int(float(p["id_product"])), product_name=p["product_name"],
        product_barcode=str(p.get("product_barcode", "")), product_price=_f("product_price"),
        min_product_price=_f("min_product_price"), max_product_price=_f("max_product_price"),
        unit_product=p.get("unit_product") or None, unit_quantity_product=_f("unit_quantity_product"),
        product_group=p.get("product_group"), product_line=p.get("product_line"),
        facade_file=fachada, product_file=f_prod, shelf_file=f_etq)
    t0 = time.time()
    res = motor(captura, estado.dir)
    r = res.model_dump(mode="json")

    if r["decision"] == "aprobada":
        nuevo, puede_repetir = "aprobada", False
        mensaje = f"Listo. Precio validado: ${r['precio_detectado']:.2f}."
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
    registro = {"capture_id": cid, "codigo": str(codigo), "capturista": nombre, "tienda": tienda,
                "id_product": str(id_product), "producto": p["product_name"], "intento": intento,
                "hora": _ahora(), "segundos": round(time.time() - t0, 1), "decision": r["decision"],
                "reason_code": r["reason_code"], "explicacion": r["explicacion"],
                "precio_detectado": r["precio_detectado"], "precio_tecleado": precio,
                "precio_referencia": _f("product_price"), "foto_producto": f_prod, "foto_etiqueta": f_etq}
    with estado.lock:
        t = estado._t(codigo, id_product)
        t.update(estado=nuevo, mensaje=mensaje, precio=r["precio_detectado"])
        estado.d["capturas"].append(registro)
        estado._guardar()
    return {"estado": nuevo, "mensaje": mensaje, "decision": r["decision"], "puede_repetir": puede_repetir,
            "intento": intento, "precio_detectado": r["precio_detectado"]}


def motor_real(dir_env=None):
    """El mismo motor del lote: lectura v3 + reglas + compuertas + consenso."""
    from .cliente import Cliente
    from .correr import procesar
    clientes = {}

    def _motor(captura, dir_datos):
        cli = clientes.setdefault(str(dir_datos), Cliente(dir_datos))
        return procesar(captura, dir_datos, cli, True)[1]
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
        if self.path.startswith("/api/supervisor/estado"):
            return
        print(f"  {_ahora()[11:]} {self.command} {self.path.split('?')[0]} -> {args[1] if len(args) > 1 else ''}")

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
        self._enviar(codigo, json.dumps(obj, ensure_ascii=False).encode("utf-8"))

    def _cuerpo(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        if n <= 0 or n > MAX_CUERPO:
            raise ValueError("Petición vacía o demasiado grande.")
        return json.loads(self.rfile.read(n).decode("utf-8"))

    def do_GET(self):
        ruta = self.path.split("?")[0]
        if ruta == "/":
            return self._enviar(200, PAGINA_CAPTURISTA.encode("utf-8"), "text/html; charset=utf-8")
        if ruta in ("/supervisor", "/api/supervisor/estado", "/api/supervisor/precios.csv") or ruta.startswith("/fotos/"):
            if not self._local():
                return self._json({"error": "El panel del supervisor solo se abre en la laptop del supervisor."}, 403)
            if ruta == "/supervisor":
                pagina = PAGINA_SUPERVISOR.replace("__CADENAS__", json.dumps(CADENAS, ensure_ascii=False))
                return self._enviar(200, pagina.encode("utf-8"), "text/html; charset=utf-8")
            if ruta == "/api/supervisor/estado":
                d = self.estado.resumen()
                d["url"] = getattr(self.server, "url_publica", "")
                d["n_catalogo"] = len(self.estado.catalogo)
                return self._json(d)
            if ruta == "/api/supervisor/precios.csv":
                return self._enviar(200, precios_csv(self.estado).encode("utf-8-sig"), "text/csv; charset=utf-8")
            archivo = (self.estado.dir / ruta.lstrip("/")).resolve()
            if (self.estado.dir / "fotos").resolve() in archivo.parents and archivo.is_file():
                return self._enviar(200, archivo.read_bytes(), "image/jpeg")
        self._json({"error": "No existe."}, 404)

    def do_POST(self):
        ruta = self.path.split("?")[0]
        try:
            d = self._cuerpo()
            if ruta == "/api/supervisor/alta":
                if not self._local():
                    return self._json({"error": "Solo el supervisor da de alta capturistas."}, 403)
                return self._json(self.estado.alta(d.get("nombre", ""), d.get("tienda", ""),
                                                   d.get("cuantos", 5), d.get("filtro", "")))
            codigo = str(d.get("codigo", "")).strip()
            if ruta == "/api/vincular":
                return self._json(self.estado.perfil(codigo))
            if ruta == "/api/ubicacion":
                self.estado.ubicar(codigo, d["lat"], d["lon"], d.get("precision"))
                return self._json({"ok": True})
            if ruta == "/api/fachada":
                self.estado.guardar_fachada(codigo, _jpg(d.get("foto")))
                return self._json({"ok": True})
            if ruta == "/api/omitir":
                self.estado.omitir(codigo, d.get("id_product"), d.get("motivo"))
                return self._json({"ok": True})
            if ruta == "/api/captura":
                return self._json(capturar(self.estado, self.motor, codigo, d.get("id_product"),
                                           d.get("foto_producto"), d.get("foto_etiqueta"), d.get("precio", "")))
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


def certificado(dir_salida: Path, ip: str):
    """Certificado propio para https (el celular solo da ubicación en https). Devuelve (cert, llave) o None."""
    cert, llave = dir_salida / "campo-cert.pem", dir_salida / "campo-llave.pem"
    marca = dir_salida / "campo-cert.ip"
    if cert.exists() and llave.exists() and marca.exists() and marca.read_text().strip() == ip:
        return cert, llave
    try:
        import datetime as dt
        import ipaddress
        from cryptography import x509
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.x509.oid import NameOID
        k = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        nombre = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Validat3B campo (local)")])
        ahora = dt.datetime.now(dt.timezone.utc)
        san = x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address(ip)),
                                           x509.IPAddress(ipaddress.ip_address("127.0.0.1")), x509.DNSName("localhost")])
        c = (x509.CertificateBuilder().subject_name(nombre).issuer_name(nombre).public_key(k.public_key())
             .serial_number(x509.random_serial_number()).not_valid_before(ahora - dt.timedelta(minutes=5))
             .not_valid_after(ahora + dt.timedelta(days=3)).add_extension(san, critical=False)
             .sign(k, hashes.SHA256()))
        llave.write_bytes(k.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL,
                                          serialization.NoEncryption()))
        cert.write_bytes(c.public_bytes(serialization.Encoding.PEM))
    except ImportError:
        for exe in ("openssl", r"C:\Program Files\Git\usr\bin\openssl.exe", r"C:\Program Files\Git\mingw64\bin\openssl.exe"):
            try:
                subprocess.run([exe, "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "3",
                                "-keyout", str(llave), "-out", str(cert), "-subj", "/CN=Validat3B campo (local)",
                                "-addext", f"subjectAltName=IP:{ip},IP:127.0.0.1,DNS:localhost"],
                               check=True, capture_output=True, timeout=60)
                break
            except Exception:
                continue
        else:
            return None
    marca.write_text(ip)
    return cert, llave


def cargar_catalogo(ruta) -> list[dict]:
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        filas = [r for r in csv.DictReader(f) if r.get("id_product") and r.get("product_name")]
    for r in filas:
        r["id_product"] = str(int(float(r["id_product"])))
    return filas


def cargar_env(rutas):
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    for r in rutas:
        if r and Path(r).is_file():
            load_dotenv(r)
            return


def crear_servidor(estado: Estado, motor, host="0.0.0.0", puerto=8443) -> ThreadingHTTPServer:
    manejador = type("ManejadorCampo", (Manejador,), {"estado": estado, "motor": staticmethod(motor)})
    return ThreadingHTTPServer((host, puerto), manejador)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Validat3B en campo: servidor local para capturistas")
    ap.add_argument("--catalogo", default="datos/privado/metadatos/catalogo_productos.csv")
    ap.add_argument("--salida", default="salidas/campo")
    ap.add_argument("--puerto", type=int, default=8443)
    ap.add_argument("--env", default=None, help="ruta a .env.local (por omisión: ./.env.local y ../repo/.env.local)")
    ap.add_argument("--sin-modelo", action="store_true", help="pruebas: no llama al endpoint; todo sale a revisión")
    ap.add_argument("--http", action="store_true", help="sin https (el celular no dará ubicación)")
    a = ap.parse_args(argv)

    cargar_env([a.env, ".env.local", "../repo/.env.local"])
    salida = Path(a.salida)
    estado = Estado(salida, cargar_catalogo(a.catalogo))
    motor = motor_sin_modelo if a.sin_modelo else motor_real()
    srv = crear_servidor(estado, motor, puerto=a.puerto)
    ip = ip_local()
    par = None if a.http else certificado(salida, ip)
    esquema = "http"
    if par:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(str(par[0]), str(par[1]))
        srv.socket = ctx.wrap_socket(srv.socket, server_side=True)
        esquema = "https"
    srv.url_publica = f"{esquema}://{ip}:{a.puerto}"
    print("\n  Validat3B en campo")
    print(f"  Capturistas (celular, misma red):  {srv.url_publica}/")
    print(f"  Supervisor (en esta laptop):       {esquema}://localhost:{a.puerto}/supervisor")
    print(f"  Catálogo: {len(estado.catalogo)} productos · motor: {'SIN MODELO (pruebas)' if a.sin_modelo else 'lectura v3 + reglas + consenso'}")
    if esquema == "http":
        print("  AVISO: sin https el celular no entrega ubicación. Instala `cryptography` en el venv o usa Git para Windows (openssl).")
    else:
        print("  El celular mostrará un aviso de certificado la primera vez: «Avanzado» -> «Continuar».")
    print("  Ctrl+C para detener.\n")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n  Detenido. El estado quedó en", estado.ruta)
    return 0


# ---------------------------------------------------------------------------------------------------- páginas
_CSS = """
:root{--rojo:#E31B23;--rojo-osc:#C4101A;--tinta:#04211F;--t700:#31413F;--t500:#667170;--t200:#DADFDF;--t100:#EAEEED;
--t50:#F4F6F6;--ok:#1F7A4D;--ok-bg:#E3F3EA;--av:#8A5A12;--av-bg:#FBF0DC;--mal:#9D0812;--mal-bg:#FFE4E0}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;font-family:Montserrat,"Segoe UI",system-ui,-apple-system,sans-serif;color:var(--tinta);background:var(--t50);font-size:16px;line-height:1.4}
header{background:var(--tinta);color:#fff;padding:14px 16px;display:flex;justify-content:space-between;align-items:center;gap:12px}
header b{font-size:17px}header span{font-size:13px;color:var(--t200)}
main{max-width:560px;margin:0 auto;padding:16px}
h1{font-size:22px;margin:4px 0 6px}h2{font-size:17px;margin:20px 0 8px}p{margin:6px 0}
.tarjeta{background:#fff;border:1px solid var(--t200);border-radius:10px;padding:14px;margin:10px 0}
button,.boton{font:inherit;font-weight:700;min-height:48px;border-radius:8px;border:1px solid var(--t200);background:#fff;color:var(--tinta);padding:10px 16px;width:100%;cursor:pointer}
button.primario{background:var(--rojo);border-color:var(--rojo);color:#fff}button.primario:active{background:var(--rojo-osc)}
button:disabled{opacity:.5}button.liga{border:0;background:none;color:var(--t700);text-decoration:underline;font-weight:600;min-height:44px}
input,select{font:inherit;font-size:16px;min-height:48px;border:1px solid var(--t200);border-radius:8px;padding:10px 12px;width:100%;background:#fff;color:var(--tinta)}
label{display:block;font-weight:600;font-size:14px;margin:10px 0 4px}
.chip{display:inline-block;border-radius:999px;padding:2px 10px;font-size:12px;font-weight:700;white-space:nowrap}
.pendiente{background:var(--t100);color:var(--t700)}.aprobada{background:var(--ok-bg);color:var(--ok)}
.revision,.repetir{background:var(--av-bg);color:var(--av)}.rechazada{background:var(--mal-bg);color:var(--mal)}.omitida{background:var(--t100);color:var(--t500)}
.aviso{border-left:4px solid var(--av);background:var(--av-bg);padding:10px 12px;border-radius:6px;margin:10px 0}
.exito{border-left:4px solid var(--ok);background:var(--ok-bg);padding:10px 12px;border-radius:6px;margin:10px 0}
.error{border-left:4px solid var(--mal);background:var(--mal-bg);padding:10px 12px;border-radius:6px;margin:10px 0}
.fila{display:flex;justify-content:space-between;align-items:center;gap:10px}.tenue{color:var(--t500);font-size:14px}
img.prev{width:100%;max-height:220px;object-fit:cover;border-radius:8px;border:1px solid var(--t200);margin-top:8px}
.pasos{display:flex;gap:6px;margin:8px 0 14px}.pasos i{flex:1;height:5px;border-radius:3px;background:var(--t200)}.pasos i.h{background:var(--rojo)}
"""

PAGINA_CAPTURISTA = """<!doctype html><html lang="es-MX"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Validat3B · Capturista</title><style>""" + _CSS + """</style></head>
<body><header><b>Validat3B · campo</b><span id="quien"></span></header><main id="app"></main>
<script>
const $=s=>document.querySelector(s), app=$('#app');
let codigo=sessionStorage.getItem('codigo')||'', perfil=null, actual=null, fotos={};
const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
async function api(ruta,datos){
  let r; try{ r=await fetch(ruta,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({codigo,...datos})}); }
  catch(e){ throw new Error('Sin conexión con la laptop del supervisor. Revisa que sigas en la misma red.'); }
  const j=await r.json().catch(()=>({error:'Respuesta no válida.'}));
  if(!r.ok) throw new Error(j.error||'No se pudo.'); return j;
}
function foto(archivo){ // reduce en el celular: menos datos y la misma lectura
  return new Promise((ok,mal)=>{ const img=new Image(); img.onload=()=>{ const m=1600, k=Math.min(1,m/Math.max(img.width,img.height));
    const c=document.createElement('canvas'); c.width=Math.round(img.width*k); c.height=Math.round(img.height*k);
    c.getContext('2d').drawImage(img,0,0,c.width,c.height); URL.revokeObjectURL(img.src); ok(c.toDataURL('image/jpeg',.85)); };
    img.onerror=()=>mal(new Error('No se pudo leer la foto.')); img.src=URL.createObjectURL(archivo); });
}
const pasos=(n,t)=>'<div class="pasos">'+Array.from({length:t},(_,i)=>'<i class="'+(i<n?'h':'')+'"></i>').join('')+'</div>';
const ETQ={pendiente:'Pendiente',aprobada:'Validada',revision:'A revisión',repetir:'Repetir foto',omitida:'Omitida'};
function error(e){ const d=document.createElement('div'); d.className='error'; d.textContent=e.message||e; app.prepend(d); setTimeout(()=>d.remove(),7000); }

function vVincular(msg){
  app.innerHTML=`<h1>Vincula tu celular</h1><p class="tenue">Pide tu código de 6 dígitos al supervisor.</p>
  ${msg?`<div class="error">${esc(msg)}</div>`:''}<div class="tarjeta"><label for="c">Código de vinculación</label>
  <input id="c" inputmode="numeric" autocomplete="one-time-code" maxlength="6" placeholder="000000" value="${esc(codigo)}">
  <p></p><button class="primario" id="b">Vincular</button></div>`;
  $('#b').onclick=async()=>{ codigo=$('#c').value.trim(); $('#b').disabled=true;
    try{ perfil=await api('/api/vincular',{}); sessionStorage.setItem('codigo',codigo); siguiente(); }catch(e){ vVincular(e.message); } };
}
function siguiente(){
  $('#quien').textContent=perfil.nombre+' · '+perfil.tienda;
  if(!perfil.ubicacion && !sessionStorage.getItem('sinUbic')) return vUbicacion();
  if(!perfil.tiene_fachada) return vFachada();
  vLista();
}
function vUbicacion(){
  app.innerHTML=`${pasos(1,3)}<h1>Tu ubicación</h1><p>Se registra una vez al llegar a la tienda, para saber qué visita es.</p>
  <div class="tarjeta"><button class="primario" id="b">Compartir mi ubicación</button><button class="liga" id="o">Ahora no</button></div>`;
  $('#o').onclick=()=>{ sessionStorage.setItem('sinUbic','1'); siguiente(); };
  $('#b').onclick=()=>{ if(!navigator.geolocation||!window.isSecureContext){ error(new Error('Este navegador no entrega ubicación en esta página. Continúa sin ella.')); return; }
    $('#b').disabled=true; $('#b').textContent='Buscando…';
    navigator.geolocation.getCurrentPosition(async p=>{ try{ await api('/api/ubicacion',{lat:p.coords.latitude,lon:p.coords.longitude,precision:p.coords.accuracy});
        perfil.ubicacion={lat:p.coords.latitude}; siguiente(); }catch(e){ error(e); $('#b').disabled=false; $('#b').textContent='Compartir mi ubicación'; } },
      e=>{ error(new Error('No se obtuvo la ubicación. Revisa el permiso o continúa sin ella.')); $('#b').disabled=false; $('#b').textContent='Compartir mi ubicación'; },
      {enableHighAccuracy:true,timeout:15000,maximumAge:60000}); };
}
function entradaFoto(id,texto){ return `<label class="boton" style="display:flex;align-items:center;justify-content:center;margin:0">${texto}
  <input id="${id}" type="file" accept="image/*" capture="environment" hidden></label><img class="prev" id="${id}p" hidden alt="Vista previa">`; }
function alTomar(id,despues){ $('#'+id).onchange=async ev=>{ const f=ev.target.files[0]; if(!f) return;
  try{ const d=await foto(f); fotos[id]=d; const p=$('#'+id+'p'); p.src=d; p.hidden=false; despues&&despues(); }catch(e){ error(e); } }; }
function vFachada(){
  fotos={};
  app.innerHTML=`${pasos(2,3)}<h1>Fachada de la tienda</h1><p>Una foto de la entrada, donde se lea el nombre de <b>${esc(perfil.tienda)}</b>.</p>
  <div class="tarjeta">${entradaFoto('fa','Tomar foto de la fachada')}<p></p><button class="primario" id="b" disabled>Continuar</button></div>`;
  alTomar('fa',()=>$('#b').disabled=false);
  $('#b').onclick=async()=>{ $('#b').disabled=true; $('#b').textContent='Enviando…';
    try{ await api('/api/fachada',{foto:fotos.fa}); perfil.tiene_fachada=true; siguiente(); }catch(e){ error(e); $('#b').disabled=false; $('#b').textContent='Continuar'; } };
}
function vLista(){
  const hechas=perfil.tareas.filter(t=>['aprobada','revision','omitida'].includes(t.estado)).length;
  app.innerHTML=`${pasos(3,3)}<h1>Tus productos</h1><p class="tenue">${hechas} de ${perfil.tareas.length} cerrados</p>`+
  perfil.tareas.map((t,i)=>`<div class="tarjeta"><div class="fila"><div><b>${esc(t.nombre)}</b><div class="tenue">${esc(t.contenido)}</div></div>
   <span class="chip ${t.estado}">${ETQ[t.estado]||t.estado}</span></div>
   ${t.mensaje&&t.estado!=='pendiente'?`<p class="tenue">${esc(t.mensaje)}</p>`:''}
   ${['pendiente','repetir'].includes(t.estado)||(t.estado==='revision'&&t.intentos<perfil.max_intentos)?`<p></p><button class="${t.estado==='revision'?'':'primario'}" data-i="${i}">${t.estado==='pendiente'?'Capturar':'Repetir fotos'}</button>`:''}</div>`).join('')+
  (hechas===perfil.tareas.length?'<div class="exito"><b>Terminaste la lista.</b> Gracias: ya puedes cerrar esta página.</div>':'');
  app.querySelectorAll('button[data-i]').forEach(b=>b.onclick=()=>vProducto(perfil.tareas[+b.dataset.i]));
}
function vProducto(t){
  actual=t; fotos={};
  app.innerHTML=`<button class="liga" id="v" style="width:auto;padding:0">← Mis productos</button>
  <h1>${esc(t.nombre)}</h1><p class="tenue">${esc(t.contenido)} · intento ${t.intentos+1} de ${perfil.max_intentos}</p>
  ${t.estado==='repetir'&&t.mensaje?`<div class="aviso"><b>Qué mejorar:</b> ${esc(t.mensaje)}</div>`:''}
  <div class="tarjeta"><h2 style="margin-top:0">1. Foto del producto</h2><p class="tenue">De frente y cerca: que se lean marca, descripción y contenido.</p>${entradaFoto('pr','Tomar foto del producto')}</div>
  <div class="tarjeta"><h2 style="margin-top:0">2. Foto del letrero de precio</h2><p class="tenue">Acércate: el letrero debe llenar al menos un tercio de la foto.</p>${entradaFoto('et','Tomar foto del letrero')}</div>
  <div class="tarjeta"><h2 style="margin-top:0">3. Precio que ves</h2><label for="px">Precio en pesos</label><input id="px" inputmode="decimal" placeholder="0.00"></div>
  <button class="primario" id="b" disabled>Enviar captura</button>
  <div class="tarjeta"><b>¿No puedes capturarlo?</b><label for="mo">Motivo</label><select id="mo">${perfil.motivos_omitir.map(m=>`<option>${esc(m)}</option>`).join('')}</select>
  <p></p><button id="om">Omitir este producto</button></div>`;
  const listo=()=>$('#b').disabled=!(fotos.pr&&fotos.et); alTomar('pr',listo); alTomar('et',listo);
  $('#v').onclick=vLista;
  $('#om').onclick=async()=>{ try{ await api('/api/omitir',{id_product:t.id_product,motivo:$('#mo').value}); await recargar(); }catch(e){ error(e); } };
  $('#b').onclick=async()=>{ const precio=$('#px').value; app.innerHTML='<h1>Validando…</h1><p>El motor está leyendo tus fotos. Tarda entre 10 y 40 segundos; no cierres la página.</p>';
    try{ const r=await api('/api/captura',{id_product:t.id_product,foto_producto:fotos.pr,foto_etiqueta:fotos.et,precio}); perfil=await api('/api/vincular',{}); vResultado(t,r); }
    catch(e){ await recargar().catch(()=>{}); error(e); } };
}
function vResultado(t,r){
  const clase=r.estado==='aprobada'?'exito':(r.estado==='repetir'?'aviso':'aviso');
  const titulo=r.estado==='aprobada'?'Captura validada':(r.estado==='repetir'?'Repite las fotos':'Guardada para revisión');
  app.innerHTML=`<h1>${titulo}</h1><div class="${clase}">${esc(r.mensaje)}</div>
   ${r.puede_repetir&&r.estado!=='aprobada'?'<button class="primario" id="rp">Repetir fotos ahora</button><p></p>':''}<button id="sg">Siguiente producto</button>`;
  $('#sg').onclick=vLista; if($('#rp')) $('#rp').onclick=()=>vProducto(perfil.tareas.find(x=>x.id_product===t.id_product));
}
async function recargar(){ perfil=await api('/api/vincular',{}); vLista(); }
(async()=>{ if(codigo){ try{ perfil=await api('/api/vincular',{}); return siguiente(); }catch(e){ sessionStorage.removeItem('codigo'); codigo=''; } } vVincular(); })();
</script></body></html>"""

PAGINA_SUPERVISOR = """<!doctype html><html lang="es-MX"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Validat3B · Supervisor</title><style>""" + _CSS + """
main{max-width:1180px}.rej{display:grid;grid-template-columns:340px 1fr;gap:16px;align-items:start}@media(max-width:900px){.rej{grid-template-columns:1fr}}
table{width:100%;border-collapse:collapse;font-size:14px}th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--t100);vertical-align:top}
th{font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:var(--t500)}td.n{text-align:right;font-variant-numeric:tabular-nums}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.kpi{background:#fff;border:1px solid var(--t200);border-radius:10px;padding:12px}
.kpi b{display:block;font-size:28px;font-variant-numeric:tabular-nums}.kpi span{font-size:13px;color:var(--t500)}
.cod{font:700 22px ui-monospace,Consolas,monospace;letter-spacing:.12em}.url{font:600 15px ui-monospace,Consolas,monospace;word-break:break-all}
img.mini{width:54px;height:54px;object-fit:cover;border-radius:6px;border:1px solid var(--t200)}button{width:auto}
</style></head><body><header><b>Validat3B · panel del supervisor</b><span id="reloj"></span></header><main>
<div class="tarjeta"><div class="fila"><div><div class="tenue">Enlace para los capturistas (misma red wifi)</div><div class="url" id="url">…</div></div>
<a class="boton" style="width:auto;text-decoration:none" href="/api/supervisor/precios.csv">Exportar precios validados (CSV)</a></div></div>
<div class="kpis" id="kpis"></div>
<div class="rej"><div><div class="tarjeta"><h2 style="margin-top:0">Dar de alta a un capturista</h2>
<label for="nom">Nombre</label><input id="nom" autocomplete="off"><label for="tda">Cadena que visita</label><select id="tda"></select>
<label for="cua">Productos a capturar</label><input id="cua" type="number" min="1" max="30" value="5">
<label for="fil">Solo productos que contengan (opcional)</label><input id="fil" placeholder="p. ej. frijol, leche, jabón"><p></p>
<button class="primario" id="alta" style="width:100%">Generar código de vinculación</button><div id="msg"></div></div></div>
<div><div class="tarjeta"><h2 style="margin-top:0">Capturistas</h2><div id="caps" class="tenue">Aún no hay capturistas.</div></div>
<div class="tarjeta"><h2 style="margin-top:0">Precios validados por el motor</h2><div id="precios" class="tenue">Aquí aparecen solo las capturas aprobadas.</div></div>
<div class="tarjeta"><h2 style="margin-top:0">Calidad de campo</h2><div id="calidad" class="tenue">Sin capturas todavía.</div></div>
<div class="tarjeta"><h2 style="margin-top:0">Últimas capturas</h2><div id="feed" class="tenue">Sin capturas todavía.</div></div></div></div></main>
<script>
const $=s=>document.querySelector(s), esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const CADENAS=__CADENAS__; $('#tda').innerHTML=CADENAS.map(c=>`<option>${esc(c)}</option>`).join('');
const MOTIVO={CAPTURA_LEJANA:'Letrero lejano',CAPTURA_BORROSA:'Foto borrosa',DESCRIPCION_INCOMPLETA:'Frente del producto ilegible',SIN_ETIQUETA_PRECIO:'Sin letrero de precio',
 PRODUCTO_NO_COINCIDE:'Producto dudoso',ETIQUETA_NO_CORRESPONDE:'Letrero de otro producto',PRECIO_FUERA_DE_RANGO:'Precio fuera de rango',SIN_LECTURA:'Sin lectura'};
const DEC={aprobada:'Aprobada',rechazada:'Rechazada',revision_manual:'Revisión'};
$('#alta').onclick=async()=>{ $('#msg').innerHTML='';
  const r=await fetch('/api/supervisor/alta',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({nombre:$('#nom').value,tienda:$('#tda').value,cuantos:+$('#cua').value,filtro:$('#fil').value})});
  const j=await r.json(); if(!r.ok){ $('#msg').innerHTML=`<div class="error">${esc(j.error)}</div>`; return; }
  $('#msg').innerHTML=`<div class="exito">Código de <b>${esc(j.nombre)}</b>: <span class="cod">${esc(j.codigo)}</span></div>`; $('#nom').value=''; pinta(); };
async function pinta(){
  let d; try{ d=await (await fetch('/api/supervisor/estado')).json(); }catch(e){ return; }
  $('#url').textContent=d.url+'/'; $('#reloj').textContent=new Date().toLocaleTimeString('es-MX');
  const caps=Object.entries(d.capturistas), c=d.capturas, ap=c.filter(x=>x.decision==='aprobada');
  const rep=c.filter(x=>x.decision==='rechazada').length;
  $('#kpis').innerHTML=[[caps.length,'Capturistas'],[c.length,'Capturas recibidas'],[ap.length,'Precios validados'],[rep,'Fotos que se pidió repetir']].map(k=>`<div class="kpi"><b>${k[0]}</b><span>${k[1]}</span></div>`).join('');
  if(caps.length) $('#caps').innerHTML='<table><tr><th>Capturista</th><th>Código</th><th>Cadena</th><th>Avance</th><th>Ubicación</th></tr>'+caps.map(([cod,p])=>{
    const h=p.tareas.filter(t=>['aprobada','revision','omitida'].includes(t.estado)).length, v=p.tareas.filter(t=>t.estado==='aprobada').length;
    const u=p.ubicacion?`${p.ubicacion.lat.toFixed(5)}, ${p.ubicacion.lon.toFixed(5)}<div class="tenue">±${p.ubicacion.precision_m} m · ${esc(p.ubicacion.hora.slice(11,16))}</div>`:(p.vinculado?'<span class="tenue">sin compartir</span>':'<span class="tenue">sin vincular</span>');
    return `<tr><td><b>${esc(p.nombre)}</b></td><td class="cod" style="font-size:16px">${esc(cod)}</td><td>${esc(p.tienda)}</td><td>${h} de ${p.tareas.length}<div class="tenue">${v} validados</div></td><td>${u}</td></tr>`; }).join('')+'</table>';
  if(ap.length) $('#precios').innerHTML='<table><tr><th>Producto</th><th>Cadena</th><th class="n">Precio validado</th><th class="n">Referencia 3B</th><th class="n">Diferencia</th></tr>'+ap.map(x=>{
    const dif=x.precio_referencia?((x.precio_detectado-x.precio_referencia)/x.precio_referencia*100):null;
    return `<tr><td>${esc(x.producto)}</td><td>${esc(x.tienda)}</td><td class="n">$${x.precio_detectado.toFixed(2)}</td><td class="n">${x.precio_referencia?'$'+x.precio_referencia.toFixed(2):'—'}</td><td class="n">${dif===null?'—':(dif>0?'+':'')+dif.toFixed(1)+' %'}</td></tr>`; }).join('')+'</table>';
  if(c.length){ const m={}; c.filter(x=>x.decision!=='aprobada').forEach(x=>{ const k=MOTIVO[x.reason_code]||'Dudas en la foto'; m[k]=(m[k]||0)+1; });
    const filas=Object.entries(m).sort((a,b)=>b[1]-a[1]);
    $('#calidad').innerHTML=`<p>${ap.length} de ${c.length} capturas se validaron sin persona.</p>`+(filas.length?'<table><tr><th>Motivo por el que no se validó</th><th class="n">Capturas</th></tr>'+filas.map(f=>`<tr><td>${esc(f[0])}</td><td class="n">${f[1]}</td></tr>`).join('')+'</table>':'');
    $('#feed').innerHTML='<table><tr><th>Fotos</th><th>Producto</th><th>Capturista</th><th>Resultado</th><th>Explicación del motor</th></tr>'+c.slice(-12).reverse().map(x=>
     `<tr><td style="white-space:nowrap"><img class="mini" src="/${esc(x.foto_producto)}" alt="Producto"> <img class="mini" src="/${esc(x.foto_etiqueta)}" alt="Letrero"></td><td>${esc(x.producto)}<div class="tenue">intento ${x.intento} · ${x.segundos} s</div></td><td>${esc(x.capturista)}<div class="tenue">${esc(x.tienda)} · ${esc(x.hora.slice(11,16))}</div></td><td><span class="chip ${x.decision==='revision_manual'?'revision':x.decision}">${DEC[x.decision]}</span></td><td>${esc(x.explicacion)}</td></tr>`).join('')+'</table>'; }
}
pinta(); setInterval(pinta,3000);
</script></body></html>"""


if __name__ == "__main__":
    raise SystemExit(main())
