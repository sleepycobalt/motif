// Bundle src/board.ts into one script for Figma's MCP `use_figma`, with a layout fixture and a fixed
// origin baked in, so the renderer that ships in the plugin is the one drawn and read back on a real board.
//   node test/board_script.mjs test/fixtures/layout-synthesis.json 0 0 > /tmp/board-script.js
import { build } from "esbuild";
import { readFileSync } from "node:fs";

const [fixture, ox = "0", oy = "0"] = process.argv.slice(2);
const r = await build({ entryPoints: ["src/board.ts"], bundle: true, format: "iife", globalName: "MotifBoard", minify: true, write: false, logLevel: "silent" });
const layout = readFileSync(fixture, "utf8");
process.stdout.write(`${r.outputFiles[0].text}
const layout = ${layout};
const res = await MotifBoard.renderBoard(layout, { origin: [${Number(ox)}, ${Number(oy)}], editor: figma.editorType });
return { counts: res.counts, bounds: res.bounds, editor: res.editor, cardId: res.cardId, sectionIds: res.sectionIds, nStickyIds: res.stickyIds.length, connectorIds: res.connectorIds };
`);
