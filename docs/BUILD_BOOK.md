# The Satellite1 Ultra Build Book

> **DO NOT PRINT THE FULL ENCLOSURE YET.**
> **PRINT AND MEASURE THE 8 SMALL CALIBRATION PIECES FIRST.**

This is the only document you need to follow from start to finish. Work through
the phases in order. Every other guide in this package is reference material
that this book points you to at the moment you need it.

You are building a serviceable passive-radiator speaker enclosure around the
FutureProofHomes Satellite1 **Batch 1** development kit: Core rev4.1 and HAT
rev4.1 / R2024.12.06. Satellite1.1 / Batch 2 does not fit and is not supported.

Expected difficulty is 4 out of 5. Nothing here is glued; every joint is a
screw into a brass insert, so you can open the unit again later.

![The finished Satellite1 Ultra, assembled](IMAGES/assembly_iso.png)

## The whole build at a glance

| Phase | What you do | Roughly how long |
|---|---|---|
| 1 | Check your printer and buy the parts | ordering time |
| 2 | Print 8 small calibration pieces | 4-6 hours |
| 3 | Measure them and correct the files | 1 hour |
| 4 | Print 12 Ultra parts and 6 Satellite top parts | 3-5 days |
| 5 | Cut 3 foam gaskets from the templates | 30 minutes |
| 6 | Lay out and check every part | 30 minutes |
| 7 | Assemble, in 9 numbered steps | 3-4 hours |
| 8 | Test before you use it normally | 2 hours |

## Status you should know before you start

Every gate in this repository is a **digital** check: geometry, clearances,
volumes, exports, and documents. No physical unit has been built and measured.
Fit, sealing, acoustic output, thermals, Wi-Fi, microphones, buttons, LEDs, and
wake-word behaviour are all `REQUIRES_PHYSICAL_VALIDATION`. Your calibration,
leak, and commissioning checks in phases 3 and 8 are part of the build, not
optional extras.

---

# Phase 1 — Check your printer and buy the parts

## Your printer must actually fit the parts

The largest footprint belongs to `shell_base` at
**188 x 188 mm**. The tallest part is
`main_cabinet` at **183 mm**. Against the
configured usable travel of **220 x 200 x
250 mm** that leaves 32 mm and
12 mm of edge margin.

The outer skin is deliberately split into three stacked segments so no single
print is enormous. That keeps every part comfortably inside a common bed and
means a failed print costs you one segment, not the whole body.

- Purge lines, bed clips, and firmware exclusion zones all steal usable travel.
  Measure what your machine really reaches, then set `printing.build_volume_x`,
  `_y` and `_z` in `config/default.yaml` to what you measured. The printability
  gate reads those numbers and tests both in-plane rotations of every part, so
  it will actually fail if something does not fit.
- Printing a skin segment on its side is not supported: it puts support contact
  on the cosmetic surface.

You also need an enclosed printer, a 0.4 mm nozzle, and dry filament.

## Materials

- **ASA** for every rigid part. **PETG** is a documented alternative.
- **TPU 95A** for the two flexible parts: the cable seal and the bottom grip.
- **PLA+** is only acceptable for a display mock-up, never a finished unit.

## Tools

Digital calipers reading 0.01 mm, a scale reading 0.01 g, a 2.0 mm hex driver,
a temperature-controlled soldering iron with an M3 heat-set-insert tip,
wire strippers and a crimper or soldering iron, ESD protection, a hand bulb
with a 0-500 Pa gauge, and leak-detection solution.

## What to buy

Buy every item marked required in `BOM.csv`. The essentials are:

- One FutureProofHomes Satellite1 Batch 1 kit (E01).
- One Dayton Audio ND91-4 speaker (A01).
- Two SB Acoustics SB12PACR-00 passive radiators (A02).
- M3 heat-set inserts, with four spares (H01).
- Every M3 screw in `FASTENERS.csv`.
- One 300 x 300 mm sheet of 2.0 mm closed-cell EPDM foam (G00).
- Two mild-steel ballast plates (B01).
- Two matched sets of self-adhesive tuning mass for the radiators (B02).
- One 2-pin JST-XH speaker lead (H02).

