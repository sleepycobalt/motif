/**
 * Motif for Figma: main thread.
 *
 * Owns what only the main thread can: client storage (the user's Anthropic key,
 * the last job id), notifications, window size. The UI iframe (ui.ts) owns the
 * network. The key is read from storage only when the UI asks at submit time,
 * sent to the iframe once, and never rendered back except masked.
 *
 * The board writer (stage 3) will live here too: it needs the plugin API.
 */

type ToMain =
  | { type: "ui-ready" }
  | { type: "get-key" }
  | { type: "save-key"; key: string }
  | { type: "clear-key" }
  | { type: "set-last-job"; jobId: string | null; question?: string }
  | { type: "notify"; message: string; error?: boolean }
  | { type: "resize"; width: number; height: number }
  | { type: "close" };

type ToUi =
  | { type: "init"; keyMasked: string | null; lastJob: { jobId: string; question?: string } | null; editor: string }
  | { type: "key"; key: string | null; keyMasked: string | null };

const KEY = "anthropic_key";
const LAST_JOB = "last_job";
const DEFAULT_SIZE = { width: 440, height: 660 };

function masked(key: string | null): string | null {
  return key ? `…${key.slice(-4)}` : null;
}

async function send(msg: ToUi): Promise<void> {
  figma.ui.postMessage(msg);
}

figma.showUI(__html__, { ...DEFAULT_SIZE, themeColors: true, title: "Motif" });

figma.ui.onmessage = async (msg: ToMain) => {
  switch (msg.type) {
    case "ui-ready": {
      const key = (await figma.clientStorage.getAsync(KEY)) as string | undefined;
      const lastJob = ((await figma.clientStorage.getAsync(LAST_JOB)) as { jobId: string; question?: string } | undefined) ?? null;
      await send({ type: "init", keyMasked: masked(key ?? null), lastJob, editor: figma.editorType });
      break;
    }
    case "get-key": {
      const key = ((await figma.clientStorage.getAsync(KEY)) as string | undefined) ?? null;
      await send({ type: "key", key, keyMasked: masked(key) });
      break;
    }
    case "save-key": {
      const key = msg.key.trim();
      if (!key) { figma.notify("The key was empty; nothing saved.", { error: true }); break; }
      await figma.clientStorage.setAsync(KEY, key);
      await send({ type: "key", key: null, keyMasked: masked(key) });
      figma.notify("Key saved on this device. It is sent only to Motif's engine, for your runs.");
      break;
    }
    case "clear-key": {
      await figma.clientStorage.deleteAsync(KEY);
      await send({ type: "key", key: null, keyMasked: null });
      figma.notify("Key removed.");
      break;
    }
    case "set-last-job": {
      if (msg.jobId) await figma.clientStorage.setAsync(LAST_JOB, { jobId: msg.jobId, question: msg.question });
      else await figma.clientStorage.deleteAsync(LAST_JOB);
      break;
    }
    case "notify":
      figma.notify(msg.message, { error: !!msg.error, timeout: msg.error ? 6000 : 3000 });
      break;
    case "resize":
      figma.ui.resize(Math.max(320, Math.round(msg.width)), Math.max(400, Math.round(msg.height)));
      break;
    case "close":
      figma.closePlugin();
      break;
  }
};
