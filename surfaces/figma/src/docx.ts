/**
 * Paragraph text out of a .docx, in the browser, with no library.
 *
 * A .docx is a zip; the body is word/document.xml. The sample corpus files are
 * ~6 MB each because they embed fonts, while their text is a few hundred KB,
 * so the plugin extracts paragraphs here and uploads text (see
 * docs/part3-notes.md, 2026-09-04). The extraction mirrors python-docx's
 * `paragraph.text` for body-level paragraphs, which is what the engine's
 * ingest reads: body-level <w:p>, then each <w:r> (directly or under a
 * <w:hyperlink>) contributes <w:t> text, <w:tab> as a tab. One deliberate
 * difference: <w:br>/<w:cr> inside a paragraph becomes a space, not a newline,
 * because the upload is one turn per line and a newline would split the turn.
 * Parity with python-docx (modulo that) is checked by test/docx_parity.mjs on
 * the sample corpus.
 *
 * Inflate uses DecompressionStream("deflate-raw"), available in Chromium.
 */

const W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main";

function u16(b: DataView, o: number): number { return b.getUint16(o, true); }
function u32(b: DataView, o: number): number { return b.getUint32(o, true); }

async function inflateRaw(data: Uint8Array): Promise<Uint8Array> {
  const ds = new DecompressionStream("deflate-raw");
  const stream = new Blob([data as BlobPart]).stream().pipeThrough(ds);
  return new Uint8Array(await new Response(stream).arrayBuffer());
}

/** Read one member of a zip by name. Handles stored and deflated entries; no zip64. */
export async function zipMember(buf: ArrayBuffer, wanted: string): Promise<Uint8Array> {
  const bytes = new Uint8Array(buf);
  const dv = new DataView(buf);
  const dec = new TextDecoder("utf-8");
  // End of central directory: signature 0x06054b50, searched backwards through the comment space.
  let eocd = -1;
  for (let i = bytes.length - 22; i >= Math.max(0, bytes.length - 22 - 65535); i--) {
    if (u32(dv, i) === 0x06054b50) { eocd = i; break; }
  }
  if (eocd < 0) throw new Error("not a zip file (no end-of-central-directory record)");
  const count = u16(dv, eocd + 10);
  let p = u32(dv, eocd + 16);
  for (let n = 0; n < count; n++) {
    if (u32(dv, p) !== 0x02014b50) throw new Error("corrupt zip central directory");
    const method = u16(dv, p + 10);
    const csize = u32(dv, p + 20);
    const nameLen = u16(dv, p + 28), extraLen = u16(dv, p + 30), commentLen = u16(dv, p + 32);
    const local = u32(dv, p + 42);
    const name = dec.decode(bytes.subarray(p + 46, p + 46 + nameLen));
    p += 46 + nameLen + extraLen + commentLen;
    if (name !== wanted) continue;
    if (u32(dv, local) !== 0x04034b50) throw new Error("corrupt zip local header");
    const start = local + 30 + u16(dv, local + 26) + u16(dv, local + 28);
    const raw = bytes.subarray(start, start + csize);
    if (method === 0) return raw;
    if (method === 8) return inflateRaw(raw);
    throw new Error(`unsupported zip compression method ${method}`);
  }
  throw new Error(`${wanted} not found in zip`);
}

function elements(n: Node): Element[] {
  // childNodes, not children: the Node-side parity test runs this under @xmldom/xmldom (DOM level 2).
  return Array.from(n.childNodes).filter((c): c is Element => c.nodeType === 1);
}

function runText(run: Element): string {
  let s = "";
  for (const c of elements(run)) {
    if (c.namespaceURI !== W) continue;
    if (c.localName === "t") s += c.textContent ?? "";
    else if (c.localName === "tab") s += "\t";
    else if (c.localName === "br" || c.localName === "cr") s += " ";  // a break inside a paragraph stays inside the turn
  }
  return s;
}

/** Body-level paragraphs as text, in order. Empty paragraphs are kept (callers strip and skip). */
export function paragraphsFromDocumentXml(xml: string, parser: { parseFromString(s: string, t: string): Document } = new DOMParser()): string[] {
  const doc = parser.parseFromString(xml, "application/xml");
  const err = doc.getElementsByTagName("parsererror")[0];
  if (err) throw new Error("word/document.xml did not parse: " + (err.textContent ?? "").slice(0, 120));
  const body = doc.getElementsByTagNameNS(W, "body")[0];
  if (!body) throw new Error("word/document.xml has no body");
  const out: string[] = [];
  for (const p of elements(body)) {
    if (p.namespaceURI !== W || p.localName !== "p") continue;
    let s = "";
    for (const c of elements(p)) {
      if (c.namespaceURI !== W) continue;
      if (c.localName === "r") s += runText(c);
      else if (c.localName === "hyperlink") {
        for (const r of elements(c)) if (r.namespaceURI === W && r.localName === "r") s += runText(r);
      }
    }
    out.push(s);
  }
  return out;
}

/** The engine's ingest reads one paragraph per line and skips blank lines; produce exactly that. */
export async function docxToText(buf: ArrayBuffer, parser?: { parseFromString(s: string, t: string): Document }): Promise<string> {
  const xml = new TextDecoder("utf-8").decode(await zipMember(buf, "word/document.xml"));
  return paragraphsFromDocumentXml(xml, parser).map((s) => s.trim()).filter(Boolean).join("\n") + "\n";
}
