"""Verificador de aprobadas (I3): segunda mirada, a mayor resolución, solo a lo que va a salir «aprobada».

Ante cualquier duda (ok=false, error del endpoint, JSON inválido) la captura baja a revisión manual.
"""
import hashlib
import json
import re
from pathlib import Path

from .contrato import Captura, Extraccion, Resultado
from .extraer import _jpeg, resolver_imagen

VERIFICAR_VERSION = "verificar-v1"
LADO = 1024          # si una llamada pasa de TOPE_TOKENS de entrada, baja a LADO_ALTERNO
LADO_ALTERNO = 896
TOPE_TOKENS = 2500

_PROMPT = """Eres un verificador estricto. Fotos: 1ª = PRODUCTO en anaquel, 2ª = ETIQUETA de precio.
Esperado por catálogo: marca "{marca}", producto "{producto}", contenido {contenido}.
Leído antes (puede estar mal): marca "{l_marca}", descripción "{l_desc}", contenido {l_cont}, etiqueta "{l_etq}", precio {l_precio}.
¿Se leen con claridad, sin adivinar, la marca, la descripción, el contenido neto y el precio, y la etiqueta corresponde a este producto exacto (no a otro sabor, tamaño o submarca)?
Ante cualquier duda responde false. Responde SOLO el JSON, sin análisis previo ni texto fuera de él:
{{"ok": bool, "motivo": "máximo 12 palabras"}}"""


def _contenido(cant, unidad) -> str:
    return "no leído" if cant is None else f"{cant:g} {unidad or ''}".strip()


def _prompt(captura: Captura, ext: Extraccion) -> str:
    p, e = ext.producto, ext.etiqueta
    return _PROMPT.format(
        marca=captura.capture_brand or "?", producto=captura.product_name,
        contenido=_contenido(captura.unit_quantity_product, captura.unit_product),
        l_marca=p.marca, l_desc=p.descripcion, l_cont=_contenido(p.contenido_cantidad, p.contenido_unidad),
        l_etq=e.texto_producto, l_precio=e.precio)


def _parsear(texto: str) -> tuple[bool, str]:
    try:
        m = re.search(r"\{.*\}", texto, re.S)
        d = json.loads(m.group(0) if m else texto)
        ok = d["ok"]
        if not isinstance(ok, bool):
            return False, "respuesta inválida del verificador"
        return ok, str(d.get("motivo") or "")[:160]
    except Exception:
        return False, "respuesta inválida del verificador"


def verificar(captura: Captura, ext: Extraccion, dir_datos, cliente) -> tuple[bool, str]:
    """Una llamada. Nunca lanza: error -> (False, motivo)."""
    try:
        prompt = _prompt(captura, ext)
        version = VERIFICAR_VERSION + "-" + hashlib.sha1(prompt.encode()).hexdigest()[:8]
        for lado in (LADO, LADO_ALTERNO):
            imgs = [_jpeg(resolver_imagen(dir_datos, captura.product_file), lado),
                    _jpeg(resolver_imagen(dir_datos, captura.shelf_file), lado)]
            texto, t_in, _, _ = cliente.consultar(captura.capture_id, version, prompt, imgs,
                                                  max_tokens=200, etiqueta="verificar")
            if t_in <= TOPE_TOKENS:
                break
        return _parsear(texto)
    except Exception as e:
        return False, f"error del verificador ({type(e).__name__})"


def aplicar_verificacion(captura: Captura, ext: Extraccion, res: Resultado, dir_datos, cliente) -> Resultado:
    """Solo llama si `res` es aprobada. Si no hay ok=true, la baja a revisión manual."""
    if res.decision != "aprobada" or cliente is None:
        return res
    ok, motivo = verificar(captura, ext, dir_datos, cliente)
    if ok:
        return res
    return res.model_copy(update={
        "decision": "revision_manual", "reason_code": None, "confidence_score": 0.5,
        "explicacion": f"{res.explicacion} Segunda revisión: {motivo or 'sin motivo'}"})
