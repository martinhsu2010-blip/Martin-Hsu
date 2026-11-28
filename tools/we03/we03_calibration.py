#!/usr/bin/env python3
"""T-018A1 / WE-03A deterministic calibration generator (Claude-owned; read-only analysis, no browser).

Reads index.html (as text), specs/we02/district_plan.json, the WE-01 fixtures and, when present, the measured
specs/we03/baseline_metrics.json; writes calibration_data.json, fixture_plan.json, proposed_budgets.json and the
two Markdown reports. Everything it computes itself is ANALYTIC_ESTIMATE or SOURCE_CONFIRMED; only numbers copied
from baseline_metrics.json are MEASURED_HEADLESS. The independent check (we03_calibration_check.py) recomputes
every number without importing this file.
Usage: python3 tools/we03/we03_calibration.py [--out-dir specs/we03]
"""
import argparse, csv, hashlib, json, math, random, re, statistics, subprocess, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
FX = REPO / "tools/fixtures/we01/e_formal"
L0_CSV = REPO / "tools/fixtures/we01/we01a_common_l0_cells.csv"
ENGINEERING_BASE = "e8d5250fce0ea5f07f68840481cb95d2eca803fb"
PRESET_ORDER = ["PHONE_LOW", "PHONE_MED", "TABLET_LOW", "TABLET_MED", "TABLET_HIGH", "DESKTOP_MED", "DESKTOP_HIGH", "DESKTOP_ULTRA", "IGPU_LOW", "IGPU_MED", "IGPU_HIGH"]
MEASURED_PRESETS = ["PHONE_LOW", "PHONE_MED", "TABLET_MED", "DESKTOP_HIGH"]
TRI = {"R01": (12000, 3000, 300), "R02": (20000, 5000, 600), "R05": (5000, 1200, 150), "R08": (8000, 2000, 240)}   # WE-03 draft s.11 (PROPOSED_LIMIT)
FOOT = {"R01": (42, 34), "R02": (48, 42), "R05": (24, 22), "R08": (38, 24)}                                         # WE-02 footprints (w along x, d along z)
LOD = {"PHONE_LOW": (100, 250, 650), "PHONE_MED": (120, 300, 750), "TABLET_MED": (140, 350, 850), "DESKTOP_HIGH": (200, 500, 1200)}   # draft s.8.2
SHADOW_RANGE = {"LOW": 60, "MED": 85, "HIGH": 110, "ULTRA": 130}
COMP = {40: {"R01": 9, "R02": 5, "R05": 22, "R08": 4}, 57: {"R01": 12, "R02": 7, "R05": 33, "R08": 5},
        60: {"R01": 13, "R02": 7, "R05": 34, "R08": 6}, 120: {"R01": 26, "R02": 14, "R05": 68, "R08": 12}}
GRIDS = (64, 128, 256)
RADII = (140, 180, 217, 260, 350)   # active-body radius sensitivity (m); 217 m is the G0 estimate radius
SEED = 20261128


def sh(*a):
    return subprocess.run(a, cwd=REPO, capture_output=True, text=True).stdout.strip()


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def dump(o):
    return json.dumps(o, indent=1, sort_keys=True, ensure_ascii=False) + "\n"


def pct(a, q):
    s = sorted(a); return s[max(0, min(len(s) - 1, math.ceil(q * len(s) / 100) - 1))]


# ------------------------------------------------------------------ A01 source inventory (text search; line numbers are SOURCE_CONFIRMED)
ITEMS = [  # id, topic, definition regexes, risk (assessment, not source fact), follow-up subtask
    ("A01-01", "world initialisation", [r"function buildRealisticWorld\(", r"function buildSuburbs\(", r"function buildCityDetails\(", r"function buildShowcaseSiteA\("], "residential streaming must not change the one-shot world build order or the Site A atlas lifetime", "T-018B/C3"),
    ("A01-02", "renderer and animation loop", [r"new THREE\.WebGLRenderer\(", r"function animate\(now\)"], "streaming work must run inside animate() under the frame budget; renderer is shared with post-FX", "T-018E1"),
    ("A01-03", "physics step", [r"physicsWorld\.step\("], "a single step per frame: body add/remove needs a safe point before it", "T-018D"),
    ("A01-04", "TREE_COLLIDERS (precedent)", [r"const TREE_COLLIDERS = ", r"function initTreeColliders\(", r"function refreshTreeColliders\(", r"function treeInteracting\("], "closest existing collision-streaming precedent: radius 140/180 m, 0.5 s interval, interaction guard", "T-018D"),
    ("A01-05", "existing LOD systems", [r"function updateFacadeLOD\(", r"function updateShowcaseSiteALOD\("], "two independent LOD controllers already exist; the new controller must not touch their resources", "T-018C4"),
    ("A01-06", "material, geometry, texture lifecycle", [r"function buildShowcaseFacadeMaps\(", r"function loadPolyHavenModels\(", r"\.dispose\(\)"], "no central registry; disposal is ad hoc, so registry must own only its own resources", "T-018C1"),
    ("A01-07", "fast travel and respawn", [r"function fastTravelTo\(", r"const FAST_TRAVEL = ", r"function teleportTo\("], "teleportTo has side effects (tree colliders, Site A LOD); destination readiness has no hook", "T-018E2"),
    ("A01-08", "quality switching and reset", [r"function applyQualitySetting\(", r"const QUALITY_CONFIG = ", r"function detectDevice\("], "quality switch rebuilds shadow maps/post-FX; streaming budgets must follow the preset", "T-018E1"),
    ("A01-09", "window.__VH diagnostics", [r"window\.__VH = "], "diagnostic surface is the only test hook; streaming adds fields without breaking existing keys", "T-018A2/C2"),
    ("A01-10", "?fps=1 behaviour", [r"function createFpsReadout\(", r"get\('fps'\)==='1'"], "readout gives 1 s average/min only; no percentile or frame-time list", "T-018A2"),
]
CALL_RE = {"physicsWorld.step": r"physicsWorld\.step\(", "teleportTo": r"\bteleportTo\(", "refreshTreeColliders": r"\brefreshTreeColliders\(", "updateFacadeLOD": r"\bupdateFacadeLOD\(", "updateShowcaseSiteALOD": r"\bupdateShowcaseSiteALOD\("}


def inventory(lines):
    items = []
    for iid, topic, pats, risk, nxt in ITEMS:
        syms = [{"pattern": p, "def_lines": [i + 1 for i, l in enumerate(lines) if re.search(p, l)][:12]} for p in pats]
        items.append({"id": iid, "topic": topic, "symbols": syms, "source_class": "SOURCE_CONFIRMED", "integration_risk_assessment": risk, "follow_up_subtask": nxt})
    calls = {k: [i + 1 for i, l in enumerate(lines) if re.search(r, l)] for k, r in CALL_RE.items()}
    resets = {"teleportTo_definition_and_callers": calls["teleportTo"],
              "direct_position_set_lines": [i + 1 for i, l in enumerate(lines) if re.search(r"(PLAYER\.body|chassisBody)\.position\.set\(", l)],
              "all_body_position_set_lines": [i + 1 for i, l in enumerate(lines) if re.search(r"^\s*\S*[bB]ody\.position\.set\(", l)],
              "fastTravelTo_checks": [i + 1 for i, l in enumerate(lines) if "DELIVERY.job && !bypassDelivery" in l],
              "SHOWCASE_SITE_A_bypass": [i + 1 for i, l in enumerate(lines) if "bypassDelivery" in l and "SHOWCASE_SITE_A" in l]}
    resets["creation_or_other_sites"] = [n for n in resets["all_body_position_set_lines"] if n not in resets["direct_position_set_lines"]]    # static/dynamic body construction helpers, not player or car resets
    return {"items": items, "call_lines": calls, "position_reset_inventory": resets}