`HARDWARE_AND_MATERIALS_GUIDE.pdf` gives the full specification for each line.

> Do not print the official original speaker chamber, speaker plate, or
> anti-slip ring. The Ultra parts replace all three.

---

# Phase 2 — Print the 8 calibration pieces

These are small. They exist so you discover your printer's real dimensional
behaviour before you spend days of filament on the big parts.

Open `PRINT_THESE_FILES/1_CALIBRATION_FIRST` and print every file, one at a
time, using the exact settings you will use for the enclosure:

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

Baseline settings: 0.4 mm nozzle, 0.20 mm layers, five walls, six top and six
bottom layers, 35% gyroid infill, no supports, 5 mm brim on the rigid pieces.
ASA runs 250-260 C nozzle and 100-110 C bed with the enclosure closed. PETG
runs 235-250 C nozzle and 75-85 C bed.

---

# Phase 3 — Measure the pieces and correct the files

This is the step that makes the big parts fit. `CALIBRATION_GUIDE.pdf` shows
exactly where each caliper jaw goes; the images below name each check.

![Where to measure the Satellite top fit piece](IMAGES/calibration_official_interface.png)

![Using the screw and insert as go/no-go gauges](IMAGES/calibration_fasteners.png)

![Checking the speaker seats by hand](IMAGES/calibration_driver.png)

![Checking a radiator seats by hand](IMAGES/calibration_radiator.png)

![Squeezing the foam between the two gasket pieces](IMAGES/calibration_gasket.png)

![Fitting the two real wires through the cable seal](IMAGES/calibration_cable.png)

## The eight checks

| Check | What you do | It passes when |
|---|---|---|
| XY scale | Inside caliper jaws across the engraved 110.60 mm recess, at three heights | 110.40-110.80 mm after correction |
| Z scale | Outside jaws across a clean 3.00 mm edge, at four corners | 2.90-3.10 mm |
| Screw clearance | Try a clean M3 screw in the 3.4, 3.5 and 3.6 mm holes | smallest hole the screw falls through without force |
| Insert bore | Install identical inserts into the 4.0-4.3 mm blind bores | square and flush, no crack, no spin |
| Speaker fit | Seat the real ND91-4 in its test ring | drops in by hand, flange lies flat, play under 0.30 mm |
| Radiator fit | Seat one real SB12PACR-00 in its test ring | drops in by hand, flange lies flat, play under 0.30 mm |
| Gasket squeeze | Clamp a strip of your actual foam until both hard stops touch | 15%-45% compression, no light path, foam not cut |
| Cable seal | Push the two real conductors and the TPU seal into the test hole | moderate finger force, seal cannot rotate or lift |

Do not measure a 3-4 mm hole with caliper tips. The screw and the insert are
the gauges.

## Enter your numbers

You have three ways to turn those measurements into corrected files. All three
produce the same `physical_calibration.yaml`.

1. **In your browser (easiest).** Open the calibration wizard page listed in
   the project README, type in what you measured, and it computes and
   downloads the file for you. Nothing to install.
2. **On GitHub.** Paste the file contents into the "Calibrated build" workflow
   and GitHub rebuilds the whole corrected package for you to download.
3. **On your own computer.** Run `python scripts/calibrate.py`, which asks the
   same questions and then runs `make calibrated-release`.

Reprint every calibration piece affected by a correction you entered, and
re-check it. Continue only when all eight checks pass on corrected pieces.

> If a piece fails, do not sand it and do not "make it work". Correct the
> number, regenerate, and reprint. Sanding a sealing face destroys the seal.

---

# Phase 4 — Print every enclosure part

