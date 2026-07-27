# Active-driver and passive-radiator selection

## Active-driver result

Primary: **Dayton Audio ND91-4**  
Fallback: **Tectonic Audio Labs TEBM65C20F-4**

Manufacturer parameters and dimensions are
`DERIVED_FROM_MANUFACTURER_DRAWING`. Weighted scores are
`ENGINEERING_ESTIMATE`.

| Candidate | Weighted score / 10 | Decision |
|---|---:|---|
| Scan-Speak 10F/4424G00 | 8.625 | Highest unconstrained score, rejected as primary because 3 mm Xmax gives materially less bass displacement at over three times the cost |
| Dayton ND91-4 | 8.550 | Selected: 4.6 mm Xmax, 4 ohm TAS2780 match, published Klippel data, 30 W rating, compact neo motor, broad availability |
| Tectonic TEBM65C20F-4 | 8.025 | Fallback: excellent broad BMR radiation and shallow package; lower excursion and incomplete published T/S set require impedance measurement |
| FaitalPRO 3FE25-4 | 7.600 | High sensitivity but 110 Hz Fs and 1.7 mm Xmax are poor fits for the bass objective |
| SB Acoustics SB10PGC21-4 | 7.450 | High Qts and 2.25 mm Xmax constrain output/EQ |
| Peerless TC9FD18-08 | 7.350 | Affordable but 8 ohm load, 130 Hz Fs, and high Qts under-use the amplifier |
| Markaudio CHN-50P MICA | 7.150 | Low 7 W rating and 126 Hz Fs do not meet output objectives |

The score is a decision aid, not a substitute for constraints. The Scan-Speak
candidate edges the paper score through sensitivity, response, and motor
quality, but active displacement is a hard constraint in this one-driver
architecture. ND91-4 has approximately 14.0 cm³ linear swept volume from
published Sd and Xmax versus approximately 10.5 cm³ for the Scan-Speak.

The selected driver is 4 ohm nominal with published Re 4.3 ohm. This is above
the TAS2780 3.2 ohm minimum and uses its voltage swing more effectively than an
8 ohm part. Published 85.6 dB sensitivity is referenced to 2.83 V/1 m; it is
not comparable to a 1 W/1 m number without impedance normalization.

## Passive-radiator result

Primary: **two opposed SB Acoustics SB12PACR-00**  
Fallback: **two opposed Dayton Audio DMA105-PR**

Two opposed radiators were selected over one radiator because:

- total linear radiator displacement is approximately 72 cm³ at the 7.2 mm
  design excursion, over five times the active driver's one-way swept volume
- equal, opposed diaphragms cancel their first-order cabinet reaction force at
  tuning
- each SB radiator provides accessible M6 mass adjustment
- a single SB radiator would have less displacement margin and unbalanced
  rocking force

For the preliminary 3.2 L net design volume and 50 Hz target, the lumped model
requires approximately 30.8 g moving mass per radiator, or 11.6 g added above
the published 19.2 g Mms. This value will be regenerated from exported CAD net
volume. It is `ENGINEERING_ESTIMATE` until enclosure leakage, actual moving
mass, and impedance response are measured.

The SB frame is 122 mm OD with a 102 mm cutout. That diameter drove a rounded-
square 160 mm structural cabinet: true flat radiator gasket lands are more
reliable than forcing a flat frame onto a cylindrical wall. The active driver
faces -Y and the radiators face ±X in the documented master coordinate system.

## Scoring method

Weights and raw 1–10 scores are machine-readable in `config/components.yaml`.
The categories are bandwidth/response 20%, displacement/bass 15%, amplifier
match 15%, distortion/motor 15%, breakup/directivity 10%, sensitivity 10%,
mechanical fit 5%, thermal power 5%, and availability/cost 5%.

Prices and availability are a retrieval-date `ENGINEERING_ESTIMATE`; they must
be rechecked before a production purchase.