# ------------------------------------------------------------------ A02 presets
def parse_quality(src):
    i = src.index("const QUALITY_CONFIG = {"); j = src.index("autoDropBelowFps", i); blk = src[i:j]
    presets = {}
    for m in re.finditer(r"^\s+([A-Z]+_[A-Z]+):\s*\{([^}]*)\}", blk, re.M):
        presets[m.group(1)] = {k: (v == "true" if v in ("true", "false") else float(v)) for k, v in re.findall(r"(\w+):\s*([\d.]+|true|false)", m.group(2))}
    fps = {k: int(v) for k, v in re.findall(r"(\w+):\s*(\d+)", re.search(r"fpsCap:\s*\{([^}]*)\}", blk).group(1))}
    dev = {m.group(1): {"levels": re.findall(r"'(\w+)'", m.group(2)), "defaultLevel": m.group(3)} for m in re.finditer(r"^\s+(PHONE|TABLET|DESKTOP|IGPU):\s*\{ levels: \[([^\]]*)\],\s*defaultLevel: '(\w+)'", blk, re.M)}
    npc = {k: int(v) for k, v in re.findall(r"(\w+):\s*(\d+)", re.search(r"npcDrawDist:\s*\{([^}]*)\}", blk).group(1))}
    return {"presets": presets, "fpsCap": fps, "devices": dev, "npcDrawDist": npc}


MAP_RULE = {  # PROPOSED_LIMIT: tier rule, not source fact. Draft s.8.2 gives the four anchor rows; others follow their device/level tier.
    "PHONE_LOW": ("PHONE_LOW", "draft anchor"), "PHONE_MED": ("PHONE_MED", "draft anchor"), "TABLET_MED": ("TABLET_MED", "draft anchor"), "DESKTOP_HIGH": ("DESKTOP_HIGH", "draft anchor"),
    "TABLET_LOW": ("PHONE_LOW", "LOW tier: same fog/shadow/pixel ratio as PHONE_LOW"), "TABLET_HIGH": ("INTERP", "between TABLET_MED and DESKTOP_HIGH (pixelRatio 1.75, ssao)"),
    "DESKTOP_MED": ("TABLET_MED", "MED tier: pixelRatio 1.0, shadow 2048, no ssao"), "DESKTOP_ULTRA": ("ULTRA", "fog 0.0006: LOD2 raised so fog transmittance at LOD2 stays comparable"),
    "IGPU_LOW": ("PHONE_LOW", "LOW tier, 60 FPS cap on weak GPU"), "IGPU_MED": ("PHONE_MED", "MED tier"), "IGPU_HIGH": ("TABLET_MED", "HIGH tier on iGPU: no ssao, smaa"),
}
INTERVAL_MS = {"LOW": 250, "MED": 200, "HIGH": 100, "ULTRA": 100}
CPU_BUDGET_MS = {"PHONE": 2, "TABLET": 2, "IGPU": 2, "DESKTOP": 4}


def lod_for(name):
    ref, why = MAP_RULE[name]
    if ref == "INTERP":
        a, b = LOD["TABLET_MED"], LOD["DESKTOP_HIGH"]; return tuple(round((x + y) / 2 / 5) * 5 for x, y in zip(a, b)), why
    if ref == "ULTRA":
        return (240, 600, 1500), why
    return LOD[ref], why


def presets_block(q):
    out = {}
    for name in PRESET_ORDER:
        dev, lvl = name.split("_"); p = q["presets"][name]; l0, l1, l2 = lod_for(name)[0]
        vis = lambda d: round(math.exp(-(p["fog"] * d) ** 2), 3)          # FogExp2 transmittance exp(-(density*distance)^2)
        out[name] = {"source_class": "SOURCE_CONFIRMED", "quality_config": p, "fps_cap": q["fpsCap"][dev], "npc_draw_dist_m": q["npcDrawDist"][lvl], "shadow_range_m": SHADOW_RANGE[lvl],
                     "existing_lod": "updateFacadeLOD + Site A showcase LOD only (no residential LOD)",
                     "proposed_mapping": {"source_class": "PROPOSED_LIMIT", "approved": False, "streaming_enabled": False, "rule": lod_for(name)[1],
                                          "lod_m": [l0, l1, l2], "hysteresis": {"upgrade_factor": 0.9, "downgrade_factor": 1.1, "cooldown_ms": 500}, "update_interval_ms": INTERVAL_MS[lvl],
                                          "preload_s": 4, "cpu_budget_ms_p95": CPU_BUDGET_MS[dev], "fog_transmittance_at_lod": [vis(l0), vis(l1), vis(l2)]}}
    return out


