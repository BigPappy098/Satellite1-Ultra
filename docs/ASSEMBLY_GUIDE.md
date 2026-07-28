# Illustrated Assembly Guide

Front is -Y, rear is +Y, left/right radiators are -X/+X, and +Z points
toward the microphones. All torque values are `ENGINEERING_ESTIMATE`
until the selected insert/process is pull-tested.

![Exploded part identification](IMAGES/exploded_parts_identification.png)

## Exploded-view part key

| Exact part name | Qty | Material |
|---|---|---|
| anti_slip_ring | 1 | TPU 95A |
| outer_shell | 1 | ASA |
| main_cabinet | 1 | ASA |
| pressure_divider | 1 | ASA |
| electronics_shroud | 1 | ASA |
| active_driver_clamp_ring | 1 | ASA |
| passive_radiator_clamp_ring | 2 | ASA |
| divider_gasket | 1 | 2 mm closed-cell EPDM |
| driver_gasket | 1 | 2 mm closed-cell EPDM |
| passive_radiator_gasket | 2 | 2 mm closed-cell EPDM |
| cable_gland | 1 | TPU 95A |
| base_skirt | 1 | ASA |
| bottom_service_plate | 1 | ASA |
| ballast_cartridge | 1 | ASA |
| ballast_cartridge_lid | 1 | ASA |

![Fastener identification](IMAGES/fastener_identification.png)

## Step 1: Identify and inspect the hardware

- Parts: Batch 1 Core rev4.1, HAT rev4.1, official Squircle upper stack
- Fasteners: none
- Tools: bright light; calipers
- Gasket/seal: none
- Action: Confirm the board revision labels. Reject Batch 2 / Satellite1.1 for this release. Inspect every printed sealing face and remove strings without rounding an edge.
- Pass: Correct Batch 1 hardware is present; no crack, warp, blocked bore, or damaged gasket land.
- Warning: Do not force or approximately place the Core. Its exact stack placement requires the physical official hardware.

![Step 1 - Identify and inspect the hardware](IMAGES/assembly_stage_01_identify.png)

## Step 2: Install and cold-check all M3 inserts

- Parts: main_cabinet, pressure_divider, base_skirt, ballast_cartridge, outer_shell
- Fasteners: H01 inserts
- Tools: temperature-controlled iron; M3 insert tip; square
- Gasket/seal: none
- Action: At 250-270 C, press each insert into its labeled blind bore until flush and square. Let every insert cool for five minutes. Thread an M3 screw by hand for three turns.
- Pass: No insert spins, tilts, protrudes, or blocks before three turns.
- Warning: Do not torque a hot insert. Fumes and the iron can burn; ventilate and use eye protection.

![Step 2 - Install and cold-check all M3 inserts](IMAGES/assembly_stage_02_inserts.png)

## Step 3: Wire and clamp the active driver

- Parts: main_cabinet, Dayton ND91-4, driver_gasket, active_driver_clamp_ring, JST-XH lead
- Fasteners: F04, 4 screws
- Tools: 2.0 mm hex; crimper or soldering iron; polarity tester
- Gasket/seal: G02
- Action: Mark the red conductor positive. Connect red to the terminal marked + and black to -. Face the terminals upward. Center G02, seat the driver from the -Y/front side, fit the clamp ring, and tighten F04 in two diagonal passes to 0.35 N m; never exceed 0.45 N m.
- Pass: Ring bottoms evenly; gasket is not visible in the bore; cone moves outward on a brief 1.5 V positive polarity pulse.
- Warning: Use only a brief low-voltage polarity pulse. Never connect a loose driver to the powered HAT.

![Step 3 - Wire and clamp the active driver](IMAGES/assembly_stage_03_driver.png)

## Step 4: Mass-match and clamp both passive radiators

- Parts: 2 SB12PACR-00, 2 passive_radiator_gaskets, 2 clamp rings, matched M6 washer stacks
- Fasteners: F05, 8 screws total
- Tools: 0.01 g scale; 2.0 mm hex
- Gasket/seal: G03, one per side
- Action: Weigh two identical tuning stacks to the value in reports/acoustics/summary.json. Secure one to each M6 post. Install radiators on +/-X with matching orientation, then tighten each F05 crosswise to 0.35 N m; never exceed 0.45 N m.
- Pass: Added masses match within 0.02 g; both rings bottom evenly; surrounds move freely and do not touch the shell keep-out.
- Warning: Unequal mass defeats reaction-force cancellation. Do not press on either cone.

