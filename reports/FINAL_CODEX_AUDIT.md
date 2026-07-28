# Final Codex engineering audit

## Scope and method

This audit treats every inherited completion claim as unverified. The baseline
was inspected on 2026-07-28 from `main` at `df1ad5b`, then reproduced in a
separate clone created under `/tmp`. The clean-room `make bootstrap` completed
with Python 3.12 and CadQuery 2.6.1. The baseline clean-room `make release`
failed at lint before CAD generation, proving that the inherited release was
not reproducible from its declared command.

The final correction is developed on `codex/include-complete-squircle-parts`.

## Baseline findings and corrections

| Severity | Baseline defect | Correction |
|---|---|---|
| Critical | `make release` failed with 14 Ruff errors in the calibration wizard. | Wizard rewritten, typed, range-checked, atomic, and integrated with `make calibrated-release`. |
| Critical | Tests silently skipped missing validation and export reports, permitting absent/stale output to appear green. | Missing reports are failures; release cleans, regenerates, then runs fast, deep, mutation, and documentation validation. |
| High | Three incompatible ballast definitions existed; the documented four-screw lid had no screw geometry. | One 2 x 110 x 122 x 5 mm steel stack, retained cartridge, four blind insert bosses, four lid holes, and F06 schedule are authoritative. |
| High | Assembly instructions mounted electronics directly to divider bosses, although the measured interface is for the official mid-plate. | Assembly sequence now mounts the unmodified official mid-plate first and labels exact Core placement `REQUIRES_PHYSICAL_VALIDATION`. |
| High | The pressure test demanded 1 kPa/60 s and conflated decay with acoustic leakage Q. | Temporary TPU adapter and a 100-250 Pa gross bubble screen are used; final sealing/tuning requires an impedance sweep. |
| High | Multiple compensation files and internal variables made printer calibration ambiguous. | One user-facing `config/physical_calibration.yaml` with safe limits, seven printed coupon parts, six checks, and one regeneration command. |
| High | The acoustic model subtracted unretained damping and a stale script could overwrite current 60 Hz results with 50 Hz results. | RC1 contains no damping; the legacy script delegates to the authoritative CAD-coupled model. |
| High | User docs conflicted on coupon count, wiring, ballast, seals, part names, and physical validation. | Obsolete task guides are replaced by one generated hierarchy, a beginner-first guide, and seven illustrated PDFs. |
| Medium | Cable specification could not fit the individual gland bores. | One 22 AWG red/black stranded lead, conductor OD no greater than 1.8 mm, with the official 2-pin JST-XH interface is specified. |
| Medium | Part print-orientation prose contradicted encoded orientation for clamp rings, cable gland, and ballast lid. | Metadata and one render per released part use the actual Z=0 orientation. |
| Medium | Gasket instructions lacked authoritative cutting templates. | Three 1:1 DXF profiles are generated from the gasket B-reps. |
| Medium | Evidence used the prohibited label `UNDETERMINED`. | All claims use exactly the five project evidence labels. |

## Independent engineering conclusions

- The preserved official reference assets remain unmodified. Provenance,
  revision, license, byte count, and SHA-256 remain recorded in
  `reference-assets/MANIFEST.csv`.
- Supported electronics are Satellite1 Batch 1 only: Core rev4.1 plus HAT
  rev4.1 / R2024.12.06. Batch 2 is unsupported.
- The official mid-plate plane and mount pattern remain measured from the
  preserved official B-rep. Exact Core placement is not present in an official
  assembled model and therefore requires the physical Batch 1 kit.
- The selected acoustic parts remain Dayton Audio ND91-4 and two SB Acoustics
  SB12PACR-00 radiators. Manufacturer dimensions and parameters are
  `DERIVED_FROM_MANUFACTURER_DRAWING`.
- Lumped acoustic response, excursion, SPL, thermal behavior, leakage
  sensitivity, and tuning are `ENGINEERING_ESTIMATE`, not measurements.
- No physical print, assembly, leak, impedance, microphone, wake-word, thermal,
  Wi-Fi, LED, or button evidence was supplied. Those results remain
  `REQUIRES_PHYSICAL_VALIDATION`.

## Final evidence

The authoritative source is
`0ae7c9bbf745f27bdfa5d2d6e62dcb2841d9c2c4`. The final fast suite passed
with 120 tests, and the release passed with six deep tests
and 18 deliberate mutations. The same command then succeeded in a fresh clone
and fresh virtual environment. It regenerated 23 STEP/STL/3MF part sets, three
assembly STEP files, three gasket DXFs, 62 CAD renders, 23 drawing sheets, seven
illustrated PDFs, and a checksummed 163-file user release.

All 64 PDF pages were rendered to images and visually reviewed. Corrections
made during that review included missing calibration illustrations, incorrect
fastener lengths and layout, an obscured ballast stage, measurement arrows, and
page-fit issues.

The final status, release checksum, engineering values, test counts, and
remaining specimen-dependent risks are recorded in
`reports/FINAL_RELEASE_STATUS.md`. The defensible release state is
`DIGITAL_PROTOTYPE_READY`, never `PHYSICALLY_VALIDATED`.