# ------------------------------------------------------------------ A05 speed / readiness
def speed_block(src, baseline):
    cm = src[src.index("const CAR_MODELS"):src.index("const CAR_MODELS") + 4000]
    vmax = [int(v) for v in re.findall(r"vmax:\s*(\d+)", cm)]
    default_v = int(re.search(r"this\.vmax = \(md && md\.vmax\) \|\| (\d+)", src).group(1))
    nitro = max(float(x) for x in re.findall(r"nitroBoost = ([\d.]+)", src)); step = float(re.search(r"upgMultiplier = 1 \+ \(STATE\.upgradeLevel - 1\) \* ([\d.]+)", src).group(1))
    maxlvl = int(re.search(r"STATE\.upgradeLevel < (\d+) &&", src).group(1)); run = float(re.search(r"isRunning \? ([\d.]+) :", src).group(1))
    tc = dict(re.findall(r"(\w+):\s*([\d.]+)", re.search(r"const TREE_COLLIDERS = \{([^;]*?),\s*elapsed", src).group(1)))
    vtop, upg = max(vmax + [default_v]), 1 + (maxlvl - 1) * step
    ceil = {"base_no_nitro": vtop / 3.6, "base_nitro": vtop * nitro / 3.6, "max_upgrade_no_nitro": vtop * upg / 3.6, "max_upgrade_nitro": vtop * upg * nitro / 3.6, "on_foot_run": run}
    meas = {f"{r['model'] or 'default'}|L{r['upgrade']}|{'nitro' if r['nitro'] else 'plain'}": round(r["peak_mps"], 2) for r in (baseline or {}).get("speed", {}).get("runs", [])}
    top = max(list(meas.values()) + [0])
    steps = {f"{v_name}@{ms}ms": round(v * ms / 1000, 2) for v_name, v in (("measured_peak", top), ("code_ceiling_base_nitro", ceil["base_nitro"]), ("code_ceiling_max", ceil["max_upgrade_nitro"])) for ms in (100, 200, 250)}
    skip = {}
    for name, (l0, l1, l2) in LOD.items():
        lvl = {"PHONE_LOW": 250, "PHONE_MED": 200, "TABLET_MED": 200, "DESKTOP_HIGH": 100}[name]
        for v_name, v in (("measured_peak", top), ("code_ceiling_base_nitro", ceil["base_nitro"]), ("code_ceiling_max", ceil["max_upgrade_nitro"])):
            skip[f"{name}|{v_name}"] = {"step_m": round(v * lvl / 1000, 2), "lod_band_m": [round(0.2 * b, 1) for b in (l0, l1, l2)], "step_exceeds_band": [v * lvl / 1000 > 0.2 * b for b in (l0, l1, l2)]}
    return {"source_constants": {"source_class": "SOURCE_CONFIRMED", "vmax_kmh_by_model": vmax, "default_vmax_kmh": default_v, "nitro_boost": nitro, "upgrade_step": step, "max_upgrade_level": maxlvl,
                                 "on_foot_run_mps": run, "tree_colliders": {k: float(v) for k, v in tc.items() if k in ("cell", "enter", "leave", "interval")}},
            "code_derived_ceilings_mps": {"source_class": "ANALYTIC_ESTIMATE", "note": "force limits only; drag/terrain may prevent reaching them; not a game rule", **{k: round(v, 2) for k, v in ceil.items()}},
            "measured_peak_lower_bounds_mps": {"source_class": "MEASURED_HEADLESS" if meas else "PENDING", "note": "peak on one 1.7 km straight; lower bound only", "runs": meas},
            "step_distance_m_per_update": steps, "hysteresis_skip_risk": skip,
            "t_ready_method": {"source_class": "PROPOSED_LIMIT", "claimed_measured": False, "terms": ["queue wait", "scheduler update delay", "collision body creation time", "physics safe-point wait"], "owner": "T-018D/E1 (A1 has no streaming system)"},
            "shapes_per_building": {"source_class": "SOURCE_CONFIRMED", "precedent": "buildHouseColliders: one Box shape per house, 16 houses per static body", "proposed_initial_cap": 4, "proposed_bodies_per_building": 1,
                                    "basis": "draft s.22 ratio 128 shapes / 32 bodies = 4; PROPOSED_LIMIT"}}


# ------------------------------------------------------------------ A06 chunks
def idx(v, g): return math.floor(v / g)
def cover(lo, hi, g): return list(range(math.floor(lo / g), math.ceil(hi / g)))


def chunk_block(parcels):
    res = {}
    for g in GRIDS:
        owners, cov, per = {}, [], {}
        for p in parcels:
            x0, z0, x1, z1 = p["b"]
            o = (idx((x0 + x1) / 2, g), idx((z0 + z1) / 2, g)); owners[p["id"]] = o; per[o] = per.get(o, 0) + 1
            c = [(i, j) for i in cover(x0, x1, g) for j in cover(z0, z1, g)]; cov.append(len(c))
        loads = sorted(per.values())
        res[str(g)] = {"occupied_owner_chunks": len(per), "parcels_per_chunk_max": max(loads), "parcels_per_chunk_p50": statistics.median(loads), "cross_chunk_parcels": sum(1 for c in cov if c > 1), "max_chunks_covered": max(cov),
                       "coverage_sum": sum(cov), "lod0_triangles_per_owner_chunk_max": max(sum(TRI[p["proto"]][0] for p in parcels if owners[p["id"]] == o) for o in per)}
    vec = [{"v": v, "chunk128": idx(v, 128)} for v in (-1, -2, -3, -128, -128.0001, 0, 127.9999, 128)]
    cv = [{"min": a, "max": b, "chunks128": cover(a, b, 128)} for a, b in ((0, 128), (0, 128.0001), (-128, 0), (-128.0001, 0), (120, 136), (-5, 5), (128, 256))]
    par = [{"c": c, "parent": math.floor(c / 2)} for c in (-3, -2, -1, 0, 1, 2, 3)]
    return {"source_class": "ANALYTIC_ESTIMATE", "footprint_definition": "WE-02 parcel bounds_internal rectangle (orientation 0/90 only, WE-02 G0-W7): footprint == parcel bounds", "grids": res, "index_vectors": vec, "coverage_vectors": cv, "parent_vectors": par}


# ------------------------------------------------------------------ A07 fixtures
def rect_clip_area(poly, r):
    def clip(pts, inside, inter):
        out = []
        for i, a in enumerate(pts):
            b = pts[(i + 1) % len(pts)]; ia, ib = inside(a), inside(b)
            if ia: out.append(a)
            if ia != ib: out.append(inter(a, b))
        return out
    x0, z0, x1, z1 = r; pts = [tuple(p) for p in poly]
    for ins, it in ((lambda p: p[0] >= x0, lambda a, b: (x0, a[1] + (b[1] - a[1]) * (x0 - a[0]) / (b[0] - a[0]))), (lambda p: p[0] <= x1, lambda a, b: (x1, a[1] + (b[1] - a[1]) * (x1 - a[0]) / (b[0] - a[0]))),
                    (lambda p: p[1] >= z0, lambda a, b: (a[0] + (b[0] - a[0]) * (z0 - a[1]) / (b[1] - a[1]), z0)), (lambda p: p[1] <= z1, lambda a, b: (a[0] + (b[0] - a[0]) * (z1 - a[1]) / (b[1] - a[1]), z1))):
        if not pts: return 0.0
        pts = clip(pts, ins, it)
    return abs(sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))) / 2 if len(pts) > 2 else 0.0


def overlap(a, b, gap=0.0):
    return min(a[2], b[2]) - max(a[0], b[0]) > -gap and min(a[3], b[3]) - max(a[1], b[1]) > -gap


def corridors(plan):
    st = json.load(open(FX / "internal_streets.json")); rs = json.load(open(FX / "road_survey.json"))
    streets = {s["street_id"]: s["corridor_geometry"]["polygon"] for r in ("B1", "B2", "B3") for s in st["scenarios"]["ENVELOPE"][r]["selected_streets"]}
    cand = {}
    for c in rs["candidate_corridors"]:
        if c["id"].startswith("CAND_"): cand.setdefault(c["id"].split("_")[1], []).append(c["polygon"])
    ids = sorted({i["id"] for ph in plan["phases"].values() for i in ph["engineering"]["items"]})
    return ids, {i: ([streets[i]] if i in streets else cand[i]) for i in ids}


