"""Pruebas de decidir(). Datos inventados; no usa datos de 3B."""
import unittest

from ml.validat3b.contrato import (
    Captura, Extraccion, LecturaEtiqueta, LecturaProducto,
    RC_BORROSA, RC_ETIQUETA_AJENA, RC_INCOMPLETA, RC_LEJANA, RC_NO_COINCIDE, RC_NO_VISIBLE,
    RC_PANTALLA, RC_PRECIO_RANGO, RC_SIN_ETIQUETA, RC_SIN_LECTURA,
)
import json
from pathlib import Path

import ml.validat3b.contrato as contrato
from ml.validat3b.decidir import decidir, traducir


def captura(**cambios):
    datos = dict(
        capture_id="CAP-TEST-1", capture_store_name="Tienda Prueba", capture_date="2026-11-21",
        capture_barcode="7501000000011", capture_price=45.5, capture_brand="Nutrioli",
        id_product=1, product_name="Aceite Nutrioli", product_barcode="7501000000011",
        min_product_price=40.0, max_product_price=60.0,
        unit_product="ml", unit_quantity_product=900.0,
        facade_file="imagenes/f.jpg", product_file="imagenes/p.jpg", shelf_file="imagenes/e.jpg",
    )
    datos.update(cambios)
    return Captura(**datos)


def lectura_producto(**cambios):
    datos = dict(
        hay_producto=True, marca="NUTRIOLI", descripcion="Aceite Nutrioli",
        contenido_cantidad=900.0, contenido_unidad="ml",
        nitidez="nitida", encuadre="cercano",
    )
    datos.update(cambios)
    return LecturaProducto(**datos)


def lectura_etiqueta(**cambios):
    datos = dict(hay_etiqueta=True, texto_producto="Aceite Nutrioli 900 ml",
                 precio=45.5, legible=True)
    datos.update(cambios)
    return LecturaEtiqueta(**datos)


def extraccion(cap=None, producto=None, etiqueta=None, **cambios):
    datos = dict(
        capture_id=(cap or captura()).capture_id,
        producto=producto or lectura_producto(),
        etiqueta=etiqueta or lectura_etiqueta(),
        origen="modelo",
    )
    datos.update(cambios)
    return Extraccion(**datos)


