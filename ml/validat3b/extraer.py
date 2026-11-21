"""Extracción v1: UNA llamada por captura (foto de producto + foto de etiqueta), lectura a ciegas."""
import io
import json
import re
from pathlib import Path

from PIL import Image

from .cliente import Cliente
from .contrato import Captura, Extraccion, LecturaEtiqueta, LecturaProducto

PROMPT_VERSION = "v1"

PROMPT = """Recibes dos fotos de una tienda: la 1ª es el PRODUCTO en anaquel, la 2ª es la ETIQUETA de precio.
Solo LEE lo que se ve; no juzgues ni adivines. Si algo no se alcanza a leer, usa null.
Responde SOLO un JSON, sin texto extra, con esta forma:
{"producto":{"hay_producto":bool,"marca":str|null,"descripcion":str|null,"contenido_cantidad":número|null,"contenido_unidad":"g"|"kg"|"ml"|"l"|"pza"|null,"nitidez":"nitida"|"dudosa"|"borrosa","encuadre":"cercano"|"medio"|"lejano","varios_productos":bool,"foto_de_pantalla":bool},
"etiqueta":{"hay_etiqueta":bool,"texto_producto":str|null,"precio":número|null,"tipo_precio":"regular"|"oferta"|"volumen"|null,"otros_precios":[números],"legible":bool}}
Reglas: "contenido" es el peso/volumen impreso en el empaque (p. ej. 400 g). "encuadre" lejano = el texto del empaque es muy pequeño para leerse. "foto_de_pantalla" = es foto de un monitor o celular. "precio" es el precio unitario vigente de la etiqueta."""


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
        version = PROMPT_VERSION if intento == 0 else PROMPT_VERSION + "-r"
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
