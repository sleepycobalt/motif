/**
 * Motif for Figma: the UI iframe. Owns the network (api.ts) and the docx extraction
 * (docx.ts); asks the main thread (code.ts) for storage, notifications, and the board.
 *
 * Two modes on the setup screen: synthesise transcripts, or check a pasted synthesis
 * against transcripts (the critic alone). Both end on the result screen, where
 * "Build board" hands the run's layout to the main thread to draw.
 *
 * Standalone harness: opened directly in a browser (no Figma parent, or a ?harness
 * frame), the same UI runs with localStorage standing in for figma.clientStorage, so
 * the layout can be checked at any width and the whole flow exercised against the
 * live service; "Build board" is acknowledged, not drawn.
 */

import { docxToText } from "./docx";
import { followJob, getBoard, getJob, submitCritique, submitSynthesis, ServiceError,
  type Insight, type Result, type Upload, type VerdictResult } from "./api";
import type { Layout } from "./board";

type Screen = "key" | "setup" | "running" | "result" | "error";
type Mode = "synthesize" | "critique";

interface Prepared { name: string; text: string; words: number; paragraphs: number; error?: string }
interface Stored { kind: Mode; question: string; nTranscripts: number; result: Result | VerdictResult; layout: Layout | null; jobId: string; when: number }

const $ = <T extends HTMLElement>(id: string): T => document.getElementById(id) as T;
// Inside Figma the UI is an iframe; the width harness (test/harness.html) also frames it, and says so with ?harness.
const inFigma = window.parent !== window && !new URLSearchParams(location.search).has("harness");

// ------------------------------------------------------------- main-thread bridge

type ToUi =
  | { type: "init"; keyMasked: string | null; lastJob: { jobId: string; question?: string; kind?: string } | null; hasLastResult: boolean; editor: string }
  | { type: "key"; key: string | null; keyMasked: string | null }
  | { type: "last-result"; payload: Stored | null }
  | { type: "board-done"; counts: { sections: number; stickies: number; connectors: number }; editor: string }
  | { type: "board-failed"; message: string };

const listeners: ((m: ToUi) => void)[] = [];

function post(msg: Record<string, unknown>): void {
  if (inFigma) { parent.postMessage({ pluginMessage: msg }, "*"); return; }
  // Harness: emulate code.ts with localStorage.
  const key = localStorage.getItem("anthropic_key");
  const masked = (k: string | null) => (k ? `…${k.slice(-4)}` : null);
  const reply = (m: ToUi) => setTimeout(() => listeners.forEach((l) => l(m)), 0);
  switch (msg.type) {
    case "ui-ready": {
      const lj = localStorage.getItem("last_job");
      reply({ type: "init", keyMasked: masked(key), lastJob: lj ? JSON.parse(lj) : null,
        hasLastResult: !!localStorage.getItem("last_result"), editor: "harness" }); break;
    }
    case "get-key": reply({ type: "key", key, keyMasked: masked(key) }); break;
    case "save-key": localStorage.setItem("anthropic_key", String(msg.key)); reply({ type: "key", key: null, keyMasked: masked(String(msg.key)) }); break;
    case "clear-key": localStorage.removeItem("anthropic_key"); reply({ type: "key", key: null, keyMasked: null }); break;
    case "set-last-job": msg.jobId ? localStorage.setItem("last_job", JSON.stringify({ jobId: msg.jobId, question: msg.question, kind: msg.kind })) : localStorage.removeItem("last_job"); break;
    case "set-last-result": msg.payload ? localStorage.setItem("last_result", JSON.stringify(msg.payload)) : localStorage.removeItem("last_result"); break;
    case "get-last-result": { const s = localStorage.getItem("last_result"); reply({ type: "last-result", payload: s ? JSON.parse(s) : null }); break; }
    case "build-board": {
      const lay = msg.layout as Layout;
      const stickies = lay.sections.reduce((n, s) => n + s.stickies.length, 0) + 1;
      console.log("[harness] build-board acknowledged, not drawn:", lay.n_sections, "sections", stickies, "stickies");
      reply({ type: "board-done", counts: { sections: lay.n_sections, stickies, connectors: lay.sections.reduce((n, s) => n + s.connectors.length, 0) }, editor: "harness" });
      break;
    }
    case "notify": console.log("[notify]", msg.message); break;
  }
}

