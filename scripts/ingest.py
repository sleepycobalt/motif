"""
ingest.py — convert interview transcripts (.docx, .txt, .md) into citable plain text.

Usage:
    python scripts/ingest.py data/raw data/processed

Thin CLI over synth.ingest.ingest; see that module for the format and the
turn-ID scheme.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from synth.ingest import ingest  # noqa: E402

if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    try:
        ingest(sys.argv[1], sys.argv[2], emit=print)
    except ValueError as e:
        sys.exit(str(e))