def fixture_block(plan, terrain):
    parcels = [{"id": p["parcel_id"], "region": p["region"], "proto": p["prototype_id"], "phase": p["phase"], "b": p["bounds_internal"]} for p in plan["parcels"]]
    cells = {}
    for r in csv.DictReader(open(L0_CSV)): cells[(math.floor(float(r["x_center"]) / 5), math.floor(float(r["z_center"]) / 5))] = r["region_id"]
    hmap = {}
    if terrain:
        for x, z, h in zip(terrain["x"], terrain["z"], terrain["height_m"]): hmap[(math.floor(x / 5), math.floor(z / 5))] = h
    ids, cors = corridors(plan); site = plan["site_a_protection"]["bounds_internal"]; win = {k: v["bounds_internal"] for k, v in plan["regions"].items()}
    beach = json.load(open(FX / "map_geometry.json"))["beach_regions"]
    taken = [p["b"] for p in parcels]; rng = random.Random(SEED); extras = []

    def ok(b, region):
        w = win[region]
        if b[0] < w[0] or b[1] < w[1] or b[2] > w[2] or b[3] > w[3]: return False
        ci = [(i, j) for i in range(math.floor(b[0] / 5), math.ceil(b[2] / 5)) for j in range(math.floor(b[1] / 5), math.ceil(b[3] / 5))]
        if any(cells.get(c) != region for c in ci): return False
        if hmap:
            hs = [hmap[c] for c in ci if c in hmap]
            if len(hs) != len(ci) or max(hs) - min(hs) > TERRAIN_SPAN_M or min(hs) < TERRAIN_MIN_M: return False
        if overlap(b, site, 4) or any(overlap(b, t, 2) for t in taken): return False
        grown = [b[0] - 2, b[1] - 2, b[2] + 2, b[3] + 2]
        return not any(rect_clip_area(poly, grown) > 0 for polys in cors.values() for poly in polys)

    def place(proto, region_order):
        w, d = FOOT[proto]
        for region in region_order:
            anchors = sorted({(c[0] * 5, c[1] * 5) for c, rg in cells.items() if rg == region})
            rng.shuffle(anchors)
            for ax, az in anchors[:4000]:
                b = [ax, az, ax + w, az + d]
                if ok(b, region): return region, b
        raise SystemExit(f"cannot place synthetic {proto}")

    syn = []; counter = {}
    def add(proto, order):
        region, b = place(proto, order); k = counter.setdefault((region, proto), 0) + 1; counter[(region, proto)] = k
        o = {"id": f"SYN_{region}_{proto}_{k:03d}", "region": region, "intended_region": order[0], "classification": "B3_DENSITY" if region == order[0] == "B3" else "GLOBAL_STRESS_ONLY" if region != order[0] else "REGION_DENSITY", "proto": proto, "phase": None, "b": b, "kind": "SYNTHETIC_ONLY"}; syn.append(o); taken.append(b)
    for proto in ("R01", "R05", "R08"): add(proto, ["B3", "B1", "B2"])                            # 57 -> 60: the B3 shortfall (draft s.9 / A1-C9); B3 fits only the R01 and R05 extras, so the R08 extra falls back to B1/B2
    s60 = list(syn)
    rot = ["B1", "B2", "B3"]
    for proto, n in (("R01", 13), ("R02", 7), ("R05", 34), ("R08", 6)):
        for i in range(n): add(proto, rot[i % 3:] + rot[:i % 3])
    objs = [dict(p, kind="WE02_PARCEL") for p in parcels] + syn
    for o in objs:
        o["owner_chunk_128"] = [idx((o["b"][0] + o["b"][2]) / 2, 128), idx((o["b"][1] + o["b"][3]) / 2, 128)]
        o["coverage_chunks_128"] = [[i, j] for i in cover(o["b"][0], o["b"][2], 128) for j in cover(o["b"][1], o["b"][3], 128)]
    sets = {"40": [p["id"] for p in parcels if p["phase"] == 1], "57": [p["id"] for p in parcels], "60": [p["id"] for p in parcels] + [s["id"] for s in s60], "120": [o["id"] for o in objs]}
    comp = {k: {pr: sum(1 for o in objs if o["id"] in set(v) and o["proto"] == pr) for pr in TRI} for k, v in sets.items()}
    moved = [o["id"] for o in syn if o["region"] != o["intended_region"]]
    return {"objects": objs, "sets": sets, "composition": comp, "placed_outside_intended_region": moved, "b3_density_test": {"status": "INCONCLUSIVE" if any(o["id"] in moved for o in syn if o["id"] in {x["id"] for x in s60}) else "PLACED", "reason": f"A1-C9 asks for 3 extra buildings in B3; only {sum(1 for o in syn if o['id'] in {x['id'] for x in s60} and o['region'] == 'B3')} fit on free WE-01 land in B3, the rest fell back to B1/B2 and are GLOBAL_STRESS_ONLY", "scope_exception": "PENDING_MARTIN_APPROVAL", "we01_land_constraints_relaxed": False}, "corridor_ids": ids, "beach_regions": beach, "site_a_protection": site, "terrain_applied": bool(hmap)}


TERRAIN_SPAN_M, TERRAIN_MIN_M = 1.5, -0.1    # PROPOSED_LIMIT: footprint height span and minimum ground height for synthetic sites (measured L0 land is flat at 0.0)


def scenarios():
    S = lambda n, desc, kind, **k: dict(name=n, description=desc, kind=kind, **k)
    return [S("S1_B1_border_sweep", "out and back along the z=1024 chunk border (8 x 128) through B1", "path", waypoints=[[-10, 1024], [490, 1024], [-10, 1024]], speed_mps=12, sim_seconds=84),
            S("S2_B2_reversal", "drive east then reverse direction across x chunk borders in B2", "path", waypoints=[[-1000, 945], [-400, 945], [-1000, 945]], speed_mps=15, sim_seconds=80),
            S("S3_B3_diagonal", "slow diagonal through B3, crossing x=-512 and z=-768 borders", "path", waypoints=[[-740, -910], [-240, -510]], speed_mps=8, sim_seconds=80),
            S("S4_far_view_avenue", "far observation: avenue x=0 from CBD towards B3 at low speed", "path", waypoints=[[0, -100], [0, -700]], speed_mps=6, sim_seconds=100),
            S("S5_destination_switch", "test-only destination switch B1 -> B3 -> B2 with 20 s holds", "teleport_hold", stops=[[240, 1080], [-490, -710], [-700, 945]], hold_seconds=20, sim_seconds=60),
            S("S6_high_speed_pass", "three peak-speed passes along avenue x=0 past the planned district edge", "path", waypoints=[[0, -880], [0, 880], [0, -880], [0, 880]], speed_mps=68, sim_seconds=78)]


# ------------------------------------------------------------------ A08 triangles
def pts_of(objs):
    return [((o["b"][0] + o["b"][2]) / 2, (o["b"][1] + o["b"][3]) / 2, o["proto"]) for o in objs]


def tri_view(pts, gx, gz, r, half=None, heading=0.0):
    t = 0
    for x, z, pr in pts:
        d = math.hypot(x - gx, z - gz)
        if d > r[2]: continue
        if half is not None and d > 1e-9 and abs((math.atan2(z - gz, x - gx) - heading + math.pi) % (2 * math.pi) - math.pi) > half: continue
        t += TRI[pr][0 if d <= r[0] else 1 if d <= r[1] else 2]
    return t