window.onmessage = (e: MessageEvent) => {
  const m = e.data?.pluginMessage as ToUi | undefined;
  if (m) listeners.forEach((l) => l(m));
};

function ask<T extends ToUi["type"]>(request: Record<string, unknown>, replyType: T): Promise<Extract<ToUi, { type: T }>> {
  return new Promise((resolve) => {
    const once = (m: ToUi) => { if (m.type === replyType) { listeners.splice(listeners.indexOf(once), 1); resolve(m as Extract<ToUi, { type: T }>); } };
    listeners.push(once);
    post(request);
  });
}

// ------------------------------------------------------------------------ state

let files: Prepared[] = [];
let mode: Mode = "synthesize";
let keyMasked: string | null = null;
let lastJob: { jobId: string; question?: string; kind?: string } | null = null;
let follow: AbortController | null = null;
let timer: number | null = null;
let current: Stored | null = null;

function show(s: Screen): void {
  for (const id of ["key", "setup", "running", "result", "error"]) $(`screen-${id}`).hidden = id !== s;
  window.scrollTo(0, 0);
}

function fail(message: string): void {
  stopTimer();
  const hint = /authentication_error|API key is invalid|401/.test(message)
    ? "Anthropic rejected the key. Check it at console.anthropic.com, then use “change” to enter it again."
    : /credit balance|insufficient_quota|billing/i.test(message)
      ? "Anthropic reports no credit on this key. Top up at console.anthropic.com and try again."
      : /Could not reach|unreachable|Failed to fetch/i.test(message)
        ? "Motif's engine could not be reached. Check your connection and try again; the engine's status is at motif-hosted.fly.dev/healthz."
        : "";
  $("error-hint").textContent = hint;
  $("error-hint").hidden = !hint;
  $("error-text").textContent = message;
  show("error");
}

// ------------------------------------------------------------------- key screen

const keyInput = $<HTMLInputElement>("key-input");
keyInput.oninput = () => { $<HTMLButtonElement>("key-save").disabled = keyInput.value.trim().length < 20; };
keyInput.onkeydown = (e) => { if (e.key === "Enter" && !$<HTMLButtonElement>("key-save").disabled) $("key-save").click(); };
$("key-save").onclick = () => { post({ type: "save-key", key: keyInput.value }); keyInput.value = ""; };
$("key-change").onclick = () => { post({ type: "clear-key" }); show("key"); keyInput.focus(); };

// ----------------------------------------------------------------- setup screen

const drop = $("drop");
const fileInput = $<HTMLInputElement>("file-input");
const question = $<HTMLTextAreaElement>("question");
const document_ = $<HTMLTextAreaElement>("document");
const runBtn = $<HTMLButtonElement>("run-btn");

function words(s: string): number { return s.split(/\s+/).filter(Boolean).length; }

async function prepare(f: File): Promise<Prepared> {
  const ext = f.name.toLowerCase().replace(/^.*\./, "");
  try {
    let text: string;
    if (ext === "docx") text = await docxToText(await f.arrayBuffer());
    else if (ext === "txt" || ext === "md") text = await f.text();
    else return { name: f.name, text: "", words: 0, paragraphs: 0, error: "not .docx, .txt, or .md" };
    const paras = text.split("\n").map((l) => l.trim()).filter(Boolean);
    if (!paras.length) return { name: f.name, text: "", words: 0, paragraphs: 0, error: "no text found" };
    const labelled = paras.filter((p) => /^[A-Za-z][A-Za-z ]*?\d?\s*:/.test(p)).length;
    const err = labelled === 0 ? "no 'Speaker: text' turns found" : undefined;
    return { name: f.name.replace(/\.docx$/i, ".txt"), text: paras.join("\n") + "\n", words: words(text), paragraphs: paras.length, error: err };
  } catch (e) {
    return { name: f.name, text: "", words: 0, paragraphs: 0, error: (e as Error).message };
  }
}

async function addFiles(list: FileList | File[]): Promise<void> {
  const incoming = Array.from(list).filter((f) => !files.some((p) => p.name === f.name.replace(/\.docx$/i, ".txt")));
  const prepared = await Promise.all(incoming.map(prepare));
  files = files.concat(prepared);
  renderFiles();
}

