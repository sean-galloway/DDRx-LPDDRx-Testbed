# lpddr4-test-board — MacroFab package

Kintex-7 (AMD-Xilinx XC7K70T) LPDDR4 test mainboard.
Source: `antmicro/lpddr4-test-board` @ `5c8b5d3` (local clone, unmodified).

## Contents

| Path | Purpose |
|---|---|
| `gerbers/` | Gerber X2 (Protel extensions) + Excellon drill `PTH.drl` / `NPTH.drl` (mm) + drill maps + `drill-report.txt` |
| `bom/lpddr4-test-board.csv` | generic BOM (JLCPCB-style columns), 416 placements / 83 unique parts |
| `cpl/lpddr4-test-board-{top,bottom}.csv` | generic pick & place, mm |

**Vendor package** (self-contained, upload this): `../../pcb-vendors/macrofab/lpddr4-test-board/`
— gerber copy + MacroFab BOM CSV + single-file positions + this README.

## PCB order spec

- Size 110.0 × 90.0 mm, **4 layers**, thickness **1.6 mm**
- **Blind vias required** (BGA fanout): 0.20 mm drills, two spans —
  F.Cu→In1.GND (49 holes) and F.Cu→In2.Cu (114 holes). See the separate
  `front-in1.drl` / `front-in2.drl` in `gerbers/`. A plain through-via build
  cannot reproduce this board; make sure blind vias are enabled in the quote
  (MacroFab supports them; standard JLCPCB does not — another reason this
  board goes to MacroFab).
- Surface finish: **ENIG** (0.8 mm-pitch BGA; do not use plain HASL)
- No fiducials in the design — the assembler adds their own for assembly

## Assembly notes

- **Consigned:** `U3` — AMD-Xilinx **XC7K70T-1FBG484C** BGA-484 FPGA (flagged in BOM
  `Sourcing` column). Buy from DigiKey/Mouser and ship to the consignment
  address MacroFab assigns at order time.
- Rows marked `no physical part - do not order` (test points TP1–TP20, net tie
  N2) are intentionally unmatched — mark them do-not-place in the MacroFab BOM
  review.
- After uploading positions, verify component rotations in their viewer
  (KiCad vs house rotation conventions differ for some footprints).

## Ordering at MacroFab

1. Create a project at macrofab.com, upload the `gerbers/` zip. Set: 4 layers,
   1.6 mm, ENIG, 110 × 90 mm.
2. Add assembly; upload `../../pcb-vendors/macrofab/lpddr4-test-board/lpddr4-test-board-bom.csv` and
   `../../pcb-vendors/macrofab/lpddr4-test-board/lpddr4-test-board-positions.csv`. Confirm the
   column mapping in their importer (Designator / Manufacturer / MPN / Quantity
   for the BOM; Designator / Mid X / Mid Y / Rotation / Layer for positions).
3. Part sourcing: most MPNs resolve against DigiKey/Mouser automatically.
   Set `U3` to **consigned** — MacroFab shows a per-work-order warehouse
   address; ship the FPGAs there labeled with the order number and meet the
   per-part overage they list. Review any form-fit-function substitutions they
   propose before approving.
4. Review the first-article photos before authorizing the full run.

Regenerate: `python3 ../../../scripts/build_vendor_packages.py --board lpddr4-test-board`
(re-run `--step bom` after `scripts/match_lcsc.py` to refresh LCSC matches)
