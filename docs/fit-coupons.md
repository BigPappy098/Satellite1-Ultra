# Fit-coupon inspection sheet

All expected dimensions are `DERIVED_FROM_OFFICIAL_CAD` or
`DERIVED_FROM_MANUFACTURER_DRAWING`. Pass/fail limits are
`ENGINEERING_ESTIMATE`. Results are `REQUIRES_PHYSICAL_VALIDATION` until a
coupon is printed and measured.

## Common print setup

- Material: same ASA brand/color/dry condition intended for the cabinet
- Nozzle: 0.4 mm
- Layer height: 0.20 mm
- Line width: 0.45 mm
- Walls: 5
- Top/bottom layers: 6
- Infill: 35% gyroid
- Scale: 100%; do not tune slicer XY compensation between coupons
- Orientation: exported 3MF orientation, largest flat face on the bed
- Conditioning: cool to room temperature for at least two hours before
  measurement
- Measurement tool: calibrated 0.01 mm digital caliper; use pin gauges for
  insert bores where available

## Inspection

| Coupon | Critical checks | Expected | Pass criteria | Compensation input |
|---|---|---:|---:|---|
| Official interface | Four hole centers; 110.6 mm recess; official mid-plate drop fit | X ±45.0534, Y ±31.5467 mm; 110.6 mm | Hole-center error ≤0.20 mm; mid-plate seats without force and radial shake ≤0.40 mm | `xy_scale_correction_fraction`, `hole_diameter_offset` |
| Active driver | Seat Ø, bore Ø, seat depth, clamp bolt circle, insert bores | seat Ø103.8; bore Ø88.7; seat depth 5.50; BCD 112.0 | Driver flange drops into the seat without force; the clamp ring bottoms on the coupon face while loading the flange; all four M3 screws enter freely | `hole_diameter_offset`, `xy_scale_correction_fraction`, `insert_hole_diameter_offset` |
| Active-driver flange thickness | Measure the driver's actual flange thickness | 3.00 mm assumed | Enter the measured value in `config/components.yaml`; it sets the seat depth | `components.yaml: flange_thickness_mm` |
| Passive radiator | Ledge Ø, seat Ø, bore Ø, seat depth, clamp bolt circle | ledge Ø140.6 x 5.00; seat Ø122.6; bore Ø102.2; seat depth 11.50; BCD 130.0 | Radiator flange drops into the seat without force; the clamp ring bottoms on the ledge while loading the flange | `hole_diameter_offset`, `xy_scale_correction_fraction` |
| Radiator flange thickness | Measure the radiator's actual flange thickness | 4.00 mm assumed | Enter the measured value in `config/components.yaml` | `components.yaml: flange_thickness_mm` |
| Heat-set insert | Four blind bores | Ø4.0/4.1/4.2/4.3 x 7.2 mm for a Ø4.6 M3 insert | Select the smallest bore that accepts the insert flush without cracking, then pull-test to 250 N | `insert_hole_diameter_offset` |
| Gasket compression | 2.0 mm EPDM sample between stops | 1.50 mm assembled | 1.45–1.55 mm immediately; ≥1.40 mm after 24 h; no extrusion into opening | `gasket_groove_depth_offset` |
| Cable passage | TPU gland in divider-thickness plate | Ø8.0 hole; Ø8.3 gland body | Gland installs without tearing; wires resist 20 N pull; leak test passes | `cable_passage_offset` |

The official threaded mid-plate and lock ring are **not** coupon-tested here.
This design does not reproduce that interface: those parts are printed from
the unmodified official files, so their thread fit belongs to the official
geometry. The interface this project derives is the official four-point mount,
which the official-interface coupon covers.

## Feedback procedure

Enter measured corrections only in `config/physical_compensation.yaml`. Positive
hole compensation enlarges holes; positive external compensation enlarges
outside dimensions. Regenerate all CAD and rerun geometry/export validation
after any change. Do not compensate the official reference files themselves.

The full enclosure should not be printed until all coupons pass. A digital pass
does not replace this gate.
