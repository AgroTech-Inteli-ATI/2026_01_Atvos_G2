import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    fs: {
      // Permite importar arquivos fora da pasta views/ (ex: DATA/gold/)
      allow: ['..'],
    },
  },
});
