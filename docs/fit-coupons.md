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
| Threaded/locking interface | Engage official threaded mid-plate/lock system through full travel | Exact official B-rep | Hand engagement without cross-binding; no visible layer damage; rotational play ≤1° | `threaded_interface_radial_offset` |
| Active driver | Cutout, bolt circle, frame seat | Ø88.5; BCD 93.3; frame Ø103.2 mm | Cutout +0.20/+0.50; every M3 screw enters freely; frame rock <0.20 mm | `hole_diameter_offset`, `xy_scale_correction_fraction` |
| Passive radiator | Cutout, bolt circle, frame seat | Ø102.0; BCD 111.5; frame Ø122.0 mm | Cutout +0.20/+0.50; every screw enters freely; frame rock <0.20 mm | `hole_diameter_offset`, `xy_scale_correction_fraction` |
| Heat-set insert | Four blind bores | Ø4.4/4.5/4.6/4.7 x 6.5 mm | Select smallest bore accepting insert without cracking or pullout at 250 N | `insert_hole_diameter_offset` |
| Gasket compression | 2.0 mm EPDM sample between stops | 1.50 mm assembled | 1.45–1.55 mm immediately; ≥1.40 mm after 24 h; no extrusion into opening | `gasket_groove_depth_offset` |
| Cable passage | TPU gland in divider-thickness plate | Ø8.0 hole; Ø8.3 gland body | Gland installs without tearing; wires resist 20 N pull; leak test passes | `cable_passage_offset` |

## Feedback procedure

Enter measured corrections only in `config/physical_compensation.yaml`. Positive
hole compensation enlarges holes; positive external compensation enlarges
outside dimensions. Regenerate all CAD and rerun geometry/export validation
after any change. Do not compensate the official reference files themselves.

The full enclosure should not be printed until all coupons pass. A digital pass
does not replace this gate.
