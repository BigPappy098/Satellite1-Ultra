"""Generate the illustrated builder website.

The website is the primary instructions: one screen per step, big pictures,
plain language.  Every list of files, quantity, and assembly action is taken
from the same authoritative data the PDFs and the release package use, so the
site cannot drift away from what is actually shipped.
"""

from __future__ import annotations

import csv
import json
import shutil
from html import escape
from pathlib import Path

from satellite1_ultra.builder_files import (
    CALIBRATION_STAGE_ONE,
    CALIBRATION_STAGE_TWO,
    FABRIC_WRAP_PRINT_ORDER,
    OFFICIAL_TOP_PRINT_ORDER,
    ULTRA_PRINT_ORDER,
)
from satellite1_ultra.configuration import ROOT
from satellite1_ultra.exporting import PARTS
from satellite1_ultra.release import (
    CALIBRATION_DIR,
    CALIBRATION_STAGE_TWO_DIR,
    ENCLOSURE_DIR,
    FABRIC_DIR,
    GASKET_DIR,
    GASKET_SOLIDS,
    OFFICIAL_DIR,
    RELEASE_NAME,
    STL_DIR,
)

#: Filled in once the repository is public; every download link hangs off this.
REPO = "https://github.com/BigPappy098/Satellite1-Ultra"
RAW = f"{REPO}/raw/main/release/{RELEASE_NAME}"
#: Two notebooks, because the rounds ask for different things and a single one
#: branching on a hidden prefix is a trap: paste the wrong code and it quietly
#: builds the wrong set. Each notebook now refuses the other's code by name.
_COLAB = (
    "https://colab.research.google.com/github/BigPappy098/Satellite1-Ultra/blob/main/notebooks/"
)
COLAB_TEST_PIECES = _COLAB + "make_my_test_pieces.ipynb"
COLAB_PARTS = _COLAB + "make_my_parts.ipynb"

#: Parts package_release ships an STL for: everything printable.  Only the
#: gasket solids are absent, and those are cut from foam, not printed.
_STL_AVAILABLE = {name for name in PARTS if name not in GASKET_SOLIDS}

PAGES = (
    ("index.html", "Start"),
    ("calibrate.html", "1 · Calibrate"),
    ("parts.html", "2 · Get parts"),
    ("assemble.html", "3 · Build it"),
)


def _printer_limits(root: Path) -> dict[str, float]:
    """Largest footprint and tallest part, read from the printability report.

    Taken from the gate's own output rather than retyped, so the figure on the
    site is the figure the release was checked against. Reading the report keeps
    the site build fast; recomputing would rebuild all 28 B-reps.
    """
    report = json.loads(
        (root / "reports" / "validation" / "printability.json").read_text(encoding="utf-8")
    )
    long_mm = short_mm = tall_mm = 0.0
    for part in report["parts"]:
        x, y, z = (float(v) for v in part["bounds_mm"])
        long_side, short_side = max(x, y), min(x, y)
        if long_side * short_side > long_mm * short_mm:
            long_mm, short_mm = long_side, short_side
        tall_mm = max(tall_mm, z)
    return {"long_mm": long_mm, "short_mm": short_mm, "tallest_mm": tall_mm}


def _shell(current: str, title: str, body: str) -> str:
    """Wrap page content in the shared header, step strip, and footer."""
    strip = []
    seen_current = False
    for href, label in PAGES:
        if href == current:
            state, seen_current = "now", True
        else:
            state = "" if seen_current else "done"
        number, _, name = label.partition(" · ")
        inner = f"<b>{escape(name or number)}</b>" if name else f"<b>{escape(number)}</b>"
        small = f"Step {escape(number)}" if name else "&nbsp;"
        strip.append(f'<li><a class="{state}" href="{href}">{small}{inner}</a></li>')
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)} — Satellite1 Ultra</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<header class="bar"><div class="wrap"><a href="index.html">Satellite1 Ultra</a>
<span style="opacity:.75;font-size:.92rem">Build guide</span></div></header>
<div class="wrap">
<ul class="steps">{"".join(strip)}</ul>
{body}
<footer>
Nothing here has been built and measured yet, so your own checks matter.<br>
Hardware is CERN-OHL-S-2.0. Official Satellite1 parts keep their own licence.
</footer>
</div>
</body>
</html>
"""


def _material(source: str) -> str:
    """The material a part is actually exported as.

    Read from PARTS rather than written out here.  The page used to hard-code
    "TPU 95A" for anti_slip_ring and ASA for everything else, which labelled the
    mic isolators and the leak-test tool -- both TPU -- as ASA. Printing the
    isolators rigid removes the decoupling they exist to provide.
    """
    return str(PARTS[source].material)


def _material_cell(material: str) -> str:
    """Material as a coloured badge, so it cannot be skimmed past."""
    kind = "tpu" if material.startswith("TPU") else "asa" if material == "ASA" else "other"
    return f'<td><span class="mat {kind}">{escape(material)}</span></td>'


def _file_table(rows: list[tuple[str, str, int, str]], folder: str) -> str:
    """A download table: what to print, how many, in what material, both formats.

    Every row links into the release package, whose folder names come from
    release.py so the two cannot drift apart again.
    """
    cells = []
    for source, name, quantity, material in rows:
        # The official top parts are already STL, so there is no second format
        # to offer; everything we generate ourselves has both.
        alternate = (
            f'<a href="{RAW}/{STL_DIR}/{source}.stl">STL</a>'
            if source in _STL_AVAILABLE and not name.lower().endswith(".stl")
            else '<span class="dim">already STL</span>'
            if name.lower().endswith(".stl")
            else '<span class="dim">—</span>'
        )
        cells.append(
            f'<tr><td><a href="{RAW}/{folder}/{name}">{escape(name)}</a></td>'
            f'<td class="qty">{quantity}</td>{_material_cell(material)}'
            f"<td>{alternate}</td></tr>"
        )
    # Label the primary column with the format these rows actually are, rather
    # than assuming 3MF: the official-top table is STL and said "3MF".
    suffixes = sorted({Path(name).suffix.upper().lstrip(".") for _s, name, _q, _m in rows})
    primary = " / ".join(suffixes) if suffixes else "file"
    return (
        f'<table class="files"><tr><th>File — click to download ({escape(primary)})</th>'
        "<th>How many</th><th>Print in</th><th>Also available as</th></tr>"
        f"{''.join(cells)}</table>"
    )


def _material_summary() -> str:
    """Which filament each part needs, counted from PARTS.

    Stated up front because the split is easy to get wrong: the seals look like
    the obvious TPU candidates and are not printed at all, while the four parts
    that genuinely need TPU are easy to miss in a long table.
    """
    printed = {
        name: definition
        for name, definition in PARTS.items()
        if name not in {"divider_gasket", "driver_gasket", "passive_radiator_gasket"}
    }
    tpu = sorted(n for n, d in printed.items() if str(d.material).startswith("TPU"))
    asa = [n for n, d in printed.items() if d.material == "ASA"]
    tpu_total = sum(PARTS[n].quantity for n in tpu)
    tpu_list = ", ".join(
        f"{n.replace('_', ' ')}{f' (×{PARTS[n].quantity})' if PARTS[n].quantity > 1 else ''}"
        for n in tpu
    )
    return f"""