def worst_multi(pts, r, halves, step=20, hstep=15):
    """Max triangles over the 20 m viewpoint grid: key 'omni' plus one entry per half-angle (best of 24 headings). Returns {key: (tri, gx, gz, heading_deg)}."""
    best = {"omni": (0, 0, 0, 0), **{h: (0, 0, 0, 0) for h in halves}}
    for gx in range(-1100, 600, step):
        for gz in range(-1000, 1400, step):
            lst = []
            for x, z, pr in pts:
                d = math.hypot(x - gx, z - gz)
                if d <= r[2]: lst.append((math.atan2(z - gz, x - gx) if d > 1e-9 else None, TRI[pr][0 if d <= r[0] else 1 if d <= r[1] else 2]))
            tot = sum(t for _, t in lst)
            if tot > best["omni"][0]: best["omni"] = (tot, gx, gz, 0)
            live = [half for half in halves if tot > best[half][0]]          # a cone can never beat its own omni total: skip hopeless viewpoints
            for h in (range(0, 360, hstep) if live else ()):
                hr = math.radians(h)
                for half in live:
                    t = sum(t for a, t in lst if a is not None and abs((a - hr + math.pi) % (2 * math.pi) - math.pi) <= half)
                    if t > best[half][0]: best[half] = (t, gx, gz, h)
    return best


def path_samples(sc):
    out = []
    if sc["kind"] == "teleport_hold":
        for k, (x, z) in enumerate(sc["stops"]):
            for t in range(0, sc["hold_seconds"] * 2): out.append((x, z, 0.0))
        return out
    wp, v, T = sc["waypoints"], sc["speed_mps"], sc["sim_seconds"]; legs = [(wp[i], wp[i + 1], math.hypot(wp[i + 1][0] - wp[i][0], wp[i + 1][1] - wp[i][1])) for i in range(len(wp) - 1)]
    total = sum(l[2] for l in legs)
    for k in range(int(T * 2)):
        s = min(v * k / 2, total - 1e-6); a = 0.0
        for (p, q, L) in legs:
            if s <= L:
                out.append((p[0] + (q[0] - p[0]) * s / L, p[1] + (q[1] - p[1]) * s / L, math.atan2(q[1] - p[1], q[0] - p[0]))); break
            s -= L
    return out


def shadow_tri(pts, gx, gz, r, sh_r):
    return sum(TRI[pr][0 if d <= r[0] else 1 if d <= r[1] else 2] for x, z, pr in pts for d in [math.hypot(x - gx, z - gz)] if d <= sh_r)


def triangle_block(plan, fx, scs, presets):
    objs = [o for o in fx["objects"] if o["id"] in set(fx["sets"]["57"])]; pts = pts_of(objs); res = {}
    for name, r in LOD.items():
        fovs = (("cone96_reference", 96), ("hfov_16x9_91.5", 91.5), ("hfov_20x9_104.2", 104.2)); wm = worst_multi(pts, r, [math.radians(a) / 2 for _, a in fovs])
        om = wm["omni"]; fov = {k: wm[math.radians(a) / 2] for k, a in fovs}
        sh_r = SHADOW_RANGE[{"PHONE_LOW": "LOW", "PHONE_MED": "MED", "TABLET_MED": "MED", "DESKTOP_HIGH": "HIGH"}[name]]
        gx, gz = fov["cone96_reference"][1], fov["cone96_reference"][2]
        shadow = shadow_tri(pts, gx, gz, r, sh_r)
        contrib = {}
        for x, z, pr in pts:
            d = math.hypot(x - gx, z - gz)
            if d <= r[2]:
                k = f"{pr}/LOD{0 if d <= r[0] else 1 if d <= r[1] else 2}"; contrib[k] = contrib.get(k, 0) + TRI[pr][0 if d <= r[0] else 1 if d <= r[1] else 2]
        replay = {}
        for sc in scs:
            ps = path_samples(sc); vals = [tri_view(pts, x, z, r, math.radians(96) / 2, h) for x, z, h in ps]; allp = [a + shadow_tri(pts, x, z, r, sh_r) for a, (x, z, _) in zip(vals, ps)]
            replay[sc["name"]] = {"samples": len(vals), "p50": pct(vals, 50), "p95": pct(vals, 95), "max": max(vals), "p95_incl_shadow": pct(allp, 95), "max_incl_shadow": max(allp)}
        res[name] = {"omni_resident_upper_bound": list(om), "view_cone": {k: list(v) for k, v in fov.items()}, "shadow_pass_extra_at_cone96_worst": shadow, "cone96_peak_viewpoint_plus_shadow_estimate": fov["cone96_reference"][0] + shadow, "shadow_range_m": sh_r, "fog_transmittance_at_lod2_edge": presets[name]["proposed_mapping"]["fog_transmittance_at_lod"][2],
                     "contribution_at_cone96_worst_viewpoint": dict(sorted(contrib.items())), "replay_path": replay}
    fov_note = {"vertical_fov_deg": 60, "aspect_16x9_h_fov": round(math.degrees(2 * math.atan(math.tan(math.radians(30)) * 16 / 9)), 1), "aspect_20x9_h_fov": round(math.degrees(2 * math.atan(math.tan(math.radians(30)) * 20 / 9)), 1)}
    return {"source_class": "ANALYTIC_ESTIMATE", "method": "57 WE-02 parcels at bounds centres, 20 m viewpoint grid x[-1100,600) z[-1000,1400), 15 deg headings, draft triangle caps, no fog/occlusion/height",
            "metric_definition": "view-cone and omni columns count building meshes at their LOD in ONE pass (no shadow); cone96_peak_viewpoint_plus_shadow_estimate and p95_incl_shadow add the shadow-pass extra and are the only analytic values comparable to renderer.info.render.triangles (all passes) in MEASURED tables",
            "limitations": ["no fog or occlusion: LOD2 meshes at the far edge are largely faded by fog (see fog_transmittance_at_lod2_edge), so counts can overstate the far field; the model samples building centres on a 20 m viewpoint grid and is not a strict bound", "2-D distances, ground-level camera: height and terrain relief not modelled", "worst case is a single viewpoint, not a P95; replay P95 uses six scripted paths only", "no budget is validated by this block"],
            "fov": fov_note, "presets": res}


