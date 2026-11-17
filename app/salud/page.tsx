import { Suspense } from "react";
import { connection } from "next/server";
import { revisarBase } from "@/lib/datos/servidor";

export const metadata = { title: "Salud" };

async function Estado() {
  await connection();
  const sha = process.env.VERCEL_GIT_COMMIT_SHA?.slice(0, 7) ?? "local";
  const rama = process.env.VERCEL_GIT_COMMIT_REF ?? "local";
  const hora = new Date().toLocaleString("es-MX", { timeZone: "America/Mexico_City" });
  const base = await revisarBase();
  return (
    <dl className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-2 font-mono text-sm">
      <dt className="text-neutral-500">commit</dt>
      <dd data-testid="sha">{sha}</dd>
      <dt className="text-neutral-500">rama</dt>
      <dd>{rama}</dd>
      <dt className="text-neutral-500">hora servidor</dt>
      <dd>{hora}</dd>
      <dt className="text-neutral-500">base</dt>
      <dd className={base.ok ? "text-green-700" : "text-red-700"}>
        {base.ok ? `ok · ${base.ms} ms` : base.motivo}
      </dd>
    </dl>
  );
}

export default function Salud() {
  return (
    <main className="mx-auto max-w-md p-6">
      <h1 className="mb-4 text-lg font-semibold">Salud del despliegue</h1>
      <Suspense fallback={<p className="text-sm text-neutral-500">Revisando…</p>}>
        <Estado />
      </Suspense>
    </main>
  );
}
