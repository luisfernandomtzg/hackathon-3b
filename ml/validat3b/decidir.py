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
from ml.validat3b.normalizar import a_base, parecido, pesos_del_nombre

# Umbrales (constantes de decisión)
UMBRAL_NO_COINCIDE = 0.4      # parecido < 0.4 → producto distinto
UMBRAL_ZONA_GRIS = 0.7        # 0.4–0.7 → revisión manual
UMBRAL_ETIQUETA_AJENA = 0.6   # texto de etiqueta vs producto esperado (0.3 dejaba pasar CAP-206200)
TOLERANCIA_CONTENIDO = 0.02   # 2 %
# Medido con salidas-sp2: aceptar el «(total: NNNg)» del nombre rescata 2 válidas pero aprueba 3 inválidas
# (costo +24 neto). Apagado hasta que haya una señal que distinga ambos casos.
ACEPTAR_PESO_TOTAL = False

# --- Foto de la etiqueta (S005, lectura v3). Medido con salidas/sp11 (100 de desarrollo, 13:55):
# las 33 aprobadas reales tienen el letrero nítido y a ≥ 25 % del ancho; con ≤ 20 %, «lejano» o «borrosa»
# hay 16 rechazadas reales, 4 de revisión reales y 0 aprobadas reales.
ANCHO_ETIQUETA_LEJANA = 20.0   # % del ancho de la foto: de aquí hacia abajo el letrero está lejos → rechazo
ANCHO_ETIQUETA_APROBAR = 30.0  # para aprobar, el letrero ocupa al menos esto (y se lee nítido)
# Con el letrero cerca y nítido, que el nombre del catálogo y el del empaque/letrero se redacten distinto
# («Jabón de tocador rosa» / «Jabon rosa Rosa Venus») no frena la aprobación SI el propio letrero dice el
# contenido esperado. Medido en sp11: 8 capturas, 8 aprobadas reales, 0 de otra clase.
APROBAR_REDACCION_DISTINTA = True
# Lo mismo para «varios productos en la foto» y «otros precios en el letrero» (este exige además que el precio
# leído sea el que tecleó el capturista). Medido en sp11: 3 de 3 aprobadas reales. Apagado: son solo 3 casos.
APROBAR_FOTO_CON_VECINOS = False

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


def _ambiguedad_de_contenido(leido: tuple, esperado: tuple, nombre: Optional[str],
                             texto_etiqueta: Optional[str] = None) -> Optional[str]:
    """Frase si la diferencia de contenido es una ambigüedad del catálogo; None si es una diferencia real."""
    for total in pesos_del_nombre(nombre):
        if leido[1] == total[1] and total[0] > 0 and abs(leido[0] - total[0]) / total[0] <= TOLERANCIA_CONTENIDO:
            return (f"En la foto se lee {leido[0]:g} {leido[1]}, que es el peso total que declara el nombre esperado "
                    f"({nombre}), no el contenido neto ({esperado[0]:g} {esperado[1]}).")
    if {leido[1], esperado[1]} == {"g", "ml"} and leido[0] == esperado[0]:
        return (f"En la foto se lee {leido[0]:g} {leido[1]} y se esperaban {esperado[0]:g} {esperado[1]}: "
                f"la misma cantidad con otra unidad.")
    # (S005, sp11) El empaque y el letrero dicen lo mismo y solo el catálogo difiere (p. ej. peso neto contra drenado).
    if _etiqueta_dice_contenido(texto_etiqueta, leido):
        return (f"En la foto se lee {leido[0]:g} {leido[1]} y el letrero dice lo mismo; el catálogo espera "
                f"{esperado[0]:g} {esperado[1]}. La evidencia de total coincide entre sí, no con el catálogo.")
    return None


_RE_CONTENIDO = __import__("re").compile(r"(\d+(?:[.,]\d+)?)\s*(kg|kgs|kilo|kilos|k|gr|grs|gramos|g|ml|lts|lt|litros|litro|l|pzas|pza|pz)\b")


