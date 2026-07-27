# Official FutureProofHomes source audit

All statements in this report are `DERIVED_FROM_OFFICIAL_CAD` unless another
evidence label is stated.

## Retrieval baseline

- Retrieval date: 2026-07-27
- Organization: `FutureProofHomes`
- Official organization repositories found: 25
- Repositories classified as relevant and cloned: 11
- Official CAD/manufacturing assets preserved: 126
- Official STEP files imported through CadQuery/OCCT: 57
- OCCT import/topology/finite-bound failures: 0
- Independent Gmsh/OpenCascade import of selected mid-plate: passed

The repository pins, URLs, branches, licenses, retrieval dates, and relevance
decisions are in `references/FUTUREPROOFHOMES_REPOSITORIES.csv`. Byte-for-byte
asset provenance is in `reference-assets/MANIFEST.csv`. Exact solid counts,
volumes, and bounds are in
`reports/geometry/official_step_inventory.csv`.

## Relevant repositories

- `Satellite1-Enclosures`: authoritative enclosure, upper stack, board reference
  CAD, STEP, STL, and slicer projects.
- `Satellite1-Hardware`: board revisions, schematics, KiCad source, and detailed
  board STEP models.
- `Satellite1-ESPHome`: TAS2780/PCM5122 control, PD-aware amplifier power mode,
  audio routing, and software/DSP integration.
- `Satellite1-XMOS`: microphone/AEC/audio-processing firmware and signal path.
- `Documentation`: official hardware, enclosure, assembly, music/DSP, and
  firmware documentation.
- `home-assistant-voice-pe`: Satellite1 integration fork.
- `Satellite1-HA-Automations`: official user/control integration context.
- `Satellite1-RPi`, `Satellite1-RPi-SDK`, `Satellite1-RPi-Image`, and
  `Satellite1-RPi-Setup`: alternative-core and expansion constraints.

The full organization was searched. Other repositories were excluded from
dimensional scope because they concern the Nexus base station, general Wyoming
software, Music Assistant, unrelated wake-word training, or organization
administration.

## Official mechanical inventory

The preserved enclosure set includes:

- Cylindrical first-generation enclosure, threaded speaker chamber, UFO
  electronics enclosure/base, lock ring, wire covers, speaker stands, and
  adapters for Dayton RS75-4, GRS 3FR-4, and Tectonic TEBM46C-20N.
- Squircle top plate variants, multi-material buttons, diffuser rings, PCB
  spacer, lock ring, mid-plate, threaded mid-plate, five wire-cover sizes,
  3 W/15 W/25 W chambers, anti-slip ring, legs, and speaker plates for Dayton
  PC83-4/RS75-4, FaitalPRO 3FE25, GRS/Visaton, and Tectonic BMR.
- In-ceiling enclosure.
- Current Satellite1.1 OEM single/multi-material top plates, small enclosure,
  large front/back chamber, Wi-Fi pocket, bass port, LD2450 pocket, and screw
  guide.
- Board assemblies for public Batch 1 and Batch 2, plus detailed Hat/Core/Shoe/
  Shim board exports from the hardware repository.

## Hardware revisions

The hardware repository defines:

- Public Batch 1: Hat rev4.1 / R2024.12.06 and Core rev4.1 / R2024.12.06.
- Public Batch 2: Hat rev6.1 / R2025.03.18 and Core rev5.1 / R2025.03.18.
- Intermediate Hat rev4/rev5/rev6 and Core rev4/rev4.2/rev5 are prototypes.
- Shoe rev1 and Shim rev1 are prototypes.

The original small square development-kit enclosure is the official Squircle
family. `ENGINEERING_ESTIMATE`: a user describing that enclosure most likely
owns public Batch 1. The official documentation now warns that Squircle is not
compatible with Satellite1.1 kits shipped with the required external Wi-Fi
antenna after 2026-02-17.

Satellite1 Ultra therefore selects Batch 1 for the baseline but keeps board
revision and adapter selection parametric. Batch 2 support is planned through a
swappable external-antenna/USB-C service adapter; it is explicitly
`REQUIRES_PHYSICAL_VALIDATION`.

## Reused upper stack

The authoritative baseline reuses the official Squircle:

- top plate and multi-material button/diffuser geometry
- PCB spacer
- lock ring
- mid-plate
- threaded mid-plate

No microphone, LED, button, PCB mounting, or threaded-interface geometry is
redrawn. These parts remain official unmodified B-reps in the reference
assembly.

## Master coordinate system

The 25 W official speaker chamber ends at Z=140.8 mm, where the mid-plate seats.
This centered rim is the product interface datum:

- origin: X=0, Y=0, Z=140.8 mm in the official Squircle assembly
- master transform: translation (0, 0, -140.8 mm)
- +Z: official upper stack and microphones
- -Z: Satellite1 Ultra acoustic enclosure
- -Y: active-driver front
- ±X: opposed passive radiators

This convention places the official top assembly approximately from Z=-26.5 mm
(mid-plate intrusions) to Z=+17.1 mm (top plate). Negative mid-plate features are
allowed to intrude into the isolated electronics service region but not through
the acoustic pressure divider.

## Board alignment evidence

The official Squircle PCB spacer mounting holes are at X=±29 mm and Y=±24.5 mm.
The Batch 1 HAT mounting-hole pattern is X=±29 mm and Y=-23.501/+25.499 mm,
showing the board CAD datum is offset +0.999 mm in Y. Translating the HAT by
Y=-0.999 mm aligns all four holes. The spacer top is official Z=150.0 mm; the
HAT PCB bottom is Z=0, giving placed HAT translation Z=+150.0 mm in official
coordinates or +9.2 mm in the master system.

## License conclusions

`Satellite1-Enclosures` and `Satellite1-Hardware` declare CERN-OHL-S-2.0. Their
preserved files retain that license. Documentation and firmware repositories
retain their repository licenses; no firmware or documentation binary is
redistributed as manufactured geometry.

