"use strict";
/* Calibration maths for the builder site.
   Mirrors CALIBRATION_LIMITS in src/satellite1_ultra/configuration.py. The real
   build re-validates everything; this only gives instant feedback. */

const LIMITS = {
  xy_scale_correction_fraction: [-0.03, 0.03],
  z_scale_correction_fraction: [-0.03, 0.03],
  fastener_clearance_diameter_offset_mm: [-0.8, 0.8],
  insert_bore_diameter_offset_mm: [-0.5, 0.5],
  driver_cutout_diameter_offset_mm: [-1.0, 1.0],
  passive_radiator_cutout_diameter_offset_mm: [-1.0, 1.0],
  cable_passage_diameter_offset_mm: [-0.8, 0.8],
  gasket_sheet_thickness_mm: [1.5, 2.5],
  gasket_compressed_thickness_offset_mm: [-0.25, 0.25],
  active_driver_flange_thickness_mm: [2.0, 5.0],
  passive_radiator_flange_thickness_mm: [2.0, 6.0],
};
const KEYS = Object.keys(LIMITS);

/* A correction only matters if it moves real geometry. The largest part is
   about 212 mm, so a 0.0005 scale error moves it about 0.1 mm — below what a
   printer repeats anyway. Anything inside these bands leaves the shipped files
   unchanged, and the builder can skip the rebuild entirely. */
const NEGLIGIBLE = {
  xy_scale_correction_fraction: 0.0005,
  z_scale_correction_fraction: 0.0005,
  fastener_clearance_diameter_offset_mm: 0.001,
  insert_bore_diameter_offset_mm: 0.001,
  driver_cutout_diameter_offset_mm: 0.001,
  passive_radiator_cutout_diameter_offset_mm: 0.001,
  cable_passage_diameter_offset_mm: 0.001,
  gasket_compressed_thickness_offset_mm: 0.02,
};
const NOMINAL = {
  gasket_sheet_thickness_mm: 2.0,
  active_driver_flange_thickness_mm: 3.0,
  passive_radiator_flange_thickness_mm: 4.0,
};

const el = (id) => document.getElementById(id);
const num = (id) => parseFloat(el(id).value);
const round = (v, p) => Math.round(v * 10 ** p) / 10 ** p;

function say(id, text, good) {
  const node = el(id + "_v");
  if (!node) return;
  node.textContent = text;
  node.className = "verdict " + (text ? (good ? "good" : "bad") : "");
}

