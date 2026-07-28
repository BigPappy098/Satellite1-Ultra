# Start Here - Satellite1 Ultra

> **DO NOT PRINT THE FULL ENCLOSURE YET.**
> **PRINT AND COMPLETE THE CALIBRATION PARTS FIRST.**

For the simplest instructions, open
`BUILD_SATELLITE1_ULTRA_FOR_BEGINNERS.pdf` and follow it from top to bottom.
It tells you which folder to open, which file to print, how many copies to
make, and what to do next. The other manuals provide extra detail when that
guide sends you to them.

Satellite1 Ultra is a serviceable passive-radiator enclosure for the
FutureProofHomes Satellite1 **Batch 1** development kit: Core rev4.1 and HAT
rev4.1 / R2024.12.06. Satellite1.1 / Batch 2 is not supported.

Status: `DIGITAL_PROTOTYPE_READY` only after every digital gate passes.
No physical specimen has been validated. Fit, sealing, acoustics, thermals,
Wi-Fi, microphones, buttons, LEDs, and wake-word performance are
`REQUIRES_PHYSICAL_VALIDATION`.

## You need

- An enclosed printer with at least **212 x 192 x 189 mm of genuinely usable
  travel** (X/Y may be swapped). A 220 x 220 x 200 mm printer is the practical
  minimum; the 192 x 212 x 189 mm outer shell is the limiting part.
- 0.4 mm nozzle, dry ASA, TPU 95A, and a documented PETG alternative.
- Digital calipers (0.01 mm display), 0.01 g scale, 2.0 mm hex driver, M3
  insert tip, wire tools, ESD protection, and basic acoustic test equipment.
- Everything in `BOM.csv`, `FASTENERS.csv`, and `GASKETS.csv`.

## Exact order

1. Read `START_HERE_CALIBRATION_GUIDE.pdf`.
2. Print seven coupon files plus `cable_gland.3mf`.
3. Measure, edit `CALIBRATION_INPUT_TEMPLATE.yaml`, and run
   `make calibrated-release`.
4. Reprint affected coupons and pass every calibration check.
5. Print **both** groups in `PRINTING_GUIDE.pdf`: every required custom Ultra
   3MF and all six official Squircle STL files.
6. Follow `ASSEMBLY_GUIDE.pdf`.
7. Complete `TESTING_AND_COMMISSIONING_GUIDE.pdf` before normal use.

The project is advanced: expected builder difficulty is 4/5. Allow several
days for printing plus calibration and test time.

![Exploded Satellite1 Ultra](IMAGES/exploded_parts_identification.png)
