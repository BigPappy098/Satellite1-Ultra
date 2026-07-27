# Project status

## Status

- Project: Satellite1 Ultra
- Branch: `codex/bootstrap`
- Release state: `IN_DEVELOPMENT`
- Physical validation state: `NOT_PERFORMED`
- Last updated: 2026-07-27

## Active phase

Phase 5 — quantitative validation. The complete serviceable functional part set
and removable industrial-design cage are modeled; exact B-rep volume, tolerance,
fastener, wall, stability, and release-export gates are now being generated.

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
- `VERIFIED_DIGITALLY`: all 17 functional manufactured parts and seven fit
  coupons are valid single B-rep solids and fit the 256 mm build envelope.
- `VERIFIED_DIGITALLY`: the sealed functional assembly has no unclassified
  volumetric collisions; the sole interference is the intentional TPU wire
  gland compression in the pressure divider.
- `VERIFIED_DIGITALLY`: the vented electronics shroud clears every selected
  official upper-stack solid, including the public Batch 1 HAT assembly.
- `VERIFIED_DIGITALLY`: the active-driver and opposed-radiator envelopes clear
  one another, the acoustic floor, the pressure divider, and the protective
  grille cage at full modeled mechanical excursion.
- `ENGINEERING_ESTIMATE`: a removable 120 × 120 × 9 mm steel-plate ballast
  stack provides approximately 1.02 kg low in the base without exposing
  electronics to wet casting material.

## Open work

- Replace preliminary acoustic volume with exact final B-rep-derived net volume
  and regenerate the passive-radiator tuning analysis.
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

Generate exact-volume, collision, clearance, wall, tolerance, fastener, and
stability reports; feed the resulting net volume back into the acoustic model,
then generate release exports and drawing/render sheets.

## Release gate

The correct final digital state is `DIGITAL_PROTOTYPE_READY`. It is not yet
claimed. No item is `PHYSICALLY_VALIDATED`; all fit, acoustic, wake-word,
thermal, leakage, and print claims that require a specimen remain
`REQUIRES_PHYSICAL_VALIDATION`.
