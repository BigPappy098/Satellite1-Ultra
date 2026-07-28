# Project status

## Status

- Project: Satellite1 Ultra
- Branch: `codex/include-complete-squircle-parts`
- Release state: `DIGITAL_PROTOTYPE_READY`
- Physical validation state: `REQUIRES_PHYSICAL_VALIDATION`
- Authoritative source: `45cfb9dd335752ec704865bac14170af43f014b0`
- Last updated: 2026-07-28

## Release-candidate correction

The previous RC1 package omitted the six required official Squircle
upper-stack print files by representing them only as a vague BOM “set.” This
was a release-blocking documentation/package defect. The correction now:

- packages all six mandatory official STL files byte-for-byte under
  `OFFICIAL_PARTS/REQUIRED_SINGLE_MATERIAL/`;
- separates the two optional multi-material inserts;
- names every official print individually in the BOM, Printing Guide, and
  Assembly Guide;
- explicitly tells builders to print both the Ultra and official groups, while
  excluding the original chamber, speaker plate, and anti-slip ring that the
  Ultra replaces;
- validates official release copies against their pinned source hashes; and
- states the measured limiting mesh envelope: 192 x 212 x 189 mm, with
  212 x 192 x 189 mm absolute usable travel and 220 x 220 x 200 mm practical
  minimum when the full bed is usable.

Regeneration and final validation are in progress on the topic branch.

Builder usability was then treated as a second release blocker. The corrected
package now adds:

- `00_READ_ME_FIRST.txt`;
- one plain-language `BUILD_SATELLITE1_ULTRA_FOR_BEGINNERS.pdf`;
- three numbered `PRINT_THESE_FILES` folders for calibration, Ultra enclosure,
  and mandatory Squircle top parts;
- friendly ordered filenames with quantities stated in the guide; and
- an automated coverage test proving the beginner folders contain every
  required printed part and match the validated source files byte-for-byte.

Technical reports and exchange files remain available but are explicitly
outside the normal first-time-builder path.

The beginner-path review also found that the eight official upper-stack
M3 x 8 screws were assumed rather than listed. F10 and F11 now cover those two
four-screw joints in `FASTENERS.csv`, the BOM, the fastener picture, and the
beginner assembly checklist. They use the measured official printed pilots and
do not increase the heat-set-insert quantity.

## Previous completed milestone

The final engineering audit, corrective CAD pass, release regeneration,
documentation rewrite, mutation testing, PDF visual review, and independent
clean-clone reproduction are complete. The builder-facing RC1 archive is
`release/Satellite1-Ultra-RC1.zip`.

## Verified digital evidence

- `VERIFIED_DIGITALLY`: `make check` passes, including 118 fast tests and all
  eleven quantitative engineering gates.
- `VERIFIED_DIGITALLY`: five independent deep tests pass, including
  Gmsh/OpenCascade STEP reopen.
- `VERIFIED_DIGITALLY`: all 17 deliberately injected defects are rejected by
  their intended gates.
- `DERIVED_FROM_OFFICIAL_CAD`: 126 official reference files remain
  byte-for-byte preserved and the interface datum/pattern are measured from the
  official B-rep in tests.
- `VERIFIED_DIGITALLY`: 23 STEP/STL/3MF part sets, three assembly STEP files,
  three gasket DXFs, 54 CAD-derived images, 23 drawing sheets, six illustrated
  manuals, and the 119-file release package regenerate from one command.
- `VERIFIED_DIGITALLY`: release documentation and every packaged checksum pass.
- `ENGINEERING_ESTIMATE`: 3.5176 L net chamber, 60 Hz tuning, 0.7818 g added
  mass per radiator, 56.9 Hz f3, and a fourth-order 51 Hz high-pass.

## Handoff

Digital work is complete and the working branch is ready to push and merge.
The next milestone starts with physical calibration coupons and specimen
measurements; see `reports/NEXT_ACTION.md` and
`reports/FINAL_RELEASE_STATUS.md`.
