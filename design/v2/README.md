# v2 — seamless industrial design

Exploratory work toward a v2 enclosure that reads as **one part** after
assembly. Nothing here is production geometry, nothing here is validated, and
nothing here is exported. It exists to settle the form before
`src/satellite1_ultra/geometry.py` is touched.

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

## What v2 does instead

One superellipse section family for the whole product, a vertical body, a
generous roll into a single flat top, and the official part dropped into that
plane dead flush with a 0.4 mm hairline so it can still lift out.

| | v1 | v2 |
|---|---|---|
| Footprint | 192 × 212 | 184 × 184 |
| Overall height | 237 mm | 269.5 mm |
| Section | rounded rectangle | superellipse n = 4.13 |
| Top | perched, 5 mm ledge | flush in a flat plane |
| Gross sealed prism | 3.966 L | 3.966 L |

The footprint shrinks on **both** axes and the sealed volume is unchanged, so
there is no acoustic cost. The extra height pays for the volume the narrower
plan gives up.

## Bed constraint

The v1 `outer_shell` is 192 × 212 mm and does **not** fit the target printer
(Ender 5, ~220 × 200 usable). The printability gate never caught this because
it assumes a 256 mm cube envelope. v2 is sized so the largest part is
184 × 184 mm. See task 5 / `reports/review/`.

## Files

- `v2_silhouette.py` — the profile, the section family, and the volume solve.
- `render_v2.py` — renders v2 against v1 from the shared camera set.

Run from the repo root with `.venv/bin/python design/v2/render_v2.py`.
