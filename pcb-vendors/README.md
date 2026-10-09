# PCB vendor manufacturing packages

One directory per board to fabricate. Everything the fab needs is inside each
board directory: `gerbers/` (zip and upload as the PCB file), `bom/` + `cpl/`
(for SMT assembly), and a `README.md` with the order-time choices (surface
finish, gold fingers, thickness) that can't be embedded in the files.

| Board | Chosen house | Size | Layers | Thickness | Finish | Source repo @ rev |
|---|---|---|---|---|---|---|
| [lpddr4-test-board](../references/lpddr4-test-board/) | **MacroFab** | 110 × 90 mm | 4 | 1.6 mm | ENIG | antmicro/lpddr4-test-board @ 5c8b5d3 |
| [lpddr4-testbed](../references/lpddr4-testbed/) | **PCBWay** | 69.6 × 30 mm | 4 | 1.6 mm | hard gold fingers | antmicro/lpddr4-testbed @ 93e67cf |
| [ddr5-testbed](../references/ddr5-testbed/) | **PCBWay** | 69.6 × 30 mm | 4 | 1.258 mm (→ PCBWay 1.2 mm) | hard gold fingers | antmicro/ddr5-testbed @ 5db928c |

MacroFab and PCBWay were chosen over JLCPCB because their sourcing is not
tied to the captive LCSC catalog (they buy exact BOM MPNs from normal
distribution) and both handle consigned parts cleanly — the mainboard FPGA and
the testbed DRAMs are consigned in either flow.

## Layout

- `references/<board>/` (repo root) — canonical per-board outputs: `gerbers/`,
  generic `bom/` + `cpl/`, and the board README with order specs. Everything
  in here is regenerated from the source repos.
- `<vendor>/<board>/` — **self-contained vendor package**: a gerber copy plus
  that vendor's BOM/position formats and the board README. This is what you
  upload; zip the vendor board directory and send it.

```
pcb-vendors/
├── macrofab/lpddr4-test-board/     ← upload to MacroFab
├── pcbway/lpddr4-testbed/          ← upload to PCBWay
├── pcbway/ddr5-testbed/            ← upload to PCBWay
└── match_report.csv, lcsc_map.json, README.md

references/
├── lpddr4-test-board/  lpddr4-testbed/  ddr5-testbed/
```

## Regenerating

Requires KiCad 10 (`kicad-cli`) on PATH and the board clones in the sibling
`../` directory:

```sh
python3 scripts/build_vendor_packages.py            # gerbers + BOM + CPL + verify, all boards
python3 scripts/build_vendor_packages.py --board ddr5-testbed --step bom
```

Then, to refresh LCSC part-number matches (optional; requires the jlcparts
cache DB — see `scripts/match_lcsc.py` docstring for how to fetch it):

```sh
python3 scripts/match_lcsc.py              # writes lcsc_map.json + match_report.csv
python3 scripts/build_vendor_packages.py --step bom # merge matches into the BOMs
```

## Part-matching reality check

Antmicro designs use European-sourced parts; most are **not** in JLCPCB's SMT
assembly catalog. `match_report.csv` shows the result of exact-MPN matching
against a 1.8M-part JLCPCB snapshot: only a handful of lines pre-match. That
is expected — at order time the assembler's BOM tool suggests in-catalog substitutes
per line, or parts can be consigned. Lines that must be consigned (the
Kintex-7 FPGA on the mainboard, the Micron DRAMs on the testbeds) are flagged
in each BOM's `Sourcing` column.
