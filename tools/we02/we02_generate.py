#!/usr/bin/env python3
"""Claude-owned T-017 (WE-02) planning artifact generator. Offline, stdlib only, deterministic.

Reads the formal WE-01 e_formal fixtures and writes district_plan.json, masterplan.svg,
masterplan.md and dependency_matrix.md. No analysis of the game, no verdict changes.
Usage: python3 -B tools/we02/we02_generate.py --input-dir DIR --out DIR
"""
import argparse, hashlib, json, math, os, sys

BASE = "84319439243b51aa8d119e33eb62a0637feea887"
REGIONS = ("B1", "B2", "B3")
TARGETS = {  # building targets by phase (cumulative) and prototype, spec section 5/6
    1: {"B1": {"R01": 5, "R02": 5}, "B2": {"R05": 12}, "B3": {"R01": 4, "R05": 10, "R08": 4}},
    2: {"B1": {"R01": 7, "R02": 7}, "B2": {"R05": 18}, "B3": {"R01": 6, "R05": 16, "R08": 6}},
}
PHASE1_ENG = {"X01", "H02", "ENVELOPE_B1_ST_0305"}
PHASE2_STREETS = ("ENVELOPE_B1_ST_0085", "ENVELOPE_B1_ST_0115")
FILES = ("conditional_parcels", "internal_streets", "road_survey", "feasibility", "map_geometry")
SITE_A = (-561, -831, -441, -753)  # xmin, zmin, xmax, zmax (internal order)


def load(indir):
    man = json.load(open(os.path.join(indir, "inputs_manifest.json")))
    if man["base_sha"] != BASE:
        sys.exit("manifest BASE mismatch")
    data, hashes = {}, {}
    for n in FILES:
        raw = open(os.path.join(indir, n + ".json"), "rb").read()
        h = hashlib.sha256(raw).hexdigest()
        if man["files"][n + ".json"] != h:
            sys.exit(f"hash mismatch {n}")
        data[n], hashes[n + ".json"] = json.loads(raw), h
    for n in FILES[:4]:
        if data[n].get("polygon_revision") != 2 or data[n].get("base_sha") != BASE:
            sys.exit(f"{n}: polygon_revision/BASE mismatch")
    return data, hashes


# ---------- geometry (own stdlib rasterizer: 1 m cells, overlap area > 1e-6) ----------
def clip_area(poly, x0, z0, x1, z1):
    """Area of polygon clipped to an axis-aligned rectangle (Sutherland-Hodgman)."""
    pts = [tuple(p) for p in poly]
    for axis, lim, keep_low in ((0, x1, True), (0, x0, False), (1, z1, True), (1, z0, False)):
        if not pts:
            return 0.0
        out, prev = [], pts[-1]
        for cur in pts:
            pin = (prev[axis] <= lim) if keep_low else (prev[axis] >= lim)
            cin = (cur[axis] <= lim) if keep_low else (cur[axis] >= lim)
            if pin != cin:
                t = (lim - prev[axis]) / (cur[axis] - prev[axis])
                out.append((prev[0] + t * (cur[0] - prev[0]), prev[1] + t * (cur[1] - prev[1])))
            if cin:
                out.append(cur)
            prev = cur
        pts = out
    a = 0.0
    for i, p in enumerate(pts):
        q = pts[(i + 1) % len(pts)]
        a += p[0] * q[1] - q[0] * p[1]
    return abs(a) / 2.0


def paint(polys, win, beach):
    """Cells (x, z) of the 1 m grid inside window win=(xmin,zmin,xmax,zmax) touched by any polygon,
    minus cells overlapping beach rectangles (WE-01 counts new road only on eligible land)."""
    cells = set()
    for poly in polys:
        xs, zs = [p[0] for p in poly], [p[1] for p in poly]
        for x in range(max(win[0], math.floor(min(xs))), min(win[2], math.ceil(max(xs)))):
            for z in range(max(win[1], math.floor(min(zs))), min(win[3], math.ceil(max(zs)))):
                if clip_area(poly, x, z, x + 1, z + 1) > 1e-6:
                    cells.add((x, z))
    gone = {c for c in cells if any(clip_area(b, c[0], c[1], c[0] + 1, c[1] + 1) > 1e-6 for b in beach)}
    return cells - gone, gone


