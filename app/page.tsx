import type { Metadata } from "next";
import Link from "next/link";
import { Shell } from "@/components/shell";
import { ConsolaValidat3B } from "@/components/validat3b/consola-validat3b";

export const metadata: Metadata = {
  title: "Validat3B · Consola Operativa",
  description: "Consola de auditoría, revisión manual e ingesta del set ciego para Tiendas 3B.",
};

export default function Inicio() {
  return (
    <Shell>
      <div className="space-y-6">
        <ConsolaValidat3B />
        <footer className="flex flex-wrap items-center justify-between gap-4 border-t border-border pt-4 text-xs text-text-muted">
          <span>Sistema Tarima · Prototipo para Tiendas 3B</span>
          <div className="flex gap-4">
            <Link href="/tema" className="text-link underline underline-offset-4">
              Sistema de diseño (/tema)
            </Link>
            <Link href="/salud" className="text-link underline underline-offset-4">
              Salud del despliegue (/salud)
            </Link>
          </div>
        </footer>
      </div>
    </Shell>
  );
}
