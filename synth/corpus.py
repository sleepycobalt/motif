"""Load processed transcripts (from scripts/ingest.py) into memory."""

import json
from pathlib import Path


class Corpus:
    def __init__(self, processed_dir: str | Path, names: list[str] | None = None):
        self.dir = Path(processed_dir)
        manifest = json.load(open(self.dir / "manifest.json", encoding="utf-8"))
        self.meta = {m["name"]: m for m in manifest}
        self.names = names or sorted(self.meta)
        missing = [n for n in self.names if n not in self.meta]
        if missing:
            raise SystemExit(f"unknown transcript(s): {missing}; have {sorted(self.meta)}")
        self.turns: dict[str, dict] = {}
        self.text: dict[str, str] = {}
        for n in self.names:
            with open(self.dir / f"{n}.jsonl", encoding="utf-8") as fh:
                for line in fh:
                    t = json.loads(line)
                    self.turns[t["id"]] = t
            self.text[n] = open(self.dir / f"{n}.txt", encoding="utf-8").read()

    def transcript_of(self, turn_id: str) -> str:
        return turn_id.split(":", 1)[0]

    def has(self, turn_id: str) -> bool:
        return turn_id in self.turns

    def render_turns(self, ids: list[str]) -> str:
        out = []
        for i in ids:
            t = self.turns.get(i)
            out.append(f"[{i}] {t['speaker']}: {t['text']}" if t else f"[{i}] (NOT FOUND)")
        return "\n".join(out)

    def render_all(self) -> str:
        parts = []
        for n in self.names:
            m = self.meta[n]
            parts.append(f"=== TRANSCRIPT: {n} ({m['turns']} turns, {m['words']} words) ===\n{self.text[n]}")
        return "\n\n".join(parts)

    @property
    def words(self) -> int:
        return sum(self.meta[n]["words"] for n in self.names)
