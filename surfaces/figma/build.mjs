// Build the plugin: src/code.ts -> dist/code.js (main thread), src/ui.ts + ui.css + ui.html -> dist/ui.html
// (one self-contained file: Figma loads the UI from a single HTML string, so script and style are inlined).
import { build, context } from "esbuild";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";

const watch = process.argv.includes("--watch");
mkdirSync("dist", { recursive: true });

const main = {
  entryPoints: ["src/code.ts"],
  bundle: true,
  outfile: "dist/code.js",
  target: "es2020",
  format: "iife",
  logLevel: "info",
};

const uiJs = {
  entryPoints: ["src/ui.ts"],
  bundle: true,
  write: false,
  target: "es2020",
  format: "iife",
  logLevel: "info",
};

function assembleUi(js) {
  const html = readFileSync("src/ui.html", "utf8");
  const css = readFileSync("src/ui.css", "utf8");
  const out = html.replace("/*CSS*/", css).replace("/*JS*/", js.replaceAll("</script", "<\\/script"));
  writeFileSync("dist/ui.html", out);
  console.log(`dist/ui.html  ${(out.length / 1024).toFixed(1)}kb`);
}

if (watch) {
  const c = await context({ ...uiJs, write: true, outfile: "dist/ui.js" });
  await c.watch();
  const m = await context(main);
  await m.watch();
  console.log("watching; assemble dist/ui.html by re-running `node build.mjs` after UI edits");
} else {
  await build(main);
  const r = await build(uiJs);
  assembleUi(r.outputFiles[0].text);
}