function compute() {
  const problems = [];
  const xy = num("xy"), z = num("z"), sheet = num("sheet"), gap = num("gap");
  const dflange = num("dflange"), pflange = num("pflange");

  if (!Number.isFinite(xy) || xy <= 0) {
    problems.push("Measurement 1 (the marked slot) is empty.");
    say("xy", "Type the number your calipers show.", false);
  } else {
    const pct = (110.6 / xy - 1) * 100;
    say("xy", Math.abs(pct) <= 3
      ? (Math.abs(pct) < 0.05 ? "Spot on." : `Fine — we'll correct by ${pct.toFixed(2)}%.`)
      : `That is ${pct.toFixed(1)}% out, which is too far. Re-measure, or check the print.`,
      Math.abs(pct) <= 3);
  }
  if (!Number.isFinite(z) || z <= 0) {
    problems.push("Measurement 2 (the flat edge) is empty.");
    say("z", "Type the number your calipers show.", false);
  } else {
    const pct = (3.0 / z - 1) * 100;
    say("z", Math.abs(pct) <= 3
      ? (Math.abs(pct) < 0.05 ? "Spot on." : `Fine — we'll correct by ${pct.toFixed(2)}%.`)
      : `That is ${pct.toFixed(1)}% out, which is too far. Re-measure, or check the print.`,
      Math.abs(pct) <= 3);
  }

  const values = {
    xy_scale_correction_fraction: round(110.6 / xy - 1, 7),
    z_scale_correction_fraction: round(3.0 / z - 1, 7),
    fastener_clearance_diameter_offset_mm: round(parseFloat(el("clear").value) - 3.4, 3),
    insert_bore_diameter_offset_mm: round(parseFloat(el("bore").value) - 4.2, 3),
    driver_cutout_diameter_offset_mm: round(num("dcut"), 3),
    passive_radiator_cutout_diameter_offset_mm: round(num("pcut"), 3),
    cable_passage_diameter_offset_mm: round(num("cable"), 3),
    gasket_sheet_thickness_mm: round(sheet, 3),
    gasket_compressed_thickness_offset_mm: round(gap - 0.75 * sheet, 3),
    active_driver_flange_thickness_mm: round(dflange, 3),
    passive_radiator_flange_thickness_mm: round(pflange, 3),
  };

  const squash = Number.isFinite(sheet) && sheet > 0 ? (1 - gap / sheet) * 100 : NaN;
  if (!Number.isFinite(squash)) {
    problems.push("Measurement 7 (the foam) needs both numbers.");
    say("gap", "Type both foam numbers.", false);
  } else if (squash < 15 || squash > 45) {
    say("gap", `Your foam squashed by ${squash.toFixed(0)}%. It needs to be between `
      + `15% and 45%. Check you tightened until the two hard edges touched.`, false);
    problems.push(`The foam squashed by ${squash.toFixed(0)}%, which is outside 15–45%.`);
  } else {
    say("gap", `Good — it squashed by ${squash.toFixed(0)}%.`, true);
  }
  if (Number.isFinite(sheet)) {
    const ok = sheet >= 1.5 && sheet <= 2.5;
    say("sheet", ok ? "Fine." : "That should be between 1.5 and 2.5 mm. Is it 2 mm foam?", ok);
  }

  const friendly = {
    driver_cutout_diameter_offset_mm: ["dcut", "The speaker hole change"],
    passive_radiator_cutout_diameter_offset_mm: ["pcut", "The radiator hole change"],
    cable_passage_diameter_offset_mm: ["cable", "The cable hole change"],
    active_driver_flange_thickness_mm: ["dflange", "The speaker rim thickness"],
    passive_radiator_flange_thickness_mm: ["pflange", "The radiator rim thickness"],
  };
  for (const key of KEYS) {
    const [low, high] = LIMITS[key];
    const value = values[key];
    const pair = friendly[key];
    if (!Number.isFinite(value)) {
      problems.push(`${pair ? pair[1] : key} is empty.`);
      if (pair) say(pair[0], "Type a number.", false);
      continue;
    }
    if (value < low || value > high) {
      problems.push(`${pair ? pair[1] : key} (${value}) must be between ${low} and ${high}.`);
      if (pair) say(pair[0], `That must be between ${low} and ${high}.`, false);
    } else if (pair && key.endsWith("_offset_mm")) {
      say(pair[0], value === 0 ? "No change needed." : "Fine.", true);
    } else if (pair) {
      say(pair[0], "Fine.", true);
    }
  }
  return { values, problems };
}

/* True when nothing measured actually moves the geometry. */
function isStandard(values) {
  for (const [key, band] of Object.entries(NEGLIGIBLE)) {
    if (Math.abs(values[key]) > band) return false;
  }
  for (const [key, nominal] of Object.entries(NOMINAL)) {
    if (Math.abs(values[key] - nominal) > 0.05) return false;
  }
  return true;
}

/* Compact, typo-resistant code: the eleven values in fixed order. */
function encode(values) {
  const packed = KEYS.map((k) => values[k]).join(",");
  return "S1U-" + btoa(packed).replace(/=+$/, "");
}

let currentCode = "";

function refresh() {
  const { values, problems } = compute();
  const ok = problems.length === 0;
  const perfect = ok && isStandard(values);
  currentCode = ok ? encode(values) : "";

  el("problems").classList.toggle("hide", ok);
  if (!ok) {
    el("problems").innerHTML = "<strong>Not quite there yet</strong><ul>"
      + problems.map((p) => `<li>${p}</li>`).join("") + "</ul>";
  }
  el("perfect").classList.toggle("hide", !perfect);
  el("needs").classList.toggle("hide", !(ok && !perfect));
  el("code").classList.toggle("hide", !(ok && !perfect));
  el("copy").classList.toggle("hide", !(ok && !perfect));
  if (ok && !perfect) el("code").textContent = currentCode;

  el("status").textContent = !ok
    ? "Check the boxes marked in red above."
    : perfect
      ? "All eight checks passed, and your printer needs no corrections at all."
      : "All eight checks passed. Your printer needs a few small corrections.";
  el("go").textContent = perfect
    ? "Go to step 3 and download the parts →"
    : "Go to step 3 with my code →";
}

document.querySelectorAll("input, select").forEach((node) => {
  node.addEventListener("input", refresh);
  node.addEventListener("change", refresh);
});

const copyButton = el("copy");
if (copyButton) {
  copyButton.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(currentCode);
      copyButton.textContent = "Copied";
      setTimeout(() => { copyButton.textContent = "Copy my code"; }, 1600);
    } catch {
      copyButton.textContent = "Select the code above and copy it";
    }
  });
}

refresh();