def rect_poly(b):
    return [[b[0], b[1]], [b[2], b[1]], [b[2], b[3]], [b[0], b[3]]]


def overlap_area(a, b):
    return max(0.0, min(a[2], b[2]) - max(a[0], b[0])) * max(0.0, min(a[3], b[3]) - max(a[1], b[1]))


# ---------- selection ----------
def eng_of(p):
    return {e for e in p["dependency_chain"] if not e.startswith("J:")}


def select(parcels, targets, allowed, chosen):
    """Cumulative deterministic pick: keep chosen, then fill per prototype from allowed parcels
    ordered DIRECT first, then parcel_id."""
    sel = list(chosen)
    pool = sorted((p for p in parcels if p["id"] not in sel and eng_of(p) <= allowed),
                  key=lambda p: (p["status"] != "DIRECT", p["id"]))
    byid = {p["id"]: p for p in parcels}
    for proto, n in sorted(targets.items()):
        have = sum(1 for i in sel if byid[i]["prototype_id"] == proto)
        for p in pool:
            if have >= n:
                break
            if p["prototype_id"] == proto and p["id"] not in sel:
                sel.append(p["id"]); have += 1
    return sorted(sel)


def counts(parcels, ids, key="prototype_id"):
    byid = {p["id"]: p for p in parcels}
    c = {}
    for i in ids:
        c[byid[i][key]] = c.get(byid[i][key], 0) + 1
    return dict(sorted(c.items()))


