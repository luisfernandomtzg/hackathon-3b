"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  CheckCircle2,
  Copy,
  Download,
  FileJson,
  FolderUp,
  ImagePlus,
  RotateCw,
  Search,
  Upload,
  ZoomIn,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

export type Decision = "aprobada" | "rechazada" | "revision_manual";
type TabId = "resumen" | "cola" | "auditoria" | "ingesta";
type ViewMode = "cards" | "table";
type OrdenId = "original" | "costo-desc" | "costo-asc";

export interface Validaciones {
  tienda_fachada: "ok" | "falla";
  producto: "ok" | "falla";
  codigo_barras: "ok" | "falla";
  evidencia_precio: "ok" | "falla";
}

export interface ResultadoOficial {
  capture_id: string;
  decision: Decision;
  confidence_score: number;
  reason_code: string | null;
  validaciones: Validaciones;
  precio_detectado: number | null;
  codigo_barras_detectado: string | null;
  explicacion: string;
}

export interface ExtraccionItem {
  capture_id: string;
  producto?: {
    marca?: string | null;
    descripcion?: string | null;
    contenido_cantidad?: number | string | null;
    contenido_unidad?: string | null;
    nitidez?: string | null;
    encuadre?: string | null;
  };
  etiqueta?: {
    precio?: number | null;
    tipo_precio?: string | null;
  };
  origen?: string;
  tokens_entrada?: number;
  tokens_salida?: number;
}

export interface RegistroConsola {
  capture_id: string;
  store: string;
  brand: string;
  product_name: string;
  qty: string;
  unit: string;
  price_ref: string;
  esperada: Decision | "";
  motivo_esperado?: string;
  motor: Decision | "";
  confidence: number | null;
  reason_code: string;
  explicacion: string;
  precio_detectado: number | null;
  codigo_barras_detectado: string;
  leido_marca: string;
  leido_desc: string;
  leido_cant: string;
  leido_unid: string;
  validaciones: Validaciones;
  facade_name?: string;
  product_name_file?: string;
  shelf_name?: string;
  img_facade: string;
  img_product: string;
  img_shelf: string;
  costo: number | null;
}

const DEMO_INICIAL: RegistroConsola[] = [
  {
    capture_id: "CAP-DEMO-001",
    store: "Tienda Norte 104",
    brand: "Despensa Valle",
    product_name: "Frijol negro cocido 400 g",
    qty: "400",
    unit: "g",
    price_ref: "18.50",
    esperada: "aprobada",
    motor: "aprobada",
    confidence: 0.98,
    reason_code: "",
    explicacion: "Marca, gramaje y etiqueta de precio unitario legibles y coincidentes.",
    precio_detectado: 18.5,
    codigo_barras_detectado: "7501000001011",
    leido_marca: "Despensa Valle",
    leido_desc: "Frijol negro cocido",
    leido_cant: "400",
    leido_unid: "g",
    validaciones: { tienda_fachada: "ok", producto: "ok", codigo_barras: "ok", evidencia_precio: "ok" },
    img_facade: "",
    img_product: "",
    img_shelf: "",
    costo: 0,
  },
  {
    capture_id: "CAP-DEMO-002",
    store: "Mercado Centro 22",
    brand: "Brisa Pura",
    product_name: "Aceite vegetal comestible 900 ml",
    qty: "900",
    unit: "ml",
    price_ref: "39.00",
    esperada: "rechazada",
    motor: "rechazada",
    confidence: 0.94,
    reason_code: "CAPTURA_BORROSA",
    explicacion: "La foto de etiqueta está desenfocada y no permite confirmar el precio unitario.",
    precio_detectado: null,
    codigo_barras_detectado: "7501000002025",
    leido_marca: "Brisa Pura",
    leido_desc: "Aceite vegetal",
    leido_cant: "",
    leido_unid: "",
    validaciones: { tienda_fachada: "ok", producto: "ok", codigo_barras: "ok", evidencia_precio: "falla" },
    img_facade: "",
    img_product: "",
    img_shelf: "",
    costo: 0,
  },
  {
    capture_id: "CAP-DEMO-003",
    store: "Supermercado Sur 08",
    brand: "Grano Dorado",
    product_name: "Arroz blanco largo 1 kg",
    qty: "1000",
    unit: "g",
    price_ref: "29.00",
    esperada: "revision_manual",
    motor: "revision_manual",
    confidence: 0.55,
    reason_code: "ETIQUETA_NO_CORRESPONDE",
    explicacion: "La etiqueta muestra dos precios en promoción; se escala a revisión humana (1 pt).",
    precio_detectado: 27.5,
    codigo_barras_detectado: "7501000003039",
    leido_marca: "Grano Dorado",
    leido_desc: "Arroz blanco largo",
    leido_cant: "1",
    leido_unid: "kg",
    validaciones: { tienda_fachada: "ok", producto: "ok", codigo_barras: "ok", evidencia_precio: "falla" },
    img_facade: "",
    img_product: "",
    img_shelf: "",
    costo: 1,
  },
  {
    capture_id: "CAP-DEMO-004",
    store: "Autoservicio Poniente",
    brand: "Lácteos Sierra",
    product_name: "Leche evaporada 360 ml",
    qty: "360",
    unit: "ml",
    price_ref: "21.00",
    esperada: "revision_manual",
    motor: "revision_manual",
    confidence: 0.62,
    reason_code: "DESCRIPCION_INCOMPLETA",
    explicacion: "Contenido parcial por ángulo del empaque; se evita falso positivo (10 pts).",
    precio_detectado: 21.0,
    codigo_barras_detectado: "7501000004043",
    leido_marca: "Lácteos Sierra",
    leido_desc: "Leche evaporada",
    leido_cant: "360",
    leido_unid: "ml",
    validaciones: { tienda_fachada: "ok", producto: "falla", codigo_barras: "ok", evidencia_precio: "ok" },
    img_facade: "",
    img_product: "",
    img_shelf: "",
    costo: 1,
  },
  {
    capture_id: "CAP-DEMO-005",
    store: "Bodega Oriente 15",
    brand: "Hogar Limpio",
    product_name: "Detergente polvo floral 800 g",
    qty: "800",
    unit: "g",
    price_ref: "26.50",
    esperada: "aprobada",
    motor: "aprobada",
    confidence: 0.97,
    reason_code: "",
    explicacion: "Lectura unánime en producto, gramaje y etiqueta vigente.",
    precio_detectado: 26.5,
    codigo_barras_detectado: "7501000005057",
    leido_marca: "Hogar Limpio",
    leido_desc: "Detergente polvo floral",
    leido_cant: "800",
    leido_unid: "g",
    validaciones: { tienda_fachada: "ok", producto: "ok", codigo_barras: "ok", evidencia_precio: "ok" },
    img_facade: "",
    img_product: "",
    img_shelf: "",
    costo: 0,
  },
  {
    capture_id: "CAP-DEMO-006",
    store: "Tienda Norte 104",
    brand: "Molino Real",
    product_name: "Harina para hot cakes 800 g",
    qty: "800",
    unit: "g",
    price_ref: "32.00",
    esperada: "rechazada",
    motor: "rechazada",
    confidence: 0.91,
    reason_code: "CAPTURA_LEJANA",
    explicacion: "Toma general del pasillo impide verificar el contenido neto del empaque.",
    precio_detectado: null,
    codigo_barras_detectado: "7501000006061",
    leido_marca: "Molino Real",
    leido_desc: "Harina preparada",
    leido_cant: "",
    leido_unid: "",
    validaciones: { tienda_fachada: "ok", producto: "falla", codigo_barras: "ok", evidencia_precio: "ok" },
    img_facade: "",
    img_product: "",
    img_shelf: "",
    costo: 0,
  },
];

const U_MAP: Record<string, string> = {
  gramo: "g",
  gramos: "g",
  kilogramo: "kg",
  kilogramos: "kg",
  mililitro: "ml",
  mililitros: "ml",
  litro: "l",
  litros: "l",
  pieza: "pza",
  piezas: "pza",
};

function fmtCont(cant: unknown, unit: unknown): string {
  if (cant === null || cant === undefined || cant === "") return "—";
  const n = Number(cant);
  const ns = Number.isFinite(n)
    ? Number.isInteger(n)
      ? String(n)
      : String(Number(n.toFixed(2)))
    : String(cant);
  const u = String(unit ?? "").trim().toLowerCase();
  return `${ns} ${U_MAP[u] || u}`.trim();
}

function fmtPrecio(val: unknown): string {
  if (val === null || val === undefined || val === "") return "—";
  const n = Number(val);
  return Number.isFinite(n) ? `$${n.toFixed(2)}` : `$${val}`;
}

