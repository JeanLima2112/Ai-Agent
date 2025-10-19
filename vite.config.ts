import tailwindcss  from '@tailwindcss/vite';
import path from "path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    VitePWA({
      registerType: "autoUpdate",
      devOptions: {
        enabled: true
      },
      
      includeAssets: [
        "favicon.ico",
        "apple-touch-icon.png",
        "logos/techgo-logo.svg",
      ],
      manifest: {
        name: "TechGo",
        short_name: "TechGo",
        description: "Software de gestão",
        theme_color: "#04070b",
        background_color: "#04070b",
        display: "standalone",
        start_url: "/",
        icons: [
          {
            src: "/logos/techgo-logo-192x192.png",
            sizes: "192x192",
            type: "image/png",
          },
          {
            src: "/logos/techgo-logo-512x512.png",
            sizes: "512x512",
            type: "image/png",
          },
        ],
      },
    }),
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    allowedHosts: true,
  },
});