def _etiqueta_dice_contenido(texto_etiqueta: Optional[str], esperado: Optional[tuple]) -> bool:
    """¿El letrero trae impreso el contenido esperado? («… 1 KG», «950ML», «64 Gramos»)."""
    if not texto_etiqueta or esperado is None:
        return False
    for num, uni in _RE_CONTENIDO.findall(texto_etiqueta.lower()):
        uni = {"k": "kg", "kgs": "kg", "grs": "g", "pzas": "pza"}.get(uni, uni)
        leido = a_base(float(num.replace(",", ".")), uni)
        if leido and leido[1] == esperado[1] and esperado[0] > 0 \
                and abs(leido[0] - esperado[0]) / esperado[0] <= TOLERANCIA_CONTENIDO:
            return True
    return False


def _foto_etiqueta(e) -> str:
    """'mala' (lejana o borrosa: se rechaza), 'buena' (se puede aprobar) o 'regular' (no se aprueba ni se rechaza)."""
    if e.nitidez == "borrosa" or e.encuadre == "lejano" or (e.ancho_pct is not None and e.ancho_pct <= ANCHO_ETIQUETA_LEJANA):
        return "mala"
    if e.nitidez == "nitida" and e.encuadre in ("cercano", "medio") \
            and e.ancho_pct is not None and e.ancho_pct >= ANCHO_ETIQUETA_APROBAR:
        return "buena"
    return "regular"  # incluye lecturas sin estos campos (v2): nunca se aprueba a ciegas


