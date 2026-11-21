import type { Metadata } from "next";
import type { ReactNode } from "react";
import { Shell } from "@/components/shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";

export const metadata: Metadata = { title: "Tema" };

type Tono = "success" | "warning" | "danger" | "info";

const TONOS: Record<Tono, string> = {
  success: "bg-success-bg text-success",
  warning: "bg-warning-bg text-warning",
  danger: "bg-danger-bg text-danger",
  info: "bg-info-bg text-info",
};

function Estatus({ tono, children }: { tono: Tono; children: ReactNode }) {
  return (
    <span
      className={`inline-flex h-6 items-center gap-1.5 rounded-full px-2.5 text-xs font-medium ${TONOS[tono]}`}
    >
      <span aria-hidden className="size-2 rounded-full bg-current" />
      {children}
    </span>
  );
}

const AVISOS: Record<Tono, string> = {
  success: "border-success bg-success-bg",
  warning: "border-warning bg-warning-bg",
  danger: "border-danger bg-danger-bg",
  info: "border-info bg-info-bg",
};
const AVISOS_TITULO: Record<Tono, string> = {
  success: "text-success",
  warning: "text-warning",
  danger: "text-danger",
  info: "text-info",
};

function Aviso({ tono, titulo, children }: { tono: Tono; titulo: string; children: ReactNode }) {
  return (
    <div
      role={tono === "danger" ? "alert" : undefined}
      className={`rounded-lg border p-4 ${AVISOS[tono]}`}
    >
      <p className={`text-base font-semibold ${AVISOS_TITULO[tono]}`}>{titulo}</p>
      <p className="mt-1 text-sm text-text-secondary">{children}</p>
    </div>
  );
}

function Fila({
  nombre,
  sku,
  cantidad,
  tono,
  estatus,
}: {
  nombre: string;
  sku: string;
  cantidad: string;
  tono: Tono;
  estatus: string;
}) {
  return (
    <li className="flex h-13 items-center gap-3 border-b border-border px-4 last:border-b-0">
      <div className="min-w-0 flex-1">
        <p className="truncate text-base leading-6 font-semibold text-foreground" title={nombre}>
          {nombre}
        </p>
        <p className="font-mono text-[13px] leading-5 text-text-tertiary">{sku}</p>
      </div>
      <span className="font-semibold tabular-nums text-foreground">{cantidad}</span>
      <Estatus tono={tono}>{estatus}</Estatus>
    </li>
  );
}

function Seccion({ titulo, children }: { titulo: string; children: ReactNode }) {
  return (
    <section className="space-y-4">
      <h2 className="font-heading text-2xl font-extrabold">{titulo}</h2>
      {children}
    </section>
  );
}