Now print the real parts. Open `PRINT_THESE_FILES/2_ULTRA_ENCLOSURE_PARTS`
and print every file:

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
| 09_MIC_ISOLATORS_TPU_PRINT_FOUR.3mf | 4 | TPU 95A |
| 10_OUTER_SKIN_BOTTOM.3mf | 1 | ASA |
| 11_OUTER_SKIN_MIDDLE_WITH_GRILLES.3mf | 1 | ASA |
| 12_OUTER_SKIN_TOP.3mf | 1 | ASA |
| 13_FLEXIBLE_BOTTOM_GRIP_TPU.3mf | 1 | TPU 95A |
| 14_LEAK_TEST_TOOL.3mf | 1 | ASA |

Note that the radiator clamp ring is the only part you print **twice**.

![The outer shell, positioned on the bed](IMAGES/print_orientation_outer_shell.png)

Then open `PRINT_THESE_FILES/3_SQUIRCLE_TOP_PARTS` and print all six official
Satellite top parts. These are not optional; they complete the normal
Satellite top:

| File | Print this many | Material |
|---|---|---|
| 01_SATELLITE_MID_PLATE.stl | 1 | ASA |
| 02_SATELLITE_THREADED_PLATE.stl | 1 | ASA |
| 03_CIRCUIT_BOARD_SPACER.stl | 1 | ASA |
| 04_TOP_LOCK_RING.stl | 1 | ASA |
| 05_BUTTON_AND_LIGHT_TOP.stl | 1 | ASA |
| 06_SNAP_IN_LIGHT_RING.stl | 1 | ASA |

`PRINTING_GUIDE.pdf` holds the full slicer baseline, the per-part orientation
sheets, and the inspection checklist. Check each part as it comes off the bed:
gasket lands must be continuous and unbroken, shell slots must all be open,
clamp rings must be flat within 0.20 mm, and no insert bore may have opened
into the chamber.

---

# Phase 5 — Cut the three foam gaskets

The gaskets are not printed. You cut them from your 2.0 mm EPDM sheet using the
1:1 templates in `GASKET_TEMPLATES/`. Print each template at exactly 100% scale
(no "fit to page"), check the printed size against the sheet, then cut with a
sharp knife or a cutting plotter.

| ID | Seal | How many | Material | Template |
|---|---|---|---|---|
| G01 | divider_gasket | 1 | 2.0 mm closed-cell EPDM, soft, smooth skin | GASKET_TEMPLATES/divider_gasket.dxf |
| G02 | driver_gasket | 1 | 2.0 mm closed-cell EPDM, soft, smooth skin | GASKET_TEMPLATES/driver_gasket.dxf |
| G03 | passive_radiator_gasket | 2 | 2.0 mm closed-cell EPDM, soft, smooth skin | GASKET_TEMPLATES/passive_radiator_gasket.dxf |

The fourth seal, G04, is the flexible cable seal you already printed in TPU as
`08_FLEXIBLE_CABLE_SEAL_TPU.3mf`.

Each gasket must be one continuous piece. Do not splice, join, or stretch a
gasket to fit.

![Where each of the four seals sits](IMAGES/gasket_placement.png)

---

# Phase 6 — Lay out and check every part

Put everything on a clean table and account for it before you start. The
diagram below names every single piece and tells you which file it came from
or which item you purchased.

![Every part in the build, with its file name](IMAGES/exploded_parts_identification.png)

Check that you have all of it:

- All 12 printed Ultra parts, with two radiator clamp rings.
- All 6 printed Satellite top parts.
- One ND91-4 speaker and two SB12PACR-00 radiators.
- Three cut foam gaskets and one printed TPU cable seal.
- Every screw and insert in `FASTENERS.csv`.
- Two steel ballast plates, deburred and dry.
- Two matched radiator tuning masses, each weighed to
  0.78 g within 0.02 g.
- One red/black speaker lead with the correct plug.

