"""
Credit ledger for the paid tier. Designed now, switched on later.

The paid tier sells prepaid credit bundles; a run is metered against the
buyer's balance before it starts and settled when it ends. Exposure is bounded
by what was prepaid: `reserve` refuses when the balance is short, and there is
no path to a paid run without a reservation. Balances are integer cents.

Top-ups come from a payment provider's webhook (Stripe Checkout, per the
plan). That path is deliberately not built here: `stripe_topup` raises until
the prerequisites in docs/specs/motif-figma-plugin.md are met and the
webhook is written and tested against a real (test-mode) purchase.

Pricing calibration, from docs/part2-notes.md: the MCP refactor regression
(11,482 words) cost $0.5529; the 15-transcript recorded run cost $4.88. The
spec asks for runs priced at 2x API cost or more, so the reserve rate is
10 cents per 1,000 words (about 2.1x the regression run's cost per word) and
settlement charges max(2x actual API cost, the reservation's floor of 50 cents).
"""

from __future__ import annotations

import math
import sqlite3
import threading
import time
from pathlib import Path

CENTS_PER_1000_WORDS = 10
MARGIN = 2.0
MIN_CHARGE_CENTS = 50


class InsufficientCredits(RuntimeError):
    pass


def estimate_cents(words: int) -> int:
    """What to reserve before a run of `words` starts."""
    return max(MIN_CHARGE_CENTS, math.ceil(words / 1000 * CENTS_PER_1000_WORDS))


def settle_cents(api_cost_usd: float) -> int:
    """What a finished run actually costs the buyer."""
    return max(MIN_CHARGE_CENTS, math.ceil(api_cost_usd * 100 * MARGIN))


class Ledger:
    """SQLite-backed balance and reservation log. One writer at a time; small by design."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        with self._conn() as c:
            c.executescript("""
                CREATE TABLE IF NOT EXISTS balances (user TEXT PRIMARY KEY, cents INTEGER NOT NULL DEFAULT 0);
                CREATE TABLE IF NOT EXISTS entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL NOT NULL, user TEXT NOT NULL,
                    kind TEXT NOT NULL, cents INTEGER NOT NULL, ref TEXT);
                CREATE TABLE IF NOT EXISTS reservations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL NOT NULL, user TEXT NOT NULL,
                    cents INTEGER NOT NULL, job_id TEXT, settled INTEGER NOT NULL DEFAULT 0, actual INTEGER);
            """)

    def _conn(self):
        return sqlite3.connect(self.path, isolation_level=None)

    def balance(self, user: str) -> int:
        with self._conn() as c:
            row = c.execute("SELECT cents FROM balances WHERE user=?", (user,)).fetchone()
        return int(row[0]) if row else 0

    def add(self, user: str, cents: int, ref: str) -> int:
        """Credit a top-up (or a refund). Returns the new balance."""
        if cents <= 0:
            raise ValueError("top-up must be positive")
        with self._lock, self._conn() as c:
            c.execute("INSERT INTO balances(user, cents) VALUES(?, 0) ON CONFLICT(user) DO NOTHING", (user,))
            c.execute("UPDATE balances SET cents = cents + ? WHERE user=?", (cents, user))
            c.execute("INSERT INTO entries(ts, user, kind, cents, ref) VALUES(?,?,?,?,?)",
                      (time.time(), user, "topup", cents, ref))
            return int(c.execute("SELECT cents FROM balances WHERE user=?", (user,)).fetchone()[0])

    def reserve(self, user: str, cents: int, job_id: str) -> int:
        """Hold `cents` for a job. Refuses rather than overdrawing. Returns the reservation id."""
        with self._lock, self._conn() as c:
            row = c.execute("SELECT cents FROM balances WHERE user=?", (user,)).fetchone()
            have = int(row[0]) if row else 0
            if have < cents:
                raise InsufficientCredits(f"balance {have} cents is below the {cents} cents this run needs")
            c.execute("UPDATE balances SET cents = cents - ? WHERE user=?", (cents, user))
            cur = c.execute("INSERT INTO reservations(ts, user, cents, job_id) VALUES(?,?,?,?)",
                            (time.time(), user, cents, job_id))
            c.execute("INSERT INTO entries(ts, user, kind, cents, ref) VALUES(?,?,?,?,?)",
                      (time.time(), user, "reserve", -cents, job_id))
            return int(cur.lastrowid)

    def settle(self, reservation_id: int, actual_cents: int) -> int:
        """Replace the hold with the real charge, capped at the hold. Returns the refund in cents."""
        with self._lock, self._conn() as c:
            row = c.execute("SELECT user, cents, settled FROM reservations WHERE id=?", (reservation_id,)).fetchone()
            if not row:
                raise LookupError(f"no reservation {reservation_id}")
            user, held, settled = row
            if settled:
                raise RuntimeError(f"reservation {reservation_id} already settled")
            charge = min(int(held), max(0, actual_cents))
            refund = int(held) - charge
            c.execute("UPDATE reservations SET settled=1, actual=? WHERE id=?", (charge, reservation_id))
            if refund:
                c.execute("UPDATE balances SET cents = cents + ? WHERE user=?", (refund, user))
            c.execute("INSERT INTO entries(ts, user, kind, cents, ref) VALUES(?,?,?,?,?)",
                      (time.time(), user, "settle", refund, str(reservation_id)))
            return refund

    def release(self, reservation_id: int) -> int:
        """A job that never ran (failed before its first model call) gets its hold back in full."""
        return self.settle(reservation_id, 0)


def stripe_topup(*_args, **_kw):
    raise NotImplementedError(
        "the paid tier is not switched on: no payment rails until the prerequisites in "
        "docs/specs/motif-figma-plugin.md are met")
