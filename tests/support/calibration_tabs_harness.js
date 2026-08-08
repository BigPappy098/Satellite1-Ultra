// Drive the real wizard.js through the real generated calibrate.html tab markup.
const fs = require("fs");
const html = fs.readFileSync(process.argv[2], "utf8");

const tabKeys = [...html.matchAll(/data-tab="(\w+)"/g)].map((m) => m[1]);
const gotoKeys = [...html.matchAll(/data-goto="(\w+)"/g)].map((m) => m[1]);

const store = {};
global.localStorage = {
  getItem: (k) => (k in store ? store[k] : null),
  setItem: (k, v) => { store[k] = v; },
};
const INPUTS = { xy: "110.60", z: "3.00", clear: "3.4", bore: "4.2", dcut: "0",
  pcut: "0", cable: "0", sheet: "2.00", gap: "1.50", dflange: "3.00", pflange: "4.00" };

const panels = {};
const make = (id) => ({
  id, value: INPUTS[id] !== undefined ? INPUTS[id] : "", textContent: "", innerHTML: "",
  hidden: false, dataset: {}, attrs: {},
  addEventListener() {}, setAttribute(k, v) { this.attrs[k] = v; }, focus() {},
  classList: { _s: new Set(), add(c) { this._s.add(c); }, remove(c) { this._s.delete(c); },
    toggle(c, on) { on ? this._s.add(c) : this._s.delete(c); }, has(c) { return this._s.has(c); } },
});
for (const k of tabKeys) panels["panel-" + k] = make("panel-" + k);
const nodes = {};
const el = (id) => {
  if (id.endsWith("_v")) return null;
  if (panels[id]) return panels[id];
  if (!nodes[id]) nodes[id] = make(id);
  return nodes[id];
};
const tabButtons = tabKeys.map((k) => { const n = make("tab-" + k); n.dataset.tab = k; return n; });
const gotoButtons = gotoKeys.map((k) => { const n = make("goto-" + k); n.dataset.goto = k; return n; });

global.navigator = { clipboard: { writeText: async () => {} } };
global.window = { scrollTo() {} };
global.document = {
  getElementById: el,
  querySelector: (s) => (s.includes("aria-selected") ? tabButtons.find((b) => b.attrs["aria-selected"] === "true") || null : null),
  querySelectorAll: (s) => {
    if (s === ".tabs button") return tabButtons;
    if (s === "[data-goto]") return gotoButtons;
    if (s === "input, select") return Object.keys(INPUTS).map(el);
    return [];
  },
  addEventListener() {},
};

require("vm").runInThisContext(fs.readFileSync(process.argv[3], "utf8"));

const result = { tabKeys, gotoKeys, checks: {} };
// Every data-goto target must be a real tab, or a Next button goes nowhere.
result.checks.gotoTargetsExist = gotoKeys.every((k) => tabKeys.includes(k));
// showTab must expose exactly one panel.
showTab("measure");
result.checks.oneVisible = tabKeys.filter((k) => !panels["panel-" + k].hidden).length === 1;
result.checks.correctVisible = panels["panel-measure"].hidden === false;
result.checks.selectedMarked =
  tabButtons.find((b) => b.dataset.tab === "measure").attrs["aria-selected"] === "true";
// State must survive a reload.
result.checks.persisted = JSON.parse(store["s1u.calibration.v1"] || "{}").__tab === "measure";
// Editing a scale field after entering the measuring round must raise the flag.
el("xy").value = "109.60";
markStale();
result.checks.staleFlagged = el("stale_warn").classList.has("on");
// ...and clear again when it is put back.
el("xy").value = "110.60";
markStale();
result.checks.staleClears = !el("stale_warn").classList.has("on");
// An unknown tab key must be ignored rather than blanking the page.
showTab("nonexistent");
result.checks.unknownIgnored = tabKeys.filter((k) => !panels["panel-" + k].hidden).length === 1;
process.stdout.write(JSON.stringify(result));
