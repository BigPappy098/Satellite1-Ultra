# 🔊 Satellite1-Ultra Smart Speaker Enclosure

**Satellite1-Ultra** is an open-source, fully serviceable, high-fidelity passive-radiator smart-speaker enclosure designed specifically for the official **FutureProofHomes Satellite1 development kit**. 

The authoritative manufactured geometry is compiled from parametric Python/CadQuery B-rep source, with exact volumetric control, airtight pressure boundaries, and an integrated industrial design shell.

![Satellite1 Ultra](reports/renders/assembly_iso.png)

---

## 🚦 Project Status

**STATUS:** 🟢 `DIGITAL_PROTOTYPE_READY` | 🟡 `REQUIRES_PHYSICAL_VALIDATION`

*   **CAD / Digital Gates:** **100% COMPLETE & PASSING.** All 11 digital validation gates (interferences, volume, clearances, seal continuously, printability) are mathematically verified.
*   **Physical Gates:** In progress. Awaiting user physical verification of coupon print tolerances and acoustic sweep measurements. (See [Release Checklist](docs/release-checklist.md)).
*   **Audit logs:** Read our full independent analysis in [`reports/PROJECT_STATUS.md`](reports/PROJECT_STATUS.md).

---

## 🎯 Printing & Assembly Gateway

To make your physical build as straightforward and successful as possible, follow our dedicated, step-by-step documentation pipeline:

```
[ STEP 1: Calibrate ] ➔ [ STEP 2: Compile CAD ] ➔ [ STEP 3: 3D Print ] ➔ [ STEP 4: Assemble ]
  - docs/print-guide.md     - config/physical_compensation.yaml   - docs/print-guide.md     - docs/assembly-guide.md
  - docs/fit-coupons.md     - run `make release`                  - exports/3mf             - docs/disassembly-guide.md
```

1.  **🚀 Step 1: Calibrate Print Tolerances First**
    *   Do **not** print the main cabinet first. Print the 8 fit coupons first to check your printer’s shrinkage with ASA or PETG.
    *   Read the **[3D Printing Guide & Calibration Gateway](docs/print-guide.md)** for orientation and parameter profiles.
    *   Follow the **[Fit-Coupon Inspection & Calibration Manual](docs/fit-coupons.md)** to measure print deviations using calipers.
2.  **⚙️ Step 2: Compile Your Custom CAD Models**
    *   Input your caliper-measured deviations directly into `config/physical_compensation.yaml`.
    *   Run `make release` in your terminal to automatically regenerate and re-verify all part geometries (and exports) compensated exactly for your printer!
3.  **🖨️ Step 3: Print the Full Part Set**
    *   Retrieve your custom-compensated `.3mf` or `.stl` files from `exports/3mf/` and `exports/stl/`.
    *   Follow the **[3D Printing Guide](docs/print-guide.md)** to print the cabinet, outer shell, clamps, shroud, and TPU base.
4.  **🔧 Step 4: Assemble & Wire the Speaker**
    *   Follow the **[Assembly Guide](docs/assembly-guide.md)** for detailed phase-by-step instructions, complete with beautiful exploded assembly renders, wiring guides, and torque specifications.
    *   Refer to the **[Disassembly Guide](docs/disassembly-guide.md)** if you ever need to service or inspect internal parts.
    *   Refer to the **[Maintenance Guide](docs/maintenance-guide.md)** for routine care, cleaning, and performance checkups.

---

## 📊 System Overview & Specifications

