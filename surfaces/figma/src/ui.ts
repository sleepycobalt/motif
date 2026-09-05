/**
 * Motif for Figma: the UI iframe. Owns the network (api.ts) and the docx extraction
 * (docx.ts); asks the main thread (code.ts) for storage and notifications.
 *
 * Standalone harness: opened directly in a browser (no Figma parent), the same UI
 * runs with localStorage standing in for figma.clientStorage, so the layout can be
 * checked at any width and the whole flow exercised against the live service.
 */

import { docxToText } from "./docx";
import { followJob, getJob, submitSynthesis, ServiceError, type Insight, type Result, type Upload } from "./api";

type Screen = "key" | "setup" | "running" | "result" | "error";

interface Prepared { name: string; text: string; words: number; paragraphs: number; error?: string }

const $ = <T extends HTMLElement>(id: string): T => document.getElementById(id) as T;
// Inside Figma the UI is an iframe; the width harness (test/harness.html) also frames it, and says so with ?harness.
const inFigma = window.parent !== window && !new URLSearchParams(location.search).has("harness");

// ------------------------------------------------------------- main-thread bridge

type ToUi = { type: "init"; keyMasked: string | null; lastJob: { jobId: string; question?: string } | null; editor: string }
  | { type: "key"; key: string | null; keyMasked: string | null };

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
      reply({ type: "init", keyMasked: masked(key), lastJob: lj ? JSON.parse(lj) : null, editor: "harness" }); break;
    }
    case "get-key": reply({ type: "key", key, keyMasked: masked(key) }); break;
    case "save-key": localStorage.setItem("anthropic_key", String(msg.key)); reply({ type: "key", key: null, keyMasked: masked(String(msg.key)) }); break;
    case "clear-key": localStorage.removeItem("anthropic_key"); reply({ type: "key", key: null, keyMasked: null }); break;
    case "set-last-job": msg.jobId ? localStorage.setItem("last_job", JSON.stringify({ jobId: msg.jobId, question: msg.question })) : localStorage.removeItem("last_job"); break;
    case "notify": console.log("[notify]", msg.message); break;
  }
}

window.onmessage = (e: MessageEvent) => {
  const m = e.data?.pluginMessage as ToUi | undefined;
  if (m) listeners.forEach((l) => l(m));
};

function requestKey(): Promise<string | null> {
  return new Promise((resolve) => {
    const once = (m: ToUi) => { if (m.type === "key") { listeners.splice(listeners.indexOf(once), 1); resolve(m.key); } };
    listeners.push(once);
    post({ type: "get-key" });
  });
}

// ------------------------------------------------------------------------ state

let files: Prepared[] = [];
let keyMasked: string | null = null;
let lastJob: { jobId: string; question?: string } | null = null;
let follow: AbortController | null = null;
let timer: number | null = null;

function show(s: Screen): void {
  for (const id of ["key", "setup", "running", "result", "error"]) $(`screen-${id}`).hidden = id !== s;
  window.scrollTo(0, 0);
}

