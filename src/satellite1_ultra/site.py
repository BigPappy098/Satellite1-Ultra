"""Generate the illustrated builder website.

The website is the primary instructions: one screen per step, big pictures,
plain language.  Every list of files, quantity, and assembly action is taken
from the same authoritative data the PDFs and the release package use, so the
site cannot drift away from what is actually shipped.
"""

from __future__ import annotations

import shutil
from html import escape
from pathlib import Path

from satellite1_ultra.builder_files import (
    CALIBRATION_PRINT_ORDER,
    OFFICIAL_TOP_PRINT_ORDER,
    ULTRA_PRINT_ORDER,
)
from satellite1_ultra.configuration import ROOT

#: Filled in once the repository is public; every download link hangs off this.
REPO = "https://github.com/BigPappy098/Satellite1-Ultra"
RAW = f"{REPO}/raw/main/release/Satellite1-Ultra-RC1"
COLAB = "https://colab.research.google.com/github/BigPappy098/Satellite1-Ultra/blob/main/notebooks/make_my_parts.ipynb"

PAGES = (
    ("index.html", "Start"),
    ("print-tests.html", "1 · Test prints"),
    ("calibrate.html", "2 · Measure"),
    ("parts.html", "3 · Get parts"),
    ("assemble.html", "4 · Build it"),
)


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


def _file_table(rows: list[tuple[str, int, str]], folder: str) -> str:
    """A download table: what to print, how many, in what material."""
    body = "".join(
        f'<tr><td><a href="{RAW}/PRINT_THESE_FILES/{folder}/{name}">{escape(name)}</a></td>'
        f'<td class="qty">{quantity}</td><td>{escape(material)}</td></tr>'
        for name, quantity, material in rows
    )
    return (
        "<table><tr><th>File — click to download</th><th>How many</th>"
        f"<th>Material</th></tr>{body}</table>"
    )


def _index() -> str:
    body = """
<h1>Let's build your Satellite1 Ultra</h1>
<p class="lede">A big-sounding speaker for your Satellite1 voice assistant.
Follow these four steps in order. You only ever download part files.</p>

<img src="images/assembly_iso.png" alt="The finished Satellite1 Ultra">

<div class="warn"><strong>Read this one thing first</strong>
Do not print the big parts yet. Print eight small test pieces first, so we can
check how your printer really behaves. Skipping this wastes days of filament.</div>

<h2>The four steps</h2>

<div class="step"><h3><span class="num">1</span>Print eight small test pieces</h3>
<p>They are small and quick. They tell us exactly how your printer prints.</p>
<a class="btn" href="print-tests.html">Start step 1</a></div>

<div class="step"><h3><span class="num">2</span>Measure them, type in the numbers</h3>
<p>We show you exactly where to put the calipers, and exactly which box to type
the number into. No maths for you to do.</p>
<a class="btn" href="calibrate.html">Go to step 2</a></div>

<div class="step"><h3><span class="num">3</span>Get your parts</h3>
<p>If your printer is spot on, you download the normal parts. If it is a little
off, we make a corrected set that fits <em>your</em> printer.</p>
<a class="btn" href="parts.html">Go to step 3</a></div>

<div class="step"><h3><span class="num">4</span>Build it</h3>
<p>Nine steps with a picture for each one. Nothing is glued, so you can always
open it again.</p>
<a class="btn" href="assemble.html">Go to step 4</a></div>

<h2>Before you spend any money</h2>
<div class="note"><strong>Check these three things</strong>
<ul>
<li><b>Your kit:</b> a FutureProofHomes Satellite1 <b>Batch 1</b> (Core rev4.1 and
HAT rev4.1). Satellite1.1 / Batch 2 does not fit.</li>
<li><b>Your printer:</b> it must really reach <b>212 &times; 192 &times; 189 mm</b>.
The outer shell is the big one. A 220 &times; 220 mm bed only works if the whole
bed is usable.</li>
<li><b>Your filament:</b> ASA for the hard parts (PETG also works), and TPU 95A
for two bendy parts.</li>
</ul></div>

<p>You will also buy one Dayton ND91-4 speaker, two SB Acoustics SB12PACR-00
passive radiators, M3 screws and heat-set inserts, a sheet of 2&nbsp;mm foam, and
two steel plates. The full shopping list is in
<a href="parts.html#shopping">step 3</a>.</p>

<p class="next"><a class="btn" href="print-tests.html">Start step 1 &rarr;</a></p>
"""
    return _shell("index.html", "Start", body)


