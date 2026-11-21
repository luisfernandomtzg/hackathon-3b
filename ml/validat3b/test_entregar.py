"""Pruebas de entregar. Datos e imágenes inventados; no usa datos de 3B."""
import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from PIL import Image

from ml.validat3b import correr, entregar
from ml.validat3b.contrato import Resultado, Validaciones

CAMPOS = ["capture_id", "capture_store_name", "capture_date", "capture_barcode", "capture_price", "capture_brand",
          "id_product", "product_name", "product_barcode", "facade_file", "product_file", "shelf_file"]


def res(cid, rc=None, decision="revision_manual"):
    return Resultado(capture_id=cid, decision=decision, confidence_score=0.5, reason_code=rc,
                     validaciones=Validaciones(), explicacion="x").model_dump(mode="json")


def fila(cid):
    return {"capture_id": cid, "capture_store_name": "T", "capture_date": "2026-11-21", "capture_barcode": "0750100",
            "capture_price": "10", "capture_brand": "M", "id_product": "1", "product_name": "P",
            "product_barcode": "0750100", "facade_file": f"imagenes/{cid}_facade.jpg",
            "product_file": f"imagenes/{cid}_product.jpg", "shelf_file": f"imagenes/{cid}_shelf.jpg"}


class PruebasValidar(unittest.TestCase):
    def test_ok(self):
        self.assertEqual(entregar.validar(["A", "B"], [res("A"), res("B")], None), [])

    def test_faltante_falla(self):
        self.assertTrue(any("falta" in p for p in entregar.validar(["A", "B"], [res("A")], None)))

    def test_duplicado_falla(self):
        self.assertTrue(any("2 veces" in p for p in entregar.validar(["A"], [res("A"), res("A")], None)))

    def test_codigo_fuera_del_mapa_falla(self):
        self.assertTrue(entregar.validar(["A"], [res("A", "CAPTURA_BORROSA")], {"OFI_1"}))
        self.assertEqual(entregar.validar(["A"], [res("A", "OFI_1"), ], {"OFI_1"}), [])

    def test_resultado_invalido_falla(self):
        malo = res("A")
        malo["confidence_score"] = 7
        self.assertTrue(any("contrato" in p for p in entregar.validar(["A"], [malo], None)))


class PruebasEntrega(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        t = Path(self.tmp.name)
        # estructura distinta a la de desarrollo: lote/datos.../capturas.csv y lote/fotos/imagenes/*.jpg
        (t / "set" / "tabla").mkdir(parents=True)
        (t / "set" / "fotos" / "imagenes").mkdir(parents=True)
        filas = [fila("CAP-1"), fila("CAP-2")]  # sin decision_esperada ni motivo_rechazo
        with open(t / "set" / "tabla" / "capturas.csv", "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=CAMPOS)
            w.writeheader()
            w.writerows(filas)
        for cid in ("CAP-1",):  # CAP-2 queda sin ninguna foto
            for s in ("facade", "product", "shelf"):
                Image.new("RGB", (200, 200), (90, 90, 90)).save(t / "set" / "fotos" / "imagenes" / f"{cid}_{s}.jpg")
        self.datos, self.out = t / "set", t / "entrega"

    def tearDown(self):
        self.tmp.cleanup()

    def entregar(self):
        return entregar.main(["--datos", str(self.datos), "--salida", str(self.out), "--sin-modelo"])

    def test_localiza_y_entrega_sin_etiquetas_y_sin_foto_a_revision(self):
        self.assertEqual(self.entregar(), 0)
        r = {x["capture_id"]: x for x in json.loads((self.out / "resultados.json").read_text(encoding="utf-8"))}
        self.assertEqual(set(r), {"CAP-1", "CAP-2"})
        self.assertEqual(r["CAP-2"]["decision"], "revision_manual")
        self.assertEqual(r["CAP-2"]["reason_code"], "SIN_LECTURA")
        self.assertIn("Falta material", r["CAP-2"]["explicacion"])
        self.assertIn("VALIDACIÓN: OK", (self.out / "resumen.txt").read_text(encoding="utf-8"))

    def test_resultado_faltante_hace_fallar_la_entrega(self):
        """Si se quita la validación de entregar.main, esta prueba se pone roja."""
        real = correr.main

        def recorta(argv):
            real(argv)
            ruta = Path(argv[argv.index("--salida") + 1])
            datos = json.loads(ruta.read_text(encoding="utf-8"))
            ruta.write_text(json.dumps(datos[:1]), encoding="utf-8")
            return 0

        with mock.patch.object(correr, "main", recorta):
            self.assertEqual(self.entregar(), 1)
        self.assertIn("VALIDACIÓN: FALLÓ", (self.out / "resumen.txt").read_text(encoding="utf-8"))
        self.assertTrue((self.out / "resultados.json").exists(), "no debe borrar nada")

    def test_sin_capturas_para_con_mensaje(self):
        vacio = Path(self.tmp.name) / "vacio"
        vacio.mkdir()
        self.assertEqual(entregar.main(["--datos", str(vacio), "--salida", str(self.out), "--sin-modelo"]), 2)

    def test_sin_imagenes_para(self):
        for p in (self.datos / "fotos").rglob("*.jpg"):
            p.unlink()
        self.assertEqual(self.entregar(), 2)


if __name__ == "__main__":
    unittest.main()
