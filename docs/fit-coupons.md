# 📐 Step-by-Step Printer Calibration & Model Compilation Manual

Welcome to the **Satellite1-Ultra Calibration Manual**. This guide is designed to be completely foolproof. By printing a few quick test parts (coupons) and measuring them with your digital calipers, you will adapt the entire CAD model to your specific 3D printer's shrinkage (ASA/PETG) and physical hardware dimensions.

Follow this guide step-by-step before printing any of the main, full-sized cabinet parts!

---

## 📝 Part 1: The Printable Calibration Worksheet

Before starting, grab a pen and a piece of paper, and copy down this worksheet. As you measure each printed coupon, write your physical caliper reading in the **"Your Measurement"** column.

| Calibration Step | Coupon File | What to Measure | nominal / Target | Your Measurement (mm) | Wizard Input |
|---|---|---|---|---|---|
| **1. XY Shrinkage** | `coupon_official_interface.3mf` | Inside width of the main square pocket recess | **110.60 mm** | \_\_\_\_\_\_\_\_\_\_\_\_ mm | Enter this exact number |
| **2. Z-Axis Height** | `coupon_official_interface.3mf` | Vertical height of the outer square lip | **3.00 mm** | \_\_\_\_\_\_\_\_\_\_\_\_ mm | Enter this exact number |
| **3. Screw Holes** | `coupon_active_driver.3mf` | Inside diameter of any outer M3 clearance hole | **4.00 mm** | \_\_\_\_\_\_\_\_\_\_\_\_ mm | Enter this exact number |
| **4. Brass Inserts**| `coupon_heat_set_insert.3mf` | Which hole diameter (4.0, 4.1, 4.2, 4.3) fits best? | **4.20 mm** | \_\_\_\_\_\_\_\_\_\_\_\_ mm | Select Choice (1 to 4) |
| **5. Cable Gland** | `coupon_cable_passage.3mf` | How snug is the printed TPU gland inside the hole? | **Snug Fit** | (Circle) OK / Tight / Loose | Select Choice (1 to 3) |
| **6. Active Driver**| *Physical Dayton ND91-4* | Metal/rubber flange thickness on your driver | **3.00 mm** | \_\_\_\_\_\_\_\_\_\_\_\_ mm | Enter this exact number |
| **7. Passive PR** | *Physical SB Acoustics* | Outer plastic flange thickness on your radiator | **4.00 mm** | \_\_\_\_\_\_\_\_\_\_\_\_ mm | Enter this exact number |

---

## 🔍 Part 2: Step-by-Step Coupon Measurement Guide

Let's walk through every coupon, explaining how to print it, what it does, and exactly how to measure it with your calipers.

---

### Step 2.1: XY Shrinkage & Z-Axis Lip Calibration
*   **Print this file:** `exports/3mf/coupon_official_interface.3mf`
*   **What it does:** Represents the mounting footprint of the official Raspberry Pi Core mid-plate. It verifies global shrinkage.
*   **How to measure XY Shrinkage:**
    1.  Open your digital calipers and zero them.
    2.  Place the **outside measuring jaws** of your caliper flat inside the square recessed pocket on the coupon.
    3.  Extend the jaws until they touch both opposing inner walls of the recess.
    4.  *Write down the measurement in Row 1 of your worksheet.* (Nominal: **110.60 mm**).
*   **How to measure Z-Axis Height:**
    1.  Place the coupon flat on a hard table.
    2.  Use the flat jaws of your caliper vertically, or use the caliper's **depth rod/pin** extended from the bottom.
    3.  Measure the thickness of the outer square lip from the bed-surface up to the top face.
    4.  *Write down the measurement in Row 2 of your worksheet.* (Nominal: **3.00 mm**).

---

### Step 2.2: Screw Clearance Hole Calibration
*   **Print this file:** `exports/3mf/coupon_active_driver.3mf`
*   **What it does:** Tests the alignment and bolt circle diameters of your active speaker.
*   **How to measure Clearance Holes:**
    1.  Clean any tiny "ooze" strands from inside the screw holes.
    2.  Insert the **inside measuring claws** (the smaller upper claws) of your caliper into one of the four outer screw holes.
    3.  Spread the claws open until they flatly contact the inside cylinder walls.
    4.  *Write down the measurement in Row 3 of your worksheet.* (Nominal: **4.00 mm**).

---

### Step 2.3: Heat-Set Insert Boss Calibration
*   **Print this file:** `exports/3mf/coupon_heat_set_insert.3mf`
*   **What it does:** Features four blind test bores ranging from 4.0 mm to 4.3 mm in diameter.
*   **How to perform the test:**
    1.  Turn on your soldering iron and equip it with an M3 heat-set insert tip. Set it to **250–270°C**.
    2.  Heat-press a brass M3 insert (Ø4.6 mm outer diameter) into each of the four holes labeled `4.0`, `4.1`, `4.2`, and `4.3`.
    3.  Let the plastic cool completely (5 minutes).
    4.  Inspect the holes:
        *   If the hole is **too small (e.g. 4.0 mm)**, the insert might bulge the outer plastic boss walls or create excess molten squeeze-out that blocks the threads.
        *   If the hole is **too large (e.g. 4.3 mm)**, the insert will slip in too easily, meaning it won't have enough grip and might pull out under torque.
    5.  Identify the hole that holds the insert perfectly square, flush, and tight.
    6.  *Write down your chosen hole diameter in Row 4 of your worksheet.* (Nominal Default: **4.20 mm**).

