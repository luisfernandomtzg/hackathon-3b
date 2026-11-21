"""Fast opaque-box E2E smoke test suite for Validat3B Campo App (alt/campo-app).

Covers the 12 essential E2E smoke tests across Tiers 1-4 (per TEST_INFRA.md):
- Shared class-level `CampoServerHarness` (`--sin-modelo`) for tests 01-11.
- Dedicated restart persistence test (`test_12_restart_persistence_sigterm`).
- Strict opaque-box isolation: zero `ml.validat3b.*` imports, ephemeral free ports,
  `tempfile.TemporaryDirectory()` for `--salida` (never touches :8443 or `salidas/campo/`).
"""
from __future__ import annotations

import base64
import csv
import http.client
import io
import json
import os
import re
import socket
import ssl
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from cryptography import x509
from PIL import Image, ImageDraw

REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOGO_CSV = REPO_ROOT / "datos" / "privado" / "metadatos" / "catalogo_productos.csv"
FONT_WOFF2 = REPO_ROOT / "app" / "fonts" / "Montserrat-Variable.woff2"

CADENAS = ["Soriana", "Bodega Aurrera", "Bara", "Neto", "Walmart", "Chedraui"]
MOTIVOS_OMITIR = [
    "No hay producto en anaquel",
    "No tiene letrero de precio",
    "No me dejaron tomar la foto",
    "No encontré el producto",
    "Otro",
]
MAX_INTENTOS = 3
CSV_HEADERS = [
    "producto",
    "id_product",
    "cadena",
    "precio_validado",
    "precio_referencia_3b",
    "diferencia_pct",
    "capturista",
    "hora",
    "capture_id",
]
EMOJI_RE = re.compile(r"[\U0001F300-\U0001FAFF\u2600-\u27BF\uFE0F\U0001F1E6-\U0001F1FF]")


# ---------------------------------------------------------------------------
# Synthetic Media & Pure-Python EAN-13 Generator
# ---------------------------------------------------------------------------

_EAN13_PARITY = {
    "0": "LLLLLL",
    "1": "LLGLGG",
    "2": "LLGGLG",
    "3": "LLGGGL",
    "4": "LGLLGG",
    "5": "LGGLLG",
    "6": "LGGGLL",
    "7": "LGLGLG",
    "8": "LGLGGL",
    "9": "LGGLGL",
}
_EAN13_L = {
    "0": "0001101",
    "1": "0011001",
    "2": "0010011",
    "3": "0111101",
    "4": "0100011",
    "5": "0110001",
    "6": "0101111",
    "7": "0111011",
    "8": "0110111",
    "9": "0001011",
}
_EAN13_G = {
    "0": "0100111",
    "1": "0110011",
    "2": "0011011",
    "3": "0100001",
    "4": "0011101",
    "5": "0111001",
    "6": "0000101",
    "7": "0010001",
    "8": "0001001",
    "9": "0010111",
}
_EAN13_R = {
    "0": "1110010",
    "1": "1100110",
    "2": "1101100",
    "3": "1000010",
    "4": "1011100",
    "5": "1001110",
    "6": "1010000",
    "7": "1000100",
    "8": "1001000",
    "9": "1110100",
}