<div class="note"><strong>Which filament goes where</strong>
<table class="mats">
<tr>{_material_cell("ASA")}<td><b>{len(asa)} files.</b> The cabinet, the skin, the
clamp rings, the base, the weight tray, and all eight test pieces. One spool is
plenty.</td></tr>
<tr>{_material_cell("TPU 95A")}<td><b>{len(tpu)} files, {tpu_total} pieces:</b>
{escape(tpu_list)}. These have to flex — printing them rigid defeats the point.</td></tr>
<tr>{_material_cell("2 mm closed-cell EPDM")}<td><b>3 seals, not printed.</b> You
cut these from foam sheet using the DXF templates further down this page.</td></tr>
</table>
<p class="help">Any TPU around 95A shore works. Softer is fine for the isolators
and the foot; the cable seal wants the firmer end so it grips the wires.</p></div>
"""


#: How BOM categories are grouped on the shopping page, in buying order.
_SHOPPING_GROUPS = (
    ("The electronics and drivers", ("official electronics", "active driver", "passive radiator")),
    ("Screws, inserts and wiring", ("fastener", "insert", "speaker cable", "speaker terminals")),
    (
        "Weight, seals and filament",
        ("ballast", "radiator tuning", "gasket stock", "optional acoustic material"),
    ),
)
#: Printed upstream parts, listed on the download tables rather than bought.
_SHOPPING_SKIP_CATEGORIES = {"official printed part"}


def _shopping_table() -> str:
    """The shopping list, generated from BOM.csv so every item carries its link.

    This page used to hold a hand-written nine-row table with no links at all,
    while BOM.csv already had a US source for all 21 purchasable lines.
    """
    with (ROOT / "docs" / "BOM.csv").open(encoding="utf-8", newline="") as source:
        rows = list(csv.DictReader(source))
    printed = {"printed part", "calibration part", "service tool"}
    printed |= _SHOPPING_SKIP_CATEGORIES
    by_category = {row["id"]: row for row in rows if row["category"] not in printed}

    sections = []
    placed: set[str] = set()
    for heading, categories in _SHOPPING_GROUPS:
        body = []
        for row in by_category.values():
            if row["category"] not in categories:
                continue
            placed.add(row["id"])
            link = row.get("buy_link", "")
            where = (
                f'<a href="{escape(link)}" target="_blank" rel="noopener">Buy</a>'
                if link.startswith("http")
                else escape(link or "—")
            )
            body.append(
                f"<tr><td>{escape(row['item'])}</td>"
                f'<td class="qty">{escape(row["quantity"])}</td>'
                f"<td>{escape(row['specification'][:150])}</td><td>{where}</td></tr>"
            )
        if body:
            sections.append(
                f"<h3>{escape(heading)}</h3><table><tr><th>What</th><th>How many</th>"
                f"<th>Specification</th><th>Where</th></tr>{''.join(body)}</table>"
            )
    missed = [row["id"] for row in by_category.values() if row["id"] not in placed]
    if missed:
        raise ValueError(f"BOM rows not shown on the shopping page: {', '.join(sorted(missed))}")
    return "".join(sections)


def _index(req: dict[str, float]) -> str:
    body = f"""
<h1>Let\u2019s build your Satellite1 Ultra</h1>
<p class="lede">Your Satellite1 keeps its microphones, its buttons and its
lights. Everything below them gets replaced by a sealed, weighted cabinet with a
real 3.5&nbsp;inch driver and a passive radiator on each side.</p>