![Step 4 - Mass-match and clamp both passive radiators](IMAGES/assembly_stage_04_radiators.png)

## Step 5: Route the cable, close the divider, and leak-check

- Parts: pressure_divider, divider_gasket, leak_test_adapter, cable_gland
- Fasteners: F03, 8 screws
- Tools: 2.0 mm hex; hand bulb; 0-500 Pa gauge; leak-detection solution
- Gasket/seal: G01; temporary adapter then G04
- Action: Pass both conductors through the divider. Fit the temporary adapter over them, place G01 without twists, and tighten F03 in a star pattern to 0.35 N m. Apply only 100-250 Pa with a hand bulb. Brush leak solution on external gasket seams; no bubbles are allowed. Vent, pull the adapter upward, and install G04 with its flange toward the electronics bay.
- Pass: No growing bubbles, abnormal diaphragm displacement, or audible leak; final gland cannot rotate or lift by finger force.
- Warning: Never use shop air, never exceed 250 Pa, and keep liquid away from electronics. This is a gross-leak screen, not an acoustic-Q measurement.

![Step 5 - Route the cable, close the divider, and leak-check](IMAGES/assembly_stage_05_sealing.png)

## Step 6: Install the base and retained ballast

- Parts: base_skirt, ballast_cartridge, 2 steel plates, ballast lid, bottom_service_plate
- Fasteners: F06, F07, F08
- Tools: 2.0 mm hex; scale
- Gasket/seal: none
- Action: Attach the base skirt with F07. Place both deburred dry plates flat in the cartridge; there must be no rocking. Install the lid with F06, insert the cartridge from below, and capture it with the bottom service plate using F08.
- Pass: Cartridge mass is approximately 1054 g; no plate moves when shaken gently; all four lid screws engage at least 3 mm.
- Warning: The steel stack is heavy. Keep fingers clear and do not operate the unit without the retained lid and service plate.

![Step 6 - Install the base and retained ballast](IMAGES/assembly_stage_06_ballast.png)

## Step 7: Install and lock the outer shell

- Parts: outer_shell; lower assembly
- Fasteners: F09, 4 screws with nylon washers
- Tools: 2.0 mm hex
- Gasket/seal: none
- Action: Align FRONT with -Y and slide the shell downward without touching either surround. Invert on a soft mat and install F09 through the bottom service plate into the shell bosses.
- Pass: Every slot is clear; shell has an even reveal and at least 2 mm moving-part clearance; no wire is visible near a cone.
- Warning: Stop if the shell contacts a clamp ring or surround. Do not flex the shell over an obstruction.

![Step 7 - Install and lock the outer shell](IMAGES/assembly_stage_07_shell.png)

## Step 8: Install the shroud and official Batch 1 upper stack

- Parts: electronics_shroud; official mid-plate, threads, PCB spacer, HAT/Core, top plate, buttons/diffuser, lock ring
- Fasteners: F01 and F02
- Tools: 2.0 mm hex; ESD-safe bench
- Gasket/seal: none; electronics bay is outside the acoustic chamber
- Action: Bolt the shroud to its four outboard bosses with F02. Seat the official mid-plate on the four measured divider bosses and install F01. Assemble the official Batch 1 PCB spacer, HAT/Core, top plate, buttons/diffuser, and lock ring in the official order. Connect the keyed JST-XH speaker plug before the top closes.
- Pass: Mid-plate sits on all four bosses; USB-C remains reachable; cable has service slack and cannot enter a moving-part envelope; buttons click and diffuser/LED apertures remain clear.
- Warning: Core placement is REQUIRES_PHYSICAL_VALIDATION. Follow the official Batch 1 instructions and stop at any collision; do not improvise a transform from the CAD envelope.

![Step 8 - Install the shroud and official Batch 1 upper stack](IMAGES/assembly_stage_08_upper.png)

## Step 9: Fit the anti-slip ring and complete inspection

- Parts: anti_slip_ring; complete assembly
- Fasteners: none
- Tools: hands; flashlight
- Gasket/seal: inspect G01-G04
- Action: Stretch the TPU ring evenly around the bottom rim. Set the unit upright and inspect all seams, fastener heads, slots, cable exits, buttons, and moving components.
- Pass: Unit stands without rocking; no rattle is heard during gentle handling; every fastener is present and every seal is continuously compressed.
- Warning: Do not power the unit until the commissioning checklist is ready.

![Step 9 - Fit the anti-slip ring and complete inspection](IMAGES/assembly_stage_09_final.png)
