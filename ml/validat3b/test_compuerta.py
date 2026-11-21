"""Pruebas de compuerta() y de su cableado en correr. Datos inventados; no usa datos de 3B."""
import unittest
from unittest import mock

from ml.validat3b import correr
from ml.validat3b.compuerta import UMBRAL_NITIDEZ_ETIQUETA, compuerta
from ml.validat3b.contrato import Extraccion, Resultado, Validaciones
from ml.validat3b.test_decidir import captura, lectura_etiqueta, lectura_producto


def resultado(decision="aprobada"):
    return Resultado(capture_id="CAP-TEST-1", decision=decision, confidence_score=0.9,
                     reason_code=None if decision == "aprobada" else "CAPTURA_LEJANA",
                     validaciones=Validaciones(), explicacion="Decidido por reglas.")


BUENAS = {"codigo_coincide": True, "nitidez_etiqueta": 300.0, "codigo_barras_leido": "7501000000011"}


class PruebasCompuerta(unittest.TestCase):
    def test_codigo_no_coincide_baja_aprobada(self):
        r = compuerta(resultado(), {**BUENAS, "codigo_coincide": False, "codigo_barras_leido": "0401013049343"}, "7501791626163")
        self.assertEqual((r.decision, r.reason_code, r.confidence_score), ("revision_manual", None, 0.5))
        self.assertIn("(0401013049343) no coincide con el registrado (7501791626163)", r.explicacion)

    def test_codigo_no_coincide_baja_tambien_rechazada(self):
        r = compuerta(resultado("rechazada"), {**BUENAS, "codigo_coincide": False}, "x")
        self.assertEqual(r.decision, "revision_manual")

    def test_etiqueta_poco_nitida_baja_aprobada(self):
        r = compuerta(resultado(), {**BUENAS, "nitidez_etiqueta": UMBRAL_NITIDEZ_ETIQUETA - 1})
        self.assertEqual(r.decision, "revision_manual")
        self.assertIn("nitidez suficiente", r.explicacion)

    def test_sin_senales_baja_aprobada(self):
        for sen in ({}, None, {"nitidez_etiqueta": None}):
            self.assertEqual(compuerta(resultado(), sen).decision, "revision_manual", sen)

    def test_buenas_senales_no_cambian(self):
        r = resultado()
        self.assertEqual(compuerta(r, BUENAS), r)

    def test_nitidez_baja_no_toca_rechazada_ni_revision(self):
        for d in ("rechazada", "revision_manual"):
            r = resultado(d)
            self.assertEqual(compuerta(r, {"nitidez_etiqueta": 10.0}), r)

    def test_codigo_no_leido_no_baja(self):
        r = resultado()
        self.assertEqual(compuerta(r, {**BUENAS, "codigo_coincide": None}), r)

    def test_nunca_aprueba(self):
        for d in ("rechazada", "revision_manual"):
            self.assertNotEqual(compuerta(resultado(d), BUENAS).decision, "aprobada")


class PruebasCableado(unittest.TestCase):
    """Si se quita compuerta() de correr, esta prueba se pone roja."""

    def test_correr_aplica_la_compuerta_tras_decidir(self):
        c = captura()
        ext = Extraccion(capture_id=c.capture_id, producto=lectura_producto(), etiqueta=lectura_etiqueta())
        senales = {"codigo_coincide": False, "codigo_barras_leido": "0401013049343", "nitidez_etiqueta": 300.0}
        with mock.patch.object(correr, "extraer", return_value=ext), \
             mock.patch.object(correr, "senales_locales", return_value=senales), \
             mock.patch.object(correr, "decidir", return_value=resultado("aprobada")):
            _, res = correr.procesar(c, "x", None, True)
        self.assertEqual(res.decision, "revision_manual")
        self.assertIn("no coincide", res.explicacion)

    def test_verificador_apagado_por_omision(self):
        c = captura()
        ext = Extraccion(capture_id=c.capture_id, producto=lectura_producto(), etiqueta=lectura_etiqueta())
        with mock.patch.object(correr, "extraer", return_value=ext), \
             mock.patch.object(correr, "senales_locales", return_value=BUENAS), \
             mock.patch.object(correr, "decidir", return_value=resultado("aprobada")), \
             mock.patch.object(correr, "aplicar_verificacion") as v:
            _, res = correr.procesar(c, "x", None, True)
            self.assertEqual(res.decision, "aprobada")
            v.assert_not_called()


if __name__ == "__main__":
    unittest.main()
