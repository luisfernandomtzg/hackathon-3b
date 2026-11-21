"""Consenso de lecturas (I5): una aprobada solo queda aprobada si las lecturas independientes adicionales también la aprueban.

El modelo no admite temperature=0 (el endpoint rechaza «temperature: Extra inputs are not permitted»), así que dos
lecturas de la misma foto difieren y su acuerdo es la señal de estabilidad. Solo se llama a las que salen aprobadas
(~10-15 % de las capturas) y se corta en la primera lectura que no apruebe. Ante error o desacuerdo: revisión manual. Nunca convierte nada en aprobada.
"""
from .compuerta import compuerta
from .contrato import Captura, Extraccion, Resultado
from .extraer import extraer

LECTURAS_PARA_APROBAR = 3  # unánime: tienen que aprobar TODAS (no «2 de 3», que sería más permisivo)
VARIANTES = ["-b", "-c", "-d", "-e"]  # una llave de caché por lectura adicional
VARIANTE = VARIANTES[0]


def aplicar_consenso(captura: Captura, ext: Extraccion, res: Resultado, dir_datos, cliente, decidir_fn) -> Resultado:
    """La lectura 1 ya aprobó (`res`). Se piden las siguientes una a una y se corta en la primera que no apruebe."""
    if res.decision != "aprobada" or cliente is None:
        return res
    motivo = None
    for n, variante in enumerate(VARIANTES[: LECTURAS_PARA_APROBAR - 1], start=2):
        try:
            ext2 = extraer(captura, dir_datos, cliente, variante=variante)
            ext2.senales = ext.senales  # las señales locales no dependen del modelo
            res2 = Resultado.model_validate(decidir_fn(captura, ext2).model_dump())
            res2 = compuerta(res2, ext2.senales, captura.capture_barcode)
            if res2.decision != "aprobada":
                motivo = f"la lectura {n} de {LECTURAS_PARA_APROBAR} no confirma la aprobación"
                break
        except Exception as e:
            motivo = f"falló la lectura {n} de {LECTURAS_PARA_APROBAR} ({type(e).__name__})"
            break
    if motivo is None:
        return res
    return res.model_copy(update={
        "decision": "revision_manual", "reason_code": None, "confidence_score": 0.5,
        "explicacion": f"{res.explicacion} Consenso: {motivo}."})
