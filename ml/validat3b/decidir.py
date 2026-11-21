"""decidir(): de la lectura del modelo a la decisión, con reglas puras.

Principio todo o nada: solo se aprueba con evidencia completa y clara; ante duda nunca se aprueba.
Las reglas se evalúan en orden; la primera que se cumple decide.
"""
from typing import Optional

from ml.validat3b.contrato import (
    Captura, Extraccion, Resultado, Validaciones,
    RC_BORROSA, RC_LEJANA, RC_INCOMPLETA, RC_NO_COINCIDE, RC_NO_VISIBLE, RC_PANTALLA,
    RC_SIN_ETIQUETA, RC_ETIQUETA_AJENA, RC_PRECIO_RANGO, RC_SIN_LECTURA,
)
from ml.validat3b.normalizar import a_base, parecido

# Umbrales (constantes de decisión)
UMBRAL_NO_COINCIDE = 0.4      # parecido < 0.4 → producto distinto
UMBRAL_ZONA_GRIS = 0.7        # 0.4–0.7 → revisión manual
UMBRAL_ETIQUETA_AJENA = 0.3   # texto de etiqueta vs producto esperado
TOLERANCIA_CONTENIDO = 0.02   # 2 %

CONF_DURA = 0.95      # reglas 2–5, 8 y 12 con todo nítido
CONF_CLARA = 0.8      # reglas 6–7 claras
CONF_REVISION = 0.5   # toda revision_manual


def _val(producto: str = "ok", evidencia: str = "ok") -> Validaciones:
    return Validaciones(producto=producto, evidencia_precio=evidencia)


def _resultado(captura: Captura, x: Extraccion, decision: str, rc: Optional[str],
               conf: float, validaciones: Validaciones, explicacion: str) -> Resultado:
    return Resultado(
        capture_id=captura.capture_id,
        decision=decision,
        confidence_score=conf,
        reason_code=rc,
        validaciones=validaciones,
        precio_detectado=x.etiqueta.precio,
        codigo_barras_detectado=x.codigo_barras_leido or captura.capture_barcode,
        explicacion=explicacion,
    )


def _vacio(s: Optional[str]) -> bool:
    return s is None or not s.strip()


