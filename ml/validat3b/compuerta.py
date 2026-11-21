"""Compuertas locales de aprobación (I3.1): sin tokens, después de decidir(). Nunca convierten nada en «aprobada»."""
from typing import Any, Optional

from .contrato import Resultado

# Fijado con las 100 de desarrollo, 21-nov 11:27 (la falsa 410562 tiene 99; la válida más baja, 970141, 83 → baja a revisión).
UMBRAL_NITIDEZ_ETIQUETA = 100.0


def _a_revision(res: Resultado, frase: str) -> Resultado:
    return res.model_copy(update={"decision": "revision_manual", "reason_code": None,
                                  "confidence_score": 0.5, "explicacion": f"{res.explicacion} {frase}".strip()})


def compuerta(res: Resultado, senales: Optional[dict[str, Any]], esperado: Optional[str] = None) -> Resultado:
    senales = senales or {}
    if senales.get("codigo_coincide") is False:
        return _a_revision(res, f"El código de barras de la foto ({senales.get('codigo_barras_leido')}) "
                                f"no coincide con el registrado ({esperado}).")
    if res.decision == "aprobada":
        nit = senales.get("nitidez_etiqueta")
        if nit is None or nit < UMBRAL_NITIDEZ_ETIQUETA:
            return _a_revision(res, "La etiqueta no se ve con nitidez suficiente para aprobar.")
    return res