class DecidirTest(unittest.TestCase):

    def test_01_sin_lectura_del_modelo_va_a_revision(self):
        cap = captura()
        r = decidir(cap, extraccion(cap, origen="sin_modelo"))
        self.assertEqual(r.decision, "revision_manual")
        self.assertEqual(r.reason_code, RC_SIN_LECTURA)

    def test_02_foto_de_pantalla_se_rechaza(self):
        cap = captura()
        r = decidir(cap, extraccion(cap, producto=lectura_producto(foto_de_pantalla=True)))
        self.assertEqual((r.decision, r.reason_code), ("rechazada", RC_PANTALLA))
        self.assertEqual(r.validaciones.producto, "falla")

    def test_03_sin_producto_visible_se_rechaza(self):
        cap = captura()
        r = decidir(cap, extraccion(cap, producto=lectura_producto(hay_producto=False)))
        self.assertEqual((r.decision, r.reason_code), ("rechazada", RC_NO_VISIBLE))

    def test_04_borrosa_se_rechaza(self):
        cap = captura()
        r = decidir(cap, extraccion(cap, producto=lectura_producto(nitidez="borrosa")))
        self.assertEqual((r.decision, r.reason_code), ("rechazada", RC_BORROSA))

    def test_05_lejana_se_rechaza(self):
        cap = captura()
        r = decidir(cap, extraccion(cap, producto=lectura_producto(encuadre="lejano")))
        self.assertEqual((r.decision, r.reason_code), ("rechazada", RC_LEJANA))

    def test_06_sin_marca_es_incompleta(self):
        cap = captura()
        r = decidir(cap, extraccion(cap, producto=lectura_producto(marca=None)))
        self.assertEqual((r.decision, r.reason_code), ("rechazada", RC_INCOMPLETA))

    def test_07_sin_contenido_con_encuadre_medio_es_lejana(self):
        cap = captura()
        prod = lectura_producto(contenido_cantidad=None, contenido_unidad=None, encuadre="medio")
        r = decidir(cap, extraccion(cap, producto=prod))
        self.assertEqual((r.decision, r.reason_code), ("rechazada", RC_LEJANA))

    def test_08_marca_claramente_distinta_se_rechaza(self):
        cap = captura()
        r = decidir(cap, extraccion(cap, producto=lectura_producto(marca="ZAPATOS ROJOS", descripcion="tenis")))
        self.assertEqual((r.decision, r.reason_code), ("rechazada", RC_NO_COINCIDE))

    def test_09_zona_gris_va_a_revision(self):
        cap = captura()
        # la descripción coincide a medias con el nombre del producto (1 de 2 palabras)
        r = decidir(cap, extraccion(cap, producto=lectura_producto(descripcion="aceite de oliva extra")))
        self.assertEqual((r.decision, r.reason_code), ("revision_manual", RC_NO_COINCIDE))

    def test_10_sin_etiqueta_legible_se_rechaza(self):
        cap = captura()
        r = decidir(cap, extraccion(cap, etiqueta=lectura_etiqueta(hay_etiqueta=False, precio=None, legible=False)))
        self.assertEqual((r.decision, r.reason_code), ("rechazada", RC_SIN_ETIQUETA))
        self.assertEqual(r.validaciones.evidencia_precio, "falla")

    def test_11_etiqueta_de_otro_producto_va_a_revision(self):
        cap = captura()
        r = decidir(cap, extraccion(cap, etiqueta=lectura_etiqueta(texto_producto="Galletas Marías 200 g")))
        self.assertEqual((r.decision, r.reason_code), ("revision_manual", RC_ETIQUETA_AJENA))

    def test_12_precio_fuera_de_rango_va_a_revision(self):
        cap = captura()
        r = decidir(cap, extraccion(cap, etiqueta=lectura_etiqueta(precio=99.0)))
        self.assertEqual((r.decision, r.reason_code), ("revision_manual", RC_PRECIO_RANGO))

    def test_13_nitidez_dudosa_va_a_revision_sin_codigo(self):
        cap = captura()
        r = decidir(cap, extraccion(cap, producto=lectura_producto(nitidez="dudosa")))
        self.assertEqual((r.decision, r.reason_code), ("revision_manual", None))

    def test_14_todo_claro_aprueba_aunque_la_marca_tenga_acento_y_mayusculas(self):
        cap = captura()
        prod = lectura_producto(marca="NÚTRIOLI")
        r = decidir(cap, extraccion(cap, producto=prod))
        self.assertEqual((r.decision, r.reason_code), ("aprobada", None))
        self.assertEqual(r.precio_detectado, 45.5)
        self.assertEqual(r.codigo_barras_detectado, cap.capture_barcode)
        self.assertEqual(r.confidence_score, 0.95)

    def test_15_coincidencia_de_etiqueta_media_va_a_revision(self):
        # UMBRAL_ETIQUETA_AJENA = 0.6: el texto de la etiqueta coincide solo a medias (1 de 2 palabras)
        cap = captura()
        r = decidir(cap, extraccion(cap, etiqueta=lectura_etiqueta(texto_producto="Aceite Galleta")))
        self.assertEqual((r.decision, r.reason_code), ("revision_manual", RC_ETIQUETA_AJENA))

    def test_16_etiqueta_con_otros_precios_va_a_revision(self):
        # Dos precios en la etiqueta y no se sabe cuál aplica → revisión (regla 11)
        cap = captura()
        r = decidir(cap, extraccion(cap, etiqueta=lectura_etiqueta(otros_precios=[22.0, 17.5])))
        self.assertEqual((r.decision, r.reason_code), ("revision_manual", None))

    def test_17_todo_codigo_de_decidir_es_llave_del_mapa(self):
        mapa = json.loads((Path(__file__).parent / "mapa_codigos.json").read_text(encoding="utf-8"))
        codigos = {v for k, v in vars(contrato).items() if k.startswith("RC_") and isinstance(v, str)}
        self.assertTrue(codigos <= set(mapa), f"faltan en mapa: {codigos - set(mapa)}")

    def test_18_oferta_se_dice_en_la_explicacion(self):
        cap = captura()
        r = decidir(cap, extraccion(cap, etiqueta=lectura_etiqueta(tipo_precio="oferta")))
        self.assertEqual(r.decision, "aprobada")
        self.assertIn("de oferta", r.explicacion)

    def test_19_traducir_cambia_codigo_solo_si_hay_entrada(self):
        cap = captura()
        r = decidir(cap, extraccion(cap, producto=lectura_producto(encuadre="lejano")))
        self.assertEqual(traducir(r, {"CAPTURA_LEJANA": "OFICIAL_LEJANA"}).reason_code, "OFICIAL_LEJANA")
        self.assertEqual(traducir(r, {}).reason_code, "CAPTURA_LEJANA")


if __name__ == "__main__":
    unittest.main()
