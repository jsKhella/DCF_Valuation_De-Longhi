"""Populate data/raw/ with the exact input files used by the project.

    python fetch_data.py            # fills data/raw next to this script
    python fetch_data.py --dest X   # fills X instead (market files are copied there from data/raw/market)

What it does
  * market/  (ECB + Yahoo): already shipped in data/raw/market as a frozen snapshot. These are "last 5 years"
             feeds, so re-downloading later gives different numbers; the snapshot is the input. Only checked.
  * reports/ and damodaran/: downloaded from the URLs listed in data/raw/SOURCES.md (company PDFs and Damodaran
             datasets, not redistributed here) and checked against the recorded SHA-256.
Files already present with the right hash are skipped. Exit code 1 if any file is missing or has a
different hash (a different hash means the publisher changed the file: results may then differ).
"""
import argparse
import hashlib
import re
import shutil
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
SOURCES = RAW / "SOURCES.md"
SNAPSHOT = RAW / "market"


def parse_sources():
    """Yield (subdir, filename, url, sha256) for every table row in SOURCES.md."""
    subdir = None
    for line in SOURCES.read_text(encoding="utf-8").splitlines():
        m = re.match(r"##\s.*\(`(\w+)/`\)", line)
        if m:
            subdir = m.group(1)
        row = [c.strip() for c in line.strip().strip("|").split("|")]
        if subdir and len(row) == 4 and re.fullmatch(r"[0-9a-f]{64}", row[3]):
            yield subdir, row[0], row[1], row[3]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url, target):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (reproducibility-fetch)"})
    with urllib.request.urlopen(req, timeout=120) as r, open(target, "wb") as f:
        shutil.copyfileobj(r, f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", default=str(RAW))
    dest = Path(ap.parse_args().dest).resolve()
    bad = 0
    for subdir, name, url, want in parse_sources():
        target = dest / subdir / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and sha256(target) == want:
            print(f"ok       {subdir}/{name} (already present)")
            continue
        try:
            if subdir == "market":
                if (SNAPSHOT / name).resolve() == target:
                    raise FileNotFoundError("snapshot file missing or altered; restore it from the repository")
                shutil.copyfile(SNAPSHOT / name, target)
            else:
                print(f"fetching {subdir}/{name} ...", flush=True)
                download(url, target)
        except Exception as e:  # noqa: BLE001
            print(f"MISSING  {subdir}/{name}: {e}")
            bad += 1
            continue
        got = sha256(target)
        if got == want:
            print(f"ok       {subdir}/{name}")
        else:
            print(f"MISMATCH {subdir}/{name}: expected {want[:12]}..., got {got[:12]}... (publisher changed the file)")
            bad += 1
    if dest != RAW and not (dest / "SOURCES.md").exists():
        shutil.copyfile(SOURCES, dest / "SOURCES.md")  # the process guide cites data/raw/SOURCES.md
    print("\nAll inputs present and identical." if not bad else f"\n{bad} file(s) missing or different.")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
