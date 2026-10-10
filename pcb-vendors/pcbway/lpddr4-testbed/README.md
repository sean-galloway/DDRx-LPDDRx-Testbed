# lpddr4-testbed — PCBWay package

LPDDR4 SO-DIMM-module testbed (single 200-ball WFBGA LPDDR4 breakout).
Source: `antmicro/lpddr4-testbed` @ `93e67cf` (local clone, unmodified).

## Contents

| Path | Purpose |
|---|---|
| `gerbers/` | Gerber X2 (Protel extensions) + Excellon drill `PTH.drl` / `NPTH.drl` (mm) + drill maps + `drill-report.txt` |
| `bom/lpddr4-testbed.csv` | generic BOM, 61 placements / 13 unique parts |
| `cpl/lpddr4-testbed-{top,bottom}.csv` | generic pick & place, mm |

**Vendor package** (self-contained, upload this): `../../pcb-vendors/pcbway/lpddr4-testbed/`
— gerber copy + PCBWay BOM XLSX + positions CSV + this README, bundled as one upload zip (`lpddr4-testbed.zip`).

## PCB order spec

- Size 69.6 × 30.0 mm (SO-DIMM DDR4 module form factor), **4 layers**, thickness **1.6 mm**
- **Gold fingers required**: the card-edge SO-DIMM connector needs hard gold
  (≥ 30 µin). Plain ENIG will wear out from repeated module swapping.
- Upload: zip the whole `gerbers/` directory.

## Assembly notes

- **Consigned:** `U1` — Micron **MT53E1G32D2NP-046 WT:A** LPDDR4, BGA-200
  (flagged in BOM `Sourcing` column).
- `TP1`–`TP3` are bare test pads — excluded from the BOM and positions files
  (no parts to place).
- Antmicro sources the passives/ICs (Yageo/Murata/Walsin/Panasonic/Kingbright/
  NXP/Atmel/TI) outside JLCPCB's catalog — PCBWay's partial-turnkey sourcing
  buys the exact MPNs from normal distribution instead.

## Ordering at PCBWay

1. Quote at pcbway.com, upload the `gerbers/` zip. Set: 4 layers, 1.6 mm,
   size 69.6 × 30 mm, surface finish **Gold Fingers (hard gold, ≥ 30 µin)**,
   and add edge beveling if offered.
2. Add the assembly service and choose **partial turnkey**: upload
   `../../pcb-vendors/pcbway/lpddr4-testbed/lpddr4-testbed-bom.xlsx` and
   `../../pcb-vendors/pcbway/lpddr4-testbed/lpddr4-testbed-positions.csv`.
3. Set `U1` (Micron LPDDR4) to **consigned** ("Kitted or Consigned" option):
   ship the DRAMs to the address PCBWay gives with your order number, per
   their kitting checklist (they require spares).
4. Verify component rotations in the DFM review they send back before
   production.

Regenerate: `python3 ../../../scripts/build_vendor_packages.py --board lpddr4-testbed`
