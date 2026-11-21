"""Pruebas unitarias para la puerta local sin tokens (`ml.validat3b.puerta`)."""

from __future__ import annotations

import unittest

from ml.validat3b.contrato import RC_BORROSA
from ml.validat3b.puerta import (
    UMBRAL_SEGURO_ETIQUETA,
    UMBRAL_SEGURO_PRODUCTO,
    puerta,
)


class TestPuertaLocal(unittest.TestCase):
    def test_por_encima_del_umbral_va_al_modelo(self) -> None:
        """Capturas con nitidez por encima del umbral seguro devuelven None (van al modelo)."""
        senales = {
            "nitidez_producto": UMBRAL_SEGURO_PRODUCTO + 50.0,
            "nitidez_etiqueta": UMBRAL_SEGURO_ETIQUETA + 50.0,
        }
        self.assertIsNone(puerta(senales))

    def test_en_el_umbral_exacto_va_al_modelo(self) -> None:
        """Valores exactamente iguales al umbral seguro no se rechazan (van al modelo)."""
        senales = {
            "nitidez_producto": UMBRAL_SEGURO_PRODUCTO,
            "nitidez_etiqueta": UMBRAL_SEGURO_ETIQUETA,
        }
        self.assertIsNone(puerta(senales))

    def test_producto_bajo_umbral_rechaza_borrosa(self) -> None:
        """Nitidez de producto debajo del umbral seguro devuelve CAPTURA_BORROSA."""
        senales = {
            "nitidez_producto": UMBRAL_SEGURO_PRODUCTO - 10.0,
            "nitidez_etiqueta": UMBRAL_SEGURO_ETIQUETA + 100.0,
        }
        self.assertEqual(puerta(senales), RC_BORROSA)

    def test_etiqueta_bajo_umbral_rechaza_borrosa(self) -> None:
        """Nitidez de etiqueta debajo del umbral seguro devuelve CAPTURA_BORROSA."""
        senales = {
            "nitidez_producto": UMBRAL_SEGURO_PRODUCTO + 100.0,
            "nitidez_etiqueta": UMBRAL_SEGURO_ETIQUETA - 5.0,
        }
        self.assertEqual(puerta(senales), RC_BORROSA)

    def test_senales_con_none_o_vacias_devuelve_none(self) -> None:
        """Ante señales con None, vacías o inválidas, devuelve None (ante la duda, va al modelo)."""
        self.assertIsNone(puerta(None))
        self.assertIsNone(puerta({}))
        self.assertIsNone(puerta({"nitidez_producto": None, "nitidez_etiqueta": None}))
        self.assertIsNone(puerta({"nitidez_producto": "", "nitidez_etiqueta": "nan"}))
        self.assertIsNone(puerta({"nitidez_producto": None, "nitidez_etiqueta": UMBRAL_SEGURO_ETIQUETA + 10.0}))


if __name__ == "__main__":
    unittest.main()