function renderFiles(): void {
  const ul = $("file-list");
  ul.innerHTML = "";
  for (const [i, f] of files.entries()) {
    const li = document.createElement("li");
    const name = document.createElement("span"); name.className = "name"; name.textContent = f.name; name.title = f.name;
    const meta = document.createElement("span"); meta.className = "meta" + (f.error ? " bad" : "");
    meta.textContent = f.error ? f.error : `${f.paragraphs} paragraphs · ${f.words.toLocaleString()} words`;
    const rm = document.createElement("button"); rm.className = "rm"; rm.textContent = "×"; rm.title = "Remove";
    rm.setAttribute("aria-label", `Remove ${f.name}`);
    rm.onclick = () => { files.splice(i, 1); renderFiles(); };
    li.append(name, meta, rm);
    ul.append(li);
  }
  const good = files.filter((f) => !f.error);
  const total = good.reduce((n, f) => n + f.words, 0);
  $("file-summary").textContent = good.length
    ? `${good.length} transcript${good.length === 1 ? "" : "s"}, ${total.toLocaleString()} words. Sent as text: about ${(good.reduce((n, f) => n + f.text.length, 0) / 1024).toFixed(0)} KB.`
    : "";
  updateRun();
}

function setMode(m: Mode): void {
  mode = m;
  $("mode-synth").classList.toggle("on", m === "synthesize");
  $("mode-critique").classList.toggle("on", m === "critique");
  $("document-card").hidden = m !== "critique";
  $("question-label").textContent = m === "critique" ? "2. Question (optional: the one the synthesis answers)" : "2. Question";
  $("run-fine").textContent = m === "critique"
    ? "One critic pass over the pasted synthesis against the transcripts: a couple of minutes, about $0.35 on your key. Every claim is checked for citations that exist, quotes that match, interviewer turns, dissent, and overreach."
    : "Takes minutes and spends API budget on your key: about $1 for two transcripts, about $5 for fifteen. Condition C: intake → synthesis → critic → revise, up to three rounds.";
  runBtn.textContent = m === "critique" ? "Check the synthesis" : "Synthesise";
  updateRun();
}

function updateRun(): void {
  const haveFiles = files.some((f) => !f.error);
  runBtn.disabled = mode === "critique" ? !(haveFiles && document_.value.trim().length > 20)
    : !(haveFiles && question.value.trim().length > 0);
}

drop.onclick = () => fileInput.click();
drop.onkeydown = (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); fileInput.click(); } };
fileInput.onchange = () => { if (fileInput.files) void addFiles(fileInput.files); fileInput.value = ""; };
for (const ev of ["dragenter", "dragover"]) drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.add("over"); });
for (const ev of ["dragleave", "drop"]) drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.remove("over"); });
drop.addEventListener("drop", (e) => { const dt = (e as DragEvent).dataTransfer; if (dt?.files) void addFiles(dt.files); });
document.body.addEventListener("dragover", (e) => e.preventDefault());
document.body.addEventListener("drop", (e) => e.preventDefault());
question.oninput = updateRun;
document_.oninput = updateRun;
$("mode-synth").onclick = () => setMode("synthesize");
$("mode-critique").onclick = () => setMode("critique");

runBtn.onclick = async () => {
  const good = files.filter((f) => !f.error);
  const uploads: Upload[] = good.map((f) => ({ name: f.name, bytes_b64: btoa(unescape(encodeURIComponent(f.text))) }));
  const q = question.value.trim();
  runBtn.disabled = true;
  const { key } = await ask({ type: "get-key" }, "key");
  if (!key) { runBtn.disabled = false; show("key"); return; }
  let jobId: string;
  try {
    jobId = mode === "critique" ? await submitCritique(key, uploads, document_.value.trim(), q || null)
      : await submitSynthesis(key, uploads, q);
  } catch (e) {
    runBtn.disabled = false;
    fail(e instanceof ServiceError ? `${e.message}${e.status ? ` (HTTP ${e.status})` : ""}` : (e as Error).message);
    return;
  }
  post({ type: "set-last-job", jobId, question: q, kind: mode });
  lastJob = { jobId, question: q, kind: mode };
  await run(jobId, q, Date.now(), good.length);
};

