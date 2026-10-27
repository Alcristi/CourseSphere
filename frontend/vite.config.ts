import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const backend = process.env.BACKEND_PROXY_TARGET || "http://127.0.0.1:5000";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: Object.fromEntries(
      ["/users", "/chats", "/courses", "/my", "/hash", "/health", "/ready"].map((path) => [
        path,
        { target: backend, changeOrigin: true },
      ]),
    ),
  },
});