The screws all look similar, so identify them by length before you begin:

![Screw lengths and where each one is used](IMAGES/fastener_identification.png)

Do not begin assembly with a missing part.

---

# Phase 7 — Assemble

Nine steps, in this order. Each one shows what to install, which screws to use,
which seal it captures, and how to tell it is right.

Tighten every screw into a printed part gently, using the short arm of the
2 mm hex key: 0.35 N m is the target and 0.45 N m is the absolute maximum.
Stop as soon as the parts meet evenly. Do not keep turning "for luck".

### Step 1 of 9 — Identify and inspect the hardware

![Build step 1: Identify and inspect the hardware](IMAGES/assembly_stage_01_identify.png)

**You need:** Batch 1 Core rev4.1 and HAT rev4.1; O01 official_mid_plate; O02 official_mid_plate_threads; O03 official_pcb_spacer; O04 official_lock_ring; O05 official_top_plate; O06 official_top_plate_snap_in_diffuser_ring

**Screws:** none   **Seal:** none   **Tools:** bright light; calipers

**Do this:** Confirm the board revision labels. Reject Batch 2 / Satellite1.1. Check off all six required official filenames in OFFICIAL_PARTS/REQUIRED_SINGLE_MATERIAL and every required custom 3MF in the Printing Guide. Inspect every sealing face and remove strings without rounding an edge.

**It is right when:** Correct Batch 1 hardware and every required printed part are present; no crack, warp, blocked bore, or damaged gasket land.

> Careful: Do not force or approximately place the Core. Its exact stack placement requires the physical official hardware.

### Step 2 of 9 — Install and cold-check all M3 inserts

![Build step 2: Install and cold-check all M3 inserts](IMAGES/assembly_stage_02_inserts.png)

**You need:** main_cabinet, pressure_divider, base_skirt, ballast_cartridge, skin segments

**Screws:** H01 inserts   **Seal:** none   **Tools:** temperature-controlled iron; M3 insert tip; square

**Do this:** At 250-270 C, press each insert into its labeled blind bore until flush and square. Let every insert cool for five minutes. Thread an M3 screw by hand for three turns.

**It is right when:** No insert spins, tilts, protrudes, or blocks before three turns.

> Careful: Do not torque a hot insert. Fumes and the iron can burn; ventilate and use eye protection.

### Step 3 of 9 — Wire and clamp the active driver

![Build step 3: Wire and clamp the active driver](IMAGES/assembly_stage_03_driver.png)

**You need:** main_cabinet, Dayton ND91-4, driver_gasket, active_driver_clamp_ring, JST-XH lead

**Screws:** F04, 4 screws   **Seal:** G02   **Tools:** 2.0 mm hex; crimper or soldering iron; polarity tester

**Do this:** Mark the red conductor positive. Connect red to the terminal marked + and black to -. Face the terminals upward. Center G02, seat the driver from the -Y/front side, fit the clamp ring, and tighten F04 in two diagonal passes to 0.35 N m; never exceed 0.45 N m.

**It is right when:** Ring bottoms evenly; G02 is continuous all the way round and covers all four unused driver mounting holes; cone moves outward on a brief 1.5 V positive polarity pulse.

> Careful: Use only a brief low-voltage polarity pulse. Never connect a loose driver to the powered HAT.

### Step 4 of 9 — Mass-match and clamp both passive radiators

![Build step 4: Mass-match and clamp both passive radiators](IMAGES/assembly_stage_04_radiators.png)

**You need:** 2 SB12PACR-00, 2 passive_radiator_gaskets, 2 clamp rings, matched tuning masses

**Screws:** F05, 8 screws total   **Seal:** G03, one per side   **Tools:** 0.01 g scale; 2.0 mm hex

**Do this:** Trim and weigh two identical tuning masses to the value in reports/acoustics/summary.json, matching them within 0.02 g. Apply one centred on each radiator mass post. Install radiators on +/-X with matching orientation, then tighten each F05 crosswise to 0.35 N m; never exceed 0.45 N m.