$("resume-btn").onclick = () => { if (lastJob) void run(lastJob.jobId, lastJob.question ?? "", null, 0); };
$("resume-dismiss").onclick = () => { lastJob = null; post({ type: "set-last-job", jobId: null }); $("resume-card").hidden = true; };
$("open-last").onclick = async () => {
  const { payload } = await ask({ type: "get-last-result" }, "last-result");
  if (!payload) { $("last-card").hidden = true; return; }
  renderResult(payload);
};

// --------------------------------------------------------------- running screen

const log = $("log");

function stopTimer(): void { if (timer !== null) { clearInterval(timer); timer = null; } }

function startTimer(startedAt: number): void {
  stopTimer();
  const tick = () => {
    const s = Math.max(0, Math.round((Date.now() - startedAt) / 1000));
    $("elapsed").textContent = `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
  };
  tick();
  timer = window.setInterval(tick, 1000);
}

function appendLog(line: string): void {
  log.textContent += (log.textContent ? "\n" : "") + line;
  log.scrollTop = log.scrollHeight;
}

async function run(jobId: string, q: string, startedAt: number | null, nTranscripts: number): Promise<void> {
  show("running");
  log.textContent = "";
  $("job-id").textContent = jobId;
  follow?.abort();
  follow = new AbortController();
  let job;
  try {
    job = await getJob(jobId);
  } catch (e) {
    post({ type: "set-last-job", jobId: null });
    fail(e instanceof ServiceError && e.status === 404
      ? "That run has expired on the engine (results are kept for an hour after they finish). Start a new run."
      : (e as Error).message);
    return;
  }
  $("running-title").textContent = job.kind === "critique" ? "Checking" : "Synthesising";
  startTimer(startedAt ?? job.created * 1000);
  if (job.state === "done" || job.state === "failed") { await finish(job.state, job.error, q, jobId, nTranscripts); return; }
  let end;
  try {
    end = await followJob(jobId, appendLog, follow.signal);
  } catch (e) {
    if ((e as Error).name === "AbortError") { show("setup"); return; }
    fail((e as Error).message);
    return;
  }
  await finish(end.state, end.error, q, jobId, nTranscripts);
}

async function finish(state: string, error: string | null, q: string, jobId: string, nTranscripts: number): Promise<void> {
  stopTimer();
  post({ type: "set-last-job", jobId: null });
  lastJob = null;
  $("resume-card").hidden = true;
  if (state !== "done") { fail(error || `The run ended as "${state}" with no result.`); return; }
  let job;
  try { job = await getJob(jobId); } catch (e) { fail((e as Error).message); return; }
  const result = job.result;
  if (!result || !result.insights?.length) { fail("The run finished but returned no insights. Silence is never a result."); return; }
  let layout: Layout | null = null;
  try { layout = await getBoard(jobId); } catch (e) { appendLog(`board layout unavailable: ${(e as Error).message}`); }
  const kind: Mode = job.kind === "critique" ? "critique" : "synthesize";
  const stored: Stored = { kind, question: q, nTranscripts, result, layout, jobId, when: Date.now() };
  post({ type: "set-last-result", payload: stored });
  renderResult(stored);
  const msg = isVerdict(result)
    ? `Motif critique: ${result.summary.n_fail} fails, ${result.summary.n_warn} warnings.`
    : `Motif: ${result.n_insights} insights, ${result.contested.length} contested.`;
  post({ type: "notify", message: msg });
}

$("stop-follow").onclick = () => { follow?.abort(); stopTimer(); show("setup"); };

// ----------------------------------------------------------------- result screen

function isVerdict(r: Result | VerdictResult): r is VerdictResult { return "verdict" in r; }

function renderResult(s: Stored): void {
  current = s;
  const r = s.result;
  $("result-question").textContent = s.question || (isVerdict(r) ? "Critique of a pasted synthesis" : "");
  $("result-title").textContent = isVerdict(r) ? "Critique" : "Synthesis";
  const tiles = $("tiles");
  tiles.innerHTML = "";
  const tile = (num: string, lbl: string, warn = false) => {
    const d = document.createElement("div"); d.className = "tile" + (warn ? " warn" : "");
    const n = document.createElement("span"); n.className = "num"; n.textContent = num;
    const l = document.createElement("span"); l.className = "lbl"; l.textContent = lbl;
    d.append(n, l); tiles.append(d);
  };
  const note = $("contested-note");
  if (isVerdict(r)) {
    tile(r.verdict.pass ? "PASS" : "FAIL", "verdict", !r.verdict.pass);
    tile(String(r.insights.length), "claims");
    tile(String(r.summary.n_fail), "fails", r.summary.n_fail > 0);
    tile(String(r.summary.n_warn), "warnings");
    const skipped = r.verdict.skipped_rules ?? [];
    const notes = (r.verdict.notes ?? "").replace(/\s*\[not checked:[^\]]*\]\s*$/i, "").trim();
    note.hidden = false;
    note.textContent = (skipped.length ? `Not checked: ${skipped.join(", ")} (no intake notes for a pasted document). ` : "")
      + (r.source_format === "model" ? "The document was structured into claims by the model; ids and quotes were copied from the text, not invented." : "");
    const nd = $<HTMLDetailsElement>("critic-notes");
    nd.hidden = !notes;
    $("critic-notes-text").textContent = notes;
  } else {
    tile(String(r.n_insights), "insights");
    tile(String(r.contested.length), "contested", r.contested.length > 0);
    tile(String(r.iterations), "rounds");
    tile(r.cost_usd != null ? `$${r.cost_usd.toFixed(2)}` : "–", "API cost");
    tile(r.wall_seconds != null ? (r.wall_seconds / 60).toFixed(1) : "–", "minutes");
    if (r.contested.length) {
      note.hidden = false;
      note.textContent = `The critic still objected to ${r.contested.join(", ")} when the loop stopped (${r.stop_reason.replace("_", " ")}). Read those with the objection in view; silence is never agreement.`;
    } else {
      note.hidden = r.stop_reason === "critic_pass";
      note.textContent = r.stop_reason === "critic_pass" ? "" : `Stopped: ${r.stop_reason.replace("_", " ")}.`;
    }
  }
  if (!isVerdict(r)) $("critic-notes").hidden = true;
  const bb = $<HTMLButtonElement>("build-board");
  bb.disabled = !s.layout;
  bb.textContent = s.layout ? (inFigma ? "Build board" : "Build board (harness: acknowledged only)") : "Board layout unavailable";
  bb.title = s.layout ? "Draws the run on this page: one section per insight, stickies for claim, receipts, counter-evidence, opportunity, and open objections" : "";
  $("board-status").textContent = "";
  $("clip").hidden = true; $("clip-note").hidden = true;
  const ol = $("insights");
  ol.innerHTML = "";
  if (isVerdict(r)) for (const ins of r.insights) ol.append(claimEl(ins, r));
  else for (const ins of r.insights) ol.append(insightEl(ins, s.nTranscripts));
  show("result");
}

function confidenceBadge(ins: Insight, nTranscripts: number): HTMLElement {
  const conf = (ins.confidence || "low").toLowerCase();
  const n = ins.sources?.length ?? 0;
  const b = document.createElement("span");
  b.className = `badge ${conf}`;
  // Say why: high needs 4+ participants and no counter-evidence, so on a small corpus "low" is the ceiling.
  b.textContent = nTranscripts ? `${conf} · ${n} of ${nTranscripts}` : `${conf} · ${n} source${n === 1 ? "" : "s"}`;
  b.title = `${n} participant${n === 1 ? "" : "s"} cited${nTranscripts ? ` of ${nTranscripts} transcripts` : ""}. High needs 4+ participants and no counter-evidence; medium 2-3; low 1.`;
  return b;
}

function insightEl(ins: Insight, nTranscripts: number): HTMLElement {
  const li = document.createElement("li");
  const d = document.createElement("details"); d.className = "insight";
  const sum = document.createElement("summary");
  const id = document.createElement("span"); id.className = "id"; id.textContent = ins.id;
  const title = document.createElement("span"); title.className = "title"; title.textContent = ins.title;
  sum.append(id, title, confidenceBadge(ins, nTranscripts));
  if (ins.critic_flags?.length) { const c = document.createElement("span"); c.className = "badge contested"; c.textContent = "contested"; sum.append(c); }
  const body = document.createElement("div"); body.className = "body";
  const claim = document.createElement("p"); claim.textContent = ins.claim; body.append(claim);
  const src = document.createElement("p"); src.className = "fine";
  src.textContent = `Sources: ${(ins.sources ?? []).join(", ") || "–"} · ${ins.evidence?.length ?? 0} receipts · ${ins.counter_evidence?.length ?? 0} counter`;
  body.append(src);
  for (const ev of (ins.evidence ?? []).slice(0, 2)) {
    const qd = document.createElement("p"); qd.className = "quote"; qd.textContent = `${ev.turn}: “${ev.quote}”`; body.append(qd);
  }
  if (ins.counter_note) { const cn = document.createElement("p"); cn.className = "fine"; cn.textContent = `Counter: ${ins.counter_note}`; body.append(cn); }
  if (ins.opportunity) { const op = document.createElement("p"); op.className = "opp"; op.textContent = `Opportunity: ${ins.opportunity}`; body.append(op); }
  if (ins.critic_flags?.length) { const fl = document.createElement("p"); fl.className = "flags"; fl.textContent = `Critic: ${ins.critic_flags.join(" · ")}`; body.append(fl); }
  d.append(sum, body);
  li.append(d);
  return li;
}

function claimEl(ins: Insight, r: VerdictResult): HTMLElement {
  const objections = r.verdict.failures.filter((f) => f.insight_id === ins.id);
  const worst = objections.some((f) => f.severity !== "warn") ? "fail" : objections.length ? "warn" : "pass";
  const li = document.createElement("li");
  const d = document.createElement("details"); d.className = "insight"; d.open = worst !== "pass";
  const sum = document.createElement("summary");
  const id = document.createElement("span"); id.className = "id"; id.textContent = ins.id;
  const title = document.createElement("span"); title.className = "title"; title.textContent = ins.title || ins.claim.slice(0, 80);
  const b = document.createElement("span"); b.className = `badge ${worst === "fail" ? "contested" : worst === "warn" ? "medium" : "high"}`;
  b.textContent = worst === "pass" ? "no objection" : `${objections.length} ${worst === "fail" ? "fail" : "warning"}${objections.length === 1 ? "" : "s"}`;
  sum.append(id, title, b);
  const body = document.createElement("div"); body.className = "body";
  const claim = document.createElement("p"); claim.textContent = ins.claim; body.append(claim);
  const src = document.createElement("p"); src.className = "fine";
  src.textContent = `Cites ${ins.evidence?.length ?? 0} turn${(ins.evidence?.length ?? 0) === 1 ? "" : "s"}${ins.evidence?.length ? ": " + ins.evidence.map((e) => e.turn).join(", ") : ""}`;
  body.append(src);
  for (const f of objections) {
    const p = document.createElement("p"); p.className = f.severity === "warn" ? "fine" : "flags";
    p.textContent = `${f.severity.toUpperCase()} ${f.rule}: ${f.detail}${f.turns?.length ? ` [${f.turns.join(", ")}]` : ""}`;
    body.append(p);
  }
  d.append(sum, body);
  li.append(d);
  return li;
}

function verdictMarkdown(s: Stored, r: VerdictResult): string {
  const lines = [`# Motif critique`, "", s.question ? `Question: ${s.question}` : "", `Run: ${r.run_id}`,
    `Verdict: ${r.verdict.pass ? "PASS" : "FAIL"} — ${r.summary.n_fail} fail(s), ${r.summary.n_warn} warning(s) on ${r.insights.length} claim(s)`,
    r.verdict.skipped_rules?.length ? `Not checked: ${r.verdict.skipped_rules.join(", ")}` : "", r.verdict.notes ? `Notes: ${r.verdict.notes}` : "", ""];
  for (const ins of r.insights) {
    lines.push(`## ${ins.id} — ${ins.title || ""}`, "", ins.claim, "");
    if (ins.evidence?.length) lines.push(`Cites: ${ins.evidence.map((e) => e.turn).join(", ")}`, "");
    const obj = r.verdict.failures.filter((f) => f.insight_id === ins.id);
    if (!obj.length) lines.push("- no objection", "");
    for (const f of obj) lines.push(`- **${f.severity.toUpperCase()} ${f.rule}**: ${f.detail}${f.turns?.length ? ` [${f.turns.join(", ")}]` : ""}`);
    if (obj.length) lines.push("");
  }
  const rest = r.verdict.failures.filter((f) => !r.insights.some((i) => i.id === f.insight_id));
  if (rest.length) { lines.push("## Whole corpus", ""); for (const f of rest) lines.push(`- **${f.severity.toUpperCase()} ${f.rule}**: ${f.detail}`); }
  return lines.filter((l, i, a) => !(l === "" && a[i - 1] === "")).join("\n");
}