def decidir(captura: Captura, x: Extraccion) -> Resultado:
    p = x.producto
    e = x.etiqueta

    # 1. Sin lectura del modelo
    if x.origen in ("error", "sin_modelo"):
        return _resultado(captura, x, "revision_manual", RC_SIN_LECTURA, CONF_REVISION, _val(),
                          f"No hubo lectura utilizable del modelo (origen: {x.origen}).")

    # 2. Foto de pantalla
    if p.foto_de_pantalla:
        return _resultado(captura, x, "rechazada", RC_PANTALLA, CONF_DURA, _val(producto="falla"),
                          "La foto del producto es una pantalla, no el producto físico.")

    # 3. No hay producto visible
    if not p.hay_producto:
        return _resultado(captura, x, "rechazada", RC_NO_VISIBLE, CONF_DURA, _val(producto="falla"),
                          "No se ve el producto en la foto.")

    # 4. Borrosa
    if p.nitidez == "borrosa":
        return _resultado(captura, x, "rechazada", RC_BORROSA, CONF_DURA, _val(producto="falla"),
                          "La foto del producto está borrosa; no se puede leer.")

    # 5. Lejana
    if p.encuadre == "lejano":
        return _resultado(captura, x, "rechazada", RC_LEJANA, CONF_DURA, _val(producto="falla"),
                          "El producto sale muy lejos; no se alcanza a leer.")

    # 6. Descripción o contenido incompletos
    esperado_tiene_contenido = captura.unit_quantity_product is not None
    if _vacio(p.marca) or _vacio(p.descripcion):
        return _resultado(captura, x, "rechazada", RC_INCOMPLETA, CONF_CLARA, _val(producto="falla"),
                          "No se lee completa la marca o la descripción del producto.")
    if p.contenido_cantidad is None and esperado_tiene_contenido:
        rc = RC_LEJANA if (p.encuadre != "cercano" or p.varios_productos) else RC_INCOMPLETA
        return _resultado(captura, x, "rechazada", rc, CONF_CLARA, _val(producto="falla"),
                          "No se lee el contenido (g/ml/piezas) del producto.")

    # 7. Coincidencia con lo esperado
    score_marca = parecido(p.marca, captura.capture_brand) if captura.capture_brand else 1.0
    score_desc = parecido(p.descripcion, captura.product_name)
    peor = min(score_marca, score_desc)

    contenido_distinto = False
    contenido_incomparable = False
    if esperado_tiene_contenido and p.contenido_cantidad is not None:
        leido = a_base(p.contenido_cantidad, p.contenido_unidad)
        esperado = a_base(captura.unit_quantity_product, captura.unit_product)
        if leido is None or esperado is None:
            contenido_incomparable = True
        elif leido[1] != esperado[1]:
            contenido_distinto = True
        else:
            mayor = max(leido[0], esperado[0])
            if mayor > 0 and abs(leido[0] - esperado[0]) / mayor > TOLERANCIA_CONTENIDO:
                contenido_distinto = True

    if contenido_distinto or peor < UMBRAL_NO_COINCIDE:
        return _resultado(
            captura, x, "rechazada", RC_NO_COINCIDE, CONF_CLARA, _val(producto="falla"),
            f"El producto lee marca «{p.marca}», descripción «{p.descripcion}» y "
            f"{p.contenido_cantidad or '—'} {p.contenido_unidad or ''}; no coincide con lo esperado "
            f"({captura.capture_brand or '—'}, {captura.product_name}, "
            f"{captura.unit_quantity_product or '—'} {captura.unit_product or ''}).",
        )
    if peor < UMBRAL_ZONA_GRIS or contenido_incomparable:
        return _resultado(captura, x, "revision_manual", RC_NO_COINCIDE, CONF_REVISION, _val(producto="falla"),
                          f"La coincidencia con el producto esperado es dudosa (marca «{p.marca}», "
                          f"descripción «{p.descripcion}»); pasa a revisión manual.")

    # 8. Sin etiqueta, sin precio o ilegible
    if not e.hay_etiqueta or e.precio is None or not e.legible:
        return _resultado(captura, x, "rechazada", RC_SIN_ETIQUETA, CONF_DURA,
                          _val(evidencia="falla"),
                          "No hay etiqueta de precio legible en la foto.")

    # 9. Etiqueta de otro producto
    if not _vacio(e.texto_producto):
        referencia = f"{captura.product_name} {p.marca or ''}"
        if parecido(e.texto_producto, referencia) < UMBRAL_ETIQUETA_AJENA:
            return _resultado(captura, x, "revision_manual", RC_ETIQUETA_AJENA, CONF_REVISION,
                              _val(evidencia="falla"),
                              f"La etiqueta dice «{e.texto_producto}», que no corresponde al producto esperado "
                              f"({captura.product_name}).")

    # 10. Precio fuera de rango
    minimo, maximo = captura.min_product_price, captura.max_product_price
    if minimo and maximo and minimo > 0 and maximo > 0 and not (minimo <= e.precio <= maximo):
        return _resultado(captura, x, "revision_manual", RC_PRECIO_RANGO, CONF_REVISION,
                          _val(evidencia="falla"),
                          f"La etiqueta dice ${e.precio:.2f}, fuera del rango esperado "
                          f"(${minimo:.2f}–${maximo:.2f}).")

    # 11. Dudas visuales
    if p.nitidez == "dudosa" or p.encuadre == "medio" or p.varios_productos:
        return _resultado(captura, x, "revision_manual", None, CONF_REVISION, _val(),
                          "La foto es dudosa (nitidez, encuadre o varios productos); pasa a revisión manual.")

    # 12. Todo claro
    return _resultado(
        captura, x, "aprobada", None, CONF_DURA, _val(),
        f"La etiqueta dice ${e.precio:.2f} y el producto leído coincide con lo esperado "
        f"({p.marca}, {captura.product_name}).",
    )
