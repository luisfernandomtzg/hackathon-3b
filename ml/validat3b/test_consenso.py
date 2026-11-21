"""Pruebas del consenso. Cliente falso y datos inventados; no usa datos de 3B."""
import unittest
from unittest import mock

from ml.validat3b import consenso, correr
from ml.validat3b.contrato import Extraccion, Resultado, Validaciones
from ml.validat3b.test_decidir import captura, lectura_etiqueta, lectura_producto

BUENAS = {"codigo_coincide": True, "nitidez_etiqueta": 300.0, "codigo_barras_leido": "7501000000011"}


def res(decision):
    return Resultado(capture_id="CAP-TEST-1", decision=decision, confidence_score=0.9,
                     reason_code=None if decision == "aprobada" else "CAPTURA_LEJANA",
                     validaciones=Validaciones(), explicacion="Decidido por reglas.")


def ext():
    return Extraccion(capture_id="CAP-TEST-1", producto=lectura_producto(), etiqueta=lectura_etiqueta(), senales=BUENAS)


def aplicar(decision_original, decision_segunda=None, error=None, decisiones=None):
    decidir_fn = mock.Mock(side_effect=[res(d) for d in decisiones]) if decisiones else         mock.Mock(return_value=res(decision_segunda or "aprobada"))
    with mock.patch.object(consenso, "extraer", side_effect=error, return_value=ext()) as ex:
        out = consenso.aplicar_consenso(captura(), ext(), res(decision_original), "x", object(), decidir_fn)
    return out, ex


class PruebasConsenso(unittest.TestCase):
    def test_segunda_lectura_aprueba_sigue_aprobada(self):
        out, ex = aplicar("aprobada", "aprobada")
        self.assertEqual(out.decision, "aprobada")
        self.assertEqual([c.kwargs["variante"] for c in ex.call_args_list], ["-b", "-c"])  # cada lectura, su llave

    def test_segunda_lectura_no_aprueba_baja_a_revision(self):
        for d in ("revision_manual", "rechazada"):
            out, _ = aplicar("aprobada", d)
            self.assertEqual((out.decision, out.reason_code, out.confidence_score), ("revision_manual", None, 0.5), d)
            self.assertIn("Consenso", out.explicacion)

    def test_una_de_tres_que_no_aprueba_baja_a_revision(self):
        for decisiones in (["aprobada", "revision_manual"], ["revision_manual", "aprobada"]):
            out, _ = aplicar("aprobada", decisiones=decisiones)
            self.assertEqual(out.decision, "revision_manual", decisiones)
            self.assertIn("Consenso", out.explicacion)

    def test_tercera_lectura_no_se_llama_si_la_segunda_no_aprueba(self):
        """Se pone roja si la tercera se pide siempre."""
        out, ex = aplicar("aprobada", decisiones=["revision_manual"])
        self.assertEqual(out.decision, "revision_manual")
        self.assertEqual(ex.call_count, 1)

    def test_son_tres_lecturas_unanimes(self):
        self.assertEqual(consenso.LECTURAS_PARA_APROBAR, 3)

    def test_error_en_la_segunda_lectura_baja_a_revision(self):
        out, _ = aplicar("aprobada", error=RuntimeError("429"))
        self.assertEqual(out.decision, "revision_manual")

    def test_no_aprobada_cero_llamadas(self):
        for d in ("rechazada", "revision_manual"):
            out, ex = aplicar(d)
            self.assertEqual(out.decision, d)
            ex.assert_not_called()

    def test_sin_cliente_no_llama(self):
        with mock.patch.object(consenso, "extraer") as ex:
            out = consenso.aplicar_consenso(captura(), ext(), res("aprobada"), "x", None, mock.Mock())
        self.assertEqual(out.decision, "aprobada")
        ex.assert_not_called()


class PruebasCableado(unittest.TestCase):
    """Si se quita el consenso de correr, esta prueba se pone roja."""

    def test_correr_exige_consenso(self):
        c = captura()
        with mock.patch.object(correr, "extraer", return_value=ext()), \
             mock.patch.object(correr, "senales_locales", return_value=BUENAS), \
             mock.patch.object(correr, "decidir", return_value=res("aprobada")), \
             mock.patch.object(consenso, "extraer", return_value=ext()), \
             mock.patch.object(correr, "aplicar_consenso", wraps=correr.aplicar_consenso):
            # la segunda lectura "no aprueba": el decidir de la 2ª llamada devuelve revisión
            seq = [res("aprobada"), res("aprobada"), res("revision_manual")]  # la 3ª lectura no aprueba
            with mock.patch.object(correr, "decidir", side_effect=seq):
                _, out = correr.procesar(c, "x", object(), True)
        self.assertEqual(out.decision, "revision_manual")
        self.assertIn("Consenso", out.explicacion)


if __name__ == "__main__":
    unittest.main()