**It is right when:** Added masses match within 0.02 g; both rings bottom evenly; surrounds move freely and do not touch the shell keep-out.

> Careful: Unequal mass defeats reaction-force cancellation. Do not press on either cone.

### Step 5 of 9 — Route the cable, close the divider, and leak-check

![Build step 5: Route the cable, close the divider, and leak-check](IMAGES/assembly_stage_05_sealing.png)

**You need:** pressure_divider, divider_gasket, leak_test_adapter, cable_gland

**Screws:** F03, 8 screws   **Seal:** G01; temporary adapter then G04   **Tools:** 2.0 mm hex; hand bulb; 0-500 Pa gauge; leak-detection solution

**Do this:** Pass both conductors through the divider. Fit the temporary adapter over them, place G01 without twists, and tighten F03 in a star pattern to 0.35 N m. Apply only 100-250 Pa with a hand bulb. Brush leak solution on external gasket seams; no bubbles are allowed. Vent, pull the adapter upward, and install G04 with its flange toward the electronics bay.

**It is right when:** No growing bubbles, abnormal diaphragm displacement, or audible leak; final gland cannot rotate or lift by finger force.

> Careful: Never use shop air, never exceed 250 Pa, and keep liquid away from electronics. This is a gross-leak screen, not an acoustic-Q measurement.

### Step 6 of 9 — Install the base and retained ballast

![Build step 6: Install the base and retained ballast](IMAGES/assembly_stage_06_ballast.png)

**You need:** base_skirt, ballast_cartridge, 2 steel plates, ballast lid, bottom_service_plate

**Screws:** F06, F07, F08   **Seal:** none   **Tools:** 2.0 mm hex; scale

**Do this:** Attach the base skirt with F07. Place both deburred dry plates flat in the cartridge; there must be no rocking. Install the lid with F06, insert the cartridge from below, and capture it with the bottom service plate using F08.

**It is right when:** Cartridge mass matches the steel stack listed in BOM.csv; no plate moves when shaken gently; all four lid screws engage at least 3 mm.

> Careful: The steel stack is heavy. Keep fingers clear and do not operate the unit without the retained lid and service plate.

### Step 7 of 9 — Stack the three outer skin segments

![Build step 7: Stack the three outer skin segments](IMAGES/assembly_stage_07_shell.png)

**You need:** shell_base, shell_grille, shell_crown; lower assembly

**Screws:** F09, 4 screws with nylon washers; F02, 4 screws into the divider   **Seal:** none   **Tools:** 2.0 mm hex

**Do this:** Work bottom to top. Slide shell_base up over the cabinet with FRONT at -Y, invert on a soft mat, and install F09 through the bottom service plate into its four bosses. Stand the unit back up. Press shell_grille down onto the exposed lap until its outer face meets the segment below; the four crush ribs give a firm, even resistance and the joint closes on 0.15 mm of interference, so it should need hand pressure and stay put. Press shell_crown on the same way, then bolt it down onto the divider's four bosses with F02. Check that all three grille windows line up with the driver and both radiators.

**It is right when:** Both seams show an even hairline shadow line all round with no step you can catch a fingernail on; no segment rocks or rattles when the body is tapped; at least 2 mm clearance from every clamp ring and surround; no wire visible through a window.

> Careful: Do not force a segment on if it binds — lift it off and check for a stringing artefact on the lap or a crush rib that printed proud. Never flex a segment over an obstruction. The crown must be bolted to the divider before the official stack goes on, because its tabs sit underneath.

### Step 8 of 9 — Fit the mic isolators and the official Batch 1 upper stack

![Build step 8: Fit the mic isolators and the official Batch 1 upper stack](IMAGES/assembly_stage_08_upper.png)

