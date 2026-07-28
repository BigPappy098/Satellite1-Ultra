# Next action

The next action is physical, not another digital design pass.

1. Push and review `codex/final-audit-and-release`, then merge it to `main`.
2. Use `release/Satellite1-Ultra-RC1/START_HERE.pdf`.
3. Print only the calibration set first.
4. Record the measurements in `config/physical_calibration.yaml`.
5. Run `make calibrated-release` and repeat any failed coupon.
6. Do not print the full enclosure until every coupon passes.

All fit, tuning, leakage, audio, microphone, radio, thermal, print, and service
results remain `REQUIRES_PHYSICAL_VALIDATION` until specimen evidence is
recorded.
