# Testing and Commissioning Guide

Every result in this guide requires a physical unit and is
`REQUIRES_PHYSICAL_VALIDATION`.

![Seal locations](IMAGES/gasket_placement.png)

![Final assembled inspection](IMAGES/assembly_stage_09_final.png)

## Before power

1. Verify red driver lead to + and black to -.
2. Confirm both radiators carry equal added mass: model target
   7.94 g each.
3. Confirm every screw ID and quantity against `FASTENERS.csv`.
4. Confirm G01-G04 are continuous and no wire touches a moving component.
5. Perform the 100-250 Pa gross-leak screen during assembly. Never use shop air.

## Controlled first power

Use a current-limited supported USB-C supply and the official Batch 1
firmware. Start muted, then at minimum volume.

- LEDs: all segments visible and even.
- Buttons: each click registers once and returns freely.
- USB-C: plug inserts/removes without shell contact.
- Wi-Fi: connect and record RSSI beside a bare Batch 1 control.
- Microphones: verify all four channels, then run 50 wake-word trials at 1, 3,
  and 5 m on-axis and 45 degrees.
- Audio: play a polarity pulse, then a 100-500 Hz sweep at low level. Stop for
  rub, buzz, air noise, or asymmetric radiator motion.

## Acoustic commissioning

Measure impedance magnitude and phase from 20 Hz to 20 kHz at low level. The
two low-frequency peaks should bracket tuning; the minimum between them is the
real Fb. Model targets are 60.0 Hz Fb,
4.39 ohm minimum impedance,
and 59.0 Hz f3. They are
`ENGINEERING_ESTIMATE`, not pass/fail measurements.

Start DSP with the modelled 51.0
Hz fourth-order high-pass and no positive bass boost. Final EQ, limiter, and
tuning mass require measured response and excursion.

## Thermal and reliability

Instrument Core SoC, amplifier area, and electronics-bay air. Test 60 minutes
idle and 60 minutes pink noise at 25 C, then repeat at 35 C. Pass only if every
supplier limit retains 15 C margin, there is no throttling, and no printed part
softens. Perform a gentle rattle check and repeat the leak/impedance check after
five service cycles.

Record results; do not change the repository status to physically validated
without the measurements.
