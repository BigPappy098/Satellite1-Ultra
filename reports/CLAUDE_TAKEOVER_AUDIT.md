# Claude takeover audit

Independent audit of the inherited Codex work, and the record of what was
repaired, replaced and continued.

- Audit date: 2026-07-27
- Inherited branch: `codex/bootstrap`, HEAD `8168c26`
- Working branch: `claude/codex-takeover`
- Codex history preserved: yes, nothing rewritten or deleted

---

## 1. Repository state as inherited

| Item | State |
|---|---|
| Branch | `codex/bootstrap`, 4 commits, no other branches or remotes |
| Working tree | dirty: `src/satellite1_ultra/validation.py`, `reports/validation/`, `exports/` untracked |
| Environment | Python 3.12.3, CadQuery 2.6.1, cadquery-ocp 7.8.1.1, hash-locked, builds |
| Official assets | 126 files, 392 MB, checksummed against `reference-assets/MANIFEST.csv` |
| Tests | 49 passed, 1 deep test passed |
| Lint | **failed** (2 unused imports in the untracked module) |
| Typecheck | passed |

The first action taken was a preservation commit (`1eb7f2c`) that records the
untracked Codex work verbatim, so every later change is auditable as a diff
against what Codex actually left.

## 2. What was genuinely complete

These were verified independently, not taken on trust:

- **Phase 0 — bootstrap.** Hash-locked lock file, working CadQuery/OCCT,
  STEP round-trip smoke test, CI skeleton. Confirmed by running it.
- **Phase 1 — official reference research.** 25 repositories inventoried, 11
  pinned, 126 assets preserved with repository, commit, path, license,
  retrieval date, byte count and SHA-256. All checksums re-verified. All 57
  preserved STEP files import through OCCT. Independent Gmsh reader confirmed.
- **Phase 2 — component research.** Seven active-driver candidates with
  manufacturer data, weighted scoring, published PDFs preserved. The
  active-driver conclusion is defensible (see §4.1).
- **Phase 3/4 — mechanical.** True parametric CadQuery B-rep throughout. No
  mesh, voxel, SDF or marching-cubes geometry anywhere. This was checked by
  reading every builder, not by reading the claim.

Good work was preserved. The rounded-prism primitives, the loft helpers, the
lumped-parameter acoustic solver, the export round-trip machinery, the
provenance manifest and the compensation-file concept are all Codex's and are
all still in use.

## 3. What was incomplete, stale or unsupported

| Finding | Severity | Detail |
|---|---|---|
| F-006 | HIGH | The CLI was a stub. `build`, `export`, `report` and `manual` printed "not yet implemented". `make release` therefore did nothing, and all four CI workflows invoked `make release`, so **CI could not have been detecting anything**. |
| F-007 | MEDIUM | `make clean` invoked `scripts/clean_generated.py`, which does not exist. |
| F-008 | MEDIUM | The on-disk validation reports were stale: they contained a key (`connected_air_before_damping_l`) that the current code no longer emits. |
| F-010 | MEDIUM | `PROJECT_STATUS.md` claimed "Simulation outputs and volume/leak/mass sensitivity plots are generated". `reports/acoustics/` did not exist. Unsupported claim. |
| F-011 | MEDIUM | The acoustic model used a hard-coded 3.20 L net volume while the validation gate computed 2.65 L. The two were never connected. |
| F-012 | LOW | `.gitattributes` declared Git LFS filters for `.step/.stl/.3mf/.pdf/.png`, but no object in the repository is an LFS pointer and git-lfs is not installed. A contributor with git-lfs would have produced a mixed object store and broken checksum verification. |
| F-013 | LOW | The 25 W chamber, wire covers and Batch 2 assets were preserved but the **Core board was never placed or checked** in any assembly. |

## 4. Engineering defects found by independent verification

These are the substantive findings. Each was confirmed by measurement on the
B-rep, not by inspection of the source.

### F-001 — CRITICAL — the enclosure was not sealed