$("copy-report").onclick = async () => {
  if (!current) return;
  const md = isVerdict(current.result) ? verdictMarkdown(current, current.result) : current.result.report_markdown;
  const ta = $<HTMLTextAreaElement>("clip");
  ta.value = md;
  let ok = false;
  try { await navigator.clipboard.writeText(md); ok = true; } catch { /* sandboxed iframe: fall through */ }
  if (!ok) {
    ta.hidden = false; ta.focus(); ta.select();
    try { ok = document.execCommand("copy"); } catch { ok = false; }
  }
  if (ok) {
    ta.hidden = true;
    post({ type: "notify", message: "Report copied as Markdown." });
  } else {
    $("clip-note").hidden = false;
    ta.hidden = false; ta.focus(); ta.select();
    post({ type: "notify", message: "Clipboard is blocked here. The report is selected below: press Cmd+C or Ctrl+C.", error: true });
  }
};

$("build-board").onclick = async () => {
  if (!current?.layout) return;
  const bb = $<HTMLButtonElement>("build-board");
  bb.disabled = true;
  $("board-status").textContent = "Building the board…";
  const layout = current.layout;
  const reply = await new Promise<ToUi>((resolve) => {
    const once = (m: ToUi) => { if (m.type === "board-done" || m.type === "board-failed") { listeners.splice(listeners.indexOf(once), 1); resolve(m); } };
    listeners.push(once);
    post({ type: "build-board", layout });
  });
  bb.disabled = false;
  if (reply.type === "board-done") {
    const c = reply.counts;
    $("board-status").textContent = `Board built: ${c.sections} sections, ${c.stickies} stickies` +
      (c.connectors ? `, ${c.connectors} connectors` : reply.editor === "figma" ? " (no connectors in Figma Design)" : "") + ".";
    bb.textContent = "Build board again";
  } else if (reply.type === "board-failed") {
    $("board-status").textContent = `Board failed: ${reply.message}`;
  }
};

