#!/usr/bin/env python3
"""build_vendor_packages.py — regenerate PCB vendor manufacturing packages.

Produces, per board, under <repo>/references/<board>/:
  gerbers/            Gerber X2 layer files + Excellon drill + drill map/report
  bom/<board>.csv     generic BOM (grouped; LCSC/Sourcing columns merged from
                      pcb-vendors/lcsc_map.json if present)
  cpl/<board>-*.csv   pick-and-place, JLCPCB header names, top and bottom
  README.md           order notes (not overwritten if it already exists)

The script only reads the source repos; it never writes to them.

Usage:
  python3 scripts/build_vendor_packages.py                 # all boards, all steps
  python3 scripts/build_vendor_packages.py --board ddr5-testbed --step bom
"""

import argparse
import csv
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # DDRx-LPDDRx-Testbed
ANTMICRO = ROOT.parent                                  # dir holding the board repos
BUILD = ROOT / "build"                                  # scratch (gitignored)

BOARDS = [
    {
        "name": "lpddr4-test-board",
        "repo": ANTMICRO / "lpddr4-test-board",
        "pcb": "lpddr4-test-board.kicad_pcb",
        "sch": "lpddr4-test-board.kicad_sch",
        "vendor": "macrofab",
    },
    {
        "name": "lpddr4-testbed",
        "repo": ANTMICRO / "lpddr4-testbed",
        "pcb": "lpddr4-testbed.kicad_pcb",
        "sch": "lpddr4-testbed.kicad_sch",
        "vendor": "pcbway",
    },
    {
        "name": "ddr5-testbed",
        "repo": ANTMICRO / "ddr5-testbed",
        "pcb": "ddr5-testbed.kicad_pcb",
        "sch": "ddr5-testbed.kicad_sch",
        "vendor": "pcbway",
    },
]

# Parts that JLCPCB assembly cannot or will not place even though they may
# exist in the LCSC catalog (BGA FPGAs, bare DRAM, etc.). Matched by regex on
# "Manufacturer:MPN". Sourcing column and READMEs use this.
CONSIGN_HINTS = [
    (r"^(AMD-)?Xilinx:", "consign - BGA FPGA not in JLCPCB SMT library"),
    (r"^Micron( Technology)?:MT\d", "consign - DRAM not in JLCPCB SMT library"),
]

# JLCPCB wants BOM rows grouped; sort designators naturally (R2 before R10).
def natkey(ref):
    m = re.match(r"([A-Za-z]+)(\d+)", ref)
    return (m.group(1) if m else ref, int(m.group(2)) if m else 0, ref)


def run(cmd):
    cmd = [str(c) for c in cmd]
    print("+", " ".join(cmd))
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout[-3000:])
        print(r.stderr[-3000:], file=sys.stderr)
        raise SystemExit(f"command failed ({r.returncode}): {cmd[0]} ...")
    return r


def signal_layers(pcb_path):
    """Canonical signal-layer names from the board's (layers ...) block."""
    names = []
    in_layers = False
    for line in Path(pcb_path).read_text(errors="replace").splitlines():
        if "(layers" in line:
            in_layers = True
        if in_layers:
            m = re.match(r'\s*\(\d+\s+"([^"]+)"\s+signal', line)
            if m:
                names.append(m.group(1))
            if line.strip() == ")":
                break
    return names


def gen_gerbers(b):
    out = ROOT / "references" / b["name"] / "gerbers"
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*"):
        old.unlink()
    layers = signal_layers(b["repo"] / b["pcb"])
    layers += ["F.Mask", "B.Mask", "F.Silkscreen", "B.Silkscreen",
               "F.Paste", "B.Paste", "Edge.Cuts"]
    run(["kicad-cli", "pcb", "export", "gerbers",
         "--subtract-soldermask",
         "-l", ",".join(layers),
         "-o", out, b["repo"] / b["pcb"]])
    run(["kicad-cli", "pcb", "export", "drill",
         "--excellon-units", "mm",
         "--excellon-zeros-format", "decimal",
         "--excellon-separate-th",
         "--generate-map",
         "--generate-report",
         "--report-path", out / "drill-report.txt",
         "-o", out, b["repo"] / b["pcb"]])
    return sorted(p.name for p in out.iterdir())


def parse_bom_xml(xml_path):
    tree = ET.parse(xml_path)
    comps = []
    for c in tree.getroot().iter("comp"):
        fields = {f.get("name"): (f.get("value") if f.get("value") is not None else (f.text or ""))
                  for f in c.findall("fields/field")}
        comps.append({
            "ref": c.get("ref"),
            "value": (c.findtext("value") or "").strip(),
            "footprint": (c.findtext("footprint") or "").strip(),
            "manufacturer": fields.get("Manufacturer", ""),
            "mpn": fields.get("MPN", ""),
            "description": fields.get("Description", ""),
            "datasheet": fields.get("Datasheet", ""),
            "val": fields.get("Val", ""),
        })
    return comps


