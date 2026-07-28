# Final release status

Status: **DIGITAL_PROTOTYPE_READY**

Nothing in this repository is `PHYSICALLY_VALIDATED`. The release is a
production-quality digital prototype and manufacturing package whose remaining
specimen-dependent claims are explicitly `REQUIRES_PHYSICAL_VALIDATION`.

## Release identity

| Item | Final value |
|---|---|
| Authoritative source commit | `0ae7c9bbf745f27bdfa5d2d6e62dcb2841d9c2c4` |
| Topic branch | `codex/include-complete-squircle-parts` |
| Supported electronics | Satellite1 Batch 1: Core rev4.1 and HAT rev4.1 / R2024.12.06 |
| Active driver | Dayton Audio ND91-4, one |
| Passive radiators | SB Acoustics SB12PACR-00, two |
| CAD-derived net acoustic volume | 3.517634704 L |
| Simulated target tuning | 60.0 Hz |
| Calculated added mass | 0.7818 g per passive radiator |
| Simulated f3 | 56.9 Hz |
| Recommended protection | Fourth-order 51 Hz high-pass |
| Release archive | `release/Satellite1-Ultra-RC1.zip` |
| Archive SHA-256 | `172f7b64442436e4c0bb7df12e6c7f09e9b4b02f6d67f273c83b6f041fddb1c8` |

The acoustic values above are `ENGINEERING_ESTIMATE`. Component geometry and
parameters are `DERIVED_FROM_MANUFACTURER_DRAWING`; they are not physical
measurements of a completed unit.

## Digital release evidence

| Gate | Result | Evidence |
|---|---:|---|
| Final fast suite | 120 passed | Zero failure, error, or skip; deep/mutation cases excluded by marker |
| Independent deep tests | 6 passed | Includes official release-copy hashes and independent Gmsh/OpenCascade STEP reopen |
| Mutation tests | 18 passed | Every deliberately injected defect was rejected, including changed export-source provenance |
| Official asset manifest | PASS | 126 preserved files rechecked against byte counts and SHA-256 |
| Manufactured B-reps | PASS | 23 valid, single-solid parts; each within 256 x 256 x 256 mm |
| Export validation | PASS | 23 STEP, 23 STL, and 23 3MF; STEP exact reopen; meshes watertight and single-component; 3MF units mm |
| Assembly exports | PASS | Functional, complete, and exploded STEP assemblies |
| Gasket templates | PASS | Three 1:1 DXF profiles generated from gasket B-reps |
| Quantitative validation | PASS | Acoustic volume, sealing, collision, clearance, Core fit, wall thickness, fasteners, tolerance, assembly, printability, and center of gravity |
| Documentation validation | PASS | Nine task guides and seven PDFs; all links, images, part names, BOM/fastener/gasket IDs, revisions, text extraction, and A4 page bounds checked |
| Visual PDF review | PASS | All 64 manual pages rendered to PNG and visually reviewed; the beginner guide, tables, images, clipping, and page flow pass |
| Release checksum verification | PASS | Every entry in `SOURCE_CHECKSUMS.txt` verifies |
| Clean one-command reproduction | PASS | Fresh clone and fresh virtual environment built with `make all` from the authoritative source commit |

Warnings emitted by CadQuery's pinned pyparsing compatibility layer are
upstream deprecation warnings, not skipped tests or release failures.

Reproduction here means equivalent validated B-rep/mesh geometry and complete
artifact generation, not a byte-identical archive. STL geometry hashes were
identical between the primary and clean-clone builds. OCCT STEP, 3MF/DXF
containers, ReportLab PDFs, and the final ZIP carry writer timestamps or other
non-geometric container metadata, so their byte hashes vary between builds.
`SOURCE_CHECKSUMS.txt` authenticates the specific published package.

## Release contents

The corrected user-facing package includes the complete printable product:

- `00_READ_ME_FIRST.txt` and a single plain-language beginner build guide;
- numbered `PRINT_THESE_FILES` folders that cover calibration, the complete
  Ultra enclosure, and all six mandatory Squircle top prints;
- one complete fastener schedule including F10/F11, the eight official M3 x 8
  upper-stack screws;
- seven illustrated PDF guides led by the beginner guide;
- `BOM.csv`, `FASTENERS.csv`, `GASKETS.csv`, and the calibration YAML template;
- 23 authoritative STEP part files and three assembly STEP files;
- printable STL and millimetre-unit 3MF manufacturing files;
- six mandatory unmodified official Squircle upper-stack STL files and two
  optional multi-material inserts in clearly separated folders;
- eight calibration print files;
- three gasket DXF templates;
- 62 current CAD-derived images;
- release notes and per-file SHA-256 checksums.

The mandatory first action is stated in the entry document: do not print the
full enclosure until the calibration coupons have passed and a calibrated
release has been regenerated.

The limiting print is the 192 x 212 x 189 mm outer shell. Absolute usable
machine travel is 212 x 192 x 189 mm (X/Y may be swapped). A fully usable
220 x 220 x 200 mm machine is the practical minimum and permits at most a 3 mm
shell brim; bed clips, purge lines, or firmware exclusions may require a larger
bed.

## Required physical gates

The following remain `REQUIRES_PHYSICAL_VALIDATION`:

1. Print the calibration set in the intended ASA/PETG process and enter measured
   compensation values.
2. Confirm the official Batch 1 Core stack placement and cable routing with the
   physical electronics.
3. Verify driver, radiator, insert, gasket, cable-gland, and threaded-interface
   fit on printed coupons before the full enclosure.
4. Verify insert pull-out, screw torque feel, gasket compression, warping,
   airtightness, ballast retention, and repeated service cycles.
5. Perform the 100-250 Pa gross bubble leak screen, then measure impedance to
   determine real tuning and leakage Q.
6. Set passive-radiator mass and DSP from measured impedance; then verify
   excursion, polarity, clipping, SPL, rattles, and thermal behaviour.
7. Verify microphones, wake word, buttons, LEDs, USB-C, Wi-Fi, antenna
   performance, and sustained-temperature behaviour on the assembled specimen.

No physical fit, sound, thermal, radio, microphone, or durability claim should
be upgraded without recorded specimen data.

## PLA+ determination

PLA+ is not a supported final-enclosure material for RC1. It may be used for
non-operational visual or assembly prototypes, but a PLA+ coupon cannot
calibrate a later ASA/PETG print because the shrink and hole response differ.

The exclusion is an engineering risk decision, not a claim that every
commercial product labelled PLA+ has identical properties. “PLA+” has no
single controlled formulation, and this enclosure depends on sustained gasket
clamp load, heat-set-insert retention, four ballast-retainer screws, cabinet
dimensional stability, and an electronics-bay thermal soak at 35 C ambient.
Those requirements make ordinary PLA+ heat deflection and long-term creep
margin inadequate or unproven. The current mass, center-of-gravity, insert
pull-test, thermal, and service-cycle evidence is also based on ASA, with PETG
as the documented alternative.

A builder who wants to qualify a specific high-temperature or annealed PLA
must treat it as a new material process: obtain its manufacturer datasheet,
print all coupons in that exact material, demonstrate dimensional stability
after the complete 35 C ambient thermal test, meet the 250 N insert pull-test,
repeat five gasket/service cycles, and rerun mass/center-of-gravity evidence
with the measured density. Until those tests are recorded, use ASA or PETG for
the final unit.
