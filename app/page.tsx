import Link from "next/link";

export default function Inicio() {
  return (
    <main className="mx-auto flex min-h-dvh max-w-md flex-col justify-center gap-4 p-6">
      <p className="text-sm text-neutral-500">Hackatón Tiendas 3B · 21-nov-2026</p>
      <h1 className="text-2xl font-semibold">Proyecto en construcción</h1>
      <Link href="/salud" className="text-sm underline underline-offset-4">
        Ver salud del despliegue
      </Link>
    </main>
  );
}
