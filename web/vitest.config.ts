import viteConfig from "./vite.config"

export default {
  ...viteConfig,
  test: {
    environment: "jsdom",
    setupFiles: "./src/test/setup.ts",
  },
}