---

### Step 2.4: Cable Gland Fit Calibration
*   **Print these files:** 
    *   Coupon: `exports/3mf/coupon_cable_passage.3mf` (Rigid ASA/PETG)
    *   Gland: `exports/3mf/cable_gland.3mf` (Flexible TPU 95A)
*   **What it does:** Tests how airtight and tight your wire gland fits inside the cabinet divider.
*   **How to perform the test:**
    1.  Gently press your printed TPU `cable_gland` into the center hole of the rigid `coupon_cable_passage`.
    2.  Check the fit:
        *   **Perfect:** Gland presses in with moderate finger force, seats firmly, and does not slip out. (Write down **"Perfect"** in Row 5).
        *   **Too Tight:** Impossible to press in, or the TPU gland buckles/collapses. (Write down **"Too Tight"**).
        *   **Too Loose:** Slides in with zero resistance, spins, or falls out when shaken. (Write down **"Too Loose"**).

---

### Step 2.5: Physical Speaker Driver Measurements
*   **Take your physical components:** 
    1.  Dayton ND91-4 speaker driver
    2.  SB Acoustics SB12PACR-00 passive radiator
*   **What it does:** Physical manufacturing batches can vary slightly from catalog drawings. Measuring them ensures your speaker sits perfectly flush with the printed cabinet pockets.
*   **How to measure the Dayton Driver Flange:**
    1.  Place the flat jaws of your calipers over the outer rim/flange of your Dayton ND91-4 active speaker.
    2.  Measure the thickness of the metal-and-rubber mounting rim (avoid squeezing the rubber too hard).
    3.  *Write down the reading in Row 6.* (Nominal assumed: **3.00 mm**).
*   **How to measure the SB Acoustics PR Flange:**
    1.  Place the flat jaws of your calipers over the outer plastic rim flange of your SB Acoustics passive radiator.
    2.  *Write down the reading in Row 7.* (Nominal assumed: **4.00 mm**).

---

## ⚙️ Part 3: Running the Calibration Wizard

Now that your worksheet is filled with numbers, let's feed them into the CAD generator!

1.  Open your terminal.
2.  Navigate to the project directory:
    ```bash
    cd ~/Satellite1-Ultra
    ```
3.  Execute the interactive calibration wizard script:
    ```bash
    python scripts/calibrate.py
    ```
4.  The wizard will greet you and prompt you for each step sequentially:
    *   **Step 1:** Enter the pocket recess width you wrote down in Row 1 (e.g. `110.15`).
    *   **Step 2:** Enter the lip height you wrote down in Row 2 (e.g. `2.95`).
    *   **Step 3:** Enter the screw hole diameter you wrote down in Row 3 (e.g. `3.85`).
    *   **Step 4:** Select the choice matching your best brass insert hole from Row 4.
    *   **Step 5:** Select whether your TPU gland was Perfect (1), Too tight (2), or Too loose (3). If tight/loose, input how many millimeters you want to enlarge/shrink the hole (we recommend `0.15 mm` to start).
    *   **Step 6:** Enter your Dayton driver flange thickness from Row 6 (e.g. `3.10`).
    *   **Step 7:** Enter your SB Acoustics radiator flange thickness from Row 7 (e.g. `4.20`).
5.  Review the summary table displayed on your screen.
6.  When prompted `Save these settings to configuration files? [Y/n]:`, press **`Y`** and hit Enter.

---

## 🚀 Part 4: Automatic Custom CAD Compilation

After saving, the wizard will ask you:
```
Would you like to automatically regenerate and compile your new CAD files now? [Y/n]:
```
1.  Type **`Y`** and press Enter.
2.  Your terminal will activate the CadQuery engine. It will:
    *   Load your custom caliper dimensions and shrinkage ratios.
    *   **Regenerate every B-rep part automatically** with custom-calculated scaling, hole enlargements, and recess adjustments.
    *   Re-run all 11 digital safety gates (interferences, sealing limits, clearance checks).
    *   Export a fresh, custom-compensated set of manufacturing files.

---

## 🖨️ Part 5: Safe to Print!

Once compilation is complete and you see `SUCCESS!`, your custom models are ready to be printed:

*   **Custom 3MF Files (Recommended):** Look inside **`exports/3mf/`**
    *   *These files are pre-oriented, nested, and optimized for slicers like Bambu Studio, OrcaSlicer, or PrusaSlicer!*
*   **Custom STL Files:** Look inside **`exports/stl/`**
    *   *Standard watertight mesh files.*

Because these exported models are now custom-tailored to your physical printer's shrinkage profile and your physical drivers:

🎉 **You are now 100% safe to print the main cabinet, shell, and clamp rings!** 🎉