The active driver and both passive radiators were mounted in a pocket cut
straight through the 4 mm wall, with the seat face formed by a separate 2 mm
ring fused *inside* the cavity. Between the carrier's outside diameter and the
pocket bore there was a 0.30 mm annular gap that ran from ambient, past the
component gasket, and into the sealed chamber — all the way around all three
components.

Measured on the inherited geometry: of the 816.6 mm³ annulus that should have
been solid material, **48.2 mm³ was material — 5.9 %**. The seat annulus behind
the gasket measured 28.8 mm³ solid out of 306 mm³.

Consequence: a passive-radiator alignment in a chamber vented to ambient. The
entire acoustic design premise was void, and no existing test could see it,
because a leak is an *absence* of material and the suite only looked for
unwanted *presence* of material.

**Repair.** Component mounts rebuilt on continuous internal pads: a solid disc
fused to the inside of the wall, then a blind counterbore, a through-bore and
blind insert bores cut into it. The gasket land is now one uninterrupted
annulus. New gate `sealing` proves it by solid-fraction probe; it now measures
1.000000 on all three mounts.

### F-002 — HIGH — fasteners fouled the driver opening

M3 insert bores were placed on the *component's own* bolt circle (Ø93.3) while
the through-bore was Ø89.1. The bore edge sits at r = 44.55 and a Ø4.6 insert at
r = 46.65 reaches inward to r = 44.35: the insert broke into the driver bore by
0.20 mm, measured at 1.40 mm³ per mount. Worse, the Ø9.4 boss around it
protruded **131.4 mm³ into the driver cutout**, where the driver basket goes.

The existing collision test did not catch it because the driver envelope was
modelled as a smooth cone that is narrower than the real basket immediately
behind the flange.

**Repair.** The component's bolt circle is no longer used for fastening. A
printed clamp ring bolts into inserts at Ø112 (driver) and Ø130 (radiator),
well outboard of the bore, and clamps the component flange against a gasket.
This also makes the mount driver-agnostic. The driver envelope was rebuilt with
a full-diameter collar for the first 8 mm behind the flange, so an intrusion of
this kind now registers. Insert-bore-versus-component-bore overlap is now
0.0000 mm³ and is asserted in `tests/test_geometry.py`.

### F-003 — HIGH — heat-set insert bores were drawn at the insert diameter

`insert_outer_diameter: 4.6` was used as the *hole* diameter everywhere. A
Ø4.6 insert dropped into a Ø4.6 hole has zero interference and no pull-out
strength. Correct practice for a Ø4.6 M3 insert is a Ø4.0–4.2 bore.

**Repair.** Separate `insert_bore_diameter` (4.2) from `insert_outer_diameter`
(4.6), and `insert_bore_depth` (7.2) from `insert_depth` (5.7) so no screw can
bottom on the bore floor. `tests/test_configuration.py` asserts the ordering.

### F-004 — HIGH — the official interface never made contact

The official mid-plate's downward seating plane is at **Z = -6.8 mm**, measured
on the preserved official B-rep (a 10,197 mm² planar face). The divider's
mounting bosses stopped at Z = -7.0. The interface had a 0.2 mm gap and never
seated, and a 110 mm plate carrying the whole electronics and top assembly was
supported on four unsupported Ø9.4 stalks 20.5 mm tall.

The existing test asserted only `overlap < 0.01` — "does not collide" is not
"seats".

**Repair.** `OFFICIAL_INTERFACE_Z = -6.8` is now measured from the official
B-rep by a test, not asserted. The boss tops are coplanar with it and are tied
together by a rib frame. The clearance gate requires face contact
(distance ≤ 0.01 mm) for this interface specifically.

### F-005 — HIGH — the components did not fit the cabinet

The conservative driver and radiator envelopes overlapped by 188.5 mm³. This is
geometric, not a modelling artefact: a 62.9 mm-deep driver on one face and two
38.3 mm-deep radiators on the perpendicular faces cannot coexist in a 160 mm
box. The required axial separation is ~34.5 mm; the available range allowed at
most 25.7 mm.

**Repair.** Cabinet depth increased from 160 mm to 180 mm, which removes the
conflict entirely (the driver's cone is then narrower than the radiator's reach
everywhere they share a Z band) and raises net volume. Component axes re-sited
so every clamp ring seats fully inside its own face.

