"""Cliente del endpoint Foundry: reintentos, caché en disco y registro de tokens."""
import base64
import csv
import hashlib
import json
import os
import threading
import time
from pathlib import Path

MODELO = "claude-haiku-5-5"
BASE_URL = "https://softwaredevelopment-resource.services.ai.azure.com/anthropic"
_lock = threading.Lock()


def _cargar_env():
    try:
        from dotenv import load_dotenv
        load_dotenv(".env.local")
    except ImportError:
        pass


class Cliente:
    def __init__(self, dir_salidas="salidas"):
        self.dir = Path(dir_salidas)
        self.cache_dir = self.dir / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.tokens_csv = self.dir / "tokens.csv"
        self._api = None
        self.tokens_verificar = 0  # tokens gastados por el verificador en esta corrida

    def _cliente_api(self):
        if self._api is None:
            _cargar_env()
            llave = os.environ.get("FOUNDRY_API_KEY")
            if not llave:
                raise RuntimeError("Falta FOUNDRY_API_KEY (ponla en .env.local)")
            from anthropic import AnthropicFoundry
            self._api = AnthropicFoundry(api_key=llave, base_url=BASE_URL)
        return self._api

    @staticmethod
    def clave(prompt_version: str, imagenes: list[bytes]) -> str:
        h = hashlib.sha1(prompt_version.encode())
        for b in imagenes:
            h.update(b)
        return h.hexdigest()

    def _registrar(self, capture_id, t_in, t_out, seg, origen):
        with _lock:
            nuevo = not self.tokens_csv.exists()
            with open(self.tokens_csv, "a", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                if nuevo:
                    w.writerow(["capture_id", "tokens_entrada", "tokens_salida", "segundos", "origen"])
                w.writerow([capture_id, t_in, t_out, round(seg, 2), origen])

    def consultar(self, capture_id, prompt_version, prompt, imagenes_jpeg: list[bytes], max_tokens=400,
                  etiqueta=None):
        """Devuelve (texto, tokens_in, tokens_out, origen). Caché: tokens 0 y origen 'cache'.
        `etiqueta` rotula la fila de tokens.csv (p. ej. 'verificar'); el origen devuelto no cambia."""
        t0 = time.time()
        archivo = self.cache_dir / f"{self.clave(prompt_version, imagenes_jpeg)}.json"
        if archivo.exists():
            texto = json.loads(archivo.read_text(encoding="utf-8"))["texto"]
            self._registrar(capture_id, 0, 0, time.time() - t0, (etiqueta + "_cache") if etiqueta else "cache")
            return texto, 0, 0, "cache"

        contenido = [{"type": "image", "source": {"type": "base64", "media_type": "image/jpeg",
                                                  "data": base64.b64encode(b).decode()}} for b in imagenes_jpeg]
        contenido.append({"type": "text", "text": prompt})
        api = self._cliente_api()
        ultimo = None
        for intento in range(5):
            try:
                r = api.messages.create(model=MODELO, max_tokens=max_tokens, thinking={"type": "disabled"},
                                        messages=[{"role": "user", "content": contenido}])
                texto = "".join(b.text for b in r.content if getattr(b, "type", "") == "text")
                t_in, t_out = r.usage.input_tokens, r.usage.output_tokens
                archivo.write_text(json.dumps({"texto": texto, "tokens_entrada": t_in, "tokens_salida": t_out}),
                                   encoding="utf-8")
                if etiqueta == "verificar":
                    with _lock:
                        self.tokens_verificar += t_in + t_out
                self._registrar(capture_id, t_in, t_out, time.time() - t0, etiqueta or "modelo")
                return texto, t_in, t_out, "modelo"
            except Exception as e:  # reintenta solo 429/5xx y fallas de red
                ultimo = e
                estado = getattr(e, "status_code", None)
                if estado is not None and estado != 429 and estado < 500:
                    raise
                time.sleep(2 ** intento)
        raise RuntimeError(f"endpoint sin respuesta tras 5 intentos: {ultimo}")