function fail(message: string): void {
  stopTimer();
  const hint = /authentication_error|API key is invalid|401/.test(message)
    ? "Anthropic rejected the key. Check it at console.anthropic.com, then use \u201cchange\u201d to enter it again."
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

function updateRun(): void {
  runBtn.disabled = !(files.some((f) => !f.error) && question.value.trim().length > 0);
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

runBtn.onclick = async () => {
  const good = files.filter((f) => !f.error);
  const uploads: Upload[] = good.map((f) => ({ name: f.name, bytes_b64: btoa(unescape(encodeURIComponent(f.text))) }));
  const q = question.value.trim();
  runBtn.disabled = true;
  const key = await requestKey();
  if (!key) { runBtn.disabled = false; show("key"); return; }
  let jobId: string;
  try {
    jobId = await submitSynthesis(key, uploads, q);
  } catch (e) {
    runBtn.disabled = false;
    fail(e instanceof ServiceError ? `${e.message}${e.status ? ` (HTTP ${e.status})` : ""}` : (e as Error).message);
    return;
  }
  post({ type: "set-last-job", jobId, question: q });
  lastJob = { jobId, question: q };
  await run(jobId, q, Date.now());
};

$("resume-btn").onclick = () => { if (lastJob) void run(lastJob.jobId, lastJob.question ?? "", null); };
$("resume-dismiss").onclick = () => { lastJob = null; post({ type: "set-last-job", jobId: null }); $("resume-card").hidden = true; };

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

async function run(jobId: string, q: string, startedAt: number | null): Promise<void> {
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
  startTimer(startedAt ?? job.created * 1000);
  if (job.state === "done" || job.state === "failed") { finish(job.state, job.error, q, jobId); return; }
  let end;
  try {
    end = await followJob(jobId, appendLog, follow.signal);
  } catch (e) {
    if ((e as Error).name === "AbortError") { show("setup"); return; }
    fail((e as Error).message);
    return;
  }
  finish(end.state, end.error, q, jobId);
}

async function finish(state: string, error: string | null, q: string, jobId: string): Promise<void> {
  stopTimer();
  post({ type: "set-last-job", jobId: null });
  lastJob = null;
  $("resume-card").hidden = true;
  if (state !== "done") { fail(error || `The run ended as "${state}" with no result.`); return; }
  let job;
  try { job = await getJob(jobId); } catch (e) { fail((e as Error).message); return; }
  if (!job.result || !job.result.insights?.length) { fail("The run finished but returned no insights. Silence is never a result."); return; }
  renderResult(job.result, q);
  post({ type: "notify", message: `Motif: ${job.result.n_insights} insights, ${job.result.contested.length} contested.` });
}

$("stop-follow").onclick = () => { follow?.abort(); stopTimer(); show("setup"); };

// ----------------------------------------------------------------- result screen

let lastResult: Result | null = null;

function renderResult(r: Result, q: string): void {
  lastResult = r;
  $("result-question").textContent = q;
  $("t-insights").textContent = String(r.n_insights);
  $("t-contested").textContent = String(r.contested.length);
  $("t-iterations").textContent = String(r.iterations);
  $("t-cost").textContent = r.cost_usd != null ? `$${r.cost_usd.toFixed(2)}` : "–";
  $("t-time").textContent = r.wall_seconds != null ? (r.wall_seconds / 60).toFixed(1) : "–";
  const note = $("contested-note");
  if (r.contested.length) {
    note.hidden = false;
    note.textContent = `The critic still objected to ${r.contested.join(", ")} when the loop stopped (${r.stop_reason.replace("_", " ")}). Read those with the objection in view; silence is never agreement.`;
  } else {
    note.hidden = r.stop_reason === "critic_pass" ? true : false;
    note.textContent = r.stop_reason === "critic_pass" ? "" : `Stopped: ${r.stop_reason.replace("_", " ")}.`;
  }
  const ol = $("insights");
  ol.innerHTML = "";
  for (const ins of r.insights) ol.append(insightEl(ins));
  show("result");
}

function insightEl(ins: Insight): HTMLElement {
  const li = document.createElement("li");
  const d = document.createElement("details"); d.className = "insight";
  const sum = document.createElement("summary");
  const id = document.createElement("span"); id.className = "id"; id.textContent = ins.id;
  const title = document.createElement("span"); title.className = "title"; title.textContent = ins.title;
  const conf = document.createElement("span"); conf.className = `badge ${(ins.confidence || "low").toLowerCase()}`; conf.textContent = (ins.confidence || "low").toLowerCase();
  sum.append(id, title, conf);
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

$("copy-report").onclick = async () => {
  if (!lastResult) return;
  const md = lastResult.report_markdown;
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
    // No clipboard access here: leave the report selected in a visible box so one keystroke copies it.
    $("clip-note").hidden = false;
    ta.hidden = false; ta.focus(); ta.select();
    post({ type: "notify", message: "Clipboard is blocked here. The report is selected below: press Cmd+C or Ctrl+C.", error: true });
  }
};

$("new-run").onclick = () => { lastResult = null; show("setup"); };
$("error-back").onclick = () => show(keyMasked ? "setup" : "key");

// ------------------------------------------------------------------------ init

listeners.push((m) => {
  if (m.type === "init") {
    keyMasked = m.keyMasked; lastJob = m.lastJob;
    $("key-masked").textContent = keyMasked ?? "";
    $("resume-card").hidden = !lastJob;
    show(keyMasked ? "setup" : "key");
    if (!keyMasked) keyInput.focus();
  } else if (m.type === "key") {
    keyMasked = m.keyMasked;
    $("key-masked").textContent = keyMasked ?? "";
    if (keyMasked && $("screen-key").hidden === false) show("setup");
  }
});

post({ type: "ui-ready" });

// Harness-only hooks (never active inside Figma): ?files=url,url loads transcripts from URLs;
// ?demo=url renders a saved result JSON, so every screen can be checked at any width without a run.
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
    if (demo) { const r = await fetch(demo); renderResult((await r.json()) as Result, q.get("q") ?? "Demo result"); }
  })().catch((e) => console.error("harness:", e));
}
