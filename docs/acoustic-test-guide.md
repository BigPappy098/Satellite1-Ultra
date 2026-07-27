# Acoustic test guide

`REQUIRES_PHYSICAL_VALIDATION`. The modelled values below are targets to compare against, not results.

## 1. Impedance sweep (do this first)

Measure impedance magnitude and phase, 20 Hz to 20 kHz, on the fully assembled and sealed cabinet at a level low enough to stay linear.

- The two impedance peaks bracket the system tuning; the minimum between them is the real Fb.
- Modelled Fb target: 60.0 Hz.
- Modelled minimum impedance: 4.39 ohm. If the measured minimum drops below 3.2 ohm, stop and re-check before driving the amplifier hard.
- Enter the measured Fb and the derived leakage Q into `config/default.yaml` and re-run the acoustic stage.

## 2. Sealed-box leak check

Pressurise the acoustic chamber to about 1 kPa through the cable gland passage with the driver and radiators fitted, and record the decay over 60 s. A fast decay means a leak; find it before measuring anything else.

## 3. Nearfield response

Measure nearfield at the driver and at each radiator, scale by area ratio and sum, then splice to a gated farfield measurement above 300 Hz. Compare against `reports/acoustics/response.csv`.

- Modelled f3: 56.9 Hz.

## 4. Maximum output and distortion

Step the level in 3 dB increments at 50, 80 and 200 Hz, recording THD and radiator excursion. Stop at 10 % THD or at the radiator's 9 mm mechanical limit, whichever comes first.

- Modelled maximum SPL at 100 Hz: 93.9 dB at 1 m.

## 5. Tuning-mass adjustment

The model calls for 1.07 g added to each radiator's M6 post. Adjust both radiators identically; unequal mass destroys the force cancellation that the opposed layout exists for.
