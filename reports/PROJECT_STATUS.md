# Project status

## Status

- Project: Satellite1 Ultra
- Branch: `claude/codex-takeover`
- Release state: `IN_DEVELOPMENT`
- Physical validation state: `NOT_PERFORMED`
- Last updated: 2026-07-27

## Active phase

Phase 7 complete, Phase 8 in progress. The functional design is validated, the
industrial-design shell is in place, and the full manufacturing package
generates from one command. What remains before `DIGITAL_PROTOTYPE_READY` can
be claimed is listed under *Open work*.

## Phase completion

| Phase | State | Note |
|---|---|---|
| 0 — Bootstrap | complete | Inherited and verified; `make release` now actually runs the pipeline it claimed to |
| 1 — Official reference research | complete | Inherited; datum and mount pattern re-derived from the official B-rep by test rather than asserted |
| 2 — Component and acoustic research | complete | Driver selection verified and upheld; the alignment was wrong and is now derived by an optimiser |
| 3 — Mechanical skeleton | complete | Rebuilt: clamp-ring mounts, internal pads, bracing |
| 4 — Functional mechanical design | complete | 15 manufactured parts plus 7 fit coupons |
| 5 — Validation | complete | Eleven gates, all PASS; 13 mutations, all detected |
| 6 — Industrial design | complete | Slotted outer shell, cosmetic shoulder, two controlled concentric seams |
| 7 — Manufacturing package | complete | STEP/STL/3MF, assemblies, drawings, BOM, schedules, guides, PDF manual |
| 8 — Digital prototype readiness | in progress | See *Open work* |

## Verified evidence

- `VERIFIED_DIGITALLY`: Python 3.12, CadQuery 2.6.1 and cadquery-ocp 7.8.1.1
  build from the hashed lock file; STEP export/reopen round trip is exact.
- `DERIVED_FROM_OFFICIAL_CAD`: 126 official assets preserved byte-for-byte with
  repository, commit, path, license, retrieval date, size and SHA-256; every
  checksum re-verified.
- `DERIVED_FROM_OFFICIAL_CAD`: the master datum, the official interface plane
  (Z = -6.8 mm) and the four-point mount pattern (±45.0534, ±31.5467) are each
  *measured* from the preserved official B-rep by a test, not asserted.
- `VERIFIED_DIGITALLY`: all 22 exported parts are single valid B-rep solids,
  fit the 256 mm build envelope, round-trip through STEP with exact volume and
  bounds, and produce watertight single-component STL and 3MF meshes.
- `VERIFIED_DIGITALLY`: the acoustic pressure boundary is continuous. Every
  gasket land measures a solid fraction of 1.000000, every insert bore in the
  boundary is blind and backed, and no fastener crosses the boundary.
- `VERIFIED_DIGITALLY`: the functional assembly has exactly one classified
  interference — the intended TPU wire-gland compression. Every printed part
  clears every official upper-stack solid and the conservative envelope of the
  official HAT.
- `VERIFIED_DIGITALLY`: net acoustic volume is 3.447 L, computed as the exact
  OCCT volume of the connected air domain after 0.229 L of printed intrusion.
- `VERIFIED_DIGITALLY`: the assembly graph is acyclic with no trapped parts and
  no unresolved dependencies; every part has a defined insertion and removal
  direction and tool.
- `VERIFIED_DIGITALLY`: 13 injected defects are each detected by the gate
  responsible for them; three gaps this exposed have been closed.
- `ENGINEERING_ESTIMATE`: modelled f3 of 56.9 Hz against 132.1 Hz for the same
  driver sealed, at 60 Hz tuning with 1.07 g of added mass per radiator;
  minimum modelled impedance 4.39 Ω, 1.19 Ω above the TAS2780 limit.
- `ENGINEERING_ESTIMATE`: 3.49 kg assembled with a removable 1.05 kg dry steel
  ballast stack; minimum static tipping angle 49.6°.

## Open work before `DIGITAL_PROTOTYPE_READY`

1. Verify the clean build from a genuinely fresh checkout in a container, not
   just from the developed tree. Docker is installed but this account has no
   access to the daemon.
2. Add a second independent STEP reader over the *generated* exports. Gmsh
   currently provides independent-reader coverage of the official geometry
   only; FreeCAD is not installed here.
3. Re-run the whole pipeline once more and commit the artifacts so every
   exported file's `source_commit` matches the commit that contains it.

## Environment limitations

- Docker CLI is installed but this account has no access to the Docker daemon,
  so container-based clean-build validation is deferred.
- FreeCAD CLI is not installed. Independent reader coverage is Gmsh/OpenCascade
  for now.
- Git LFS is not installed. The repository has been made consistent with that:
  the inert LFS filter declaration was removed, since no object in the history
  is an LFS pointer.

## Next autonomous action

Regenerate the full artifact set against the final source commit, confirm every
`source_commit` field matches, then evaluate the `DIGITAL_PROTOTYPE_READY`
gate.

## Release gate

The correct final digital state is `DIGITAL_PROTOTYPE_READY`. It is **not yet
claimed**. Nothing is `PHYSICALLY_VALIDATED`; all fit, acoustic, wake-word,
thermal, leakage, wireless and print claims that require a specimen remain
`REQUIRES_PHYSICAL_VALIDATION`. See `docs/release-checklist.md`.
