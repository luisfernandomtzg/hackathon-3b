"""Señales locales sin tokens para Validat3B (Reto 2).

Calcula por captura:
- codigo_barras_leido: decodificación EAN/UPC en foto de producto y luego etiqueta (zxing-cpp)
- codigo_coincide: comparación contra capture_barcode ignorando ceros a la izquierda
- nitidez_producto, nitidez_etiqueta: varianza del laplaciano en grises a 640 px de ancho (numpy)
- ancho y alto de cada foto (fachada, producto, etiqueta)
- huella_fachada: md5 de los bytes de la foto de fachada (para cachear por visita)
"""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path
from typing import Any, Optional

import numpy as np
import zxingcpp
from PIL import Image


def _obtener_campo(captura: Any, campo: str) -> Any:
    """Obtiene un atributo o llave de `captura` (soporta BaseModel/objeto o dict)."""
    if isinstance(captura, dict):
        return captura.get(campo)
    return getattr(captura, campo, None)


def _resolver_ruta_imagen(dir_datos: str | Path, rel_path: Optional[str]) -> Optional[Path]:
    """Resuelve la ruta de una imagen dentro de `dir_datos`."""
    if not rel_path or not isinstance(rel_path, str):
        return None
    base = Path(dir_datos)
    candidatos = [
        base / "imagenes" / rel_path,
        base / rel_path,
        base / "imagenes" / "imagenes" / Path(rel_path).name,
    ]
    for c in candidatos:
        if c.is_file():
            return c
    return None


def _normalizar_codigo(codigo: Optional[str]) -> Optional[str]:
    """Limpia espacios y ceros a la izquierda para comparar códigos EAN/UPC."""
    if codigo is None:
        return None
    limpio = str(codigo).strip()
    if not limpio:
        return None
    sin_ceros = limpio.lstrip("0")
    return sin_ceros if sin_ceros else "0"


def calcular_nitidez_imagen(img: Image.Image, ancho_objetivo: int = 640) -> Optional[float]:
    """Calcula la varianza del laplaciano sobre una imagen Pillow en grises a 640 px de ancho."""
    try:
        gris = img.convert("L")
        w, h = gris.size
        if w <= 0 or h <= 0:
            return None
        nuevo_alto = max(3, int(round(h * (ancho_objetivo / float(w)))))
        gris_redim = gris.resize((ancho_objetivo, nuevo_alto), Image.Resampling.BILINEAR)
        arr = np.asarray(gris_redim, dtype=np.float64)
        if arr.shape[0] < 3 or arr.shape[1] < 3:
            return None
        # Kernel Laplaciano 3x3: [[0, 1, 0], [1, -4, 1], [0, 1, 0]]
        laplaciano = (
            arr[:-2, 1:-1]
            + arr[2:, 1:-1]
            + arr[1:-1, :-2]
            + arr[1:-1, 2:]
            - 4.0 * arr[1:-1, 1:-1]
        )
        return round(float(np.var(laplaciano)), 4)
    except Exception:
        return None


def _leer_codigo_barras_imagen(img: Image.Image) -> Optional[str]:
    """Intenta decodificar un código de barras EAN/UPC con zxing-cpp."""
    try:
        resultados = zxingcpp.read_barcodes(
            img,
            formats=zxingcpp.BarcodeFormat.EANUPC,
            try_rotate=True,
            try_downscale=True,
        )
        for r in resultados:
            texto = (r.text or "").strip()
            if texto:
                return texto
        return None
    except Exception:
        return None


def _dimensiones_y_imagen(ruta: Optional[Path]) -> tuple[Optional[Image.Image], Optional[int], Optional[int]]:
    """Abre una imagen y devuelve (imagen_cargada, ancho, alto), o (None, None, None) ante error."""
    if ruta is None:
        return None, None, None
    try:
        with Image.open(ruta) as im:
            im.load()
            copia = im.copy()
            w, h = copia.size
            return copia, int(w), int(h)
    except Exception:
        return None, None, None


def _md5_archivo(ruta: Optional[Path]) -> Optional[str]:
    """Calcula el hash MD5 en hexadecimal de los bytes de un archivo."""
    if ruta is None:
        return None
    try:
        datos = ruta.read_bytes()
        return hashlib.md5(datos).hexdigest()
    except Exception:
        return None


