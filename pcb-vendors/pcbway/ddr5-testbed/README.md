# ddr5-testbed — PCBWay package

DDR5 SO-DIMM-module testbed.
Source: `antmicro/ddr5-testbed` @ `5db928c` (local clone, unmodified).

## Contents

| Path | Purpose |
|---|---|
| `gerbers/` | Gerber X2 (Protel extensions) + Excellon drill `PTH.drl` / `NPTH.drl` (mm) + drill maps + `drill-report.txt` |
| `bom/ddr5-testbed.csv` | generic BOM, 62 placements / 18 unique parts |
| `cpl/ddr5-testbed-{top,bottom}.csv` | generic pick & place, mm |

**Vendor package** (self-contained, upload this): `../../pcb-vendors/pcbway/ddr5-testbed/`
— gerber copy + PCBWay BOM XLSX + positions CSV + this README.

## PCB order spec

- Size 69.6 × 30.0 mm (SO-DIMM DDR4 module form factor), **4 layers**
- Thickness: design stackup is **1.258 mm**; closest standard is **1.2 mm**
  (0.058 mm thinner). Acceptable for SODIMM-slot mating, but be aware of it.
- **Gold fingers required**: hard gold on the card edge (≥ 30 µin). Plain ENIG
  will not survive repeated mating.
- Upload: zip the whole `gerbers/` directory.

## Assembly notes

- **Consigned:** `U1` — Micron **MT60B2G8HB-48B:A** DDR5 (flagged in BOM
  `Sourcing` column).
- Rows `N1/N2` (net ties) and `TP1–TP3` marked `no physical part - do not order`.

## Ordering at PCBWay

1. Quote at pcbway.com, upload the `gerbers/` zip. Set: 4 layers,
   thickness **1.2 mm** (design stackup is 1.258 mm — closest standard),
   size 69.6 × 30 mm, surface finish **Gold Fingers (hard gold, ≥ 30 µin)**,
   and add edge beveling if offered.
2. Add the assembly service and choose **partial turnkey**: upload
   `../../pcb-vendors/pcbway/ddr5-testbed/ddr5-testbed-bom.xlsx` and
   `../../pcb-vendors/pcbway/ddr5-testbed/ddr5-testbed-positions.csv`.
   their sourcing team buys the BOM MPNs from normal distribution.
3. Set `U1` (Micron DDR5) to **consigned** ("Kitted or Consigned" option):
   ship the DRAMs to the address PCBWay gives with your order number, per
   their kitting checklist.
4. Verify component rotations in the DFM review they send back before
   production.

Regenerate: `python3 ../../../scripts/build_vendor_packages.py --board ddr5-testbed`