def make_jpeg_data_url(width: int = 160, height: int = 120, color: tuple[int, int, int] = (210, 195, 175)) -> str:
    img = Image.new("RGB", (width, height), color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def make_sharp_jpeg_data_url(width: int = 960, height: int = 720) -> str:
    """Create a high-contrast JPEG so local signal analysis stays busy >60 ms."""
    img = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    step = 24
    for y in range(24, height - 24, step * 2):
        for x in range(24, width - 24, step * 2):
            draw.rectangle([x, y, x + step - 1, y + step - 1], fill=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=88)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def make_ean13_jpeg_data_url(digits13: str = "7501017004270") -> str:
    """Encode a 13-digit EAN-13 barcode onto a white Pillow canvas with quiet zones."""
    if len(digits13) != 13 or not digits13.isdigit():
        raise ValueError(f"Expected 13 digits for EAN-13, got {digits13!r}")
    parity = _EAN13_PARITY[digits13[0]]
    bits = ["101"]
    for ch, pat in zip(digits13[1:7], parity):
        bits.append(_EAN13_L[ch] if pat == "L" else _EAN13_G[ch])
    bits.append("01010")
    for ch in digits13[7:]:
        bits.append(_EAN13_R[ch])
    bits.append("101")
    pattern = "".join(bits)

    mod_w = 4
    quiet = 44
    bar_h = 160
    pad_y = 24
    w = len(pattern) * mod_w + quiet * 2
    h = bar_h + pad_y * 2
    img = Image.new("RGB", (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    for idx, bit in enumerate(pattern):
        if bit == "1":
            x0 = quiet + idx * mod_w
            draw.rectangle([x0, pad_y, x0 + mod_w - 1, pad_y + bar_h], fill=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


# ---------------------------------------------------------------------------
# Subprocess & HTTPS Harness
# ---------------------------------------------------------------------------


def alloc_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("0.0.0.0", 0))
        return int(s.getsockname()[1])


class CampoServerHarness:
    """Isolated opaque-box runner for `ml.validat3b.campo` subprocess."""

    def __init__(
        self,
        *,
        catalogo: Path | str | None = CATALOGO_CSV,
        salida_dir: Path | None = None,
        sin_modelo: bool = True,
    ):
        self._owns_tmp = salida_dir is None
        self._tmpdir = tempfile.TemporaryDirectory() if salida_dir is None else None
        self.salida = Path(self._tmpdir.name) if self._tmpdir is not None else Path(salida_dir)
        self.catalogo = Path(catalogo) if catalogo is not None else None
        self.sin_modelo = sin_modelo
        self.port: int = 0
        self.proc: subprocess.Popen[str] | None = None
        self.banner_lines: list[str] = []
        self._drain_thread: threading.Thread | None = None
        self._ssl_ctx: ssl.SSLContext | None = None

    def start(self) -> "CampoServerHarness":
        last_err = ""
        for _ in range(3):
            self.port = alloc_free_port()
            cmd = [
                sys.executable,
                "-u",
                "-m",
                "ml.validat3b.campo",
                "--salida",
                str(self.salida),
                "--puerto",
                str(self.port),
            ]
            if self.catalogo is not None:
                cmd += ["--catalogo", str(self.catalogo)]
            if self.sin_modelo:
                cmd.append("--sin-modelo")

            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"
            self.banner_lines = []
            self.proc = subprocess.Popen(
                cmd,
                cwd=str(REPO_ROOT),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            if self._wait_ready(timeout=15.0):
                try:
                    self._drain_thread = threading.Thread(target=self._drain_stdout, daemon=True)
                    self._drain_thread.start()
                    cert_path = self.salida / "campo-cert.pem"
                    self._ssl_ctx = (
                        ssl.create_default_context(cafile=str(cert_path))
                        if cert_path.is_file()
                        else ssl._create_unverified_context()
                    )
                    return self
                except Exception:
                    self._terminate_proc()
                    raise
            last_err = "\n".join(self.banner_lines)
            self._terminate_proc()
        raise RuntimeError(f"Failed to start campo.py server:\n{last_err}")

    def _wait_ready(self, timeout: float) -> bool:
        assert self.proc is not None and self.proc.stdout is not None
        deadline = time.monotonic() + timeout
        ready_queue: list[str] = []
        stop_flag = threading.Event()

        def _reader() -> None:
            assert self.proc is not None and self.proc.stdout is not None
            while not stop_flag.is_set():
                line = self.proc.stdout.readline()
                if not line:
                    break
                ready_queue.append(line.rstrip("\r\n"))
                if "Ctrl+C para detener." in line:
                    break

        t = threading.Thread(target=_reader, daemon=True)
        t.start()
        while time.monotonic() < deadline:
            if any("Ctrl+C para detener." in ln for ln in ready_queue):
                self.banner_lines.extend(ready_queue)
                return True
            if self.proc.poll() is not None:
                t.join(timeout=1.0)
                self.banner_lines.extend(ready_queue)
                return False
            time.sleep(0.05)
        stop_flag.set()
        self.banner_lines.extend(ready_queue)
        return False

    def _drain_stdout(self) -> None:
        if self.proc is None or self.proc.stdout is None:
            return
        try:
            for line in self.proc.stdout:
                self.banner_lines.append(line.rstrip("\r\n"))
        except Exception:
            pass

    def _terminate_proc(self) -> None:
        if self.proc is not None:
            if self.proc.poll() is None:
                self.proc.terminate()
                try:
                    self.proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.proc.kill()
                    self.proc.wait(timeout=5)
            if self.proc.stdout is not None:
                try:
                    self.proc.stdout.close()
                except Exception:
                    pass
            self.proc = None

    def stop(self, cleanup: bool = True) -> None:
        self._terminate_proc()
        if cleanup and self._owns_tmp and self._tmpdir is not None:
            self._tmpdir.cleanup()
            self._tmpdir = None

    def __enter__(self) -> "CampoServerHarness":
        return self.start()

    def __exit__(self, exc_type, exc, tb) -> None:
        self.stop(cleanup=True)

    def base_url(self, host: str = "127.0.0.1") -> str:
        return f"https://{host}:{self.port}"

    def request_raw(
        self,
        method: str,
        path: str,
        body: bytes | None = None,
        headers: dict[str, str] | None = None,
        base_url: str | None = None,
        timeout: float = 15.0,
    ) -> tuple[int, dict[str, str], bytes]:
        url = (base_url or self.base_url()) + path
        req = urllib.request.Request(url, data=body, method=method, headers=headers or {})
        try:
            with urllib.request.urlopen(req, context=self._ssl_ctx, timeout=timeout) as resp:
                hdrs = {k.lower(): v for k, v in resp.headers.items()}
                return resp.status, hdrs, resp.read()
        except urllib.error.HTTPError as exc:
            hdrs = {k.lower(): v for k, v in exc.headers.items()}
            return exc.code, hdrs, exc.read()

    def get(
        self, path: str, base_url: str | None = None, headers: dict[str, str] | None = None
    ) -> tuple[int, dict[str, str], bytes]:
        return self.request_raw("GET", path, headers=headers, base_url=base_url)

    def get_json(self, path: str, base_url: str | None = None) -> tuple[int, dict]:
        st, _, raw = self.get(path, base_url=base_url)
        return st, json.loads(raw.decode("utf-8"))

    def post_json(
        self, path: str, payload: dict, base_url: str | None = None, headers: dict[str, str] | None = None
    ) -> tuple[int, dict]:
        hdrs = {"Content-Type": "application/json"}
        if headers:
            hdrs.update(headers)
        st, _, raw = self.request_raw(
            "POST",
            path,
            body=json.dumps(payload).encode("utf-8"),
            headers=hdrs,
            base_url=base_url,
        )
        return st, json.loads(raw.decode("utf-8"))

    def non_loopback_url(self) -> str | None:
        st, d = self.get_json("/api/supervisor/estado")
        if st != 200:
            return None
        for u in d.get("urls", []):
            host = urllib.parse.urlparse(u).hostname
            if host and host not in ("127.0.0.1", "localhost", "::1"):
                return u
        return None


def _unwrap_producto(resp: dict) -> dict:
    return resp["producto"] if isinstance(resp.get("producto"), dict) else resp


def _poll_until_settled(srv: CampoServerHarness, codigo: str, id_product: str, timeout: float = 10.0) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        st, d = srv.get_json(f"/api/estado?codigo={urllib.parse.quote(codigo)}")
        if st == 200:
            for t in d.get("tareas", []):
                if str(t.get("id_product")) == str(id_product) and t.get("estado") != "procesando":
                    return t
        time.sleep(0.05)
    raise AssertionError(f"Task {id_product} for {codigo} stayed in 'procesando' beyond {timeout}s")


def _extract_css(html: str) -> str:
    blocks = re.findall(r"<style[^>]*>(.*?)</style>", html, flags=re.S | re.I)
    return re.sub(r"/\*.*?\*/", "", "\n".join(blocks), flags=re.S)


def _extract_visible_html(html: str) -> str:
    no_style = re.sub(r"<style[^>]*>.*?</style>", " ", html, flags=re.S | re.I)
    no_script = re.sub(r"<script[^>]*>.*?</script>", " ", no_style, flags=re.S | re.I)
    no_comments = re.sub(r"<!--.*?-->", " ", no_script, flags=re.S)
    no_doctype = re.sub(r"<!doctype\s+html>", " ", no_comments, flags=re.I)
    return re.sub(r"<[^>]+>", " ", no_doctype)


# ---------------------------------------------------------------------------
# Fast Smoke E2E Suite (12 Tests)
# ---------------------------------------------------------------------------


class TestCampoE2ESmoke(unittest.TestCase):
    """Tests 01-11 running against a shared `--sin-modelo` HTTPS server."""

    @classmethod
    def setUpClass(cls):
        cls.srv = CampoServerHarness(sin_modelo=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.stop()

    def test_01_https_san_cert_and_montserrat_font(self):
        self.assertTrue((self.srv.salida / "campo-cert.pem").is_file())
        self.assertTrue((self.srv.salida / "campo-llave.pem").is_file())

        cert = x509.load_pem_x509_certificate((self.srv.salida / "campo-cert.pem").read_bytes())
        san = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
        dns_names = set(san.get_values_for_type(x509.DNSName))
        ip_strs = {str(ip) for ip in san.get_values_for_type(x509.IPAddress)}
        self.assertIn("localhost", dns_names)
        self.assertIn("127.0.0.1", ip_strs)

        st_est, est = self.srv.get_json("/api/supervisor/estado")
        self.assertEqual(st_est, 200)
        for u in est["urls"]:
            host = urllib.parse.urlparse(u).hostname
            if host:
                self.assertIn(host, ip_strs)

        st_loc, _, _ = self.srv.get("/", base_url=f"https://localhost:{self.srv.port}")
        self.assertEqual(st_loc, 200)

        st_f, hdrs_f, body_f = self.srv.get("/fonts/montserrat.woff2")
        self.assertEqual(st_f, 200)
        self.assertIn("font/woff2", hdrs_f.get("content-type", ""))
        self.assertTrue(body_f.startswith(b"wOF2"))
        self.assertEqual(body_f, FONT_WOFF2.read_bytes())

    def test_02_localhost_guard_and_path_traversal(self):
        _, alta = self.srv.post_json("/api/supervisor/alta", {"nombre": "Guard T2", "tienda": "Bara", "cuantos": 1})
        cod = alta["codigo"]
        self.srv.post_json("/api/fachada", {"codigo": cod, "foto": make_jpeg_data_url()})
        _, est = self.srv.get_json("/api/supervisor/estado")
        fachada_path = "/" + est["capturistas"][cod]["fachada"].lstrip("/")

        self.assertEqual(self.srv.get("/supervisor")[0], 200)
        self.assertEqual(self.srv.get("/api/supervisor/estado")[0], 200)
        self.assertEqual(self.srv.get("/api/supervisor/catalogo?q=frijol")[0], 200)
        self.assertEqual(self.srv.get("/api/supervisor/precios.csv")[0], 200)
        st_img, hdrs_img, img_bytes = self.srv.get(fachada_path)
        self.assertEqual(st_img, 200)
        self.assertIn("image/jpeg", hdrs_img.get("content-type", ""))
        self.assertTrue(img_bytes.startswith(b"\xff\xd8"))

        st_trav, _, raw_trav = self.srv.get("/fotos/../estado.json")
        self.assertEqual(st_trav, 404)
        self.assertNotIn(b"capturistas", raw_trav)
        self.assertEqual(self.srv.get("/fotos/..%2Festado.json")[0], 404)

        lan_url = self.srv.non_loopback_url()
        if lan_url:
            for blocked in ("/supervisor", "/api/supervisor/estado", "/api/supervisor/catalogo", "/api/supervisor/precios.csv", fachada_path):
                self.assertEqual(self.srv.get(blocked, base_url=lan_url)[0], 403, f"Expected 403 on {blocked} via {lan_url}")
            self.assertEqual(self.srv.post_json("/api/supervisor/alta", {"nombre": "X", "tienda": "Soriana"}, base_url=lan_url)[0], 403)
            self.assertEqual(self.srv.get("/", base_url=lan_url)[0], 200)
            st_v, dv = self.srv.post_json("/api/vincular", {"codigo": cod}, base_url=lan_url)
            self.assertEqual(st_v, 200)
            self.assertEqual(dv["nombre"], "Guard T2")

    def test_03_tarima_ui_compliance_and_flows(self):
        html_cap = self.srv.get("/")[2].decode("utf-8")
        html_sup = self.srv.get("/supervisor")[2].decode("utf-8")

        for route, html in (("/", html_cap), ("/supervisor", html_sup)):
            css = _extract_css(html)
            css_low = css.lower()
            self.assertIn("#e31b23", css_low, f"Missing Tarima primary #E31B23 on {route}")
            self.assertIn("#04211f", css_low, f"Missing Tarima ink #04211F on {route}")
            self.assertTrue("#ffffff" in css_low or "#fff" in css_low, f"Missing white surface on {route}")
            self.assertIn("Prototipo para Tiendas 3B", html, f"Missing 3B attribution on {route}")

            self.assertIsNone(
                re.search(
                    r"(?:^|[\s,}])body(?:\s*,\s*[^{]+)?\s*\{[^}]*background(?:-color)?\s*:\s*(#f4f6f6|var\(--(t50|ink-50|muted)[^)]*\))",
                    css,
                    re.I,
                ),
                f"Forbidden gray body bg on {route}",
            )
            self.assertIsNotNone(
                re.search(
                    r"(?:^|[\s,}])body(?:\s*,\s*[^{]+)?\s*\{[^}]*background(?:-color)?\s*:\s*(#fff(?:fff)?\b|white\b|var\(--(?:background|bg|blanco|white|superficie|surface|fondo)[^)]*\))",
                    css,
                    re.I,
                ),
                f"Body not white on {route}",
            )

            header_blocks = re.findall(r"(?:^|[\s,}])header(?:\s*,\s*[^{]+)?\s*\{([^}]*)\}", css, re.I)
            for h_body in header_blocks:
                self.assertIsNone(
                    re.search(
                        r"background(?:-color)?\s*:\s*(?:#(?:04211f|000(?:000)?|1c2f2e|31413f)\b|var\(--(?:tinta|ink-[89]00|text-primary|text-secondary)[^)]*\))",
                        h_body,
                        re.I,
                    ),
                    f"Forbidden dark header on {route}",
                )
                if re.search(r"background(?:-color)?\s*:", h_body, re.I):
                    self.assertIsNotNone(
                        re.search(
                            r"background(?:-color)?\s*:\s*(?:#fff(?:fff)?\b|white\b|transparent\b|inherit\b|var\(--(?:background|bg|blanco|white|superficie|surface(?:-2)?|fondo)[^)]*\))",
                            h_body,
                            re.I,
                        ),
                        f"Header must use light/white/surface background on {route}",
                    )

            self.assertIsNone(
                re.search(
                    r"(?:border-left(?:-width)?|border-inline-start(?:-width)?)\s*:",
                    css,
                    re.I,
                ),
                f"Forbidden left-stripe alert border on {route}",
            )
            self.assertIsNone(
                re.search(
                    r"border-width\s*:\s*0(?:px)?\s+0(?:px)?\s+0(?:px)?\s+[1-9]",
                    css,
                    re.I,
                ),
                f"Forbidden asymmetric left border-width on {route}",
            )
            alert_rules = re.findall(
                r"([^{}]*(?:\.(?:aviso|exito|error|alerta)\b|\[role=[\"']?alert[\"']?\])[^{]*)\{([^}]*)\}",
                css,
                re.I,
            )
            self.assertGreaterEqual(len(alert_rules), 1, f"Missing alert CSS rules on {route}")
            alert_decls_by_cls: dict[str, list[str]] = {}
            for sel, body_css in alert_rules:
                for cls_name in re.findall(r"\.(aviso|exito|error|alerta)\b", sel, re.I):
                    alert_decls_by_cls.setdefault(cls_name.lower(), []).append(body_css)
                if "role" in sel.lower():
                    alert_decls_by_cls.setdefault("[role=alert]", []).append(body_css)
            for cls_name, decls in alert_decls_by_cls.items():
                combined = "\n".join(decls)
                has_shorthand_border = bool(re.search(r"(?<![-\w])border\s*:\s*(?!0\b|none\b)", combined, re.I))
                has_longhand_border = bool(
                    re.search(r"border-width\s*:", combined, re.I)
                    and re.search(r"border-style\s*:\s*(?!none\b)", combined, re.I)
                    and re.search(r"border-color\s*:", combined, re.I)
                )
                self.assertTrue(
                    has_shorthand_border or has_longhand_border,
                    f"Full border missing on alert '.{cls_name}' in {route}",
                )

            has_role_alert = bool(
                re.search(
                    r"""role\s*=\s*["']alert["']|setAttribute\(\s*["']role["']\s*,\s*["']alert["']\s*\)""",
                    html,
                )
            )
            self.assertTrue(has_role_alert, f"Missing role='alert' on {route}")

            self.assertNotIn('class="dark"', html, f"Dark class on {route}")
            self.assertIsNone(re.search(r"\.dark\b|prefers-color-scheme\s*:\s*dark", css, re.I), f"Dark CSS on {route}")
            self.assertIsNone(re.search(r"(linear|radial|conic)-gradient\s*\(", css, re.I), f"Gradient found on {route}")
            self.assertIsNone(EMOJI_RE.search(html), f"Emoji found on {route}")
            self.assertNotIn("¡Ups!", html)
            self.assertNotIn("!", _extract_visible_html(html), f"Exclamation in visible HTML on {route}")

            self.assertIsNone(re.search(r"<(link|script)[^>]*(href|src)=[\"']https?://", html, re.I), f"External CDN tag on {route}")
            for bad_cdn in ("fonts.googleapis.com", "fonts.gstatic.com", "unpkg.com", "jsdelivr.net", "cdnjs.cloudflare.com"):
                self.assertNotIn(bad_cdn, html.lower(), f"External CDN {bad_cdn} on {route}")

            self.assertIn("/fonts/montserrat.woff2", css, f"Local Montserrat missing on {route}")
            self.assertIn("@font-face", css, f"@font-face missing on {route}")
            self.assertTrue("tabular-nums" in css or "tnum" in css, f"tabular-nums missing on {route}")

            has_16px_declared = bool(re.search(r"(?:16px|1rem)\b", css, re.I))
            input_16_direct = bool(
                re.search(
                    r"\binput\b[^{]*\{[^}]*(?:font-size\s*:\s*(?:16px|1rem)\b|font\s*:[^;}]*\b(?:16px|1rem)\b)",
                    css,
                    re.I,
                )
            )
            input_16_var_or_inherit = has_16px_declared and bool(
                re.search(r"\binput\b[^{]*\{[^}]*font(?:-size)?\s*:[^;}]*(?:var\(--[^)]+\)|inherit\b)", css, re.I)
            )
            self.assertTrue(input_16_direct or input_16_var_or_inherit, f"16px input rule missing on {route}")

            has_touch_px_declared = bool(re.search(r":\s*(?:4[4-9]|[5-9]\d)px\b", css, re.I))
            touch_direct = bool(
                re.search(
                    r"(?:button|\.boton|\.btn)[^{]*\{[^}]*(?:min-)?height\s*:\s*(?:4[4-9]|[5-9]\d|\d{3,})px\b",
                    css,
                    re.I,
                )
            )
            touch_var = has_touch_px_declared and bool(
                re.search(r"(?:button|\.boton|\.btn)[^{]*\{[^}]*(?:min-)?height\s*:\s*var\(--[^)]+\)", css, re.I)
            )
            self.assertTrue(touch_direct or touch_var, f"44px+ touch control missing on {route}")

        # Capturista 4-step wizard & barcode-first hooks
        for needle in (
            'inputmode="numeric"',
            'maxlength="6"',
            "/api/vincular",
            "navigator.geolocation",
            "/api/ubicacion",
            "/api/fachada",
            "getUserMedia",
            "BarcodeDetector",
            "/api/leer_codigo",
            "/api/buscar_codigo",
            "/api/registrar_producto",
            "/api/agregar_producto_propio",
            "/api/reportar_codigo",
            "/api/captura",
            "/api/estado",
            "Escanear producto nuevo",
        ):
            self.assertIn(needle, html_cap, f"Missing Capturista UI hook: {needle}")
        self.assertTrue("Paso 1" in html_cap or "pasos(1,4)" in html_cap or "pasos(" in html_cap)
        self.assertIsNotNone(re.search(r"async\s*:\s*(true|!0)", html_cap))

        # Supervisor UI hooks
        self.assertIsNotNone(
            re.search(r"\b[A-Za-z_$][\w$]*\.urls\b", html_sup),
            "Missing Supervisor UI hook: *.urls",
        )
        for needle in (
            "/api/supervisor/catalogo",
            "/api/supervisor/producto",
            "/api/supervisor/alta",
            "/api/supervisor/agregar_tarea",
            "reportes_codigo",
            "/api/supervisor/resolver_reporte",
            "precio_tecleado",
            "barcode",
            "/api/supervisor/precios.csv",
        ):
            self.assertIn(needle, html_sup, f"Missing Supervisor UI hook: {needle}")
        self.assertTrue("<svg" in html_sup.lower() or "createelementns" in html_sup.lower() or "<canvas" in html_sup.lower())
        self.assertNotIn("api.qrserver.com", html_sup.lower())

    def test_04_supervisor_catalog_custom_products_and_propagation(self):
        st_q, d_q = self.srv.get_json("/api/supervisor/catalogo?q=frijol")
        self.assertEqual(st_q, 200)
        self.assertGreaterEqual(len(d_q["productos"]), 1)

        st1, r1 = self.srv.post_json(
            "/api/supervisor/producto",
            {"nombre": "Agua Bonafont 3B 500 ml", "marca": "Bonafont", "contenido": "500 ml", "barcode": "7501086801046", "precio_referencia": 10.0},
        )
        self.assertEqual(st1, 200)
        self.assertTrue(r1.get("ok") is True)
        p1 = _unwrap_producto(r1)
        self.assertGreaterEqual(int(p1["id_product"]), 900001)
        self.assertTrue(p1["custom"])
        self.assertEqual(p1["unit_product"], "mililitro")
        self.assertEqual(float(p1["unit_quantity_product"]), 500.0)

        st2, r2 = self.srv.post_json(
            "/api/supervisor/producto",
            {"nombre": "Boost Energy", "marca": "Boost", "contenido": "235 ml", "barcode": "7502223334445", "precio_referencia": 22.0},
        )
        self.assertEqual(st2, 200)
        p2 = _unwrap_producto(r2)
        self.assertGreater(int(p2["id_product"]), int(p1["id_product"]))

        st_alta, alta = self.srv.post_json(
            "/api/supervisor/alta",
            {"nombre": "Prop T4", "tienda": "Walmart", "productos": [p1["id_product"], "4"]},
        )
        self.assertEqual(st_alta, 200)
        cod = alta["codigo"]
        self.assertEqual([t["id_product"] for t in alta["tareas"]], [p1["id_product"], "4"])

        st_prop, prop = self.srv.post_json("/api/supervisor/agregar_tarea", {"codigo": cod, "id_product": p2["id_product"]})
        self.assertEqual(st_prop, 200)
        self.assertTrue(prop.get("ok") is True)
        _, est = self.srv.get_json(f"/api/estado?codigo={cod}")
        self.assertIn(p2["id_product"], [t["id_product"] for t in est["tareas"]])

    def test_05_barcode_lookup_normalization_decode_register_and_report(self):
        cod = self.srv.post_json("/api/supervisor/alta", {"nombre": "Barcode T5", "tienda": "Chedraui", "productos": ["6"]})[1]["codigo"]

        st_ex, d_ex = self.srv.post_json("/api/buscar_codigo", {"codigo": cod, "barcode": "7501017004270"})
        self.assertEqual((st_ex, d_ex["encontrado"], d_ex["producto"]["id_product"]), (200, True, "4"))

        # Catalog item 2692 has 11-digit barcode '41789001864'; scanner adds leading zero '041789001864'
        st_nz, d_nz = self.srv.post_json("/api/buscar_codigo", {"codigo": cod, "barcode": "041789001864"})
        self.assertEqual((st_nz, d_nz["encontrado"], d_nz["producto"]["id_product"]), (200, True, "2692"))

        st_dec, dec = self.srv.post_json("/api/leer_codigo", {"codigo": cod, "foto": make_ean13_jpeg_data_url("7501017004270")})
        self.assertEqual((st_dec, dec.get("ok"), dec.get("barcode")), (200, True, "7501017004270"))

        st_reg, reg = self.srv.post_json(
            "/api/registrar_producto",
            {"codigo": cod, "nombre": "Snack Nuevo T5", "marca": "3B", "contenido": "150 g", "barcode": "7509876543210", "precio_referencia": 19.5},
        )
        self.assertEqual(st_reg, 200)
        self.assertTrue(reg.get("ok") is True)
        self.assertGreaterEqual(int(reg["producto"]["id_product"]), 900001)
        self.assertEqual(reg["tarea"]["id_product"], reg["producto"]["id_product"])

        st_own, own = self.srv.post_json("/api/agregar_producto_propio", {"codigo": cod, "id_product": "12"})
        self.assertEqual((st_own, own.get("ok"), own["tarea"]["id_product"]), (200, True, "12"))

        st_rep, rep = self.srv.post_json(
            "/api/reportar_codigo",
            {"codigo": cod, "id_product": "6", "barcode": "7501017004270", "motivo": "Código dañado en empaque"},
        )
        self.assertEqual((st_rep, rep.get("ok")), (200, True))
        rid = rep["reporte"]["id_reporte"]
        st_res, res = self.srv.post_json("/api/supervisor/resolver_reporte", {"id_reporte": rid, "nota": "Corregido"})
        self.assertEqual((st_res, res.get("ok"), res["reporte"]["resuelto"]), (200, True, True))

    def test_06_capturista_onboarding_gps_facade_and_omit(self):
        cod = self.srv.post_json("/api/supervisor/alta", {"nombre": "Funnel T6", "tienda": "Soriana", "cuantos": 2})[1]["codigo"]

        st_v, perf = self.srv.post_json("/api/vincular", {"codigo": cod})
        self.assertEqual(st_v, 200)
        self.assertFalse(perf["tiene_fachada"])
        self.assertEqual(perf["max_intentos"], MAX_INTENTOS)
        self.assertEqual(perf["motivos_omitir"], MOTIVOS_OMITIR)

        st_u, _ = self.srv.post_json("/api/ubicacion", {"codigo": cod, "lat": 19.4326012, "lon": -99.1332018, "precision": 14.7})
        self.assertEqual(st_u, 200)
        _, est = self.srv.get_json("/api/supervisor/estado")
        self.assertEqual(est["capturistas"][cod]["ubicacion"]["lat"], 19.432601)
        self.assertEqual(est["capturistas"][cod]["ubicacion"]["precision_m"], 15)

        st_f, _ = self.srv.post_json("/api/fachada", {"codigo": cod, "foto": make_jpeg_data_url()})
        self.assertEqual(st_f, 200)
        self.assertTrue(self.srv.post_json("/api/vincular", {"codigo": cod})[1]["tiene_fachada"])

        idp = perf["tareas"][0]["id_product"]
        self.assertEqual(self.srv.post_json("/api/omitir", {"codigo": cod, "id_product": idp, "motivo": "Motivo inventado"})[0], 400)
        st_om, om = self.srv.post_json("/api/omitir", {"codigo": cod, "id_product": idp, "motivo": MOTIVOS_OMITIR[0]})
        self.assertEqual((st_om, om.get("ok"), om.get("estado")), (200, True, "omitida"))

    def test_07_non_blocking_async_capture_and_polling(self):
        cod = self.srv.post_json("/api/supervisor/alta", {"nombre": "Async T7", "tienda": "Walmart", "productos": ["4"]})[1]["codigo"]
        self.srv.post_json("/api/fachada", {"codigo": cod, "foto": make_jpeg_data_url()})
        sharp_jpg = make_sharp_jpeg_data_url()
        payload = {"codigo": cod, "id_product": "4", "foto_producto": sharp_jpg, "foto_etiqueta": sharp_jpg, "precio": "17.00", "async": True}

        # Pre-establish TLS connection for duplicate request so it hits server before worker finishes
        conn_dup = http.client.HTTPSConnection("127.0.0.1", self.srv.port, context=self.srv._ssl_ctx, timeout=5)
        conn_dup.connect()
        try:
            t0 = time.monotonic()
            st1, r1 = self.srv.post_json("/api/captura", payload)
            elapsed = time.monotonic() - t0
            self.assertEqual(st1, 200)
            self.assertLess(elapsed, 0.5)
            self.assertEqual(r1["estado"], "procesando")
            self.assertEqual(r1["intento"], 1)

            body_bytes = json.dumps(payload).encode("utf-8")
            conn_dup.request("POST", "/api/captura", body=body_bytes, headers={"Content-Type": "application/json", "Content-Length": str(len(body_bytes))})
            resp_dup = conn_dup.getresponse()
            dup_body = json.loads(resp_dup.read().decode("utf-8"))
            self.assertEqual(resp_dup.status, 400, f"Expected 400 duplicate-while-procesando, got {resp_dup.status}: {dup_body}")
        finally:
            conn_dup.close()

        settled = _poll_until_settled(self.srv, cod, "4")
        self.assertEqual(settled["estado"], "revision")
        self.assertEqual(settled["intentos"], 1)

    def test_08_safe_attempt_accounting_and_retake_cap(self):
        cod = self.srv.post_json("/api/supervisor/alta", {"nombre": "Attempts T8", "tienda": "Neto", "productos": ["4"]})[1]["codigo"]
        jpg = make_jpeg_data_url()
        self.srv.post_json("/api/fachada", {"codigo": cod, "foto": jpg})

        st_bad1, _ = self.srv.post_json("/api/captura", {"codigo": cod, "id_product": "4", "foto_producto": "data:text/plain;base64,AAAA", "foto_etiqueta": jpg, "precio": "17"})
        st_bad2, _ = self.srv.post_json("/api/captura", {"codigo": cod, "id_product": "4", "foto_producto": jpg, "foto_etiqueta": "data:image/jpeg;base64,NOTJPEG", "precio": "17"})
        self.assertEqual((st_bad1, st_bad2), (400, 400))
        self.assertEqual(self.srv.get_json(f"/api/estado?codigo={cod}")[1]["tareas"][0]["intentos"], 0)

        # Under --sin-modelo, intento increments 1..3 and `puede_repetir` enforces the MAX_INTENTOS=3 UX retake limit
        results = [
            self.srv.post_json("/api/captura", {"codigo": cod, "id_product": "4", "foto_producto": jpg, "foto_etiqueta": jpg, "precio": "17"})[1]
            for _ in range(MAX_INTENTOS)
        ]
        self.assertEqual([r["intento"] for r in results], [1, 2, 3])
        self.assertEqual([r["estado"] for r in results], ["revision", "revision", "revision"])
        self.assertEqual([r["puede_repetir"] for r in results], [True, True, False])

    def test_09_supervisor_csv_export_schema(self):
        st, hdrs, raw_csv = self.srv.get("/api/supervisor/precios.csv")
        self.assertEqual(st, 200)
        self.assertIn("text/csv", hdrs.get("content-type", ""))
        self.assertTrue(raw_csv.startswith(b"\xef\xbb\xbf"))
        rows = list(csv.reader(io.StringIO(raw_csv.decode("utf-8-sig"))))
        # Under --sin-modelo, all captures are revision_manual/rechazada/omitida and must be excluded from precios.csv
        self.assertEqual(len(rows), 1, f"Unapproved captures leaked into precios.csv: {rows}")
        self.assertEqual(rows[0], CSV_HEADERS)

    def test_10_boundary_guards_and_security_headers(self):
        cod = self.srv.post_json("/api/supervisor/alta", {"nombre": "Guard T10", "tienda": "Soriana", "productos": ["4"]})[1]["codigo"]
        jpg = make_jpeg_data_url()

        st_prefac, d_prefac = self.srv.post_json("/api/captura", {"codigo": cod, "id_product": "4", "foto_producto": jpg, "foto_etiqueta": jpg, "precio": "17"})
        self.assertEqual(st_prefac, 400)
        self.assertIn("fachada", d_prefac["error"].lower())

        for bad_cod in ("000000", "abc", ""):
            self.assertEqual(self.srv.post_json("/api/vincular", {"codigo": bad_cod})[0], 404)

        st_bad_json, _, raw_bad = self.srv.request_raw("POST", "/api/vincular", body=b"{not json", headers={"Content-Type": "application/json"})
        self.assertEqual(st_bad_json, 400)
        self.assertNotIn("Traceback", raw_bad.decode("utf-8", errors="replace"))

        # Header-level oversize payload check (> 12 MB MAX_CUERPO) without allocating 13 MB
        conn_big = http.client.HTTPSConnection("127.0.0.1", self.srv.port, context=self.srv._ssl_ctx, timeout=5)
        try:
            conn_big.putrequest("POST", "/api/vincular")
            conn_big.putheader("Content-Type", "application/json")
            conn_big.putheader("Content-Length", str(13 * 1024 * 1024))
            conn_big.endheaders()
            conn_big.send(b"{}")
            resp_big = conn_big.getresponse()
            raw_big = resp_big.read().decode("utf-8", errors="replace")
            self.assertEqual(resp_big.status, 400)
            self.assertIn("demasiado grande", raw_big.lower())
        finally:
            conn_big.close()

        for path in ("/", "/supervisor", "/api/supervisor/estado", "/api/supervisor/precios.csv", "/no/existe"):
            _, hdrs, _ = self.srv.get(path)
            self.assertEqual(hdrs.get("cache-control"), "no-store", f"Missing Cache-Control on {path}")
            self.assertEqual(hdrs.get("x-content-type-options"), "nosniff", f"Missing nosniff on {path}")

    def test_11_mesa_3b_multi_capturista_end_to_end(self):
        p_bona = _unwrap_producto(
            self.srv.post_json(
                "/api/supervisor/producto",
                {"nombre": "Agua Bonafont 3B 500 ml Mesa", "marca": "Bonafont", "contenido": "500 ml", "barcode": "7501086802050", "precio_referencia": 10.0},
            )[1]
        )
        p_boost = _unwrap_producto(
            self.srv.post_json(
                "/api/supervisor/producto",
                {"nombre": "Boost Energy Mesa", "marca": "Boost", "contenido": "235 ml", "barcode": "7502223335551", "precio_referencia": 22.0},
            )[1]
        )
        pids = [p_bona["id_product"], p_boost["id_product"]]
        c1 = self.srv.post_json("/api/supervisor/alta", {"nombre": "Mesa Cap 1", "tienda": "Bodega Aurrera", "productos": pids})[1]["codigo"]
        c2 = self.srv.post_json("/api/supervisor/alta", {"nombre": "Mesa Cap 2", "tienda": "Soriana", "productos": pids})[1]["codigo"]

        jpg = make_jpeg_data_url()
        errs: list[str] = []

        def worker(cod: str, lat: float) -> None:
            try:
                if self.srv.post_json("/api/vincular", {"codigo": cod})[0] != 200:
                    errs.append(f"vincular failed {cod}")
                if self.srv.post_json("/api/ubicacion", {"codigo": cod, "lat": lat, "lon": -99.13, "precision": 10})[0] != 200:
                    errs.append(f"ubicacion failed {cod}")
                if self.srv.post_json("/api/fachada", {"codigo": cod, "foto": jpg})[0] != 200:
                    errs.append(f"fachada failed {cod}")
                st_b, bc = self.srv.post_json("/api/buscar_codigo", {"codigo": cod, "barcode": "07501086802050"})
                if st_b != 200 or not bc.get("encontrado") or bc["producto"]["id_product"] != p_bona["id_product"]:
                    errs.append(f"buscar_codigo failed {cod}: {bc}")
                for idp, px in ((p_bona["id_product"], "10.50"), (p_boost["id_product"], "22.00")):
                    st_c, r_c = self.srv.post_json(
                        "/api/captura",
                        {"codigo": cod, "id_product": idp, "foto_producto": jpg, "foto_etiqueta": jpg, "precio": px, "async": True},
                    )
                    if st_c != 200 or r_c.get("estado") != "procesando":
                        errs.append(f"async captura failed {cod}/{idp}: {r_c}")
            except Exception as exc:
                errs.append(repr(exc))

        t1 = threading.Thread(target=worker, args=(c1, 19.43))
        t2 = threading.Thread(target=worker, args=(c2, 19.44))
        t1.start()
        t2.start()
        t1.join(timeout=15)
        t2.join(timeout=15)
        self.assertEqual(errs, [])

        for cod in (c1, c2):
            for idp in pids:
                settled = _poll_until_settled(self.srv, cod, idp)
                self.assertIn(settled["estado"], ("aprobada", "repetir", "revision"))

        _, est = self.srv.get_json("/api/supervisor/estado")
        mesa_caps = [c for c in est["capturas"] if c["codigo"] in (c1, c2)]
        self.assertEqual(len(mesa_caps), 4)
        for cap in mesa_caps:
            self.assertEqual(self.srv.get("/" + cap["foto_producto"].lstrip("/"))[0], 200)
            self.assertEqual(self.srv.get("/" + cap["foto_etiqueta"].lstrip("/"))[0], 200)

        st_csv, _, raw_csv = self.srv.get("/api/supervisor/precios.csv")
        self.assertEqual(st_csv, 200)
        self.assertTrue(raw_csv.startswith(b"\xef\xbb\xbf"))
        rows_csv = list(csv.reader(io.StringIO(raw_csv.decode("utf-8-sig"))))
        self.assertEqual(len(rows_csv), 1, f"Unapproved --sin-modelo captures must not appear in precios.csv: {rows_csv}")
        self.assertEqual(rows_csv[0], CSV_HEADERS)


class TestCampoE2ERestart(unittest.TestCase):
    """Test 12: Dedicated SIGTERM restart persistence on same `--salida`."""

    def test_12_restart_persistence_sigterm(self):
        with tempfile.TemporaryDirectory() as out_dir:
            out_path = Path(out_dir)
            with CampoServerHarness(salida_dir=out_path, sin_modelo=True) as s1:
                pid = _unwrap_producto(
                    s1.post_json("/api/supervisor/producto", {"nombre": "Persist Prod T12", "barcode": "7509000111222"})[1]
                )["id_product"]
                cod = s1.post_json("/api/supervisor/alta", {"nombre": "Persist User T12", "tienda": "Soriana", "productos": [pid, "4"]})[1]["codigo"]
                jpg = make_jpeg_data_url()
                s1.post_json("/api/ubicacion", {"codigo": cod, "lat": 19.5, "lon": -99.2, "precision": 8})
                s1.post_json("/api/fachada", {"codigo": cod, "foto": jpg})
                s1.post_json("/api/captura", {"codigo": cod, "id_product": pid, "foto_producto": jpg, "foto_etiqueta": jpg, "precio": "12.0"})
                s1.post_json("/api/reportar_codigo", {"codigo": cod, "id_product": "4", "motivo": "Etiqueta rota"})

            with CampoServerHarness(salida_dir=out_path, sin_modelo=True) as s2:
                st, est = s2.get_json("/api/supervisor/estado")
                self.assertEqual(st, 200)
                self.assertIn(pid, est["productos_custom"])
                self.assertIn(cod, est["capturistas"])
                self.assertEqual(est["capturistas"][cod]["ubicacion"]["lat"], 19.5)
                self.assertEqual(len(est["reportes_codigo"]), 1)
                self.assertEqual(len(est["capturas"]), 1)
                self.assertEqual(s2.get("/" + est["capturistas"][cod]["fachada"].lstrip("/"))[0], 200)
                self.assertEqual(s2.get("/" + est["capturas"][0]["foto_producto"].lstrip("/"))[0], 200)


if __name__ == "__main__":
    unittest.main()
