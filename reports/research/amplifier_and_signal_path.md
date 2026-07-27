# Amplifier, power, and signal-path constraints

## Evidence boundary

Electrical limits below are `DERIVED_FROM_MANUFACTURER_DRAWING` when sourced
from the preserved TI TAS2780 Rev B data sheet. Firmware behavior is
`VERIFIED_DIGITALLY` against the pinned official Satellite1-ESPHome commit.
System-level consequences are `ENGINEERING_ESTIMATE` and remain
`REQUIRES_PHYSICAL_VALIDATION`.

## TAS2780

- The TAS2780 is a mono digital-input Class-D amplifier with integrated boost,
  voltage/current sensing, thermal protection, and load diagnostics.
- The supported minimum load is 3.2 ohm. A nominal 4 ohm driver is therefore
  the intended high-output match; nominal 8 ohm candidates give away voltage-
  limited output.
- TI specifies 25 W into 4 ohm at 18 V and less than 1% THD+N, and 30 W at
  10% THD+N. The latter is a clipping/distortion boundary, not a continuous
  clean-output target.
- Absolute operating constraints include 24 V maximum boost output and 6 A
  peak output current. Satellite1 Ultra models 10 V RMS as the conservative
  clean sine limit into the selected load and separately enforces current,
  driver thermal, active excursion, and passive-radiator excursion limits.
- The chip exposes speaker voltage/current sense data on SDOUT. This can feed
  echo cancellation or protection logic, but the pinned Satellite1 firmware
  does not establish a calibrated electro-thermal protection model for the
  selected driver. Safe EQ therefore cannot depend on active protection.

Primary source: `references/manufacturer/TI_TAS2780_revB.pdf`.

## Satellite1 implementation

The official configuration identifies:

- TAS2780 at I2C address `0x3F`
- PCM5122 line-output DAC at `0x4D`
- external I2S, 48 kHz, 32-bit stereo transport
- selectable mono left+right downmix, left-only, or right-only output
- PD-dependent TAS2780 activation: power mode 2 for a negotiated contract of at
  least 9 V, power mode 0 otherwise

Source:
`references/upstream-repos/Satellite1-ESPHome/config/common/speaker.yaml`.

`ENGINEERING_ESTIMATE`: a USB-C supply advertised as “30 W” does not by itself
prove that 25 W reaches the loudspeaker continuously. Board conversion losses,
the negotiated PDO, boost current, thermal conditions, program crest factor,
and firmware gain all reduce usable continuous output. Design validation uses
the TI electrical ceiling, then calls for thermal and clipping tests with the
actual supply.

## DSP and microphone consequences

The official audio chain supports 48 kHz playback and Music Assistant exposes
DSP equalization. The upper assembly contains four microphones and XMOS audio
processing. Official enclosure documentation warns that enclosure vibration
and high playback levels can reduce wake-word performance.

Consequently:

- no positive boost is recommended below passive-radiator tuning
- the baseline protection filter is a 38 Hz fourth-order high-pass
- only broad cut EQ is release-safe before anechoic/ground-plane measurement
- final bass shelves, limiters, and microphone/AEC settings are
  `REQUIRES_PHYSICAL_VALIDATION`
- the acoustic pressure chamber is mechanically and pneumatically separated
  from the official microphone/electronics stack

