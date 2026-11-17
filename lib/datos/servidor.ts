import "server-only";
import { createClient, type SupabaseClient } from "@supabase/supabase-js";

let cliente: SupabaseClient | null = null;

/** Cliente de Supabase con llave secreta. Solo servidor; jamás se importa desde app/ o components/ cliente. */
export function clienteServidor(): SupabaseClient | null {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const llave = process.env.SUPABASE_SECRET_KEY;
  if (!url || !llave) return null;
  cliente ??= createClient(url, llave, { auth: { persistSession: false } });
  return cliente;
}

export type EstadoBase = { ok: true; ms: number } | { ok: false; motivo: string };

/** Consulta trivial para /salud. No filtra secretos en el motivo. */
export async function revisarBase(): Promise<EstadoBase> {
  const db = clienteServidor();
  if (!db) return { ok: false, motivo: "faltan NEXT_PUBLIC_SUPABASE_URL o SUPABASE_SECRET_KEY" };
  const t0 = Date.now();
  // Una tabla que no existe responde con error de PostgREST: eso ya prueba que la base contesta.
  const { error } = await db.from("_salud").select("*", { head: true, count: "exact" });
  const ms = Date.now() - t0;
  if (!error) return { ok: true, ms };
  if (error.code === "PGRST205" || error.code === "42P01") return { ok: true, ms };
  return { ok: false, motivo: `${error.code ?? "sin código"}: ${error.message}` };
}
