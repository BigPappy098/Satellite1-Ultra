# Start Here - Satellite1 Ultra

> **DO NOT PRINT THE FULL ENCLOSURE YET.**
> **PRINT AND COMPLETE THE CALIBRATION PARTS FIRST.**

Satellite1 Ultra is a serviceable passive-radiator enclosure for the
FutureProofHomes Satellite1 **Batch 1** development kit: Core rev4.1 and HAT
rev4.1 / R2024.12.06. Satellite1.1 / Batch 2 is not supported.

Status: `DIGITAL_PROTOTYPE_READY` only after every digital gate passes.
No physical specimen has been validated. Fit, sealing, acoustics, thermals,
Wi-Fi, microphones, buttons, LEDs, and wake-word performance are
`REQUIRES_PHYSICAL_VALIDATION`.

## You need

- An enclosed 256 x 256 x 256 mm or larger FDM printer capable of ASA.
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
5. Follow `PRINTING_GUIDE.pdf`, then `ASSEMBLY_GUIDE.pdf`.
6. Complete `TESTING_AND_COMMISSIONING_GUIDE.pdf` before normal use.

The project is advanced: expected builder difficulty is 4/5. Allow several
days for printing plus calibration and test time.

![Exploded Satellite1 Ultra](IMAGES/exploded_parts_identification.png)
