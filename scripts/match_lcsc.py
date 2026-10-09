#!/usr/bin/env python3
"""match_lcsc.py — best-effort match of BOM MPNs to LCSC/JLCPCB part numbers.

Queries the jlcparts cache.sqlite3 snapshot (full JLCPCB catalog, ~1.8M parts),
expected at <antmicro>/.jlcparts-cache/cachex/cache.sqlite3. To (re)fetch it:

  curl -LO https://codeload.github.com/yaqwsx/jlcparts/tar.gz/refs/heads/gh-pages
  # extract, then: 7z x data/data/cache.zip  (needs cache.z01/cache.z02 alongside)

Outputs:
  pcb-vendors/lcsc_map.json     consumed by build_vendor_packages.py ("LCSC Part #" column)
  pcb-vendors/match_report.csv  human review: matched/unmatched with stock levels

Matching is conservative: exact MPN match (case/dash/space/slash-insensitive).
Among candidates the preferred one is a JLCPCB "basic" part that is in stock
with the lowest qty-1 price. Anything unmatched is left for manual selection
on JLCPCB's site.
"""

import csv
import json
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ANTMICRO = ROOT.parent
DB = ANTMICRO / ".jlcparts-cache" / "cachex" / "cache.sqlite3"
BOARDS = ["lpddr4-test-board", "lpddr4-testbed", "ddr5-testbed"]

NORM_SQL = "upper(replace(replace(replace(replace(mfr,' ',''),'-',''),'/',''),'.',''))"


def norm(mpn):
    return re.sub(r"[^A-Z0-9]", "", (mpn or "").upper())


def qty1_price(price_str):
    if not price_str:
        return None
    try:
        first = price_str.split(",")[0]
        return float(first.split(":")[1])
    except (IndexError, ValueError):
        return None


def main():
    if not DB.exists():
        raise SystemExit(f"database missing: {DB} (see docstring)")

    con = sqlite3.connect(DB)
    con.execute(f"CREATE INDEX IF NOT EXISTS idx_mfr_norm ON jlc_components({NORM_SQL})")
    con.commit()

    lcsc_map = {}
    rows = []
    for board in BOARDS:
        bom = ROOT / "references" / board / "bom" / f"{board}.csv"
        with bom.open() as f:
            for rec in csv.DictReader(f):
                mpn = rec["MPN"].strip()
                mfr = rec["Manufacturer"].strip()
                if not mpn:
                    rows.append([board, mfr, mpn, rec["Designator"],
                                 "NO-MPN-IN-SCHEMATIC", "", 0, "", 0])
                    continue
                q = f"""SELECT lcsc, mfr, manufacturer, stock, price, library_type,
                               assembly, package, description
                        FROM jlc_components
                        WHERE present=1 AND {NORM_SQL}=?"""
                cands = con.execute(q, (norm(mpn),)).fetchall()
                if not cands:
                    rows.append([board, mfr, mpn, rec["Designator"],
                                 "UNMATCHED", "", 0, "", 0])
                    continue

                def score(c):
                    lcsc, db_mfr, db_mfrname, stock, price, lib, asm, pkg, desc = c
                    p = qty1_price(price)
                    mfr_ok = bool(mfr) and mfr.upper() in (db_mfrname or "").upper()
                    return (lib == "basic", mfr_ok, stock > 0,
                            -(p if p is not None else 9e9))

                best = max(cands, key=score)
                lcsc, db_mfr, db_mfrname, stock, price, lib, asm, pkg, desc = best
                lcsc_map[mpn.upper()] = {
                    "lcsc": f"C{lcsc}", "stock": stock, "library_type": lib,
                    "matched_mpn": db_mfr}
                rows.append([board, mfr, mpn, rec["Designator"],
                             "matched", f"C{lcsc}", stock, lib,
                             qty1_price(price) or 0])

    (ROOT / "pcb-vendors" / "lcsc_map.json").write_text(
        json.dumps(lcsc_map, indent=1, sort_keys=True) + "\n")
    with (ROOT / "pcb-vendors" / "match_report.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["board", "manufacturer", "mpn", "designators",
                    "result", "lcsc", "stock", "library_type", "qty1_price_usd"])
        w.writerows(rows)

    matched = [r for r in rows if r[4] == "matched"]
    basic = [r for r in matched if r[7] == "basic"]
    print(f"matched {len(matched)}/{len(rows)} BOM lines "
          f"({len(lcsc_map)} distinct MPNs, {len(basic)} basic parts)")
    unmatched = [r for r in rows if r[4] != "matched"]
    if unmatched:
        print("\nunmatched (manual selection / consign needed):")
        for r in unmatched:
            print(f"  [{r[0]}] {r[1]} {r[2]} x{len(r[3].split(','))} ({r[3][:40]})")
    print("\nwrote pcb-vendors/lcsc_map.json and pcb-vendors/match_report.csv")


if __name__ == "__main__":
    main()
