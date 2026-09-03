"""
ingest.py — convert interview transcripts (.docx, .txt, .md) into citable plain text.

Usage:
    python scripts/ingest.py data/raw data/processed

Transcripts must have one speaker turn per paragraph/line, starting with the
speaker's name and a colon ("Sam: ..."). Interviewer turns should be labelled
"Researcher" (or "Researcher 1", "Interviewer") so they can be excluded from
evidence. For each transcript this writes:
    data/processed/<name>.txt    one turn per line:  [<name>:0042] Speaker: text
    data/processed/<name>.jsonl  one JSON object per turn (id, speaker, text, words)
and a single data/processed/manifest.json with per-transcript metadata.

Turn IDs are stable and are the unit of citation for the whole loop:
every insight the synthesis agent produces must point at one or more
turn IDs, and the critic checks the claim against exactly those turns.
"""

import json
import re
import sys
from pathlib import Path

try:
    import docx
except ImportError:
    sys.exit("python-docx not installed: pip install python-docx")

SPEAKER_RE = re.compile(r"^\s*([A-Za-z][A-Za-z ]*?\d?)\s*:\s*(.*)$", re.S)
HEADER_RE = re.compile(
    r"^(?P<date>\d{2}-\w{3}-\d{4})\s*[-–]\s*(?P<time>\d{2}:\d{2})\s*[-–]\s*"
    r"(?P<length>(?:\d+h)?\d+m\d{2}s)\s*[-–]\s*(?P<naming>.+)$"
)
RESEARCHER_RE = re.compile(r"^(Researcher|Interviewer|Moderator)\s*\d*$", re.I)


def slug(stem: str) -> str:
    """'Dataset-2_Sam' -> 'sam'."""
    return stem.split("_", 1)[-1].strip().lower().replace(" ", "-")


def read_paragraphs(path: Path) -> list[str]:
    if path.suffix.lower() == ".docx":
        doc = docx.Document(path)
        return [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    # plain text / markdown: one paragraph per non-empty line
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
        # bare header line (e.g. just the participant name)
        meta["header"] = paras[0]
        body = paras[1:]

    turns = []
    speakers = {}
    current = None
    for text in body:
        sm = SPEAKER_RE.match(text)
        if sm:
            if current:
                turns.append(current)
            speaker, content = sm.group(1).strip(), sm.group(2).strip()
            current = {"speaker": speaker, "text": content}
            speakers[speaker] = speakers.get(speaker, 0) + 1
        elif current:
            # continuation paragraph with no speaker label
            current["text"] += " " + text
        else:
            # preamble text before first speaker; keep as its own turn
            current = {"speaker": "UNLABELLED", "text": text}
    if current:
        turns.append(current)

    name = slug(path.stem)
    for i, t in enumerate(turns, start=1):
        t["id"] = f"{name}:{i:04d}"
        t["words"] = len(t["text"].split())

    participant_speakers = [s for s in speakers if not RESEARCHER_RE.match(s)]
    meta.update(
        {
            "name": name,
            "turns": len(turns),
            "words": sum(t["words"] for t in turns),
            "participant_words": sum(
                t["words"] for t in turns if t["speaker"] in participant_speakers
            ),
            "speakers": speakers,
        }
    )
    return meta, turns


def main(raw_dir: str, out_dir: str):
    raw, out = Path(raw_dir), Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    manifest = []

    files = sorted(p for p in raw.iterdir()
                   if p.suffix.lower() in (".docx", ".txt", ".md") and "readme" not in p.name.lower())
    if not files:
        sys.exit(f"no .docx/.txt/.md transcripts found in {raw}")

    for f in files:
        result = parse(f)
        if not result:
            print(f"skip (empty): {f.name}")
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
        print(f"{name:10s} {meta['turns']:4d} turns  {meta['words']:6d} words  "
              f"speakers={list(meta['speakers'])}")

    with open(out / "manifest.json", "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=False)

    total = sum(m["words"] for m in manifest)
    print(f"\n{len(manifest)} transcripts, {total:,} words -> {out}/")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
