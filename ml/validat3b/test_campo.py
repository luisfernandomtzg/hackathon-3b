"""Pruebas del servidor de campo. Datos inventados; no usa datos de 3B ni el endpoint."""
import base64
import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from ml.validat3b import campo
from ml.validat3b.contrato import RC_LEJANA, Resultado, Validaciones

CATALOGO = [{"id_product": "1", "product_name": "Aceite Prueba 900 ml", "product_barcode": "7500000000011",
             "product_price": "40.0", "min_product_price": "30.0", "max_product_price": "50.0",
             "unit_product": "mililitro", "unit_quantity_product": "900.0", "product_group": "g", "product_line": "aceite"},
            {"id_product": "2", "product_name": "Frijol Prueba 400 g", "product_barcode": "7500000000028",
             "product_price": "15.0", "min_product_price": "10.0", "max_product_price": "20.0",
             "unit_product": "gramo", "unit_quantity_product": "400.0", "product_group": "g", "product_line": "frijol"}]
JPG = "data:image/jpeg;base64," + base64.b64encode(b"\xff\xd8\xff\xe0" + b"0" * 64).decode()


def motor_falso(decisiones):
    cola = list(decisiones)

    def _m(captura, dir_datos):
        dec, rc = cola.pop(0)
        return Resultado(capture_id=captura.capture_id, decision=dec, confidence_score=0.9, reason_code=rc,
                         validaciones=Validaciones(), precio_detectado=41.5, explicacion="explicación de prueba")
    return _m


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


if __name__ == "__main__":
    unittest.main()
