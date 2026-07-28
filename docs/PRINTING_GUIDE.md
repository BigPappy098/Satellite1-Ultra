# Printing Guide

`VERIFIED_DIGITALLY` for part geometry, stored 3MF units, and bounding boxes.
Actual print time, material use, shrinkage, warping, and airtightness are
`REQUIRES_PHYSICAL_VALIDATION`.

## Authoritative slicer baseline

- ASA primary; PETG alternative. Do not mix materials within a bolted joint.
- 0.4 mm nozzle; 0.20 mm layer; 0.45 mm line width.
- Five walls; six top and six bottom layers; 35% gyroid.
- ASA: 250-260 C nozzle, 100-110 C bed, enclosed printer, low part cooling,
  draft shield if chamber is below 40 C.
- PETG: 235-250 C nozzle, 75-85 C bed, moderate cooling after layer three.
- Supports: disabled. The horizontal acoustic openings are self-progressing
  circular overhangs; inspect their upper arcs and never place support on a
  gasket seat.
- Seam: rear (+Y) for cabinet/shell/shroud; away from all gasket lands.
- Elephant-foot compensation: set in the slicer from your coupon, not by
  sanding the part.

## Print order and exact orientation

| Group | Filename | Qty | Material | Face/orientation | Supports | Brim | Difficulty | Calibration |
|---|---|---|---|---|---|---|---|---|
| cosmetic | anti_slip_ring.3mf | 1 | TPU 95A | flat | none | none | 2/5 | yes |
| cosmetic | outer_shell.3mf | 1 | ASA | upright, base band on the bed | none | 10 mm | 5/5 | yes |
| structural | main_cabinet.3mf | 1 | ASA | upright, acoustic floor on bed | none | 10 mm | 4/5 | yes |
| structural | pressure_divider.3mf | 1 | ASA | flat, acoustic face on bed | none | none | 2/5 | yes |
| cosmetic | electronics_shroud.3mf | 1 | ASA | wide divider end on bed | none | none | 2/5 | yes |
| structural | active_driver_clamp_ring.3mf | 1 | ASA | lip face on bed | none | none | 2/5 | yes |
| structural | passive_radiator_clamp_ring.3mf | 2 | ASA | lip face on bed | none | none | 2/5 | yes |
| calibration | cable_gland.3mf | 1 | TPU 95A | body end on bed | none | 5 mm | 2/5 | first |
| service tool | leak_test_adapter.3mf | 1 | TPU 95A | flange on bed; temporary service tool, not installed in service | none | none | 2/5 | yes |
| structural | base_skirt.3mf | 1 | ASA | service opening on bed | none | none | 2/5 | yes |
| structural | bottom_service_plate.3mf | 1 | ASA | exterior face on bed | none | none | 2/5 | yes |
| structural | ballast_cartridge.3mf | 1 | ASA | tray floor on bed | none | none | 2/5 | yes |
| structural | ballast_cartridge_lid.3mf | 1 | ASA | tongue face on bed | none | none | 2/5 | yes |
| calibration | coupon_official_interface.3mf | 1 | ASA | largest flat face on bed | none | 5 mm | 2/5 | first |
| calibration | coupon_active_driver.3mf | 1 | ASA | largest flat face on bed | none | 5 mm | 2/5 | first |
| calibration | coupon_passive_radiator.3mf | 1 | ASA | largest flat face on bed | none | 5 mm | 2/5 | first |
| calibration | coupon_heat_set_insert.3mf | 1 | ASA | largest flat face on bed | none | 5 mm | 2/5 | first |
| calibration | coupon_gasket_base.3mf | 1 | ASA | largest flat face on bed | none | 5 mm | 2/5 | first |
| calibration | coupon_gasket_cap.3mf | 1 | ASA | largest flat face on bed | none | 5 mm | 2/5 | first |
| calibration | coupon_cable_passage.3mf | 1 | ASA | largest flat face on bed | none | 5 mm | 2/5 | first |

The 3MF files already store millimetres and the documented orientation.

## CAD-derived orientation sheets

![anti_slip_ring print orientation](IMAGES/print_orientation_anti_slip_ring.png)

![outer_shell print orientation](IMAGES/print_orientation_outer_shell.png)

![main_cabinet print orientation](IMAGES/print_orientation_main_cabinet.png)

![pressure_divider print orientation](IMAGES/print_orientation_pressure_divider.png)

![electronics_shroud print orientation](IMAGES/print_orientation_electronics_shroud.png)

![active_driver_clamp_ring print orientation](IMAGES/print_orientation_active_driver_clamp_ring.png)

![passive_radiator_clamp_ring print orientation](IMAGES/print_orientation_passive_radiator_clamp_ring.png)

![cable_gland print orientation](IMAGES/print_orientation_cable_gland.png)

![leak_test_adapter print orientation](IMAGES/print_orientation_leak_test_adapter.png)

![base_skirt print orientation](IMAGES/print_orientation_base_skirt.png)

![bottom_service_plate print orientation](IMAGES/print_orientation_bottom_service_plate.png)

![ballast_cartridge print orientation](IMAGES/print_orientation_ballast_cartridge.png)

![ballast_cartridge_lid print orientation](IMAGES/print_orientation_ballast_cartridge_lid.png)

![coupon_official_interface print orientation](IMAGES/print_orientation_coupon_official_interface.png)

![coupon_active_driver print orientation](IMAGES/print_orientation_coupon_active_driver.png)

![coupon_passive_radiator print orientation](IMAGES/print_orientation_coupon_passive_radiator.png)

![coupon_heat_set_insert print orientation](IMAGES/print_orientation_coupon_heat_set_insert.png)

![coupon_gasket_base print orientation](IMAGES/print_orientation_coupon_gasket_base.png)

![coupon_gasket_cap print orientation](IMAGES/print_orientation_coupon_gasket_cap.png)

![coupon_cable_passage print orientation](IMAGES/print_orientation_coupon_cable_passage.png)

## Inspection before continuing

- Cabinet and divider: continuous, glossy-enough gasket lands; no seam gap,
  crack, under-extrusion, or insert bore opened into the chamber.
- Shell: all slots open, four retention bridges intact, no warp at either rim.
- Clamp rings: flat within 0.20 mm on a surface plate; lip clean and continuous.
- Ballast cartridge: lid holes align; both plates lie flat; four bosses sound.
- TPU parts: no tear, string in a wire bore, or layer split.

Approximate filament and time vary too much by slicer and machine to be
verified digitally. Your slicer estimate is authoritative for planning; record
it before starting each full-size print.