def _print_tests() -> str:
    rows = [
        (filename, quantity, "ASA" if source != "cable_gland" else "TPU 95A")
        for source, filename, quantity in CALIBRATION_PRINT_ORDER
    ]
    body = f"""
<h1>Step 1 — Print eight small test pieces</h1>
<p class="lede">These are small and fast. They exist so you find out how your
printer really behaves <em>before</em> you spend days printing the big parts.</p>

<div class="warn"><strong>Print these, and only these, right now</strong>
Do not print the enclosure yet. It will very likely not fit until step 2 is done.</div>

<h2>Download and print</h2>
{_file_table(rows, "1_CALIBRATION_FIRST")}

<div class="step"><h3><span class="num">A</span>Use these printer settings</h3>
<p>Use the <b>same settings you will use for the real parts</b>. That is the whole
point: we are measuring your printer, not the file.</p>
<ul>
<li>0.4 mm nozzle, 0.20 mm layers</li>
<li>5 walls, 6 top and 6 bottom layers, 35% gyroid infill</li>
<li><b>No supports</b></li>
<li>5 mm brim on the hard (ASA) pieces</li>
<li>ASA: 250–260 °C nozzle, 100–110 °C bed, printer enclosed</li>
<li>PETG instead: 235–250 °C nozzle, 75–85 °C bed</li>
</ul></div>

<div class="step"><h3><span class="num">B</span>Print them one at a time</h3>
<p>One piece per print. The last one on the list is the bendy TPU seal, so load
TPU for that one.</p></div>

<div class="step"><h3><span class="num">C</span>Let them cool, then clean them up</h3>
<p>Snap off the brim. Remove any stringy bits. <b>Do not sand anything</b> — if a
piece is wrong we fix it with numbers, not sandpaper.</p></div>

<div class="ok"><strong>When all eight are printed</strong>
Grab your digital calipers and go to step 2. We will walk you through every
single measurement.</div>

<p class="next"><a class="btn" href="calibrate.html">I've printed them — go to step 2 &rarr;</a></p>
"""
    return _shell("print-tests.html", "Test prints", body)


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
    body = f"""
<h1>Step 2 — Measure your test pieces</h1>
<p class="lede">Type each number in the box under its picture. We do the maths.
Green means good. Red tells you what to fix.</p>

<div class="note"><strong>You need</strong>
Digital calipers that read to 0.01 mm, one M3 screw, one heat-set insert, your
real speaker and one radiator, and a strip of your foam sheet.</div>

{
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
            '<input type="number" id="xy" step="0.01" value="110.60">'
            '<div class="verdict" id="xy_v"></div></div>',
        )
    }

{
        _measurement_card(
            "2",
            "How thick is the flat edge?",
            "calibration_official_interface.png",
            "the same piece",
            "Use the <b>big outside jaws</b> on a clean flat edge of the same piece. "
            "Measure at four corners and use the middle answer.",
            '<div class="field"><label class="q" for="z">Type what the calipers say (mm)</label>'
            '<div class="help">If your printer is perfect this reads 3.00.</div>'
            '<input type="number" id="z" step="0.01" value="3.00">'
            '<div class="verdict" id="z_v"></div></div>',
        )
    }

{
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
        )
    }

{
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
        )
    }

{
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
        )
    }

{
        _measurement_card(
            "6",
            "Does your radiator drop in?",
            "calibration_radiator.png",
            "the piece marked <code>04_CHECK_RADIATOR_FIT</code>",
            "Same idea, with one SB12PACR-00 passive radiator.",
            '<div class="field"><label class="q" for="pcut">Change the hole size by (mm)</label>'
            '<div class="help">0 means "it was fine".</div>'
            '<input type="number" id="pcut" step="0.05" value="0">'
            '<div class="verdict" id="pcut_v"></div></div>'
            '<div class="field"><label class="q" for="pflange">How thick is the radiator\'s rim? (mm)</label>'
            '<input type="number" id="pflange" step="0.01" value="4.00">'
            '<div class="verdict" id="pflange_v"></div></div>',
        )
    }

{
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
        )
    }

{
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
        )
    }

<h2 id="result">Your result</h2>
<div class="step" id="summary">
<p class="lede" id="status">Fill in the boxes above.</p>
<div id="perfect" class="ok hide"><strong>Great news — your printer is spot on</strong>
Nothing needs changing. You can download the normal parts and start printing.</div>
<div id="needs" class="note hide"><strong>Your printer needs small corrections</strong>
That is completely normal. Copy the code below and take it to step 3, where we
make a set of parts that fits your printer exactly.</div>
<div id="code" class="code-big hide"></div>
<div id="problems" class="warn hide"></div>
<div class="btn-row">
<button class="btn" id="copy">Copy my code</button>
<a class="btn blue" id="go" href="parts.html">Go to step 3 &rarr;</a>
</div>
</div>
<script src="wizard.js"></script>
"""
    return _shell("calibrate.html", "Measure", body)


