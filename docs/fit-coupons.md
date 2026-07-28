# Fit-Coupon Inspection & Calibration Manual

This guide outlines how to measure your test coupons and apply physical compensations. This process adapts the CAD model to your specific 3D printer's shrinkage and extrusion profile, achieving an airtight, zero-force drop-fit before printing the final parts.

All expected dimensions are `DERIVED_FROM_OFFICIAL_CAD` or `DERIVED_FROM_MANUFACTURER_DRAWING`. Pass/fail limits are `ENGINEERING_ESTIMATE`.

---

## 🔧 Inspection Preparation

Before measuring:
1.  **Cooling Time:** Let your coupons cool to room temperature for at least **2 hours** on a flat surface. Measuring warm plastic will result in incorrect shrinkage values.
2.  **Calibrate Calipers:** Zero your digital calipers before every measurement.
3.  **No Post-Processing:** Do not sand or scrape any coupon surfaces before inspecting them (except for installing the heat-set inserts as part of the insert test).

---

## 📐 Coupon Inspection Schedule

| Coupon File | Feature to Measure | Expected Value | Acceptable Tolerances | Action / Compensation Parameter |
|---|---|---|---|---|
| **coupon_official_interface.3mf** | • Four mounting hole centers<br>• Recess boundary<br>• Official mid-plate drop-fit | • X: ±45.0534 mm<br>• Y: ±31.5467 mm<br>• Recess: 110.60 mm | • Center error ≤ 0.15 mm<br>• Drop fit: slide in smoothly with zero force and radial shake ≤ 0.30 mm | If tight/loose, adjust `xy_scale_correction_fraction` and `hole_diameter_offset` in `config/physical_compensation.yaml`. |
| **coupon_active_driver.3mf** | • Speaker seat Ø<br>• Internal bore Ø<br>• Seat depth<br>• Bolt circle diameter (BCD) | • Seat Ø: 103.80 mm<br>• Bore Ø: 88.70 mm<br>• Seat depth: 5.50 mm<br>• BCD: 112.00 mm | • Seat Ø: +0.20 / -0.00 mm<br>• Depth: ±0.10 mm<br>• Flange sits perfectly flat;<br>• M3 bolts align with clamp ring | Measure your Dayton ND91-4 speaker flange thickness. If it deviates from 3.00 mm, update `flange_thickness_mm` in `config/components.yaml` to adjust the pocket depth. |
| **coupon_passive_radiator.3mf** | • Radiator ledge Ø<br>• Seating surface Ø<br>• Internal bore Ø<br>• Seat depth | • Ledge Ø: 140.60 mm<br>• Seat Ø: 122.60 mm<br>• Bore Ø: 102.20 mm<br>• Seat depth: 11.50 mm | • Seat Ø: +0.20 / -0.00 mm<br>• Depth: ±0.10 mm<br>• Radiator sits flat;<br>• Clamp ring compresses fully | Measure your SB Acoustics SB12PACR-00 flange thickness. If it deviates from 4.00 mm, update `flange_thickness_mm` in `config/components.yaml`. |
| **coupon_heat_set_insert.3mf** | • Smallest insert bore accepting insert smoothly | • Bores range from Ø4.0 to Ø4.3 mm | • Insert installs perfectly flush, sits square, and survives a 250 N pull test | Adjust `insert_hole_diameter_offset` to match the best-performing diameter hole. |
| **coupon_gasket_base.3mf** & **coupon_gasket_cap.3mf** | • Assembled EPDM thickness under hard stop | • Target gasket compression height: 1.50 mm | • 1.45 to 1.55 mm height immediately after compression; no visible extrusion | Adjust `gasket_groove_depth_offset` if EPDM thickness is not tightly controlled. |
| **coupon_cable_passage.3mf** | • TPU gland insertion and wire fit | • Gland: Ø8.3 mm<br>• Passage: Ø8.0 mm | • Gland seats without tearing;<br>• Wires resist 20 N pull;<br>• Acoustic seal is airtight | Adjust `cable_passage_offset` if gland fits loosely or is impossible to press in. |

---

## 🔄 Calibration & Feedback Loop

Follow these steps to feed your physical measurements back into the CAD files:

```
[ Print Coupon ] ➔ [ Measure Deviation ] ➔ [ Edit config/*.yaml ] ➔ [ run `make release` ] ➔ [ Verify & Export ]
```

### 1. Identify the Deviations
Measure the printed coupon features. For example:
*   If the **active speaker seat Ø** is measured as `103.45 mm` instead of the expected `103.80 mm`, your printer is undersizing circles by **0.35 mm** due to material shrinkage or over-extrusion.

### 2. Update Configuration Files
Open `/config/physical_compensation.yaml` and modify the parameters.

*   `xy_scale_correction_fraction`: Adjust this parameter to scale the X and Y axes globally to account for plastic shrinkage (e.g., change `1.0` to `1.0035` if your parts shrink by 0.35%).
*   `hole_diameter_offset`: Positive values will enlarge circular cutouts. If holes are too small by `0.15 mm`, set this to `0.15`.
*   `insert_hole_diameter_offset`: Sets the specific target diameter for heat-set brass inserts.
*   `gasket_groove_depth_offset`: Sets the height offset for compression stop control.

### 3. Regenerate the Models
In your terminal, run:
```bash
make release
```
This triggers the full automated pipeline:
*   Imports your modified YAML configurations.
*   Regenerates all part designs (cabinet, clamp rings, coupons, etc.) with custom offsets.
*   Re-runs the mechanical validation tests to ensure no collisions were introduced.
*   Re-exports fresh STEP, STL, and 3MF files with your unique printer compensation!

---

## ⚠️ Important Calibration Rules
*   **Do Not scale files in your slicer.** Slicer scaling scales the entire object uniformly, which ruins critical localized tolerances (like the wall thickness of the speaker bosses or the exact M3 screw hole clearance). Let the CAD model handle scaling and hole offsets.
*   **Keep your filament dry.** Humid filament prints larger, rougher walls, and degrades circular tolerances. Perform all coupon tests using the exact spool of dry filament you will use for the final speaker cabinet.
