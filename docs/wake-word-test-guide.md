# Wake-word and microphone test guide

`REQUIRES_PHYSICAL_VALIDATION`. The enclosure does not move, cover or obstruct any microphone: the official top plate, diffuser, buttons and PCB spacer are used unmodified and the microphone openings are untouched. That is a geometric fact, not an acoustic result.

## Control

Run every test twice: once on a bare Satellite1 development kit and once on the assembled Satellite1 Ultra, in the same room, same positions, same firmware.

## Procedure

1. Wake-word detection rate: 50 utterances at 1, 3 and 5 m, on axis and at 45 degrees. Record hits and false rejects.
2. Barge-in: repeat at playback levels of 60, 70 and 80 dBA measured at 1 m, using pink noise and then music.
3. False accepts: 60 minutes of continuous speech-shaped noise and 60 minutes of television audio.
4. Button and LED check: every button actuates through the official top plate without binding, and the LED ring is evenly visible from 30 degrees above horizontal at 2 m.

## Pass criteria

Detection rate must not fall by more than 5 percentage points against the control at any distance, and barge-in must not fall by more than 5 points at 70 dBA. Anything worse is a finding against this enclosure, not against the kit.