def gen_bom(b):
    BUILD.mkdir(exist_ok=True)
    xml = BUILD / f"{b['name']}-bom.xml"
    run(["kicad-cli", "sch", "export", "python-bom",
         b["repo"] / b["sch"], "-o", xml])
    comps = parse_bom_xml(xml)

    lcsc_map = {}
    map_path = ROOT / "pcb-vendors" / "lcsc_map.json"
    if map_path.exists():
        lcsc_map = json.loads(map_path.read_text())

    groups = OrderedDict()
    for c in comps:
        key = (c["manufacturer"], c["mpn"], c["footprint"], c["value"])
        groups.setdefault(key, []).append(c)

    out = ROOT / "references" / b["name"] / "bom"
    out.mkdir(parents=True, exist_ok=True)
    csv_path = out / f"{b['name']}.csv"
    with csv_path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Designator", "Name", "Footprint", "Manufacturer", "MPN",
                    "Description", "Quantity", "Datasheet",
                    "LCSC Part #", "Sourcing"])
        for (mfr, mpn, fp, val), cs in sorted(groups.items(), key=lambda kv: natkey(kv[1][0]["ref"])):
            refs = sorted((c["ref"] for c in cs), key=natkey)
            name = cs[0]["val"] or cs[0]["value"]
            entry = lcsc_map.get(mpn.upper()) or lcsc_map.get(f"{mfr}:{mpn}") or {}
            sourcing = ""
            for pat, note in CONSIGN_HINTS:
                if re.search(pat, f"{mfr}:{mpn}"):
                    sourcing = note
                    break
            if not mpn and not sourcing:
                sourcing = "no physical part - do not order"
            w.writerow([",".join(refs), name, fp, mfr, mpn,
                        cs[0]["description"], len(cs), cs[0]["datasheet"],
                        entry.get("lcsc", ""), sourcing])
    return len(comps), len(groups)


def gen_cpl(b):
    out = ROOT / "references" / b["name"] / "cpl"
    out.mkdir(parents=True, exist_ok=True)
    ren = {"Ref": "Designator", "Val": "Val", "Package": "Package",
           "PosX": "Mid X", "PosY": "Mid Y", "Rot": "Rotation", "Side": "Layer"}
    counts = {}
    for side, suffix in (("front", "top"), ("back", "bottom")):
        tmp = BUILD / f"{b['name']}-{suffix}.csv"
        run(["kicad-cli", "pcb", "export", "pos",
             "--side", side, "--format", "csv", "--units", "mm",
             "-o", tmp, b["repo"] / b["pcb"]])
        with tmp.open() as f:
            rows = list(csv.reader(f))
        header, body = rows[0], rows[1:]
        dst = out / f"{b['name']}-{suffix}.csv"
        with dst.open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow([ren.get(h, h) for h in header])
            for row in body:
                row = row[:]
                row[header.index("Side")] = row[header.index("Side")].capitalize()
                w.writerow(row)
        counts[suffix] = len(body)
    return counts


def gen_vendor_package(b):
    """Assemble the self-contained package for the board's chosen vendor:
    pcb-vendors/<vendor>/<board>/ with a gerber copy, that vendor's BOM/position
    formats, and the board README. Requires bom + cpl steps already run.
    """
    import shutil

    jl = ROOT / "references" / b["name"]
    vendor = b["vendor"]
    out = ROOT / "pcb-vendors" / vendor / b["name"]
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    shutil.copytree(jl / "gerbers", out / "gerbers")
    readme = jl / "README.md"
    if readme.exists():
        # vendor copies sit one level deeper; fix the relative script path
        text = readme.read_text().replace("../../scripts/", "../../../scripts/")
        (out / "README.md").write_text(text)

    with (jl / "bom" / f"{b['name']}.csv").open() as f:
        bom_rows = list(csv.DictReader(f))
    pos_rows = []
    for side in ("top", "bottom"):
        p = jl / "cpl" / f"{b['name']}-{side}.csv"
        if p.exists():
            pos_rows.extend(csv.DictReader(p.open()))

    if vendor == "macrofab":
        with (out / f"{b['name']}-bom.csv").open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["Designator", "Manufacturer", "MPN", "Quantity",
                        "Value", "Package", "Description", "Datasheet",
                        "LCSC Part #", "Sourcing"])
            for r in bom_rows:
                w.writerow([r["Designator"], r["Manufacturer"], r["MPN"],
                            r["Quantity"], r["Name"], r["Footprint"],
                            r["Description"], r["Datasheet"],
                            r["LCSC Part #"], r["Sourcing"]])
    else:  # pcbway
        try:
            from openpyxl import Workbook
            wb = Workbook()
            ws = wb.active
            ws.title = "BOM"
            ws.append(["Designator", "Name", "Footprint", "Manufacturer",
                       "MPN", "Description", "Quantity", "Datasheet",
                       "LCSC Part #", "Sourcing"])
            for r in bom_rows:
                ws.append([r["Designator"], r["Name"], r["Footprint"],
                           r["Manufacturer"], r["MPN"], r["Description"],
                           int(r["Quantity"]), r["Datasheet"],
                           r["LCSC Part #"], r["Sourcing"]])
            wb.save(out / f"{b['name']}-bom.xlsx")
        except ImportError:
            with (out / f"{b['name']}-bom.csv").open("w", newline="") as f:
                w = csv.writer(f)
                w.writerow(["Designator", "Name", "Footprint", "Manufacturer",
                            "MPN", "Description", "Quantity", "Datasheet",
                            "LCSC Part #", "Sourcing"])
                for r in bom_rows:
                    w.writerow([r["Designator"], r["Name"], r["Footprint"],
                                r["Manufacturer"], r["MPN"], r["Description"],
                                r["Quantity"], r["Datasheet"],
                                r["LCSC Part #"], r["Sourcing"]])

    with (out / f"{b['name']}-positions.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Designator", "Val", "Package", "Mid X", "Mid Y",
                    "Rotation", "Layer"])
        for r in pos_rows:
            w.writerow([r["Designator"], r["Val"], r["Package"], r["Mid X"],
                        r["Mid Y"], r["Rotation"], r["Layer"]])

    # legacy layout cleanup: per-board vendor subdirs from earlier revisions
    for old in ("macrofab", "pcbway"):
        d = jl / old
        if d.exists():
            shutil.rmtree(d)
    return len(bom_rows), len(pos_rows)