### F-014 — HIGH — the passive-radiator alignment was wrong

The tuning target was 50 Hz for a driver with Fs 74 Hz and Vas 1.4 L in a
2.65 L box. That places Fb far below the driver's in-box resonance, so the
radiators barely contributed. Modelled f3 was **105 Hz** — only 19 Hz better
than the same driver sealed.

**Repair.** An alignment optimiser now sweeps Fb and selects the lowest -3 dB
corner subject to passband ripple ≤ 3.5 dB and an added mass the M6 post can
physically accept. It selects 59 Hz; the design target is 60 Hz and the acoustic
summary FAILs if the two diverge by more than 3 Hz. Modelled f3 is now
**56.9 Hz** against 132.1 Hz sealed.

### F-015 — MEDIUM — blind insert bores were capped

Introduced and caught during this work, worth recording because it shows the
export gate earning its place: the divider fastener compression stops were solid
discs fused directly over the insert bores, sealing them. The B-rep still
reported one valid solid; the STL mesh reported nine connected components,
because eight fully-enclosed voids had been created. The screws could never have
reached their inserts. Compression stops are now annular.

### Other repairs

- Gasket land width claimed 5.0 mm; the actual land was the 4 mm wall carrying
  a 2 mm-wide gasket. Now 3 mm of gasket on the 4 mm land, and the divider
  fasteners moved inboard so they cannot interrupt it.
- The grille cage's retention bridges passed through the base skirt wall
  (476 mm³) and the ballast tray (262 mm³).
- The electronics shroud touched the official mid-plate (0.0 mm clearance).
- Base-skirt fasteners bored 7.2 mm into an 8 mm acoustic floor, leaving 0.8 mm
  of pressure boundary. Now bossed and bored clear of it.

## 5. Mutation testing

Thirteen intentional defects were injected and the gates asserted to fail. Two
of them mutate the checked-in YAML on disk to exercise the configuration path;
all mutations are restored in a `finally` block and the restore is asserted.

**Three mutations initially survived**, which is the entire point of doing this:

1. Setting `pad_backing` to zero was not detected, because the blind-insert
   probe was sized from the very parameter it was testing. The probe now uses a
   fixed 2 mm depth.
2. A mounting pad narrower than its own seat was not detected. The `sealing`
   gate's continuity probe was correct but nothing checked the pad-versus-seat
   relation directly; a clearance check was added.
3. Corrupting the published driver cutout from 88.5 mm to 108 mm — which makes
   the bore larger than its seat and eliminates the gasket land entirely — was
   not detected by any gate. A gasket-land-radial-width check was added.

One sensitivity limit was established and is recorded rather than papered over:
moving the official interface plane anywhere between -6.8 mm and about 0 mm
produces **no** collision, because the divider bosses stand inside the
mid-plate's hollow centre. Errors in that band are caught by the clearance
gate's comparison against the measured official plane, not by the collision
gate.

All 13 mutations are now detected. No intentional defect was retained.

## 6. Verification method

Everything above is reproducible:

```bash
make check            # lint, strict typecheck, 97 fast tests
make validate         # the eleven quantitative gates
make mutation         # the 13 injected-defect tests
make test-deep        # independent-reader and export round-trip checks
make release          # all of the above plus every artifact
```

Geometric findings were measured with solid-fraction probes on the B-rep, in
the same way the new `sealing` and `wall_thickness` gates work, so any reader
can re-derive them.

## 7. Remaining risks

See [`docs/risk-register.md`](../docs/risk-register.md). The three HIGH entries
are: unpublished component flange thicknesses (R-01), the undetermined Core
board position in the official stack (R-02), and the fact that bass extension
is now limited by the driver's displacement rather than by the enclosure (R-03).

R-02 deserves emphasis. The published FutureProofHomes assets contain no
assembled Core+HAT model, and every stack-up trialled placed the Core inside
the official mid-plate solid. Rather than assert a placement that cannot be
supported, the Core is registered for provenance and size only, its placement
evidence is `UNDETERMINED`, and the enclosure is validated instead against a
Core-sized free volume in the electronics bay.