<img src="images/product_iso.png" alt="The finished Satellite1 Ultra">

<p>It is built from the official squircle\u2019s own curve, so the Satellite1 top
sits flush in a single flat surface rather than perched on a shoulder. Assembled,
it reads as one object. Nothing is glued \u2014 every part comes back apart with a
hex key.</p>

<div class="warn"><strong>The one thing that matters most</strong>
<p>Do not print the big parts first. Print the eight small test pieces, measure
them, and let us size your files to the printer you actually own.</p>
<p>Skipping this is how people lose four days of ASA to a cabinet that will not
seal. The test pieces take an evening.</p></div>

<h2>How this goes</h2>

<div class="step"><h3><span class="num">01</span>Print eight test pieces</h3>
<p>Small, quick, and they tell us exactly how your printer lays down plastic \u2014
holes, inserts, seats, gaskets.</p>
<a class="btn" href="calibrate.html">Start here</a></div>

<div class="step"><h3><span class="num">02</span>Measure them</h3>
<p>We show you where to put the calipers and which box to type each number into.
No arithmetic on your side.</p>
<a class="btn blue" href="calibrate.html">Measuring guide</a></div>

<div class="step"><h3><span class="num">03</span>Get your parts</h3>
<p>Printer dead on? Download the standard files. A little off? We generate a set
corrected for <em>your</em> machine.</p>
<a class="btn blue" href="parts.html">Part files</a></div>

<div class="step"><h3><span class="num">04</span>Build it</h3>
<p>Nine steps, one picture each, in the order that actually works. Wrap it in
speaker cloth at the end if you want to.</p>
<a class="btn blue" href="assemble.html">Assembly steps</a></div>

<h2>Before you spend anything</h2>
<div class="note"><strong>Three things to check</strong>
<ul>
<li><b>Your kit.</b> A FutureProofHomes Satellite1 <b>Batch 1</b> \u2014 Core
rev4.1 with HAT rev4.1. Batch 2 / Satellite1.1 will not fit, and there is no
workaround in this design.</li>
<li><b>Your printer.</b> You need <b>{req["long_mm"]:.0f} &times;
{req["short_mm"]:.0f}&nbsp;mm</b> of usable bed and <b>{req["tallest_mm"]:.0f}&nbsp;mm</b>
of height. The outer skin is three stacked segments rather than one tall shell,
so a failed print costs you one segment, not the whole body.</li>
<li><b>Your filament.</b> ASA for the rigid parts, PETG if you prefer. A little
TPU 95A for the flexible ones. You want an enclosed printer and dry filament \u2014
ASA will warp otherwise, and a warped cabinet will not seal.</li>
</ul></div>

<p>You will also need one Dayton ND91-4 driver, two Dayton Audio DSA115-PR
radiators, M3 screws and heat-set inserts, <b>M3&nbsp;&times;&nbsp;\u23004
shoulder screws with a 16&nbsp;mm shoulder</b>, a sheet of 2&nbsp;mm closed-cell
foam, and two 6&nbsp;mm steel plates. Full list in
<a href="parts.html#shopping">step&nbsp;3</a>.</p>

<div class="warn"><strong>Read this before you order screws</strong>
<p>The four screws holding the Satellite1 top must be <b>shoulder screws</b>, not
ordinary M3. The shoulder bottoms out and lets the top float on rubber bushings,
which keeps the woofer from shaking your microphones.</p>
<p>With ordinary screws the rubber carries under 3% of the load and does nothing
at all. If the top feels rock solid, you have the wrong screws.</p></div>

<h2>Where this honestly stands</h2>
<p>Nobody has built one yet. The geometry, clearances, seals and volumes all pass
a strict set of automated checks, and every part has been measured against every
other part \u2014 but no one has printed a whole one, sealed it, and put a
microphone in front of it.</p>
<p>So fit, sealing, sound, heat and wake-word behaviour are all still unproven.
Your checks along the way are not extra credit; they are the first real evidence
this design works. If something does not fit, that is genuinely useful \u2014 please
open an issue.</p>

<p class="next"><a class="btn" href="calibrate.html">Calibrate your printer</a></p>
"""
    return _shell("index.html", "Start", body)


def _print_settings() -> str:
    """Shared by both printing rounds: the settings are identical, and the
    reason they must not change between rounds is the whole point."""
    return """
<div class="step"><h3><span class="num">01</span>Use your real settings</h3>
<p>Print with the <b>exact settings you will use for the actual parts</b>. That
is the point &mdash; we are measuring your printer, not the file. Change the
settings later and every measurement stops meaning anything.</p>
<ul>
<li>0.4 mm nozzle, 0.20 mm layers</li>
<li>5 walls, 6 top and 6 bottom layers, 35% gyroid infill</li>
<li><b>No supports</b></li>
<li>5 mm brim on the hard (ASA) pieces</li>
<li>ASA: 250&ndash;260 &deg;C nozzle, 100&ndash;110 &deg;C bed, printer enclosed</li>
<li>PETG instead: 235&ndash;250 &deg;C nozzle, 75&ndash;85 &deg;C bed</li>
</ul></div>

