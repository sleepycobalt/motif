/**
 * Motif for Figma: main thread.
 *
 * Owns what only the main thread can: client storage (the user's Anthropic key,
 * the last job, the last result with its board layout), notifications, window
 * size, and the board writer (board.ts), which needs the plugin API. The UI
 * iframe (ui.ts) owns the network. The key is read from storage only when the
 * UI asks at submit time, sent to the iframe once, and never rendered back
 * except masked.
 */

import { renderBoard, type Layout } from "./board";

type ToMain =
  | { type: "ui-ready" }
  | { type: "get-key" }
  | { type: "save-key"; key: string }
  | { type: "clear-key" }
  | { type: "set-last-job"; jobId: string | null; question?: string; kind?: string }
  | { type: "set-last-result"; payload: unknown | null }
  | { type: "get-last-result" }
  | { type: "build-board"; layout: Layout }
  | { type: "notify"; message: string; error?: boolean }
  | { type: "resize"; width: number; height: number }
  | { type: "close" };

type ToUi =
  | { type: "init"; keyMasked: string | null; lastJob: LastJob | null; hasLastResult: boolean; editor: string }
  | { type: "key"; key: string | null; keyMasked: string | null }
  | { type: "last-result"; payload: unknown | null }
  | { type: "board-done"; counts: { sections: number; stickies: number; connectors: number }; editor: string;
      bounds: { x: number; y: number; width: number; height: number } }
  | { type: "board-failed"; message: string };

interface LastJob { jobId: string; question?: string; kind?: string }

const KEY = "anthropic_key";
const LAST_JOB = "last_job";
const LAST_RESULT = "last_result";
const DEFAULT_SIZE = { width: 440, height: 660 };

function masked(key: string | null): string | null {
  return key ? `…${key.slice(-4)}` : null;
}

function send(msg: ToUi): void {
  figma.ui.postMessage(msg);
}

figma.showUI(__html__, { ...DEFAULT_SIZE, themeColors: true, title: "Motif" });

figma.ui.onmessage = async (msg: ToMain) => {
  switch (msg.type) {
    case "ui-ready": {
      const key = (await figma.clientStorage.getAsync(KEY)) as string | undefined;
      const lastJob = ((await figma.clientStorage.getAsync(LAST_JOB)) as LastJob | undefined) ?? null;
      const last = await figma.clientStorage.getAsync(LAST_RESULT);
      send({ type: "init", keyMasked: masked(key ?? null), lastJob, hasLastResult: !!last, editor: figma.editorType });
      break;
    }
    case "get-key": {
      const key = ((await figma.clientStorage.getAsync(KEY)) as string | undefined) ?? null;
      send({ type: "key", key, keyMasked: masked(key) });
      break;
    }
    case "save-key": {
      const key = msg.key.trim();
      if (!key) { figma.notify("The key was empty; nothing saved.", { error: true }); break; }
      await figma.clientStorage.setAsync(KEY, key);
      send({ type: "key", key: null, keyMasked: masked(key) });
      figma.notify("Key saved on this device. It is sent only to Motif's engine, for your runs.");
      break;
    }
    case "clear-key": {
      await figma.clientStorage.deleteAsync(KEY);
      send({ type: "key", key: null, keyMasked: null });
      figma.notify("Key removed.");
      break;
    }
    case "set-last-job": {
      if (msg.jobId) await figma.clientStorage.setAsync(LAST_JOB, { jobId: msg.jobId, question: msg.question, kind: msg.kind });
      else await figma.clientStorage.deleteAsync(LAST_JOB);
      break;
    }
    case "set-last-result": {
      if (msg.payload) await figma.clientStorage.setAsync(LAST_RESULT, msg.payload);
      else await figma.clientStorage.deleteAsync(LAST_RESULT);
      break;
    }
    case "get-last-result": {
      send({ type: "last-result", payload: (await figma.clientStorage.getAsync(LAST_RESULT)) ?? null });
      break;
    }
    case "build-board": {
      try {
        const res = await renderBoard(msg.layout);
        const nodes = res.nodeIds.map((id) => figma.getNodeById(id)).filter((n): n is SceneNode => !!n && "x" in n);
        figma.viewport.scrollAndZoomIntoView(nodes);
        send({ type: "board-done", counts: res.counts, editor: res.editor, bounds: res.bounds });
        figma.notify(`Motif board: ${res.counts.sections} sections, ${res.counts.stickies} stickies` +
          (res.counts.connectors ? `, ${res.counts.connectors} connectors` : ""));
      } catch (e) {
        send({ type: "board-failed", message: (e as Error).message });
        figma.notify(`Board failed: ${(e as Error).message}`, { error: true, timeout: 6000 });
      }
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
