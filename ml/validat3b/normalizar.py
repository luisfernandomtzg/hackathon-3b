"""Normalización de texto y unidades para decidir(). Funciones puras: sin red, sin archivos."""
import difflib
import re
import unicodedata
from typing import Optional

_UNIDADES = {
    "g": ("g", 1.0), "gr": ("g", 1.0), "gramo": ("g", 1.0), "gramos": ("g", 1.0),
    "kg": ("g", 1000.0), "kilo": ("g", 1000.0), "kilos": ("g", 1000.0),
    "kilogramo": ("g", 1000.0), "kilogramos": ("g", 1000.0),
    "ml": ("ml", 1.0), "mililitro": ("ml", 1.0), "mililitros": ("ml", 1.0),
    "l": ("ml", 1000.0), "lt": ("ml", 1000.0), "lts": ("ml", 1000.0),
    "litro": ("ml", 1000.0), "litros": ("ml", 1000.0),
    "pza": ("pza", 1.0), "pz": ("pza", 1.0), "pieza": ("pza", 1.0), "piezas": ("pza", 1.0),
    "unidad": ("pza", 1.0), "unidades": ("pza", 1.0),
}


def texto(s: Optional[str]) -> str:
    """Minúsculas, sin acentos, sin signos; espacios colapsados."""
    if not s:
        return ""
    sin_acento = unicodedata.normalize("NFKD", s)
    sin_acento = "".join(c for c in sin_acento if not unicodedata.combining(c))
    limpio = re.sub(r"[^a-z0-9]+", " ", sin_acento.lower())
    return " ".join(limpio.split())


def _palabra_parecida(p: str, candidatas: list[str]) -> bool:
    for c in candidatas:
        if p == c:
            return True
        if difflib.SequenceMatcher(None, p, c).ratio() >= 0.8:
            return True
    return False


def parecido(a: Optional[str], b: Optional[str]) -> float:
    """0–1: proporción de palabras de la más corta que aparecen en la otra (tolera faltas de ortografía)."""
    pa, pb = texto(a).split(), texto(b).split()
    if not pa or not pb:
        return 0.0
    corta, larga = (pa, pb) if len(pa) <= len(pb) else (pb, pa)
    encontradas = sum(1 for p in corta if _palabra_parecida(p, larga))
    return encontradas / len(corta)


def a_base(cantidad: Optional[float], unidad: Optional[str]) -> Optional[tuple[float, str]]:
    """Convierte a g, ml o pza. None si no hay cantidad o la unidad no se reconoce."""
    if cantidad is None or not unidad:
        return None
    entrada = _UNIDADES.get(texto(unidad))
    if entrada is None:
        return None
    base, factor = entrada
    return cantidad * factor, base


def pesos_del_nombre(nombre: Optional[str]) -> list[tuple[float, str]]:
    """Pesos explícitos en el nombre: «(total: 820g)» → [(820.0, 'g')]. Lista vacía si no hay."""
    if not nombre:
        return []
    m = re.search(r"total:?\s*(\d+(?:[.,]\d+)?)\s*(kg|g|ml|l)\b", nombre.lower())
    if not m:
        return []
    cantidad = float(m.group(1).replace(",", "."))
    base = a_base(cantidad, m.group(2))
    return [base] if base else []