<div class="step"><h3><span class="num">02</span>Cool, then clean up carefully</h3>
<p>Snap off the brim and pick off any stringing. Then stop.</p>
<p><b>Do not sand, file or ream anything.</b> A piece that came out wrong is
information, and we correct it with numbers. Sand it to fit and you have thrown
away the measurement &mdash; and the real parts will still be wrong.</p></div>
"""


#: The calibration rounds, in order.  Titles live here so the tab strip and the
#: panels cannot drift apart, which is what happened when the same flow was
#: described separately on two pages.
CALIBRATION_TABS = (
    ("print1", "Print this one part"),
    ("scale", "Your printer's scale"),
    ("print2", "Print the other seven"),
    ("measure", "Measure those seven"),
    ("done", "Get your parts"),
)


def _tab_strip() -> str:
    buttons = "".join(
        f'<button role="tab" id="tab-{key}" aria-controls="panel-{key}" '
        f'aria-selected="{"true" if index == 0 else "false"}" '
        f'data-tab="{key}"><span class="n">{index + 1}</span>{escape(label)}</button>'
        for index, (key, label) in enumerate(CALIBRATION_TABS)
    )
    return f'<div class="tabs" role="tablist">{buttons}</div>'


def _panel(key: str, body: str, back: str = "", forward: str = "") -> str:
    """One calibration round.  A panel shows only what its own round needs."""
    index = [name for name, _ in CALIBRATION_TABS].index(key)
    nav = ['<div class="tab-nav">']
    if back:
        previous = CALIBRATION_TABS[index - 1][0]
        nav.append(
            f'<button class="btn ghost" data-goto="{previous}">&larr; {escape(back)}</button>'
        )
    nav.append('<span class="spacer"></span>')
    if forward:
        following = CALIBRATION_TABS[index + 1][0]
        nav.append(f'<button class="btn" data-goto="{following}">{escape(forward)} &rarr;</button>')
    nav.append("</div>")
    hidden = "" if index == 0 else " hidden"
    return (
        f'<section class="panel" role="tabpanel" id="panel-{key}" '
        f'aria-labelledby="tab-{key}"{hidden}>{body}{"".join(nav)}</section>'
    )


def _measurement_card(
    number: str,
    title: str,
    image: str,
    where: str,
    how: str,
    field_html: str,
) -> str:
    return f"""
<div class="step"><h3><span class="num">{number}</span>{title}</h3>
<img src="images/{image}" alt="{escape(title)}">
<p><b>Which piece:</b> {where}</p>
<p><b>What to do:</b> {how}</p>
{field_html}
</div>
"""


def _calibrate() -> str:
    """The whole calibration, as five tabs on one page.

    This used to be two pages -- a printing page and a measuring page -- joined
    by notes telling a builder to fill in the first two boxes, leave, print
    seven more parts, and come back to box three. That instruction is easy to
    miss and expensive to miss, because measurements 3 onward all read features
    the printer's scale error has already moved. A tab simply does not show the
    inputs that do not belong to its round yet, which is a structure the builder
    cannot skim past.
    """
    stage_one = [
        (source, filename, quantity, _material(source))
        for source, filename, quantity in CALIBRATION_STAGE_ONE
    ]
    stage_two = [
        (source, filename, quantity, _material(source))
        for source, filename, quantity in CALIBRATION_STAGE_TWO
        if source != "coupon_official_interface"
    ]

    print1 = _panel(
        "print1",
        f"""
<h2>Print this one part</h2>
<p class="lede">One file. Nothing to type yet and nothing to measure yet. It
carries a marked slot and a flat edge, and those two features are what tell us
how your printer scales.</p>
{_file_table(stage_one, CALIBRATION_DIR)}
{_print_settings()}
<div class="warn"><strong>Only this one, for now</strong>
<p>There are seven more test pieces and they are deliberately not on this tab.
Every one of them measures something your printer&rsquo;s scale error has
already moved &mdash; hole diameters, seat widths, the gasket gap, the cable
bore. Print them before we know your scale and each reading mixes two errors
together with no way to separate them.</p>
<p>This is not hypothetical. A builder printed the speaker-fit piece straight
from the shipped files on a printer running 0.9% small, found the driver would
not seat, and reasonably concluded the seat was the wrong shape. It was the
right shape, 0.34&nbsp;mm too small.</p></div>
""",
        forward="I printed it",
    )

    scale = _panel(
        "scale",
        f"""
<h2>Your printer&rsquo;s scale</h2>
<p class="lede">Two measurements, both off the part you just printed. Nothing
else is asked for on this tab.</p>
{
            "".join(
                (
                    _measurement_card(
                        "1",
                        "How wide is the marked slot?",
                        "calibration_official_interface.png",
                        "the piece marked <code>01_CHECK_SATELLITE_TOP_FIT</code>",
                        "Find the engraved words <b>MEASURE XY 110.60</b>. Put the <b>small inside "
                        "jaws</b> of your calipers inside that slot and open them until they touch. "
                        "Do it at three different heights and use the middle answer.",
                        '<div class="field"><label class="q" for="xy">Type what the calipers say (mm)</label>'
                        '<div class="help">If your printer is perfect this reads 110.60.</div>'
                        '<input type="number" id="xy" step="0.01" placeholder="110.60">'
                        '<div class="verdict" id="xy_v"></div></div>',
                    ),
                    _measurement_card(
                        "2",
                        "How thick is the flat edge?",
                        "calibration_official_interface.png",
                        "the same piece",
                        "Use the <b>big outside jaws</b> on a clean flat edge of the same piece. "
                        "Measure at four corners and use the middle answer.",
                        '<div class="field"><label class="q" for="z">Type what the calipers say (mm)</label>'
                        '<div class="help">If your printer is perfect this reads 3.00.</div>'
                        '<input type="number" id="z" step="0.01" placeholder="3.00">'
                        '<div class="verdict" id="z_v"></div></div>',
                    ),
                )
            )
        }
