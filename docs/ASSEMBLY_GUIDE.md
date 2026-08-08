# Illustrated Assembly Guide

Front is -Y, rear is +Y, left/right radiators are -X/+X, and +Z points
toward the microphones. All torque values are `ENGINEERING_ESTIMATE`
until the selected insert/process is pull-tested.

![Exploded part identification](IMAGES/exploded_parts_identification.png)

## Exploded-view part key

| Exact part name | Qty | Material |
|---|---|---|
| anti_slip_ring | 1 | TPU 95A |
| shell_base | 1 | ASA |
| shell_grille | 1 | ASA |
| shell_crown | 1 | ASA |
| shell_base_fabric | 1 | ASA |
| shell_grille_fabric | 1 | ASA |
| shell_crown_fabric | 1 | ASA |
| main_cabinet | 1 | ASA |
| pressure_divider | 1 | ASA |
| mic_isolation_bushing | 4 | TPU 95A |
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
| official_mid_plate | 1 | ASA (PETG alternative) |
| official_mid_plate_threads | 1 | ASA (PETG alternative) |
| official_pcb_spacer | 1 | ASA (PETG alternative) |
| official_lock_ring | 1 | ASA (PETG alternative) |
| official_top_plate | 1 | ASA (PETG alternative) |
| official_top_plate_snap_in_diffuser_ring | 1 | ASA (PETG alternative) |

![Fastener identification](IMAGES/fastener_identification.png)

## Step 1: Identify and inspect the hardware

- Parts: Batch 1 Core rev4.1 and HAT rev4.1; O01 official_mid_plate; O02 official_mid_plate_threads; O03 official_pcb_spacer; O04 official_lock_ring; O05 official_top_plate; O06 official_top_plate_snap_in_diffuser_ring
- Fasteners: none
- Tools: bright light; calipers
- Gasket/seal: none
- Action: Confirm the board revision labels. Reject Batch 2 / Satellite1.1. Check off all six required official filenames in OFFICIAL_PARTS/REQUIRED_SINGLE_MATERIAL and every required custom 3MF in the Printing Guide. Inspect every sealing face and remove strings without rounding an edge.
- Pass: Correct Batch 1 hardware and every required printed part are present; no crack, warp, blocked bore, or damaged gasket land.
- Warning: Do not force or approximately place the Core. Its exact stack placement requires the physical official hardware.

![Step 1 - Identify and inspect the hardware](IMAGES/assembly_stage_01_identify.png)

## Step 2: Install and cold-check all M3 inserts

- Parts: main_cabinet, pressure_divider, base_skirt, ballast_cartridge, skin segments
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
- Action: Mark the red conductor positive. Connect red to the terminal marked + and black to -. Look into the driver opening before you fit anything: at the top, in line with the topmost corner of the recess, the wall is notched wider. The driver's terminals sit in line with one of its four corner tabs and stand proud enough that the basket will not pass the opening anywhere else, so rotate the driver until its terminals point straight up into that notch. It only goes in one way round, and that is also the way the wire needs to leave to reach the cable passage in the divider above. Center G02, seat the driver from the -Y/front side, fit the clamp ring, and tighten F04 in two diagonal passes to 0.35 N m; never exceed 0.45 N m.
- Pass: Ring bottoms evenly; G02 is continuous all the way round and covers all four unused driver mounting holes; cone moves outward on a brief 1.5 V positive polarity pulse.
- Warning: Use only a brief low-voltage polarity pulse. Never connect a loose driver to the powered HAT.

![Step 3 - Wire and clamp the active driver](IMAGES/assembly_stage_03_driver.png)

## Step 4: Mass-match and clamp both passive radiators

- Parts: 2 passive radiators, 2 passive_radiator_gaskets, 2 clamp rings, matched tuning masses
- Fasteners: F05, 8 screws total
- Tools: 0.01 g scale; 2.0 mm hex
- Gasket/seal: G03, one per side
- Action: Trim and weigh two identical tuning masses to the value in reports/acoustics/summary.json, matching them within 0.02 g. Apply one centred on each radiator mass post. Install radiators on +/-X with matching orientation, then tighten each F05 crosswise to 0.35 N m; never exceed 0.45 N m.
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
- Pass: Cartridge mass matches the steel stack listed in BOM.csv; no plate moves when shaken gently; all four lid screws engage at least 3 mm.
- Warning: The steel stack is heavy. Keep fingers clear and do not operate the unit without the retained lid and service plate.

