# Hardware and Materials Guide

Use Batch 1 only. The public Batch 1 pair is Core rev4.1 plus HAT rev4.1 /
R2024.12.06. If the board or packaging says Satellite1.1, rev5.1 Core, rev6.1
HAT, or requires an external Wi-Fi antenna, stop: that hardware is unsupported.

| ID | Category | Item | Exact specification | Qty | Required | Where to buy (US) |
|---|---|---|---|---|---|---|
| A01 | active driver | Dayton Audio ND91-4 | 4 ohm full-range driver; manufacturer model ND91-4 | 1 | yes | https://www.parts-express.com/Dayton-Audio-ND91-4-3-1-2-Aluminum-Cone-Full-Range-Driver-4-290-224 |
| A02 | passive radiator | Dayton Audio DSA115-PR | 4 inch passive radiator with M5 mass post | 2 | yes | https://www.parts-express.com/Dayton-Audio-DSA115-PR-4-Designer-Series-Aluminum-Cone-Passive-Radiator-295-544 |
| E01 | official electronics | FutureProofHomes Satellite1 Batch 1 development kit | Core rev4.1 + HAT rev4.1 / R2024.12.06; not Satellite1.1 | 1 | yes | https://futureproofhomes.net/products/satellite1-kit |
| H01 | insert | CNC Kitchen M3 x 5.7 heat-set insert | M3x0.5 internal thread, 5.7 mm length, 4.6 mm maximum OD | 48 | yes; includes four spares | https://www.amazon.com/s?k=CNC+Kitchen+M3+heat+set+insert+M3x5.7 |
| H02 | speaker cable | 2-pin JST-XH 2.54 mm speaker lead | 22 AWG stranded red/black, each insulated conductor OD <=1.8 mm, 350 mm minimum | 1 | yes | https://www.amazon.com/s?k=JST-XH+2.54mm+2+pin+speaker+pigtail |
| H03 | speaker terminals | solder the leads directly to the driver's terminal lugs | The ND91-4 ships with flat solder lugs, each pierced by an oblong hole: thread the conductor through, crimp it closed, then flow solder, so the joint is mechanically captive rather than relying on solder for strength. Dress the wire toward the driver axis, never outward, and heat-shrink each joint. Radial bulk here is the binding constraint: the terminals are the widest thing that must pass the 76.65 mm bore, they clear it only through the notch, and the leads have to be attached before the driver goes in because the chamber is sealed after. | 2 joints | recommended | https://www.amazon.com/s?k=3mm+heat+shrink+tubing+assortment |
| H04 | speaker terminals | 2.8 mm fully insulated female quick-disconnects | Alternative to H03, and the weaker one. A disconnect body plus its sleeve stands 2 to 3 mm proud of the lug on the side that has the least room, and it is a rattle source inside a sealed chamber. It also buys nothing: reaching this joint means pulling the driver anyway. If used, verify the blade width against the lug first, measured across the flat face and not along it, and confirm the fit on the speaker-fit coupon before committing to the cabinet print. | 2 | optional | https://www.amazon.com/s?k=2.8mm+fully+insulated+female+quick+disconnect |
| B01 | ballast | mild-steel plate | 100 x 92 x 6 mm, edges deburred, dry, light oil removed | 2 | yes | https://www.onlinemetals.com/en/buy/steel/0-25-mild-steel-plate-a36-hot-rolled/pid/1156 |
| B02 | radiator tuning | M5 washers plus self-adhesive lead-free strip for final trim | 8.00 g per radiator, the two sets matched within 0.02 g, applied centred on the M5 mass post. Stack M5 washers for the bulk -- about 13 of them at roughly 0.6 g each -- then trim self-adhesive lead-free strip for the last fraction of a gram. Weigh both radiators' finished stacks and match them, rather than trusting counts | 2 matched sets | yes; final mass requires physical tuning | https://www.amazon.com/s?k=M5+flat+washer+stainless+assortment |
| G00 | gasket stock | closed-cell EPDM foam sheet | 2.0 mm nominal, soft, smooth skin, ASTM D1056 2A1 or equivalent | one 300 x 300 mm sheet | yes | https://www.amazon.com/s?k=2mm+closed+cell+EPDM+foam+sheet+adhesive |
| D01 | optional acoustic material | polyester acoustic batting | not installed in RC1; reserve for measurement-led development only | 0 | no | https://www.parts-express.com/search?keywords=acoustic%20polyfill |
| O01 | official printed part | official_mid_plate | ASA (PETG alternative); exact file OFFICIAL_PARTS/REQUIRED_SINGLE_MATERIAL/official_mid_plate.stl; preserved official STL | 1 | yes | printed by you |
| O02 | official printed part | official_mid_plate_threads | ASA (PETG alternative); exact file OFFICIAL_PARTS/REQUIRED_SINGLE_MATERIAL/official_mid_plate_threads.stl; preserved official STL | 1 | yes | printed by you |
| O03 | official printed part | official_pcb_spacer | ASA (PETG alternative); exact file OFFICIAL_PARTS/REQUIRED_SINGLE_MATERIAL/official_pcb_spacer.stl; preserved official STL | 1 | yes | printed by you |
| O04 | official printed part | official_lock_ring | ASA (PETG alternative); exact file OFFICIAL_PARTS/REQUIRED_SINGLE_MATERIAL/official_lock_ring.stl; preserved official STL | 1 | yes | printed by you |
| O05 | official printed part | official_top_plate | ASA (PETG alternative); exact file OFFICIAL_PARTS/REQUIRED_SINGLE_MATERIAL/official_top_plate.stl; preserved official STL | 1 | yes | printed by you |
| O06 | official printed part | official_top_plate_snap_in_diffuser_ring | ASA (PETG alternative); exact file OFFICIAL_PARTS/REQUIRED_SINGLE_MATERIAL/official_top_plate_snap_in_diffuser_ring.stl; preserved official STL | 1 | yes | printed by you |
| O07 | official printed part | official_top_plate_mm_buttons | ASA (PETG alternative); exact file OFFICIAL_PARTS/OPTIONAL_MULTI_MATERIAL/official_top_plate_mm_buttons.stl; preserved official STL | 1 | optional alternative | printed by you |
| O08 | official printed part | official_top_plate_mm_diffuser_ring | ASA (PETG alternative); exact file OFFICIAL_PARTS/OPTIONAL_MULTI_MATERIAL/official_top_plate_mm_diffuser_ring.stl; preserved official STL | 1 | optional alternative | printed by you |
| F01 | fastener | M3 x 16 shoulder screw | M3 x d4 shoulder screw, A2-70 stainless, M3x0.5 | 4 | yes | https://www.mcmaster.com/screws/socket-head-screws/thread-size~m3/ |
| F02 | fastener | M3 x 8 button head screw | ISO 7380-1, A2-70 stainless, M3x0.5 | 4 | yes | https://www.mcmaster.com/screws/socket-head-screws/thread-size~m3/ |
| F03 | fastener | M3 x 8 socket cap screw | ISO 4762, A2-70 stainless, M3x0.5 | 8 | yes | https://www.mcmaster.com/screws/socket-head-screws/thread-size~m3/ |
| F04 | fastener | M3 x 10 socket cap screw | ISO 4762, A2-70 stainless, M3x0.5 | 4 | yes | https://www.mcmaster.com/screws/socket-head-screws/thread-size~m3/ |
| F05 | fastener | M3 x 10 socket cap screw | ISO 4762, A2-70 stainless, M3x0.5 | 8 | yes | https://www.mcmaster.com/screws/socket-head-screws/thread-size~m3/ |
| F06 | fastener | M3 x 6 button head screw | ISO 7380-1, A2-70 stainless, M3x0.5 | 4 | yes | https://www.mcmaster.com/screws/socket-head-screws/thread-size~m3/ |
| F07 | fastener | M3 x 10 socket cap screw | ISO 4762, A2-70 stainless, M3x0.5 | 4 | yes | https://www.mcmaster.com/screws/socket-head-screws/thread-size~m3/ |
| F08 | fastener | M3 x 8 button head screw | ISO 7380-1, A2-70 stainless, M3x0.5 | 4 | yes | https://www.mcmaster.com/screws/socket-head-screws/thread-size~m3/ |
| F09 | fastener | M3 x 8 button head screw | ISO 7380-1, A2-70 stainless, M3x0.5 | 4 | yes | https://www.mcmaster.com/screws/socket-head-screws/thread-size~m3/ |
| F10 | fastener | M3 x 8 socket cap screw | ISO 4762, A2-70 stainless, M3x0.5 | 4 | yes | https://www.mcmaster.com/screws/socket-head-screws/thread-size~m3/ |
| F11 | fastener | M3 x 8 socket cap screw | ISO 4762, A2-70 stainless, M3x0.5 | 4 | yes | https://www.mcmaster.com/screws/socket-head-screws/thread-size~m3/ |

All purchasing availability and prices must be checked by the builder.
Manufacturer geometry and electrical parameters are
`DERIVED_FROM_MANUFACTURER_DRAWING`; supplier availability is an
`ENGINEERING_ESTIMATE`.

No structural glue is used. No damping material is installed in RC1. Gaskets
are replaceable mechanically compressed EPDM, and the cable seal is TPU 95A.
