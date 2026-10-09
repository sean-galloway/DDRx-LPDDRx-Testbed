# DDRx / LPDDRx Testbed Project

Umbrella repo for building Antmicro-compatible memory testbeds (see NOTES.md
in the parent workspace for the full project context).

**Ultimate goal:** testbeds for every standard in the DDR2/LPDDR2 → DDR5/LPDDR5
span — filling in the missing ones (DDR2/LPDDR2, DDR3/LPDDR3, DDR4/LPDDR4 as
needed) alongside the DDR5 and LPDDR4 boards below.

Currently this repo collects the **PCB vendor manufacturing packages** for the
three Antmicro reference boards we are having made:

- `lpddr4-test-board` — Kintex-7 LPDDR4 test mainboard
- `lpddr4-testbed` — LPDDR4 SO-DIMM-module testbed
- `ddr5-testbed` — DDR5 SO-DIMM-module testbed

See [pcb-vendors/README.md](pcb-vendors/README.md) for the package layout, order specs,
and how to regenerate everything with `scripts/build_vendor_packages.py`.

Future work (design files will live here): testbed modules for the remaining
standards in the span above — DDR2/LPDDR2/DDR3/LPDDR3/DDR4/LPDDR5; see NOTES.md bring-up plan.