def senales_locales(captura: Any, dir_datos: str | Path) -> dict[str, Any]:
    """Calcula todas las señales locales sin tokens para una captura.

    Nunca lanza excepción: ante cualquier error en un campo, ese campo vale `None`.
    """
    resultado: dict[str, Any] = {
        "codigo_barras_leido": None,
        "codigo_coincide": None,
        "nitidez_producto": None,
        "nitidez_etiqueta": None,
        "ancho_fachada": None,
        "alto_fachada": None,
        "ancho_producto": None,
        "alto_producto": None,
        "ancho_etiqueta": None,
        "alto_etiqueta": None,
        "ancho": None,
        "alto": None,
        "huella_fachada": None,
    }

    try:
        ruta_fachada = _resolver_ruta_imagen(dir_datos, _obtener_campo(captura, "facade_file"))
        ruta_producto = _resolver_ruta_imagen(dir_datos, _obtener_campo(captura, "product_file"))
        ruta_etiqueta = _resolver_ruta_imagen(dir_datos, _obtener_campo(captura, "shelf_file"))

        # Fachada: dimensiones y huella MD5
        _, w_fac, h_fac = _dimensiones_y_imagen(ruta_fachada)
        resultado["ancho_fachada"] = w_fac
        resultado["alto_fachada"] = h_fac
        resultado["huella_fachada"] = _md5_archivo(ruta_fachada)

        # Producto: dimensiones, nitidez y código de barras
        img_prod, w_prod, h_prod = _dimensiones_y_imagen(ruta_producto)
        resultado["ancho_producto"] = w_prod
        resultado["alto_producto"] = h_prod
        resultado["ancho"] = w_prod
        resultado["alto"] = h_prod
        if img_prod is not None:
            resultado["nitidez_producto"] = calcular_nitidez_imagen(img_prod)

        # Etiqueta: dimensiones, nitidez y código de barras
        img_etiq, w_etiq, h_etiq = _dimensiones_y_imagen(ruta_etiqueta)
        resultado["ancho_etiqueta"] = w_etiq
        resultado["alto_etiqueta"] = h_etiq
        if img_etiq is not None:
            resultado["nitidez_etiqueta"] = calcular_nitidez_imagen(img_etiq)

        # Código de barras: primero en producto, luego en etiqueta
        codigo_leido: Optional[str] = None
        if img_prod is not None:
            codigo_leido = _leer_codigo_barras_imagen(img_prod)
        if codigo_leido is None and img_etiq is not None:
            codigo_leido = _leer_codigo_barras_imagen(img_etiq)
        resultado["codigo_barras_leido"] = codigo_leido

        # Coincidencia contra capture_barcode (ignorando ceros a la izquierda)
        esperado_norm = _normalizar_codigo(_obtener_campo(captura, "capture_barcode"))
        leido_norm = _normalizar_codigo(codigo_leido)
        if leido_norm is not None and esperado_norm is not None:
            resultado["codigo_coincide"] = leido_norm == esperado_norm
        else:
            resultado["codigo_coincide"] = None
    except Exception:
        pass

    return resultado


def _cargar_filas_capturas(dir_datos: Path) -> list[dict[str, Any]]:
    """Carga las filas de `capturas.csv` desde `dir_datos/metadatos/capturas.csv`."""
    candidatos = [
        dir_datos / "metadatos" / "capturas.csv",
        dir_datos / "capturas.csv",
    ]
    ruta_csv: Optional[Path] = None
    for c in candidatos:
        if c.is_file():
            ruta_csv = c
            break
    if ruta_csv is None:
        raise FileNotFoundError(f"No se encontró capturas.csv en {dir_datos}")

    with open(ruta_csv, mode="r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Calcula señales locales sin tokens (código de barras, nitidez, huella de fachada)."
    )
    parser.add_argument(
        "--datos",
        required=True,
        help="Directorio raíz de datos (ej. datos/privado)",
    )
    parser.add_argument(
        "--salida",
        required=True,
        help="Ruta del archivo CSV de salida (ej. salidas/locales.csv)",
    )
    args = parser.parse_args()

    dir_datos = Path(args.datos)
    ruta_salida = Path(args.salida)
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)

    capturas = _cargar_filas_capturas(dir_datos)

    columnas = [
        "capture_id",
        "codigo_barras_leido",
        "codigo_coincide",
        "nitidez_producto",
        "nitidez_etiqueta",
        "ancho_fachada",
        "alto_fachada",
        "ancho_producto",
        "alto_producto",
        "ancho_etiqueta",
        "alto_etiqueta",
        "ancho",
        "alto",
        "huella_fachada",
        "decision_esperada",
        "motivo_rechazo",
    ]

    total = len(capturas)
    codigos_leidos = 0
    codigos_coinciden = 0
    huellas_unicas: set[str] = set()
    nitidez_por_motivo: dict[str, dict[str, list[float]]] = {}

    filas_salida: list[dict[str, Any]] = []
    for cap in capturas:
        senales = senales_locales(cap, dir_datos)
        decision_esp = (cap.get("decision_esperada") or "").strip() or None
        motivo_rech = (cap.get("motivo_rechazo") or "").strip() or None

        if senales["codigo_barras_leido"] is not None:
            codigos_leidos += 1
        if senales["codigo_coincide"] is True:
            codigos_coinciden += 1
        if senales["huella_fachada"]:
            huellas_unicas.add(senales["huella_fachada"])

        etiqueta_motivo = motivo_rech if motivo_rech else "(sin_motivo)"
        grupo = nitidez_por_motivo.setdefault(
            etiqueta_motivo, {"producto": [], "etiqueta": []}
        )
        if senales["nitidez_producto"] is not None:
            grupo["producto"].append(float(senales["nitidez_producto"]))
        if senales["nitidez_etiqueta"] is not None:
            grupo["etiqueta"].append(float(senales["nitidez_etiqueta"]))

        fila = {
            "capture_id": cap.get("capture_id"),
            **senales,
            "decision_esperada": decision_esp,
            "motivo_rechazo": motivo_rech,
        }
        filas_salida.append(fila)

    with open(ruta_salida, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columnas)
        writer.writeheader()
        writer.writerows(filas_salida)

    print(
        f"Capturas procesadas: {total} | "
        f"Código leído: {codigos_leidos} | "
        f"Código coincide: {codigos_coinciden} | "
        f"Fachadas únicas (md5): {len(huellas_unicas)}"
    )
    print("Mediana de nitidez por motivo_rechazo:")
    for motivo in sorted(nitidez_por_motivo.keys()):
        vals_p = nitidez_por_motivo[motivo]["producto"]
        vals_e = nitidez_por_motivo[motivo]["etiqueta"]
        med_p = float(np.median(vals_p)) if vals_p else 0.0
        med_e = float(np.median(vals_e)) if vals_e else 0.0
        n_grupo = max(len(vals_p), len(vals_e))
        print(
            f"  - {motivo} (n={n_grupo}): "
            f"nitidez_producto={med_p:.2f} · nitidez_etiqueta={med_e:.2f}"
        )


if __name__ == "__main__":
    main()
