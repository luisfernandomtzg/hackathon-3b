"""PROVISIONAL (Integrador): todo a revisión manual. Núcleo entrega decidir.py en N1 y correr.py lo prefiere."""
from .contrato import RC_SIN_LECTURA, Captura, Extraccion, Resultado, Validaciones


def decidir(captura: Captura, extraccion: Extraccion) -> Resultado:
    return Resultado(capture_id=captura.capture_id, decision="revision_manual", confidence_score=0.0,
                     reason_code=RC_SIN_LECTURA, validaciones=Validaciones(),
                     precio_detectado=extraccion.etiqueta.precio,
                     codigo_barras_detectado=extraccion.codigo_barras_leido,
                     explicacion="Decisión provisional: sin reglas, se envía a revisión manual.")
