"""Fachada (S005): antes de dejar una captura como «aprobada» se lee la foto de la fachada y se compara la cadena.

El reto lista «fachada incorrecta» entre los rechazos por calidad de evidencia. Solo se llama para las capturas que
ya pasaron reglas, compuertas y consenso (~16 %), con la foto reducida; las capturas de una misma visita comparten
foto de fachada y por lo tanto comparten lectura (misma llave de caché). Solo una CONTRADICCIÓN legible baja la
aprobación a revisión: si el letrero no se lee, no se castiga. Nunca convierte nada en aprobada.
"""
import json
import re

from .contrato import RC_FACHADA, Captura, Resultado
from .extraer import _jpeg, resolver_imagen
from .normalizar import _palabra_parecida, texto

FACHADA_VERSION = "fachada-v1"
PROMPT = """Foto de la entrada o fachada de una tienda. Responde SOLO JSON: {"cadena": str|null}
cadena: el nombre del comercio que se LEE en el letrero o rótulo (p. ej. "Soriana", "Bodega Aurrera"); null si no se lee ninguno. No adivines por colores."""
# Palabras que no distinguen una cadena de otra.
_GENERICAS = {"tienda", "tiendas", "super", "supermercado", "bodega", "mercado", "express", "supercenter", "hiper",
              "selecto", "plaza", "sucursal", "de", "la", "el", "los", "las", "y", "s", "a", "sa", "cv", "mi"}


def _claves(nombre) -> list[str]:
    palabras = texto(nombre).split()
    return [p for p in palabras if p not in _GENERICAS] or palabras


def misma_cadena(leida, esperada) -> bool:
    """¿El letrero leído y la cadena registrada comparten alguna palabra distintiva? (tolera acentos y faltas)."""
    a, b = _claves(leida), _claves(esperada)
    return any(_palabra_parecida(p, b) for p in a) or any(_palabra_parecida(p, a) for p in b)


def leer_cadena(captura: Captura, dir_datos, cliente):
    ruta = resolver_imagen(dir_datos, captura.facade_file)
    if ruta is None:
        raise FileNotFoundError("falta la foto de fachada")
    salida = cliente.consultar(captura.capture_id, FACHADA_VERSION, PROMPT, [_jpeg(ruta, lado=512)], max_tokens=60)
    m = re.search(r"\{.*\}", salida[0], re.S)
    cadena = json.loads(m.group(0) if m else salida[0]).get("cadena")
    return cadena.strip() if isinstance(cadena, str) and cadena.strip() else None


def aplicar_fachada(captura: Captura, res: Resultado, dir_datos, cliente) -> Resultado:
    if res.decision != "aprobada" or cliente is None:
        return res
    try:
        cadena = leer_cadena(captura, dir_datos, cliente)
    except Exception as e:
        return res.model_copy(update={
            "decision": "revision_manual", "reason_code": None, "confidence_score": 0.5,
            "explicacion": f"{res.explicacion} No se pudo revisar la fachada ({type(e).__name__}); pasa a revisión."})
    if cadena is None or not (captura.capture_store_name or "").strip() or misma_cadena(cadena, captura.capture_store_name):
        return res
    val = res.validaciones.model_copy(update={"tienda_fachada": "falla"})
    return res.model_copy(update={
        "decision": "revision_manual", "reason_code": RC_FACHADA, "confidence_score": 0.5, "validaciones": val,
        "explicacion": f"{res.explicacion} Pero la fachada dice «{cadena}» y la captura se registró en "
                       f"«{captura.capture_store_name}»; pasa a revisión."})
