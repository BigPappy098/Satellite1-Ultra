# Engineering Appendix

Source commit at generation: `b59edacd4ed097bdf22620df0254b79bbeca01d2`.

## Coordinate system

- Origin: center of the measured official mid-plate interface plane.
- +Z: microphones/top; -Y: active-driver front; +/-X: opposed radiators.
- Units: millimetres.

## Current digital acoustic model

- Net acoustic volume: 3.518 L,
  `VERIFIED_DIGITALLY` from the connected OCCT air domain.
- Tuning: 60.0 Hz.
- Added mass: 0.78 g per radiator.
- Modelled f3: 56.9 Hz.
- Modelled minimum impedance:
  4.39 ohm.

All acoustic performance values are `ENGINEERING_ESTIMATE`.

## Digital gates

| Gate | Status | Evidence |
|---|---|---|
| acoustic_volume | PASS | VERIFIED_DIGITALLY |
| assembly | PASS | VERIFIED_DIGITALLY |
| center_of_gravity | PASS | ENGINEERING_ESTIMATE |
| clearance | PASS | VERIFIED_DIGITALLY |
| collision | PASS | VERIFIED_DIGITALLY |
| core_fit | PASS | VERIFIED_DIGITALLY |
| fasteners | PASS | VERIFIED_DIGITALLY |
| printability | PASS | VERIFIED_DIGITALLY |
| sealing | PASS | VERIFIED_DIGITALLY |
| tolerance | PASS | ENGINEERING_ESTIMATE |
| wall_thickness | PASS | VERIFIED_DIGITALLY |

## Risk register

| ID | Severity | Risk | Closure | Evidence |
|---|---|---|---|---|
| R-01 | HIGH | Driver and radiator flange thicknesses are not dimensioned | Measure both purchased components, enter the values in config/physical_calibration.yaml, and pass both component coupons. | REQUIRES_PHYSICAL_VALIDATION |
| R-02 | HIGH | Core board placement is absent from the official assembled CAD | The CAD reserves a Core-sized service volume. Confirm the official Core/HAT stack against the physical Batch 1 kit before closing the upper stack. | REQUIRES_PHYSICAL_VALIDATION |
| R-03 | HIGH | Low-frequency output is excursion limited | Start with the documented fourth-order high-pass, verify polarity and tuning with an impedance sweep, then set DSP from measurements. | ENGINEERING_ESTIMATE |
| R-04 | MEDIUM | Printed walls and compressed seals have not been leak tested | Use the temporary leak-test adapter at 100-250 Pa, inspect every joint, and then confirm the final cable gland by impedance measurement. | REQUIRES_PHYSICAL_VALIDATION |
| R-05 | MEDIUM | Printer dimensional performance is unknown | Complete all eight calibration checks and regenerate with make calibrated-release before any full-size print. | REQUIRES_PHYSICAL_VALIDATION |
| R-06 | MEDIUM | Wake-word, Wi-Fi, LED, and button performance are unmeasured | Run the controlled bare-kit versus enclosed-kit commissioning tests. | REQUIRES_PHYSICAL_VALIDATION |
| R-07 | MEDIUM | Closed-shroud thermal behavior is unmeasured | Perform the documented 25 C and 35 C thermal soaks with instrumented hardware. | REQUIRES_PHYSICAL_VALIDATION |
| R-08 | LOW | Insert pullout strength depends on printer, material, and installation | Select the coupon bore that installs square, torque-test it cold, and reserve the 250 N pull test for formal physical validation. | REQUIRES_PHYSICAL_VALIDATION |
| R-09 | LOW | Satellite1.1 / Batch 2 is not supported by this release | Use only Batch 1 rev4.1 Core + rev4.1 HAT. Add a validated adapter before claiming Batch 2 compatibility. | DERIVED_FROM_OFFICIAL_CAD |

Detailed machine-readable evidence remains under `reports/validation/`,
`reports/acoustics/`, `reports/research/`, and `reference-assets/MANIFEST.csv`.
