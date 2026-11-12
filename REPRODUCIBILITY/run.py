"""CURIOSITY pipeline runner: the single way to (re)build every output from data/raw/.

    python run.py                 # rebuild everything
    python run.py --through 3     # rebuild steps 1..3
    python run.py --fresh         # delete data/curiosity.duckdb first (raw_ tables are reloaded by step 0)

Executors register their step by adding one entry to STEPS. Files run in the listed order:
.sql files are executed in DuckDB; .py files run as scripts from the project root.
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent
DB = ROOT / "data" / "curiosity.duckdb"

# step number -> files (relative to project root). Step 0 = load raw data (written by the Planner).
STEPS = {
    0: ["py/00_load_raw.py", "sql/00_load_raw.sql", "sql/00_profile.sql"],
    1: ["py/01_statements.py", "sql/01_ratios.sql"],
    2: ["py/02_wacc_bridge.py"],
    3: ["py/03_forecast_valuation.py"],  # uses py/dcf.py (shared DCF engine, reused in step 4)
    4: ["py/04_sensitivity_mc.py"],      # WACC x g grid, beta line, Monte Carlo (seed 20261109)
    5: ["py/05_build_report.py"],          # Excel report + report_headline (values only; runs step 1-4 checks and the determinism test)
    6: ["py/06_build_note.py"],            # investment note .docx + chart png (numbers read back from the workbook)
    7: ["py/07_process_guide.py"],         # process guide PDF + report/build/guide_numbers.json (numbers from DuckDB or allowed files)
}


def run_file(path: Path):
    print(f"  -> {path.relative_to(ROOT)}")
    if path.suffix == ".sql":
        con = duckdb.connect(str(DB))
        try:
            con.execute(path.read_text(encoding="utf-8"))
        finally:
            con.close()
    elif path.suffix == ".py":
        subprocess.run([sys.executable, str(path)], cwd=ROOT, check=True)
    else:
        raise ValueError(f"Unsupported file type: {path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--through", type=int, default=None)
    ap.add_argument("--fresh", action="store_true")
    a = ap.parse_args()

    os.chdir(ROOT)  # relative paths inside .sql files resolve from the project root
    if a.fresh and DB.exists():
        DB.unlink()
    DB.parent.mkdir(parents=True, exist_ok=True)

    for n in sorted(STEPS):
        if a.through is not None and n > a.through:
            break
        print(f"Step {n:02d}")
        for f in STEPS[n]:
            run_file(ROOT / f)
    print("Pipeline finished.")


if __name__ == "__main__":
    main()
