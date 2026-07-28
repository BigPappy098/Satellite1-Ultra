# Hardware and Materials Guide

Use Batch 1 only. The public Batch 1 pair is Core rev4.1 plus HAT rev4.1 /
R2024.12.06. If the board or packaging says Satellite1.1, rev5.1 Core, rev6.1
HAT, or requires an external Wi-Fi antenna, stop: that hardware is unsupported.

| ID | Category | Item | Exact specification | Qty | Required |
|---|---|---|---|---|---|
| A01 | active driver | Dayton Audio ND91-4 | 4 ohm full-range driver; manufacturer model ND91-4 | 1 | yes |
| A02 | passive radiator | SB Acoustics SB12PACR-00 | 4 inch aluminum passive radiator with M6 mass post | 2 | yes |
| E01 | official electronics | FutureProofHomes Satellite1 Batch 1 development kit | Core rev4.1 + HAT rev4.1 / R2024.12.06; not Satellite1.1 | 1 | yes |
| H01 | insert | CNC Kitchen M3 x 5.7 heat-set insert | M3x0.5 internal thread, 5.7 mm length, 4.6 mm maximum OD | 48 | yes; includes four spares |
| H02 | speaker cable | 2-pin JST-XH 2.54 mm speaker lead | 22 AWG stranded red/black, each insulated conductor OD <=1.8 mm, 350 mm minimum | 1 | yes |
| H03 | speaker terminals | 2.8 mm fully insulated female quick-disconnects | for 22-18 AWG wire; verify fit on the purchased ND91-4 before crimping | 2 | recommended; direct solder is acceptable |
| B01 | ballast | mild-steel plate | 110 x 122 x 5 mm, edges deburred, dry, light oil removed | 2 | yes |
| B02 | radiator tuning | M6 stainless flat washers | identical stacks totaling 0.78 g per radiator | 2 matched stacks | yes; final mass requires physical tuning |
| G00 | gasket stock | closed-cell EPDM foam sheet | 2.0 mm nominal, soft, smooth skin, ASTM D1056 2A1 or equivalent | one 300 x 300 mm sheet | yes |
| D01 | optional acoustic material | polyester acoustic batting | not installed in RC1; reserve for measurement-led development only | 0 | no |
| O01 | official printed part | official_mid_plate | ASA (PETG alternative); exact file OFFICIAL_PARTS/REQUIRED_SINGLE_MATERIAL/official_mid_plate.stl; preserved official STL | 1 | yes |
| O02 | official printed part | official_mid_plate_threads | ASA (PETG alternative); exact file OFFICIAL_PARTS/REQUIRED_SINGLE_MATERIAL/official_mid_plate_threads.stl; preserved official STL | 1 | yes |
| O03 | official printed part | official_pcb_spacer | ASA (PETG alternative); exact file OFFICIAL_PARTS/REQUIRED_SINGLE_MATERIAL/official_pcb_spacer.stl; preserved official STL | 1 | yes |
| O04 | official printed part | official_lock_ring | ASA (PETG alternative); exact file OFFICIAL_PARTS/REQUIRED_SINGLE_MATERIAL/official_lock_ring.stl; preserved official STL | 1 | yes |
| O05 | official printed part | official_top_plate | ASA (PETG alternative); exact file OFFICIAL_PARTS/REQUIRED_SINGLE_MATERIAL/official_top_plate.stl; preserved official STL | 1 | yes |
| O06 | official printed part | official_top_plate_snap_in_diffuser_ring | ASA (PETG alternative); exact file OFFICIAL_PARTS/REQUIRED_SINGLE_MATERIAL/official_top_plate_snap_in_diffuser_ring.stl; preserved official STL | 1 | yes |
| O07 | official printed part | official_top_plate_mm_buttons | ASA (PETG alternative); exact file OFFICIAL_PARTS/OPTIONAL_MULTI_MATERIAL/official_top_plate_mm_buttons.stl; preserved official STL | 1 | optional alternative |
| O08 | official printed part | official_top_plate_mm_diffuser_ring | ASA (PETG alternative); exact file OFFICIAL_PARTS/OPTIONAL_MULTI_MATERIAL/official_top_plate_mm_diffuser_ring.stl; preserved official STL | 1 | optional alternative |
| F01 | fastener | M3 x 6 socket cap screw | ISO 4762, A2-70 stainless, M3x0.5 | 4 | yes |
| F02 | fastener | M3 x 8 button head screw | ISO 7380-1, A2-70 stainless, M3x0.5 | 4 | yes |
| F03 | fastener | M3 x 10 socket cap screw | ISO 4762, A2-70 stainless, M3x0.5 | 8 | yes |
| F04 | fastener | M3 x 10 socket cap screw | ISO 4762, A2-70 stainless, M3x0.5 | 4 | yes |
| F05 | fastener | M3 x 10 socket cap screw | ISO 4762, A2-70 stainless, M3x0.5 | 8 | yes |
| F06 | fastener | M3 x 8 button head screw | ISO 7380-1, A2-70 stainless, M3x0.5 | 4 | yes |
| F07 | fastener | M3 x 10 socket cap screw | ISO 4762, A2-70 stainless, M3x0.5 | 4 | yes |
| F08 | fastener | M3 x 8 button head screw | ISO 7380-1, A2-70 stainless, M3x0.5 | 4 | yes |
| F09 | fastener | M3 x 8 button head screw | ISO 7380-1, A2-70 stainless, M3x0.5 | 4 | yes |
| F10 | fastener | M3 x 8 socket cap screw | ISO 4762, A2-70 stainless, M3x0.5 | 4 | yes |
| F11 | fastener | M3 x 8 socket cap screw | ISO 4762, A2-70 stainless, M3x0.5 | 4 | yes |

All purchasing availability and prices must be checked by the builder.
Manufacturer geometry and electrical parameters are
`DERIVED_FROM_MANUFACTURER_DRAWING`; supplier availability is an
`ENGINEERING_ESTIMATE`.

No structural glue is used. No damping material is installed in RC1. Gaskets
are replaceable mechanically compressed EPDM, and the cable seal is TPU 95A.