# ------------------------------------------------------------------ A09 benefit
def benefit_block(fx, scs):
    objs = {o["id"]: o for o in fx["objects"]}; out = {"source_class": "ANALYTIC_ESTIMATE", "assumptions": {"bodies_per_building": 1, "radii_m": RADII, "peak_grid_m": 40, "replay_p95": "pooled 2 Hz samples of the six replay scenarios (96 deg is irrelevant: bodies are omnidirectional)"}, "sets": {}}
    paths = [path_samples(sc) for sc in scs]
    for n in ("40", "57", "60"):
        pts = pts_of([objs[i] for i in fx["sets"][n]]); N = len(pts); cnt = lambda gx, gz, R: sum(1 for x, z, _ in pts if math.hypot(x - gx, z - gz) <= R); row = {"buildings": N, "by_radius": {}}
        for R in RADII:
            peak = max(cnt(gx, gz, R) for gx in range(-1100, 600, 40) for gz in range(-1000, 1400, 40)); rep = [cnt(x, z, R) for ps in paths for x, z, _ in ps]
            row["by_radius"][str(R)] = {"max_active_bodies_peak_grid": peak, "replay_active_p95": pct(rep, 95), "replay_active_max": max(rep), "saving_peak": round(1 - peak / N, 3), "saving_replay_p95": round(1 - pct(rep, 95) / N, 3)}
        row["unique_asset_model_all_resident_triangles"] = sum(sum(TRI[objs[i]["proto"]]) for i in fx["sets"][n]); row["shared_prototype_model_resident_triangles"] = sum(sum(v) for v in TRI.values()); out["sets"][n] = row
    out["finding"] = ("Four shared prototypes: resident geometry and the shared atlas do not depend on the number of buildings, so geometry/texture savings from streaming are structurally ~0 under Control A with the same LOD strategy; "
                      "collision bodies are the only large saving, and it is conditional on 1 body per building and on the active radius (see by_radius: peak-grid maximum and replay P95 differ, and the saving falls as the radius grows).")
    out["recommended_gate_revision"] = {"source_class": "PROPOSED_LIMIT", "replace": "geometry+texture resident peak >= 20 % lower", "with": ["active collision bodies P95 >= 20 % lower than all-resident at the radius chosen by A2 (see by_radius; the 56 % figure is the peak-grid saving at 217 m for 57 buildings, not a replay P95)",
        "visual object instances alive P95 reported (no ratio gate)", "draw calls P95 +<=5 %", "frame-time ratio only with a valid control; otherwise INCONCLUSIVE", "geometry/texture savings evaluated on the unique-asset model for WE-06 and reported, not gated"]}
    return out


# ------------------------------------------------------------------ A10 device protocol
def device_protocol():
    return {"source_class": "PROPOSED_LIMIT", "devices": ["Samsung Galaxy S26 Ultra", "Samsung Galaxy Tab S11"], "presets": ["PHONE_LOW", "PHONE_MED", "TABLET_MED"], "url_flag": "?fps=1", "fixed": ["preset set manually", "auto quality off", "dynamic resolution off"],
            "record": ["release/CACHE", "commit SHA", "device, OS, browser version", "resolution and orientation", "refresh rate", "FPS cap", "preset", "resScale", "auto-quality state", "time of day", "load (40/60 buildings)", "thermal state if available"],
            "procedure": {"warmup_min": 3, "runs_per_load": 3, "run_seconds_min": 120, "loads": [40, 60], "paths": ["day", "night", "chunk switch"], "frame_source": "in-game diagnostics, never screen recording"},
            "fps_acceptance": {"rule": "average FPS >= fps_cap x 0.97", "cap_30_threshold": 29.1, "note": "tolerance for timing, not a lower target"},
            "other_thresholds_unchanged": {"p95_ms": 40, "p99_ms": 66.7, "min_1s_fps": 24, "over_100ms_ratio": 0.005},
            "a2_required_fields": ["P50/P95/P99 frame time", "count > 50 ms", "count > 100 ms", "longest frame", "preset", "resScale", "fpsCap", "CACHE name", "existing average/min text kept"],
            "limitation": "until A2 ships, ?fps=1 gives only a 1 s average and minimum: not sufficient as a baseline"}


# ------------------------------------------------------------------ A11 budgets and reports
def v(value, cls, basis, unit=None):
    return {"value": value, "source_class": cls, "basis": basis, **({"unit": unit} if unit else {})}


def budgets(q, base, tri, speed):
    out = {"schema": "we03-proposed-budgets-v1", "status": "PROPOSED_NOT_APPROVED", "note": "A1 closure does not approve any value; PROPOSED_LIMIT rows come from WE-03 draft s.22 and stay provisional until ChatGPT, Claude and Martin confirm", "presets": {}}
    adds = {"PHONE_LOW": (30, 120000, 16, 32, 32, 128, 1.20, 2), "PHONE_MED": (38, 160000, 20, 40, 36, 144, 1.20, 2), "TABLET_MED": (45, 200000, 24, 48, 40, 160, 1.20, 2), "DESKTOP_HIGH": (75, 350000, 48, 96, 60, 240, 1.25, 4)}
    for name, (dc, tr, geo, tex, bod, shp, ratio, cpu) in adds.items():
        tp = tri["presets"][name]; cone = tp["view_cone"]["cone96_reference"][0]; rep = max(r["p95"] for r in tp["replay_path"].values()); rep_sh = max(r["p95_incl_shadow"] for r in tp["replay_path"].values()); itp = name == "PHONE_MED"
        src = (lambda d: "INTERPOLATED midpoint of the draft s.22 PHONE_LOW and TABLET_MED rows (the draft has no PHONE_MED row); not approved") if itp else (lambda d: d)
        b = {"added_draw_calls_p95": v(dc, "PROPOSED_LIMIT", src("draft s.22")), "added_triangles_p95": v(tr, "PROPOSED_LIMIT", src("draft s.22")), "analytic_cone96_worst_triangles": v(cone, "ANALYTIC_ESTIMATE", "calibration_data.json triangles", "triangles"),
             "analytic_replay_p95_max_over_scenarios": v(rep, "ANALYTIC_ESTIMATE", "96 deg cone along replay paths, single pass (no shadow)", "triangles"), "analytic_cone96_peak_plus_shadow_triangles": v(cone + tp["shadow_pass_extra_at_cone96_worst"], "ANALYTIC_ESTIMATE", "cone96 worst viewpoint + shadow-pass extra; comparable to renderer.info all-pass triangles", "triangles"),
             "analytic_replay_p95_incl_shadow_max": v(rep_sh, "ANALYTIC_ESTIMATE", "replay P95 + shadow-pass extra, max over scenarios", "triangles"), "triangle_budget_comparison": {"status": "NOT_VALIDATED", "note": f"analytic worst {cone + tp['shadow_pass_extra_at_cone96_worst']} and replay P95 incl. shadow {rep_sh} versus proposed {tr}: sampled centre-point estimates without fog, occlusion or height (not a strict bound, not a measured P95); no budget is validated"}, "added_geometry_buffer_mib": v(geo, "PROPOSED_LIMIT", src("draft s.22")), "added_texture_mib": v(tex, "PROPOSED_LIMIT", src("draft s.22")),
             "active_bodies": v(bod, "PROPOSED_LIMIT", src("draft s.22")), "active_shapes": v(shp, "PROPOSED_LIMIT", src("draft s.22; 4 shapes per body")), "physics_step_median_ratio": v(ratio, "PROPOSED_LIMIT", src("draft s.22; control band 1/1.10..1.10 decides validity")),
             "streaming_cpu_ms_p95": v(cpu, "PROPOSED_LIMIT", src("draft s.22")), "lod_m": v(list(LOD[name]), "PROPOSED_LIMIT", "draft s.8.2"),
             "device_avg_fps": v("PENDING_DEVICE", "PENDING_DEVICE", "avg >= fps_cap x 0.97 (29.1 at cap 30); measured by Martin after A2"),
             "device_frame_time_p95_ms": v(40, "PENDING_DEVICE", "draft s.25 initial acceptance"), "device_frame_time_p99_ms": v(66.7, "PENDING_DEVICE", "draft s.25 initial acceptance")}
        if base and name in base["presets"]:
            b["base_headless"] = {"source_class": "MEASURED_HEADLESS", **base["presets"][name]}
        out["presets"][name] = b
    out["preset_mapping"] = {k: v(p["proposed_mapping"]["lod_m"], "PROPOSED_LIMIT", p["proposed_mapping"]["rule"]) for k, p in q.items()}
    out["streaming_benefit_targets"] = v("see calibration_data.json benefit.recommended_gate_revision", "PROPOSED_LIMIT", "A09")
    out["speed_ceilings_mps"] = {k: v(val, "ANALYTIC_ESTIMATE", "force-limit derivation from index.html constants", "m/s") for k, val in speed["code_derived_ceilings_mps"].items() if k != "source_class" and k != "note"}
    out["device_protocol"] = device_protocol()
    return out