function normText(s: unknown): string {
  return String(s ?? "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

function toBaseUnit(str: unknown): { v: number; u: string } | null {
  const m = String(str ?? "")
    .trim()
    .toLowerCase()
    .match(
      /^(\d+(?:\.\d+)?)\s*(g|gr|gramo|gramos|kg|kilo|kilos|ml|mililitro|mililitros|l|lt|lts|litro|litros|pza|pz|pieza|piezas)$/
    );
  if (!m) return null;
  const val = Number(m[1]);
  const u = m[2];
  if (["kg", "kilo", "kilos"].includes(u)) return { v: val * 1000, u: "g" };
  if (["g", "gr", "gramo", "gramos"].includes(u)) return { v: val, u: "g" };
  if (["l", "lt", "lts", "litro", "litros"].includes(u)) return { v: val * 1000, u: "ml" };
  if (["ml", "mililitro", "mililitros"].includes(u)) return { v: val, u: "ml" };
  return { v: val, u: "pza" };
}

function diffCampoCls(a: unknown, b: unknown, kind: "marca" | "producto" | "contenido" | "precio"): string {
  if (b === null || b === undefined || b === "" || b === "—") return "";
  if (kind === "precio") {
    const na = Number(String(a ?? "").replace(/[^0-9.-]+/g, ""));
    const nb = Number(String(b ?? "").replace(/[^0-9.-]+/g, ""));
    if (Number.isFinite(na) && Number.isFinite(nb)) {
      return Math.abs(na - nb) > 0.01 ? "font-bold text-danger" : "";
    }
  }
  if (kind === "contenido") {
    const qa = toBaseUnit(a);
    const qb = toBaseUnit(b);
    if (qa && qb) {
      if (qa.u !== qb.u) return "font-bold text-danger";
      const maxV = Math.max(qa.v, qb.v, 1);
      return Math.abs(qa.v - qb.v) / maxV > 0.02 ? "font-bold text-danger" : "";
    }
  }
  const sa = normText(a);
  const sb = normText(b);
  if (!sa || !sb) return "";
  if (sa === sb || sa.replace(/\s+/g, "") === sb.replace(/\s+/g, "")) return "";
  return "font-bold text-danger";
}

function calcularCostoPesimista(motor: Decision | "", esperada: Decision | ""): number | null {
  if (!motor || !esperada) return null;
  if (motor === "revision_manual") return 1;
  if (motor === esperada) return 0;
  if (motor === "aprobada") return 10;
  return 3;
}

function parseCsvTexto(text: string): Record<string, string>[] {
  const lines = text.replace(/^\uFEFF/, "").split(/\r?\n/).filter(Boolean);
  if (!lines.length) return [];
  const splitLine = (line: string) => {
    const out: string[] = [];
    let cur = "";
    let inQ = false;
    for (let i = 0; i < line.length; i++) {
      const c = line[i];
      if (c === '"') {
        if (inQ && line[i + 1] === '"') {
          cur += '"';
          i++;
        } else {
          inQ = !inQ;
        }
      } else if (c === "," && !inQ) {
        out.push(cur);
        cur = "";
      } else {
        cur += c;
      }
    }
    out.push(cur);
    return out;
  };
  const hdr = splitLine(lines[0]);
  return lines.slice(1).map((line) => {
    const vals = splitLine(line);
    const obj: Record<string, string> = {};
    hdr.forEach((h, i) => {
      obj[h.trim()] = vals[i] ?? "";
    });
    return obj;
  });
}

async function extractZipEntriesBrowser(file: File): Promise<{ name: string; bytes: Uint8Array }[]> {
  const buf = await file.arrayBuffer();
  const view = new DataView(buf);
  const bytes = new Uint8Array(buf);
  let eocd = -1;
  for (let i = bytes.length - 22; i >= Math.max(0, bytes.length - 65557); i--) {
    if (view.getUint32(i, true) === 0x06054b50) {
      eocd = i;
      break;
    }
  }
  if (eocd < 0) throw new Error(`El archivo ${file.name} no es un ZIP válido.`);
  const totalEntries = view.getUint16(eocd + 10, true);
  let cdOffset = view.getUint32(eocd + 16, true);
  const dec = new TextDecoder("utf-8");
  const out: { name: string; bytes: Uint8Array }[] = [];

  for (let i = 0; i < totalEntries; i++) {
    if (view.getUint32(cdOffset, true) !== 0x02014b50) break;
    const method = view.getUint16(cdOffset + 10, true);
    const compSize = view.getUint32(cdOffset + 20, true);
    const nameLen = view.getUint16(cdOffset + 28, true);
    const extraLen = view.getUint16(cdOffset + 30, true);
    const commentLen = view.getUint16(cdOffset + 32, true);
    const localOffset = view.getUint32(cdOffset + 42, true);
    const fullName = dec.decode(bytes.subarray(cdOffset + 46, cdOffset + 46 + nameLen));
    cdOffset += 46 + nameLen + extraLen + commentLen;

    if (fullName.endsWith("/")) continue;
    const baseName = fullName.split("/").pop() || "";
    if (!baseName || baseName.startsWith(".")) continue;

    const lNameLen = view.getUint16(localOffset + 26, true);
    const lExtraLen = view.getUint16(localOffset + 28, true);
    const dataStart = localOffset + 30 + lNameLen + lExtraLen;
    const slice = bytes.subarray(dataStart, dataStart + compSize);

    let rawBytes: Uint8Array | null = null;
    if (method === 0) {
      rawBytes = slice;
    } else if (method === 8 && typeof DecompressionStream !== "undefined") {
      const ds = new DecompressionStream("deflate-raw");
      const writer = ds.writable.getWriter();
      writer.write(slice);
      writer.close();
      rawBytes = new Uint8Array(await new Response(ds.readable).arrayBuffer());
    }
    if (rawBytes) out.push({ name: baseName, bytes: rawBytes });
  }
  return out;
}

function ChipDecision({ decision, fallbackLabel = "ciego" }: { decision: Decision | ""; fallbackLabel?: string }) {
  if (!decision) {
    return (
      <span className="inline-flex h-6 items-center gap-1.5 rounded-full bg-info-bg px-2.5 text-xs font-bold text-info">
        <span aria-hidden className="size-2 rounded-full bg-current" />
        {fallbackLabel}
      </span>
    );
  }
  const styles: Record<Decision, string> = {
    aprobada: "bg-success-bg text-success",
    rechazada: "bg-danger-bg text-danger",
    revision_manual: "bg-warning-bg text-warning",
  };
  return (
    <span className={`inline-flex h-6 items-center gap-1.5 rounded-full px-2.5 text-xs font-bold ${styles[decision]}`}>
      <span aria-hidden className="size-2 rounded-full bg-current" />
      {decision}
    </span>
  );
}

export function ConsolaValidat3B() {
  const [registros, setRegistros] = useState<RegistroConsola[]>(DEMO_INICIAL);
  const [esDemoSintetico, setEsDemoSintetico] = useState(true);
  const [tokensPromedio, setTokensPromedio] = useState<number | null>(null);
  const [tab, setTab] = useState<TabId>("resumen");
  const [viewMode, setViewMode] = useState<ViewMode>("cards");
  const [cargando, setCargando] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [alerta, setAlerta] = useState<{ tipo: "ok" | "err"; msg: string } | null>(null);

  // Cachés persistentes en sesión para fusión no destructiva sin importar el orden de subida
  const imgCacheRef = useRef<Record<string, string>>({});
  const resCacheRef = useRef<Record<string, ResultadoOficial>>({});
  const extCacheRef = useRef<Record<string, ExtraccionItem>>({});

  // Filtros globales
  const [query, setQuery] = useState("");
  const [filtroTienda, setFiltroTienda] = useState("");
  const [filtroEsperada, setFiltroEsperada] = useState("");
  const [filtroMotor, setFiltroMotor] = useState("");
  const [soloErrores, setSoloErrores] = useState(false);
  const [soloFp, setSoloFp] = useState(false);
  const [soloFn, setSoloFn] = useState(false);
  const [orden, setOrden] = useState<OrdenId>("original");

  // Cola HITL
  const [hitlIdx, setHitlIdx] = useState(0);
  const [rotaciones, setRotaciones] = useState<Record<string, number>>({});
  const [dictamenAnalista, setDictamenAnalista] = useState<Record<string, "aprobada" | "rechazada">>({});

  // Modales
  const [fotoModal, setFotoModal] = useState<{ label: string; src: string } | null>(null);
  const [jsonModal, setJsonModal] = useState<ResultadoOficial | null>(null);
  const [copiado, setCopiado] = useState(false);

  // Simulador 3 fotos
  const [simFiles, setSimFiles] = useState<{ facade?: File; product?: File; shelf?: File }>({});

  const tiendas = useMemo(
    () => Array.from(new Set(registros.map((r) => r.store).filter(Boolean))).sort(),
    [registros]
  );

  const filtrados = useMemo(() => {
    const q = query.trim().toLowerCase();
    let items = registros.filter((r) => {
      if (filtroTienda && r.store !== filtroTienda) return false;
      if (filtroEsperada && r.esperada !== filtroEsperada) return false;
      if (filtroMotor && r.motor !== filtroMotor) return false;
      if (soloErrores && (!r.esperada || !r.motor || r.esperada === r.motor)) return false;
      if (soloFp && !(r.motor === "aprobada" && r.esperada && r.esperada !== "aprobada")) return false;
      if (soloFn && !(r.motor === "rechazada" && r.esperada === "aprobada")) return false;
      if (q) {
        const hay = `${r.capture_id} ${r.store} ${r.brand} ${r.product_name} ${r.reason_code}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });
    if (orden === "costo-desc") {
      items = [...items].sort((a, b) => (b.costo ?? -1) - (a.costo ?? -1));
    } else if (orden === "costo-asc") {
      items = [...items].sort((a, b) => (a.costo ?? 999) - (b.costo ?? 999));
    }
    return items;
  }, [registros, query, filtroTienda, filtroEsperada, filtroMotor, soloErrores, soloFp, soloFn, orden]);

  const metricas = useMemo(() => {
    const total = filtrados.length;
    let costo = 0;
    let aprobadas = 0;
    let tp = 0;
    let rechazadas = 0;
    let manuales = 0;
    let jsonOk = 0;

    for (const r of filtrados) {
      if (r.costo !== null) costo += r.costo;
      if (r.motor) jsonOk++;
      if (r.motor === "aprobada") {
        aprobadas++;
        if (!r.esperada || r.esperada === "aprobada") tp++;
      } else if (r.motor === "rechazada") {
        rechazadas++;
      } else if (r.motor === "revision_manual") {
        manuales++;
      }
    }

    const precision = aprobadas > 0 ? (tp / aprobadas) * 100 : 100;
    const autoPct = total > 0 ? ((aprobadas + rechazadas) / total) * 100 : 0;
    const jsonPct = total > 0 ? (jsonOk / total) * 100 : 0;

    const porTienda: Record<string, number> = {};
    const porMotivo: Record<string, number> = {};
    for (const r of filtrados) {
      if (r.store) porTienda[r.store] = (porTienda[r.store] || 0) + 1;
      if (r.reason_code) porMotivo[r.reason_code] = (porMotivo[r.reason_code] || 0) + 1;
    }

    return {
      total,
      costo,
      aprobadas,
      tp,
      rechazadas,
      manuales,
      precision,
      autoPct,
      jsonPct,
      tiendasOrdenadas: Object.entries(porTienda).sort((a, b) => b[1] - a[1]),
      motivosOrdenados: Object.entries(porMotivo).sort((a, b) => b[1] - a[1]).slice(0, 6),
    };
  }, [filtrados]);

  const estadoIngesta = useMemo(() => {
    const total = esDemoSintetico ? 0 : registros.length;
    const conFotos = esDemoSintetico
      ? 0
      : registros.filter((d) => Boolean(d.img_facade && d.img_product && d.img_shelf)).length;
    const conRes = esDemoSintetico ? 0 : registros.filter((d) => Boolean(d.motor)).length;
    const conExt = esDemoSintetico
      ? 0
      : registros.filter((d) => Boolean(d.leido_marca || d.leido_desc || d.leido_cant)).length;
    return { total, conFotos, conRes, conExt };
  }, [registros, esDemoSintetico]);

  const colaManual = useMemo(
    () => filtrados.filter((r) => r.motor === "revision_manual" || !r.motor),
    [filtrados]
  );

  const casoActual = colaManual.length ? colaManual[hitlIdx % colaManual.length] : null;

  const marcarHitl = useCallback((cid: string, decision: "aprobada" | "rechazada") => {
    setDictamenAnalista((prev) => ({ ...prev, [cid]: decision }));
    setHitlIdx((i) => i + 1);
  }, []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (tab !== "cola" || !casoActual) return;
      const tag = (e.target as HTMLElement | null)?.tagName || "";
      if (["INPUT", "SELECT", "TEXTAREA"].includes(tag)) return;
      if (e.key === "a" || e.key === "A") marcarHitl(casoActual.capture_id, "aprobada");
      else if (e.key === "r" || e.key === "R") marcarHitl(casoActual.capture_id, "rechazada");
      else if (e.key === "s" || e.key === "S" || e.key === "ArrowRight") setHitlIdx((i) => i + 1);
      else if (e.key === "ArrowLeft") setHitlIdx((i) => (i > 0 ? i - 1 : 0));
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [tab, casoActual, marcarHitl]);

  const sincronizarRegistroConCaches = useCallback((reg: RegistroConsola): RegistroConsola => {
    const imgMap = imgCacheRef.current;
    const extMap = extCacheRef.current;
    const resMap = resCacheRef.current;

    const fName = reg.facade_name || `${reg.capture_id}_facade.jpg`;
    const pName = reg.product_name_file || `${reg.capture_id}_product.jpg`;
    const sName = reg.shelf_name || `${reg.capture_id}_shelf.jpg`;

    const next: RegistroConsola = {
      ...reg,
      facade_name: fName,
      product_name_file: pName,
      shelf_name: sName,
      img_facade: imgMap[fName] || reg.img_facade || "",
      img_product: imgMap[pName] || reg.img_product || "",
      img_shelf: imgMap[sName] || reg.img_shelf || "",
    };

    const ext = extMap[reg.capture_id];
    if (ext) {
      const prod = ext.producto || {};
      const etiq = ext.etiqueta || {};
      next.leido_marca = prod.marca ?? next.leido_marca ?? "";
      next.leido_desc = prod.descripcion ?? next.leido_desc ?? "";
      next.leido_cant = prod.contenido_cantidad != null ? String(prod.contenido_cantidad) : next.leido_cant;
      next.leido_unid = prod.contenido_unidad ?? next.leido_unid ?? "";
      if (next.precio_detectado === null && etiq.precio != null) {
        next.precio_detectado = Number(etiq.precio);
      }
    }

    const res = resMap[reg.capture_id];
    if (res) {
      next.motor = res.decision || next.motor;
      next.confidence = res.confidence_score ?? next.confidence;
      next.reason_code = res.reason_code || "";
      next.explicacion = res.explicacion || next.explicacion;
      next.validaciones = res.validaciones || next.validaciones;
      if (res.precio_detectado !== null && res.precio_detectado !== undefined) {
        next.precio_detectado = res.precio_detectado;
      }
      if (res.codigo_barras_detectado) {
        next.codigo_barras_detectado = res.codigo_barras_detectado;
      }
      next.costo = calcularCostoPesimista(next.motor, next.esperada);
    }
    return next;
  }, []);

  const procesarArchivosUnificados = useCallback(
    async (fileList: FileList | File[] | null) => {
      if (!fileList) return;
      const rawFiles = Array.from(fileList);
      if (!rawFiles.length) return;

      setCargando(true);
      setAlerta(null);
      try {
        interface VirtualEntry {
          name: string;
          getText: () => Promise<string>;
          getBlobUrl: () => string;
        }
        const virtualFiles: VirtualEntry[] = [];

        for (const f of rawFiles) {
          if (f.name.toLowerCase().endsWith(".zip")) {
            const entries = await extractZipEntriesBrowser(f);
            for (const ent of entries) {
              virtualFiles.push({
                name: ent.name,
                getText: () => Promise.resolve(new TextDecoder("utf-8").decode(ent.bytes)),
                getBlobUrl: () => URL.createObjectURL(new Blob([ent.bytes as unknown as BlobPart])),
              });
            }
          } else {
            virtualFiles.push({
              name: f.name,
              getText: () => f.text(),
              getBlobUrl: () => URL.createObjectURL(f),
            });
          }
        }

        let nImgs = 0;
        let nCaps = 0;
        let nRes = 0;
        let nExt = 0;
        let nTok = 0;
        let nuevasFilasBase: Record<string, string>[] | null = null;

        // 1. Imágenes
        for (const vf of virtualFiles) {
          const low = vf.name.toLowerCase();
          if (/\.(jpg|jpeg|png|webp)$/.test(low)) {
            imgCacheRef.current[vf.name] = vf.getBlobUrl();
            nImgs++;
          }
        }

        // 2. CSV y JSON
        for (const vf of virtualFiles) {
          const low = vf.name.toLowerCase();
          if (low.endsWith(".csv") && !low.includes("catalogo")) {
            const rows = parseCsvTexto(await vf.getText());
            if (!rows.length) continue;
            if ("tokens_entrada" in rows[0]) {
              const tRows = rows.filter((r) => (!r.origen || r.origen === "modelo") && (r.tokens_entrada || r.tokens_salida));
              if (tRows.length) {
                const cids = new Set(tRows.map((r) => r.capture_id).filter(Boolean));
                const sum = tRows.reduce(
                  (acc, r) => acc + Number(r.tokens_entrada || 0) + Number(r.tokens_salida || 0),
                  0
                );
                const denom = cids.size || tRows.length;
                setTokensPromedio(Math.round(sum / denom));
                nTok = tRows.length;
              }
            } else if ("capture_id" in rows[0]) {
              nuevasFilasBase = rows;
              nCaps = rows.length;
            }
          } else if (low.endsWith(".json")) {
            try {
              const parsed = JSON.parse(await vf.getText());
              if (Array.isArray(parsed) || Array.isArray(parsed?.capturas)) {
                const arr = Array.isArray(parsed) ? parsed : parsed.capturas;
                if (!arr.length) continue;
                if (arr[0].producto || arr[0].etiqueta) {
                  for (const item of arr as ExtraccionItem[]) {
                    if (item && item.capture_id) extCacheRef.current[item.capture_id] = item;
                  }
                  nExt = arr.length;
                } else if (arr[0].decision) {
                  for (const item of arr as ResultadoOficial[]) {
                    if (item && item.capture_id) resCacheRef.current[item.capture_id] = item;
                  }
                  nRes = arr.length;
                } else if (arr[0].capture_id) {
                  nuevasFilasBase = arr;
                  nCaps = arr.length;
                }
              } else if (parsed && parsed.capture_id && parsed.decision) {
                resCacheRef.current[parsed.capture_id] = parsed as ResultadoOficial;
                nRes++;
              }
            } catch {
              // Ignorar JSON ajeno al esquema
            }
          }
        }

        setRegistros((prev) => {
          const base =esDemoSintetico ? [] : prev;
          const prevMap = new Map(base.map((r) => [r.capture_id, r]));

          if (nuevasFilasBase) {
            return nuevasFilasBase.map((r) => {
              const cid = String(r.capture_id || "");
              const old = prevMap.get(cid);
              const fName = String(r.facade_file || old?.facade_name || `${cid}_facade.jpg`).split("/").pop() || "";
              const pName = String(r.product_file || old?.product_name_file || `${cid}_product.jpg`).split("/").pop() || "";
              const sName = String(r.shelf_file || old?.shelf_name || `${cid}_shelf.jpg`).split("/").pop() || "";
              const esperada = (r.decision_esperada ?? old?.esperada ?? "") as Decision | "";
              const merged: RegistroConsola = {
                capture_id: cid,
                store: r.capture_store_name || old?.store || "",
                brand: r.capture_brand || old?.brand || "",
                product_name: r.product_name || old?.product_name || "",
                qty: String(r.unit_quantity_product ?? old?.qty ?? ""),
                unit: r.unit_product || old?.unit || "",
                price_ref: String(r.capture_price ?? old?.price_ref ?? ""),
                esperada,
                motivo_esperado: r.motivo_rechazo ?? old?.motivo_esperado ?? "",
                motor: old?.motor || "",
                confidence: old?.confidence ?? null,
                reason_code: old?.reason_code || "",
                explicacion: old?.explicacion || "",
                precio_detectado: old?.precio_detectado ?? null,
                codigo_barras_detectado: r.capture_barcode || old?.codigo_barras_detectado || "",
                leido_marca: old?.leido_marca || "",
                leido_desc: old?.leido_desc || "",
                leido_cant: old?.leido_cant || "",
                leido_unid: old?.leido_unid || "",
                validaciones: old?.validaciones || {
                  tienda_fachada: "ok",
                  producto: "ok",
                  codigo_barras: "ok",
                  evidencia_precio: "ok",
                },
                facade_name: fName,
                product_name_file: pName,
                shelf_name: sName,
                img_facade: old?.img_facade || r.facade_url || "",
                img_product: old?.img_product || r.product_url || "",
                img_shelf: old?.img_shelf || r.shelf_url || "",
                costo: old?.costo ?? null,
              };
              return sincronizarRegistroConCaches(merged);
            });
          }

          if (!base.length && Object.keys(resCacheRef.current).length > 0) {
            return Object.values(resCacheRef.current).map((res) =>
              sincronizarRegistroConCaches({
                capture_id: res.capture_id,
                store: "Set cargado",
                brand: "—",
                product_name: "Sube capturas.csv para ver producto esperado",
                qty: "",
                unit: "",
                price_ref: res.precio_detectado != null ? String(res.precio_detectado) : "0",
                esperada: "",
                motor: res.decision,
                confidence: res.confidence_score,
                reason_code: res.reason_code || "",
                explicacion: res.explicacion || "",
                precio_detectado: res.precio_detectado,
                codigo_barras_detectado: res.codigo_barras_detectado || "",
                leido_marca: "",
                leido_desc: "",
                leido_cant: "",
                leido_unid: "",
                validaciones: res.validaciones,
                facade_name: `${res.capture_id}_facade.jpg`,
                product_name_file: `${res.capture_id}_product.jpg`,
                shelf_name: `${res.capture_id}_shelf.jpg`,
                img_facade: "",
                img_product: "",
                img_shelf: "",
                costo: null,
              })
            );
          }

          return base.map((reg) => sincronizarRegistroConCaches(reg));
        });

        setEsDemoSintetico(false);
        setHitlIdx(0);

        const partes: string[] = [];
        if (nCaps) partes.push(`${nCaps} capturas`);
        if (nImgs) partes.push(`${nImgs} fotos`);
        if (nRes) partes.push(`${nRes} veredictos`);
        if (nExt) partes.push(`${nExt} lecturas del modelo`);
        if (nTok) partes.push("métricas de tokens");

        if (!partes.length) {
          setAlerta({
            tipo: "err",
            msg: "No se detectaron archivos compatibles (.zip, capturas.csv, resultados.json, extracciones.json o fotos).",
          });
        } else {
          setAlerta({
            tipo: "ok",
            msg: `Lote actualizado sin perder datos previos: ${partes.join(" · ")}.`,
          });
        }
      } catch (err) {
        setAlerta({
          tipo: "err",
          msg: err instanceof Error ? err.message : "No se pudieron procesar los archivos seleccionados.",
        });
      } finally {
        setCargando(false);
      }
    },
    [esDemoSintetico, sincronizarRegistroConCaches]
  );

  function limpiarLoteParaSubir() {
    imgCacheRef.current = {};
    resCacheRef.current = {};
    extCacheRef.current = {};
    setRegistros([]);
    setTokensPromedio(null);
    setEsDemoSintetico(false);
    setHitlIdx(0);
    setAlerta({
      tipo: "ok",
      msg: "Lote reiniciado. Arrastra o selecciona tus archivos .zip, carpetas o JSON/CSV en la zona unificada.",
    });
  }

  function agregarCapturaSimulada() {
    if (!simFiles.facade || !simFiles.product || !simFiles.shelf) {
      setAlerta({
        tipo: "err",
        msg: "Selecciona las tres fotos (fachada, producto y etiqueta) antes de cargar la captura.",
      });
      return;
    }
    const nueva: RegistroConsola = {
      capture_id: `CAP-VIVO-${String(Date.now()).slice(-4)}`,
      store: "Captura en vivo",
      brand: "Muestra local",
      product_name: "Producto cargado desde navegador",
      qty: "1",
      unit: "pza",
      price_ref: "0.00",
      esperada: "",
      motor: "revision_manual",
      confidence: 0.5,
      reason_code: "SIN_LECTURA",
      explicacion: "Evidencia lista en memoria local para inspección o corrida en el motor Python.",
      precio_detectado: null,
      codigo_barras_detectado: "",
      leido_marca: "",
      leido_desc: "",
      leido_cant: "",
      leido_unid: "",
      validaciones: { tienda_fachada: "ok", producto: "ok", codigo_barras: "ok", evidencia_precio: "ok" },
      img_facade: URL.createObjectURL(simFiles.facade),
      img_product: URL.createObjectURL(simFiles.product),
      img_shelf: URL.createObjectURL(simFiles.shelf),
      costo: 1,
    };
    setRegistros((prev) => [nueva, ...prev]);
    setEsDemoSintetico(false);
    setTab("cola");
    setHitlIdx(0);
    setAlerta({ tipo: "ok", msg: `Captura ${nueva.capture_id} agregada a la cola de revisión.` });
  }

  function exportarCsv() {
    const cols = [
      "capture_id",
      "store",
      "brand",
      "product_name",
      "price_ref",
      "precio_detectado",
      "motor",
      "reason_code",
      "confidence",
      "explicacion",
    ] as const;
    const cell = (v: unknown) => `"${String(v ?? "").replace(/"/g, '""')}"`;
    const rows = [
      cols.join(","),
      ...filtrados.map((r) => cols.map((c) => cell(r[c])).join(",")),
    ];
    const blob = new Blob(["\uFEFF" + rows.join("\n")], { type: "text/csv;charset=utf-8;" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "validat3b_auditoria.csv";
    a.click();
  }

  function limpiarFiltros() {
    setQuery("");
    setFiltroTienda("");
    setFiltroEsperada("");
    setFiltroMotor("");
    setSoloErrores(false);
    setSoloFp(false);
    setSoloFn(false);
    setOrden("original");
  }

  function abrirJson(r: RegistroConsola) {
    setJsonModal({
      capture_id: r.capture_id,
      decision: (r.motor || "revision_manual") as Decision,
      confidence_score: r.confidence ?? 0,
      reason_code: r.reason_code || null,
      validaciones: r.validaciones,
      precio_detectado: r.precio_detectado,
      codigo_barras_detectado: r.codigo_barras_detectado || null,
      explicacion: r.explicacion || "Sin veredicto cargado.",
    });
  }

  const maxTienda = Math.max(1, ...metricas.tiendasOrdenadas.map((x) => x[1]));
  const maxMotivo = Math.max(1, ...metricas.motivosOrdenados.map((x) => x[1]));

  return (
    <div className="space-y-6">
      {/* Encabezado de consola y pestañas */}
      <div className="flex flex-col gap-4 border-b border-border pb-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="font-heading text-2xl font-extrabold tracking-tight text-foreground">
            Validat3B · Consola Operativa
          </h1>
          <p className="text-sm text-text-tertiary">
            {esDemoSintetico
              ? "Prototipo para Tiendas 3B · Modo offline sin dependencias (Sube tu lote o .zip en 4. Cargar set ciego)"
              : `Prototipo para Tiendas 3B · ${filtrados.length} de ${registros.length} capturas cargadas`}
          </p>
        </div>

        <div className="flex flex-wrap gap-2" role="tablist" aria-label="Módulos de Validat3B">
          {(
            [
              ["resumen", "1. Resumen ejecutivo"],
              ["cola", "2. Cola revisión manual"],
              ["auditoria", "3. Explorador auditoría"],
              ["ingesta", "4. Cargar set ciego"],
            ] as const
          ).map(([id, label]) => (
            <Button
              key={id}
              type="button"
              variant={tab === id ? "secondary" : "outline"}
              className={tab === id ? "border-foreground bg-foreground font-semibold text-background hover:bg-foreground" : undefined}
              onClick={() => setTab(id)}
            >
              {label}
            </Button>
          ))}
        </div>
      </div>

      {/* Aviso de estado / error */}
      {alerta && (
        <div
          role={alerta.tipo === "err" ? "alert" : "status"}
          className={`rounded-lg border p-4 text-sm ${
            alerta.tipo === "err"
              ? "border-danger bg-danger-bg text-danger"
              : "border-success bg-success-bg text-success"
          }`}
        >
          <p className="font-semibold">{alerta.msg}</p>
        </div>
      )}

      {/* Filtros globales (idénticos al visor) */}
      <div className="flex flex-wrap items-center gap-2 rounded-lg border border-border bg-surface-2 p-3">
        <div className="relative min-w-60 flex-1">
          <Search className="pointer-events-none absolute top-3.5 left-3 size-4 text-text-muted" />
          <Input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Buscar capture_id, marca, producto o tienda..."
            className="pl-9"
            aria-label="Buscar captura"
          />
        </div>
        <select
          value={filtroTienda}
          onChange={(e) => setFiltroTienda(e.target.value)}
          aria-label="Filtrar por cadena"
          className="h-11 rounded-md border border-input bg-background px-3 text-sm font-medium text-foreground"
        >
          <option value="">Cadena: Todas</option>
          {tiendas.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
        <select
          value={filtroEsperada}
          onChange={(e) => setFiltroEsperada(e.target.value)}
          aria-label="Filtrar por esperada"
          className="h-11 rounded-md border border-input bg-background px-3 text-sm font-medium text-foreground"
        >
          <option value="">Esperada: Todas</option>
          <option value="aprobada">Esperada: aprobada</option>
          <option value="rechazada">Esperada: rechazada</option>
          <option value="revision_manual">Esperada: revision_manual</option>
        </select>
        <select
          value={filtroMotor}
          onChange={(e) => setFiltroMotor(e.target.value)}
          aria-label="Filtrar por motor"
          className="h-11 rounded-md border border-input bg-background px-3 text-sm font-medium text-foreground"
        >
          <option value="">Motor: Todas</option>
          <option value="aprobada">Motor: aprobada</option>
          <option value="rechazada">Motor: rechazada</option>
          <option value="revision_manual">Motor: revision_manual</option>
        </select>
        <label className="inline-flex h-11 cursor-pointer items-center gap-2 rounded-md border border-input bg-background px-3 text-sm font-semibold text-foreground">
          <input
            type="checkbox"
            checked={soloErrores}
            onChange={(e) => setSoloErrores(e.target.checked)}
          />
          Solo errores
        </label>
        <Button
          type="button"
          variant={soloFp ? "destructive" : "outline"}
          onClick={() => setSoloFp((v) => !v)}
        >
          Aprobadas falsas
        </Button>
        <Button
          type="button"
          variant={soloFn ? "destructive" : "outline"}
          onClick={() => setSoloFn((v) => !v)}
        >
          Válidas rechazadas
        </Button>
        <Button type="button" onClick={exportarCsv}>
          <Download className="size-4" />
          Exportar CSV
        </Button>
        <Button type="button" variant="outline" onClick={limpiarFiltros}>
          Limpiar
        </Button>
      </div>

      {/* Cargando */}
      {cargando && (
        <div className="grid gap-4 md:grid-cols-4">
          {[0, 1, 2, 3].map((k) => (
            <Skeleton key={k} className="h-28 w-full rounded-lg bg-muted" />
          ))}
        </div>
      )}

      {/* MÓDULO 1: RESUMEN EJECUTIVO */}
      {!cargando && tab === "resumen" && (
        <div className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Card className="border border-border bg-surface-2 shadow-none">
              <CardHeader className="pb-2">
                <CardTitle className="text-xs font-semibold uppercase tracking-wide text-text-secondary">
                  Precisión en aprobadas
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="inline-block border-b-2 border-primary pb-0.5 font-heading text-3xl font-extrabold tabular-nums text-foreground">
                  {metricas.precision.toFixed(1)} %
                </p>
                <p className="mt-2 text-xs text-text-muted">
                  {metricas.tp} de {metricas.aprobadas} aprobadas · meta oficial ≥ 97 %
                </p>
              </CardContent>
            </Card>

            <Card className="border border-border bg-surface-2 shadow-none">
              <CardHeader className="pb-2">
                <CardTitle className="text-xs font-semibold uppercase tracking-wide text-text-secondary">
                  Costo operativo pesimista
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="font-heading text-3xl font-extrabold tabular-nums text-foreground">
                  {metricas.costo} pts
                </p>
                <p className="mt-2 text-xs text-text-muted">
                  vs. {metricas.total} pts de enviar todo a revisión manual
                </p>
              </CardContent>
            </Card>

            <Card className="border border-border bg-surface-2 shadow-none">
              <CardHeader className="pb-2">
                <CardTitle className="text-xs font-semibold uppercase tracking-wide text-text-secondary">
                  Automatización sin persona
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="font-heading text-3xl font-extrabold tabular-nums text-foreground">
                  {metricas.autoPct.toFixed(0)} %
                </p>
                <p className="mt-2 text-xs text-text-muted">
                  {metricas.aprobadas + metricas.rechazadas} de {metricas.total} resueltas automáticamente
                </p>
              </CardContent>
            </Card>

            <Card className="border border-border bg-surface-2 shadow-none">
              <CardHeader className="pb-2">
                <CardTitle className="text-xs font-semibold uppercase tracking-wide text-text-secondary">
                  Salud JSON · Eficiencia
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="font-heading text-3xl font-extrabold tabular-nums text-foreground">
                  {metricas.jsonPct.toFixed(0)} %
                </p>
                <p className="mt-2 text-xs text-text-muted">
                  {tokensPromedio !== null ? `${tokensPromedio.toLocaleString("es-MX")} tok/captura` : "Meta JSON ≥ 99 %"}
                </p>
              </CardContent>
            </Card>
          </div>

          <div className="grid gap-4 lg:grid-cols-3">
            <Card className="border border-border shadow-none">
              <CardHeader>
                <CardTitle className="text-base font-bold">Distribución de decisiones</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {(
                  [
                    ["aprobada", metricas.aprobadas, "bg-success"],
                    ["rechazada", metricas.rechazadas, "bg-danger"],
                    ["revision_manual", metricas.manuales, "bg-warning"],
                  ] as const
                ).map(([dec, count, barCls]) => (
                  <button
                    key={dec}
                    type="button"
                    onClick={() => setFiltroMotor(filtroMotor === dec ? "" : dec)}
                    className="flex w-full items-center gap-3 text-left text-sm"
                  >
                    <span className="w-28 truncate font-medium text-text-secondary">{dec}</span>
                    <div className="h-3 flex-1 overflow-hidden rounded-full bg-muted">
                      <div
                        className={`h-full rounded-full ${barCls}`}
                        style={{ width: `${metricas.total ? (count / metricas.total) * 100 : 0}%` }}
                      />
                    </div>
                    <span className="w-8 text-right font-mono font-semibold tabular-nums">{count}</span>
                  </button>
                ))}
              </CardContent>
            </Card>

            <Card className="border border-border shadow-none">
              <CardHeader>
                <CardTitle className="text-base font-bold">Capturas por cadena competidora</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {metricas.tiendasOrdenadas.map(([st, count]) => (
                  <button
                    key={st}
                    type="button"
                    onClick={() => setFiltroTienda(filtroTienda === st ? "" : st)}
                    className="flex w-full items-center gap-3 text-left text-sm"
                  >
                    <span className="w-32 truncate font-medium text-text-secondary">{st}</span>
                    <div className="h-3 flex-1 overflow-hidden rounded-full bg-muted">
                      <div
                        className="h-full rounded-full bg-chart-1"
                        style={{ width: `${(count / maxTienda) * 100}%` }}
                      />
                    </div>
                    <span className="w-8 text-right font-mono font-semibold tabular-nums">{count}</span>
                  </button>
                ))}
              </CardContent>
            </Card>

            <Card className="border border-border shadow-none">
              <CardHeader>
                <CardTitle className="text-base font-bold">Motivos de rechazo / alerta (reason_code)</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {metricas.motivosOrdenados.length ? (
                  metricas.motivosOrdenados.map(([rc, count]) => (
                    <button
                      key={rc}
                      type="button"
                      onClick={() => setQuery(rc)}
                      className="flex w-full items-center gap-3 text-left text-sm"
                    >
                      <span className="w-36 truncate font-mono text-xs text-text-secondary">{rc}</span>
                      <div className="h-3 flex-1 overflow-hidden rounded-full bg-muted">
                        <div
                          className="h-full rounded-full bg-chart-3"
                          style={{ width: `${(count / maxMotivo) * 100}%` }}
                        />
                      </div>
                      <span className="w-8 text-right font-mono font-semibold tabular-nums">{count}</span>
                    </button>
                  ))
                ) : (
                  <p className="text-sm text-text-muted">Sin motivos registrados en la vista actual.</p>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* MÓDULO 2: COLA DE REVISIÓN MANUAL */}
      {!cargando && tab === "cola" && (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-border bg-surface-2 p-4">
            <div className="flex flex-wrap items-center gap-3">
              <span className="font-heading text-base font-bold">
                Caso {colaManual.length ? `${(hitlIdx % colaManual.length) + 1} de ${colaManual.length}` : "0"} en cola
              </span>
              {casoActual && (
                <span className="font-mono text-sm text-text-tertiary">
                  {casoActual.capture_id} · {casoActual.store}
                </span>
              )}
              {casoActual && dictamenAnalista[casoActual.capture_id] && (
                <ChipDecision decision={dictamenAnalista[casoActual.capture_id]} />
              )}
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs text-text-muted">
                Revisadas: {Object.keys(dictamenAnalista).length}
              </span>
              <Button
                type="button"
                variant="outline"
                onClick={() => setHitlIdx((i) => (i > 0 ? i - 1 : 0))}
                disabled={!colaManual.length}
              >
                ← Anterior
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => setHitlIdx((i) => i + 1)}
                disabled={!colaManual.length}
              >
                Siguiente (S) →
              </Button>
            </div>
          </div>

          {!casoActual ? (
            <div className="rounded-lg border border-border p-8 text-center">
              <p className="text-base font-semibold text-foreground">No hay capturas en revisión manual</p>
              <p className="mt-1 text-sm text-text-tertiary">
                Ajusta los filtros superiores o carga tu lote en la pestaña 4. Cargar set ciego.
              </p>
            </div>
          ) : (
            <div className="grid gap-4 lg:grid-cols-3">
              <div className="grid gap-3 sm:grid-cols-3 lg:col-span-2">
                {(
                  [
                    ["Fachada", casoActual.img_facade, "f"],
                    ["Producto", casoActual.img_product, "p"],
                    ["Etiqueta", casoActual.img_shelf, "s"],
                  ] as const
                ).map(([label, src, key]) => {
                  const deg = rotaciones[`${casoActual.capture_id}_${key}`] || 0;
                  return (
                    <Card key={key} className="border border-border shadow-none">
                      <CardHeader className="flex flex-row items-center justify-between pb-2">
                        <CardTitle className="text-sm font-semibold">{label}</CardTitle>
                        <div className="flex gap-1">
                          <Button
                            type="button"
                            variant="outline"
                            size="icon"
                            aria-label={`Rotar ${label}`}
                            onClick={() =>
                              setRotaciones((prev) => ({
                                ...prev,
                                [`${casoActual.capture_id}_${key}`]: (deg + 90) % 360,
                              }))
                            }
                          >
                            <RotateCw className="size-4" />
                          </Button>
                          {src && (
                            <Button
                              type="button"
                              variant="outline"
                              size="icon"
                              aria-label={`Ampliar ${label}`}
                              onClick={() => setFotoModal({ label, src })}
                            >
                              <ZoomIn className="size-4" />
                            </Button>
                          )}
                        </div>
                      </CardHeader>
                      <CardContent>
                        {src ? (
                          <div className="flex h-56 items-center justify-center overflow-hidden rounded-md border border-border bg-surface-2">
                            {/* eslint-disable-next-line @next/next/no-img-element */}
                            <img
                              src={src}
                              alt={`${label} ${casoActual.capture_id}`}
                              style={{ transform: `rotate(${deg}deg)` }}
                              className="max-h-full max-w-full cursor-zoom-in object-contain"
                              onClick={() => setFotoModal({ label, src })}
                            />
                          </div>
                        ) : (
                          <div className="flex h-56 flex-col items-center justify-center rounded-md border border-dashed border-border bg-surface-2 p-4 text-center text-xs text-text-muted">
                            <ImagePlus className="mb-2 size-6" />
                            <span>Sube las imágenes o el .zip en la pestaña 4 para ver la foto aquí.</span>
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  );
                })}
              </div>

              <Card className="border border-border shadow-none">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <ChipDecision decision={casoActual.motor} fallbackLabel="sin veredicto" />
                    <span className="font-mono text-xs text-text-muted">
                      Confianza: {casoActual.confidence !== null ? casoActual.confidence.toFixed(2) : "—"} · Riesgo evitar FP: 10 pts
                    </span>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Campo</TableHead>
                        <TableHead>Esperado</TableHead>
                        <TableHead>Leído por modelo</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      <TableRow>
                        <TableCell>Marca</TableCell>
                        <TableCell>{casoActual.brand}</TableCell>
                        <TableCell className={diffCampoCls(casoActual.brand, casoActual.leido_marca, "marca")}>
                          {casoActual.leido_marca || "—"}
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Producto</TableCell>
                        <TableCell>{casoActual.product_name}</TableCell>
                        <TableCell className={diffCampoCls(casoActual.product_name, casoActual.leido_desc, "producto")}>
                          {casoActual.leido_desc || "—"}
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Contenido</TableCell>
                        <TableCell>{fmtCont(casoActual.qty, casoActual.unit)}</TableCell>
                        <TableCell
                          className={diffCampoCls(
                            fmtCont(casoActual.qty, casoActual.unit),
                            fmtCont(casoActual.leido_cant, casoActual.leido_unid),
                            "contenido"
                          )}
                        >
                          {fmtCont(casoActual.leido_cant, casoActual.leido_unid)}
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Precio</TableCell>
                        <TableCell className="font-mono">{fmtPrecio(casoActual.price_ref)}</TableCell>
                        <TableCell
                          className={`font-mono ${diffCampoCls(casoActual.price_ref, casoActual.precio_detectado, "precio")}`}
                        >
                          {fmtPrecio(casoActual.precio_detectado)}
                        </TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>

                  <p className="text-sm text-text-secondary">
                    <strong className="text-foreground">Motivo / Explicación:</strong>{" "}
                    {casoActual.reason_code || "—"} — {casoActual.explicacion || "Sin explicación"}
                  </p>

                  <div className="flex flex-wrap gap-2 pt-2">
                    <Button
                      type="button"
                      onClick={() => marcarHitl(casoActual.capture_id, "aprobada")}
                      className="flex-1"
                    >
                      <CheckCircle2 className="size-4" />
                      Aprobar (A)
                    </Button>
                    <Button
                      type="button"
                      variant="destructive"
                      onClick={() => marcarHitl(casoActual.capture_id, "rechazada")}
                      className="flex-1"
                    >
                      Rechazar (R)
                    </Button>
                    <Button type="button" variant="outline" onClick={() => abrirJson(casoActual)}>
                      <FileJson className="size-4" />
                      Ver JSON oficial
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      )}

      {/* MÓDULO 3: EXPLORADOR AUDITORÍA (Versión original de tarjetas con 3 fotos + tabla Esperado/Leído + chips Esp/Mot) */}
      {!cargando && tab === "auditoria" && (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <span className="text-sm font-bold text-foreground">
              {filtrados.length} de {registros.length} capturas
            </span>
            <div className="flex flex-wrap items-center gap-2">
              <Button
                type="button"
                variant={viewMode === "cards" ? "destructive" : "outline"}
                onClick={() => setViewMode("cards")}
              >
                Vista tarjetas
              </Button>
              <Button
                type="button"
                variant={viewMode === "table" ? "destructive" : "outline"}
                onClick={() => setViewMode("table")}
              >
                Vista tabla (52 px)
              </Button>
              <select
                value={orden}
                onChange={(e) => setOrden(e.target.value as OrdenId)}
                aria-label="Ordenar"
                className="h-11 rounded-md border border-input bg-background px-3 text-sm font-medium text-foreground"
              >
                <option value="original">Orden: Original</option>
                <option value="costo-desc">Mayor costo primero</option>
                <option value="costo-asc">Menor costo primero</option>
              </select>
            </div>
          </div>

          {!filtrados.length ? (
            <div className="rounded-lg border border-border p-8 text-center">
              <p className="font-semibold">Ninguna captura coincide con los filtros.</p>
              <Button type="button" variant="outline" className="mt-3" onClick={limpiarFiltros}>
                Limpiar filtros
              </Button>
            </div>
          ) : viewMode === "table" ? (
            <div className="overflow-x-auto rounded-lg border border-border">
              <Table>
                <TableHeader>
                  <TableRow className="bg-surface-2">
                    <TableHead>ID</TableHead>
                    <TableHead>Cadena</TableHead>
                    <TableHead>Producto</TableHead>
                    <TableHead>Precio Esp/Det</TableHead>
                    <TableHead>Esperada</TableHead>
                    <TableHead>Motor</TableHead>
                    <TableHead>Motivo</TableHead>
                    <TableHead>Costo</TableHead>
                    <TableHead className="text-right">Acción</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filtrados.map((r) => (
                    <TableRow key={r.capture_id} className="h-[52px]">
                      <TableCell className="font-mono font-bold">{r.capture_id}</TableCell>
                      <TableCell>{r.store}</TableCell>
                      <TableCell className="max-w-xs truncate" title={`${r.brand} — ${r.product_name}`}>
                        {r.brand} — {r.product_name}
                      </TableCell>
                      <TableCell className="font-mono tabular-nums">
                        {fmtPrecio(r.price_ref)} / {fmtPrecio(r.precio_detectado)}
                      </TableCell>
                      <TableCell>
                        <ChipDecision decision={r.esperada} fallbackLabel="ciego" />
                      </TableCell>
                      <TableCell>
                        {r.motor ? <ChipDecision decision={r.motor} /> : "—"}
                      </TableCell>
                      <TableCell className="font-mono text-xs text-text-tertiary">
                        {r.reason_code || "—"}
                      </TableCell>
                      <TableCell className="font-mono tabular-nums">
                        {r.costo !== null ? `${r.costo} pts` : "—"}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button type="button" variant="outline" onClick={() => abrirJson(r)}>
                          JSON
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {filtrados.map((r) => {
                const esError = Boolean(r.esperada && r.motor && r.esperada !== r.motor);
                const espCont = fmtCont(r.qty, r.unit);
                const leidoCont = fmtCont(r.leido_cant, r.leido_unid);
                return (
                  <article
                    key={r.capture_id}
                    className={`flex flex-col gap-2.5 rounded-lg border bg-background p-3.5 ${
                      esError ? "border-danger" : "border-border"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-mono text-sm">
                        <strong>{r.capture_id}</strong> · {r.store}
                      </span>
                      <button
                        type="button"
                        onClick={() => abrirJson(r)}
                        className="min-h-8 cursor-pointer rounded-md border border-border bg-background px-2.5 text-xs font-semibold text-foreground hover:bg-surface-2"
                      >
                        JSON · {r.costo !== null ? `${r.costo} pts` : "—"}
                      </button>
                    </div>

                    <div className="grid grid-cols-3 gap-1.5">
                      {(
                        [
                          ["Fachada", r.img_facade],
                          ["Producto", r.img_product],
                          ["Etiqueta", r.img_shelf],
                        ] as const
                      ).map(([lbl, src]) =>
                        src ? (
                          // eslint-disable-next-line @next/next/no-img-element
                          <img
                            key={lbl}
                            src={src}
                            alt={lbl}
                            loading="lazy"
                            onClick={() => setFotoModal({ label: `${lbl} · ${r.capture_id}`, src })}
                            className="h-[92px] w-full cursor-zoom-in rounded-md border border-border bg-surface-2 object-cover"
                          />
                        ) : (
                          <div
                            key={lbl}
                            className="flex h-[92px] items-center justify-center rounded-md border border-border bg-surface-2 text-xs text-text-muted"
                          >
                            {lbl}
                          </div>
                        )
                      )}
                    </div>

                    <table className="w-full border-collapse text-xs">
                      <thead>
                        <tr className="border-b border-border bg-surface-2 text-left font-semibold text-text-secondary">
                          <th className="px-2 py-1.5">Campo</th>
                          <th className="px-2 py-1.5">Esperado</th>
                          <th className="px-2 py-1.5">Leído</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr className="border-b border-border">
                          <td className="px-2 py-1.5">Marca</td>
                          <td className="px-2 py-1.5">{r.brand}</td>
                          <td className={`px-2 py-1.5 ${diffCampoCls(r.brand, r.leido_marca, "marca")}`}>
                            {r.leido_marca || "—"}
                          </td>
                        </tr>
                        <tr className="border-b border-border">
                          <td className="px-2 py-1.5">Producto</td>
                          <td className="px-2 py-1.5">{r.product_name}</td>
                          <td className={`px-2 py-1.5 ${diffCampoCls(r.product_name, r.leido_desc, "producto")}`}>
                            {r.leido_desc || "—"}
                          </td>
                        </tr>
                        <tr className="border-b border-border">
                          <td className="px-2 py-1.5">Contenido</td>
                          <td className="px-2 py-1.5">{espCont}</td>
                          <td className={`px-2 py-1.5 ${diffCampoCls(espCont, leidoCont, "contenido")}`}>
                            {leidoCont}
                          </td>
                        </tr>
                        <tr className="border-b border-border">
                          <td className="px-2 py-1.5">Precio</td>
                          <td className="px-2 py-1.5">{fmtPrecio(r.price_ref)}</td>
                          <td className={`px-2 py-1.5 ${diffCampoCls(r.price_ref, r.precio_detectado, "precio")}`}>
                            {fmtPrecio(r.precio_detectado)}
                          </td>
                        </tr>
                      </tbody>
                    </table>

                    <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
                      <span className="inline-flex items-center gap-1.5">
                        Esp: <ChipDecision decision={r.esperada} fallbackLabel="ciego" />
                      </span>
                      <span className="inline-flex items-center gap-1.5">
                        Mot: {r.motor ? <ChipDecision decision={r.motor} /> : "—"}
                      </span>
                    </div>

                    {r.explicacion && (
                      <div className="text-xs leading-relaxed text-text-secondary">{r.explicacion}</div>
                    )}
                  </article>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* MÓDULO 4: CARGAR SET CIEGO (Zona Única Inteligente + Checklist + Fusión incremental) */}
      {!cargando && tab === "ingesta" && (
        <div className="space-y-5">
          <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-border bg-surface-2 p-4">
            <div className="flex flex-wrap items-center gap-2">
              <strong className="text-sm font-bold">Estado del lote activo:</strong>
              <Button type="button" variant="outline" onClick={limpiarLoteParaSubir}>
                Nuevo lote vacío
              </Button>
            </div>
            <Button type="button" onClick={() => setTab("auditoria")}>
              Ver en 3. Explorador auditoría →
            </Button>
          </div>

          {/* Checklist de 4 pasos en vivo */}
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <div
              className={`rounded-lg border p-3 ${
                estadoIngesta.total > 0 ? "border-success bg-success-bg" : "border-border bg-background"
              }`}
            >
              <span
                className={`block text-xs font-bold uppercase ${
                  estadoIngesta.total > 0 ? "text-success" : "text-text-secondary"
                }`}
              >
                1. Padrón (capturas.csv)
              </span>
              <span className="mt-1 block text-sm font-bold text-foreground">
                {estadoIngesta.total > 0 ? `${estadoIngesta.total} capturas cargadas` : "Pendiente de subir"}
              </span>
            </div>

            <div
              className={`rounded-lg border p-3 ${
                estadoIngesta.total > 0 && estadoIngesta.conFotos === estadoIngesta.total
                  ? "border-success bg-success-bg"
                  : "border-border bg-background"
              }`}
            >
              <span
                className={`block text-xs font-bold uppercase ${
                  estadoIngesta.total > 0 && estadoIngesta.conFotos === estadoIngesta.total
                    ? "text-success"
                    : "text-text-secondary"
                }`}
              >
                2. Fotografías (3 por captura)
              </span>
              <span className="mt-1 block text-sm font-bold text-foreground">
                {estadoIngesta.total > 0
                  ? `${estadoIngesta.conFotos} de ${estadoIngesta.total} con 3 fotos`
                  : "Pendiente de subir"}
              </span>
            </div>

            <div
              className={`rounded-lg border p-3 ${
                estadoIngesta.total > 0 && estadoIngesta.conRes === estadoIngesta.total
                  ? "border-success bg-success-bg"
                  : "border-border bg-background"
              }`}
            >
              <span
                className={`block text-xs font-bold uppercase ${
                  estadoIngesta.total > 0 && estadoIngesta.conRes === estadoIngesta.total
                    ? "text-success"
                    : "text-text-secondary"
                }`}
              >
                3. Veredictos (resultados.json)
              </span>
              <span className="mt-1 block text-sm font-bold text-foreground">
                {estadoIngesta.total > 0
                  ? `${estadoIngesta.conRes} de ${estadoIngesta.total} con decisión`
                  : "Pendiente de subir"}
              </span>
            </div>

            <div
              className={`rounded-lg border p-3 ${
                estadoIngesta.total > 0 && estadoIngesta.conExt > 0
                  ? "border-success bg-success-bg"
                  : "border-border bg-background"
              }`}
            >
              <span
                className={`block text-xs font-bold uppercase ${
                  estadoIngesta.total > 0 && estadoIngesta.conExt > 0 ? "text-success" : "text-text-secondary"
                }`}
              >
                4. Lecturas (extracciones.json)
              </span>
              <span className="mt-1 block text-sm font-bold text-foreground">
                {estadoIngesta.total > 0
                  ? `${estadoIngesta.conExt} con lectura${tokensPromedio ? ` · ${tokensPromedio} tok` : ""}`
                  : "Pendiente de subir"}
              </span>
            </div>
          </div>

          {/* Zona Única Inteligente (Drag & Drop + ZIP / Carpeta / Archivos) */}
          <div
            onDragEnter={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={(e) => {
              e.preventDefault();
              setDragOver(false);
            }}
            onDrop={(e) => {
              e.preventDefault();
              setDragOver(false);
              if (e.dataTransfer?.files?.length) {
                void procesarArchivosUnificados(e.dataTransfer.files);
              }
            }}
            className={`flex flex-col items-center justify-center gap-3 rounded-lg border-2 border-dashed p-6 text-center transition-colors ${
              dragOver ? "border-primary bg-danger-bg" : "border-input bg-surface-2"
            }`}
          >
            <Upload className="size-6 text-primary" />
            <p className="text-base font-bold text-foreground">
              Carga rápida unificada (Arrastra y suelta aquí todo tu lote)
            </p>
            <p className="max-w-2xl text-sm text-text-secondary">
              Suelta de una sola vez o en pasos tus archivos <span className="font-mono">.zip</span> (como{" "}
              <span className="font-mono">Validat3B_evaluacion_imagenes.zip</span> y{" "}
              <span className="font-mono">Validat3B_evaluacion_metadatos.zip</span>), carpetas,{" "}
              <span className="font-mono">capturas.csv</span>, <span className="font-mono">resultados.json</span>,{" "}
              <span className="font-mono">extracciones.json</span> o fotos sueltas. Todo se combina sin borrar lo que ya
              subiste.
            </p>
            <div className="mt-1 flex flex-wrap justify-center gap-3">
              <label className="inline-flex min-h-11 cursor-pointer items-center gap-2 rounded-md bg-primary px-4 text-sm font-semibold text-primary-foreground hover:bg-primary-hover">
                Seleccionar archivos (.zip, .csv, .json, fotos)
                <input
                  type="file"
                  multiple
                  accept=".zip,.csv,.json,image/*"
                  onChange={(e) => void procesarArchivosUnificados(e.target.files)}
                  className="hidden"
                />
              </label>
              <label className="inline-flex min-h-11 cursor-pointer items-center gap-2 rounded-md border border-input bg-background px-4 text-sm font-semibold text-foreground hover:bg-surface-2">
                <FolderUp className="size-4" />
                Seleccionar carpeta completa
                <input
                  type="file"
                  // @ts-expect-error webkitdirectory soportado en navegadores modernos
                  webkitdirectory=""
                  multiple
                  onChange={(e) => void procesarArchivosUnificados(e.target.files)}
                  className="hidden"
                />
              </label>
            </div>
          </div>

          <details className="rounded-lg border border-border bg-background p-4">
            <summary className="cursor-pointer text-sm font-bold text-text-secondary">
              Opciones avanzadas: subir archivos por separado o probar 3 fotos sueltas en vivo
            </summary>
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <Card className="border border-dashed border-border bg-surface-2 shadow-none">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base font-bold">
                    <FolderUp className="size-5 text-primary" />
                    1. Subir carpeta completa del Set Ciego
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3 text-sm text-text-secondary">
                  <p>
                    Detecta automáticamente <span className="font-mono">capturas.csv</span>,{" "}
                    <span className="font-mono">resultados.json</span>,{" "}
                    <span className="font-mono">extracciones.json</span> y fotos locales.
                  </p>
                  <input
                    type="file"
                    // @ts-expect-error webkitdirectory es soportado por navegadores Chromium/Edge/Firefox
                    webkitdirectory=""
                    multiple
                    onChange={(e) => void procesarArchivosUnificados(e.target.files)}
                    className="block min-h-11 w-full max-w-full cursor-pointer overflow-hidden rounded-md border border-input bg-background p-2.5 text-sm"
                  />
                </CardContent>
              </Card>

              <Card className="border border-border bg-surface-2 shadow-none">
                <CardHeader>
                  <CardTitle className="text-base font-bold">2. Subir CSV, JSON o ZIP individual</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4 text-sm text-text-secondary">
                  <div className="min-w-0">
                    <label className="mb-1 block font-medium text-foreground">
                      Archivo CSV o ZIP (capturas.csv / tokens.csv)
                    </label>
                    <input
                      type="file"
                      accept=".csv,.zip"
                      multiple
                      onChange={(e) => void procesarArchivosUnificados(e.target.files)}
                      className="block min-h-11 w-full max-w-full cursor-pointer overflow-hidden rounded-md border border-input bg-background p-2 text-sm"
                    />
                  </div>
                  <div className="min-w-0">
                    <label className="mb-1 block font-medium text-foreground">
                      Archivo JSON (resultados.json / extracciones.json)
                    </label>
                    <input
                      type="file"
                      accept=".json,.zip"
                      multiple
                      onChange={(e) => void procesarArchivosUnificados(e.target.files)}
                      className="block min-h-11 w-full max-w-full cursor-pointer overflow-hidden rounded-md border border-input bg-background p-2 text-sm"
                    />
                  </div>
                </CardContent>
              </Card>

              <Card className="border border-border shadow-none md:col-span-2">
                <CardHeader>
                  <CardTitle className="text-base font-bold">3. Probar 3 fotos sueltas en vivo</CardTitle>
                </CardHeader>
                <CardContent className="grid gap-4 md:grid-cols-4 md:items-end">
                  <div className="min-w-0">
                    <label className="mb-1 block text-sm font-medium">Foto de fachada</label>
                    <input
                      type="file"
                      accept="image/*"
                      onChange={(e) => setSimFiles((s) => ({ ...s, facade: e.target.files?.[0] }))}
                      className="block min-h-11 w-full max-w-full overflow-hidden rounded-md border border-input bg-input-bg p-2 text-sm"
                    />
                  </div>
                  <div className="min-w-0">
                    <label className="mb-1 block text-sm font-medium">Foto del producto</label>
                    <input
                      type="file"
                      accept="image/*"
                      onChange={(e) => setSimFiles((s) => ({ ...s, product: e.target.files?.[0] }))}
                      className="block min-h-11 w-full max-w-full overflow-hidden rounded-md border border-input bg-input-bg p-2 text-sm"
                    />
                  </div>
                  <div className="min-w-0">
                    <label className="mb-1 block text-sm font-medium">Foto de etiqueta</label>
                    <input
                      type="file"
                      accept="image/*"
                      onChange={(e) => setSimFiles((s) => ({ ...s, shelf: e.target.files?.[0] }))}
                      className="block min-h-11 w-full max-w-full overflow-hidden rounded-md border border-input bg-input-bg p-2 text-sm"
                    />
                  </div>
                  <Button type="button" onClick={agregarCapturaSimulada} className="w-full">
                    Cargar captura al explorador
                  </Button>
                </CardContent>
              </Card>
            </div>
          </details>
        </div>
      )}

      {/* Modal Foto */}
      <Dialog open={Boolean(fotoModal)} onOpenChange={(o) => !o && setFotoModal(null)}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>{fotoModal?.label}</DialogTitle>
          </DialogHeader>
          {fotoModal?.src && (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={fotoModal.src} alt={fotoModal.label} className="max-h-[75vh] w-full rounded-md object-contain" />
          )}
        </DialogContent>
      </Dialog>

      {/* Modal JSON Oficial */}
      <Dialog open={Boolean(jsonModal)} onOpenChange={(o) => !o && setJsonModal(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>JSON Oficial · {jsonModal?.capture_id}</DialogTitle>
          </DialogHeader>
          {jsonModal && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <ChipDecision decision={jsonModal.decision} />
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    navigator.clipboard.writeText(JSON.stringify(jsonModal, null, 2));
                    setCopiado(true);
                    setTimeout(() => setCopiado(false), 1200);
                  }}
                >
                  <Copy className="size-4" />
                  {copiado ? "Copiado" : "Copiar JSON"}
                </Button>
              </div>
              <pre className="max-h-96 overflow-auto rounded-md border border-border bg-surface-2 p-3 font-mono text-xs text-foreground">
                {JSON.stringify(jsonModal, null, 2)}
              </pre>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
