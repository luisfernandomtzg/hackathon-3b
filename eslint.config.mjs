import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

// Fronteras entre carriles (docs/arquitectura-provisional.md §6). Probadas en rojo en I0.
const prohibidoEnUI = [
  { group: ["@supabase/*"], message: "UI no habla con Supabase: usa acciones de lib/datos." },
  { group: ["@/lib/ia", "@/lib/ia/*"], message: "UI no llama modelos directo: pasa por el servidor." },
];
const prohibidoEnDominio = [
  { group: ["next", "next/*"], message: "lib/dominio es lógica pura: sin Next." },
  { group: ["@supabase/*"], message: "lib/dominio es lógica pura: sin base." },
  { group: ["@/app", "@/app/*", "@/components/*"], message: "lib/dominio no depende de la interfaz." },
];

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  {
    files: ["app/**/*.{ts,tsx}", "components/**/*.{ts,tsx}"],
    rules: { "no-restricted-imports": ["error", { patterns: prohibidoEnUI }] },
  },
  {
    files: ["lib/dominio/**/*.ts"],
    rules: { "no-restricted-imports": ["error", { patterns: prohibidoEnDominio }] },
  },
  globalIgnores([".next/**", "out/**", "build/**", "next-env.d.ts", "node_modules/**"]),
]);

export default eslintConfig;