def base_summary(base):
    if not base or "combinations" not in base: return None
    pres = {}
    for p in MEASURED_PRESETS:
        rows = [c for k, c in base["combinations"].items() if k.startswith(p + "/")]
        if not rows: continue
        pres[p] = {"combinations": len(rows), "draw_calls_p50_median": statistics.median(r["stats"]["draw_calls"]["p50"] for r in rows), "draw_calls_p50_max": max(r["stats"]["draw_calls"]["p50"] for r in rows),
                   "triangles_p50_median": statistics.median(r["stats"]["triangles"]["p50"] for r in rows), "triangles_p50_max": max(r["stats"]["triangles"]["p50"] for r in rows),
                   "frame_ms_p50_median": round(statistics.median(r["stats"]["frame_ms"]["p50"] for r in rows), 2), "bodies_max": max(r["resources"]["bodies"] for r in rows), "shapes_max": max(r["resources"]["shapes"] for r in rows)}
        pp = base.get("physics_pairs", {}).get(p)
        if pp: pres[p]["physics_ratio_range"] = [min(x["ratio_B_over_A"] for x in pp["pairs"]), max(x["ratio_B_over_A"] for x in pp["pairs"])]
    return {"presets": pres}


def baseline_analysis(base):
    """Stability analysis of the measured data (derived only from baseline_metrics.json; every row keeps its INCONCLUSIVE/STABLE status)."""
    if not base: return {"source_class": "PENDING", "present": False}
    phys = {}
    for p, rec in base.get("physics_pairs", {}).items():
        ratios = [x["ratio_B_over_A"] for x in rec["pairs"]]; lo, hi = rec["control_band"]
        phys[p] = {"pairs": len(ratios), "ratio_min": min(ratios), "ratio_max": max(ratios), "within_band": all(lo <= r <= hi for r in ratios), "status": "STABLE" if all(lo <= r <= hi for r in ratios) else "INCONCLUSIVE",
                   "median_ms_overall": round(statistics.median(x["median_ms_A"] for x in rec["pairs"]) , 5)}
    rep = {}
    for k, r in base.get("repeats", {}).items():
        a = base["combinations"].get(k)
        if not a: continue
        f = lambda m, key: (a["stats"][m][key], r["stats"][m][key])
        rep[k] = {"draw_calls_p50": f("draw_calls", "p50"), "triangles_p50": f("triangles", "p50"), "frame_ms_p50": f("frame_ms", "p50"), "frame_ms_p95": f("frame_ms", "p95"),
                  "frame_p50_ratio": round(r["stats"]["frame_ms"]["p50"] / a["stats"]["frame_ms"]["p50"], 4), "draw_calls_equal": a["stats"]["draw_calls"]["p50"] == r["stats"]["draw_calls"]["p50"], "triangles_equal": a["stats"]["triangles"]["p50"] == r["stats"]["triangles"]["p50"]}
    ratios = [v["frame_p50_ratio"] for v in rep.values()]
    gate = {"deterministic_counts_stable": bool(rep) and all(v["draw_calls_equal"] and v["triangles_equal"] for v in rep.values()),
            "frame_time_p50_repeat_ratio_range": [min(ratios), max(ratios)] if ratios else None,
            "frame_time_usable_as_hard_gate": bool(ratios) and 1 / 1.10 <= min(ratios) and max(ratios) <= 1.10, "p99_note": "P99 of 120 samples is the 2nd largest sample: low statistical power"}
    res = {}
    for p in MEASURED_PRESETS:
        rows = [c["resources"] for k, c in base["combinations"].items() if k.startswith(p + "/")]
        res[p] = {"geometry_mib_range": [round(min(r["geometry_buffer_bytes_estimate"] for r in rows) / 2**20, 1), round(max(r["geometry_buffer_bytes_estimate"] for r in rows) / 2**20, 1)],
                  "texture_mib_range": [round(min(r["texture_bytes_estimate"] for r in rows) / 2**20, 1), round(max(r["texture_bytes_estimate"] for r in rows) / 2**20, 1)], "bodies_range": [min(r["bodies"] for r in rows), max(r["bodies"] for r in rows)]}
    worst = sorted(((c["stats"]["frame_ms"]["max"], k) for k, c in list(base["combinations"].items()) + list(base["repeats"].items())), reverse=True)[:3]
    return {"source_class": "MEASURED_HEADLESS", "present": True, "physics_control": phys, "repeat_sessions": rep, "gate_stability": gate, "resource_ranges": res, "longest_frames_ms": [[m, k] for m, k in worst]}


