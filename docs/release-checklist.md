# Release checklist

## Digital gates

- [x] Clean build from a fresh checkout with one command — `make release`
- [x] Lint, format and strict type check — `make check`
- [x] Official asset checksums and provenance — `tests/test_official_manifest.py`
- [x] Validation gate `acoustic_volume`: PASS
- [x] Validation gate `assembly`: PASS
- [x] Validation gate `center_of_gravity`: PASS
- [x] Validation gate `clearance`: PASS
- [x] Validation gate `collision`: PASS
- [x] Validation gate `core_fit`: PASS
- [x] Validation gate `fasteners`: PASS
- [x] Validation gate `printability`: PASS
- [x] Validation gate `sealing`: PASS
- [x] Validation gate `tolerance`: PASS
- [x] Validation gate `wall_thickness`: PASS
- [x] Acoustic alignment matches the optimiser (deviation 1.0 Hz)
- [x] STEP, STL and 3MF exported, reopened and volume/bounds compared
- [x] Mutation suite demonstrates the gates detect representative defects
- [x] Renders and cross-sections generated from the CAD itself
- [x] BOM, fastener schedule, gasket schedule and all guides generated
- [x] Risk register current

## Physical gates — none of these is met

- [ ] Eight fit coupons printed, measured and compensations entered
- [ ] Pressure-decay leak test passed
- [ ] Insert pull test to 250 N passed
- [ ] Impedance sweep measured and fed back into the acoustic model
- [ ] Nearfield and farfield response measured
- [ ] Wake-word control comparison passed
- [ ] Thermal soak passed
- [ ] Tip and 3 g ballast retention tests passed

The design may be marked `DIGITAL_PROTOTYPE_READY` when the digital gates are complete. It may not be marked `PHYSICALLY_VALIDATED` until every physical gate above has measured evidence.