<div id="stage1_wait" class="note"><strong>Waiting for both measurements</strong>
<p>Type the two numbers above and your scale appears here.</p></div>

<div id="stage1_perfect" class="ok hide"><strong>Your printer is dead on</strong>
<p>No scale correction needed. Print the round two pieces exactly as they came
in the download, then carry on to the next tab.</p></div>

<div class="note hide" id="stage1_out"><strong>Round one done &mdash; your scale</strong>
<p id="stage1_pct" class="mono"></p>
<p>Take this code to the generator. It rebuilds the remaining seven test pieces
at your printer&rsquo;s scale, and <em>those</em> are the ones to print.</p>
<pre class="code" id="stage1_code"></pre>
<div class="btn-row">
<button class="btn" id="stage1_copy" type="button">Copy my round one code</button>
<a class="btn blue" href="{
            COLAB_TEST_PIECES
        }" target="_blank" rel="noopener">Generate the other seven</a>
</div>
</div>
""",
        back="Back to printing",
        forward="I have my seven files",
    )

    print2 = _panel(
        "print2",
        f"""
<h2>Print the other seven</h2>
<p class="lede">Print <em>your</em> regenerated files from the previous tab
&mdash; not the copies below. Those are the uncorrected originals, listed so you
can see what you are getting.</p>
{_file_table(stage_two, CALIBRATION_STAGE_TWO_DIR)}
<div class="note"><strong>One at a time</strong>
<p>One piece per print, so a failure costs minutes rather than hours. The last
file on the list is the flexible cable seal, so load TPU for that one.</p>
<p>Same settings as round one. If you changed anything, go back and reprint the
first part too &mdash; your scale measurement no longer describes this
printer.</p></div>
""",
        back="Back to your scale",
        forward="They are printed",
    )

    measure = _panel(
        "measure",
        f"""
<h2>Measure those seven</h2>
<p class="lede">These read your regenerated prints, so what is left is the
error your printer has <em>beyond</em> its scale.</p>
<div class="warn stale" id="stale_warn"><strong>Your scale changed</strong>
<p>You edited a round-one measurement after filling these in. If the seven
pieces in front of you were printed from the older code, they no longer match
&mdash; regenerate and reprint them before trusting anything below.</p></div>
{
            "".join(
                (
                    _measurement_card(
                        "3",
                        "Which hole does an M3 screw drop through?",
                        "calibration_fasteners.png",
                        "the piece marked <code>02_CHECK_SCREWS_AND_INSERTS</code>",
                        "There are three holes, labelled 3.4, 3.5 and 3.6. Try your M3 screw in each. "
                        "Pick the <b>smallest</b> one it falls through <b>on its own, with no pushing</b>.",
                        '<div class="field"><label class="q" for="clear">Pick the hole</label>'
                        '<select id="clear"><option value="3.4" selected>3.4 — the smallest one</option>'
                        '<option value="3.5">3.5 — the middle one</option>'
                        '<option value="3.6">3.6 — the biggest one</option></select></div>',
                    ),
                    _measurement_card(
                        "4",
                        "Which hole holds a heat-set insert best?",
                        "calibration_fasteners.png",
                        "the same piece",
                        "Melt an insert into the 4.0, 4.1, 4.2 and 4.3 holes. Pick the one where it "
                        "went in <b>straight and level with the surface</b>, did not crack the plastic, "
                        "and does not spin.",
                        '<div class="field"><label class="q" for="bore">Pick the hole</label>'
                        '<select id="bore"><option value="4.0">4.0</option><option value="4.1">4.1</option>'
                        '<option value="4.2" selected>4.2</option><option value="4.3">4.3</option></select></div>',
                    ),
                    _measurement_card(
                        "5",
                        "Does your speaker drop in?",
                        "calibration_driver.png",
                        "the piece marked <code>03_CHECK_SPEAKER_FIT</code>",
                        "Put your real Dayton ND91-4 into the ring. It should drop in <b>by hand</b> "
                        "and sit flat. Leave the box at 0 if it does. If it is too tight, type a small "
                        "positive number to make the hole bigger (try 0.2). If it is sloppy, type a "
                        "small negative number.",
                        '<div class="field"><label class="q" for="dcut">Change the hole size by (mm)</label>'
                        '<div class="help">0 means "it was fine". Most people leave this at 0.</div>'
                        '<input type="number" id="dcut" step="0.05" value="0">'
                        '<div class="verdict" id="dcut_v"></div></div>'
                        '<div class="field"><label class="q" for="dflange">How thick is the speaker\'s metal rim? (mm)</label>'
                        '<div class="help">Measure the flat outer lip of the speaker in four places.</div>'
                        '<input type="number" id="dflange" step="0.01" value="3.00">'
                        '<div class="verdict" id="dflange_v"></div></div>',
                    ),
                    _measurement_card(
                        "6",
                        "Does your radiator drop in?",
                        "calibration_radiator.png",
                        "the piece marked <code>04_CHECK_RADIATOR_FIT</code>",
                        "Same idea, with one passive radiator.",
                        '<div class="field"><label class="q" for="pcut">Change the hole size by (mm)</label>'
                        '<div class="help">0 means "it was fine".</div>'
                        '<input type="number" id="pcut" step="0.05" value="0">'
                        '<div class="verdict" id="pcut_v"></div></div>'
                        '<div class="field"><label class="q" for="pflange">How thick is the radiator\'s rim? (mm)</label>'
                        '<input type="number" id="pflange" step="0.01" value="4.00">'
                        '<div class="verdict" id="pflange_v"></div></div>',
                    ),
                    _measurement_card(
                        "7",
                        "How much does your foam squash?",
                        "calibration_gasket.png",
                        "the two pieces marked <code>05_GASKET_TEST_BASE</code> and <code>06_GASKET_TEST_TOP</code>",
                        "Measure your foam sheet on its own first. Then put a strip between the two "
                        "pieces and screw them together until they <b>stop</b> — until the two hard "
                        "edges touch. Measure the gap that is left.",
                        '<div class="field"><label class="q" for="sheet">Foam thickness on its own (mm)</label>'
                        '<input type="number" id="sheet" step="0.01" value="2.00">'
                        '<div class="verdict" id="sheet_v"></div></div>'
                        '<div class="field"><label class="q" for="gap">Gap once fully tightened (mm)</label>'
                        '<input type="number" id="gap" step="0.01" value="1.50">'
                        '<div class="verdict" id="gap_v"></div></div>',
                    ),
                    _measurement_card(
                        "8",
                        "Do the wires fit the rubber seal?",
                        "calibration_cable.png",
                        "the piece marked <code>07_CHECK_CABLE_HOLE</code> and the bendy TPU seal",
                        "Push your two real speaker wires through the seal, then push the seal into "
                        "the hole. It should take <b>firm finger pressure</b> and then stay put. Leave "
                        "the box at 0 if that worked.",
                        '<div class="field"><label class="q" for="cable">Change the hole size by (mm)</label>'
                        '<div class="help">0 means "it was fine".</div>'
                        '<input type="number" id="cable" step="0.05" value="0">'
                        '<div class="verdict" id="cable_v"></div></div>',
                    ),
                )
            )
        }
