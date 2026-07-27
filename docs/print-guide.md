# Printing guide

`VERIFIED_DIGITALLY` for geometry and orientation. Everything about how a specific printer behaves is `REQUIRES_PHYSICAL_VALIDATION`.

## Do the coupons first

Print and measure the eight fit coupons before any full-size part. Enter the results in `config/physical_compensation.yaml` and regenerate. See `docs/fit-coupons.md`.

## Process

- Primary material: ASA (alternative PETG)
- Nozzle 0.4 mm, layer 0.2 mm
- 5 walls, 6 top/bottom layers, 35% gyroid
- Heated chamber or a draught-free enclosure is required for ASA
- Do not enable any slicer XY compensation; the model carries its own

## Orientation and support

| Part | Qty | Material | Orientation | Bounds (mm) |
|---|---|---|---|---|
| anti_slip_ring | 1 | TPU 95A | flat | 188.0 x 208.0 x 2.0 |
| outer_shell | 1 | ASA | upright, base band on the bed | 192.0 x 212.0 x 189.0 |
| main_cabinet | 1 | ASA | upright, acoustic floor on bed | 160.0 x 180.0 x 162.5 |
| pressure_divider | 1 | ASA | flat, acoustic face on bed | 160.0 x 180.0 x 24.7 |
| electronics_shroud | 1 | ASA | wide divider end on bed | 185.0 x 205.0 x 30.5 |
| active_driver_clamp_ring | 1 | ASA | lip face up, flat on bed | 118.0 x 118.0 x 6.0 |
| passive_radiator_clamp_ring | 2 | ASA | lip face up, flat on bed | 140.0 x 140.0 x 6.0 |
| divider_gasket | 1 | 2 mm closed-cell EPDM | flat | 159.0 x 179.0 x 2.0 |
| driver_gasket | 1 | 2 mm closed-cell EPDM | flat | 103.8 x 103.8 x 2.0 |
| passive_radiator_gasket | 2 | 2 mm closed-cell EPDM | flat | 122.6 x 122.6 x 2.0 |
| cable_gland | 1 | TPU 95A | flange on bed | 14.0 x 13.6 x 5.5 |
| base_skirt | 1 | ASA | service opening on bed | 162.4 x 180.0 x 22.0 |
| bottom_service_plate | 1 | ASA | exterior face on bed | 151.4 x 171.4 x 4.0 |
| ballast_cartridge | 1 | ASA | tray floor on bed | 120.0 x 132.0 x 14.0 |
| ballast_cartridge_lid | 1 | ASA | outer face on bed | 120.0 x 132.0 x 3.5 |
| coupon_official_interface | 1 | ASA | largest flat face on bed | 120.0 x 120.0 x 3.0 |
| coupon_active_driver | 1 | ASA | largest flat face on bed | 126.0 x 126.0 x 10.2 |
| coupon_passive_radiator | 1 | ASA | largest flat face on bed | 144.0 x 144.0 x 15.2 |
| coupon_heat_set_insert | 1 | ASA | largest flat face on bed | 60.0 x 20.0 x 10.0 |
| coupon_gasket_base | 1 | ASA | largest flat face on bed | 60.0 x 30.0 x 9.5 |
| coupon_gasket_cap | 1 | ASA | largest flat face on bed | 60.0 x 30.0 x 3.0 |
| coupon_cable_passage | 1 | ASA | largest flat face on bed | 40.0 x 30.0 x 4.0 |

## Process notes

- The cabinet prints acoustic floor down: every gasket land and seat face is either horizontal or a vertical bore, so no sealing surface is a support interface.
- Component pockets are horizontal bores in a vertical wall; their upper 90 degrees bridge over a 0.3 mm-clearance arc and are not sealing surfaces.
- Clamp rings print lip-up so the loaded lip face is a top surface.
- Heat-set insert bores are blind and vertical or horizontal; none requires support.
- The grille cage prints upright on its bottom retention ring.

## Post-processing

- Install every heat-set insert with a temperature-controlled M3 tip, square to the boss. Do not torque a hot insert.
- Deburr the component seats and the divider rim land with a scraper; do not sand a gasket land, sanding rounds the edge and opens a leak path.
- Cut the EPDM seals from 2.0 mm sheet using the exported gasket profiles as templates.