![Step 6 - Install the base and retained ballast](IMAGES/assembly_stage_06_ballast.png)

## Step 7: Stack the three outer skin segments

- Parts: shell_base, shell_grille, shell_crown; lower assembly
- Fasteners: F09, 4 screws with nylon washers; F02, 4 screws into the divider
- Tools: 2.0 mm hex
- Gasket/seal: none
- Action: Work bottom to top. Slide shell_base up over the cabinet with FRONT at -Y, invert on a soft mat, and install F09 through the bottom service plate into its four bosses. Stand the unit back up. Press shell_grille down onto the exposed lap until its outer face meets the segment below; the four crush ribs give a firm, even resistance and the joint closes on 0.15 mm of interference, so it should need hand pressure and stay put. Press shell_crown on the same way, then bolt it down onto the divider's four bosses with F02. Check that all three grille windows line up with the driver and both radiators.
- Pass: Both seams show an even hairline shadow line all round with no step you can catch a fingernail on; no segment rocks or rattles when the body is tapped; at least 2 mm clearance from every clamp ring and surround; no wire visible through a window.
- Warning: Do not force a segment on if it binds — lift it off and check for a stringing artefact on the lap or a crush rib that printed proud. Never flex a segment over an obstruction. The crown must be bolted to the divider before the official stack goes on, because its tabs sit underneath.

![Step 7 - Stack the three outer skin segments](IMAGES/assembly_stage_07_shell.png)

## Step 8: Fit the mic isolators and the official Batch 1 upper stack

- Parts: mic_isolation_bushing x4; O01-O06 official prints; Batch 1 HAT/Core
- Fasteners: F01 (M3 x d4 shoulder screws, 16 mm shoulder), F10, F11; 4 of each
- Tools: 2.0 mm hex; ESD-safe bench
- Gasket/seal: none; electronics bay is outside the acoustic chamber
- Action: Press one TPU isolation bushing into each of the four divider counterbores, flange up. Seat O01 on the four bushing flanges — it must rest on elastomer, not on printed plastic. Install F01 and tighten until each shoulder bottoms firmly on the counterbore floor; the screw head then stops 0.3 mm above the plate and the plate stays floating on the TPU. Snap O06 into O05 (or use both O07/O08 during a multi-material O05 print; never install O06 and O08 together). Align O03's taller standoffs with the I/O side and locate the HAT. Install the Core/HAT using the official Batch 1 sequence. Align the logos and I/O on O04/O05, engage the snaps, and rotate the lock ring. Align O02's four nubs with O01 and keep I/O toward rear/+Y. Connect the keyed JST-XH speaker plug before closure.
- Pass: The official top sits flush with the surrounding flat top — you should feel a hairline, not a step or a lip. The upper stack has a barely perceptible give when pressed, which is the isolation working. USB-C remains reachable; cable has service slack and cannot enter a moving-part envelope; buttons click and diffuser/LED apertures remain clear.
- Warning: F01 must be M3 x d4 shoulder screws, not ordinary M3 screws. An ordinary screw clamps in parallel with the elastomer at roughly 35 times its stiffness, so the TPU carries under 3% of the load path and the isolation does nothing at all. If the plate feels rock solid, you have the wrong screws. Core placement is REQUIRES_PHYSICAL_VALIDATION: follow the official Batch 1 instructions and stop at any collision.

![Step 8 - Fit the mic isolators and the official Batch 1 upper stack](IMAGES/assembly_stage_08_upper.png)

## Step 9: Fit the anti-slip ring and complete inspection

- Parts: anti_slip_ring; complete assembly
- Fasteners: none
- Tools: hands; flashlight
- Gasket/seal: inspect G01-G04
- Action: Stretch the TPU ring evenly around the bottom rim. Set the unit upright and inspect all seams, fastener heads, slots, cable exits, buttons, and moving components.
- Pass: Unit stands without rocking; no rattle is heard during gentle handling; every fastener is present and every seal is continuously compressed.
- Warning: Do not power the unit until the commissioning checklist is ready.

![Step 9 - Fit the anti-slip ring and complete inspection](IMAGES/assembly_stage_09_final.png)
