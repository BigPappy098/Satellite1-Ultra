"""One obvious, ordered set of files for a first-time builder."""

from __future__ import annotations

CALIBRATION_PRINT_ORDER = (
    ("coupon_official_interface", "01_CHECK_SATELLITE_TOP_FIT.3mf", 1),
    ("coupon_heat_set_insert", "02_CHECK_SCREWS_AND_INSERTS.3mf", 1),
    ("coupon_active_driver", "03_CHECK_SPEAKER_FIT.3mf", 1),
    ("coupon_passive_radiator", "04_CHECK_RADIATOR_FIT.3mf", 1),
    ("coupon_gasket_base", "05_GASKET_TEST_BASE.3mf", 1),
    ("coupon_gasket_cap", "06_GASKET_TEST_TOP.3mf", 1),
    ("coupon_cable_passage", "07_CHECK_CABLE_HOLE.3mf", 1),
    ("cable_gland", "08_FLEXIBLE_CABLE_SEAL_TPU.3mf", 1),
)

ULTRA_PRINT_ORDER = (
    ("main_cabinet", "01_MAIN_SPEAKER_BODY.3mf", 1),
    ("pressure_divider", "02_ELECTRONICS_DIVIDER.3mf", 1),
    ("active_driver_clamp_ring", "03_SPEAKER_CLAMP_RING.3mf", 1),
    ("passive_radiator_clamp_ring", "04_RADIATOR_CLAMP_RING_PRINT_TWO.3mf", 2),
    ("base_skirt", "05_BOTTOM_BASE.3mf", 1),
    ("ballast_cartridge", "06_WEIGHT_TRAY.3mf", 1),
    ("ballast_cartridge_lid", "07_WEIGHT_TRAY_LID.3mf", 1),
    ("bottom_service_plate", "08_BOTTOM_ACCESS_PANEL.3mf", 1),
    ("electronics_shroud", "09_ELECTRONICS_COVER.3mf", 1),
    ("outer_shell", "10_OUTER_SHELL.3mf", 1),
    ("anti_slip_ring", "11_FLEXIBLE_BOTTOM_GRIP_TPU.3mf", 1),
    ("leak_test_adapter", "12_LEAK_TEST_TOOL.3mf", 1),
)

OFFICIAL_TOP_PRINT_ORDER = (
    ("official_mid_plate", "01_SATELLITE_MID_PLATE.stl", 1),
    ("official_mid_plate_threads", "02_SATELLITE_THREADED_PLATE.stl", 1),
    ("official_pcb_spacer", "03_CIRCUIT_BOARD_SPACER.stl", 1),
    ("official_lock_ring", "04_TOP_LOCK_RING.stl", 1),
    ("official_top_plate", "05_BUTTON_AND_LIGHT_TOP.stl", 1),
    ("official_top_plate_snap_in_diffuser_ring", "06_SNAP_IN_LIGHT_RING.stl", 1),
)
