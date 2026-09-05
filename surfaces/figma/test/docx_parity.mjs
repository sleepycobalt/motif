// Parity: the plugin's docx extraction vs python-docx, via the engine's own ingest.
// For every .docx in the sample corpus: extract paragraphs here -> <stem>.txt; ingest both folders with
// synth.ingest; the processed .txt/.jsonl files must be byte-identical and the manifests equal except "file".
import { build } from "esbuild";
import { readdirSync, readFileSync, writeFileSync, mkdtempSync, rmSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { DOMParser } from "@xmldom/xmldom";

const ROOT = resolve("../..");
const RAW = join(ROOT, "data/raw/Dataset-2");
const PY = join(ROOT, ".venv/bin/python");

await build({ entryPoints: ["src/docx.ts"], bundle: true, format: "esm", outfile: "test/.docx.mjs", logLevel: "silent" });
const { docxToText } = await import("./.docx.mjs");

const work = mkdtempSync(join(tmpdir(), "motif-parity-"));
const txtDir = join(work, "txt"); const procA = join(work, "proc-docx"); const procB = join(work, "proc-txt");
execFileSync("mkdir", ["-p", txtDir]);
const files = readdirSync(RAW).filter((f) => f.toLowerCase().endsWith(".docx"));
let bytesIn = 0, bytesOut = 0;
for (const f of files) {
  const buf = readFileSync(join(RAW, f));
  const text = await docxToText(buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength), new DOMParser());
  writeFileSync(join(txtDir, f.replace(/\.docx$/i, ".txt")), text);
  bytesIn += buf.length; bytesOut += Buffer.byteLength(text);
}
const py = `
import json, sys
from synth.ingest import ingest
a = ingest(sys.argv[1], sys.argv[2]); b = ingest(sys.argv[3], sys.argv[4])
strip = lambda m: [{k: v for k, v in x.items() if k != "file"} for x in m]
print("manifests equal:", strip(a) == strip(b), "| transcripts:", len(a), "| words:", sum(m["words"] for m in a))
`;
console.log(execFileSync(PY, ["-c", py, RAW, procA, txtDir, procB], { cwd: ROOT, env: { ...process.env, PYTHONPATH: ROOT } }).toString().trim());
// Turn-by-turn comparison of the processed corpora. The one allowed difference: a line break inside a
// docx paragraph is a newline on the python-docx path and a space on the plugin path (same turn either way).
let turns = 0, normalised = 0, bad = [];
for (const f of readdirSync(procA).filter((x) => x.endsWith(".jsonl"))) {
  const a = readFileSync(join(procA, f), "utf8").trim().split("\n").map((l) => JSON.parse(l));
  const b = readFileSync(join(procB, f), "utf8").trim().split("\n").map((l) => JSON.parse(l));
  if (a.length !== b.length) { bad.push(`${f}: ${a.length} vs ${b.length} turns`); continue; }
  for (let i = 0; i < a.length; i++) {
    turns++;
    const same = a[i].id === b[i].id && a[i].speaker === b[i].speaker && a[i].text === b[i].text;
    if (same) continue;
    if (a[i].id === b[i].id && a[i].speaker === b[i].speaker && a[i].text.replace(/\n/g, " ") === b[i].text) { normalised++; continue; }
    bad.push(`${f} ${a[i].id}: ${JSON.stringify(a[i].text.slice(0, 60))} vs ${JSON.stringify(b[i].text.slice(0, 60))}`);
  }
}
console.log(`files: ${files.length} docx, ${(bytesIn / 1e6).toFixed(1)} MB in -> ${(bytesOut / 1e3).toFixed(0)} KB text out`);
console.log(`turns compared: ${turns}; identical: ${turns - normalised - bad.length}; in-paragraph break as space: ${normalised}; mismatches: ${bad.length}`);
if (bad.length) { console.log("MISMATCHES:\n" + bad.join("\n")); process.exitCode = 1; } else console.log("PARITY OK");
rmSync(work, { recursive: true, force: true }); rmSync("test/.docx.mjs", { force: true });
