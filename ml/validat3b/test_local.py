"""Pruebas unitarias para señales locales sin tokens (`ml.validat3b.local`)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

from ml.validat3b.contrato import Captura
from ml.validat3b.local import calcular_nitidez_imagen, senales_locales


def _crear_imagen_patron(ancho: int = 800, alto: int = 600) -> Image.Image:
    """Genera en memoria una imagen con bordes de alto contraste (tablero/rejilla)."""
    img = Image.new("RGB", (ancho, alto), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    paso = 25
    for y in range(0, alto, paso):
        for x in range(0, ancho, paso):
            if ((x // paso) + (y // paso)) % 2 == 0:
                draw.rectangle([x, y, x + paso - 1, y + paso - 1], fill=(10, 10, 10))
    return img


class TestSenalesLocales(unittest.TestCase):
    def test_nitidez_baja_con_gaussian_blur_en_memoria(self) -> None:
        """Comprueba en memoria que una imagen desenfocada con GaussianBlur tiene menor nitidez."""
        img_nitida = _crear_imagen_patron()
        img_borrosa = img_nitida.filter(ImageFilter.GaussianBlur(radius=4))

        nitidez_alta = calcular_nitidez_imagen(img_nitida)
        nitidez_baja = calcular_nitidez_imagen(img_borrosa)

        self.assertIsNotNone(nitidez_alta)
        self.assertIsNotNone(nitidez_baja)
        assert nitidez_alta is not None and nitidez_baja is not None
        self.assertGreater(nitidez_alta, nitidez_baja)

    def test_senales_locales_nitidez_baja_y_huella_fachada(self) -> None:
        """Comprueba a través de `senales_locales` que la nitidez baja al desenfocar y calcula dimensiones y md5."""
        img_nitida = _crear_imagen_patron(800, 600)
        img_borrosa = img_nitida.filter(ImageFilter.GaussianBlur(radius=5))

        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            dir_imgs = base / "imagenes"
            dir_imgs.mkdir(parents=True, exist_ok=True)

            img_nitida.save(dir_imgs / "facade.jpg", format="JPEG", quality=95)
            img_nitida.save(dir_imgs / "prod_sharp.jpg", format="JPEG", quality=95)
            img_borrosa.save(dir_imgs / "prod_blur.jpg", format="JPEG", quality=95)

            cap = Captura(
                capture_id="CAP-TEST-01",
                capture_store_name="Tienda 3B",
                capture_date="2026-11-21 10:00:00",
                capture_barcode="007501234567890",
                id_product=1,
                product_name="Producto Prueba",
                product_barcode="7501234567890",
                facade_file="facade.jpg",
                product_file="prod_sharp.jpg",
                shelf_file="prod_blur.jpg",
            )

            res = senales_locales(cap, base)

            self.assertIsNotNone(res["nitidez_producto"])
            self.assertIsNotNone(res["nitidez_etiqueta"])
            self.assertGreater(res["nitidez_producto"], res["nitidez_etiqueta"])
            self.assertEqual(res["ancho_producto"], 800)
            self.assertEqual(res["alto_producto"], 600)
            self.assertEqual(res["ancho_etiqueta"], 800)
            self.assertEqual(res["alto_etiqueta"], 600)
            self.assertEqual(res["ancho_fachada"], 800)
            self.assertEqual(res["alto_fachada"], 600)
            self.assertIsInstance(res["huella_fachada"], str)
            self.assertEqual(len(res["huella_fachada"]), 32)

    def test_ruta_inexistente_devuelve_none_sin_romper(self) -> None:
        """Comprueba que rutas inexistentes devuelven None en sus campos sin lanzar excepción."""
        cap = Captura(
            capture_id="CAP-NO-EXISTE",
            capture_store_name="Tienda 3B",
            capture_date="2026-11-21 10:00:00",
            capture_barcode="7501234567890",
            id_product=1,
            product_name="Producto Inexistente",
            product_barcode="7501234567890",
            facade_file="imagenes/no_existe_facade.jpg",
            product_file="imagenes/no_existe_product.jpg",
            shelf_file="imagenes/no_existe_shelf.jpg",
        )

        res = senales_locales(cap, Path("ruta/que/no/existe/en/absoluto"))

        self.assertIsInstance(res, dict)
        self.assertIsNone(res["codigo_barras_leido"])
        self.assertIsNone(res["codigo_coincide"])
        self.assertIsNone(res["nitidez_producto"])
        self.assertIsNone(res["nitidez_etiqueta"])
        self.assertIsNone(res["ancho_fachada"])
        self.assertIsNone(res["alto_fachada"])
        self.assertIsNone(res["ancho_producto"])
        self.assertIsNone(res["alto_producto"])
        self.assertIsNone(res["ancho_etiqueta"])
        self.assertIsNone(res["alto_etiqueta"])
        self.assertIsNone(res["ancho"])
        self.assertIsNone(res["alto"])
        self.assertIsNone(res["huella_fachada"])


if __name__ == "__main__":
    unittest.main()