def _parts() -> str:
    ultra = [
        (filename, quantity, "TPU 95A" if source == "anti_slip_ring" else "ASA")
        for source, filename, quantity in ULTRA_PRINT_ORDER
    ]
    official = [
        (filename, quantity, "ASA") for _source, filename, quantity in OFFICIAL_TOP_PRINT_ORDER
    ]
    body = f"""
<h1>Step 3 — Get your parts</h1>
<p class="lede">Two ways to get here. Pick the one that matches what step 2 told you.</p>

<div class="step"><h3><span class="num">A</span>Step 2 said your printer is spot on</h3>
<p>Lucky you. Download the normal parts straight from the tables below and start
printing. Nothing else to do.</p></div>

<div class="step"><h3><span class="num">B</span>Step 2 gave you a code</h3>
<p>Your printer needs small corrections, which is completely normal. We will make
a set of parts sized for <em>your</em> printer. You do not install anything.</p>
<ol>
<li>Click the button below. It opens a free Google Colab page.</li>
<li>Paste your code into the one box at the top.</li>
<li>Click <b>Runtime &rarr; Run all</b> and wait. It takes about 15 minutes.</li>
<li>Your corrected parts download as a single zip.</li>
</ol>
<a class="btn" href="{COLAB}" target="_blank" rel="noopener">Make my corrected parts</a>
<p class="help">You need a free Google account, because that is what runs the
calculation. Nothing is installed on your computer.</p></div>

<div class="warn"><strong>Reprint your test pieces</strong>
If you entered a correction, print the affected test piece again from your new
files and re-check it before printing anything big.</div>

<h2>The enclosure parts</h2>
<p>Print every file here. Only one of them needs printing twice.</p>
{_file_table(ultra, "2_ULTRA_ENCLOSURE_PARTS")}

<div class="note"><strong>About the big shell</strong>
<code>10_OUTER_SHELL.3mf</code> is the biggest part at 192 &times; 212 &times; 189 mm.
Print it upright. On a 220 mm bed keep the brim to 3 mm and make sure nothing
else is using up bed space.</div>

<h2>The Satellite top parts</h2>
<p>These six are the original Satellite1 top. They are not optional — they hold
your buttons, lights and microphones.</p>
{_file_table(official, "3_SQUIRCLE_TOP_PARTS")}

<div class="warn"><strong>Do not print these three old parts</strong>
The original speaker chamber, speaker plate, and rubber ring are replaced by the
Ultra parts. Printing them wastes filament.</div>

<h2 id="shopping">The shopping list</h2>
<table>
<tr><th>What</th><th>How many</th><th>Notes</th></tr>
<tr><td>Satellite1 Batch 1 kit</td><td class="qty">1</td><td>Core rev4.1 + HAT rev4.1. Batch 2 does not fit.</td></tr>
<tr><td>Dayton Audio ND91-4 speaker</td><td class="qty">1</td><td>The main speaker.</td></tr>
<tr><td>SB Acoustics SB12PACR-00</td><td class="qty">2</td><td>The two passive radiators on the sides.</td></tr>
<tr><td>M3 heat-set inserts</td><td class="qty">48</td><td>Buy spares; they are easy to ruin.</td></tr>
<tr><td>M3 screws</td><td class="qty">52</td><td>Mixed lengths — see <code>FASTENERS.csv</code>.</td></tr>
<tr><td>2 mm closed-cell EPDM foam</td><td class="qty">1 sheet</td><td>300 &times; 300 mm is plenty.</td></tr>
<tr><td>Steel plates, 100 &times; 112 &times; 5 mm</td><td class="qty">2</td><td>The weight that stops it toppling.</td></tr>
<tr><td>Self-adhesive tuning weight</td><td class="qty">2 sets</td><td>Tiny. Trimmed to match on a 0.01 g scale.</td></tr>
<tr><td>2-pin JST-XH speaker lead</td><td class="qty">1</td><td>Red and black, 22 AWG.</td></tr>
</table>

<p class="next"><a class="btn" href="assemble.html">I have everything — go to step 4 &rarr;</a></p>
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
<h1>Step 4 — Build it</h1>
<p class="lede">Nine steps, in this order, with a picture for each. Nothing is
glued — every joint is a screw, so you can open it again later.</p>

<div class="note"><strong>How tight?</strong>
Use the <b>short end</b> of the 2 mm hex key. Stop as soon as the parts meet
evenly. These are screws going into plastic — over-tightening strips them.
Never "give it one more turn for luck".</div>

<h2>First: cut your three foam seals</h2>
<p>These are not printed. You cut them from your foam sheet using the printed
templates. Print each template at <b>exactly 100% scale</b> — turn off
"fit to page" — then check it against a ruler before cutting.</p>
<table><tr><th>ID</th><th>Seal</th><th>How many</th><th>Template</th></tr>{gasket_rows}</table>
<p>Each one must be a <b>single unbroken ring</b>. Do not join pieces together.</p>
<img src="images/gasket_placement.png" alt="Where each seal sits">

<h2>Lay everything out first</h2>
<p>Put every part on a table and check it off. This picture names every single
piece and tells you which file it came from.</p>
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
<li>Every light works, and all four microphones work</li>
<li>USB-C plugs in without rubbing the shell</li>
<li>Wi-Fi connects normally</li>
<li>No buzzing, rattling, whistling, or hot spots</li>
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
        "index.html": _index(),
        "print-tests.html": _print_tests(),
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