def build(data, hashes):
    cp, st, rs, fe, geo = (data[n] for n in FILES)
    env_parcels = {r: cp["scenarios"]["ENVELOPE"][r]["parcels"] for r in REGIONS}
    regions = {}
    for r in REGIONS:
        ev = fe["scenarios"]["ENVELOPE"]["verdict_evidence"]["road_access"][r]
        regions[r] = {"bounds_spec": ev["bounds_spec"], "bounds_internal": ev["bounds_internal"]}
    win = {r: tuple(regions[r]["bounds_internal"]) for r in REGIONS}
    streets = {s["street_id"]: s for r in REGIONS for s in st["scenarios"]["ENVELOPE"][r]["selected_streets"]}
    roads = {k: v for k, v in rs["roads"].items()}
    cors = {}
    for c in rs["candidate_corridors"]:
        if c["id"].startswith("CAND_"):
            cors.setdefault(c["id"].split("_")[1], []).append(c["polygon"])
    beach = [p for p in geo["beach_regions"]]

    def road_polys(name):
        return [streets[name]["corridor_geometry"]["polygon"]] if name in streets else cors[name]

    def region_of(name):
        return streets[name]["region_id"] if name in streets else {"X01": "B1", "C02": "B1", "H02": "B2"}[name]

    def cells_for(eng, region):
        polys = [p for e in sorted(eng) if region_of(e) == region for p in road_polys(e)]
        return paint(polys, win[region], beach)

    # Phase 1
    sel1 = {r: select(env_parcels[r], TARGETS[1][r], PHASE1_ENG, []) for r in REGIONS}
    # Phase 2 street choice (G0-W2): fewer added raster cells, then street_id
    choice = []
    base_cells, _ = cells_for(PHASE1_ENG | {"C02"}, "B1")
    for s in PHASE2_STREETS:
        eng = PHASE1_ENG | {"C02", s}
        sel_b1 = select(env_parcels["B1"], TARGETS[2]["B1"], eng, sel1["B1"])
        ok = counts(env_parcels["B1"], sel_b1) == TARGETS[2]["B1"]
        cells, _ = cells_for(eng, "B1")
        choice.append({"street_id": s, "meets_b1_phase2": ok, "added_cells_vs_c02_only": len(cells - base_cells)})
    feasible = sorted((c for c in choice if c["meets_b1_phase2"]), key=lambda c: (c["added_cells_vs_c02_only"], c["street_id"]))
    if not feasible:
        sys.exit("no feasible Phase 2 street")
    pick2 = feasible[0]["street_id"]
    eng2 = PHASE1_ENG | {"C02", pick2}
    sel2 = {r: select(env_parcels[r], TARGETS[2][r], eng2, sel1[r]) for r in REGIONS}

    byid = {r: {p["id"]: p for p in env_parcels[r]} for r in REGIONS}
    parcels, phase_of = [], {}
    for r in REGIONS:
        for ph, sel in ((1, sel1[r]), (2, sel2[r])):
            for i in sel:
                phase_of.setdefault((r, i), ph)
    for r in REGIONS:
        for p in sorted(env_parcels[r], key=lambda q: q["id"]):
            ph = phase_of.get((r, p["id"]))
            if ph is None:
                continue
            if p["status"] == "DIRECT":
                pst = "VERIFIED_DIRECT"
            elif r == "B2":
                pst = "CONDITIONAL_PROXY_R05"
            else:
                pst = "CONDITIONAL" if ph == 1 else "CONDITIONAL"
            if r == "B3" and ph == 2:
                pst = "VERIFIED_DIRECT"
            parcels.append({
                "parcel_id": p["id"], "region": r, "prototype_id": p["prototype_id"], "phase": ph,
                "we01_status": p["status"], "verification_status": p["verification_status"], "plan_status": pst,
                "bounds_internal": p["bounds"], "orientation": p["orientation"], "polygon": rect_poly(p["bounds"]),
                "area_m2": p["area_m2"], "buildings": p["buildings"], "units": p["units"],
                "engineering_required": sorted(eng_of(p)), "dependency_chain": p["dependency_chain"],
                "source_road_id": p["source_road_id"], "internal_street_id": p["internal_street_id"]})

    def length_of(name):
        return streets[name]["length_m"] if name in streets else roads[name]["new_length_m"]

    def eng_block(eng):
        items = [{"id": e, "kind": "INTERNAL_STREET" if e in streets else "EXTERNAL_CANDIDATE_ROAD", "region": region_of(e),
                  "length_m": length_of(e), "status": "CONDITIONAL_VERIFIED", "built": False,
                  "beach_encroachment_m2": 0.0 if e in streets else roads[e]["beach_encroachment_m2"]} for e in sorted(eng)]
        return {"items": items, "length_m": round(sum(i["length_m"] for i in items), 3),
                "beach_encroachment_m2": round(sum(i["beach_encroachment_m2"] for i in items), 3)}

    def land(eng, sel_ids, r):
        a = fe["scenarios"]["ENVELOPE"]["land_accounting"]["regions"][r]
        cells, beach_cells = cells_for(eng, r)
        pcells = set()
        for i in sel_ids[r]:
            b = byid[r][i]["bounds"]
            pcells |= {(x, z) for x in range(b[0], b[2]) for z in range(b[1], b[3])}
        ov = len(pcells & cells)
        out = {"A_gross": a["A_gross"], "A_protected": a["A_protected"], "A_unknown": a["A_unknown"], "A_unavailable": a["A_unavailable"],
               "A_eligible": a["A_eligible"], "A_new_road_raster": len(cells), "beach_cells_excluded": len(beach_cells),
               "selected_parcel_cells": len(pcells) - ov, "parcel_road_cell_overlap": ov}
        out["A_other_eligible"] = a["A_eligible"] - out["A_new_road_raster"] - out["selected_parcel_cells"]
        tot = out["A_protected"] + out["A_unknown"] + out["A_unavailable"] + out["A_new_road_raster"] + out["selected_parcel_cells"] + out["A_other_eligible"]
        out["conservation_error_m2"] = abs(tot - a["A_gross"])
        out["envelope_full_A_new_road"] = a["A_new_road"]
        return out

    plan = {
        "schema_version": 1, "kind": "we02_district_plan", "task": "T-017", "base_sha": BASE, "polygon_revision": 2,
        "inputs": hashes, "planning_direction": "OPTION_B_ENVELOPE",
        "coordinate_formats": {"bounds_spec": "[xmin,xmax,zmin,zmax]", "bounds_internal": "[xmin,zmin,xmax,zmax]",
                               "polygon": "[[x,z],...] (rectangle of bounds_internal; orientation is 0 or 90 in the formal data)"},
        "regions": {r: dict(regions[r], gross_area_m2=fe["scenarios"]["ENVELOPE"]["land_accounting"]["regions"][r]["A_gross"],
                            audit={"A_direct": fe["scenarios"]["ENVELOPE"]["land_accounting"]["regions"][r]["A_direct"],
                                   "C_direct": fe["scenarios"]["ENVELOPE"]["capacities"][r]["C_direct"],
                                   "C_conditional": fe["scenarios"]["ENVELOPE"]["capacities"][r]["C_conditional"]}) for r in REGIONS},
        "total_gross_area_m2": sum(fe["scenarios"]["ENVELOPE"]["land_accounting"]["regions"][r]["A_gross"] for r in REGIONS),
        "site_a_protection": {"bounds_internal": list(SITE_A), "area_m2": 9360},
        "phase_targets": {str(k): v for k, v in TARGETS.items()},
        "street_choice_phase2": {"rule": "fewer added raster cells, then lexicographic street_id", "candidates": choice, "chosen": pick2},
        "phases": {},
        "parcels": parcels,
        "excluded_never_planned": {"C01": "excluded in ENVELOPE (conflict B1_R02_005)", "H01": "NOT_FEASIBLE (grade 135.633 %)",
                                   "AVE_110": "optional extension, UNVERIFIED", "U01": "existing road, not counted as new"},
        "reserved_parcels": [],
        "limitations": ["B2 plan is the R05 flat proxy; R06 has no engineering verdict", "all roads and streets are CONDITIONAL_VERIFIED, not built",
                        "Phase 2 B3 target 28 is UNVERIFIED: verified direct parcels 25, short R01 1, R05 1, R08 1",
                        "B1 Phase 1 R01 has zero margin (exactly 5 available with X01 + ENVELOPE_B1_ST_0305)",
                        "headless numbers are not device FPS; 30 FPS on phone and tablet is unverified"],
    }
    for ph, sel, eng in ((1, sel1, PHASE1_ENG), (2, sel2, eng2)):
        sel_ids = sel
        pcs = {r: counts(env_parcels[r], sel_ids[r]) for r in REGIONS}
        units = {r: sum(byid[r][i]["units"] for i in sel_ids[r]) for r in REGIONS}
        tgt = {r: sum(TARGETS[ph][r].values()) for r in REGIONS}
        n = {r: len(sel_ids[r]) for r in REGIONS}
        plan["phases"][str(ph)] = {
            "engineering": eng_block(eng),
            "buildings": n, "buildings_total": sum(n.values()), "target_buildings": tgt, "units": units, "units_total": sum(units.values()),
            "prototype_counts": pcs,
            "deficit_by_prototype": {r: {k: TARGETS[ph][r][k] - pcs[r].get(k, 0) for k in TARGETS[ph][r] if TARGETS[ph][r][k] - pcs[r].get(k, 0)} for r in REGIONS},
            "status": {"B1": "CONDITIONAL", "B2": "CONDITIONAL_PROXY", "B3": "VERIFIED_DIRECT" if ph == 1 else "UNVERIFIED"},
            "land_accounting": {r: land(eng, sel_ids, r) for r in REGIONS}}
    plan["phases"]["1"]["new_road_raster_total"] = sum(plan["phases"]["1"]["land_accounting"][r]["A_new_road_raster"] for r in REGIONS)
    plan["phases"]["2"]["new_road_raster_total"] = sum(plan["phases"]["2"]["land_accounting"][r]["A_new_road_raster"] for r in REGIONS)
    plan["phases"]["2"]["added_engineering"] = [e for e in plan["phases"]["2"]["engineering"]["items"] if e["id"] not in PHASE1_ENG]
    plan["phases"]["2"]["added_length_m"] = round(sum(e["length_m"] for e in plan["phases"]["2"]["added_engineering"]), 3)
    # WE-01 reproduction control: the full ENVELOPE corridor set must give the WE-01 A_new_road integers
    full = {r: len(cells_for({e for e in list(streets) + ["X01", "C02", "H02"] if region_of(e) == r}, r)[0]) for r in REGIONS}
    plan["we01_reproduction_control"] = {r: {"raster": full[r], "we01_A_new_road": fe["scenarios"]["ENVELOPE"]["land_accounting"]["regions"][r]["A_new_road"]} for r in REGIONS}
    plan["_corridors"] = {e: road_polys(e) for e in sorted(set(streets) | {"X01", "C02", "H02"})}
    return plan, {r: [p for p in env_parcels[r]] for r in REGIONS}, geo


