"""Consenso de lecturas (I5): una aprobada solo queda aprobada si una SEGUNDA lectura independiente también la aprueba.

El modelo no admite temperature=0 (el endpoint rechaza «temperature: Extra inputs are not permitted»), así que dos
lecturas de la misma foto difieren y su acuerdo es la señal de estabilidad. Solo se llama a las que salen aprobadas
(~10-15 % de las capturas). Ante error o desacuerdo: revisión manual. Nunca convierte nada en aprobada.
"""
from .compuerta import compuerta
from .contrato import Captura, Extraccion, Resultado
from .extraer import extraer

VARIANTE = "-b"  # llave de caché distinta: otra lectura de las mismas fotos


def aplicar_consenso(captura: Captura, ext: Extraccion, res: Resultado, dir_datos, cliente, decidir_fn) -> Resultado:
    if res.decision != "aprobada" or cliente is None:
        return res
    try:
        ext2 = extraer(captura, dir_datos, cliente, variante=VARIANTE)
        ext2.senales = ext.senales  # las señales locales no dependen del modelo
        res2 = Resultado.model_validate(decidir_fn(captura, ext2).model_dump())
        res2 = compuerta(res2, ext2.senales, captura.capture_barcode)
        confirmada = res2.decision == "aprobada"
        motivo = "la segunda lectura no confirma la aprobación"
    except Exception as e:
        confirmada, motivo = False, f"falló la segunda lectura ({type(e).__name__})"
    if confirmada:
        return res
    return res.model_copy(update={
        "decision": "revision_manual", "reason_code": None, "confidence_score": 0.5,
        "explicacion": f"{res.explicacion} Consenso: {motivo}."})
