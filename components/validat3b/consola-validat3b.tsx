"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  CheckCircle2,
  Copy,
  Download,
  FileJson,
  FolderUp,
  ImagePlus,
  RotateCw,
  Search,
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

export interface RegistroConsola {
  capture_id: string;
  store: string;
  brand: string;
  product_name: string;
  qty: string;
  unit: string;
  price_ref: string;
  esperada: Decision | "";
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

function ChipDecision({ decision }: { decision: Decision | "" }) {
  if (!decision) {
    return (
      <span className="inline-flex h-6 items-center gap-1.5 rounded-full bg-muted px-2.5 text-xs font-medium text-text-tertiary">
        <span aria-hidden className="size-2 rounded-full bg-current" />
        Sin resultado
      </span>
    );
  }
  const styles: Record<Decision, string> = {
    aprobada: "bg-success-bg text-success",
    rechazada: "bg-danger-bg text-danger",
    revision_manual: "bg-warning-bg text-warning",
  };
  return (
    <span className={`inline-flex h-6 items-center gap-1.5 rounded-full px-2.5 text-xs font-medium ${styles[decision]}`}>
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
  const [viewMode, setViewMode] = useState<ViewMode>("table");
  const [cargando, setCargando] = useState(false);
  const [alerta, setAlerta] = useState<{ tipo: "ok" | "err"; msg: string } | null>(null);

  // Filtros globales
  const [query, setQuery] = useState("");
  const [filtroTienda, setFiltroTienda] = useState("");
  const [filtroMotor, setFiltroMotor] = useState("");
  const [soloErrores, setSoloErrores] = useState(false);

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
    return registros.filter((r) => {
      if (filtroTienda && r.store !== filtroTienda) return false;
      if (filtroMotor && r.motor !== filtroMotor) return false;
      if (soloErrores && (!r.esperada || !r.motor || r.esperada === r.motor)) return false;
      if (q) {
        const hay = `${r.capture_id} ${r.store} ${r.brand} ${r.product_name} ${r.reason_code}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });
  }, [registros, query, filtroTienda, filtroMotor, soloErrores]);

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

  const colaManual = useMemo(
    () => filtrados.filter((r) => r.motor === "revision_manual" || !r.motor),
    [filtrados]
  );

  const casoActual = colaManual.length ? colaManual[hitlIdx % colaManual.length] : null;

  const marcarHitl = useCallback(
    (cid: string, decision: "aprobada" | "rechazada") => {
      setDictamenAnalista((prev) => ({ ...prev, [cid]: decision }));
      setHitlIdx((i) => i + 1);
    },
    []
  );

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

  function aplicarCapturas(rows: Record<string, string>[], imgMap: Record<string, string> = {}) {
    const nuevos: RegistroConsola[] = rows.map((r) => {
      const fName = (r.facade_file || "").split("/").pop() || "";
      const pName = (r.product_file || "").split("/").pop() || "";
      const sName = (r.shelf_file || "").split("/").pop() || "";
      const esperada = (r.decision_esperada || "") as Decision | "";
      return {
        capture_id: r.capture_id || "",
        store: r.capture_store_name || "",
        brand: r.capture_brand || "",
        product_name: r.product_name || "",
        qty: r.unit_quantity_product || "",
        unit: r.unit_product || "",
        price_ref: r.capture_price || "",
        esperada,
        motor: "",
        confidence: null,
        reason_code: "",
        explicacion: "",
        precio_detectado: null,
        codigo_barras_detectado: r.capture_barcode || "",
        leido_marca: "",
        leido_desc: "",
        leido_cant: "",
        leido_unid: "",
        validaciones: { tienda_fachada: "ok", producto: "ok", codigo_barras: "ok", evidencia_precio: "ok" },
        img_facade: imgMap[fName] || "",
        img_product: imgMap[pName] || "",
        img_shelf: imgMap[sName] || "",
        costo: null,
      };
    });
    setRegistros(nuevos);
    setEsDemoSintetico(false);
    setHitlIdx(0);
  }

  function aplicarResultados(arr: ResultadoOficial[]) {
    const mapa = new Map(arr.map((x) => [x.capture_id, x]));
    setRegistros((prev) => {
      const actualizado = prev.map((reg) => {
        const res = mapa.get(reg.capture_id);
        if (!res) return reg;
        return {
          ...reg,
          motor: res.decision,
          confidence: res.confidence_score,
          reason_code: res.reason_code || "",
          explicacion: res.explicacion || "",
          precio_detectado: res.precio_detectado,
          codigo_barras_detectado: res.codigo_barras_detectado || reg.codigo_barras_detectado,
          validaciones: res.validaciones || reg.validaciones,
          costo: calcularCostoPesimista(res.decision, reg.esperada),
        };
      });
      if (prev.length === DEMO_INICIAL.length && !mapa.has(prev[0].capture_id)) {
        return arr.map((res) => ({
          capture_id: res.capture_id,
          store: "Set cargado",
          brand: "—",
          product_name: "Captura desde resultados.json",
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
          img_facade: "",
          img_product: "",
          img_shelf: "",
          costo: null,
        }));
      }
      return actualizado;
    });
    setEsDemoSintetico(false);
  }

  async function manejarCarpeta(files: FileList | null) {
    if (!files || !files.length) return;
    setCargando(true);
    setAlerta(null);
    try {
      const imgMap: Record<string, string> = {};
      let capFile: File | null = null;
      let resFile: File | null = null;
      let tokFile: File | null = null;

      Array.from(files).forEach((f) => {
        const low = f.name.toLowerCase();
        if (low === "capturas.csv" || low === "capturas.json") capFile = f;
        else if (low === "resultados.json") resFile = f;
        else if (low === "tokens.csv") tokFile = f;
        else if (/\.(jpg|jpeg|png|webp)$/.test(low)) {
          imgMap[f.name] = URL.createObjectURL(f);
        }
      });

      if (!capFile && !resFile) {
        setAlerta({
          tipo: "err",
          msg: "La carpeta no contiene capturas.csv, capturas.json ni resultados.json.",
        });
        return;
      }

      if (capFile) {
        const txt = await (capFile as File).text();
        const rows = (capFile as File).name.endsWith(".json")
          ? JSON.parse(txt).capturas || JSON.parse(txt)
          : parseCsvTexto(txt);
        aplicarCapturas(rows, imgMap);
      }
      if (resFile) {
        const arr = JSON.parse(await (resFile as File).text());
        aplicarResultados(arr);
      }
      if (tokFile) {
        const tRows = parseCsvTexto(await (tokFile as File).text()).filter(
          (r) => !r.origen || r.origen === "modelo"
        );
        if (tRows.length) {
          const sum = tRows.reduce(
            (acc, r) => acc + Number(r.tokens_entrada || 0) + Number(r.tokens_salida || 0),
            0
          );
          setTokensPromedio(Math.round(sum / tRows.length));
        }
      }
      setAlerta({
        tipo: "ok",
        msg: `Carpeta procesada en el navegador con ${Object.keys(imgMap).length} imágenes enlazadas.`,
      });
    } catch {
      setAlerta({ tipo: "err", msg: "No se pudo leer la carpeta seleccionada. Revisa el formato." });
    } finally {
      setCargando(false);
    }
  }

  async function manejarCsv(file: File | null) {
    if (!file) return;
    setCargando(true);
    setAlerta(null);
    try {
      const rows = parseCsvTexto(await file.text());
      if (!rows.length || !rows[0].capture_id) {
        setAlerta({ tipo: "err", msg: "El archivo CSV debe incluir la columna capture_id." });
        return;
      }
      aplicarCapturas(rows);
      setAlerta({ tipo: "ok", msg: `Archivo CSV cargado con ${rows.length} capturas.` });
    } catch {
      setAlerta({ tipo: "err", msg: "No se pudo interpretar el archivo CSV." });
    } finally {
      setCargando(false);
    }
  }

  async function manejarJson(file: File | null) {
    if (!file) return;
    setCargando(true);
    setAlerta(null);
    try {
      const parsed = JSON.parse(await file.text());
      const arr = Array.isArray(parsed) ? parsed : parsed.capturas || [];
      if (!arr.length) {
        setAlerta({ tipo: "err", msg: "El JSON está vacío o no tiene formato de lista." });
        return;
      }
      if (arr[0].decision) {
        aplicarResultados(arr);
        setAlerta({ tipo: "ok", msg: `Veredictos cargados desde ${file.name} (${arr.length}).` });
      } else {
        aplicarCapturas(arr);
        setAlerta({ tipo: "ok", msg: `Capturas cargadas desde ${file.name} (${arr.length}).` });
      }
    } catch {
      setAlerta({ tipo: "err", msg: "El archivo no es un JSON válido." });
    } finally {
      setCargando(false);
    }
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
      costo: null,
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
            Consola Validat3B
          </h1>
          <p className="text-sm text-text-tertiary">
            {esDemoSintetico
              ? "Vista con datos de ejemplo inventados. Sube tu carpeta de datos o set ciego en la pestaña Cargar set ciego."
              : `Mostrando ${filtrados.length} de ${registros.length} capturas cargadas localmente en este navegador.`}
          </p>
        </div>

        <div className="flex flex-wrap gap-2" role="tablist" aria-label="Módulos de Validat3B">
          {(
            [
              ["resumen", "1. Resumen"],
              ["cola", `2. Cola manual (${colaManual.length})`],
              ["auditoria", "3. Auditoría"],
              ["ingesta", "4. Cargar set ciego"],
            ] as const
          ).map(([id, label]) => (
            <Button
              key={id}
              type="button"
              variant={tab === id ? "secondary" : "outline"}
              className={tab === id ? "border-foreground font-semibold" : undefined}
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

      {/* Filtros globales */}
      <div className="flex flex-wrap items-center gap-3 rounded-lg border border-border bg-surface-2 p-3">
        <div className="relative min-w-60 flex-1">
          <Search className="pointer-events-none absolute top-3.5 left-3 size-4 text-text-muted" />
          <Input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Buscar ID, tienda, marca o motivo..."
            className="pl-9"
            aria-label="Buscar captura"
          />
        </div>
        <select
          value={filtroTienda}
          onChange={(e) => setFiltroTienda(e.target.value)}
          aria-label="Filtrar por tienda"
          className="h-11 rounded-md border border-input bg-background px-3 text-sm text-foreground"
        >
          <option value="">Todas las tiendas</option>
          {tiendas.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
        <select
          value={filtroMotor}
          onChange={(e) => setFiltroMotor(e.target.value)}
          aria-label="Filtrar por decisión"
          className="h-11 rounded-md border border-input bg-background px-3 text-sm text-foreground"
        >
          <option value="">Todas las decisiones</option>
          <option value="aprobada">aprobada</option>
          <option value="rechazada">rechazada</option>
          <option value="revision_manual">revision_manual</option>
        </select>
        <Button
          type="button"
          variant={soloErrores ? "destructive" : "outline"}
          onClick={() => setSoloErrores((s) => !s)}
        >
          Solo discrepancias
        </Button>
        <Button type="button" variant="outline" onClick={exportarCsv}>
          <Download className="size-4" />
          Exportar CSV
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
                <CardTitle className="text-base font-bold">Capturas por tienda</CardTitle>
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
                <CardTitle className="text-base font-bold">Motivos detectados (reason_code)</CardTitle>
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
                Cola de revisión manual: {colaManual.length ? `${(hitlIdx % colaManual.length) + 1} de ${colaManual.length}` : "0"}
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
                Anterior
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => setHitlIdx((i) => i + 1)}
                disabled={!colaManual.length}
              >
                Siguiente (S)
              </Button>
            </div>
          </div>

          {!casoActual ? (
            <div className="rounded-lg border border-border p-8 text-center">
              <p className="text-base font-semibold text-foreground">No hay capturas en revisión manual</p>
              <p className="mt-1 text-sm text-text-tertiary">
                Ajusta los filtros superiores o carga una carpeta de datos para inspeccionar casos.
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
                            <span>Sube la carpeta local de imágenes en la pestaña 4 para ver la foto aquí.</span>
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
                    <ChipDecision decision={casoActual.motor} />
                    <span className="font-mono text-xs text-text-muted">
                      Conf: {casoActual.confidence !== null ? casoActual.confidence.toFixed(2) : "—"}
                    </span>
                  </div>
                  <CardTitle className="pt-2 text-base font-bold">
                    {casoActual.brand} — {casoActual.product_name}
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="rounded-md border border-border bg-surface-2 p-3 text-sm">
                    <p className="font-semibold text-foreground">
                      Motivo: <span className="font-mono">{casoActual.reason_code || "Sin código"}</span>
                    </p>
                    <p className="mt-1 text-text-secondary">
                      {casoActual.explicacion || "Caso escalado para evitar falso positivo (1 pt vs 10 pts)."}
                    </p>
                  </div>

                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Campo</TableHead>
                        <TableHead>Esperado</TableHead>
                        <TableHead>Leído</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      <TableRow>
                        <TableCell>Marca</TableCell>
                        <TableCell>{casoActual.brand}</TableCell>
                        <TableCell>{casoActual.leido_marca || "—"}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Contenido</TableCell>
                        <TableCell>
                          {casoActual.qty} {casoActual.unit}
                        </TableCell>
                        <TableCell>
                          {casoActual.leido_cant ? `${casoActual.leido_cant} ${casoActual.leido_unid}` : "—"}
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Precio</TableCell>
                        <TableCell className="font-mono">${casoActual.price_ref}</TableCell>
                        <TableCell className="font-mono">
                          {casoActual.precio_detectado !== null ? `$${casoActual.precio_detectado}` : "—"}
                        </TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>

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
                      JSON
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      )}

      {/* MÓDULO 3: EXPLORADOR DE AUDITORÍA */}
      {!cargando && tab === "auditoria" && (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="text-sm font-medium text-text-secondary">
              {filtrados.length} registros en auditoría
            </p>
            <div className="flex gap-2">
              <Button
                type="button"
                variant={viewMode === "table" ? "secondary" : "outline"}
                className={viewMode === "table" ? "border-foreground font-semibold" : undefined}
                onClick={() => setViewMode("table")}
              >
                Tabla compacta (52 px)
              </Button>
              <Button
                type="button"
                variant={viewMode === "cards" ? "secondary" : "outline"}
                className={viewMode === "cards" ? "border-foreground font-semibold" : undefined}
                onClick={() => setViewMode("cards")}
              >
                Tarjetas
              </Button>
            </div>
          </div>

          {!filtrados.length ? (
            <div className="rounded-lg border border-border p-8 text-center">
              <p className="font-semibold">No hay registros que coincidan con la búsqueda</p>
              <Button
                type="button"
                variant="outline"
                className="mt-3"
                onClick={() => {
                  setQuery("");
                  setFiltroTienda("");
                  setFiltroMotor("");
                  setSoloErrores(false);
                }}
              >
                Limpiar filtros
              </Button>
            </div>
          ) : viewMode === "table" ? (
            <div className="overflow-x-auto rounded-lg border border-border">
              <Table>
                <TableHeader>
                  <TableRow className="bg-surface-2">
                    <TableHead>ID</TableHead>
                    <TableHead>Tienda</TableHead>
                    <TableHead>Producto</TableHead>
                    <TableHead>Precio esp. / det.</TableHead>
                    <TableHead>Decisión motor</TableHead>
                    <TableHead>Motivo</TableHead>
                    <TableHead className="text-right">JSON</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filtrados.map((r) => (
                    <TableRow key={r.capture_id} className="h-[52px]">
                      <TableCell className="font-mono font-semibold">{r.capture_id}</TableCell>
                      <TableCell>{r.store}</TableCell>
                      <TableCell className="max-w-xs truncate" title={`${r.brand} — ${r.product_name}`}>
                        {r.brand} — {r.product_name}
                      </TableCell>
                      <TableCell className="font-mono tabular-nums">
                        ${r.price_ref} / {r.precio_detectado !== null ? `$${r.precio_detectado}` : "—"}
                      </TableCell>
                      <TableCell>
                        <ChipDecision decision={r.motor} />
                      </TableCell>
                      <TableCell className="font-mono text-xs text-text-tertiary">
                        {r.reason_code || "—"}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button type="button" variant="outline" onClick={() => abrirJson(r)}>
                          Ver JSON
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {filtrados.map((r) => (
                <Card key={r.capture_id} className="border border-border shadow-none">
                  <CardHeader className="pb-2">
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-mono text-sm font-bold">{r.capture_id}</span>
                      <ChipDecision decision={r.motor} />
                    </div>
                    <CardTitle className="text-sm font-semibold">
                      {r.brand} — {r.product_name}
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3 text-sm">
                    <p className="text-text-tertiary">
                      {r.store} · Ref ${r.price_ref} · Det{" "}
                      {r.precio_detectado !== null ? `$${r.precio_detectado}` : "—"}
                    </p>
                    <p className="text-xs text-text-secondary">{r.explicacion || "Sin explicación"}</p>
                    <Button type="button" variant="outline" className="w-full" onClick={() => abrirJson(r)}>
                      <FileJson className="size-4" />
                      Inspeccionar JSON oficial
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* MÓDULO 4: CARGAR SET CIEGO / SIMULADOR EN VIVO */}
      {!cargando && tab === "ingesta" && (
        <div className="grid gap-4 md:grid-cols-2">
          <Card className="border border-dashed border-border bg-surface-2 shadow-none">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base font-bold">
                <FolderUp className="size-5 text-primary" />
                1. Cargar carpeta del Set Ciego o datos locales
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm text-text-secondary">
              <p>
                Selecciona la carpeta descomprimida del set ciego (detecta{" "}
                <span className="font-mono">capturas.csv</span>, <span className="font-mono">capturas.json</span>,{" "}
                <span className="font-mono">resultados.json</span> y las fotos locales sin subir nada a internet).
              </p>
              <input
                type="file"
                // @ts-expect-error webkitdirectory es soportado por navegadores Chromium/Edge/Firefox
                webkitdirectory=""
                multiple
                onChange={(e) => manejarCarpeta(e.target.files)}
                className="block min-h-11 w-full cursor-pointer rounded-md border border-input bg-background p-2.5 text-sm"
              />
            </CardContent>
          </Card>

          <Card className="border border-border bg-surface-2 shadow-none">
            <CardHeader>
              <CardTitle className="text-base font-bold">2. Cargar archivo CSV o JSON suelto</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-sm text-text-secondary">
              <div>
                <label className="mb-1 block font-medium text-foreground">Archivo CSV (capturas.csv)</label>
                <input
                  type="file"
                  accept=".csv"
                  onChange={(e) => manejarCsv(e.target.files?.[0] || null)}
                  className="block w-full cursor-pointer rounded-md border border-input bg-background p-2 text-sm"
                />
              </div>
              <div>
                <label className="mb-1 block font-medium text-foreground">
                  Archivo JSON (resultados.json o capturas.json)
                </label>
                <input
                  type="file"
                  accept=".json"
                  onChange={(e) => manejarJson(e.target.files?.[0] || null)}
                  className="block w-full cursor-pointer rounded-md border border-input bg-background p-2 text-sm"
                />
              </div>
            </CardContent>
          </Card>

          <Card className="border border-border shadow-none md:col-span-2">
            <CardHeader>
              <CardTitle className="text-base font-bold">3. Simulador rápido de 3 fotos en vivo</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-4 md:grid-cols-4 md:items-end">
              <div>
                <label className="mb-1 block text-sm font-medium">Foto de fachada</label>
                <input
                  type="file"
                  accept="image/*"
                  onChange={(e) => setSimFiles((s) => ({ ...s, facade: e.target.files?.[0] }))}
                  className="block w-full rounded-md border border-input bg-input-bg p-2 text-sm"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium">Foto del producto</label>
                <input
                  type="file"
                  accept="image/*"
                  onChange={(e) => setSimFiles((s) => ({ ...s, product: e.target.files?.[0] }))}
                  className="block w-full rounded-md border border-input bg-input-bg p-2 text-sm"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium">Foto de etiqueta</label>
                <input
                  type="file"
                  accept="image/*"
                  onChange={(e) => setSimFiles((s) => ({ ...s, shelf: e.target.files?.[0] }))}
                  className="block w-full rounded-md border border-input bg-input-bg p-2 text-sm"
                />
              </div>
              <Button type="button" onClick={agregarCapturaSimulada} className="w-full">
                Abrir en Cola de Revisión
              </Button>
            </CardContent>
          </Card>
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
