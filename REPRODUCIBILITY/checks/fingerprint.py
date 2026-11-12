"""Order-independent fingerprint of DuckDB tables: row count + sum of row hashes.

Two clean rebuilds must give identical fingerprints (Verifier level V1).

    python checks/fingerprint.py late_orders order_facts            # print
    python checks/fingerprint.py --save verify/fp_run1.txt t1 t2    # save
    python checks/fingerprint.py --compare verify/fp_run1.txt t1 t2 # exit 1 if different
"""
import argparse
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "curiosity.duckdb"


def fingerprint(con, table):
    rows, h = con.execute(f'SELECT COUNT(*), COALESCE(SUM(hash(t)), 0) FROM "{table}" AS t').fetchone()
    return f"{table}\t{rows}\t{h}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tables", nargs="+")
    ap.add_argument("--db", default=str(DB))
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--save")
    g.add_argument("--compare")
    a = ap.parse_args()

    con = duckdb.connect(a.db, read_only=True)
    lines = [fingerprint(con, t) for t in a.tables]
    con.close()
    out = "\n".join(lines)
    print(out)

    if a.save:
        Path(a.save).parent.mkdir(parents=True, exist_ok=True)
        Path(a.save).write_text(out + "\n", encoding="utf-8")
    if a.compare:
        before = Path(a.compare).read_text(encoding="utf-8").strip()
        if before != out:
            print("FAIL  fingerprints differ: output is not deterministic")
            sys.exit(1)
        print("PASS  fingerprints identical")


if __name__ == "__main__":
    main()