""",
        back="Back to printing",
        forward="Show my result",
    )

    done = _panel(
        "done",
        """
<h2>Get your parts</h2>
<div class="step" id="summary">
<p class="lede" id="status">Fill in the boxes on the earlier tabs.</p>
<div id="perfect" class="ok hide"><strong>Great news &mdash; your printer is spot on</strong>
Nothing needs changing. You can download the normal parts and start printing.</div>
<div id="needs" class="note hide"><strong>Your printer needs small corrections</strong>
That is completely normal. Copy the code below and take it to the generator,
which makes a set of parts that fits your printer exactly.</div>
<div id="code" class="code-big hide"></div>
<div id="problems" class="warn hide"></div>
<div class="btn-row">
<button class="btn" id="copy">Copy my code</button>
<a class="btn blue" id="go" href="parts.html">Go to step 2 &rarr;</a>
</div>
</div>
""",
        back="Back to measuring",
    )

    body = f"""
<h1>Calibrate your printer</h1>
<p class="lede">Two rounds of test prints. Round one measures how your printer
scales; round two is regenerated at that scale and measures everything else.
Work the tabs in order &mdash; each shows only what that round needs.</p>

<div class="note"><strong>Have these to hand from round two onward</strong>
<p>Digital calipers reading to 0.01 mm, one M3 screw, one heat-set insert, your
actual driver and one radiator, and a strip of your foam sheet.</p>
<p>Measure the real components, not the numbers on their datasheets. Tolerances
are why this page exists.</p></div>

<div class="note"><strong>Nothing you type here leaves your browser</strong>
<p>The whole calculation runs locally. No account, no upload, no tracking; the
correction code is simply your numbers, encoded. Entries are remembered on this
device, so you can close the tab between rounds.</p>
<p>One caveat, so it is not a surprise: generating corrected parts opens Google
Colab, and you paste the code into Google&rsquo;s service at that point. The
code contains printer measurements and nothing else.</p></div>

{_tab_strip()}
{print1}
{scale}
{print2}
{measure}
{done}
<script src="wizard.js"></script>
"""
    return _shell("calibrate.html", "Calibrate", body)


def _parts() -> str:
    ultra = [
        (source, filename, quantity, _material(source))
        for source, filename, quantity in ULTRA_PRINT_ORDER
    ]
    fabric = [
        (source, filename, quantity, _material(source))
        for source, filename, quantity in FABRIC_WRAP_PRINT_ORDER
    ]
    # The official top parts are not in PARTS -- they are preserved upstream
    # STLs, printed in the same rigid filament as the body.
    official = [
        (source, filename, quantity, "ASA")
        for source, filename, quantity in OFFICIAL_TOP_PRINT_ORDER
    ]
    body = f"""
<h1>Get your parts</h1>
<p class="lede">Two routes. Take whichever one the measuring page sent you down.</p>

<div class="step"><h3><span class="num">01</span>Your printer came out dead on</h3>
<p>Then you are done here. Download the standard files below and start printing.</p></div>

