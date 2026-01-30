import { defineConfig } from "vite";
import { resolve } from "path";
import { viteStaticCopy } from "vite-plugin-static-copy";

const OUT_DIR = resolve(
  __dirname,
  "src/sphinx_icore_open/theme/sphinx_icore_open/static",
);

export default defineConfig({
  build: {
    outDir: OUT_DIR,
    emptyOutDir: true,
    cssCodeSplit: false,

    rollupOptions: {
      input: {
        theme: resolve(__dirname, "static/js/main.js"),
        styles: resolve(__dirname, "static/scss/index.scss"),
      },

      output: {
        entryFileNames: "js/[name].js",

        assetFileNames: (assetInfo) => {
          const name = assetInfo.name ?? "";

          // Force single known CSS output
          if (name.endsWith(".css")) {
            return "css/theme.css";
          }

          // Fonts
          if (/\.(woff2?|ttf|eot|otf)$/.test(name)) {
            return "fonts/[name][extname]";
          }

          // Images
          if (/\.(png|jpe?g|svg|gif|webp|ico)$/.test(name)) {
            return "img/[name][extname]";
          }

          // Everything else (hash-safe)
          return "assets/[name].[hash][extname]";
        },
      },
    },
  },

  plugins: [
    viteStaticCopy({
      targets: [
        {
          src: "node_modules/@minvws/manon-themes/dist/icore-open/fonts/*",
          dest: "fonts",
        },
        {
          src: "node_modules/@minvws/manon-themes/dist/icore-open/img/*",
          dest: "img",
        },
      ],
    }),
  ],

  css: {
    preprocessorOptions: {
      scss: {
        loadPaths: ["node_modules"],
      },
    },
  },
});
