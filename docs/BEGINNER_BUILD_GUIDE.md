# Build Satellite1 Ultra: Beginner Guide

This is the normal build path. Start here and work from top to bottom. You do
not need to open the source code, STEP files, reports, or engineering appendix.

> **STOP: DO NOT PRINT THE BIG PARTS YET.**
> **PRINT THE SMALL CALIBRATION PARTS FIRST.**

## Before you spend money

- Electronics: FutureProofHomes Satellite1 **Batch 1**, Core rev4.1 and HAT
  rev4.1 / R2024.12.06. Satellite1.1 / Batch 2 does not fit this release.
- Printer: at least 212 x 192 x 189 mm of truly usable movement. A fully usable
  220 x 220 x 200 mm printer works one part at a time.
- Material: ASA for rigid parts and TPU 95A for the two flexible parts. PETG
  may replace ASA. PLA+ is only for a display mock-up, not the finished unit.
- Basic tools: digital calipers, 0.01 g scale, 2 mm hex key, soldering/crimping
  tools, and an M3 heat-set-insert tip.
- Buy every item marked required in `BOM.csv`.

If any line above is not true, stop and fix it before printing.

## The only folders you need for printing

Open `PRINT_THESE_FILES`. Ignore the advanced STEP/STL/3MF folders.

1. `1_CALIBRATION_FIRST` — print now.
2. `2_ULTRA_ENCLOSURE_PARTS` — print only after calibration passes.
3. `3_SQUIRCLE_TOP_PARTS` — print all six after calibration passes.

## Step 1 — Print the small test pieces

Print these one at a time with the same printer settings you will use later:

| File | Print this many | Material |
|---|---|---|
| 01_CHECK_SATELLITE_TOP_FIT.3mf | 1 | ASA |
| 02_CHECK_SCREWS_AND_INSERTS.3mf | 1 | ASA |
| 03_CHECK_SPEAKER_FIT.3mf | 1 | ASA |
| 04_CHECK_RADIATOR_FIT.3mf | 1 | ASA |
| 05_GASKET_TEST_BASE.3mf | 1 | ASA |
| 06_GASKET_TEST_TOP.3mf | 1 | ASA |
| 07_CHECK_CABLE_HOLE.3mf | 1 | ASA |
| 08_FLEXIBLE_CABLE_SEAL_TPU.3mf | 1 | TPU 95A |

Use a 0.4 mm nozzle, 0.20 mm layers, five walls, six top/bottom layers, and 35%
gyroid infill. No supports. Use a 5 mm brim on the rigid test pieces.

![What to measure on the Satellite top test](IMAGES/calibration_official_interface.png)

## Step 2 — Check the test pieces

Open `START_HERE_CALIBRATION_GUIDE.pdf`. It shows exactly where the calipers go.
The simple rule is:

- The Satellite top test must sit flat without force.
- An M3 screw must pass through its chosen hole by hand.
- A heat-set insert must finish straight, flush, and tight.
- The real speaker and both radiators must drop into their test rings by hand.
- The gasket test must squeeze the foam without cutting it or leaving a gap.
- The two real speaker wires must fit the flexible cable seal snugly.

If a test fails, do not sand the final fit and do not print the big parts.
Enter the measured correction in `CALIBRATION_INPUT_TEMPLATE.yaml`, run
`make calibrated-release`, and reprint the failed test. Continue only when
every test passes.

## Step 3 — Print every Ultra enclosure part

Open `PRINT_THESE_FILES/2_ULTRA_ENCLOSURE_PARTS` and print every file:

| File | Print this many | Material |
|---|---|---|
| 01_MAIN_SPEAKER_BODY.3mf | 1 | ASA |
| 02_ELECTRONICS_DIVIDER.3mf | 1 | ASA |
| 03_SPEAKER_CLAMP_RING.3mf | 1 | ASA |
| 04_RADIATOR_CLAMP_RING_PRINT_TWO.3mf | 2 | ASA |
| 05_BOTTOM_BASE.3mf | 1 | ASA |
| 06_WEIGHT_TRAY.3mf | 1 | ASA |
| 07_WEIGHT_TRAY_LID.3mf | 1 | ASA |
| 08_BOTTOM_ACCESS_PANEL.3mf | 1 | ASA |
| 09_ELECTRONICS_COVER.3mf | 1 | ASA |
| 10_OUTER_SHELL.3mf | 1 | ASA |
| 11_FLEXIBLE_BOTTOM_GRIP_TPU.3mf | 1 | TPU 95A |
| 12_LEAK_TEST_TOOL.3mf | 1 | ASA |