$("new-run").onclick = () => { show("setup"); };
$("error-back").onclick = () => show(keyMasked ? "setup" : "key");

// ------------------------------------------------------------------------ init

listeners.push((m) => {
  if (m.type === "init") {
    keyMasked = m.keyMasked; lastJob = m.lastJob;
    $("key-masked").textContent = keyMasked ?? "";
    $("resume-card").hidden = !lastJob;
    $("last-card").hidden = !m.hasLastResult;
    if (m.editor === "figma") $("editor-note").hidden = false;
    show(keyMasked ? "setup" : "key");
    if (!keyMasked) keyInput.focus();
  } else if (m.type === "key") {
    keyMasked = m.keyMasked;
    $("key-masked").textContent = keyMasked ?? "";
    if (keyMasked && $("screen-key").hidden === false) show("setup");
  }
});

setMode("synthesize");
post({ type: "ui-ready" });

// Harness-only hooks (never active inside Figma): ?files=url,url loads transcripts from URLs;
// ?demo=url renders a saved result JSON (with ?layout=url for its board layout), so every screen
// can be checked at any width without a run.
if (!inFigma) {
  const q = new URLSearchParams(location.search);
  const urls = (q.get("files") ?? "").split(",").filter(Boolean);
  const demo = q.get("demo");
  (async () => {
    if (urls.length) {
      const fs: File[] = [];
      for (const u of urls) { const r = await fetch(u); fs.push(new File([await r.blob()], decodeURIComponent(u.split("/").pop() ?? "t.txt"))); }
      await addFiles(fs);
    }
    if (q.get("mode") === "critique") setMode("critique");
    if (demo) {
      const result = (await (await fetch(demo)).json()) as Result | VerdictResult;
      const layout = q.get("layout") ? ((await (await fetch(q.get("layout")!)).json()) as Layout) : null;
      renderResult({ kind: "verdict" in result ? "critique" : "synthesize", question: q.get("q") ?? "Demo result",
        nTranscripts: parseInt(q.get("n") ?? "0", 10), result, layout, jobId: "demo", when: Date.now() });
    }
  })().catch((e) => console.error("harness:", e));
}