# ---------- SVG ----------
def svg(plan, env_parcels, geo):
    esc = lambda s: str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    sc, pad, W = 1.5, 30, 0
    out, y = [], 60
    phase1 = {p["parcel_id"] for p in plan["parcels"] if p["phase"] == 1}
    phase2 = {p["parcel_id"] for p in plan["parcels"] if p["phase"] == 2}
    e1 = {e["id"] for e in plan["phases"]["1"]["engineering"]["items"]}
    e2 = {e["id"] for e in plan["phases"]["2"]["engineering"]["items"]}
    for r in REGIONS:
        b = plan["regions"][r]["bounds_internal"]
        w, h = (b[2] - b[0]) * sc, (b[3] - b[1]) * sc
        W = max(W, w + 2 * pad)
        tx = lambda x: (x - b[0]) * sc
        tz = lambda z: (z - b[1]) * sc
        out.append(f'<text x="{pad}" y="{y - 10}" font-size="16" font-family="sans-serif">{r} {esc(plan["regions"][r]["bounds_spec"])} gross {plan["regions"][r]["gross_area_m2"]:,.0f} m2</text>')
        out.append(f'<svg x="{pad}" y="{y}" width="{w:.1f}" height="{h:.1f}" viewBox="0 0 {w:.1f} {h:.1f}" id="panel-{r}">')
        out.append(f'<rect id="region-{r}" x="0" y="0" width="{w:.1f}" height="{h:.1f}" fill="#f4f4ef" stroke="#444"/>')
        for br in geo["beach_regions"]:
            xs, zs = [p[0] for p in br], [p[1] for p in br]
            x0, x1 = max(min(xs), b[0]), min(max(xs), b[2])
            if x1 > x0:
                out.append(f'<rect id="beach-{r}" x="{tx(x0):.1f}" y="0" width="{(x1 - x0) * sc:.1f}" height="{h:.1f}" fill="#f2e3b3" opacity="0.7"><title>beach</title></rect>')
        for rd in geo["roads"]:
            cl = [(c[0], c[2]) for c in rd["centerline"]]
            pts = " ".join(f"{tx(x):.1f},{tz(z):.1f}" for x, z in cl)
            out.append(f'<polyline id="existing-{r}-{esc(rd["id"])}" points="{pts}" fill="none" stroke="#9aa" stroke-width="{max(1, rd["carriageway_width_m"] * sc):.1f}" opacity="0.5"/>')
        sa = SITE_A
        if overlap_area(b, sa) > 0:
            out.append(f'<rect id="site-a" x="{tx(sa[0]):.1f}" y="{tz(sa[1]):.1f}" width="{(sa[2] - sa[0]) * sc:.1f}" height="{(sa[3] - sa[1]) * sc:.1f}" fill="#d9a0a0" stroke="#a00"><title>Site A protected</title></rect>')
        for p in sorted(env_parcels[r], key=lambda q: q["id"]):
            if p["id"] in phase1 or p["id"] in phase2:
                continue
            bb = p["bounds"]
            out.append(f'<rect id="avail-{p["id"]}" data-parcel="{p["id"]}" data-phase="0" x="{tx(bb[0]):.1f}" y="{tz(bb[1]):.1f}" width="{(bb[2] - bb[0]) * sc:.1f}" height="{(bb[3] - bb[1]) * sc:.1f}" fill="none" stroke="#999" stroke-dasharray="2,2"/>')
        for name, polys in sorted(plan["_corridors"].items()):
            ph = 1 if name in e1 else (2 if name in e2 else 0)
            if ph == 0 or plan["regions"][r]["bounds_spec"] is None:
                continue
            reg = "B1" if name in ("X01", "C02") or name.startswith("ENVELOPE_B1") else "B2"
            if reg != r:
                continue
            for k, pg in enumerate(polys):
                pts = " ".join(f"{tx(x):.1f},{tz(z):.1f}" for x, z in pg)
                out.append(f'<polygon id="road-{esc(name)}-{k}" data-road="{esc(name)}" data-phase="{ph}" points="{pts}" fill="{"#3a6ea5" if ph == 1 else "#7ab0e0"}" opacity="0.85"><title>{esc(name)} phase {ph}</title></polygon>')
        for p in plan["parcels"]:
            if p["region"] != r:
                continue
            bb = p["bounds_internal"]
            out.append(f'<rect id="parcel-{p["parcel_id"]}" data-parcel="{p["parcel_id"]}" data-phase="{p["phase"]}" data-prototype="{p["prototype_id"]}" x="{tx(bb[0]):.1f}" y="{tz(bb[1]):.1f}" width="{(bb[2] - bb[0]) * sc:.1f}" height="{(bb[3] - bb[1]) * sc:.1f}" fill="{"#c2410c" if p["phase"] == 1 else "#f59e0b"}" stroke="#000" stroke-width="0.5"><title>{p["parcel_id"]} {p["prototype_id"]} phase {p["phase"]} {esc(p["plan_status"])}</title></rect>')
        out.append("</svg>")
        y += int(h) + 60
    legend = ('<text x="30" y="24" font-size="18" font-family="sans-serif">VICE HORIZON VI WE-02 masterplan (T-017, ENVELOPE) +X right, +Z down, 1.5 px per m</text>'
              f'<text x="30" y="{y}" font-size="13" font-family="sans-serif">dark orange = Phase 1 parcel; light orange = Phase 2 additional; dark blue = Phase 1 road; light blue = Phase 2 road; dashed = other audited parcel; red = Site A; sand = beach. Conditional layouts, nothing built.</text>')
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">\n' % (W, y + 30, W, y + 30)
            + legend + "\n" + "\n".join(out) + "\n</svg>\n")