def verify(b):
    """Cross-check BOM designators against CPL designators and gerber sanity."""
    problems = []
    jl = ROOT / "references" / b["name"]

    bom_refs = set()
    with (jl / "bom" / f"{b['name']}.csv").open() as f:
        for row in csv.DictReader(f):
            bom_refs.update(r.strip() for r in row["Designator"].split(",") if r.strip())

    cpl_refs = set()
    for side in ("top", "bottom"):
        p = jl / "cpl" / f"{b['name']}-{side}.csv"
        if not p.exists():
            problems.append(f"missing CPL file: {p.name}")
            continue
        with p.open() as f:
            for row in csv.DictReader(f):
                cpl_refs.add(row["Designator"].strip())

    # Test points / net ties legitimately carry no placement data; mounting
    # holes exist only on the PCB. Anything else missing in either direction
    # is a real problem.
    only_bom = sorted(bom_refs - cpl_refs, key=natkey)
    only_cpl = sorted(cpl_refs - bom_refs, key=natkey)
    odd_bom = [r for r in only_bom if not re.match(r"^(TP\d+|N\d+)$", r)]
    odd_cpl = [r for r in only_cpl if not re.match(r"^MH\d+$", r)]
    if odd_bom:
        problems.append(f"in BOM but not CPL: {odd_bom}")
    if odd_cpl:
        problems.append(f"in CPL but not BOM: {odd_cpl}")
    if only_bom:
        print(f"  note: no-placement refs (excluded from CPL): {only_bom}")
    if only_cpl:
        print(f"  note: PCB-only refs (not in schematic BOM): {only_cpl}")

    g = jl / "gerbers"
    names = [p.name for p in g.iterdir()]
    for need in ("-F_Cu.", "-B_Cu.", "-F_Mask.", "-B_Mask.",
                 "-F_Silkscreen.", "-B_Silkscreen.", "-Edge_Cuts."):
        if not any(need in n for n in names):
            problems.append(f"gerber layer missing: {need.strip('-.')}")
    if not any(n.endswith(".drl") for n in names):
        problems.append("no excellon drill file")
    return problems, len(bom_refs), len(cpl_refs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", action="append", choices=[b["name"] for b in BOARDS])
    ap.add_argument("--step", default="all",
                    choices=["gerbers", "bom", "cpl", "vendors", "verify", "all"])
    args = ap.parse_args()

    boards = [b for b in BOARDS if not args.board or b["name"] in args.board]
    for b in boards:
        print(f"\n=== {b['name']} ===")
        steps = ["gerbers", "bom", "cpl", "vendors", "verify"] \
            if args.step == "all" else [args.step]
        if "gerbers" in steps:
            files = gen_gerbers(b)
            print(f"  gerbers: {len(files)} files")
        if "bom" in steps:
            n, g = gen_bom(b)
            print(f"  bom: {n} placements, {g} unique parts")
        if "cpl" in steps:
            counts = gen_cpl(b)
            print(f"  cpl: {counts}")
        if "vendors" in steps:
            nb, np_ = gen_vendor_package(b)
            print(f"  vendor package: pcb-vendors/{b['vendor']}/{b['name']}/ "
                  f"({nb} BOM lines, {np_} positions)")
        if "verify" in steps:
            problems, nb, nc = verify(b)
            if problems:
                for p in problems:
                    print(f"  !! {p}")
            else:
                print(f"  verify OK ({nb} BOM refs == {nc} CPL refs, gerbers sane)")
    print()


if __name__ == "__main__":
    main()