def md_calibration(d, fx, bud):
    t = d["triangles"]["presets"]; L = ["# T-018A1 calibration report (WE-03A)", "", "Generated by `tools/we03/we03_calibration.py`; independently re-derived by `we03_calibration_check.py`. All numbers here are ANALYTIC_ESTIMATE or SOURCE_CONFIRMED unless a row says MEASURED_HEADLESS. Nothing is approved by A1.", "",
                                         "## Triangle analysis (A08)", "", "Single-pass columns exclude the shadow pass; `cone96 peak + shadow` is the shadow extra evaluated at the cone96 peak viewpoint (not a global maximum of the sum) and `replay P95 + shadow` adds it per sample; both are the only analytic values comparable to measured all-pass triangles. Sampled centre-point model without fog, occlusion or height, so not a strict bound; nothing here validates a budget.", "",
                                         "| preset | omni upper bound | cone 96 deg | cone 91.5 | cone 104.2 | shadow extra | cone96 peak + shadow | replay P95 max | replay P95 + shadow |", "|---|---|---|---|---|---|---|---|---|"]
    for n, r in t.items():
        L.append(f"| {n} | {r['omni_resident_upper_bound'][0]:,} | {r['view_cone']['cone96_reference'][0]:,} | {r['view_cone']['hfov_16x9_91.5'][0]:,} | {r['view_cone']['hfov_20x9_104.2'][0]:,} | {r['shadow_pass_extra_at_cone96_worst']:,} | {r['cone96_peak_viewpoint_plus_shadow_estimate']:,} | {max(x['p95'] for x in r['replay_path'].values()):,} | {max(x['p95_incl_shadow'] for x in r['replay_path'].values()):,} |")
    L += ["", "## Chunks (A06)", "", "| grid | occupied chunks | max parcels/chunk | cross-chunk parcels | max chunks covered |", "|---|---|---|---|---|"]
    for g, r in d["chunks"]["grids"].items(): L.append(f"| {g} m | {r['occupied_owner_chunks']} | {r['parcels_per_chunk_max']} | {r['cross_chunk_parcels']} | {r['max_chunks_covered']} |")
    L += ["", "## Fixtures (A07)", "", f"Composition: {json.dumps(fx['composition'])}", f"B3 density test: {fx['b3_density_test']['status']} ({fx['b3_density_test']['reason']}; scope exception {fx['b3_density_test']['scope_exception']}); fallback objects are GLOBAL_STRESS_ONLY.", "", "## Streaming benefit (A09)", "", d["benefit"]["finding"], "",
          "Active collision bodies by radius, 57 buildings, 1 body per building (peak = 40 m grid maximum; replay = P95 over the six scripted paths):", "", "| radius m | peak active | replay P95 active | saving at peak | saving at replay P95 |", "|---|---|---|---|---|",
          *[f"| {R} | {r['max_active_bodies_peak_grid']} | {r['replay_active_p95']} | {r['saving_peak']:.1%} | {r['saving_replay_p95']:.1%} |" for R, r in d["benefit"]["sets"]["57"]["by_radius"].items()], "", "## Speed and readiness (A05)", "", f"Code-derived ceilings (m/s): {json.dumps(d['speed']['code_derived_ceilings_mps'])}", "",
          f"Measured lower bounds: {json.dumps(d['speed']['measured_peak_lower_bounds_mps']['runs'])}", "", "See `proposed_budgets.json` for the labelled budget rows."]
    return "\n".join(L) + "\n"


def md_baseline(base, ana):
    L = ["# T-018A1 baseline report (WE-03A, headless)", "", "All values are MEASURED_HEADLESS: CPU submission time of `animate()` in software GL (SwiftShader, 2 vCPU shared host). They are not device FPS and not VRAM. Texture bytes are an RGBA8 + mip estimate, not VRAM.", ""]
    if not base: return "\n".join(L + ["No measurements present."]) + "\n"
    env = base["environment"]
    L += [f"- {env['browser']} / playwright {env['playwright']} / commit {env['head'][:12]} / CACHE {env['cache']}; combinations {len(base.get('combinations', {}))}/48, repeat sessions {len(base.get('repeats', {}))}/16",
          "- method: fresh Chrome per session, 20 warm-up + 120 recorded frames, dt 1/60, dayCycle off, fpsCap 0, 800x450; frame time = CPU time of one `animate()` call", "",
          "| preset/location/time | draw calls | triangles (all passes) | shadow tri | frame ms P50/P95/P99/max | bodies | shapes |", "|---|---|---|---|---|---|---|"]
    for k, c in sorted(base.get("combinations", {}).items()):
        s = c["stats"]; L.append(f"| {k} | {s['draw_calls']['p50']} | {s['triangles']['p50']:,} | {s['shadow_triangles']['p50']:,} | {s['frame_ms']['p50']}/{s['frame_ms']['p95']}/{s['frame_ms']['p99']}/{s['frame_ms']['max']} | {c['resources']['bodies']} | {c['resources']['shapes']} |")
    L += ["", "## Physics self-control (two fresh sessions of the same commit, 5 alternating pairs per preset, band 0.909..1.100)", "", "| preset | ratio min | ratio max | status |", "|---|---|---|---|"]
    L += [f"| {p} | {r['ratio_min']} | {r['ratio_max']} | {r['status']} |" for p, r in ana.get("physics_control", {}).items()]
    g = ana.get("gate_stability", {}); L += ["", "## Repeat sessions (B3 and CBD, day/night, 4 presets)", "", f"- draw calls and triangles identical in every repeat: {g.get('deterministic_counts_stable')}",
                                           f"- frame-time P50 repeat ratio range {g.get('frame_time_p50_repeat_ratio_range')}; usable as a hard gate: {g.get('frame_time_usable_as_hard_gate')} (INCONCLUSIVE otherwise)", f"- longest frames [ms, key]: {ana.get('longest_frames_ms')}",
                                           "", "## Resource estimate ranges across the 12 scenes per preset", ""]
    L += [f"- {p}: geometry {r['geometry_mib_range']} MiB, texture {r['texture_mib_range']} MiB, bodies {r['bodies_range']}" for p, r in ana.get("resource_ranges", {}).items()]
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out-dir", default=str(REPO / "specs/we03")); a = ap.parse_args(); out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
    src = (REPO / "index.html").read_text(); lines = src.splitlines(); plan = json.load(open(REPO / "specs/we02/district_plan.json"))
    bp = out / "baseline_metrics.json"; base = json.load(open(bp)) if bp.exists() else None; terrain = (base or {}).get("terrain_l0")
    q = parse_quality(src); presets = presets_block(q); spd = speed_block(src, base); fx = fixture_block(plan, terrain); scs = scenarios()
    parcels = [{"id": o["id"], "proto": o["proto"], "b": o["b"]} for o in fx["objects"] if o["kind"] == "WE02_PARCEL"]
    tri = triangle_block(plan, fx, scs, presets); data = {"schema": "we03-calibration-v1", "engineering_base": ENGINEERING_BASE, "index_html_blob": sh("git", "hash-object", "index.html"), "district_plan_sha256": sha(REPO / "specs/we02/district_plan.json"),
                                                 "l0_cells_sha256": sha(L0_CSV), "baseline_metrics_sha256": sha(bp) if bp.exists() else None, "source_inventory": inventory(lines), "presets": presets, "speed": spd, "chunks": chunk_block(parcels),
                                                 "triangles": tri, "benefit": benefit_block(fx, scs), "device_protocol": device_protocol(), "baseline_analysis": baseline_analysis(base)}
    fxp = {"schema": "we03-fixture-plan-v1", "classification": "SYNTHETIC_ONLY objects are not legal parcels, road-access or construction evidence; never written to district_plan.json", "seed": SEED, "terrain_thresholds": {"max_span_m": TERRAIN_SPAN_M, "min_height_m": TERRAIN_MIN_M, "source_class": "PROPOSED_LIMIT"},
           **fx, "replay_scenarios": scs, "source_class": "ANALYTIC_ESTIMATE"}
    bud = budgets(presets, base_summary(base), tri, spd)
    for name, obj in (("calibration_data.json", data), ("fixture_plan.json", fxp), ("proposed_budgets.json", bud)): (out / name).write_text(dump(obj))
    (out / "calibration_report.md").write_text(md_calibration(data, fx, bud)); (out / "baseline_report.md").write_text(md_baseline(base, data["baseline_analysis"]))
    print("wrote", out, "composition", fx["composition"])


if __name__ == "__main__":
    main()
