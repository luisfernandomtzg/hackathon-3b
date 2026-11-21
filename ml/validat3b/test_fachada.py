"""Pruebas de la revisión de fachada. Datos inventados; no usa datos de 3B ni el endpoint."""
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from ml.validat3b.contrato import RC_FACHADA, Captura, Resultado, Validaciones
from ml.validat3b.fachada import aplicar_fachada, misma_cadena


class ClienteFalso:
    def __init__(self, texto=None, error=None):
        self.texto, self.error, self.llamadas = texto, error, 0

    def consultar(self, capture_id, version, prompt, imagenes, max_tokens=60, etiqueta=None):
        self.llamadas += 1
        if self.error:
            raise self.error
        return self.texto, 300, 10, "modelo"


class FachadaTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        (Path(self.tmp.name) / "imagenes").mkdir()
        Image.new("RGB", (64, 48), "white").save(Path(self.tmp.name) / "imagenes" / "f.jpg")
        self.cap = Captura(capture_id="C1", capture_store_name="Bodega Aurrera", capture_date="2026-11-21",
                           capture_barcode="1", id_product=1, product_name="P", product_barcode="1",
                           facade_file="imagenes/f.jpg", product_file="imagenes/p.jpg", shelf_file="imagenes/e.jpg")

    def tearDown(self):
        self.tmp.cleanup()

    def _res(self, decision="aprobada"):
        return Resultado(capture_id="C1", decision=decision, confidence_score=0.95, validaciones=Validaciones(),
                         precio_detectado=10.0, explicacion="Todo coincide.")

    def test_misma_cadena_tolera_acentos_y_palabras_genericas(self):
        for leida, esperada in (("Bodega Aurrerá", "Bodega Aurrera"), ("AURRERA", "Bodega Aurrera"),
                                ("Tiendas Neto", "Neto"), ("Walmart Express", "Walmart"), ("Súper Chedraui", "Chedraui")):
            self.assertTrue(misma_cadena(leida, esperada), (leida, esperada))
        for leida, esperada in (("Soriana", "Bodega Aurrera"), ("Bodega Aurrera", "Walmart"), ("Oxxo", "Neto")):
            self.assertFalse(misma_cadena(leida, esperada), (leida, esperada))

    def test_fachada_de_otra_cadena_baja_la_aprobacion_a_revision(self):
        r = aplicar_fachada(self.cap, self._res(), self.tmp.name, ClienteFalso('{"cadena": "Soriana"}'))
        self.assertEqual((r.decision, r.reason_code, r.validaciones.tienda_fachada), ("revision_manual", RC_FACHADA, "falla"))
        self.assertIn("Soriana", r.explicacion)

    def test_fachada_correcta_o_ilegible_no_cambia_nada(self):
        for texto in ('{"cadena": "Bodega Aurrerá"}', '{"cadena": null}', '```json\n{"cadena": ""}\n```'):
            r = aplicar_fachada(self.cap, self._res(), self.tmp.name, ClienteFalso(texto))
            self.assertEqual((r.decision, r.validaciones.tienda_fachada), ("aprobada", "ok"), texto)

    def test_solo_se_llama_para_aprobadas_y_nunca_aprueba(self):
        for decision in ("rechazada", "revision_manual"):
            cli = ClienteFalso('{"cadena": "Bodega Aurrera"}')
            r = aplicar_fachada(self.cap, self._res(decision), self.tmp.name, cli)
            self.assertEqual((r.decision, cli.llamadas), (decision, 0))
        self.assertEqual(aplicar_fachada(self.cap, self._res(), self.tmp.name, None).decision, "aprobada")

    def test_si_la_revision_falla_no_se_aprueba_a_ciegas(self):
        for cli in (ClienteFalso(error=RuntimeError("sin red")), ClienteFalso("no es json")):
            self.assertEqual(aplicar_fachada(self.cap, self._res(), self.tmp.name, cli).decision, "revision_manual")
        sin_foto = self.cap.model_copy(update={"facade_file": "imagenes/no-existe.jpg"})
        self.assertEqual(aplicar_fachada(sin_foto, self._res(), self.tmp.name, ClienteFalso('{"cadena": null}')).decision,
                         "revision_manual")


if __name__ == "__main__":
    unittest.main()
