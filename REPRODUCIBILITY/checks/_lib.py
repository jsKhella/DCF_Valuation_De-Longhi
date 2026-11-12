"""Shared helpers for CURIOSITY check scripts. Every check prints PASS/FAIL with actual vs expected.

Usage in checks/check_stepNN.py:

    from _lib import Checks
    c = Checks()                       # connects to data/curiosity.duckdb (read-only)
    n = c.scalar("SELECT COUNT(*) FROM late_orders")
    c.equal("one row per order", n, c.scalar("SELECT COUNT(DISTINCT order_id) FROM late_orders"))
    c.between("late rate plausible", rate, 0.03, 0.20)
    c.near("total revenue", rev, other_rev, rel=1e-9)
    c.zero("no null keys", "SELECT COUNT(*) FROM late_orders WHERE order_id IS NULL")
    c.done()                           # exits 1 if any check failed
"""
import math
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "curiosity.duckdb"


class Checks:
    def __init__(self, db: Path = DB):
        self.con = duckdb.connect(str(db), read_only=True)
        self.failed = 0
        self.total = 0

    def scalar(self, sql: str):
        return self.con.execute(sql).fetchone()[0]

    def _report(self, name, ok, detail):
        self.total += 1
        if not ok:
            self.failed += 1
        print(f"{'PASS' if ok else 'FAIL'}  {name}  ({detail})")

    def equal(self, name, actual, expected):
        self._report(name, actual == expected, f"actual={actual!r} expected={expected!r}")

    def between(self, name, actual, lo, hi):
        ok = actual is not None and lo <= actual <= hi
        self._report(name, ok, f"actual={actual!r} expected in [{lo}, {hi}]")

    def near(self, name, actual, expected, rel=1e-9):
        ok = actual is not None and expected is not None and math.isclose(actual, expected, rel_tol=rel, abs_tol=0.0)
        self._report(name, ok, f"actual={actual!r} expected={expected!r} rel_tol={rel}")

    def zero(self, name, sql):
        """Passes when the query returns 0 (e.g. a count of violating rows)."""
        self.equal(name, self.scalar(sql), 0)

    def done(self):
        print(f"\n{self.total - self.failed}/{self.total} checks passed")
        self.con.close()
        sys.exit(1 if self.failed else 0)
