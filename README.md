# Satellite1 Ultra

> **DO NOT PRINT THE FULL ENCLOSURE YET.**
> **PRINT AND COMPLETE THE CALIBRATION PARTS FIRST.**

Satellite1 Ultra is an editable CadQuery B-rep enclosure for the
FutureProofHomes Satellite1 **Batch 1** development kit: Core rev4.1 plus HAT
rev4.1 / R2024.12.06. Satellite1.1 / Batch 2 is not supported.

The current release state is `DIGITAL_PROTOTYPE_READY`, not physically
validated. Printed fit, sealing, acoustic output, thermals, Wi-Fi, microphones,
buttons, LEDs, and wake-word behavior are `REQUIRES_PHYSICAL_VALIDATION`.

## Builder entry point

Download the generated `release/Satellite1-Ultra-RC1.zip`, open
`00_READ_ME_FIRST.txt`, then follow
`BUILD_SATELLITE1_ULTRA_FOR_BEGINNERS.pdf` from top to bottom. Print only from
the three numbered folders under `PRINT_THESE_FILES/`. The release package
also contains:

- six task-oriented PDF guides;
- one calibration input template and eight calibration 3MF files;
- production STEP, STL, and correctly oriented 3MF files;
- all six required official Squircle upper-stack STL files, preserved
  byte-for-byte under `OFFICIAL_PARTS/REQUIRED_SINGLE_MATERIAL/`;
- 1:1 DXF gasket templates;
- BOM, fastener, and gasket schedules;
- CAD-derived calibration, printing, assembly, and service illustrations;
- SHA-256 checksums.

Print every required custom Ultra 3MF **and** every file in
`OFFICIAL_PARTS/REQUIRED_SINGLE_MATERIAL/`. Do not print the original official
speaker chamber, speaker plate, or anti-slip ring; the Ultra enclosure replaces
them.

The limiting print is `outer_shell.3mf` at 192 x 212 x 189 mm. The absolute
usable machine travel is therefore 212 x 192 x 189 mm (X/Y may be swapped);
220 x 220 x 200 mm is the practical minimum only if the full bed is usable; it
leaves room for a 3 mm shell brim. Purge lines, clips, or firmware exclusions
can require a larger bed.

## One-command clean build

Python 3.12 is required.

```text
make all
```

`make all` creates the isolated environment from the hash-locked dependencies,
then `make release` removes generated output, regenerates and validates every B-rep,
acoustic report, STEP/STL/3MF, render, drawing, guide, PDF, mutation report, and
release package. It fails when a required artifact is missing or stale.

After physically measuring the calibration parts:

```text
python scripts/calibrate.py
```

The wizard writes only `config/physical_calibration.yaml` and runs:

```text
make calibrated-release
```

## Authoritative definitions

- Parametric B-rep source: `src/satellite1_ultra/`
- Builder calibration: `config/physical_calibration.yaml`
- Component data: `config/components.yaml`
- Official unmodified assets: `reference-assets/official/`
- Official provenance and checksums: `reference-assets/MANIFEST.csv`
- Digital evidence: `reports/validation/` and `reports/acoustics/`
- Final audit and release state: `reports/FINAL_CODEX_AUDIT.md` and
  `reports/FINAL_RELEASE_STATUS.md`

## Master coordinate system

- origin: center of the official mid-plate interface plane, as measured from
  the preserved B-rep.
- +Z: toward the microphones.
- -Y: active-driver front.
- +/-X: opposed passive radiators.
- Units: millimetres everywhere.

STEP is the authoritative exchange format. STL and 3MF are derived mesh
outputs. Source geometry never uses mesh booleans, voxels, SDFs, or
marching-cubes.

## License

Project hardware geometry is CERN-OHL-S-2.0. Official and manufacturer
reference assets retain their original licenses and provenance as recorded in
`reference-assets/MANIFEST.csv`.