# ---------- markdown ----------
def md_docs(plan):
    P1, P2 = plan["phases"]["1"], plan["phases"]["2"]
    f = lambda x: f"{x:,.0f}"
    L = ["# WE-02 世界擴張總體規劃（T-017，ENVELOPE，方案 B）", "",
         "狀態：規劃文件，由 `tools/we02/we02_generate.py` 從 WE-01 正式審計產物確定性產生；不是施工授權，所有道路與街道皆未建造，WE-01 裁定未改動。", "",
         f"- Audit Game BASE：`{plan['base_sha']}`；polygon_revision {plan['polygon_revision']}。",
         "- 座標：本文使用 `[xmin, xmax, zmin, zmax]`；`district_plan.json` 的 `bounds_internal` 使用 `[xmin, zmin, xmax, zmax]`。", "", "## 1. 規劃範圍", "",
         "| 區域 | bounds_spec | 外框面積 m² | A_direct m² | C_direct | C_conditional |", "|---|---|---|---|---|---|"]
    for r in REGIONS:
        g = plan["regions"][r]
        L.append(f"| {r} | {g['bounds_spec']} | {f(g['gross_area_m2'])} | {f(g['audit']['A_direct'])} | {g['audit']['C_direct']} | {g['audit']['C_conditional']} |")
    L += ["", f"總外框 {f(plan['total_gross_area_m2'])} m²（72 ha 為規劃外框，不是新增可行走土地，也不是世界邊界擴張）。", "",
          "## 2. 分期住宅配置（棟數；戶數僅供參考）", "", "| 區域 | 第一期 | 目標 | 第二期（累計） | 目標 | 第二期狀態 |", "|---|---|---|---|---|---|"]
    for r in REGIONS:
        L.append(f"| {r} | {P1['buildings'][r]} | {P1['target_buildings'][r]} | {P2['buildings'][r]} | {P2['target_buildings'][r]} | {P2['status'][r]} |")
    L.append(f"| 合計 | {P1['buildings_total']} | 40 | {P2['buildings_total']} | 60 | 整體 60 棟 UNVERIFIED |")
    L += ["", f"戶數：第一期 {P1['units_total']} 戶（R08 一棟四戶），第二期 {P2['units_total']} 戶。目標一律以棟數計。", "", "### 原型組成", "",
          "| 區域 | 第一期 | 第二期 | 第二期缺口 |", "|---|---|---|---|"]
    for r in REGIONS:
        L.append(f"| {r} | {P1['prototype_counts'][r]} | {P2['prototype_counts'][r]} | {P2['deficit_by_prototype'][r] or '無'} |")
    L += ["", "規則：B1 R02 ≥ 50%；B3 三種原型各 ≥ 20%；B2 全部為 R05 平地代理，R06 無工程裁定。第二期 B3 缺 R01、R05、R08 各 1 棟（目標 28，已驗證 25），須另案搜尋，不得以未驗證地塊補數。", "",
          "## 3. 分期道路工程", "", "| 期別 | 工程 | 長度 m | 海灘侵占 m² |", "|---|---|---|---|"]
    for ph, blk in (("第一期", P1["engineering"]), ("第二期新增", {"items": P2["added_engineering"]})):
        for e in blk["items"]:
            L.append(f"| {ph} | {e['id']} | {e['length_m']:.3f} | {e['beach_encroachment_m2']:.0f} |")
    L += ["", f"第一期合計 {P1['engineering']['length_m']:.3f} m，海灘侵占 {P1['engineering']['beach_encroachment_m2']:.0f} m²；第二期新增 {P2['added_length_m']:.3f} m，累計 {P2['engineering']['length_m']:.3f} m，海灘侵占 {P2['engineering']['beach_encroachment_m2']:.0f} m²。",
          f"第二期街道選擇（確定性規則：新增柵格格數較少者，其次 street_id 字典序）：{plan['street_choice_phase2']['chosen']}。", "",
          "C01（ENVELOPE 因與 B1_R02_005 衝突排除）、H01（不可行）、AVE_110（未驗證）均不列入兩期必要工程；U01 為既有道路，不計入新增。", "",
          "## 4. 土地面積（1 m 柵格，與 WE-01 同一規則）", "", "| 期別 | 區域 | 新增道路 | 已選地塊 | 其他可用 | 保護／未知／不可用 | 守恆誤差 |", "|---|---|---|---|---|---|---|"]
    for ph, blk in (("第一期", P1), ("第二期", P2)):
        for r in REGIONS:
            a = blk["land_accounting"][r]
            L.append(f"| {ph} | {r} | {f(a['A_new_road_raster'])} | {f(a['selected_parcel_cells'])} | {f(a['A_other_eligible'])} | {f(a['A_protected'])}／{f(a['A_unknown'])}／{f(a['A_unavailable'])} | {a['conservation_error_m2']:.0f} |")
    L += ["", "公園與公共設施只是對剩餘土地的規劃保留標籤，不是 WE-01 的審計土地分類，也沒有面積數字；25／25／30／20 為概念參考，不是門檻。",
          "WE-01 對照：完整 ENVELOPE 道路集合以本工具重算的柵格格數 " + "、".join(f"{r} {plan['we01_reproduction_control'][r]['raster']}（WE-01 {plan['we01_reproduction_control'][r]['we01_A_new_road']:.0f}）" for r in REGIONS) + "。", "",
          "## 5. 保護與景觀", "", "- Site A 保護範圍 X [-561,-441]、Z [-831,-753]，9,360 m²；選定地塊與道路的侵占面積均為 0。",
          "- B1 保留海濱步道與海灘景觀；C02 的 224 m² 海灘侵占只在第二期，須先有景觀保護方案。", "- B2 保留山體輪廓；B3 保留既有城市格網。", "- 既有建築拆除、海岸填地與地形改造均須獨立授權。", "",
          "## 6. 未解決工程依賴", ""] + [f"- {x}" for x in plan["limitations"]] + [
          "- X01、H02、C02 與街道皆為 CONDITIONAL_VERIFIED，尚未驗證路面、地形、碰撞、車輛通行、交通 AI 與導航。", "- B2 對外只靠 H02（H01 不可行）。", "- B1 第二期必須使用 C02。", "",
          "## 7. 後續任務（僅建議，尚未授權）", "", "WE-03 串流與效能架構；WE-04 外部道路；WE-05 地形、地基與內部街道；WE-06 住宅原型庫；WE-07/08/09 各區建設與整合驗收。每項須另行規格與批准。"]
    dm = ["# WE-02 依賴矩陣（確定性產生）", "", "## 1. 區域與道路依賴", "", "| 區域 | 期別 | 必要工程 | 依賴鏈終點 | 狀態 |", "|---|---|---|---|---|"]
    for ph, blk in (("1", P1), ("2", P2)):
        for r in REGIONS:
            eng = sorted({e for p in plan["parcels"] if p["region"] == r and p["phase"] <= int(ph) for e in p["engineering_required"]})
            ends = sorted({p["dependency_chain"][-1] if p["dependency_chain"] else "既有道路（CRS／AVE）" for p in plan["parcels"] if p["region"] == r and p["phase"] <= int(ph)})
            dm.append(f"| {r} | {ph} | {', '.join(eng) or '無新增工程'} | {', '.join(ends)} | {blk['status'][r]} |")
    dm += ["", "## 2. 非道路依賴（全部尚未完成）", "", "| 系統 | 依賴 | 負責後續任務 |", "|---|---|---|",
           "| 地形與地基 | B2 R05 平地代理、R06 無裁定；各街道與住宅地基需獨立驗證 | WE-05 |", "| 建築原型 | R01、R02、R05、R08 優先；其餘後續 | WE-06 |",
           "| 串流與 LOD | 區域載入卸載、碰撞啟用範圍、材質共用 | WE-03 |", "| 效能 | 手機與平板實機 30 FPS 尚未驗證；headless 數據不可替代 | WE-03 起 |",
           "| 景觀 | C02 海灘侵占 224 m² 須先有保護方案（第二期） | WE-04 |"]
    return "\n".join(L) + "\n", "\n".join(dm) + "\n"


def dump(obj):
    return json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input-dir", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    data, hashes = load(a.input_dir)
    plan, env_parcels, geo = build(data, hashes)
    svg_text = svg(plan, env_parcels, geo)
    corridors = plan.pop("_corridors")
    plan["_corridors"] = corridors
    md, dm = md_docs(plan)
    plan.pop("_corridors")
    os.makedirs(a.out, exist_ok=True)
    for name, text in (("district_plan.json", dump(plan)), ("masterplan.svg", svg_text), ("masterplan.md", md), ("dependency_matrix.md", dm)):
        open(os.path.join(a.out, name), "w", encoding="utf-8", newline="\n").write(text)
    print("OK [WE02] P1=%d P2=%d plan_sha=%s" % (plan["phases"]["1"]["buildings_total"], plan["phases"]["2"]["buildings_total"], hashlib.sha256(dump(plan).encode()).hexdigest()[:12]))


if __name__ == "__main__":
    main()
