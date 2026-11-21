"""Carga de capturas (csv o json) -> list[Captura]. Códigos de barras como texto; NaN -> None."""
import csv
import json
from pathlib import Path

from .contrato import Captura

_CAMPOS = set(Captura.model_fields)
_FLOAT = {"capture_price", "product_price", "min_product_price", "max_product_price", "unit_quantity_product"}
_REQ_STR = [k for k, f in Captura.model_fields.items() if f.is_required() and k != "id_product"]


def _valor(campo: str, v):
    if isinstance(v, str):
        v = v.strip()
    if v is None or v == "" or (isinstance(v, str) and v.lower() in ("nan", "none", "null")):
        return None
    if campo in _FLOAT:
        return float(v)
    if campo == "id_product":
        return int(float(v))
    if isinstance(v, float) and v == int(v):  # json: 7501372812565.0 -> "7501372812565"
        return str(int(v))
    return str(v)


def localizar_capturas(ruta) -> Path:
    """Acepta el archivo, la carpeta o su carpeta `metadatos`; prefiere el csv (el json pierde ceros a la izquierda)."""
    ruta = Path(ruta)
    if ruta.is_file():
        return ruta
    for nombre in ("capturas.csv", "metadatos/capturas.csv", "capturas.json", "metadatos/capturas.json"):
        if (ruta / nombre).is_file():
            return ruta / nombre
    for nombre in ("capturas.csv", "capturas.json"):
        hallados = sorted(ruta.rglob(nombre), key=lambda q: len(q.parts))
        if hallados:
            return hallados[0]
    raise FileNotFoundError(f"No encontré capturas.csv ni capturas.json en {ruta}")


def _filas(archivo: Path) -> list[dict]:
    if archivo.suffix.lower() == ".json":
        datos = json.loads(archivo.read_text(encoding="utf-8-sig"))
        return datos["capturas"] if isinstance(datos, dict) and "capturas" in datos else datos
    with open(archivo, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))  # todo llega como str: los códigos de barras no pierden ceros


def cargar_capturas(dir_metadatos) -> list[Captura]:
    """Una Captura por fila, sin omitir ninguna: lo que falte se rellena vacío (la captura saldrá a revisión)."""
    capturas = []
    for fila in _filas(localizar_capturas(dir_metadatos)):
        d = {k: _valor(k, v) for k, v in fila.items() if k in _CAMPOS}
        if not d.get("capture_id"):
            raise ValueError(f"fila sin capture_id: {str(fila)[:100]}")
        for k in _REQ_STR:
            d.setdefault(k, None)
            if d[k] is None:
                d[k] = ""
        d.setdefault("id_product", 0)
        if d["id_product"] is None:
            d["id_product"] = 0
        capturas.append(Captura(**d))
    return capturas