The outer shell is the largest part: 192 x 212 x 189 mm. Print it upright. On
a 220 mm bed, use no more than a 3 mm brim and make sure purge lines or bed
clips do not steal the needed space.

![Outer shell on the print bed](IMAGES/print_orientation_outer_shell.png)

## Step 4 — Print every Satellite Squircle top part

Open `PRINT_THESE_FILES/3_SQUIRCLE_TOP_PARTS` and print all six:

| File | Print this many | Material |
|---|---|---|
| 01_SATELLITE_MID_PLATE.stl | 1 | ASA |
| 02_SATELLITE_THREADED_PLATE.stl | 1 | ASA |
| 03_CIRCUIT_BOARD_SPACER.stl | 1 | ASA |
| 04_TOP_LOCK_RING.stl | 1 | ASA |
| 05_BUTTON_AND_LIGHT_TOP.stl | 1 | ASA |
| 06_SNAP_IN_LIGHT_RING.stl | 1 | ASA |

These are not optional. They complete the normal Satellite top. Do not print
the old official speaker chamber, speaker plate, or rubber ring; the Ultra
parts replace those three items.

![The six official top parts in the assembled area](IMAGES/assembly_stage_08_upper.png)

## Step 5 — Check everything before assembly

Lay every printed part on a table and check it off against the two tables
above. Also check:

- One Dayton Audio ND91-4 speaker.
- Two SB Acoustics SB12PACR-00 passive radiators.
- Every screw and insert in `FASTENERS.csv`.
- Four gaskets/seals G01 through G04 from `GASKETS.csv`.
- Two equal passive-radiator weight stacks.
- Two steel ballast plates.
- One red/black speaker wire with the correct plug.

Do not begin assembly with a missing part.

![All major printed pieces](IMAGES/exploded_parts_identification.png)

## Step 6 — Assemble in this order

Keep `ASSEMBLY_GUIDE.pdf` open for the picture that goes with each numbered
step. Use this screw-and-seal checklist so nothing is assumed:

| Step | What you install | Screws | Seal |
|---|---|---|---|
| 1 | Check all parts | none | none |
| 2 | Brass inserts | H01; keep four spares | none |
| 3 | Main speaker and clamp ring | four F04 | G02 |
| 4 | Two side radiators and two clamp rings | eight F05 total | one G03 per side |
| 5 | Electronics divider | eight F03 | G01, then flexible wire seal G04 |
| 6 | Bottom base, weight-tray lid, access panel | four F07, four F06, four F08 | none |
| 7 | Outer shell | four F09 with nylon washers | none |
| 8 | Electronics cover and Satellite top | four each of F02, F01, F10, and F11 | none |
| 9 | Flexible bottom grip | none | none |

Then follow these actions:

1. Check the electronics label and every print.
2. Install the brass inserts. Let them cool before using a screw.
3. Connect the speaker wire and clamp the main speaker.
4. Add equal weights to both radiators, then clamp them to the two sides.
5. Route the wire, fit the large divider gasket, close the divider, and run the
   gentle leak test.
6. Fit the bottom base, steel weights, weight-tray lid, and access panel.
7. Slide on the outer shell without touching a speaker or radiator.
8. Fit the electronics cover and all six Satellite top parts.
9. Fit the flexible bottom grip and inspect the finished unit.

Tighten printed-part screws gently with the short end of the 2 mm hex key. Stop
when the parts meet evenly. Do not keep turning “for luck.”

## Step 7 — Test before normal use

Open `TESTING_AND_COMMISSIONING_GUIDE.pdf` and complete every checkbox:

- No air bubbles at a gasket during the gentle leak test.
- Main speaker moves outward on the quick polarity check.
- Both side radiators move freely and do not scrape.
- Buttons click and return.
- Every light works.
- All microphones work.
- USB-C fits without rubbing.
- Wi-Fi connects normally.
- No buzz, rattle, air whistle, overheating, or soft plastic.

Stop using the unit if any check fails. Fix the problem, then repeat the test.

## If you need to open it later

Disconnect power and open `MAINTENANCE_GUIDE.pdf`. It gives the safe removal
order. Never cut a wire and never reuse a torn or permanently flattened gasket.

## What is still unknown

The files and geometry pass digital checks, but no completed physical unit has
been tested yet. Your calibration, fit, leak, sound, Wi-Fi, microphone, and
temperature checks are required parts of the build—not optional extras.
