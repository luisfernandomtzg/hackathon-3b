"""Pruebas del parseo de la lectura (v3). Datos inventados; no usa datos de 3B ni el endpoint."""
import json
import unittest

from ml.validat3b.contrato import Extraccion
from ml.validat3b.extraer import _parsear

PROD = {"hay_producto": True, "marca": "Marca", "descripcion": "Producto", "contenido_cantidad": 1, "contenido_unidad": "kg",
        "contenido_legible": True, "nitidez": "nitida", "encuadre": "cercano", "varios_productos": False, "foto_de_pantalla": False}
ETQ = {"hay_etiqueta": True, "texto_producto": "PRODUCTO 1 KG", "precio": 10.5, "tipo_precio": "regular",
       "otros_precios": [], "legible": True}


def texto(**extra):
    return "```json\n" + json.dumps({"producto": PROD, "etiqueta": {**ETQ, **extra}}) + "\n```"


class ParsearTest(unittest.TestCase):
    def test_campos_de_la_foto_de_etiqueta(self):
        _, e = _parsear(texto(encuadre="lejano", nitidez="borrosa", ancho_pct=12))
        self.assertEqual((e.encuadre, e.nitidez, e.ancho_pct), ("lejano", "borrosa", 12.0))

    def test_valores_raros_no_tumban_la_lectura(self):
        _, e = _parsear(texto(encuadre="muy lejos", nitidez=None, ancho_pct="40 %"))
        self.assertEqual((e.encuadre, e.nitidez, e.ancho_pct, e.precio), (None, None, 40.0, 10.5))
        _, e = _parsear(texto(ancho_pct="la mitad"))
        self.assertIsNone(e.ancho_pct)

    def test_lectura_v2_sin_campos_nuevos_sigue_valiendo(self):
        _, e = _parsear(texto())
        self.assertEqual((e.encuadre, e.nitidez, e.ancho_pct), (None, None, None))
        viejo = {"capture_id": "X", "producto": PROD, "etiqueta": ETQ}
        self.assertIsNone(Extraccion.model_validate(viejo).etiqueta.encuadre)


if __name__ == "__main__":
    unittest.main()