export default function Tema() {
  return (
    <Shell>
      <div className="space-y-8">
        <div className="space-y-2">
          <h1 className="font-heading text-3xl font-extrabold">Tema Tarima</h1>
          <p className="text-base text-text-secondary">
            Los componentes de DESIGN.md con sus estados. Datos de ejemplo inventados.
          </p>
        </div>

        <Seccion titulo="Botón">
          <div className="flex flex-wrap gap-3">
            <Button>Confirmar pedido</Button>
            <Button variant="secondary">Guardar borrador</Button>
            <Button variant="outline">Ver detalle</Button>
            <Button variant="ghost">Cancelar</Button>
            <Button variant="destructive">Eliminar pedido</Button>
            <Button variant="link">Ver historial</Button>
          </div>
          <div className="flex flex-wrap gap-3">
            <Button disabled>Confirmar pedido</Button>
            <Button variant="secondary" disabled>
              Guardar borrador
            </Button>
            <Button variant="outline" disabled>
              Ver detalle
            </Button>
            <Button variant="ghost" disabled>
              Cancelar
            </Button>
            <Button variant="destructive" disabled>
              Eliminar pedido
            </Button>
            <Button variant="link" disabled>
              Ver historial
            </Button>
          </div>
          <p className="text-sm text-text-tertiary">
            Arriba, en reposo; abajo, deshabilitados. Hover, foco y presionado se prueban con el
            dedo o con el teclado (Tab).
          </p>
        </Seccion>

        <Seccion titulo="Campo">
          <div className="grid gap-6 md:grid-cols-3">
            <div className="space-y-1.5">
              <label htmlFor="c-ok" className="text-sm font-medium text-text-secondary">
                Número de tienda
              </label>
              <Input id="c-ok" placeholder="Ej. 1042" inputMode="numeric" />
            </div>
            <div className="space-y-1.5">
              <label htmlFor="c-err" className="text-sm font-medium text-text-secondary">
                Cantidad a pedir
              </label>
              <Input
                id="c-err"
                defaultValue="-3"
                aria-invalid
                aria-describedby="c-err-msg"
                inputMode="numeric"
              />
              <p id="c-err-msg" className="text-sm text-danger">
                La cantidad no puede ser negativa. Escribe 0 o más.
              </p>
            </div>
            <div className="space-y-1.5">
              <label htmlFor="c-dis" className="text-sm font-medium text-text-secondary">
                CEDI asignado
              </label>
              <Input id="c-dis" defaultValue="CEDI Toluca" disabled />
            </div>
          </div>
        </Seccion>

        <Seccion titulo="Estatus">
          <div className="flex flex-wrap gap-3">
            <Estatus tono="success">Surtido</Estatus>
            <Estatus tono="warning">Por surtir</Estatus>
            <Estatus tono="danger">Agotado</Estatus>
            <Estatus tono="info">En camino</Estatus>
          </div>
        </Seccion>

        <Seccion titulo="Cifra">
          <div>
            <p className="text-sm text-text-tertiary">Productos por completar</p>
            <p className="font-heading text-[35px] leading-10 font-extrabold tabular-nums text-foreground">
              <span className="underline decoration-primary decoration-4 underline-offset-4">14</span>
            </p>
            <p className="text-sm text-text-tertiary">Tienda 1042</p>
          </div>
        </Seccion>

        <Seccion titulo="Fila">
          <ul className="overflow-hidden rounded-xl border border-border bg-surface">
            <Fila nombre="Frijol negro 900 g" sku="SKU-100234" cantidad="24 pzas" tono="success" estatus="Surtido" />
            <Fila nombre="Arroz blanco 1 kg" sku="SKU-100871" cantidad="6 pzas" tono="warning" estatus="Por surtir" />
            <Fila nombre="Aceite vegetal comestible 946 ml presentación familiar" sku="SKU-101552" cantidad="0 pzas" tono="danger" estatus="Agotado" />
            <Fila nombre="Atún en agua 140 g" sku="SKU-102019" cantidad="48 pzas" tono="info" estatus="En camino" />
          </ul>
        </Seccion>

        <Seccion titulo="Aviso">
          <div className="grid gap-3 md:grid-cols-2">
            <Aviso tono="success" titulo="Pedido confirmado">
              Tu pedido de la tienda 1042 salió al CEDI.
            </Aviso>
            <Aviso tono="warning" titulo="Faltan 14 productos">
              Completa el surtido antes de las 18:00.
            </Aviso>
            <Aviso tono="info" titulo="Nuevo corte de inventario">
              El conteo del jueves ya está disponible.
            </Aviso>
            <Aviso tono="danger" titulo="No se pudo enviar el pedido">
              La tienda no tiene conexión; quedó guardado en este teléfono.
            </Aviso>
          </div>
        </Seccion>

        <Seccion titulo="Banda">
          <div className="rounded-lg bg-primary p-5 text-primary-foreground">
            <p className="font-heading text-2xl font-extrabold">3 tiendas sin surtido hoy</p>
          </div>
        </Seccion>

        <Seccion titulo="Vacío, cargando y error">
          <div className="grid gap-6 md:grid-cols-3">
            <div className="space-y-3 rounded-lg border border-border p-4">
              <p className="text-sm font-semibold text-text-secondary">Vacío</p>
              <p className="text-base text-foreground">Aquí aparecerán los pedidos de tu tienda.</p>
              <Button variant="outline">Crear pedido</Button>
            </div>
            <div className="space-y-3 rounded-lg border border-border p-4" aria-busy="true">
              <p className="text-sm font-semibold text-text-secondary">Cargando</p>
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-1/2" />
            </div>
            <div className="space-y-3 rounded-lg border border-border p-4">
              <p className="text-sm font-semibold text-text-secondary">Error</p>
              <Aviso tono="danger" titulo="No se pudo cargar el surtido">
                Revisa tu conexión e intenta de nuevo.
              </Aviso>
              <Button variant="outline">Reintentar</Button>
            </div>
          </div>
        </Seccion>
      </div>
    </Shell>
  );
}
