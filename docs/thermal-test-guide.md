# Thermal test guide

`REQUIRES_PHYSICAL_VALIDATION`. No thermal simulation has been performed and none is claimed.

## Procedure

1. Instrument the Core SoC, the amplifier and the air in the electronics bay with thermocouples.
2. Soak at 25 C ambient, idle, for 60 minutes; record steady state.
3. Play pink noise at the maximum level the DSP allows for 60 minutes; record steady state.
4. Repeat both at 35 C ambient.
5. Repeat the 35 C playback case with the rear service aperture taped shut, to bound the worst case.

## Pass criteria

No component exceeds its supplier's maximum operating temperature with 15 C of margin, and the enclosure does not thermally throttle during the 60-minute playback soak. If margins are short, the shroud vent bank is parametric and can be opened up without touching the acoustic chamber.