<div class="step"><h3><span class="num">02</span>You have a correction code</h3>
<p>Normal, and nothing to worry about — most printers need a few tenths. We
generate a set of parts sized for your machine. You install nothing.</p>
<ol>
<li>Click the button below. It opens a free Google Colab page.</li>
<li>Paste your code into the one box at the top.</li>
<li>Click <b>Runtime &rarr; Run all</b> and wait. It takes about 15 minutes.</li>
<li>Your corrected parts download as a single zip.</li>
</ol>
<a class="btn" href="{COLAB_PARTS}" target="_blank" rel="noopener">Make my corrected parts</a>
<p class="help">You need a free Google account, because that is what runs the
calculation. Nothing is installed on your computer.</p></div>

<div class="warn"><strong>Check the correction worked</strong>
<p>If you entered a correction, reprint the test piece it applied to from your
<em>new</em> files and measure it again. Two minutes now, versus finding out on a
six-hour cabinet print.</p></div>

<h2>The enclosure</h2>
{_material_summary()}
<p>Print everything in this table. The quantity column matters — some files need
printing more than once, and the <b>Print in</b> column is not decoration.</p>
{_file_table(ultra, ENCLOSURE_DIR)}

<div class="note"><strong>The outer skin is three parts</strong>
<p>They stack and interlock: <code>10_OUTER_SKIN_BOTTOM</code>,
<code>11_OUTER_SKIN_MIDDLE_WITH_GRILLES</code>, <code>12_OUTER_SKIN_TOP</code>.
Small ribs inside each joint give a firm press fit, so the seam closes to a thin
shadow line rather than a step you can feel.</p>
<p>Print the middle and top upright. Print the bottom one <b>inverted</b>, cut
face down on the bed — that keeps its curved base off the plate.</p></div>

<h2>Wrapping it in cloth? Use these three instead</h2>
<p>Same three skin segments, with a hidden channel inside each roll to tuck the
fabric edge into. Download these <em>instead of</em> files 10, 11 and 12 above —
not as well as.</p>
{_file_table(fabric, FABRIC_DIR)}

<div class="warn"><strong>Decide before you print</strong>
<p>The channel cannot be added afterwards, and the standard files deliberately
do not have it — on a bare printed finish it reads as a line across the body.</p></div>

<h2>The three foam seals</h2>
<p>These are <b>not printed</b>. Print the templates on paper at 100% scale, lay
them on 2&nbsp;mm closed-cell EPDM foam sheet, and cut the shapes out with a
sharp knife. That is what makes the cabinet airtight.</p>
<table class="files"><tr><th>Template — click to download (DXF)</th><th>How many</th><th>Cut from</th></tr>
<tr><td><a href="{RAW}/{GASKET_DIR}/driver_gasket.dxf">driver_gasket.dxf</a></td><td class="qty">1</td>{_material_cell("2 mm closed-cell EPDM")}</tr>
<tr><td><a href="{RAW}/{GASKET_DIR}/passive_radiator_gasket.dxf">passive_radiator_gasket.dxf</a></td><td class="qty">2</td>{_material_cell("2 mm closed-cell EPDM")}</tr>
<tr><td><a href="{RAW}/{GASKET_DIR}/divider_gasket.dxf">divider_gasket.dxf</a></td><td class="qty">1</td>{_material_cell("2 mm closed-cell EPDM")}</tr>
</table>

<h2>The Satellite1 top</h2>
<p>These six are the original FutureProofHomes parts, unmodified. Not optional —
they carry your buttons, your light ring and your microphones.</p>
{_file_table(official, OFFICIAL_DIR)}

<div class="warn"><strong>Do not print these three old parts</strong>
The original speaker chamber, speaker plate, and rubber ring are replaced by the
Ultra parts. Printing them wastes filament.</div>

<h2 id="shopping">The shopping list</h2>
<p>Every line links to somewhere in the US that sells it. These are starting
points, not endorsements — buy wherever you like, the specification is what
matters.</p>
{_shopping_table()}

<p class="next"><a class="btn" href="assemble.html">I have everything — go to step 3 &rarr;</a></p>
"""
    return _shell("parts.html", "Get parts", body)


def _assemble() -> str:
    from satellite1_ultra.documentation import ASSEMBLY_STEPS, GASKETS

    cards = []
    for step in ASSEMBLY_STEPS:
        cards.append(
            f"""
<div class="step" id="s{step["number"]}"><h3><span class="num">{step["number"]}</span>{escape(step["title"])}</h3>
<img src="images/{Path(step["image"]).name}" alt="{escape(step["title"])}">
<p><b>You need:</b> {escape(step["parts"])}</p>
<p><b>Screws:</b> {escape(step["fasteners"])} &nbsp; <b>Seal:</b> {escape(step["gasket"])}</p>
<p><b>Do this:</b> {escape(step["action"])}</p>
<div class="ok"><strong>It is right when</strong>{escape(step["pass"])}</div>
<div class="warn"><strong>Careful</strong>{escape(step["warning"])}</div>
</div>"""
        )
    gasket_rows = "".join(
        f"<tr><td>{escape(row['id'])}</td><td>{escape(row['name'].replace('_', ' '))}</td>"
        f'<td class="qty">{escape(row["quantity"])}</td>'
        f"<td>{escape(row['cutting'].split(' from ')[-1])}</td></tr>"
        for row in GASKETS
        if row["id"] != "G04"
    )
    body = f"""
