"""Extracción v1: UNA llamada por captura (foto de producto + foto de etiqueta), lectura a ciegas."""
import hashlib
import io
import json
import re
from pathlib import Path

from PIL import Image

from .cliente import Cliente
from .contrato import Captura, Extraccion, LecturaEtiqueta, LecturaProducto

PROMPT_VERSION = "v3"

PROMPT = """Fotos de tienda: 1ª = PRODUCTO en anaquel, 2ª = ETIQUETA de precio. Solo LEE; no juzgues. Lo ilegible va null.
Responde SOLO JSON:
{"producto":{"hay_producto":bool,"marca":str|null,"descripcion":str|null,"contenido_cantidad":número|null,"contenido_unidad":"g"|"kg"|"ml"|"l"|"pza"|null,"contenido_legible":bool,"nitidez":"nitida"|"dudosa"|"borrosa","encuadre":"cercano"|"medio"|"lejano","varios_productos":bool,"foto_de_pantalla":bool},
"etiqueta":{"hay_etiqueta":bool,"texto_producto":str|null,"precio":número|null,"tipo_precio":"regular"|"oferta"|"volumen"|null,"otros_precios":[números],"legible":bool,"encuadre":"cercano"|"medio"|"lejano","nitidez":"nitida"|"dudosa"|"borrosa","ancho_pct":número}}
encuadre: "lejano" si el texto del frente (marca, descripción, contenido) no se lee con claridad aunque la foto sea nítida; "cercano" si se lee sin esfuerzo; si no, "medio".
contenido_legible: true solo si lees el número de contenido impreso (p. ej. 400 g).
descripcion: nombre corto del frente, máx. 6 palabras, sin ingredientes.
marca: la principal; con submarca, "Marca Submarca".
contenido: el neto del frente; si hay drenado y total, el drenado (el otro en descripcion).
precio: el unitario vigente de la etiqueta.
etiqueta = el letrero de precio del anaquel, no el empaque. texto_producto: SOLO lo impreso en ese letrero (nombre del producto); null si no se lee ahí.
etiqueta.ancho_pct: % aproximado del ancho de la 2ª foto que ocupa ese letrero (0-100). etiqueta.encuadre: "cercano" si ocupa un tercio del ancho o más; "lejano" si ocupa menos de un sexto o la foto muestra el anaquel con el letrero pequeño; si no, "medio".
etiqueta.nitidez: "borrosa" si la letra pequeña del letrero no se lee por desenfoque; "nitida" si se lee toda; si no, "dudosa"."""

_VERSION = PROMPT_VERSION + "-" + hashlib.sha1(PROMPT.encode()).hexdigest()[:6]  # editar el prompt invalida el caché


def resolver_imagen(dir_datos, rel) -> Path | None:
    """Ruta real de una foto del lote, o None. Tolera `imagenes/` de más o de menos y subcarpetas."""
    if not rel:
        return None
    base, rel = Path(dir_datos), str(rel).replace("\\", "/")
    for c in (base / "imagenes" / rel, base / rel, base / "imagenes" / "imagenes" / Path(rel).name,
              base / "imagenes" / Path(rel).name):
        if c.is_file():
            return c
    return None


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
    return LecturaProducto(**d["producto"]), LecturaEtiqueta(**_limpiar_etiqueta(d["etiqueta"]))


def _limpiar_etiqueta(e: dict) -> dict:
    """Los campos nuevos de la foto de etiqueta (v3) nunca tumban la lectura: lo que no valide queda en None."""
    e = dict(e)
    if e.get("encuadre") not in ("cercano", "medio", "lejano"):
        e["encuadre"] = None
    if e.get("nitidez") not in ("nitida", "dudosa", "borrosa"):
        e["nitidez"] = None
    try:
        v = e.get("ancho_pct")
        e["ancho_pct"] = None if v is None else max(0.0, min(100.0, float(str(v).replace("%", "").strip())))
    except (TypeError, ValueError):
        e["ancho_pct"] = None
    return e


def _vacia(capture_id, origen, t_in=0, t_out=0) -> Extraccion:
    return Extraccion(capture_id=capture_id, producto=LecturaProducto(hay_producto=False),
                      etiqueta=LecturaEtiqueta(hay_etiqueta=False), tokens_entrada=t_in,
                      tokens_salida=t_out, origen=origen)


def sin_modelo(captura: Captura) -> Extraccion:
    return _vacia(captura.capture_id, "sin_modelo")


def extraer(captura: Captura, dir_datos, cliente: Cliente | None = None, variante: str = "") -> Extraccion:
    """`variante` cambia la llave de caché: una segunda lectura independiente de la misma foto (consenso)."""
    rutas = [resolver_imagen(dir_datos, captura.product_file), resolver_imagen(dir_datos, captura.shelf_file)]
    if None in rutas:
        raise FileNotFoundError("falta la foto de producto o de etiqueta")
    imgs = [_jpeg(r) for r in rutas]
    cliente = cliente or Cliente()
    t_in = t_out = 0
    for intento in range(2):  # un reintento si el JSON no valida
        # el reintento cambia la versión para no leer del caché la misma respuesta mala
        version = (_VERSION if intento == 0 else _VERSION + "-r") + variante
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
