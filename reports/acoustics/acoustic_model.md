# Acoustic model

`ENGINEERING_ESTIMATE`. Every number below is a lumped-parameter calculation. None of it is a measurement, and none of it may be quoted as measured performance.

## System

- Net acoustic volume: **3.518 L** (exact B-rep, `VERIFIED_DIGITALLY`)
- Architecture: one active driver, 2 opposed passive radiators
- Target tuning: 60.0 Hz
- Required moving mass per radiator: **19.69 g**
- Published Mms per radiator: 11.70 g
- Added tuning mass per radiator: **7.99 g** (15.97 g total), fitted to the M5 mass-adjustment thread

## Modelled results

- Sealed-alignment f3: 132.1 Hz
- Passive-radiator f3: **59.0 Hz** (73.0 Hz of extension)
- Minimum modelled impedance: 4.39 ohm at 394 Hz (amplifier minimum 3.2 ohm, margin 1.19 ohm)
- Maximum SPL at 50 Hz: 86.3 dB at 1 m
- Maximum SPL at 100 Hz: 94.2 dB at 1 m
- Maximum SPL at 1 kHz: 93.1 dB at 1 m
- Recommended protective high-pass: **51.0 Hz, order 4**

## Conservative EQ guidance

- Do not apply low-shelf boost below the recommended high-pass corner.
- Limit any bass shelf to +3 dB between the high-pass corner and 120 Hz and re-check excursion before raising it.
- Apply a gentle 1-2 dB broad cut around the modelled impedance minimum if the amplifier reports current limiting.
- Cone breakup of the ND91-4 aluminium cone sits above 10 kHz; a low-pass or notch there is a listening choice, not a protection need.

## Physical gate

`REQUIRES_PHYSICAL_VALIDATION` — Measure impedance on the assembled cabinet to obtain the real tuning frequency and leakage Q, then re-run this model with the measured values before finalising DSP.

## Figures

- `system_response.png` — response, impedance, excursion, maximum SPL
- `sensitivity.png` — net-volume, leakage and tuning-mass sensitivity
- `response.csv` — the full tabulated simulation
