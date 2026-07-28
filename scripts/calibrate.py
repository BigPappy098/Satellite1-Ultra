#!/usr/bin/env python3
"""
Satellite1-Ultra CAD Calibration Wizard
An interactive CLI tool to calibrate print tolerances and regenerate models automatically.
"""

import os
import sys
import subprocess

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title):
    print("=" * 65)
    print(f" {title.upper().center(63)} ")
    print("=" * 65)

def get_input(prompt, default=None):
    try:
        val = input(prompt).strip()
        if not val and default is not None:
            return default
        return val
    except (KeyboardInterrupt, EOFError):
        print("\n\nCalibration aborted. No changes made.")
        sys.exit(0)

def get_float_input(prompt, nominal_val):
    while True:
        val = get_input(prompt, str(nominal_val))
        try:
            return float(val)
        except ValueError:
            print("❌ Invalid input! Please enter a valid decimal number.")

def update_compensation_yaml(filepath, updates):
    with open(filepath, 'r') as f:
        lines = f.readlines()
        
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" in line:
            key = stripped.split(":")[0].strip()
            if key in updates:
                line_indent = len(line) - len(line.lstrip(' '))
                lines[idx] = f"{' ' * line_indent}{key}: {updates[key]}\n"
                
    with open(filepath, 'w') as f:
        f.writelines(lines)

def update_flange_thickness(filepath, driver_name, new_val):
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    in_drivers_section = False
    in_target_block = False
    indent_level = -1
    
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("active_drivers:") or stripped.startswith("passive_radiators:"):
            in_drivers_section = True
            continue
        
        if in_drivers_section:
            line_indent = len(line) - len(line.lstrip(' '))
            if line_indent == 0 and stripped and not stripped.startswith("#"):
                in_drivers_section = False
                in_target_block = False
                continue
                
            if stripped.startswith(f"{driver_name}:"):
                in_target_block = True
                indent_level = line_indent
                continue
                
            if in_target_block:
                if line_indent == indent_level and stripped and not stripped.startswith("#"):
                    in_target_block = False
                    continue
                
                if stripped.startswith("flange_thickness_mm:"):
                    comment_part = ""
                    if "#" in line:
                        comment_part = "  " + line[line.find("#"):]
                    lines[idx] = f"{' ' * line_indent}flange_thickness_mm: {new_val}{comment_part}\n"
                    break
                    
    with open(filepath, 'w') as f:
        f.writelines(lines)

