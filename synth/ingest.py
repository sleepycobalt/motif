"""
Convert interview transcripts (.docx, .txt, .md) into citable plain text.

Transcripts must have one speaker turn per paragraph/line, starting with the
speaker's name and a colon ("Sam: ..."). Interviewer turns should be labelled
"Researcher" (or "Researcher 1", "Interviewer", "Moderator") so they can be
excluded from evidence. For each transcript this writes:
    <out>/<name>.txt    one turn per line:  [<name>:0042] Speaker: text
    <out>/<name>.jsonl  one JSON object per turn (id, speaker, text, words)
and a single <out>/manifest.json with per-transcript metadata.

Turn IDs are stable and are the unit of citation for the whole loop.
This module is the engine's ingest step; `scripts/ingest.py` is its CLI shim.
"""

import json
import re
from pathlib import Path
from typing import Callable, Iterable

SPEAKER_RE = re.compile(r"^\s*([A-Za-z][A-Za-z ]*?\d?)\s*:\s*(.*)$", re.S)
HEADER_RE = re.compile(
    r"^(?P<date>\d{2}-\w{3}-\d{4})\s*[-–]\s*(?P<time>\d{2}:\d{2})\s*[-–]\s*"
    r"(?P<length>(?:\d+h)?\d+m\d{2}s)\s*[-–]\s*(?P<naming>.+)$"
)
RESEARCHER_RE = re.compile(r"^(Researcher|Interviewer|Moderator)\s*\d*$", re.I)
EXTENSIONS = (".docx", ".txt", ".md")


def slug(stem: str) -> str:
    """'Dataset-2_Sam' -> 'sam'."""
    return stem.split("_", 1)[-1].strip().lower().replace(" ", "-")


def read_paragraphs(path: Path) -> list[str]:
    if path.suffix.lower() == ".docx":
        import docx  # python-docx; imported lazily so .txt corpora need no extra dependency
        doc = docx.Document(path)
        return [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]


def parse(path: Path):
    paras = read_paragraphs(path)
    if not paras:
        return None

    meta = {"file": path.name}
    m = HEADER_RE.match(paras[0])
    body = paras
    if m:
        meta.update(m.groupdict())
        body = paras[1:]
    elif ":" not in paras[0] and len(paras[0].split()) <= 6:
        meta["header"] = paras[0]
        body = paras[1:]

    turns, speakers, current = [], {}, None
    for text in body:
        sm = SPEAKER_RE.match(text)
        if sm:
            if current:
                turns.append(current)
            speaker, content = sm.group(1).strip(), sm.group(2).strip()
            current = {"speaker": speaker, "text": content}
            speakers[speaker] = speakers.get(speaker, 0) + 1
        elif current:
            current["text"] += " " + text
        else:
            current = {"speaker": "UNLABELLED", "text": text}
    if current:
        turns.append(current)

    name = slug(path.stem)
    for i, t in enumerate(turns, start=1):
        t["id"] = f"{name}:{i:04d}"
        t["words"] = len(t["text"].split())

    participant_speakers = [s for s in speakers if not RESEARCHER_RE.match(s)]
    meta.update({
        "name": name,
        "turns": len(turns),
        "words": sum(t["words"] for t in turns),
        "participant_words": sum(t["words"] for t in turns if t["speaker"] in participant_speakers),
        "speakers": speakers,
    })
    return meta, turns


def _source_files(source) -> list[Path]:
    if isinstance(source, (str, Path)):
        src = Path(source)
        if src.is_file():
            return [src]
        if not src.is_dir():
            raise ValueError(f"transcript source not found: {src}")
        return sorted(p for p in src.iterdir()
                      if p.suffix.lower() in EXTENSIONS and "readme" not in p.name.lower())
    files = [Path(p) for p in source]
    missing = [str(p) for p in files if not p.is_file()]
    if missing:
        raise ValueError(f"transcript file(s) not found: {missing}")
    return sorted(files)


def ingest(source, out_dir, emit: Callable[[str], None] | None = None) -> list[dict]:
    """Ingest a folder (or explicit list) of transcripts into out_dir. Returns the manifest.
    Raises ValueError when nothing usable is found — an empty corpus is a hard failure."""
    say = emit or (lambda _msg: None)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    files = _source_files(source)
    if not files:
        raise ValueError(f"no {'/'.join(EXTENSIONS)} transcripts found in {source}")

    manifest = []
    for f in files:
        result = parse(f)
        if not result:
            say(f"skip (empty): {f.name}")
            continue
        meta, turns = result
        name = meta["name"]
        with open(out / f"{name}.txt", "w", encoding="utf-8") as fh:
            for t in turns:
                fh.write(f"[{t['id']}] {t['speaker']}: {t['text']}\n")
        with open(out / f"{name}.jsonl", "w", encoding="utf-8") as fh:
            for t in turns:
                fh.write(json.dumps(t, ensure_ascii=False) + "\n")
        manifest.append(meta)
        say(f"{name:10s} {meta['turns']:4d} turns  {meta['words']:6d} words  speakers={list(meta['speakers'])}")

    if not manifest:
        raise ValueError(f"all {len(files)} transcript file(s) were empty")
    with open(out / "manifest.json", "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=False)
    total = sum(m["words"] for m in manifest)
    say(f"{len(manifest)} transcripts, {total:,} words -> {out}/")
    return manifest
