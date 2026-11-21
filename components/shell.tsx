import type { ReactNode } from "react";

// Shell vacío y responsivo (DESIGN.md · Encabezado y Layout).
// Celular: una columna, margen 16. Escritorio: 1,200 px máximo, margen 24.
export function Shell({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-dvh flex-col bg-background text-foreground">
      <header className="h-14 border-b border-border bg-surface-2">
        <div className="mx-auto flex h-full max-w-[1200px] items-center justify-between gap-4 px-4 md:px-6">
          <span className="font-heading text-lg font-extrabold">Prototipo</span>
          <span className="text-sm text-text-tertiary">Prototipo para Tiendas 3B</span>
        </div>
      </header>
      <main className="mx-auto w-full max-w-[1200px] flex-1 px-4 py-6 md:px-6">{children}</main>
    </div>
  );
}
