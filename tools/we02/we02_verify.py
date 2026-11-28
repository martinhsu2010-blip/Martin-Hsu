#!/usr/bin/env python3
"""Claude-owned independent verifier for the T-017 (WE-02) planning artifacts.

Does NOT import the generator. Re-derives checks from the WE-01 fixtures and the generated files
(rasterization uses the WE-01D painter, not the generator's own code). Writes we02_validation.md.
Usage: python3 -B tools/we02/we02_verify.py --input-dir DIR --plan-dir DIR [--out-validation FILE] [--repo DIR]
"""
import argparse, collections, hashlib, json, os, subprocess, sys
import xml.etree.ElementTree as ET

BASE = "84319439243b51aa8d119e33eb62a0637feea887"
BASE_HASH = {"index.html": "c8131a487d0dc81316e6adcf19226722cdce02728150ca5cee86575875cf63a3",
             "sw.js": "d8cf792dd060773bf8e592b2420aa14ee29b94c4de0e724b511766993dd295a9"}
SPEC_BOUNDS = {"B1": [-10, 490, 830, 1330], "B2": [-1000, -400, 720, 1170], "B3": [-740, -240, -910, -510]}
SPEC_AREA = {"B1": 250000, "B2": 270000, "B3": 200000}
P1_TARGET = {"B1": 10, "B2": 12, "B3": 18}
FOOT = {"R01": (42, 34), "R02": (48, 42), "R05": (24, 22), "R08": (38, 24)}
P1_ENG = {"X01", "H02", "ENVELOPE_B1_ST_0305"}
FORBIDDEN = ("C01", "H01", "AVE_110")


class Res:
    def __init__(self):
        self.rows, self.n = [], 0

    def chk(self, gate, ok, msg):
        self.n += 1
        self.rows.append((gate, bool(ok), msg))

    @property
    def fails(self):
        return [r for r in self.rows if not r[1]]


def J(p):
    return json.load(open(p, encoding="utf-8"))


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def inter(a, b):
    return max(0, min(a[2], b[2]) - max(a[0], b[0])) * max(0, min(a[3], b[3]) - max(a[1], b[1]))