def decidir_con_regla(captura: Captura, x: Extraccion) -> tuple[Resultado, int]:
    """Igual que decidir(), pero devuelve también el número de la regla que disparó (1–12; 0 = ninguna)."""
    p = x.producto
    e = x.etiqueta

    # 1. Sin lectura del modelo
    if x.origen in ("error", "sin_modelo"):
        return _resultado(captura, x, "revision_manual", RC_SIN_LECTURA, CONF_REVISION, _val(),
                          "No se pudo leer la captura; hace falta revisarla a mano."), 1

    # 2. Foto de pantalla
    if p.foto_de_pantalla:
        return _resultado(captura, x, "rechazada", RC_PANTALLA, CONF_DURA, _val(producto="falla"),
                          "La foto del producto es una pantalla, no el producto físico."), 2

    # 3. No hay producto visible
    if not p.hay_producto:
        return _resultado(captura, x, "rechazada", RC_NO_VISIBLE, CONF_DURA, _val(producto="falla"),
                          "No se ve el producto en la foto."), 3

    # 4. Borrosa
    if p.nitidez == "borrosa":
        return _resultado(captura, x, "rechazada", RC_BORROSA, CONF_DURA, _val(producto="falla"),
                          "La foto del producto está borrosa; no se puede leer."), 4

    # 5. Lejana
    if p.encuadre == "lejano":
        return _resultado(captura, x, "rechazada", RC_LEJANA, CONF_DURA, _val(producto="falla"),
                          "El producto sale muy lejos; no se alcanza a leer."), 5

    # 5b. (S005) La FOTO DE LA ETIQUETA está lejos o borrosa: es lo que el analista llama captura lejana/borrosa.
    foto_etq = _foto_etiqueta(e)
    if e.hay_etiqueta and foto_etq == "mala":
        if e.nitidez == "borrosa":
            return _resultado(captura, x, "rechazada", RC_BORROSA, CONF_DURA, _val(evidencia="falla"),
                              "La foto de la etiqueta de precio está borrosa; no se lee el letrero."), 5
        ancho = f" (ocupa ~{e.ancho_pct:.0f} % del ancho de la foto)" if e.ancho_pct is not None else ""
        return _resultado(captura, x, "rechazada", RC_LEJANA, CONF_DURA, _val(evidencia="falla"),
                          f"La etiqueta de precio sale muy lejos{ancho}; no se puede validar el letrero."), 5

    # 6. Descripción o contenido incompletos
    esperado_tiene_contenido = captura.unit_quantity_product is not None
    if _vacio(p.marca) or _vacio(p.descripcion):
        return _resultado(captura, x, "rechazada", RC_INCOMPLETA, CONF_CLARA, _val(producto="falla"),
                          "No se lee completa la marca o la descripción del producto."), 6
    if p.contenido_cantidad is None and esperado_tiene_contenido:
        rc = RC_INCOMPLETA  # medido con salidas: 4 aciertos contra 2 con LEJANA
        return _resultado(captura, x, "rechazada", rc, CONF_CLARA, _val(producto="falla"),
                          "No se lee el contenido (g/ml/piezas) del producto."), 6

    # 7. Coincidencia con lo esperado
    score_marca = parecido(p.marca, captura.capture_brand) if captura.capture_brand else 1.0
    # Desde el nombre esperado: cuántas de sus palabras aparecen en la marca + descripción leídas.
    score_desc = parecido(p.descripcion, captura.product_name)
    peor = min(score_marca, score_desc)

    contenido_distinto = False
    contenido_incomparable = False
    contenido_ambiguo = None  # frase: el contenido leído difiere, pero por una ambigüedad del catálogo, no de la foto
    if esperado_tiene_contenido and p.contenido_cantidad is not None:
        leido = a_base(p.contenido_cantidad, p.contenido_unidad)
        # Se acepta el peso esperado o el «(total: NNNg)» del nombre, si lo trae.
        aceptados = [a_base(captura.unit_quantity_product, captura.unit_product)]
        if ACEPTAR_PESO_TOTAL:
            aceptados += pesos_del_nombre(captura.product_name)
        aceptados = [a for a in aceptados if a is not None]
        if leido is None or not aceptados:
            contenido_incomparable = True
        else:
            coincide = False
            for esperado in aceptados:
                if leido[1] == esperado[1]:
                    mayor = max(leido[0], esperado[0])
                    if mayor == 0 or abs(leido[0] - esperado[0]) / mayor <= TOLERANCIA_CONTENIDO:
                        coincide = True
            contenido_distinto = not coincide
            if contenido_distinto:
                contenido_ambiguo = _ambiguedad_de_contenido(leido, aceptados[0], captura.product_name, e.texto_producto)

    # 7a. (S005) El contenido no coincide, pero la diferencia la explica el catálogo: se leyó el peso TOTAL que el
    # propio nombre esperado declara («485g (total: 820g)»), o el mismo número con g en vez de ml. No es evidencia
    # de mala foto ni de otro producto: decide una persona. Medido con salidas-sp8: 6 capturas (2 aprobadas reales,
    # 4 de revisión reales, 0 rechazadas reales) dejaban de rechazarse. Nunca aprueba.
    if contenido_ambiguo and (peor >= UMBRAL_NO_COINCIDE or "total" in contenido_ambiguo):
        return _resultado(captura, x, "revision_manual", RC_NO_COINCIDE, CONF_REVISION, _val(producto="falla"),
                          f"{contenido_ambiguo} No alcanza para rechazar ni para aprobar; pasa a revisión manual."), 7

    if contenido_distinto or peor < UMBRAL_NO_COINCIDE:
        return _resultado(
            captura, x, "rechazada", RC_LEJANA, CONF_CLARA, _val(producto="falla"),  # medido: 7 de 11 son lejanas
            f"No se distingue con claridad el producto en la foto (captura lejana o poco nítida): "
            f"se lee marca «{p.marca}», descripción «{p.descripcion}» y "
            f"{p.contenido_cantidad or '—'} {p.contenido_unidad or ''}; "
            f"se esperaba ({captura.capture_brand or '—'}, {captura.product_name}, "
            f"{captura.unit_quantity_product or '—'} {captura.unit_product or ''}).",
        ), 7
    esperado_base = a_base(captura.unit_quantity_product, captura.unit_product) if esperado_tiene_contenido else None
    letrero_confirma = foto_etq == "buena" and _etiqueta_dice_contenido(e.texto_producto, esperado_base)
    redaccion_salvada = (APROBAR_REDACCION_DISTINTA and letrero_confirma and score_marca >= UMBRAL_ZONA_GRIS
                         and not contenido_incomparable)
    if (peor < UMBRAL_ZONA_GRIS and not redaccion_salvada) or contenido_incomparable:
        return _resultado(captura, x, "revision_manual", RC_NO_COINCIDE, CONF_REVISION, _val(producto="falla"),
                          f"La coincidencia con el producto esperado es dudosa (marca «{p.marca}», "
                          f"descripción «{p.descripcion}»); pasa a revisión manual."), 7

    # 8. Sin etiqueta, sin precio o ilegible
    if not e.hay_etiqueta or e.precio is None or not e.legible:
        return _resultado(captura, x, "rechazada", RC_SIN_ETIQUETA, CONF_DURA,
                          _val(evidencia="falla"),
                          "No hay etiqueta de precio legible en la foto."), 8

    # 9. Etiqueta de otro producto
    if not _vacio(e.texto_producto):
        referencia = f"{captura.product_name} {p.marca or ''}"
        if parecido(e.texto_producto, referencia) < UMBRAL_ETIQUETA_AJENA and not redaccion_salvada:
            return _resultado(captura, x, "revision_manual", RC_ETIQUETA_AJENA, CONF_REVISION,
                              _val(evidencia="falla"),
                              f"La etiqueta dice «{e.texto_producto}», que no corresponde al producto esperado "
                              f"({captura.product_name})."), 9

    # 10. Precio fuera de rango
    minimo, maximo = captura.min_product_price, captura.max_product_price
    if minimo and maximo and minimo > 0 and maximo > 0 and not (minimo <= e.precio <= maximo):
        return _resultado(captura, x, "revision_manual", RC_PRECIO_RANGO, CONF_REVISION,
                          _val(evidencia="falla"),
                          f"La etiqueta dice ${e.precio:.2f}, fuera del rango esperado "
                          f"(${minimo:.2f}–${maximo:.2f})."), 10

    # 11. Dudas visuales
    vecinos_salvados = (APROBAR_FOTO_CON_VECINOS and letrero_confirma and peor >= UMBRAL_ZONA_GRIS
                        and not (p.varios_productos and e.otros_precios)
                        and (not e.otros_precios or (captura.capture_price is not None
                                                     and abs(e.precio - captura.capture_price) < 0.005)))
    if p.nitidez == "dudosa" or p.encuadre == "medio" or ((p.varios_productos or e.otros_precios) and not vecinos_salvados):
        return _resultado(captura, x, "revision_manual", None, CONF_REVISION, _val(),
                          "La foto es dudosa (nitidez, encuadre, varios productos) o la etiqueta trae otros precios; pasa a revisión manual."), 11

    # 11b. (S005) Sin el letrero cerca y nítido no se aprueba: es la causa medida de las aprobadas falsas.
    if foto_etq != "buena":
        return _resultado(captura, x, "revision_manual", None, CONF_REVISION, _val(evidencia="falla"),
                          "El producto coincide, pero la etiqueta de precio no se ve lo bastante cerca y nítida "
                          "para aprobar sin revisión."), 11

    # 12. Todo claro
    tipo = {"oferta": " de oferta", "volumen": " por volumen"}.get(e.tipo_precio or "", "")
    return _resultado(
        captura, x, "aprobada", None, CONF_DURA, _val(),
        f"La etiqueta dice ${e.precio:.2f}{tipo} y el producto leído coincide con lo esperado "
        f"({p.marca}, {captura.product_name}).",
    ), 12


def decidir(captura: Captura, x: Extraccion) -> Resultado:
    return decidir_con_regla(captura, x)[0]

