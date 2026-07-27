# Satellite1 Ultra

Satellite1 Ultra is an open-source, HomePod-sized, serviceable smart-speaker
enclosure for the FutureProofHomes Satellite1 development kit. The
authoritative manufactured geometry is parametric Python/CadQuery B-rep source;
STEP is the authoritative exchange format, with STL and 3MF derived for
manufacturing.

## Project status

**IN DEVELOPMENT — NOT YET DIGITAL_PROTOTYPE_READY**

No physical validation has been performed. See
[`reports/PROJECT_STATUS.md`](reports/PROJECT_STATUS.md) for the live phase,
validated evidence, open risks, and the next autonomous action.

## Coordinate system

The master datum is derived from the official Satellite1 mid-plate interface:

- origin: center of the official mid-plate interface plane
- +Z: upward toward microphones
- -Z: downward into the acoustic enclosure
- -Y: active-driver front
- ±X: opposed passive radiators

All source parts, keep-outs, assemblies, drawings, and reports use millimetres
and this datum.

## Clean build

The intended release command is:

```bash
make release
```

During development, bootstrap and validate with:

```bash
make bootstrap
make test
```

Docker is supported with:

```bash
docker build -t satellite1-ultra .
docker run --rm -v "$PWD:/work" satellite1-ultra make release
```

## Evidence labels

Engineering claims use one of these labels:

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