def main():
    clear_screen()
    print_header("SATELLITE1-ULTRA CALIBRATION WIZARD")
    print("""
This wizard will guide you step-by-step through measuring your test 
coupons with your digital calipers.

Based on your measurements, this script will automatically:
1. Calculate the exact shrinkage scaling fractions.
2. Determine required offsets to enlarge or shrink screw/cable holes.
3. Update your configuration files.
4. Regenerate and compile your customized, print-ready CAD files.

💡 Press [ENTER] at any prompt to accept the nominal default value.
""")
    get_input("Press [ENTER] to begin...")

    # 1. XY Scale/Shrinkage Calibration
    clear_screen()
    print_header("Step 1: XY Scale & Shrinkage Calibration")
    print("""
📍 Coupon: coupon_official_interface.3mf
🔍 Action: 
Measure the width of the main square pocket recess on the coupon.
Nominally, this pocket is designed to be exactly 110.60 mm wide.

If your print has shrunk, your caliper might read slightly less 
(e.g., 110.15 mm).
""")
    xy_measured = get_float_input("Enter your measured width in mm [Default 110.60]: ", 110.60)
    xy_scale = (110.60 / xy_measured) - 1.0

    # 2. Z Scale Calibration
    clear_screen()
    print_header("Step 2: Z Scale/Height Calibration")
    print("""
📍 Coupon: coupon_official_interface.3mf
🔍 Action:
Measure the vertical height of the outer square lip on the coupon.
Nominally, this lip is designed to be exactly 3.00 mm tall.
""")
    z_measured = get_float_input("Enter your measured height in mm [Default 3.00]: ", 3.00)
    z_scale = (3.00 / z_measured) - 1.0

    # 3. Screw Clearance Holes (Hole Offset)
    clear_screen()
    print_header("Step 3: Screw Clearance Hole Calibration")
    print("""
📍 Coupon: coupon_active_driver.3mf
🔍 Action:
Measure the inside diameter of the four outer screw clearance holes.
Nominally, these holes should be exactly 4.00 mm in diameter.
""")
    hole_measured = get_float_input("Enter your measured hole diameter in mm [Default 4.00]: ", 4.00)
    hole_offset = 4.00 - hole_measured

    # 4. Heat-Set Insert Bores
    clear_screen()
    print_header("Step 4: Heat-Set Insert Bore Selection")
    print("""
📍 Coupon: coupon_heat_set_insert.3mf
🔍 Action:
Heat-press an M3 brass insert into each of the four test holes
labeled 4.0 mm, 4.1 mm, 4.2 mm, and 4.3 mm.

Select the hole that holds the insert tightest and flushest without
bulging or cracking the outer plastic walls.
""")
    print("Which hole performed the best?")
    print(" 1) 4.0 mm")
    print(" 2) 4.1 mm")
    print(" 3) 4.2 mm (Nominal CAD Default)")
    print(" 4) 4.3 mm")
    
    while True:
        choice = get_input("Enter choice (1-4) [Default 3]: ", "3")
        if choice == "1":
            selected_insert_dia = 4.0
            break
        elif choice == "2":
            selected_insert_dia = 4.1
            break
        elif choice == "3":
            selected_insert_dia = 4.2
            break
        elif choice == "4":
            selected_insert_dia = 4.3
            break
        else:
            print("❌ Invalid choice. Please choose 1, 2, 3, or 4.")
            
    insert_offset = selected_insert_dia - 4.2

    # 5. Cable Passage TPU Gland fit
    clear_screen()
    print_header("Step 5: Cable Gland Fit Calibration")
    print("""
📍 Coupon: coupon_cable_passage.3mf
🔍 Action:
Press your TPU-printed cable gland into the central 8.0 mm hole.
""")
    print("How does the TPU gland fit?")
    print(" 1) Perfect, snug fit (Nominal 8.00 mm)")
    print(" 2) Too tight / impossible to press in")
    print(" 3) Too loose / slips out easily")
    
    cable_offset = 0.0
    while True:
        choice = get_input("Enter choice (1-3) [Default 1]: ", "1")
        if choice == "1":
            cable_offset = 0.0
            break
        elif choice == "2":
            adjust = get_float_input("By how many mm would you like to ENLARGE the hole? [e.g., 0.20]: ", 0.20)
            cable_offset = adjust
            break
        elif choice == "3":
            adjust = get_float_input("By how many mm would you like to SHRINK the hole? [e.g., 0.20]: ", 0.20)
            cable_offset = -adjust
            break
        else:
            print("❌ Invalid choice. Please choose 1, 2, or 3.")

    # 6. Dayton ND91-4 Flange Thickness
    clear_screen()
    print_header("Step 6: Active Driver Flange Thickness")
    print("""
🔊 Component: Dayton Audio ND91-4 active driver
🔍 Action:
Measure the actual thickness of the rubber-surrounded mounting flange 
on your physical driver. 

Nominally, the CAD assumes this flange is exactly 3.00 mm thick.
""")
    active_flange = get_float_input("Enter your driver's flange thickness in mm [Default 3.00]: ", 3.00)

    # 7. SB Acoustics SB12PACR-00 Flange Thickness
    clear_screen()
    print_header("Step 7: Passive Radiator Flange Thickness")
    print("""
🔊 Component: SB Acoustics SB12PACR-00 passive radiator
🔍 Action:
Measure the actual thickness of the plastic mounting flange on your
physical passive radiator.

Nominally, the CAD assumes this flange is exactly 4.00 mm thick.
""")
    passive_flange = get_float_input("Enter your radiator's flange thickness in mm [Default 4.00]: ", 4.00)

    # Compile Summary & Save
    clear_screen()
    print_header("Calibration Summary")
    print(f" • XY Scale Correction:         {xy_scale*100:+.3f}% (Fraction: {xy_scale:.6f})")
    print(f" • Z Scale Correction:          {z_scale*100:+.3f}% (Fraction: {z_scale:.6f})")
    print(f" • Hole Diameter Offset:        {hole_offset:+.2f} mm")
    print(f" • Heat-Set Insert Offset:      {insert_offset:+.2f} mm")
    print(f" • Cable Passage Offset:        {cable_offset:+.2f} mm")
    print(f" • Dayton Driver Flange:        {active_flange:.2f} mm")
    print(f" • SB Acoustics PR Flange:      {passive_flange:.2f} mm")
    print("-" * 65)

    confirm = get_input("Save these settings to configuration files? [Y/n]: ", "y").lower()
    if confirm != "y" and confirm != "yes":
        print("❌ Canceled. No files were written.")
        sys.exit(0)

    # Write Physical Compensation YAML
    comp_updates = {
        "xy_scale_correction_fraction": f"{xy_scale:.6f}",
        "z_scale_correction_fraction": f"{z_scale:.6f}",
        "hole_diameter_offset": f"{hole_offset:.2f}",
        "insert_hole_diameter_offset": f"{insert_offset:.2f}",
        "cable_passage_offset": f"{cable_offset:.2f}"
    }
    update_compensation_yaml("config/physical_compensation.yaml", comp_updates)
    print("✓ Saved config/physical_compensation.yaml")

    # Write Components YAML
    update_flange_thickness("config/components.yaml", "dayton_nd91_4", f"{active_flange:.1f}")
    update_flange_thickness("config/components.yaml", "sb_acoustics_sb12pacr_00", f"{passive_flange:.1f}")
    print("✓ Saved config/components.yaml")

    # Ask to build CAD
    print("-" * 65)
    run_build = get_input("Would you like to automatically regenerate and compile your new CAD files now? [Y/n]: ", "y").lower()
    if run_build == "y" or run_build == "yes":
        print("\n🚀 Compiling B-rep parts, running validation gates, and exporting STL/3MF files...\n")
        try:
            # We use make release to compile everything
            result = subprocess.run(["make", "release"], check=True)
            if result.returncode == 0:
                print("\n🎉 SUCCESS! All customized CAD parts are successfully compiled, verified, and exported to /exports/!")
        except Exception as e:
            print(f"\n❌ Error building CAD: {e}")
    else:
        print("\n💡 You can regenerate your CAD files anytime by running 'make release' in your terminal.")

if __name__ == "__main__":
    main()