| Property | Value | Evidence / Verification |
|---|---|---|
| **Overall Envelope** | 192 x 212 x 237 mm | `VERIFIED_DIGITALLY` (Fits 256 mm build envelope) |
| **Acoustic Cabinet** | 160 x 180 mm section | `VERIFIED_DIGITALLY` |
| **Net Acoustic Volume**| **3.447 Liters** | `VERIFIED_DIGITALLY` (Derived from OCCT air boundary) |
| **System Tuning (fb)** | **60 Hz** | `ENGINEERING_ESTIMATE` (Acoustic model simulation) |
| **Modelled f3** | **56.9 Hz** (Unparalleled bass extension vs. 132 Hz sealed) | `ENGINEERING_ESTIMATE` |
| **Acoustic Design** | 1 active front driver + 2 opposed lateral passive radiators | `DERIVED_FROM_MANUFACTURER_DRAWING` |
| **Active Driver** | Dayton Audio ND91-4 | `DERIVED_FROM_MANUFACTURER_DRAWING` |
| **Passive Radiators** | 2 x SB Acoustics SB12PACR-00 (with added 1.07 g tuning mass) | `DERIVED_FROM_MANUFACTURER_DRAWING` |
| **Assembled Mass** | **~3.49 kg** (removable 1.05 kg dry steel ballast stack) | `ENGINEERING_ESTIMATE` (For physical vibration isolation) |
| **Static Tipping Angle**| **49.6°** | `ENGINEERING_ESTIMATE` (Very low center of gravity) |
| **Board Stack** | Raspberry Pi Core Board + HAT Board (Batch 1, rev4.1) | `DERIVED_FROM_OFFICIAL_CAD` |
| **Upper Mechanics** | Official Squircle mid-plate, top plate, diffuser, lock ring | `DERIVED_FROM_OFFICIAL_CAD` (Unmodified drop-fit) |

---

## 📐 Coordinate System & Datum Origin

To maintain absolute dimensional accuracy across files, we use a single authoritative datum origin:
*   **Origin:** Exact center of the official mid-plate interface plane.
*   **+Z Axis:** Upward toward the microphone array.
*   **-Z Axis:** Downward into the acoustic cabinet.
*   **-Y Axis:** Active-driver front.
*   **±X Axis:** Opposed passive radiators.

The official mid-plate underside sits at `Z = -6.8 mm`, which is presented precisely by our custom-printed pressure divider.

---

## 🛠️ Developer Setup & Clean Build

All dependencies are locked, hash-verified, and compiler-free, requiring Python 3.12.

### Local Development
```bash
make bootstrap     # Create python virtual environment and install pinned requirements
make release       # Run the entire pipeline: lint, format, typecheck, test, build, acoustics, export, document
```

### Individual Pipeline Stages:
```bash
make build         # Compile and verify all custom B-rep parts
make validate      # Execute all 11 quantitative validation gates (collisions, clearance, etc.)
make acoustics     # Run acoustic model and output sensitivity curves
make exports       # Generate STEP, STL, and 3MF files, plus assemblies
make renders       # Generate high-fidelity CAD renders and cross-sections
make drawings      # Compile per-part inspection drawing sheets (PDFs)
make docs          # Rebuild BOM, schedules, guides, and checklists
make manual        # Compile the unified PDF build manual
make mutation      # Run mutation suite to test validation gate sensitivity
make clean         # Wipe all generated artifacts
```

### Docker Sandbox Build
```bash
docker build -t satellite1-ultra .
docker run --rm -v "$PWD:/work" satellite1-ultra make release
```

---

## 📦 Deliverables & Workspace Directory

| Deliverable | Description | File / Folder |
|---|---|---|
| **Parametric CAD Source** | Authoritative Python geometry definitions | `src/satellite1_ultra/geometry.py` |
| **Manufacturing Exports** | STEP, STL, and 3MF print-ready models | `exports/step/`, `exports/stl/`, `exports/3mf/` |
| **STEP Assemblies** | Complete, exploded, and functional assemblies | `exports/assembly/` |
| **Fit-Test Coupons** | Printable test couplers | `exports/*/coupon_*` |
| **Validation Reports** | Verification outputs for all gates | `reports/validation/` |
| **Acoustic Figures** | Sensitivity, impedance curves, and logs | `reports/acoustics/` |
| **Renders & Cuts** | High-fidelity visuals and sectional cross-sections | `reports/renders/` |
| **Inspection Sheets** | Part-specific engineering drawing sheets | `reports/drawings/` |

---

## ⚖️ License

*   **Hardware Design & Geometry:** Licensed under **CERN-OHL-S-2.0** (Open Hardware License).
*   **Software Utilities:** Provided under the **Apache-2.0** license.
*   **Third-Party Assets:** Reference assets retain their original manufacturer licenses and are mapped in `reference-assets/MANIFEST.csv`.
