"""Extracción v1: UNA llamada por captura (foto de producto + foto de etiqueta), lectura a ciegas."""
import hashlib
import io
import json
import re
from pathlib import Path

from PIL import Image

from .cliente import Cliente
from .contrato import Captura, Extraccion, LecturaEtiqueta, LecturaProducto

PROMPT_VERSION = "v2"

PROMPT = """Fotos de tienda: 1ª = PRODUCTO en anaquel, 2ª = ETIQUETA de precio. Solo LEE; no juzgues. Lo ilegible va null.
Responde SOLO JSON:
{"producto":{"hay_producto":bool,"marca":str|null,"descripcion":str|null,"contenido_cantidad":número|null,"contenido_unidad":"g"|"kg"|"ml"|"l"|"pza"|null,"contenido_legible":bool,"nitidez":"nitida"|"dudosa"|"borrosa","encuadre":"cercano"|"medio"|"lejano","varios_productos":bool,"foto_de_pantalla":bool},
"etiqueta":{"hay_etiqueta":bool,"texto_producto":str|null,"precio":número|null,"tipo_precio":"regular"|"oferta"|"volumen"|null,"otros_precios":[números],"legible":bool}}
encuadre: "lejano" si el texto del frente (marca, descripción, contenido) no se lee con claridad aunque la foto sea nítida; "cercano" si se lee sin esfuerzo; si no, "medio".
contenido_legible: true solo si lees el número de contenido impreso (p. ej. 400 g).
descripcion: nombre corto del frente, máx. 6 palabras, sin ingredientes.
marca: la principal; con submarca, "Marca Submarca".
contenido: el neto del frente; si hay drenado y total, el drenado (el otro en descripcion).
precio: el unitario vigente de la etiqueta."""

_VERSION = PROMPT_VERSION + "-" + hashlib.sha1(PROMPT.encode()).hexdigest()[:6]  # editar el prompt invalida el caché


def _jpeg(ruta: Path, lado=768, calidad=80) -> bytes:
    with Image.open(ruta) as im:
        im = im.convert("RGB")
        im.thumbnail((lado, lado))
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=calidad)
        return buf.getvalue()


def _parsear(texto: str):
    m = re.search(r"\{.*\}", texto, re.S)
    d = json.loads(m.group(0) if m else texto)
    return LecturaProducto(**d["producto"]), LecturaEtiqueta(**d["etiqueta"])


def _vacia(capture_id, origen, t_in=0, t_out=0) -> Extraccion:
    return Extraccion(capture_id=capture_id, producto=LecturaProducto(hay_producto=False),
                      etiqueta=LecturaEtiqueta(hay_etiqueta=False), tokens_entrada=t_in,
                      tokens_salida=t_out, origen=origen)


def sin_modelo(captura: Captura) -> Extraccion:
    return _vacia(captura.capture_id, "sin_modelo")


def extraer(captura: Captura, dir_datos, cliente: Cliente | None = None) -> Extraccion:
    base = Path(dir_datos) / "imagenes"
    imgs = [_jpeg(base / captura.product_file), _jpeg(base / captura.shelf_file)]
    cliente = cliente or Cliente()
    t_in = t_out = 0
    for intento in range(2):  # un reintento si el JSON no valida
        # el reintento cambia la versión para no leer del caché la misma respuesta mala
        version = _VERSION if intento == 0 else _VERSION + "-r"
        texto, a, b, origen = cliente.consultar(captura.capture_id, version, PROMPT, imgs, max_tokens=400)
        t_in += a
        t_out += b
        try:
            prod, etq = _parsear(texto)
            return Extraccion(capture_id=captura.capture_id, producto=prod, etiqueta=etq,
                              tokens_entrada=t_in, tokens_salida=t_out, origen=origen)
        except Exception:
            continue
    return _vacia(captura.capture_id, "error", t_in, t_out)