**You need:** mic_isolation_bushing x4; O01-O06 official prints; Batch 1 HAT/Core

**Screws:** F01 (M3 x d4 shoulder screws, 16 mm shoulder), F10, F11; 4 of each   **Seal:** none; electronics bay is outside the acoustic chamber   **Tools:** 2.0 mm hex; ESD-safe bench

**Do this:** Press one TPU isolation bushing into each of the four divider counterbores, flange up. Seat O01 on the four bushing flanges — it must rest on elastomer, not on printed plastic. Install F01 and tighten until each shoulder bottoms firmly on the counterbore floor; the screw head then stops 0.3 mm above the plate and the plate stays floating on the TPU. Snap O06 into O05 (or use both O07/O08 during a multi-material O05 print; never install O06 and O08 together). Align O03's taller standoffs with the I/O side and locate the HAT. Install the Core/HAT using the official Batch 1 sequence. Align the logos and I/O on O04/O05, engage the snaps, and rotate the lock ring. Align O02's four nubs with O01 and keep I/O toward rear/+Y. Connect the keyed JST-XH speaker plug before closure.

**It is right when:** The official top sits flush with the surrounding flat top — you should feel a hairline, not a step or a lip. The upper stack has a barely perceptible give when pressed, which is the isolation working. USB-C remains reachable; cable has service slack and cannot enter a moving-part envelope; buttons click and diffuser/LED apertures remain clear.

> Careful: F01 must be M3 x d4 shoulder screws, not ordinary M3 screws. An ordinary screw clamps in parallel with the elastomer at roughly 35 times its stiffness, so the TPU carries under 3% of the load path and the isolation does nothing at all. If the plate feels rock solid, you have the wrong screws. Core placement is REQUIRES_PHYSICAL_VALIDATION: follow the official Batch 1 instructions and stop at any collision.

### Step 9 of 9 — Fit the anti-slip ring and complete inspection

![Build step 9: Fit the anti-slip ring and complete inspection](IMAGES/assembly_stage_09_final.png)

**You need:** anti_slip_ring; complete assembly

**Screws:** none   **Seal:** inspect G01-G04   **Tools:** hands; flashlight

**Do this:** Stretch the TPU ring evenly around the bottom rim. Set the unit upright and inspect all seams, fastener heads, slots, cable exits, buttons, and moving components.

**It is right when:** Unit stands without rocking; no rattle is heard during gentle handling; every fastener is present and every seal is continuously compressed.

> Careful: Do not power the unit until the commissioning checklist is ready.


---

# Phase 8 — Test before you use it

Complete every check in `TESTING_AND_COMMISSIONING_GUIDE.pdf`. The short
version:

- The gentle 100-250 Pa leak screen shows no growing bubble at any seal.
- The speaker cone moves outward on a brief positive polarity pulse.
- Both radiators move freely and never scrape.
- Every button clicks once and returns.
- Every LED segment lights evenly.
- All four microphones work.
- USB-C plugs in and out without touching the shell.
- Wi-Fi connects, and you have recorded the signal beside a bare kit.
- There is no buzz, rattle, air whistle, overheating, or softened plastic.

Never use shop air on this enclosure, and never exceed 250 Pa.

Stop using the unit if any check fails. Fix the cause and repeat the test.

---

# Optional — Wrapping the body in speaker cloth

Entirely optional, and purely cosmetic: the enclosure is finished and airtight
without it. Cloth hides every print seam and layer line, so the body reads as
one continuous surface. The grille windows stay acoustically open underneath.

**Decide before you print.** The wrap needs the `*_FOR_FABRIC` skin files, which
are the same three segments with a concealed retention channel inside each roll.
The standard files have no channel, because on a bare printed finish it reads as
a horizontal line — exactly what this design exists to remove. You cannot add
the channel later without reprinting.

## What to buy

- About 0.5 m of **acoustically transparent speaker grille cloth**. Stretch
  knit intended for loudspeakers is right; upholstery fabric, canvas and
  blackout linings are not.
