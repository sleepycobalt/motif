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

// Chassis fonts (docs/specs/plugin-restyle.md §3): subset to Latin, woff2, base64'd into
// dist/ui.html as @font-face data URIs so the plugin never fetches Google Fonts — manifest.json
// allow-lists only motif-hosted.fly.dev, and the published listing's data-security answer
// says network requests go only there.
const FONTS = [
  { family: "Instrument Serif", weight: 400, file: "instrument-serif-400.woff2" },
  { family: "Space Grotesk", weight: 400, file: "space-grotesk-400.woff2" },
  { family: "Space Grotesk", weight: 500, file: "space-grotesk-500.woff2" },
  { family: "IBM Plex Mono", weight: 400, file: "ibm-plex-mono-400.woff2" },
  { family: "IBM Plex Mono", weight: 500, file: "ibm-plex-mono-500.woff2" },
];

function embeddedFontsCss() {
  return FONTS.map(({ family, weight, file }) => {
    const b64 = readFileSync(`fonts/${file}`).toString("base64");
    return `@font-face{font-family:'${family}';font-style:normal;font-weight:${weight};` +
      `font-display:swap;src:url(data:font/woff2;base64,${b64}) format('woff2')}`;
  }).join("\n");
}

function assembleUi(js) {
  const html = readFileSync("src/ui.html", "utf8");
  const css = readFileSync("src/ui.css", "utf8").replace("/*FONTS*/", () => embeddedFontsCss());
  // Function replacers: a string replacement would read "$$" and "$&" in the code as
  // replacement patterns (a `$${x}` template literal lost its dollar sign this way).
  const out = html.replace("/*CSS*/", () => css).replace("/*JS*/", () => js.replaceAll("</script", "<\\/script"));
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
