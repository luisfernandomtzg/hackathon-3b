"""Pruebas del verificador de aprobadas. Cliente falso e imágenes inventadas; no usa datos de 3B."""
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from ml.validat3b.contrato import Extraccion, Resultado, Validaciones
from ml.validat3b.test_decidir import captura, lectura_etiqueta, lectura_producto
from ml.validat3b.verificar import aplicar_verificacion, verificar


class ClienteFalso:
    def __init__(self, respuesta=None, error=None, tokens_in=2000):
        self.respuesta, self.error, self.tokens_in, self.llamadas = respuesta, error, tokens_in, []

    def consultar(self, capture_id, version, prompt, imagenes, max_tokens=400, etiqueta=None):
        self.llamadas.append((capture_id, etiqueta, [len(i) for i in imagenes]))
        if self.error:
            raise self.error
        return self.respuesta, self.tokens_in, 20, "modelo"


def ext():
    return Extraccion(capture_id="CAP-TEST-1", producto=lectura_producto(), etiqueta=lectura_etiqueta())


def resultado(decision):
    return Resultado(capture_id="CAP-TEST-1", decision=decision, confidence_score=0.9,
                     reason_code=None if decision == "aprobada" else "CAPTURA_LEJANA",
                     validaciones=Validaciones(), explicacion="Decidido por reglas.")


class PruebasVerificar(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        img = Path(self.tmp.name) / "imagenes" / "imagenes"
        img.mkdir(parents=True)
        for n in ("p.jpg", "e.jpg"):
            Image.new("RGB", (1600, 1200), (120, 80, 40)).save(img / n)
        self.dir = self.tmp.name
        self.c = captura(product_file="imagenes/p.jpg", shelf_file="imagenes/e.jpg")

    def tearDown(self):
        self.tmp.cleanup()

    def aplicar(self, cliente, decision="aprobada"):
        return aplicar_verificacion(self.c, ext(), resultado(decision), self.dir, cliente)

    def test_ok_false_baja_a_revision(self):
        cl = ClienteFalso('{"ok": false, "motivo": "contenido no se lee"}')
        r = self.aplicar(cl)
        self.assertEqual(r.decision, "revision_manual")
        self.assertIsNone(r.reason_code)
        self.assertEqual(r.confidence_score, 0.5)
        self.assertIn("Segunda revisión: contenido no se lee", r.explicacion)

    def test_error_del_cliente_baja_a_revision(self):
        r = self.aplicar(ClienteFalso(error=RuntimeError("429")))
        self.assertEqual(r.decision, "revision_manual")
        self.assertIn("Segunda revisión", r.explicacion)

    def test_json_invalido_baja_a_revision(self):
        for texto in ("no es json", '{"ok": "si"}', '{"motivo": "x"}', ""):
            self.assertEqual(self.aplicar(ClienteFalso(texto)).decision, "revision_manual", texto)

    def test_ok_true_sigue_aprobada(self):
        r = self.aplicar(ClienteFalso('{"ok": true, "motivo": "claro"}'))
        self.assertEqual(r.decision, "aprobada")
        self.assertEqual(r.explicacion, "Decidido por reglas.")

    def test_no_aprobada_cero_llamadas(self):
        for decision in ("rechazada", "revision_manual"):
            cl = ClienteFalso('{"ok": true}')
            r = self.aplicar(cl, decision)
            self.assertEqual(r.decision, decision)
            self.assertEqual(cl.llamadas, [], f"el verificador llamó con {decision}")

    def test_sin_cliente_no_aprueba_ni_llama(self):
        self.assertEqual(self.aplicar(None).decision, "aprobada")  # --sin-modelo no pasa por el verificador

    def test_etiqueta_de_tokens_y_alta_resolucion(self):
        cl = ClienteFalso('{"ok": true, "motivo": ""}')
        ok, _ = verificar(self.c, ext(), self.dir, cl)
        self.assertTrue(ok)
        self.assertEqual(len(cl.llamadas), 1)
        self.assertEqual(cl.llamadas[0][1], "verificar")

    def test_si_pasa_de_2500_tokens_baja_la_resolucion(self):
        cl = ClienteFalso('{"ok": true}', tokens_in=3000)
        verificar(self.c, ext(), self.dir, cl)
        self.assertEqual(len(cl.llamadas), 2)
        self.assertLess(sum(cl.llamadas[1][2]), sum(cl.llamadas[0][2]))


if __name__ == "__main__":
    unittest.main()
