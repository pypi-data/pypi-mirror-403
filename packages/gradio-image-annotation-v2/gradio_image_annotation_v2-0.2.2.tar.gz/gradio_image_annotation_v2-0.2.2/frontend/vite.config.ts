import { defineConfig } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";

export default defineConfig({
  plugins: [svelte()],
  build: {
    lib: {
      entry: "shared/index.ts",
      name: "Image",
      fileName: "my-gradio-component"
    },
    rollupOptions: {
      external: [], // 通常は空 or svelteをexternalにする場合も
    }
  }
});
