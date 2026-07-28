# Mandatory Physical Calibration Guide

> **DO NOT PRINT THE FULL ENCLOSURE YET.**
> **PRINT AND COMPLETE THE CALIBRATION PARTS FIRST.**

Use the same material, nozzle, layer height, wall count, extrusion settings,
bed preparation, and chamber temperature that you will use for the enclosure.

## Print first

Print these exact files from `CALIBRATION_PARTS/`:

1. `coupon_official_interface.3mf`
2. `coupon_heat_set_insert.3mf`
3. `coupon_active_driver.3mf`
4. `coupon_passive_radiator.3mf`
5. `coupon_gasket_base.3mf`
6. `coupon_gasket_cap.3mf`
7. `coupon_cable_passage.3mf`
8. `cable_gland.3mf` in TPU 95A

ASA baseline: 0.4 mm nozzle, 0.20 mm layers, five walls, six top/bottom
layers, 35% gyroid, 100-110 C bed, 250-260 C nozzle, enclosure closed, no
supports, 5 mm brim. PETG alternative: 235-250 C nozzle, 75-85 C bed,
three-hour dry cycle if stringing is present.

## Measure and enter values

Use the engraved labels and `IMAGES/calibration_*.png`.

| Check | Where/how | Nominal | Pass | Input key |
|---|---|---:|---|---|
| XY scale | Inside jaws across `MEASURE XY 110.60` recess, three heights | 110.60 mm | 110.40-110.80 mm after correction | `xy_scale_correction_fraction = 110.60 / measured - 1` |
| Z scale | Outside jaws across clean 3.00 mm coupon edge, four corners | 3.00 mm | 2.90-3.10 mm | `z_scale_correction_fraction = 3.00 / measured - 1` |
| M3 clearance | Try a clean ISO M3 screw in labeled 3.4/3.5/3.6 holes | 3.4 mm | smallest hole that falls through without force | chosen diameter minus 3.4 |
| Insert bore | Install identical inserts in 4.0/4.1/4.2/4.3 blind bores | 4.2 mm | square, flush, no crack/spin at 0.35 N m | chosen diameter minus 4.2 |
| Driver fit | Seat the purchased ND91-4 in the labeled coupon | catalog interface | drops in by hand, <=0.30 mm radial play, flange lies flat | cutout correction and measured flange thickness |
| Radiator fit | Seat one SB12PACR-00 in the labeled coupon | catalog interface | drops in by hand, <=0.30 mm radial play, flange lies flat | cutout correction and measured flange thickness |
| Gasket | Tighten cap on a strip of the actual sheet until both stops contact | 2.00 to 1.50 mm | 15%-45% compression; no open light path | sheet thickness and compressed-thickness offset |
| Cable gland | Fit actual two 22 AWG conductors and gland in cable coupon | 8.0 mm passage | moderate finger force; gland cannot rotate or lift | cable-passage offset |

Do not use caliper tips to measure a 3-4 mm hole; the screw and insert are the
functional gauges. Enter only values you measured.

## CAD measurement illustrations

![Official-interface XY and Z measurement](IMAGES/calibration_official_interface.png)

![M3 screw and insert functional gauges](IMAGES/calibration_fasteners.png)

![Active-driver coupon fit check](IMAGES/calibration_driver.png)

![Passive-radiator coupon fit check](IMAGES/calibration_radiator.png)

![Gasket compression coupon stack](IMAGES/calibration_gasket.png)

![Cable passage and TPU gland check](IMAGES/calibration_cable.png)

## Edit one file

Copy `CALIBRATION_INPUT_TEMPLATE.yaml` to
`config/physical_calibration.yaml`, or run:

```text
python scripts/calibrate.py
```

The file exposes only user-facing corrections. Safe limits reject implausible
values before any full part is built.

## Regenerate

```text
make calibrated-release
```

Success ends with all validation, documentation, mutation, and package checks
passing. Output is in `release/Satellite1-Ultra-RC1/`.

Example successful finish:

```text
documentation PASS; 9 guides, 7 PDFs
release/Satellite1-Ultra-RC1 (all required files present)
```

Reprint every coupon affected by a nonzero correction. You are cleared for the
full enclosure only when all eight checks above pass on the corrected coupons.

## Common failures

- Warped official coupon: improve enclosure temperature, clean the bed, add the
  brim, and do not compensate a warped part.
- Every hole undersized: check flow and elephant-foot compensation before
  adding a large CAD offset.
- Insert cracks the boss: choose a larger coupon bore or reduce iron dwell; do
  not increase torque.
- Component will not sit flat: remove only print strings. Do not sand a sealing
  land; correct the cutout and reprint the coupon.
- Gland leaks or spins: verify conductor OD <=1.8 mm, dry TPU, then correct and
  reprint both the coupon and gland.
