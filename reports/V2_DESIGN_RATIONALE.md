# v2 — seamless industrial design

Why the v2 enclosure is shaped the way it is. The geometry itself now lives in
`src/satellite1_ultra/geometry.py` and is exported and gated like everything
else; this document records the reasoning and the measurements behind it so the
decisions are not lost.

**Nothing in v2 has been physically built or measured.** Every figure here is
exact CAD.

## Why v1 does not look like one part

Three separate causes, all measured rather than assumed:

1. **Different curve families.** The official Satellite1 squircle is a true
   superellipse, `|x/a|^n + |y/a|^n = 1` with **n ≈ 4.13** (max fit error
   0.38 mm across the quarter, measured off the official lock ring). Every part
   in v1 is built from `rounded_prism` — straight sides plus circular corners —
   which best-fits the same profile at 1.00 mm error, roughly three times
   worse. The body and the top are not merely different sizes; their corners
   have fundamentally different curvature.
2. **A 5 mm ledge.** `electronics_shroud` tapers to 120 mm square while the
   official part is 110 mm square, and its docstring deliberately leaves "one
   controlled concentric reveal at each end". Three visible steps in total.
3. **A false landing height.** The official stack is only 110 mm square from
   z = −7 upward. Below that it is a 96.5 mm step and then a 44 mm spigot, both
   of which are meant to be swallowed by the enclosure.

## The v2 form

One superellipse section family for the whole product, a vertical body, a
generous roll into a single flat top, and the official part dropped into that
plane flush to **0.005 mm** with a 0.4 mm hairline so it still lifts out.

| | v1 | v2 |
|---|---|---|
| Footprint | 192 × 212 | 184 × 184 |
| Overall height | 237 mm | 268.6 mm |
| Section | rounded rectangle | superellipse n = 4.13 |
| Top | perched, 5 mm ledge | flush in a flat plane |
| Gross sealed prism | 3.966 L | 3.968 L |

The footprint shrinks on **both** axes and the sealed volume is unchanged, so
there is no acoustic cost. The extra height pays for the volume the narrower
plan gives up.

Grille openings appear only over the driver (−Y) and the two radiators (±X);
the rest of the skin is smooth. The driver and both radiators share one axis
height (z = −117, the centre of the visible silhouette) so the three windows
read as a single band. The +Y rear face is left solid.

## Splitting the skin

The body is 268.6 mm tall. Printed in one piece it needs 269 mm of Z and risks
losing a very long print to a single failure, so the skin splits into three
segments joined by lapped rabbets.

| Segment | Print size | Contains |
|---|---|---|
| `shell_base` | 184 × 184 × 79.4 | bottom roll, base interface |
| `shell_grille` | 184 × 184 × 146.0 | the entire grille band |
| `shell_crown` | 184 × 184 × 67.1 | top roll, flat top, official pocket |

Seams sit at z = −184 and z = −50, which is **5 mm clear** of the grille
windows (they span −179 to −55). Nothing grazes a window edge, and the whole
grille field lives in one segment.

### The joint

- **Lapped rabbet**, 12 mm engagement. The wall thickens inward from 3 mm to
  5 mm across the joint and splits down the middle, so each side keeps 2.5 mm.
- **0.25 mm per-side sliding clearance** at the face, 0.30 mm at the corner
  (the superellipse scales the offset by 1.202 at 45°).
- **The outer surface is continuous.** The only visible mark is a deliberate
  0.3 × 0.6 mm relief cut equally from both sides.
- **No hardware at the seams.** The radial gap to the cabinet is 9.0 mm at the
  faces and 10.8 mm at the corners — too little for an M3 boss. Instead
  `shell_crown` bolts to the pressure divider and `shell_base` to the base
  skirt, and `shell_grille` is clamped between them. The segment carrying the
  entire visible grille has no fasteners of its own.

A deliberate shadow line is a design decision, not a compromise. A bare butt
joint would show FDM layer registration error as a ragged step that reads as
accidental; a consistent 0.3 mm relief reads as intentional. Under the fabric
wrap the question is moot — nothing shows at all.

## Microphone isolation — read this before building it

The mic array rides on the official stack. That stack bolts to the divider,
which bolts to the cabinet the driver is mounted in: a direct mechanical path
from a much louder woofer to the microphones. Structure-borne vibration is the
failure mode worth designing against, because acoustic echo cancellation
handles the *linear* airborne path well and is defeated by vibration-induced
nonlinearity.

The geometry here provides for it: divider boss tops drop to z = −8.8, a
counterbore takes the body of a TPU 95A isolation bushing, and the bushing's
2 mm flange restores the official seat to exactly −6.8 so the flat top stays
flush.

**But an ordinary M3 screw defeats it.** The screw clamps in parallel with the
elastomer, and it is far stiffer:

| Path | Stiffness |
|---|---|
| M3 screw in tension (10 mm grip) | 1.005 × 10⁸ N/m |
| Four TPU flanges in compression | 2.853 × 10⁶ N/m |

The screw is **35× stiffer**, so the elastomer carries only **2.8%** of the
load path and the isolation does essentially nothing.

The fix is a fastener change, not a geometry change: **M3 shoulder screws**.
The shoulder bottoms on a hard face in the divider boss, and the official stack
is captured on the elastomer with the head clearing it, so no clamping load
passes through the plate. The counterbore and bushing already built here are
exactly what that needs.

Open item: the shoulder length must exceed the counterbore + flange + local
mid-plate thickness by 0.2–0.4 mm, so the plate is captured but not clamped.
That last dimension still has to be measured off the official CAD.

## Fabric wrap (optional finish)

The same shell serves both finishes — the grille windows stay acoustically open
under cloth, and the wrap hides every seam and layer line.

1. Print the shell segments with `fabric_grooves=True`. This adds a 2.2 × 1.5 mm
   retention channel just inside each roll. It is **off by default**, because on
   the bare printed finish it reads as a horizontal seam line.
2. Use acoustically transparent speaker grille cloth. Hold a piece to your mouth
   and breathe through it — if you feel noticeable resistance, it will audibly
   dull the treble.
3. Assemble the three segments first, so the wrap crosses the seams unbroken.
4. Wrap with the fabric's stretch running **around** the body, not up it. Keep
   even tension; a squircle shows tension variation at the corners more than a
   cylinder does.
5. Tuck both edges into the channels and secure with a thin bead of contact
   adhesive inside the channel only. Do not let adhesive wick into the grille
   windows — it stiffens the cloth and changes its acoustic transparency.

## Bed constraint

The v1 `outer_shell` is 192 × 212 mm and the printability gate never checked it
against a real bed — see `reports/review/2026-07-29-claude-v2-review.json`,
PRINT-001 and PRINT-002. Every v2 part is ≤ 184 × 184 mm and ≤ 146 mm tall.

## Where the geometry lives

- `geometry.superellipse_wire` / `section_prism` / `section_ring` — the section
  family, `SECTION_EXPONENT = 4.13`.
- `geometry.skin_body` / `skin_shell` / `skin_segments` — the monolith skin and
  its three lapped segments, plus the `*_fabric` variants.
- `geometry.mic_isolation_bushing` — the TPU isolator.
- `validation.printability_report` — the per-axis bed gate that replaced the
  scalar 256 mm check.

Regenerate everything with `make release`.
