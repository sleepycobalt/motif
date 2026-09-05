/**
 * Client for the hosted engine (surfaces/hosted/app.py): submit a job, follow its
 * event stream, fetch the result. The Anthropic key goes in the X-Motif-Key header
 * of the submit call only; it is used for that job and never stored by the service.
 */

export const SERVICE = "https://motif-hosted.fly.dev";

export interface Upload { name: string; bytes_b64: string }

export interface Insight {
  id: string; title: string; claim: string; confidence: string; sources?: string[];
  evidence?: { turn: string; quote: string }[]; counter_evidence?: { turn: string; quote: string }[];
  counter_note?: string; opportunity?: string; critic_flags?: string[];
}

export interface Result {
  run_id: string; stop_reason: string; iterations: number; n_insights: number; contested: string[];
  cost_usd: number | null; wall_seconds: number | null; insights: Insight[]; report_markdown: string;
}

export interface JobRecord {
  job_id: string; kind: string; state: "queued" | "running" | "done" | "failed"; created: number;
  finished: number | null; run_id: string | null; words: number | null; n_events: number;
  error: string | null; result?: Result;
}

export class ServiceError extends Error {
  constructor(public status: number, message: string) { super(message); }
}

async function detail(r: Response): Promise<string> {
  try { const j = await r.json(); return typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail ?? j); }
  catch { return r.statusText || `HTTP ${r.status}`; }
}

export async function submitSynthesis(key: string, transcripts: Upload[], question: string): Promise<string> {
  let r: Response;
  try {
    r = await fetch(`${SERVICE}/v1/jobs`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Motif-Key": key },
      body: JSON.stringify({ kind: "synthesize", transcripts, question, condition: "C", max_iterations: 3 }),
    });
  } catch (e) {
    throw new ServiceError(0, `Could not reach Motif's engine at ${SERVICE}: ${(e as Error).message}`);
  }
  if (!r.ok) throw new ServiceError(r.status, await detail(r));
  const j = await r.json();
  if (!j.job_id) throw new ServiceError(500, "the service accepted the job but returned no job id");
  return j.job_id as string;
}

export async function getJob(jobId: string): Promise<JobRecord> {
  const r = await fetch(`${SERVICE}/v1/jobs/${encodeURIComponent(jobId)}`);
  if (!r.ok) throw new ServiceError(r.status, await detail(r));
  return r.json();
}

/**
 * Follow the job's server-sent events until the service ends the stream, calling onMessage for
 * each engine progress line. Reconnects from the last event id if the stream drops before "end".
 * Returns the end payload. `signal` aborts the follow (the job itself keeps running on the service).
 */
export async function followJob(jobId: string, onMessage: (m: string) => void, signal?: AbortSignal,
                                since = 0): Promise<{ state: string; error: string | null }> {
  for (;;) {
    const r = await fetch(`${SERVICE}/v1/jobs/${encodeURIComponent(jobId)}/events?since=${since}`, { signal });
    if (!r.ok) throw new ServiceError(r.status, await detail(r));
    if (!r.body) throw new ServiceError(500, "event stream has no body");
    const reader = r.body.getReader();
    const dec = new TextDecoder();
    let buf = "", event: string | null = null, data: string | null = null;
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      let nl: number;
      while ((nl = buf.indexOf("\n")) >= 0) {
        const line = buf.slice(0, nl).replace(/\r$/, "");
        buf = buf.slice(nl + 1);
        if (line.startsWith("id:")) since = parseInt(line.slice(3).trim(), 10) || since;
        else if (line.startsWith("event:")) event = line.slice(6).trim();
        else if (line.startsWith("data:")) data = line.slice(5).trim();
        else if (line === "") {
          if (data !== null) {
            const payload = JSON.parse(data);
            if (event === "end") return payload;
            onMessage(payload.message ?? "");
          }
          event = null; data = null;
        }
      }
    }
    if (signal?.aborted) throw new DOMException("aborted", "AbortError");
    // stream closed without an end event: resume from the last id
  }
}