- **The breath test:** hold a single layer over your mouth and breathe out
  hard. If you feel noticeable resistance, it will audibly dull the treble.
  Anything you can breathe through freely is fine.
- A small tube of **contact adhesive**. Not superglue, which wicks and stiffens.

## Steps

1. **Print the fabric variants.** From `PRINT_THESE_FILES/2_ULTRA_PARTS`, use
   `10F`, `11F` and `12F` in place of `10`, `11` and `12`. Everything else is
   unchanged.
2. **Assemble the three segments first**, exactly as in phase 7, and bolt them
   down. Wrapping before assembly puts a fabric edge inside a lap joint, which
   will hold the seam open.
3. **Cut a rectangle** about 30 mm taller than the body and long enough to go
   right round plus 25 mm of overlap. Cut with the stretch running **around**
   the body, not up it.
4. **Find the overlap seam position.** Put it on the rear (+Y) face, which has
   no grille window. It is the only part of the wrap you will be able to see.
5. **Tension it evenly.** Work from the seam outward in both directions,
   keeping the weave straight. A squircle shows tension variation at the corners
   far more than a cylinder does, so check the weave stays square as it passes
   each corner rather than pulling into a curve.
6. **Tuck the top edge** into the channel under the top roll with a blunt
   plastic tool. Do the whole perimeter before committing any adhesive.
7. **Tuck the bottom edge** into the lower channel the same way, keeping the
   vertical tension while you work.
8. **Glue last, and only inside the channel.** A thin bead in the channel only.
   Keep adhesive away from the grille windows: it stiffens the cloth locally and
   changes its acoustic transparency, which you cannot undo.
9. **Trim the overlap** flush at the rear seam once the adhesive has set.

## Checks

- The weave runs straight and square across all four faces, with no diagonal
  pull at the corners.
- All three grille windows are still visibly open cloth, with no adhesive
  bleed and no stretched-thin patches.
- The cloth still passes the breath test after wrapping. If tension has closed
  it up over a window, it is too tight.
- The anti-slip ring still seats on the base without trapping a fabric edge.

---

# Phase 9 — Opening it again later

Disconnect power and wait five minutes. `MAINTENANCE_GUIDE.pdf` gives the safe
removal order for each subassembly.

![The order things come apart in](IMAGES/service_disassembly.png)

Replace any gasket you disturb. Never cut a wire to get a part out, and never
reuse a torn or permanently flattened seal.

---

# If something goes wrong

| Symptom | Most likely cause | What to do |
|---|---|---|
| Calibration piece is warped | chamber too cool, or bed not clean | fix the printer and reprint; never compensate for a warped part |
| Every hole is too small | over-extrusion or elephant-foot compensation | fix flow and first-layer compensation before adding a CAD offset |
| Insert cracks the boss | bore too small or iron too hot | choose a larger bore or reduce dwell; never add torque |
| Speaker will not sit flat | print strings, or cutout too small | remove strings only; correct the cutout and reprint the coupon |
| Cable seal leaks or spins | conductor too thick, or wet TPU | confirm conductor OD is 1.8 mm or less, dry the TPU, reprint |
| Shell will not slide on | clamp ring or surround contact | stop immediately; find the contact rather than forcing the shell |
| Bubbles during the leak check | gasket twisted, pinched, or a screw left loose | vent, reopen, replace the gasket, and reseat evenly |
| One radiator moves more than the other | unequal tuning mass | reweigh both stacks; they must match within 0.02 g |

---

# What is still unproven

The geometry, exports, schedules, and documents in this release pass their
digital gates. No completed physical unit has been measured. That means your
own calibration, leak, acoustic, thermal, Wi-Fi, and microphone checks are the
first real evidence this design works. Record what you find.

`ENGINEERING_APPENDIX.md` lists every open risk, its consequence, and how to
close it.
