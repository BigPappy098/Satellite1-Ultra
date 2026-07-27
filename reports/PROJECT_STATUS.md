# Project status

## Status

- Project: Satellite1 Ultra
- Branch: `codex/bootstrap`
- Release state: `IN_DEVELOPMENT`
- Physical validation state: `NOT_PERFORMED`
- Last updated: 2026-07-27

## Active phase

Phase 3 — functional mechanical skeleton. Phase 1 is complete and Phase 2 has
selected the baseline electroacoustic components; exact acoustic volume will be
fed back after bracing and sealing geometry is complete.

## Completed evidence

- `VERIFIED_DIGITALLY`: Python 3.12, CadQuery 2.6.1, and cadquery-ocp
  7.8.1.1.post1 environment builds from the hashed lock file.
- `VERIFIED_DIGITALLY`: STEP export/reopen bootstrap round trip preserved exact
  10 x 20 x 30 mm bounds and 6000 mm³ volume.
- `DERIVED_FROM_OFFICIAL_CAD`: all 25 FutureProofHomes organization repositories
  inventoried; 11 relevant repositories pinned and cloned.
- `DERIVED_FROM_OFFICIAL_CAD`: 126 official CAD/manufacturing assets preserved
  byte-for-byte with repository, commit, path, license, retrieval date, size,
  and SHA-256 provenance.
- `VERIFIED_DIGITALLY`: all 57 preserved official STEP files imported through
  CadQuery/OCCT with finite bounds, positive volume, and no import failures.
- `VERIFIED_DIGITALLY`: the selected official mid-plate independently imports
  through Gmsh's separate OpenCascade reader.
- `DERIVED_FROM_OFFICIAL_CAD`: public Batch 1 selected for the original Squircle
  development-kit baseline; Batch 2 is explicit alternate-adapter work.
- `DERIVED_FROM_OFFICIAL_CAD`: official top plate, buttons/diffuser, PCB spacer,
  lock ring, mid-plate, threaded mid-plate, and board geometry are reused.
- `DERIVED_FROM_MANUFACTURER_DRAWING`: Dayton ND91-4 selected as active driver,
  Tectonic TEBM65C20F-4 as fallback, two opposed SB12PACR-00 radiators selected,
  and two DMA105-PR radiators defined as fallback.
- `ENGINEERING_ESTIMATE`: preliminary 3.2 L / 50 Hz model calls for 30.80 g
  moving mass per SB radiator, 11.60 g above published Mms. Simulation outputs
  and volume/leak/mass sensitivity plots are generated.
- `VERIFIED_DIGITALLY`: Phase-3 manufactured skeleton parts are valid single
  B-rep solids, fit 256 mm build bounds, clear the official mid-plate, and have
  no modeled driver/radiator keep-out collisions.

## Open work

- Finish the divider/cabinet fastening interface, gasket geometry, sealed wire
  gland, bracing, base, removable ballast, bottom service cover, and grilles.
- Replace preliminary acoustic volume with exact final B-rep-derived net volume.
- Complete tolerance, wall-thickness, screw/tool-access, stability, export, mesh,
  drawing, render, documentation, and packaging gates.
- Add the Batch 2 external-antenna/USB-C service adapter.

## Environment limitations

- Docker CLI is installed, but this account lacks access to the Docker daemon.
  This does not block the clean local locked build; Docker runtime validation is
  pending a daemon-enabled environment.
- FreeCAD CLI is not installed. Independent STEP-reader coverage is provided by
  Gmsh/OpenCascade for now; a FreeCAD reader remains desirable but is not the
  only independent-reader route.

## Next autonomous action

Complete the sealed functional part set and cabinet fasteners, generate STEP
round trips from the B-rep skeleton, then run the full assembly collision and
exact-volume reports before industrial styling.

## Release gate

The correct final digital state is `DIGITAL_PROTOTYPE_READY`. It is not yet
claimed. No item is `PHYSICALLY_VALIDATED`; all fit, acoustic, wake-word,
thermal, leakage, and print claims that require a specimen remain
`REQUIRES_PHYSICAL_VALIDATION`.
