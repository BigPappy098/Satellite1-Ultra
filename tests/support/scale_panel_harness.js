const fs = require("fs"), vm = require("vm");
const store = {};
global.localStorage = { getItem: (k) => (k in store ? store[k] : null), setItem: (k, v) => { store[k] = v; } };
const V = { xy: "", z: "", clear: "3.4", bore: "4.2", dcut: "0", pcut: "0",
            cable: "0", sheet: "2.00", gap: "1.50", dflange: "3.00", pflange: "4.00" };
const mk = (id) => ({ id, value: V[id] !== undefined ? V[id] : "", textContent: "", innerHTML: "",
  hidden: false, dataset: {}, attrs: {}, addEventListener() {}, setAttribute(k, v) { this.attrs[k] = v; },
  focus() {}, classList: { _s: new Set(), add(c) { this._s.add(c); }, remove(c) { this._s.delete(c); },
    toggle(c, on) { on === undefined ? (this._s.has(c) ? this._s.delete(c) : this._s.add(c)) : (on ? this._s.add(c) : this._s.delete(c)); },
    has(c) { return this._s.has(c); } } });
const nodes = {};
const get = (id) => { if (id.endsWith("_v")) return null; if (!nodes[id]) nodes[id] = mk(id); return nodes[id]; };
global.navigator = { clipboard: { writeText: async () => {} } };
global.window = { scrollTo() {} };
global.document = { getElementById: get, querySelector: () => null,
  querySelectorAll: (s) => (s === "input, select" ? Object.keys(V).map(get) : []), addEventListener() {} };
vm.runInThisContext(fs.readFileSync(process.argv[2], "utf8"));

const shot = (label) => ({ label,
  waiting: !get("stage1_wait").classList.has("hide"),
  perfect: !get("stage1_perfect").classList.has("hide"),
  codeShown: !get("stage1_out").classList.has("hide"),
  code: get("stage1_code").textContent,
  pct: get("stage1_pct").textContent });

const steps = [];
steps.push(shot("on load, boxes empty"));
get("xy").value = "110.60"; get("z").value = "3.00"; refreshStageOne();
steps.push(shot("typed the perfect numbers"));
get("xy").value = "109.60"; refreshStageOne();
steps.push(shot("then corrected xy to 109.60"));
get("xy").value = "110.60"; refreshStageOne();
steps.push(shot("back to perfect"));
get("xy").value = "109.60"; refreshStageOne();
steps.push(shot("and off again"));
process.stdout.write(JSON.stringify(steps, null, 1));