def paint_cells(item_polys, win, beach, D):
    cors = [{"polygon": p, "bounds": [min(q[0] for q in p), min(q[1] for q in p), max(q[0] for q in p), max(q[1] for q in p)]} for p in item_polys]
    x0, z0, w, h = win[0], win[1], win[2] - win[0], win[3] - win[1]
    buf = bytearray(w * h)
    D._paint_corridors_to_mask(buf, x0, z0, w, h, cors)
    cells = {(x0 + i % w, z0 + i // w) for i, v in enumerate(buf) if v}
    bx = [(min(q[0] for q in b), max(q[0] for q in b)) for b in beach]
    gone = {c for c in cells if any(lo <= c[0] and c[0] + 1 <= hi for lo, hi in bx)}
    return cells - gone, len(gone)


def verify(indir, plandir, repo):
    R = Res()
    plan = J(os.path.join(plandir, "district_plan.json"))
    cp, st, rs, fe, geo = (J(os.path.join(indir, n + ".json")) for n in ("conditional_parcels", "internal_streets", "road_survey", "feasibility", "map_geometry"))
    man = J(os.path.join(indir, "inputs_manifest.json"))
    for n, h in plan["inputs"].items():
        R.chk("MP03", sha(os.path.join(indir, n)) == h == man["files"][n], f"input hash {n}")
    R.chk("MP01", plan["base_sha"] == BASE and plan["polygon_revision"] == 2, "BASE and polygon_revision 2")
    env = {r: {p["id"]: p for p in cp["scenarios"]["ENVELOPE"][r]["parcels"]} for r in SPEC_BOUNDS}
    streets = {s["street_id"]: s for r in SPEC_BOUNDS for s in st["scenarios"]["ENVELOPE"][r]["selected_streets"]}
    # MP01 / MP02
    for r, sb in SPEC_BOUNDS.items():
        reg = plan["regions"][r]
        ev = fe["scenarios"]["ENVELOPE"]["verdict_evidence"]["road_access"][r]
        R.chk("MP01", reg["bounds_spec"] == sb == ev["bounds_spec"], f"{r} bounds_spec")
        R.chk("MP01", reg["bounds_internal"] == [sb[0], sb[2], sb[1], sb[3]] == ev["bounds_internal"], f"{r} spec->internal conversion")
        R.chk("MP02", reg["gross_area_m2"] == SPEC_AREA[r] == (sb[1] - sb[0]) * (sb[3] - sb[2]), f"{r} area")
    R.chk("MP02", plan["total_gross_area_m2"] == 720000, "total 720,000")
    bi = {r: plan["regions"][r]["bounds_internal"] for r in SPEC_BOUNDS}
    R.chk("MP02", all(inter(bi[a], bi[b]) == 0 for a in bi for b in bi if a < b), "regions do not overlap")
    # per-parcel structure
    eng_by_phase = {"1": {e["id"] for e in plan["phases"]["1"]["engineering"]["items"]}, "2": {e["id"] for e in plan["phases"]["2"]["engineering"]["items"]}}
    R.chk("MP18", eng_by_phase["1"] == P1_ENG, "Phase 1 engineering set is X01, H02, ST_0305")
    added = eng_by_phase["2"] - eng_by_phase["1"]
    R.chk("MP18", eng_by_phase["1"] < eng_by_phase["2"] and "C02" in added and len(added) == 2 and len(added & set(("ENVELOPE_B1_ST_0085", "ENVELOPE_B1_ST_0115"))) == 1, "Phase 2 adds C02 plus exactly one of ST_0085/ST_0115")
    R.chk("MP09", not any(f in e for e in eng_by_phase["2"] for f in FORBIDDEN), "no C01/H01/AVE_110 in engineering sets")
    ids = collections.Counter()
    existing_net = {r["id"] for r in geo["roads"]}
    for p in plan["parcels"]:
        r, i, ph = p["region"], p["parcel_id"], p["phase"]
        ids[i] += 1
        src = env[r].get(i)
        R.chk("MP03", src is not None and src["prototype_id"] == p["prototype_id"] and src["bounds"] == p["bounds_internal"] and src["orientation"] == p["orientation"]
              and src["dependency_chain"] == p["dependency_chain"] and src["area_m2"] == p["area_m2"], f"{i} traceable to WE-01 ENVELOPE")
        b = p["bounds_internal"]
        w, d = b[2] - b[0], b[3] - b[1]
        fw, fd = FOOT.get(p["prototype_id"], (-1, -1))
        R.chk("MP06", p["orientation"] in (0, 90) and (w, d) == ((fw, fd) if p["orientation"] == 0 else (fd, fw)) and w * d == p["area_m2"]
              and p["polygon"] == [[b[0], b[1]], [b[2], b[1]], [b[2], b[3]], [b[0], b[3]]], f"{i} polygon equals footprint rectangle")
        eng = {e for e in p["dependency_chain"] if not e.startswith("J:")}
        R.chk("MP18", eng == set(p["engineering_required"]) and eng <= eng_by_phase[str(ph)] and not any(f in c for c in p["dependency_chain"] for f in FORBIDDEN), f"{i} dependency closure")
        if p["dependency_chain"]:
            R.chk("MP08", p["dependency_chain"][-1].startswith("J:") and p["dependency_chain"][-1].split("->")[1].rsplit("@", 1)[0] in existing_net, f"{i} chain ends at an existing verified road")
            if p["internal_street_id"]:
                R.chk("MP08", p["dependency_chain"][0] == p["internal_street_id"] and streets[p["internal_street_id"]]["source_road_id"] in p["dependency_chain"], f"{i} street chain")
        else:
            R.chk("MP08", p["we01_status"] == "DIRECT" and p["source_road_id"] in existing_net, f"{i} direct parcel on existing road")
        R.chk("MP07", inter(b, [-561, -831, -441, -753]) == 0, f"{i} outside Site A")
        R.chk("MP10", p["prototype_id"] != "R06" and (r != "B2" or (p["prototype_id"] == "R05" and p["plan_status"] == "CONDITIONAL_PROXY_R05")), f"{i} B2 proxy / no R06")
    R.chk("MP03", all(v == 1 for v in ids.values()), "no duplicate parcels")
    # MP04 / MP05 / MP06 per phase
    for ph in ("1", "2"):
        sel = [p for p in plan["parcels"] if p["phase"] <= int(ph)]
        by = {r: [p for p in sel if p["region"] == r] for r in SPEC_BOUNDS}
        if ph == "1":
            R.chk("MP04", {r: len(by[r]) for r in by} == P1_TARGET, "Phase 1 buildings 10/12/18")
        else:
            R.chk("MP04", len(by["B1"]) == 14 and len(by["B2"]) == 18 and len(by["B3"]) == 25, "Phase 2 cumulative 14/18/25 (B3 short 3)")
            R.chk("MP11", {r: plan["phases"]["2"]["deficit_by_prototype"][r] for r in by} == {"B1": {}, "B2": {}, "B3": {"R01": 1, "R05": 1, "R08": 1}}, "Phase 2 deficits R01/R05/R08 = 1 each in B3")
            R.chk("MP11", plan["phases"]["2"]["status"] == {"B1": "CONDITIONAL", "B2": "CONDITIONAL_PROXY", "B3": "UNVERIFIED"} and plan["reserved_parcels"] == [], "Phase 2 statuses, no reserved parcels")
        c1 = collections.Counter(p["prototype_id"] for p in by["B1"])
        R.chk("MP05", c1["R02"] * 2 >= len(by["B1"]) and set(c1) <= {"R01", "R02"}, f"Phase {ph} B1 R02 >= 50%")
        c3 = collections.Counter(p["prototype_id"] for p in by["B3"])
        R.chk("MP05", all(c3[k] * 5 >= len(by["B3"]) for k in ("R01", "R05", "R08")), f"Phase {ph} B3 each prototype >= 20%")
        for r in by:
            for a in range(len(by[r])):
                for c in range(a + 1, len(by[r])):
                    if inter(by[r][a]["bounds_internal"], by[r][c]["bounds_internal"]) > 0:
                        R.chk("MP06", False, f"overlap {by[r][a]['parcel_id']} {by[r][c]['parcel_id']}")
        R.chk("MP06", True, f"Phase {ph} parcel overlap scan complete")
        R.chk("MP05", plan["phases"][ph]["units_total"] == sum(p["units"] for p in sel), f"Phase {ph} units recount")
    # Phase 1 is contained in Phase 2
    R.chk("MP04", all(p["phase"] in (1, 2) for p in plan["parcels"]) and sum(1 for p in plan["parcels"] if p["phase"] == 1) == 40, "Phase 2 contains the 40 Phase 1 parcels")
    known = set(streets) | {"X01", "C02", "H02"}
    unknown = (eng_by_phase["1"] | eng_by_phase["2"]) - known
    R.chk("MP09", not unknown, f"engineering ids are audited candidates only (unknown: {sorted(unknown)})")
    if unknown:
        return R, plan, "aborted"
    # MP12 raster with the WE-01D painter
    sys.path.insert(0, os.path.join(repo, "tools", "test"))
    import we01d_feasibility_analyzer as D
    cors = collections.defaultdict(list)
    for c in rs["candidate_corridors"]:
        if c["id"].startswith("CAND_"):
            cors[c["id"].split("_")[1]].append(c["polygon"])
    reg_of = lambda e: streets[e]["region_id"] if e in streets else {"X01": "B1", "C02": "B1", "H02": "B2"}[e]
    polys = lambda e: [streets[e]["corridor_geometry"]["polygon"]] if e in streets else cors[e]
    beach = geo["beach_regions"]
    win = {r: tuple(bi[r]) for r in bi}
    for r in SPEC_BOUNDS:
        allr = [x for e in list(streets) + ["X01", "C02", "H02"] if reg_of(e) == r for x in polys(e)]
        n, _ = paint_cells(allr, win[r], beach, D) if allr else (set(), 0)
        R.chk("MP12", len(n) == fe["scenarios"]["ENVELOPE"]["land_accounting"]["regions"][r]["A_new_road"], f"{r} WE-01 A_new_road reproduced with the WE-01D painter")
    for ph in ("1", "2"):
        for r in SPEC_BOUNDS:
            cells, gone = paint_cells([x for e in eng_by_phase[ph] if reg_of(e) == r for x in polys(e)], win[r], beach, D) if any(reg_of(e) == r for e in eng_by_phase[ph]) else (set(), 0)
            la = plan["phases"][ph]["land_accounting"][r]
            pc = set()
            for p in plan["parcels"]:
                if p["region"] == r and p["phase"] <= int(ph):
                    b = p["bounds_internal"]
                    pc |= {(x, z) for x in range(b[0], b[2]) for z in range(b[1], b[3])}
            R.chk("MP12", la["A_new_road_raster"] == len(cells) and la["beach_cells_excluded"] == gone, f"Phase {ph} {r} new-road raster recomputed")
            R.chk("MP12", not (pc & cells), f"Phase {ph} {r} no selected parcel cell is a road cell")
            tot = la["A_protected"] + la["A_unknown"] + la["A_unavailable"] + la["A_new_road_raster"] + la["selected_parcel_cells"] + la["A_other_eligible"]
            R.chk("MP12", abs(tot - la["A_gross"]) <= 1 and la["A_other_eligible"] >= 0 and la["selected_parcel_cells"] == len(pc), f"Phase {ph} {r} mutually exclusive classes conserve area")
            R.chk("MP07", not any(sx in cells for sx in {(x, z) for x in range(-561, -441) for z in range(-831, -753)}), f"Phase {ph} {r} roads outside Site A")
    # G0-W2: independent recomputation of the Phase 2 street choice
    base_c, _ = paint_cells([x for e in P1_ENG | {"C02"} if reg_of(e) == "B1" for x in polys(e)], win["B1"], beach, D)
    cands = []
    for s_id in ("ENVELOPE_B1_ST_0085", "ENVELOPE_B1_ST_0115"):
        allow = P1_ENG | {"C02", s_id}
        have = collections.Counter(q["prototype_id"] for q in env["B1"].values() if {e for e in q["dependency_chain"] if not e.startswith("J:")} <= allow)
        cc, _ = paint_cells([x for e in allow if reg_of(e) == "B1" for x in polys(e)], win["B1"], beach, D)
        if have["R01"] >= 7 and have["R02"] >= 7:
            cands.append((len(cc - base_c), s_id))
    R.chk("MP18", bool(cands) and plan["street_choice_phase2"]["chosen"] == min(cands)[1] and "ENVELOPE_B1_ST_0085" == min(cands)[1], "Phase 2 street = fewer added cells, then street_id")
    sa = [f for f in geo["site_a"] if f["id"] == "SITEA_PROTECT"][0]["polygon"]
    sab = [min(q[0] for q in sa), min(q[1] for q in sa), max(q[0] for q in sa), max(q[1] for q in sa)]
    R.chk("MP07", plan["site_a_protection"]["bounds_internal"] == sab == [-561, -831, -441, -753] and plan["site_a_protection"]["area_m2"] == 9360 == (sab[2] - sab[0]) * (sab[3] - sab[1]), "Site A protection bounds and 9,360 m2 equal map_geometry")
    # lengths and beach
    for ph, length, beach_m2 in (("1", 1110.214, 0.0), ("2", 1390.214, 224.0)):
        e = plan["phases"][ph]["engineering"]
        R.chk("MP08", abs(e["length_m"] - length) < 1e-6 and e["beach_encroachment_m2"] == beach_m2, f"Phase {ph} engineering {length} m, beach {beach_m2}")
    # MP13 SVG and markdown
    root = ET.parse(os.path.join(plandir, "masterplan.svg")).getroot()
    bad = [e.tag for e in root.iter() if e.tag.split("}")[-1] in ("script", "foreignObject", "image")]
    R.chk("MP13", not bad, "SVG has no script/foreignObject/image")
    sp = {e.get("data-parcel"): (e.get("data-phase"), e.get("data-prototype")) for e in root.iter() if e.get("data-parcel") and e.get("data-phase") != "0"}
    R.chk("MP13", sp == {p["parcel_id"]: (str(p["phase"]), p["prototype_id"]) for p in plan["parcels"]}, "SVG parcels equal JSON parcels, phases and prototypes")
    sr = {(e.get("data-road"), e.get("data-phase")) for e in root.iter() if e.get("data-road")}
    exp = {(e["id"], "1") for e in plan["phases"]["1"]["engineering"]["items"]} | {(e["id"], "2") for e in plan["phases"]["2"]["added_engineering"]}
    exp = {x for x in exp if x[0] in ("X01", "C02", "H02") or x[0].startswith("ENVELOPE_")}
    R.chk("MP13", sr == exp, "SVG roads equal JSON phase engineering")
    md = open(os.path.join(plandir, "masterplan.md"), encoding="utf-8").read()
    dm = open(os.path.join(plandir, "dependency_matrix.md"), encoding="utf-8").read()
    for s in ("1110.214", "1390.214", "720,000", plan["street_choice_phase2"]["chosen"], "每棟" if False else "R08 一棟四戶", "9,360"):
        R.chk("MP13", s in md, f"masterplan.md contains {s}")
    R.chk("MP13", all(r in dm for r in SPEC_BOUNDS) and "WE-03" in dm, "dependency_matrix.md covers regions and systems")
    R.chk("MP13", not any(w in md for w in ("PENDING", "TODO")), "no placeholder text")
    R.chk("MP10", "R06" in md and "平地代理" in md, "masterplan.md states B2 proxy and R06 status")
    # MP14 / MP15 production
    prod = "SKIPPED (no git repository)"
    try:
        ok = True
        for f, h in BASE_HASH.items():
            blob = subprocess.run(["git", "-C", repo, "show", f"{BASE}:{f}"], capture_output=True, check=True).stdout
            ok &= hashlib.sha256(blob).hexdigest() == h == sha(os.path.join(repo, f))
        names = subprocess.run(["git", "-C", repo, "diff", "--name-only", BASE, "HEAD"], capture_output=True, check=True, text=True).stdout.split()
        game = [n for n in names if n.split("/")[0] not in ("specs", "tools", "docs", ".github", "handoffs") and not n.endswith(".md")]
        R.chk("MP14", ok and not game, f"index.html and sw.js equal BASE; game files changed since BASE: {game or 0}")
        R.chk("MP15", "const CACHE = 'vh-2026-11-27-02'" in open(os.path.join(repo, "sw.js")).read(), "CACHE unchanged (vh-2026-11-27-02)")
        prod = "checked"
    except Exception as ex:  # git not available: recorded, not silently passed
        R.chk("MP14", False, f"production check could not run: {ex}")
    return R, plan, prod


def report(R, plan, plandir, indir):
    L = ["# WE-02 獨立驗證紀錄（we02_validation.md）", "",
         "由 `tools/we02/we02_verify.py` 產生，不引用產生器，柵格重算使用 WE-01D 的繪製函式；結果由 Claude 負責。", "",
         f"- BASE：`{BASE}`；檢查項目數 {R.n}；失敗 {len(R.fails)}。", "", "## 來源與產物雜湊（SHA-256）", ""]
    for n, h in sorted(plan["inputs"].items()):
        L.append(f"- `{n}` {h}")
    for n in ("district_plan.json", "masterplan.svg", "masterplan.md", "dependency_matrix.md"):
        L.append(f"- `{n}` {sha(os.path.join(plandir, n))}")
    L += ["", "## 各閘門結果", "", "| 閘門 | 檢查數 | 失敗 |", "|---|---|---|"]
    by = collections.OrderedDict()
    for g, ok, m in sorted(R.rows, key=lambda r: r[0]):
        by.setdefault(g, [0, 0])[0] += 1
        by[g][1] += 0 if ok else 1
    for g, (n, f) in by.items():
        L.append(f"| {g} | {n} | {f} |")
    L += ["| MP16 | 流程閘門 | Claude G0 已完成（T-017 登記前）；Martin 批准記於 D-061 |", "| MP17 | 流程閘門 | 待 Martin 最終規劃驗收 |", "",
          "## 關鍵數字", "", f"- 第一期 {plan['phases']['1']['buildings_total']} 棟（{plan['phases']['1']['units_total']} 戶）；第二期累計 {plan['phases']['2']['buildings_total']} 棟（{plan['phases']['2']['units_total']} 戶），B3 缺 R01、R05、R08 各 1 棟。",
          f"- 第一期道路 {plan['phases']['1']['engineering']['length_m']:.3f} m（柵格 {plan['phases']['1']['new_road_raster_total']} 格）；第二期累計 {plan['phases']['2']['engineering']['length_m']:.3f} m（柵格 {plan['phases']['2']['new_road_raster_total']} 格），海灘侵占 {plan['phases']['2']['engineering']['beach_encroachment_m2']:.0f} m²。",
          f"- 第二期街道選擇：{plan['street_choice_phase2']['chosen']}（兩條對稱，規則為格數較少、其次字典序）。", "",
          "## 限制與未解問題", ""] + [f"- {x}" for x in plan["limitations"]] + [
          "- 面積為 1 m 柵格（與 WE-01 相同規則）；新增道路在海灘格不計入，與 WE-01 完整 ENVELOPE 數字（B1 8,013、B2 10,555）逐格重現。",
          "- 通過 MP01–MP18 不代表任何條件工程已完成，也不改變 WE-01 的 D3 CONDITIONAL 裁定。", ""]
    if R.fails:
        L += ["## 失敗項目", ""] + [f"- {g}: {m}" for g, ok, m in R.fails]
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input-dir", required=True)
    ap.add_argument("--plan-dir", required=True)
    ap.add_argument("--out-validation")
    ap.add_argument("--repo", default=os.getcwd())
    a = ap.parse_args(argv)
    R, plan, _ = verify(a.input_dir, a.plan_dir, a.repo)
    if a.out_validation:
        open(a.out_validation, "w", encoding="utf-8", newline="\n").write(report(R, plan, a.plan_dir, a.input_dir))
    print(f"{'OK' if not R.fails else 'FAIL'} [WE02-VERIFY] checks={R.n} fails={len(R.fails)}")
    for g, ok, m in R.fails[:20]:
        print("  FAIL", g, m)
    return 1 if R.fails else 0


if __name__ == "__main__":
    sys.exit(main())
