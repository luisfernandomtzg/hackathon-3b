import type { Metadata } from "next";
import localFont from "next/font/local";
import { GeistSans } from "geist/font/sans";
import { GeistMono } from "geist/font/mono";
import "./globals.css";
import { cn } from "@/lib/utils";

// Fuentes autoalojadas (DESIGN.md · Tipografía): la demo no depende de Google Fonts.
const montserrat = localFont({
  src: "./fonts/Montserrat-Variable.woff2",
  weight: "100 900",
  style: "normal",
  display: "swap",
  variable: "--font-montserrat",
});

export const metadata: Metadata = {
  title: { default: "Hackatón 3B", template: "%s · Hackatón 3B" },
  description: "Prototipo del equipo para el Hackatón de Tiendas 3B",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="es-MX"
      className={cn("h-full", "antialiased", GeistSans.variable, GeistMono.variable, montserrat.variable, "font-sans")}
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
