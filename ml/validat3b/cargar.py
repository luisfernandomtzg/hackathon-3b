"""Carga de capturas.csv -> list[Captura]. Códigos de barras como texto; NaN -> None."""
import csv
from pathlib import Path

from .contrato import Captura

_CAMPOS = set(Captura.model_fields)
_FLOAT = {"capture_price", "product_price", "min_product_price", "max_product_price", "unit_quantity_product"}


def _valor(campo: str, v: str):
    v = (v or "").strip()
    if v == "" or v.lower() in ("nan", "none", "null"):
        return None
    if campo in _FLOAT:
        return float(v)
    if campo == "id_product":
        return int(float(v))
    return v


def cargar_capturas(dir_metadatos) -> list[Captura]:
    ruta = Path(dir_metadatos) / "capturas.csv"
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        filas = csv.DictReader(f)  # todo llega como str: los códigos de barras no pierden ceros
        return [Captura(**{k: _valor(k, v) for k, v in fila.items() if k in _CAMPOS}) for fila in filas]
