import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  base: "/studio/ui/",
  build: {
    outDir: "../src/framework_m_studio/static",
    emptyOutDir: true,
  },
  server: {
    proxy: {
      "/studio/api": {
        target: "http://localhost:9999",
        changeOrigin: true,
      },
    },
  },
});
