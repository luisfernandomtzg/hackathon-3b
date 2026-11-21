"""Pruebas del servidor de campo. Datos inventados; no usa datos de 3B ni el endpoint."""
import base64
import contextlib
import io
import json
import os
import re
import shutil
import socket
import ssl
import subprocess
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from PIL import Image, ImageDraw

from ml.validat3b import campo, correr
from ml.validat3b.contrato import RC_LEJANA, Resultado, Validaciones

CATALOGO = [
    {"id_product": "1", "product_name": "Aceite Prueba 900 ml", "product_barcode": "7500000000011",
     "product_price": "40.0", "min_product_price": "30.0", "max_product_price": "50.0",
     "unit_product": "mililitro", "unit_quantity_product": "900.0", "product_group": "g", "product_line": "aceite"},
    {"id_product": "2", "product_name": "Frijol Prueba 400 g", "product_barcode": "7500000000028",
     "product_price": "15.0", "min_product_price": "10.0", "max_product_price": "20.0",
     "unit_product": "gramo", "unit_quantity_product": "400.0", "product_group": "g", "product_line": "frijol"},
]

CATALOGO_EXT = CATALOGO + [
    {"id_product": "3", "product_name": "Leche Prueba 1 l", "product_barcode": "0750000000035",
     "product_price": "22.0", "min_product_price": "15.0", "max_product_price": "30.0",
     "unit_product": "litro", "unit_quantity_product": "1.0", "product_group": "g", "product_line": "lacteos"},
    {"id_product": "4", "product_name": "Producto Sin Codigo", "product_barcode": "",
     "product_price": "12.0", "min_product_price": "8.0", "max_product_price": "18.0",
     "unit_product": "pieza", "unit_quantity_product": "1.0", "product_group": "g", "product_line": "otros"},
]

JPG = "data:image/jpeg;base64," + base64.b64encode(b"\xff\xd8\xff\xe0" + b"0" * 64).decode()


def _jpg_blanco(ancho=64, alto=64) -> str:
    im = Image.new("RGB", (ancho, alto), "white")
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=90)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def _ean13_jpg(codigo13: str = "7501031311309") -> str:
    l_cod = {
        "0": "0001101", "1": "0011001", "2": "0010011", "3": "0111101", "4": "0100011",
        "5": "0110001", "6": "0101111", "7": "0111011", "8": "0110111", "9": "0001011",
    }
    r_cod = {k: "".join("1" if b == "0" else "0" for b in v) for k, v in l_cod.items()}
    g_cod = {k: v[::-1] for k, v in r_cod.items()}
    paridad = {
        "0": "LLLLLL", "1": "LLGLGG", "2": "LLGGLG", "3": "LLGGGL", "4": "LGLLGG",
        "5": "LGGLLG", "6": "LGGGLL", "7": "LGLGLG", "8": "LGLGGL", "9": "LGGLGL",
    }[codigo13[0]]
    bits = ["101"]
    for dig, modo in zip(codigo13[1:7], paridad):
        bits.append(l_cod[dig] if modo == "L" else g_cod[dig])
    bits.append("01010")
    for dig in codigo13[7:]:
        bits.append(r_cod[dig])
    bits.append("101")
    patron = "".join(bits)

    mod = 3
    margen = 40
    ancho = len(patron) * mod + 2 * margen
    alto = 140
    im = Image.new("RGB", (ancho, alto), "white")
    draw = ImageDraw.Draw(im)
    for i, bit in enumerate(patron):
        if bit == "1":
            x = margen + i * mod
            draw.rectangle([x, 16, x + mod - 1, alto - 16], fill="black")
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=95)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def motor_falso(decisiones, precio_detectado=41.5):
    cola = list(decisiones)

    def _m(captura, dir_datos):
        dec, rc = cola.pop(0)
        return Resultado(capture_id=captura.capture_id, decision=dec, confidence_score=0.9, reason_code=rc,
                         validaciones=Validaciones(), precio_detectado=precio_detectado,
                         explicacion="explicación de prueba")
    return _m


@contextlib.contextmanager
def _con_servidor(estado, motor):
    srv = campo.crear_servidor(estado, motor, host="127.0.0.1", puerto=0)
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    srv.url_publica = base
    srv.urls_publicas = [base]
    hilo = threading.Thread(target=srv.serve_forever, daemon=True)
    hilo.start()

    def req(metodo: str, ruta: str, cuerpo=None, parsear_json=True, con_headers=False):
        data = json.dumps(cuerpo).encode("utf-8") if cuerpo is not None else None
        headers = {"Content-Type": "application/json"} if cuerpo is not None else {}
        r = urllib.request.Request(base + ruta, data=data, headers=headers, method=metodo)
        try:
            with urllib.request.urlopen(r, timeout=10) as resp:
                raw = resp.read()
                val = json.loads(raw) if parsear_json else raw
                return (resp.status, dict(resp.headers), val) if con_headers else (resp.status, val)
        except urllib.error.HTTPError as e:
            raw = e.read()
            val = json.loads(raw) if parsear_json else raw
            return (e.code, dict(e.headers), val) if con_headers else (e.code, val)

    try:
        yield base, srv, req
    finally:
        srv.shutdown()
        srv.server_close()
        hilo.join(timeout=2)


class CampoTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.estado = campo.Estado(Path(self.tmp.name), CATALOGO)

    def tearDown(self):
        self.tmp.cleanup()

    def _alta(self, n=2):
        return self.estado.alta("Ana Prueba", "Soriana", n)["codigo"]

    def test_alta_da_codigo_de_6_digitos_y_tareas_del_catalogo(self):
        cod = self._alta()
        self.assertRegex(cod, r"^\d{6}$")
        p = self.estado.perfil(cod)
        self.assertEqual((p["nombre"], p["tienda"], len(p["tareas"])), ("Ana Prueba", "Soriana", 2))
        with self.assertRaises(KeyError):
            self.estado.perfil("000000")
        with self.assertRaises(ValueError):
            self.estado.alta("", "Soriana", 1)
        with self.assertRaises(ValueError):
            self.estado.alta("Ana", "Tienda inventada", 1)

    def test_no_se_captura_sin_fachada(self):
        cod = self._alta(1)
        idp = self.estado.perfil(cod)["tareas"][0]["id_product"]
        with self.assertRaises(ValueError):
            campo.capturar(self.estado, motor_falso([("aprobada", None)]), cod, idp, JPG, JPG, "41.5")

    def test_letrero_lejano_pide_repetir_y_luego_valida(self):
        cod = self._alta(1)
        idp = self.estado.perfil(cod)["tareas"][0]["id_product"]
        self.estado.guardar_fachada(cod, campo._jpg(JPG))
        motor = motor_falso([("rechazada", RC_LEJANA), ("aprobada", None)])
        r1 = campo.capturar(self.estado, motor, cod, idp, JPG, JPG, "41.50")
        self.assertEqual((r1["estado"], r1["puede_repetir"]), ("repetir", True))
        self.assertIn("Acerca el letrero", r1["mensaje"])
        r2 = campo.capturar(self.estado, motor, cod, idp, JPG, JPG, "41.50")
        self.assertEqual(r2["estado"], "aprobada")
        with self.assertRaises(ValueError):  # ya cerrado: no se vuelve a capturar
            campo.capturar(self.estado, motor, cod, idp, JPG, JPG, "41.50")
        csv_txt = campo.precios_csv(self.estado)
        self.assertEqual(csv_txt.count("\n"), 2)  # encabezado + 1 aprobada
        self.assertIn("41.50", csv_txt)

    def test_al_tercer_rechazo_queda_en_revision(self):
        cod = self._alta(1)
        idp = self.estado.perfil(cod)["tareas"][0]["id_product"]
        self.estado.guardar_fachada(cod, campo._jpg(JPG))
        motor = motor_falso([("rechazada", RC_LEJANA)] * 3)
        estados = [campo.capturar(self.estado, motor, cod, idp, JPG, JPG, "")["estado"] for _ in range(3)]
        self.assertEqual(estados, ["repetir", "repetir", "revision"])

    def test_omitir_exige_motivo_de_la_lista(self):
        cod = self._alta(1)
        idp = self.estado.perfil(cod)["tareas"][0]["id_product"]
        with self.assertRaises(ValueError):
            self.estado.omitir(cod, idp, "porque sí")
        self.estado.omitir(cod, idp, campo.MOTIVOS_OMITIR[0])
        self.assertEqual(self.estado.perfil(cod)["tareas"][0]["estado"], "omitida")

    def test_el_estado_sobrevive_a_un_reinicio(self):
        cod = self._alta(1)
        otro = campo.Estado(Path(self.tmp.name), CATALOGO)
        self.assertEqual(otro.perfil(cod)["nombre"], "Ana Prueba")

    def test_http_de_punta_a_punta(self):
        srv = campo.crear_servidor(self.estado, motor_falso([("aprobada", None)]), host="127.0.0.1", puerto=0)
        srv.url_publica = "http://prueba"
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{srv.server_address[1]}"

        def post(ruta, d):
            req = urllib.request.Request(base + ruta, json.dumps(d).encode(), {"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=10) as r:
                    return r.status, json.loads(r.read())
            except urllib.error.HTTPError as e:
                return e.code, json.loads(e.read())
        try:
            self.assertEqual(post("/api/vincular", {"codigo": "123"})[0], 404)
            _, alta = post("/api/supervisor/alta", {"nombre": "Luis", "tienda": "Bara", "cuantos": 1})
            cod = alta["codigo"]
            _, perfil = post("/api/vincular", {"codigo": cod})
            idp = perfil["tareas"][0]["id_product"]
            self.assertEqual(post("/api/ubicacion", {"codigo": cod, "lat": 19.4326, "lon": -99.1332, "precision": 12})[0], 200)
            self.assertEqual(post("/api/fachada", {"codigo": cod, "foto": JPG})[0], 200)
            self.assertEqual(post("/api/fachada", {"codigo": cod, "foto": "data:text/plain;base64,AAAA"})[0], 400)
            st, r = post("/api/captura", {"codigo": cod, "id_product": idp, "foto_producto": JPG, "foto_etiqueta": JPG, "precio": "41.5"})
            self.assertEqual((st, r["estado"]), (200, "aprobada"))
            with urllib.request.urlopen(base + "/api/supervisor/estado", timeout=10) as resp:
                d = json.loads(resp.read())
            self.assertEqual((len(d["capturas"]), d["capturistas"][cod]["ubicacion"]["lat"]), (1, 19.4326))
            with urllib.request.urlopen(base + "/", timeout=10) as resp:
                self.assertIn("Vincula tu celular", resp.read().decode())
            with self.assertRaises(urllib.error.HTTPError):  # nada fuera de fotos/
                urllib.request.urlopen(base + "/fotos/../estado.json", timeout=10)
        finally:
            srv.shutdown()
            srv.server_close()

    def test_crear_producto_y_persistencia(self):
        p1 = self.estado.crear_producto("Agua Bonafont 3B", "7501017004270", "500 ml", "$18.50", "Bonafont")
        p2 = self.estado.crear_producto("Frijol Especial", "", "1,5 kg", "42", "3B")
        self.assertEqual(p1["id_product"], "900001")
        self.assertEqual(p2["id_product"], "900002")
        self.assertEqual((p1["unit_quantity_product"], p1["unit_product"]), ("500.0", "mililitro"))
        self.assertEqual((p1["min_product_price"], p1["max_product_price"]), ("9.25", "33.3"))
        self.assertEqual((p2["unit_quantity_product"], p2["unit_product"]), ("1.5", "kilogramo"))
        with self.assertRaises(ValueError):
            self.estado.crear_producto("   ")
        recargado = campo.Estado(Path(self.tmp.name), CATALOGO)
        self.assertIn("900001", recargado.catalogo)
        p3 = recargado.crear_producto("Boost Energy", "", "473 ml", "25")
        self.assertEqual(p3["id_product"], "900003")

    def test_buscar_codigo_exacto_y_ceros_a_la_izquierda(self):
        est = campo.Estado(Path(self.tmp.name), CATALOGO_EXT)
        # Exacto vs ceros iniciales
        r_exact = est.buscar_codigo("0750000000035")
        self.assertTrue(r_exact["encontrado"])
        self.assertEqual(r_exact["producto"]["id_product"], "3")
        r_sin_cero = est.buscar_codigo("750000000035")
        self.assertTrue(r_sin_cero["encontrado"])
        self.assertEqual(r_sin_cero["producto"]["id_product"], "3")
        r_con_cero = est.buscar_codigo("07500000000011")
        self.assertTrue(r_con_cero["encontrado"])
        self.assertEqual(r_con_cero["producto"]["id_product"], "1")
        # Casos vacíos / solo ceros nunca empatan producto sin código ("4")
        for malo in ("", "   ", "000", "0000"):
            self.assertEqual(est.buscar_codigo(malo), {"encontrado": False})
        # Si existen ambos (exacto y sin ceros), prefiere exacto
        est.crear_producto("Duplicado Con Cero", "07500000000011", "500 ml", "10")
        self.assertEqual(est.buscar_codigo("07500000000011")["producto"]["nombre"], "Duplicado Con Cero")
        self.assertEqual(est.buscar_codigo("7500000000011")["producto"]["id_product"], "1")

    def test_alta_con_productos_explicitos_y_errores(self):
        a1 = self.estado.alta("Luis", "Bara", productos=["1", "2"])
        self.assertEqual([t["id_product"] for t in a1["tareas"]], ["1", "2"])
        a2 = self.estado.alta("Marta", "Soriana", productos=[
            {"id_product": "1"},
            {"nombre": "Agua Bonafont 3B", "contenido": "500 ml", "precio_referencia": 10},
        ])
        self.assertEqual(a2["tareas"][0]["id_product"], "1")
        self.assertGreaterEqual(int(a2["tareas"][1]["id_product"]), 900001)
        a3 = self.estado.alta("Sofi", "Neto", cuantos=5, filtro="Frijol")
        self.assertEqual([t["id_product"] for t in a3["tareas"]], ["2"])
        with self.assertRaises(ValueError):
            self.estado.alta("Pepe", "Bara", productos=["999999"])
        with self.assertRaises(ValueError):
            self.estado.alta("Pepe", "Bara", filtro="NoExisteEnCatalogo")

    def test_agregar_tarea_idempotente_y_errores(self):
        cod = self.estado.alta("Ana Prueba", "Soriana", productos=["1"])["codigo"]
        t1 = self.estado.agregar_tarea(cod, "2")
        self.assertEqual(t1["id_product"], "2")
        self.assertEqual(t1["estado"], "pendiente")
        # Simula avance y re-agrega -> idempotente
        self.estado._t(cod, "2")["intentos"] = 1
        t2 = self.estado.agregar_tarea(cod, "2")
        self.assertEqual(t2["intentos"], 1)
        self.assertEqual(len(self.estado.perfil(cod)["tareas"]), 2)
        recargado = campo.Estado(Path(self.tmp.name), CATALOGO)
        self.assertEqual(len(recargado.perfil(cod)["tareas"]), 2)
        with self.assertRaises(KeyError):
            self.estado.agregar_tarea("000000", "1")
        with self.assertRaises(KeyError):
            self.estado.agregar_tarea(cod, "999999")

    def test_preparar_captura_no_quema_intento_con_jpeg_invalido(self):
        cod = self._alta(1)
        idp = self.estado.perfil(cod)["tareas"][0]["id_product"]
        self.estado.guardar_fachada(cod, campo._jpg(JPG))
        with self.assertRaises(ValueError):
            campo._preparar_captura(self.estado, cod, idp, "data:text/plain;base64,AAAA", JPG, "40")
        self.assertEqual(self.estado._t(cod, idp)["intentos"], 0)
        with self.assertRaises(ValueError):
            campo._preparar_captura(self.estado, cod, idp, JPG, "data:text/plain;base64,AAAA", "40")
        self.assertEqual(self.estado._t(cod, idp)["intentos"], 0)
        # Ningún archivo huérfano de captura en fotos/
        fotos = [f.name for f in (Path(self.tmp.name) / "fotos").iterdir()]
        self.assertFalse(any("CAMPO-" in f for f in fotos))
        # Captura válida posterior inicia en intento 1
        r = campo.capturar(self.estado, motor_falso([("aprobada", None)]), cod, idp, JPG, JPG, "41.5")
        self.assertEqual((r["estado"], r["intento"]), ("aprobada", 1))

    def test_evaluar_y_guardar_con_precio_detectado_none(self):
        cod = self._alta(1)
        idp = self.estado.perfil(cod)["tareas"][0]["id_product"]
        self.estado.guardar_fachada(cod, campo._jpg(JPG))
        motor = motor_falso([("aprobada", None)], precio_detectado=None)
        r = campo.capturar(self.estado, motor, cod, idp, JPG, JPG, "40.0")
        self.assertEqual(r["estado"], "aprobada")
        self.assertTrue(r["mensaje"])
        self.assertNotIn("None", r["mensaje"])
        self.assertIsNone(r["precio_detectado"])
        csv_txt = campo.precios_csv(self.estado)
        self.assertEqual(csv_txt.count("\n"), 1)  # solo encabezado porque precio_detectado es None

    def test_alta_deduplica_y_rechaza_nombre_null(self):
        a = self.estado.alta("Luis", "Bara", productos=["1", "1", {"id_product": "2"}, {"id_product": "2"}])
        self.assertEqual([t["id_product"] for t in a["tareas"]], ["1", "2"])
        with self.assertRaises(ValueError):
            self.estado.alta(None, "Bara", 1)
        with self.assertRaises(ValueError):
            self.estado.crear_producto(None)

    def test_capturar_sincrono_concurrencia_y_limpieza_huerfano(self):
        cod = self._alta(1)
        idp = self.estado.perfil(cod)["tareas"][0]["id_product"]
        self.estado.guardar_fachada(cod, campo._jpg(JPG))

        # Rollback al fallar la segunda escritura: no deja archivo huérfano ni quema intento
        orig_write = Path.write_bytes
        llamadas = {"n": 0}

        def falla_segunda(self_path, data):
            llamadas["n"] += 1
            if llamadas["n"] == 2:
                raise OSError("disco lleno")
            return orig_write(self_path, data)

        with mock.patch.object(Path, "write_bytes", falla_segunda):
            with self.assertRaises(OSError):
                campo._preparar_captura(self.estado, cod, idp, JPG, JPG, "40.0")
        self.assertEqual(self.estado._t(cod, idp)["intentos"], 0)
        self.assertEqual(self.estado._t(cod, idp)["estado"], "pendiente")
        self.assertFalse(any("CAMPO-" in f.name for f in (Path(self.tmp.name) / "fotos").iterdir()))

        # Carrera concurrente en capturar() síncrono -> solo 1 entra al motor
        iniciado = threading.Event()
        liberar = threading.Event()
        barrera = threading.Barrier(2)
        motor_calls = {"n": 0}

        def motor_lento(captura, dir_datos):
            motor_calls["n"] += 1
            iniciado.set()
            liberar.wait(timeout=5)
            return Resultado(capture_id=captura.capture_id, decision="aprobada", confidence_score=0.95,
                             reason_code=None, validaciones=Validaciones(), precio_detectado=41.5,
                             explicacion="ok")

        resultados = []
        errores = []

        def worker():
            barrera.wait(timeout=5)
            try:
                resultados.append(campo.capturar(self.estado, motor_lento, cod, idp, JPG, JPG, "41.5"))
            except Exception as e:
                errores.append(e)

        h1 = threading.Thread(target=worker)
        h2 = threading.Thread(target=worker)
        h1.start()
        h2.start()
        self.assertTrue(iniciado.wait(timeout=3))
        time.sleep(0.05)
        liberar.set()
        h1.join(timeout=5)
        h2.join(timeout=5)
        self.assertEqual(len(resultados), 1)
        self.assertEqual(len(errores), 1)
        self.assertIsInstance(errores[0], ValueError)
        self.assertEqual(motor_calls["n"], 1)
        self.assertEqual(self.estado._t(cod, idp)["intentos"], 1)


class CampoHttpTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.estado = campo.Estado(Path(self.tmp.name), CATALOGO_EXT)

    def tearDown(self):
        self.tmp.cleanup()

    def test_supervisor_catalogo_producto_agregar_tarea_y_guardia_local(self):
        with _con_servidor(self.estado, motor_falso([])) as (_, _, req):
            st, prod_res = req("POST", "/api/supervisor/producto", {
                "nombre": "Boost Energy", "barcode": "7501055300010", "contenido": "473 ml", "precio_referencia": 25
            })
            self.assertEqual(st, 200)
            self.assertTrue(prod_res["ok"])
            pid = prod_res["producto"]["id_product"]

            st, cat = req("GET", "/api/supervisor/catalogo?q=Frijol")
            self.assertEqual(st, 200)
            self.assertEqual([p["id_product"] for p in cat["productos"]], ["2"])

            st, cat_custom = req("GET", "/api/supervisor/catalogo?q=" + urllib.parse.quote("Boost Energy"))
            self.assertEqual(st, 200)
            self.assertEqual([p["id_product"] for p in cat_custom["productos"]], [pid])

            st, alta = req("POST", "/api/supervisor/alta", {"nombre": "Carlos", "tienda": "Soriana", "productos": ["1"]})
            self.assertEqual(st, 200)
            cod = alta["codigo"]

            st, tarea_res = req("POST", "/api/supervisor/agregar_tarea", {"codigo": cod, "id_product": pid})
            self.assertEqual(st, 200)
            self.assertTrue(tarea_res["ok"])
            self.assertEqual(tarea_res["tarea"]["id_product"], pid)

            # Simula cliente remoto -> rutas de supervisor devuelven 403
            with mock.patch.object(campo.Manejador, "_local", return_value=False):
                self.assertEqual(req("GET", "/api/supervisor/catalogo")[0], 403)
                self.assertEqual(req("GET", "/api/supervisor/estado")[0], 403)
                self.assertEqual(req("POST", "/api/supervisor/producto", {"nombre": "X"})[0], 403)
                self.assertEqual(req("POST", "/api/supervisor/alta", {"nombre": "X", "tienda": "Bara"})[0], 403)
                self.assertEqual(req("POST", "/api/supervisor/agregar_tarea", {"codigo": cod, "id_product": "2"})[0], 403)
                self.assertEqual(req("POST", "/api/supervisor/resolver_reporte", {"index": 0})[0], 403)

    def test_capturista_buscar_registrar_agregar_propio_y_omitir(self):
        cod = self.estado.alta("Elena", "Chedraui", productos=["1"])["codigo"]
        with _con_servidor(self.estado, motor_falso([])) as (_, _, req):
            with mock.patch.object(campo.Manejador, "_local", return_value=False):
                # Producto "1" ya asignado -> tarea_existente truthy
                st, r1 = req("POST", "/api/buscar_codigo", {"codigo": cod, "barcode": "07500000000011"})
                self.assertEqual(st, 200)
                self.assertTrue(r1["encontrado"])
                self.assertEqual(r1["tarea_existente"]["id_product"], "1")

                # Producto "3" no asignado -> tarea_existente falsy (None)
                st, r2 = req("POST", "/api/buscar_codigo", {"codigo": cod, "barcode": "750000000035"})
                self.assertEqual(st, 200)
                self.assertTrue(r2["encontrado"])
                self.assertFalse(r2["tarea_existente"])
                self.assertEqual(r2["producto"]["id_product"], "3")

                # Agregar producto propio existente -> 200 e idempotente
                st, ag = req("POST", "/api/agregar_producto_propio", {"codigo": cod, "id_product": "3"})
                self.assertEqual(st, 200)
                self.assertEqual((ag["ok"], ag["tarea"]["id_product"]), (True, "3"))
                st, ag2 = req("POST", "/api/agregar_producto_propio", {"codigo": cod, "id_product": "3"})
                self.assertEqual((st, ag2["ok"]), (200, True))
                self.assertEqual(req("POST", "/api/agregar_producto_propio", {"codigo": cod, "id_product": "999999"})[0], 404)
                self.assertEqual(req("POST", "/api/agregar_producto_propio", {"codigo": "000000", "id_product": "3"})[0], 404)

                # Registrar producto nuevo desde celular -> crea + asigna tarea
                st, reg = req("POST", "/api/registrar_producto", {
                    "codigo": cod, "nombre": "Agua 3B 500 ml", "barcode": "7509999000111",
                    "contenido": "500 ml", "precio_referencia": 10
                })
                self.assertEqual(st, 200)
                self.assertTrue(reg["ok"])
                self.assertEqual(reg["tarea"]["id_product"], reg["producto"]["id_product"])

                # Omitir devuelve ok + estado="omitida"
                st, om = req("POST", "/api/omitir", {
                    "codigo": cod, "id_product": "3", "motivo": campo.MOTIVOS_OMITIR[0]
                })
                self.assertEqual((st, om), (200, {"ok": True, "estado": "omitida"}))

    def test_reportar_codigo_y_resolver_reporte(self):
        cod = self.estado.alta("Hugo", "Walmart", productos=["1", "2"])["codigo"]
        with _con_servidor(self.estado, motor_falso([])) as (_, _, req):
            self.assertEqual(req("POST", "/api/reportar_codigo", {"codigo": cod, "id_product": "1", "motivo": "   "})[0], 400)
            self.assertEqual(req("POST", "/api/reportar_codigo", {"codigo": "000000", "id_product": "1", "motivo": "mal"})[0], 404)
            self.assertEqual(req("POST", "/api/reportar_codigo", {"codigo": cod, "id_product": "999999", "motivo": "mal"})[0], 404)

            st, r1 = req("POST", "/api/reportar_codigo", {
                "codigo": cod, "id_product": "1", "barcode": "7500000000011", "motivo": "Código roto en etiqueta"
            })
            self.assertEqual(st, 200)
            rid = r1["reporte"]["id_reporte"]
            self.assertFalse(r1["reporte"]["resuelto"])

            st, r2 = req("POST", "/api/reportar_codigo", {
                "codigo": cod, "barcode": "7501111222233", "motivo": "No aparece en catálogo"
            })
            self.assertEqual(st, 200)

            st, est_sup = req("GET", "/api/supervisor/estado")
            self.assertEqual(st, 200)
            self.assertEqual(est_sup["kpis"]["reportes_pendientes"], 2)

            # Resuelve primero por id_reporte y segundo por index=1
            st, res1 = req("POST", "/api/supervisor/resolver_reporte", {
                "id_reporte": rid, "nuevo_barcode": "7500000000099", "nota": "Corregido"
            })
            self.assertEqual((st, res1["ok"], res1["reporte"]["resuelto"]), (200, True, True))
            st, res2 = req("POST", "/api/supervisor/resolver_reporte", {"index": 1})
            self.assertEqual((st, res2["ok"], res2["reporte"]["resuelto"]), (200, True, True))

            self.assertEqual(req("POST", "/api/supervisor/resolver_reporte", {"id_reporte": "noexiste"})[0], 404)
            self.assertEqual(req("POST", "/api/supervisor/resolver_reporte", {"index": 99})[0], 404)
            self.assertEqual(req("POST", "/api/supervisor/resolver_reporte", {})[0], 400)

        recargado = campo.Estado(Path(self.tmp.name), CATALOGO_EXT)
        self.assertTrue(all(r["resuelto"] for r in recargado.d["reportes_codigo"]))
        self.assertEqual(recargado._t(cod, "1")["estado"], "pendiente")
        # Corrección de código sobre producto del catálogo base persiste tras reinicio sin mutar CATALOGO_EXT
        self.assertEqual(recargado.catalogo["1"]["product_barcode"], "7500000000099")
        self.assertEqual(CATALOGO_EXT[0]["product_barcode"], "7500000000011")

    def test_resolver_reporte_atomicidad_en_400(self):
        cod = self.estado.alta("Hugo", "Walmart", productos=["1"])["codigo"]
        rep = self.estado.reportar_codigo(cod, "1", "7500000000011", "Etiqueta dañada")
        rid = rep["id_reporte"]
        with _con_servidor(self.estado, motor_falso([])) as (_, _, req):
            st, _ = req("POST", "/api/supervisor/resolver_reporte", {
                "id_reporte": rid, "nuevo_barcode": "7509999999999", "estado_tarea": "estado_invalido"
            })
            self.assertEqual(st, 400)
            st_est, sup = req("GET", "/api/supervisor/estado")
            self.assertEqual(st_est, 200)
            self.assertFalse(sup["reportes_codigo"][0]["resuelto"])
            self.assertNotIn("barcode_corregido", sup["reportes_codigo"][0])
            self.assertEqual(self.estado.catalogo["1"]["product_barcode"], "7500000000011")
            self.assertEqual(self.estado._t(cod, "1")["estado"], "revision")

    def test_hardening_http_no_dict_nan_y_post_remoto_vacio(self):
        cod = self.estado.alta("Rita", "Bara", productos=["1"])["codigo"]
        self.estado.guardar_fachada(cod, campo._jpg(JPG))
        with _con_servidor(self.estado, motor_falso([])) as (base, _, req):
            # Cuerpo JSON no-objeto ([1, 2, 3]) devuelve 400 (nunca 500)
            st_arr, err_arr = req("POST", "/api/vincular", [1, 2, 3])
            self.assertEqual(st_arr, 400)
            self.assertIn("error", err_arr)

            # nombre null -> 400 (nunca "None")
            self.assertEqual(req("POST", "/api/supervisor/producto", {"nombre": None})[0], 400)
            self.assertEqual(req("POST", "/api/supervisor/alta", {"nombre": None, "tienda": "Bara"})[0], 400)

            # NaN / Infinity rechazados con 400 en precios y ubicación, y estado sigue JSON válido
            self.assertEqual(req("POST", "/api/supervisor/producto", {"nombre": "Agua", "precio_referencia": "NaN"})[0], 400)
            self.assertEqual(req("POST", "/api/ubicacion", {"codigo": cod, "lat": "NaN", "lon": -99.1})[0], 400)
            self.assertEqual(req("POST", "/api/captura", {
                "codigo": cod, "id_product": "1", "foto_producto": JPG, "foto_etiqueta": JPG, "precio": "NaN"
            })[0], 400)
            self.assertEqual(self.estado._t(cod, "1")["intentos"], 0)
            st_sup, raw_sup = req("GET", "/api/supervisor/estado", parsear_json=False)
            self.assertEqual(st_sup, 200)
            json.loads(raw_sup, parse_constant=lambda c: (_ for _ in ()).throw(ValueError(c)))

            # POST remoto vacío a /api/supervisor/* devuelve 403 (antes de leer/validar cuerpo)
            with mock.patch.object(campo.Manejador, "_local", return_value=False):
                req_vacio = urllib.request.Request(base + "/api/supervisor/alta", data=b"", method="POST")
                with self.assertRaises(urllib.error.HTTPError) as ctx:
                    urllib.request.urlopen(req_vacio, timeout=5)
                self.assertEqual(ctx.exception.code, 403)
                ctx.exception.close()

    def test_capturar_async_con_evento_y_estado_polling(self):
        cod = self.estado.alta("Gaby", "Bara", productos=["1", "2"])["codigo"]
        self.estado.guardar_fachada(cod, campo._jpg(JPG))
        iniciado = threading.Event()
        liberar = threading.Event()

        def motor_bloqueante(captura, dir_datos):
            if captura.id_product == 1:
                iniciado.set()
                liberar.wait(timeout=5)
            return Resultado(capture_id=captura.capture_id, decision="aprobada", confidence_score=0.95,
                             reason_code=None, validaciones=Validaciones(), precio_detectado=39.5,
                             explicacion="ok")

        with _con_servidor(self.estado, motor_bloqueante) as (_, _, req):
            try:
                st, r = req("POST", "/api/captura", {
                    "codigo": cod, "id_product": "1", "foto_producto": JPG, "foto_etiqueta": JPG,
                    "precio": "39.5", "barcode": "7500000000011", "async": True
                })
                self.assertEqual((st, r["estado"], r["intento"]), (200, "procesando", 1))
                self.assertTrue(iniciado.wait(timeout=2))

                with mock.patch.object(campo.Manejador, "_local", return_value=False):
                    # GET /api/estado accesible para capturista sin mutar vinculado
                    st_est, est_cap = req("GET", f"/api/estado?codigo={cod}")
                    self.assertEqual(st_est, 200)
                    t1 = next(t for t in est_cap["tareas"] if t["id_product"] == "1")
                    self.assertEqual(t1["estado"], "procesando")
                    self.assertIsNone(self.estado._c(cod)["vinculado"])

                    # Envío duplicado en mismo producto bloqueado sin quemar intento
                    st_dup, _ = req("POST", "/api/captura", {
                        "codigo": cod, "id_product": "1", "foto_producto": JPG, "foto_etiqueta": JPG,
                        "precio": "39.5", "async": True
                    })
                    self.assertEqual(st_dup, 400)
                    self.assertEqual(self.estado._t(cod, "1")["intentos"], 1)

                    # Segundo producto sí puede enviarse en paralelo
                    st2, r2 = req("POST", "/api/captura", {
                        "codigo": cod, "id_product": "2", "foto_producto": JPG, "foto_etiqueta": JPG,
                        "precio": "15.0", "async": False
                    })
                    self.assertEqual((st2, r2["estado"]), (200, "aprobada"))

                liberar.set()
                final = None
                for _ in range(100):
                    _, est_cap = req("GET", f"/api/estado?codigo={cod}")
                    t1 = next(t for t in est_cap["tareas"] if t["id_product"] == "1")
                    if t1["estado"] != "procesando":
                        final = est_cap
                        break
                    time.sleep(0.02)
                self.assertIsNotNone(final)
                self.assertEqual(next(t for t in final["tareas"] if t["id_product"] == "1")["estado"], "aprobada")
                self.assertEqual(len(final["recientes"]), 2)

                # GET /api/estado inválido / vacío -> 404
                self.assertEqual(req("GET", "/api/estado?codigo=000000")[0], 404)
                self.assertEqual(req("GET", "/api/estado")[0], 404)

                # GET /api/supervisor/estado incluye campos completos
                st_sup, sup = req("GET", "/api/supervisor/estado")
                self.assertEqual(st_sup, 200)
                for clave in ("url", "urls", "catalogo_count", "cadenas", "motivos_omitir", "kpis",
                              "comparador", "motivos_rechazo", "reportes_codigo", "capturistas", "capturas"):
                    self.assertIn(clave, sup)
                self.assertEqual(sup["catalogo_count"], len(CATALOGO_EXT))
                self.assertTrue(all("precio_tecleado" in cap and "barcode" in cap for cap in sup["capturas"]))
            finally:
                liberar.set()

    def test_leer_codigo_ean13_y_errores(self):
        cod = self.estado.alta("Nora", "Soriana", productos=["1"])["codigo"]
        ean_jpg = _ean13_jpg("7501031311309")
        blanco_jpg = _jpg_blanco()
        with _con_servidor(self.estado, motor_falso([])) as (_, _, req):
            st, res = req("POST", "/api/leer_codigo", {"codigo": cod, "foto": ean_jpg})
            self.assertEqual((st, res["ok"], res["barcode"]), (200, True, "7501031311309"))

            st_b, res_b = req("POST", "/api/leer_codigo", {"codigo": cod, "foto": blanco_jpg})
            self.assertEqual((st_b, res_b), (200, {"ok": True, "barcode": None}))

            self.assertEqual(req("POST", "/api/leer_codigo", {"codigo": "000000", "foto": ean_jpg})[0], 404)
            self.assertEqual(req("POST", "/api/leer_codigo", {"codigo": cod, "foto": "no-es-imagen"})[0], 400)

            with mock.patch("zxingcpp.read_barcodes", side_effect=RuntimeError("fallo")):
                st_m, res_m = req("POST", "/api/leer_codigo", {"codigo": cod, "foto": ean_jpg})
                self.assertEqual((st_m, res_m), (200, {"ok": True, "barcode": None}))

    def test_fuente_montserrat_woff2(self):
        esperado = campo._RUTA_FUENTE.read_bytes()
        with _con_servidor(self.estado, motor_falso([])) as (_, _, req):
            with mock.patch.object(campo.Manejador, "_local", return_value=False):
                st, hdrs, raw = req("GET", "/fonts/montserrat.woff2", parsear_json=False, con_headers=True)
                self.assertEqual(st, 200)
                self.assertTrue(hdrs.get("Content-Type", "").startswith("font/woff2"))
                self.assertEqual(raw, esperado)

            with mock.patch.object(campo, "_RUTA_FUENTE", Path(self.tmp.name) / "no-existe.woff2"):
                st_404, _ = req("GET", "/fonts/montserrat.woff2", parsear_json=False)
                self.assertEqual(st_404, 404)

    def test_ui_tarima_y_contratos_m2(self):
        with _con_servidor(self.estado, motor_falso([])) as (_, _, req):
            st_c, raw_c = req("GET", "/", parsear_json=False)
            st_s, raw_s = req("GET", "/supervisor", parsear_json=False)
            self.assertEqual((st_c, st_s), (200, 200))
            with mock.patch.object(campo.Manejador, "_local", return_value=False):
                self.assertEqual(req("GET", "/supervisor", parsear_json=False)[0], 403)

        html_cap = raw_c.decode("utf-8")
        html_sup = raw_s.decode("utf-8")
        emoji_re = re.compile(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]")
        for ruta, html in (("/", html_cap), ("/supervisor", html_sup)):
            self.assertIn("@font-face", html, ruta)
            self.assertIn("/fonts/montserrat.woff2", html, ruta)
            self.assertIn("Prototipo para Tiendas 3B", html, ruta)
            self.assertIn("#E31B23", html, ruta)
            self.assertIn("tabular-nums", html, ruta)
            self.assertIn('class="cifra"', html, ruta)
            self.assertIn("border:1px solid", html, ruta)
            self.assertNotIn("border-left", html, ruta)
            self.assertNotIn("fonts.googleapis.com", html.lower(), ruta)
            self.assertIsNone(emoji_re.search(html), ruta)
            self.assertIn('role', html, ruta)

        for marcador in (
            "Vincula tu celular", "Paso 1", "getUserMedia", "BarcodeDetector",
            "/api/leer_codigo", "/api/buscar_codigo", "/api/registrar_producto",
            "/api/agregar_producto_propio", "/api/reportar_codigo", "/api/estado",
            "async:true", "Escanear producto nuevo",
        ):
            self.assertIn(marcador, html_cap)

        for marcador in (
            "/api/supervisor/catalogo", "/api/supervisor/producto", "/api/supervisor/agregar_tarea",
            "/api/supervisor/resolver_reporte", "/api/supervisor/precios.csv",
            "d.urls", "precio_tecleado", "fmtNum", "<svg",
        ):
            self.assertIn(marcador, html_sup)
        self.assertNotIn("precio_detectado.toFixed", html_sup)
        self.assertNotIn("precio_referencia.toFixed", html_sup)

        if shutil.which("node"):
            for nombre, html in (("CAPTURISTA", html_cap), ("SUPERVISOR", html_sup)):
                m = re.search(r"<script>(.*)</script>", html, re.S)
                self.assertIsNotNone(m, nombre)
                res = subprocess.run(
                    ["node", "-e", "new Function(require('fs').readFileSync(0, 'utf8'))"],
                    input=m.group(1), text=True, capture_output=True, timeout=10,
                )
                self.assertEqual(res.returncode, 0, f"{nombre} JS error: {res.stderr}")


class CampoRuntimeTest(unittest.TestCase):
    def test_guardia_local_ips(self):
        for ip in ("127.0.0.1", "::1", "::ffff:127.0.0.1"):
            self.assertTrue(campo.Manejador._local(SimpleNamespace(client_address=(ip, 1234))))
        for ip in ("192.168.1.25", "172.31.12.57"):
            self.assertFalse(campo.Manejador._local(SimpleNamespace(client_address=(ip, 1234))))

    def test_ips_locales_prioriza_lan_hotspot_y_excluye_virtuales(self):
        fake_info = [
            (socket.AF_INET, socket.SOCK_STREAM, 0, "", ("192.168.56.1", 0)),
            (socket.AF_INET, socket.SOCK_STREAM, 0, "", ("169.254.10.2", 0)),
            (socket.AF_INET, socket.SOCK_STREAM, 0, "", ("192.168.43.15", 0)),
            (socket.AF_INET, socket.SOCK_STREAM, 0, "", ("172.20.10.2", 0)),
            (socket.AF_INET, socket.SOCK_STREAM, 0, "", ("172.31.12.57", 0)),
        ]
        with mock.patch.object(campo, "ip_local", return_value="192.168.43.15"), \
             mock.patch("socket.getaddrinfo", return_value=fake_info):
            ips = campo.ips_locales()
        self.assertEqual(ips[0], "192.168.43.15")
        self.assertIn("172.20.10.2", ips)
        self.assertIn("172.31.12.57", ips)
        self.assertNotIn("192.168.56.1", ips)
        self.assertNotIn("169.254.10.2", ips)

        with mock.patch.object(campo, "ip_local", return_value="127.0.0.1"), \
             mock.patch("socket.getaddrinfo", side_effect=OSError("sin red")):
            self.assertEqual(campo.ips_locales(), ["127.0.0.1"])

        # Hotspot de Windows (Microsoft Wi-Fi Direct Virtual Adapter / 192.168.137.1) NUNCA se clasifica como virtual
        self.assertFalse(campo._es_adaptador_virtual(
            "192.168.137.1", "Local Area Connection* 12", "Microsoft Wi-Fi Direct Virtual Adapter #2", True
        ))
        self.assertTrue(campo._es_adaptador_virtual(
            "192.168.56.1", "Ethernet 4", "VirtualBox Host-Only Ethernet Adapter", True
        ))
        fake_meta = {
            "192.168.56.1": {"ip": "192.168.56.1", "alias": "Ethernet 4",
                             "desc": "VirtualBox Host-Only Ethernet Adapter", "virtual": True,
                             "status": "Up", "has_gw": False},
            "192.168.137.1": {"ip": "192.168.137.1", "alias": "Conexión de área local* 1",
                              "desc": "Microsoft Wi-Fi Direct Virtual Adapter", "virtual": True,
                              "status": "Up", "has_gw": False},
            "172.31.12.57": {"ip": "172.31.12.57", "alias": "Wi-Fi",
                             "desc": "Intel(R) Wi-Fi 6 AX201", "virtual": False,
                             "status": "Up", "has_gw": True},
        }
        with mock.patch.object(campo, "ip_local", return_value="172.31.12.57"), \
             mock.patch.object(campo, "_adaptadores_windows", return_value=fake_meta), \
             mock.patch.object(campo.socket, "getaddrinfo", lambda *a, **kw: []):
            prim, virt = campo._recolectar_ips()
        self.assertIn("172.31.12.57", prim)
        self.assertIn("192.168.137.1", prim)
        self.assertEqual(virt, ["192.168.56.1"])

    def test_certificado_regenera_si_llave_corrupta(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            par1 = campo.certificado(d, ["127.0.0.1"])
            self.assertIsNotNone(par1)
            llave_orig = par1[1].read_bytes()
            par1[1].write_bytes(b"--- CORRUPTED KEY PEM ---")
            par2 = campo.certificado(d, ["127.0.0.1"])
            self.assertIsNotNone(par2)
            self.assertNotEqual(par2[1].read_bytes(), b"--- CORRUPTED KEY PEM ---")
            self.assertNotEqual(par2[1].read_bytes(), llave_orig)
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ctx.load_cert_chain(str(par2[0]), str(par2[1]))

    def test_crear_servidor_puerto_ocupado_falla_en_windows(self):
        if os.name != "nt":
            self.skipTest("Solo aplica a SO_REUSEADDR de Windows")
        with tempfile.TemporaryDirectory() as tmp:
            est = campo.Estado(Path(tmp), CATALOGO)
            srv1 = campo.crear_servidor(est, motor_falso([]), host="127.0.0.1", puerto=0)
            puerto = srv1.server_address[1]
            try:
                with self.assertRaises(OSError):
                    campo.crear_servidor(est, motor_falso([]), host="127.0.0.1", puerto=puerto)
            finally:
                srv1.server_close()

    def test_certificado_y_handshake_tls(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            par1 = campo.certificado(d, ["127.0.0.1", "192.168.43.15"])
            self.assertIsNotNone(par1)
            cert_bytes_1 = par1[0].read_bytes()
            # Misma lista de IPs -> reutiliza certificado existente
            par2 = campo.certificado(d, ["192.168.43.15", "127.0.0.1"])
            self.assertEqual(par2[0].read_bytes(), cert_bytes_1)
            # Lista distinta -> regenera
            par3 = campo.certificado(d, ["127.0.0.1", "172.31.12.57"])
            self.assertNotEqual(par3[0].read_bytes(), cert_bytes_1)

            est = campo.Estado(d, CATALOGO)
            srv = campo.crear_servidor(est, motor_falso([]), host="127.0.0.1", puerto=0)
            ctx_srv = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ctx_srv.load_cert_chain(str(par3[0]), str(par3[1]))
            srv.socket = ctx_srv.wrap_socket(srv.socket, server_side=True)
            hilo = threading.Thread(target=srv.serve_forever, daemon=True)
            hilo.start()
            try:
                ctx_cli = ssl._create_unverified_context()
                url = f"https://127.0.0.1:{srv.server_address[1]}/"
                with urllib.request.urlopen(url, context=ctx_cli, timeout=5) as resp:
                    self.assertEqual(resp.status, 200)
                    self.assertIn("Vincula tu celular", resp.read().decode("utf-8"))
            finally:
                srv.shutdown()
                srv.server_close()
                hilo.join(timeout=2)

    def test_main_sin_modelo_vs_aviso_foundry_api_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            # Sin modelo con 0 API keys arranca y sale 0 limpiamente
            buf_sin = io.StringIO()
            with mock.patch.dict(os.environ, {}, clear=True), \
                 mock.patch.object(campo.ThreadingHTTPServer, "serve_forever", side_effect=KeyboardInterrupt), \
                 contextlib.redirect_stdout(buf_sin):
                rc = campo.main(["--catalogo", "no-existe.csv", "--salida", str(d / "s1"),
                                 "--puerto", "0", "--env", str(d / "no.env"), "--sin-modelo", "--http"])
            self.assertEqual(rc, 0)
            self.assertNotIn("FOUNDRY_API_KEY", buf_sin.getvalue())

            # Sin --sin-modelo y sin FOUNDRY_API_KEY imprime aviso claro
            buf_con = io.StringIO()
            with mock.patch.dict(os.environ, {}, clear=True), \
                 mock.patch.object(campo.ThreadingHTTPServer, "serve_forever", side_effect=KeyboardInterrupt), \
                 contextlib.redirect_stdout(buf_con):
                rc2 = campo.main(["--catalogo", "no-existe.csv", "--salida", str(d / "s2"),
                                  "--puerto", "0", "--env", str(d / "no.env"), "--http"])
            self.assertEqual(rc2, 0)
            out2 = buf_con.getvalue()
            self.assertIn("FOUNDRY_API_KEY", out2)
            self.assertIn("SIN_LECTURA", out2)

            # Fallback env file sí carga FOUNDRY_API_KEY
            env_prim = d / "prim.env"
            env_sec = d / "sec.env"
            env_prim.write_text("OTRA_LLAVE=1\nFOUNDRY_API_KEY=\n", encoding="utf-8")
            env_sec.write_text("FOUNDRY_API_KEY=llave-de-prueba\n", encoding="utf-8")
            with mock.patch.dict(os.environ, {}, clear=True):
                campo.cargar_env([str(env_prim), str(env_sec)], ruta_explicita=str(env_prim))
                self.assertEqual(os.environ.get("FOUNDRY_API_KEY"), "llave-de-prueba")

            # correr.procesar sin modelo con 0 API keys
            from ml.validat3b.contrato import Captura
            (d / "fachada.jpg").write_bytes(b"\xff\xd8\xff\xe0" + b"0" * 32)
            (d / "prod.jpg").write_bytes(b"\xff\xd8\xff\xe0" + b"0" * 32)
            (d / "etq.jpg").write_bytes(b"\xff\xd8\xff\xe0" + b"0" * 32)
            cap = Captura(
                capture_id="TEST-0", capture_store_name="Soriana", capture_date="2026-11-21 12:00:00",
                capture_barcode="7500000000011", capture_price=40.0, capture_brand=None,
                id_product=1, product_name="Aceite Prueba 900 ml", product_barcode="7500000000011",
                product_price=40.0, min_product_price=30.0, max_product_price=50.0,
                unit_product="mililitro", unit_quantity_product=900.0, product_group="g", product_line="aceite",
                facade_file="fachada.jpg", product_file="prod.jpg", shelf_file="etq.jpg",
            )
            with mock.patch.dict(os.environ, {}, clear=True):
                _, res = correr.procesar(cap, d, None, False)
            self.assertEqual(res.decision, "revision_manual")


if __name__ == "__main__":
    unittest.main()