<h1>Build it</h1>
<p class="lede">In this order, with a picture for each step. Nothing is glued —
every joint is a screw into a heat-set insert, so you can open it again whenever
you want.</p>

<div class="note"><strong>How tight is tight enough</strong>
<p>Hold the <b>short end</b> of the hex key, not the long one. That limits your
leverage, which is the point. Stop the moment the parts meet evenly.</p>
<p>These are screws going into brass inserts in plastic. There is no "one more
turn for luck" — there is only stripping the insert out of the part.</p></div>

<div class="warn"><strong>Four of the screws are special</strong>
<p>The ones holding the Satellite1 top are <b>M3 × ⌀4 shoulder screws with a
16 mm shoulder</b>. Tighten those until the shoulder bottoms out firmly — the
head then stops just clear of the plate, leaving it floating on rubber. That gap
is deliberate and it is what stops the woofer shaking your microphones.</p>
<p>If the top ends up rock solid with no give at all, you have ordinary M3 screws
in there and the isolation is doing nothing.</p></div>

<h2>First, cut your three foam seals</h2>
<p>These are the only parts you do not print. You cut them from your foam sheet
using the templates below. Print each template at <b>exactly 100% scale</b> —
turn off "fit to page", then measure it against a ruler before you cut anything.
A template printed at 97% will produce a seal that looks fine and leaks.</p>
<table><tr><th>ID</th><th>Seal</th><th>How many</th><th>Template</th></tr>{gasket_rows}</table>
<p>Each seal must be a <b>single unbroken ring</b>. Do not butt two pieces
together to make up a length — a sealed cabinet is either sealed or it isn't, and
a join is the place it won't be.</p>
<img src="images/gasket_placement.png" alt="Where each seal sits">

<h2>Lay it all out first</h2>
<p>Worth ten minutes: put every part on the table and check it against this
picture, which names each piece and the file it came from. Finding a missing part
now is much better than finding it with a cabinet half-sealed.</p>
<img src="images/exploded_parts_identification.png" alt="Every part, named">
<p>The screws all look similar, so sort them by length before you start.</p>
<img src="images/fastener_identification.png" alt="Screw lengths">

<h2>The nine steps</h2>
{"".join(cards)}

<h2>Before you use it properly</h2>
<div class="warn"><strong>Check all of these</strong>
<ul>
<li>No bubbles anywhere during the gentle leak test</li>
<li>The speaker cone pushes <b>outward</b> on a quick polarity test</li>
<li>Both side radiators move freely and never scrape</li>
<li>Every button clicks once and springs back</li>
<li>Every light works, and the microphones hear you across the room</li>
<li>USB-C plugs in without rubbing the skin</li>
<li>Wi-Fi connects normally</li>
<li>No buzzing, rattling, whistling, or hot spots</li>
<li>The Satellite top sits flush with the flat top &mdash; a hairline, not a step</li>
<li>None of the three skin segments rocks or rattles when you tap the body</li>
</ul>
Stop using it if any of these fail. Fix the cause, then test again.</div>

<div class="note"><strong>Opening it again later</strong>
Unplug it and wait five minutes. Take the bottom off first. Always replace a
seal you have disturbed, and never cut a wire to get a part out.</div>
<img src="images/service_disassembly.png" alt="The order things come apart">

<p class="next"><a class="btn" href="index.html">Back to the start</a></p>
"""
    return _shell("assemble.html", "Build it", body)


#: Renders the site needs; copied next to the pages so GitHub Pages can serve them.
SITE_IMAGES = (
    "assembly_iso.png",
    "product_iso.png",
    "calibration_official_interface.png",
    "calibration_fasteners.png",
    "calibration_driver.png",
    "calibration_radiator.png",
    "calibration_gasket.png",
    "calibration_cable.png",
    "gasket_placement.png",
    "exploded_parts_identification.png",
    "fastener_identification.png",
    "service_disassembly.png",
    *(
        f"assembly_stage_{index:02d}_{name}.png"
        for index, name in (
            (1, "identify"),
            (2, "inserts"),
            (3, "driver"),
            (4, "radiators"),
            (5, "sealing"),
            (6, "ballast"),
            (7, "shell"),
            (8, "upper"),
            (9, "final"),
        )
    ),
)


def generate_site(output: Path = ROOT / "site", root: Path = ROOT) -> list[Path]:
    """Write the complete builder website."""
    output.mkdir(parents=True, exist_ok=True)
    images = output / "images"
    images.mkdir(exist_ok=True)

    written: list[Path] = []
    pages = {
        "index.html": _index(_printer_limits(root)),
        "calibrate.html": _calibrate(),
        "parts.html": _parts(),
        "assemble.html": _assemble(),
    }
    for name, content in pages.items():
        path = output / name
        path.write_text(content, encoding="utf-8")
        written.append(path)

    for asset in ("style.css", "wizard.js"):
        source = root / "wizard" / asset
        if not source.is_file():
            raise FileNotFoundError(f"missing site asset: {source}")
        shutil.copy2(source, output / asset)
        written.append(output / asset)

    renders = root / "reports" / "renders"
    for name in SITE_IMAGES:
        source = renders / name
        if not source.is_file():
            raise FileNotFoundError(f"site image not generated yet: {source}")
        shutil.copy2(source, images / name)
        written.append(images / name)
    return written
