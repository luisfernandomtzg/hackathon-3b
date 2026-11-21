"""Pruebas de D1 · evaluar.py. Costos calculados a mano sobre 6 capturas inventadas."""

import unittest

from ml.validat3b.evaluar import COSTO_SIN_PREDICCION, costo, entrada_valida, evaluar

VALIDACIONES_OK = {"tienda_fachada": "ok", "producto": "ok", "codigo_barras": "ok", "evidencia_precio": "ok"}


def entrada(cid, dec):
    return {
        "capture_id": cid, "decision": dec, "confidence_score": 0.9, "reason_code": None,
        "validaciones": dict(VALIDACIONES_OK), "precio_detectado": None,
        "codigo_barras_detectado": None, "explicacion": "prueba",
    }


# Real -> predicha, con costo calculado a mano:
#  C1 aprobada -> aprobada                 0
#  C2 aprobada -> rechazada                3
#  C3 rechazada -> aprobada               10  (falso positivo)
#  C4 rechazada -> rechazada               0
#  C5 revision_manual -> revision_manual   1 pesimista / 0 optimista
#  C6 revision_manual -> aprobada         10
CAPTURAS = {
    "C1": {"decision_esperada": "aprobada", "motivo_rechazo": "", "facade_url": "V1", "capture_price": "10.00"},
    "C2": {"decision_esperada": "aprobada", "motivo_rechazo": "", "facade_url": "V1", "capture_price": "20.00"},
    "C3": {"decision_esperada": "rechazada", "motivo_rechazo": "Capturas lejanas", "facade_url": "V2", "capture_price": ""},
    "C4": {"decision_esperada": "rechazada", "motivo_rechazo": "Capturas borrosas", "facade_url": "V2", "capture_price": ""},
    "C5": {"decision_esperada": "revision_manual", "motivo_rechazo": "", "facade_url": "V3", "capture_price": "5.00"},
    "C6": {"decision_esperada": "revision_manual", "motivo_rechazo": "", "facade_url": "V3", "capture_price": "7.00"},
}
PREDICCIONES = [
    entrada("C1", "aprobada"),
    entrada("C2", "rechazada"),
    entrada("C3", "aprobada"),
    entrada("C4", "rechazada"),
    entrada("C5", "revision_manual"),
    entrada("C6", "aprobada"),
]


class TablaCosto(unittest.TestCase):
    def test_celdas(self):
        self.assertEqual(costo("aprobada", "aprobada"), 0)
        self.assertEqual(costo("aprobada", "rechazada"), 3)
        self.assertEqual(costo("rechazada", "aprobada"), 10)
        self.assertEqual(costo("revision_manual", "revision_manual", "pesimista"), 1)
        self.assertEqual(costo("revision_manual", "revision_manual", "optimista"), 0)
        self.assertEqual(costo("revision_manual", "aprobada"), 10)
        self.assertEqual(costo("aprobada", None), COSTO_SIN_PREDICCION)


class Validez(unittest.TestCase):
    def test_entrada_valida_y_no(self):
        self.assertTrue(entrada_valida(entrada("C1", "aprobada")))
        self.assertFalse(entrada_valida(entrada("C1", "tal_vez")))
        malo = entrada("C1", "aprobada")
        malo["confidence_score"] = 1.5
        self.assertFalse(entrada_valida(malo))
        sin_llave = entrada("C1", "aprobada")
        del sin_llave["explicacion"]
        self.assertFalse(entrada_valida(sin_llave))


class Evaluacion(unittest.TestCase):
    def test_json_completo(self):
        r = evaluar(CAPTURAS, PREDICCIONES)
        self.assertEqual(r["json_ok"], 6)
        self.assertEqual(r["pct_json"], 1.0)

    def test_costos_totales(self):
        r = evaluar(CAPTURAS, PREDICCIONES)
        self.assertEqual(r["costo"]["pesimista"], 24)  # 0+3+10+0+1+10
        self.assertEqual(r["costo"]["optimista"], 23)  # 0+3+10+0+0+10

    def test_precision(self):
        r = evaluar(CAPTURAS, PREDICCIONES)
        self.assertEqual(r["aprobadas"], 3)  # C1, C3, C6
        self.assertEqual(r["tp"], 1)         # solo C1
        self.assertAlmostEqual(r["precision"], 1 / 3)

    def test_falta_una_entrada(self):
        r = evaluar(CAPTURAS, PREDICCIONES[:-1])  # sin C6
        self.assertEqual(r["json_ok"], 5)
        self.assertEqual(r["json_fallan"], ["C6"])
        self.assertEqual(r["costo"]["pesimista"], 24)  # C6 cuesta 10 sin predicción
        self.assertEqual(r["aprobadas"], 2)
        self.assertAlmostEqual(r["precision"], 0.5)

    def test_sin_aprobadas(self):
        sin_aprobar = [e for e in PREDICCIONES if e["decision"] != "aprobada"]
        r = evaluar(CAPTURAS, sin_aprobar)
        self.assertEqual(r["aprobadas"], 0)
        self.assertIsNone(r["precision"])


if __name__ == "__main__":
    unittest.main()
