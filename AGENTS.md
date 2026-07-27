# AGENTS.md

## Mission

Build and maintain Satellite1 Ultra as a production-quality, editable,
parametric smart-speaker enclosure. The Python/CadQuery B-rep source is
authoritative. STEP is the authoritative exchange format. STL and 3MF are
derived outputs.

## Non-negotiable engineering rules

- Preserve official FutureProofHomes geometry unmodified in
  `reference-assets/official/`.
- Pin source repository, commit, path, license, retrieval date, byte count, and
  SHA-256 in `reference-assets/MANIFEST.csv`.
- Reuse the official upper mechanical stack and mid-plate interface where
  geometrically possible.
- Do not move or obstruct microphones, buttons, LEDs, connectors, antennas, or
  their validated keep-outs.
- Manufactured parts must be true parametric B-rep solids. Do not use voxel,
  SDF, marching-cubes, Blender, or mesh booleans as source geometry.
- Use the documented master coordinate system and millimetres everywhere.
- Do not treat export success alone as validation.
- Never label an unmeasured physical claim as verified.
- No structural glue. Acoustic seals must be replaceable and mechanically
  compressed.
- Every part must fit within 256 × 256 × 256 mm.

## Workflow

- Develop only on `codex/*` branches.
- Update `reports/PROJECT_STATUS.md` at every milestone or stopping point.
- Keep generated release artifacts reproducible and provenance-stamped.
- Run `make check` before milestone commits and `make release` before release.
- Keep the working tree clean at handoff.
- Record autonomous blockers and the next action in the status report.

## Evidence labels

Use exactly one of:

- `VERIFIED_DIGITALLY`
- `DERIVED_FROM_OFFICIAL_CAD`
- `DERIVED_FROM_MANUFACTURER_DRAWING`
- `ENGINEERING_ESTIMATE`
- `REQUIRES_PHYSICAL_VALIDATION`

## Repository map

- `src/satellite1_ultra/`: authoritative parametric CAD and engineering models
- `config/`: product, component, and physical-compensation configuration
- `reference-assets/official/`: unmodified official source geometry
- `references/`: human-readable and machine-readable research provenance
- `tests/`: unit, geometry, export, and validation tests
- `scripts/`: reproducible build, inspection, rendering, and reporting entrypoints
- `exports/`: release STEP, STL, and 3MF artifacts
- `docs/`: manufacturing, assembly, service, and test documentation
- `reports/`: research, geometry, acoustics, validation, and review evidence

