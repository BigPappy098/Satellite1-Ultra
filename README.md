# Satellite1 Ultra

Satellite1 Ultra is an open-source, serviceable, passive-radiator smart-speaker
enclosure for the FutureProofHomes Satellite1 development kit. The
authoritative manufactured geometry is parametric Python/CadQuery B-rep source;
STEP is the authoritative exchange format, with STL and 3MF derived for
manufacturing.

![Satellite1 Ultra](reports/renders/assembly_iso.png)

## Project status

**IN DEVELOPMENT — NOT YET `DIGITAL_PROTOTYPE_READY`, NOT `PHYSICALLY_VALIDATED`**

No physical validation has been performed. See
[`reports/PROJECT_STATUS.md`](reports/PROJECT_STATUS.md) for the live phase,
[`reports/CLAUDE_TAKEOVER_AUDIT.md`](reports/CLAUDE_TAKEOVER_AUDIT.md) for the
independent audit of the inherited design, and
[`docs/risk-register.md`](docs/risk-register.md) for the open risks.

## What it is

| Property | Value | Evidence |
|---|---|---|
| Overall envelope | 192 x 212 x 237 mm | `VERIFIED_DIGITALLY` |
| Acoustic cabinet | 160 x 180 mm section | `VERIFIED_DIGITALLY` |
| Net acoustic volume | 3.447 L | `VERIFIED_DIGITALLY` |
| Architecture | 1 active driver, 2 opposed passive radiators | `DERIVED_FROM_MANUFACTURER_DRAWING` |
| Active driver | Dayton Audio ND91-4 | `DERIVED_FROM_MANUFACTURER_DRAWING` |
| Passive radiators | 2 x SB Acoustics SB12PACR-00 | `DERIVED_FROM_MANUFACTURER_DRAWING` |
| System tuning | 60 Hz | `ENGINEERING_ESTIMATE` |
| Modelled f3 | 56.9 Hz, against 132.1 Hz for the same driver sealed | `ENGINEERING_ESTIMATE` |
| Assembled mass | ~3.5 kg including 1.05 kg of removable steel ballast | `ENGINEERING_ESTIMATE` |
| Upper mechanics | Official Squircle mid-plate, top plate, diffuser, buttons, PCB spacer and lock ring, unmodified | `DERIVED_FROM_OFFICIAL_CAD` |
| Hardware revision | Public Batch 1 (Satellite1, HAT rev4.1 / Core rev4.1) | `DERIVED_FROM_OFFICIAL_CAD` |

Every acoustic figure is a lumped-parameter simulation. None of it is a
measurement, and none of it may be quoted as measured performance.

## Coordinate system

The master datum is derived from the official Satellite1 mid-plate interface:

- origin: center of the official mid-plate interface plane
- +Z: upward toward microphones
- -Z: downward into the acoustic enclosure
- -Y: active-driver front
- ±X: opposed passive radiators

All source parts, keep-outs, assemblies, drawings, and reports use millimetres
and this datum. The official mid-plate underside, measured on the preserved
official B-rep, sits at Z = -6.8 mm; that plane is what the pressure divider
presents.

## Clean build

Requires Python 3.12 and a compiler-free environment; all dependencies are
pinned and hash-locked.

```bash
make bootstrap     # create .venv from requirements.lock
make release       # lint, typecheck, test, build, validate, export, document
```

Individual stages:

```bash
make build         # build and check every B-rep part
make validate      # run all eleven quantitative validation gates
make acoustics     # run the acoustic model against the measured CAD volume
make exports       # STEP, STL, 3MF and the three STEP assemblies
make renders       # CAD-derived renders and cross sections
make drawings      # per-part inspection drawing sheets
make docs          # BOM, schedules, guides, risk register, checklist
make manual        # PDF build manual
make mutation      # prove the validation gates detect injected defects
make clean         # remove every generated artifact
```

Docker is supported with:

```bash
docker build -t satellite1-ultra .
docker run --rm -v "$PWD:/work" satellite1-ultra make release
```

## Deliverables

| Deliverable | Location |
|---|---|
| Parametric CAD source | `src/satellite1_ultra/geometry.py` |
| Per-part STEP / STL / 3MF | `exports/step`, `exports/stl`, `exports/3mf` |
| Assembly, complete and exploded STEP | `exports/assembly` |
| Fit-test coupons | `exports/*/coupon_*`, `docs/fit-coupons.md` |
| Validation gates | `reports/validation` |
| Acoustic model and figures | `reports/acoustics` |
| Renders and cross sections | `reports/renders` |
| Inspection drawing sheets | `reports/drawings` |
| BOM, schedules and guides | `docs/` |
| PDF build manual | `docs/Satellite1-Ultra-Build-Manual.pdf` |

## Print the coupons first

Do not print the full part set before printing the seven fit coupons, measuring
them against `docs/fit-coupons.md`, entering the corrections in
`config/physical_compensation.yaml` and regenerating.

## Evidence labels

Engineering claims use exactly one of:

- `VERIFIED_DIGITALLY`
- `DERIVED_FROM_OFFICIAL_CAD`
- `DERIVED_FROM_MANUFACTURER_DRAWING`
- `ENGINEERING_ESTIMATE`
- `REQUIRES_PHYSICAL_VALIDATION`

The project will not use `PHYSICALLY_VALIDATED` without supplied physical test
results.

## License

Hardware design documentation and manufactured geometry are licensed under
CERN-OHL-S-2.0. Software utilities are provided under Apache-2.0. Third-party
reference assets retain their original licenses and are documented individually
in `reference-assets/MANIFEST.csv`.
