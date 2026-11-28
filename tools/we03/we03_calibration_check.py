#!/usr/bin/env python3
"""T-018A1 / WE-03A independent check (Claude-owned). Runs in CI; never measures, never imports the generator.

Re-derives every analytic number from index.html, specs/we02/district_plan.json and the WE-01 fixtures with its own
code, validates the structure and provenance of the committed baseline_metrics.json, enforces the source-class
discipline of the reports, proves the protected files are byte-identical, and then runs negative controls: each
mutation of the committed data must make at least one validator fail.
Usage: python3 tools/we03/we03_calibration_check.py [--dir specs/we03] [--skip-git]
"""
import argparse, copy, csv, hashlib, json, math, re, statistics, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "e8d5250fce0ea5f07f68840481cb95d2eca803fb"
CLASSES = {"MEASURED_HEADLESS", "ANALYTIC_ESTIMATE", "PROPOSED_LIMIT", "PENDING_DEVICE", "SOURCE_CONFIRMED", "INCONCLUSIVE", "PENDING"}
PRESETS11 = ["PHONE_LOW", "PHONE_MED", "TABLET_LOW", "TABLET_MED", "TABLET_HIGH", "DESKTOP_MED", "DESKTOP_HIGH", "DESKTOP_ULTRA", "IGPU_LOW", "IGPU_MED", "IGPU_HIGH"]
FOUR = ["PHONE_LOW", "PHONE_MED", "TABLET_MED", "DESKTOP_HIGH"]
LOCS = ["B1", "B2", "B3", "SiteA", "CBD", "Suburbs"]
TIMES = ["12:00", "23:00"]
TRI = {"R01": (12000, 3000, 300), "R02": (20000, 5000, 600), "R05": (5000, 1200, 150), "R08": (8000, 2000, 240)}
RADII = (140, 180, 217, 260, 350)
LODR = {"PHONE_LOW": (100, 250, 650), "PHONE_MED": (120, 300, 750), "TABLET_MED": (140, 350, 850), "DESKTOP_HIGH": (200, 500, 1200)}
COMP = {"40": {"R01": 9, "R02": 5, "R05": 22, "R08": 4}, "57": {"R01": 12, "R02": 7, "R05": 33, "R08": 5}, "60": {"R01": 13, "R02": 7, "R05": 34, "R08": 6}, "120": {"R01": 26, "R02": 14, "R05": 68, "R08": 12}}
ALLOW = ("tools/we03/", "specs/we03/", "specs/WE-03-", "specs/T-018A1-", "TASKS.md", "DECISIONS.md", "LOG.md", "HANDOFF.md", ".github/workflows/pwa-cache-check.yml")
REV0_PHYSICS_SHA256 = "47e5d5c81628b68a14c1134c768a3dcc8e39bc3523b9c01b88a44d7eafd996d0"    # sha256 of the PR #132 physics_pairs (canonical JSON): the retained revision-0 evidence must be byte-for-byte that
ARRAYS = ("frame_ms", "draw_calls", "triangles", "shadow_triangles", "shadow_calls", "render_pass_triangles", "render_passes")


def J(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def blob_sha1(path): b = Path(path).read_bytes(); return hashlib.sha1(b"blob %d\0" % len(b) + b).hexdigest()
def rank(a, q): s = sorted(a); return s[max(0, min(len(s) - 1, math.ceil(q * len(s) / 100) - 1))]
def close(a, b, tol=1e-3): return abs(a - b) <= tol * max(1.0, abs(b))


# ------------------------------------------------------------------ baseline structure and provenance (A1-G03..G06, G16)
def v_baseline(b, d=None):
    f = []
    if not b or b.get("schema") != "we03-baseline-v1": return ["baseline: missing or wrong schema"]
    env = b.get("environment", {})
    for k in ("browser", "playwright", "head", "index_html_blob", "tool_sha256", "harness_sha256", "viewport", "method", "cache", "protected_blobs_at_engineering_base"):
        if k not in env: f.append(f"environment.{k} missing")
    if env.get("index_html_blob") != env.get("index_html_blob_at_engineering_base") or env.get("index_html_blob") != env.get("index_html_blob_at_audit_base"): f.append("index.html is not identical to engineering/audit base")
    if env.get("game_file_diff_vs_engineering_base"): f.append("game files differ from engineering base at measurement time")
    want = [f"{p}/{l}/{t}" for p in FOUR for l in LOCS for t in TIMES]
    comb = b.get("combinations", {}); miss = [k for k in want if k not in comb]
    if miss: f.append(f"missing measurement combinations ({len(miss)}): {miss[:3]}")
    if len(comb) != 48: f.append(f"combinations {len(comb)} != 48")
    rep_want = [f"{p}/{l}/{t}" for p in FOUR for l in ("B3", "CBD") for t in TIMES]
    if [k for k in rep_want if k not in b.get("repeats", {})]: f.append("repeat sessions incomplete (need 16)")
    for name, group in (("combinations", comb), ("repeats", b.get("repeats", {}))):
        for k, c in group.items():
            if c.get("measurement_class") != "MEASURED_HEADLESS": f.append(f"{name}/{k}: class")
            n = c.get("recorded_frames", 0)
            if n < 120 or c.get("warmup_frames", 0) < 20: f.append(f"{name}/{k}: frames {n} / warmup {c.get('warmup_frames')}")
            for a in ARRAYS:
                if len(c.get("samples", {}).get(a, [])) != n: f.append(f"{name}/{k}: samples.{a} length")
            if c.get("samples") and n:
                for m, key in (("frame_ms", "frame_ms"), ("draw_calls", "draw_calls"), ("triangles", "triangles")):
                    s = c["samples"][key]
                    for q, qn in ((50, "p50"), (95, "p95"), (99, "p99")):
                        if not close(rank(s, q), c["stats"][m][qn], 1e-3): f.append(f"{name}/{k}: stats.{m}.{qn} does not match samples")
            if c.get("ph_done") is False: f.append(f"{name}/{k}: Poly Haven models never finished (__phDone)")
            if c.get("preset") != "PHONE_LOW" and c.get("ph_done") is None: f.append(f"{name}/{k}: ph_done not recorded")
            if "page_errors" not in c or c["resources"]["bodies"] <= 0 or c["resources"]["shapes"] <= 0: f.append(f"{name}/{k}: resources/page_errors missing")
    sp = b.get("speed", {}).get("runs", [])
    if len(sp) < 4: f.append("speed runs missing")
    return f + v_phys(b, d)


def v_phys(b, d):
    """A1-C5: every pair is two fresh sessions (alternating order), both sides ready, same bodies/shapes; the status must follow the control band; the original reused-page evidence stays."""
    f = []; pp = b.get("physics_pairs", {}); v1 = b.get("physics_pairs_v1_reused_pages")
    if not v1 or v1.get("superseded_by") != "physics_pairs" or not v1.get("data"): f.append("physics: original reused-page evidence (physics_pairs_v1_reused_pages) not retained")
    elif hashlib.sha256(json.dumps(v1["data"], sort_keys=True, separators=(",", ":")).encode()).hexdigest() != REV0_PHYSICS_SHA256: f.append("physics: retained revision-0 evidence differs from PR #132")
    for p in FOUR:
        rec = pp.get(p)
        if not rec or rec.get("session_model") != "fresh_session_per_side" or len(rec["pairs"]) < 5 or rec["control_band"] != [0.90909, 1.1] or (rec["warmup_steps"], rec["recorded_steps"], rec["step"]) != (900, 360, "physicsWorld.step(1/60,1/60,3)"): f.append(f"physics {p}: needs >= 5 pairs, session_model fresh_session_per_side, band 0.90909..1.1, 900 warm-up + 360 recorded steps of physicsWorld.step(1/60,1/60,3)"); continue
        for i, x in enumerate(rec["pairs"]):
            ma, mb = statistics.median(x["samples_ms_A"]), statistics.median(x["samples_ms_B"])
            if len(x["samples_ms_A"]) != 360 or len(x["samples_ms_B"]) != 360 or not close(mb / ma, x["ratio_B_over_A"], 2e-3): f.append(f"physics {p}[{i}] samples/ratio")
            if x["order"] != (["A", "B"] if i % 2 == 0 else ["B", "A"]): f.append(f"physics {p}[{i}] order does not alternate")
            if x["bodies"]["A"] != x["bodies"]["B"] or x["shapes"]["A"] != x["shapes"]["B"] or min(x["bodies"].values()) <= 0 or min(x["shapes"].values()) <= 0: f.append(f"physics {p}[{i}] bodies/shapes differ or empty")
            if any(x["ph_done"][k] is not (None if p == "PHONE_LOW" else True) for k in "AB"): f.append(f"physics {p}[{i}] readiness (__phDone) not reached")
        want = "STABLE" if all(rec["control_band"][0] <= x["ratio_B_over_A"] <= rec["control_band"][1] for x in rec["pairs"]) else "INCONCLUSIVE"
        if d and d["baseline_analysis"]["physics_control"][p]["status"] != want: f.append(f"physics {p}: status {d['baseline_analysis']['physics_control'][p]['status']} != {want} from the control band")
    return f


def v_runtime(b, d):
    """Measured runtime settings must equal the QUALITY_CONFIG source values: proves each harness preset is the real device profile (e.g. TABLET, not iGPU)."""
    f = []; pr = b.get("preset_runtime", {}); dev_cap = {k: v for k, v in (d["presets"]["PHONE_LOW"] and {n: d["presets"][n]["fps_cap"] for n in PRESETS11}).items()}
    for n in PRESETS11:
        r = pr.get(n); src = d["presets"][n]
        if not r or r.get("measurement_class") != "MEASURED_HEADLESS": f.append(f"preset_runtime {n} missing"); continue
        s = r["settings"]
        if not close(s["fogDensity"], src["quality_config"]["fog"], 1e-6) or s["shadowMapSize"] != src["quality_config"]["shadow"] or s["fpsCap"] != src["fps_cap"] or s["quality"] != n.split("_")[1]:
            f.append(f"preset_runtime {n}: runtime {s['quality']}/{s['shadowMapSize']}/{s['fogDensity']}/{s['fpsCap']} != source")
    for k, c in {**b.get("combinations", {}), **b.get("repeats", {})}.items():
        if c.get("default_fps_cap") != dev_cap[c["preset"]]: f.append(f"{k}: default fps cap {c.get('default_fps_cap')} != {dev_cap[c['preset']]} (wrong device profile)")
        if c["resources"]["settings"]["shadowMapSize"] != d["presets"][c["preset"]]["quality_config"]["shadow"]: f.append(f"{k}: shadow map size differs from the preset")
    return f


# ------------------------------------------------------------------ source facts
def v_source(src_lines, src, d):
    f = []; inv = d["source_inventory"]
    if len(inv["items"]) != 10: f.append("source inventory must cover A01 items 1..10")
    for it in inv["items"]:
        for sy in it["symbols"]:
            if not sy["def_lines"]: f.append(f"{it['id']}: no definition found for {sy['pattern']}")
            for ln in sy["def_lines"]:
                if not re.search(sy["pattern"], src_lines[ln - 1]): f.append(f"{it['id']}: line {ln} does not match {sy['pattern']}")
    rs = inv["position_reset_inventory"]
    for ln in rs["direct_position_set_lines"]:
        if not re.search(r"position\.set\(", src_lines[ln - 1]): f.append(f"position reset line {ln}")
    al = [i + 1 for i, l in enumerate(src_lines) if re.search(r"^\s*\S*[bB]ody\.position\.set\(", l)]
    if rs["all_body_position_set_lines"] != al or sorted(rs["direct_position_set_lines"] + rs["creation_or_other_sites"]) != al: f.append("position reset inventory incomplete: every body.position.set line must be a listed reset or a listed construction site")
    own = sorted(i + 1 for i, l in enumerate(src_lines) if re.search(r"\bteleportTo\(", l))
    if own != sorted(rs["teleportTo_definition_and_callers"]): f.append("teleportTo caller inventory differs from source")
    # presets: independent parse (line by line)
    q = {}
    for l in src_lines[1560:1640]:
        m = re.match(r"\s+((?:PHONE|TABLET|DESKTOP|IGPU)_(?:LOW|MED|HIGH|ULTRA)):\s*\{(.*)\}", l)
        if m: q[m.group(1)] = {k: (True if v == "true" else False if v == "false" else float(v)) for k, v in re.findall(r"(\w+):\s*(true|false|[\d.]+)", m.group(2))}
    if sorted(q) != sorted(PRESETS11): f.append(f"source presets {sorted(q)} != 11 expected")
    for name in PRESETS11:
        e = d["presets"].get(name)
        if not e: f.append(f"preset {name} missing from calibration_data"); continue
        if e["quality_config"] != q.get(name): f.append(f"preset {name} differs from source")
        pm = e["proposed_mapping"]
        if pm["approved"] or pm["streaming_enabled"]: f.append(f"preset {name}: mapping must stay unapproved/streaming off")
        if not (pm["lod_m"][0] < pm["lod_m"][1] < pm["lod_m"][2]) or pm["source_class"] != "PROPOSED_LIMIT": f.append(f"preset {name}: mapping")
    sc = d["speed"]["source_constants"]
    vm = [int(x) for x in re.findall(r"vmax:\s*(\d+)", src[src.index("const CAR_MODELS"):src.index("const CAR_MODELS") + 4000])]
    if sc["vmax_kmh_by_model"] != vm: f.append("vmax list differs")
    nit = max(float(x) for x in re.findall(r"nitroBoost\s*=\s*([\d.]+)", src)); up = 1 + 4 * float(re.search(r"\(STATE\.upgradeLevel - 1\) \* ([\d.]+)", src).group(1))
    top = max(vm + [245]); c = d["speed"]["code_derived_ceilings_mps"]
    for k, v in (("base_nitro", top * nit / 3.6), ("max_upgrade_nitro", top * up * nit / 3.6), ("base_no_nitro", top / 3.6)):
        if not close(c[k], v, 1e-3): f.append(f"ceiling {k} {c[k]} != {v:.2f}")
    t = re.search(r"const TREE_COLLIDERS = \{ cell: (\d+), enter: (\d+), leave: (\d+), interval: ([\d.]+)", src)
    if [float(x) for x in t.groups()] != [sc["tree_colliders"][k] for k in ("cell", "enter", "leave", "interval")]: f.append("TREE_COLLIDERS constants differ")
    return f


# ------------------------------------------------------------------ chunks
def idx(v, g): return math.floor(v / g)
def cov(lo, hi, g): return list(range(math.floor(lo / g), math.ceil(hi / g)))


def v_chunks(d, plan, idx_fn=idx):
    f = []; ch = d["chunks"]
    for v in ch["index_vectors"]:
        if idx_fn(v["v"], 128) != v["chunk128"]: f.append(f"index vector {v['v']}")
    want = {-1: -1, -2: -1, -3: -1, -128: -1, -128.0001: -2, 0: 0, 127.9999: 0, 128: 1}
    for v, e in want.items():
        if idx_fn(v, 128) != e: f.append(f"negative/boundary index {v} -> {idx_fn(v, 128)} (expected {e})")
    for c in ch["coverage_vectors"]:
        if [idx_fn(c["min"], 128) + k for k in range(len(c["chunks128"]))] != c["chunks128"] and cov(c["min"], c["max"], 128) != c["chunks128"]: f.append(f"coverage {c}")
    for c in ch["parent_vectors"]:
        if math.floor(c["c"] / 2) != c["parent"]: f.append(f"parent {c}")
    ps = [p["bounds_internal"] for p in plan["parcels"] if p["phase"] <= 2]
    for g in (64, 128, 256):
        owners, cross, mx, per = {}, 0, 0, {}
        for b in ps:
            o = (idx_fn((b[0] + b[2]) / 2, g), idx_fn((b[1] + b[3]) / 2, g)); per[o] = per.get(o, 0) + 1
            n = len(cov(b[0], b[2], g)) * len(cov(b[1], b[3], g)); cross += n > 1; mx = max(mx, n)
        r = ch["grids"][str(g)]
        if (len(per), max(per.values()), cross, mx) != (r["occupied_owner_chunks"], r["parcels_per_chunk_max"], r["cross_chunk_parcels"], r["max_chunks_covered"]): f.append(f"chunk grid {g} stats differ")
    if ch["grids"]["128"]["cross_chunk_parcels"] != 34 or ch["grids"]["128"]["max_chunks_covered"] != 4: f.append("128 m grid: G0 reported 34 cross-chunk parcels and max 4 chunks; recomputation differs (report the definition difference)")
    return f


# ------------------------------------------------------------------ fixtures (A1-G08..G10)
def ov(a, b, gap=0.0): return min(a[2], b[2]) - max(a[0], b[0]) > -gap and min(a[3], b[3]) - max(a[1], b[1]) > -gap


def poly_hits(poly, r):
    """True when polygon and rectangle share positive area (Sutherland-Hodgman against the rectangle, then shoelace)."""
    pts = [tuple(p) for p in poly]
    for axis, lim, keep in ((0, r[0], 1), (0, r[2], -1), (1, r[1], 1), (1, r[3], -1)):
        out = []
        for i, a in enumerate(pts):
            b = pts[(i + 1) % len(pts)]; ia, ib = (a[axis] - lim) * keep >= 0, (b[axis] - lim) * keep >= 0
            if ia: out.append(a)
            if ia != ib:
                t = (lim - a[axis]) / (b[axis] - a[axis]); out.append((lim if axis == 0 else a[0] + (b[0] - a[0]) * t, lim if axis == 1 else a[1] + (b[1] - a[1]) * t))
        pts = out
        if len(pts) < 3: return False
    return abs(sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))) / 2 > 1e-6


def v_fixture(fp, plan, cors, cells, terrain, beach=(), idx_fn=idx):
    f = []; objs = fp["objects"]; ids = [o["id"] for o in objs]
    if len(ids) != len(set(ids)): f.append("duplicate object ID")
    byid = {o["id"]: o for o in objs}
    for name, comp in COMP.items():
        s = fp["sets"].get(name, [])
        got = {k: sum(1 for i in s if byid[i]["proto"] == k) for k in TRI}
        if got != comp or len(s) != sum(comp.values()): f.append(f"set {name} composition {got} != {comp}")
    pl = {p["parcel_id"]: p for p in plan["parcels"]}
    if set(fp["sets"]["57"]) != set(pl) or set(fp["sets"]["40"]) != {i for i, p in pl.items() if p["phase"] == 1}: f.append("40/57 sets differ from the WE-02 plan")
    for i in fp["sets"]["57"]:
        if byid[i]["b"] != pl[i]["bounds_internal"] or byid[i]["proto"] != pl[i]["prototype_id"]: f.append(f"{i}: differs from WE-02 plan")
    syn = [o for o in objs if o["kind"] == "SYNTHETIC_ONLY"]
    if len(syn) != 63 or [i for i in ids if i.startswith("SYN_") != (byid[i]["kind"] == "SYNTHETIC_ONLY")]: f.append("synthetic count/labelling")
    if any(i.startswith("SYN_") for i in pl): f.append("synthetic id inside district_plan.json")
    win, site = {k: v["bounds_internal"] for k, v in plan["regions"].items()}, plan["site_a_protection"]["bounds_internal"]
    for i, a in enumerate(objs):
        for b in objs[i + 1:]:
            if ov(a["b"], b["b"]): f.append(f"overlap {a['id']} / {b['id']}")
    for o in syn:
        b = o["b"]; w = win[o["region"]]
        if ov(b, site, 4): f.append(f"{o['id']} invades Site A protection")
        if b[0] < w[0] or b[1] < w[1] or b[2] > w[2] or b[3] > w[3]: f.append(f"{o['id']} outside region window")
        ci = [(i, j) for i in range(math.floor(b[0] / 5), math.ceil(b[2] / 5)) for j in range(math.floor(b[1] / 5), math.ceil(b[3] / 5))]
        if any(cells.get(c) != o["region"] for c in ci): f.append(f"{o['id']} not on WE-01 common-L0 land")
        if any(poly_hits(p, [b[0] - 2, b[1] - 2, b[2] + 2, b[3] + 2]) for ps in cors.values() for p in ps): f.append(f"{o['id']} touches a Phase 1/2 corridor")
        if terrain:
            hs = [terrain.get(c) for c in ci]
            if None in hs or max(hs) - min(hs) > fp["terrain_thresholds"]["max_span_m"] or min(hs) < fp["terrain_thresholds"]["min_height_m"]: f.append(f"{o['id']} fails the terrain check")
    if not terrain: f.append("terrain heights missing: synthetic sites cannot be checked")
    st = {k: set(v) for k, v in fp["sets"].items()}
    if not (st["40"] < st["57"] < st["60"] < st["120"] and st["120"] == set(ids)): f.append("sets are not nested 40 < 57 < 60 < 120 or set 120 is not every object")
    ex = [o for o in syn if o["id"] in st["60"]]; b3 = fp["b3_density_test"]
    for o in syn:
        want = "GLOBAL_STRESS_ONLY" if o["region"] != o["intended_region"] else "B3_DENSITY" if o["region"] == "B3" else "REGION_DENSITY"
        if o["classification"] != want: f.append(f"{o['id']}: fallback classification {o['classification']} != {want}")
        if any(ov(o["b"], [min(q[0] for q in poly), min(q[1] for q in poly), max(q[0] for q in poly), max(q[1] for q in poly)]) for poly in beach): f.append(f"{o['id']} overlaps a beach region")
    if sorted(fp["placed_outside_intended_region"]) != sorted(o["id"] for o in syn if o["region"] != o["intended_region"]): f.append("fallback list differs from the objects")
    if len(ex) != 3 or (b3["status"] == "INCONCLUSIVE") != any(o["region"] != "B3" for o in ex) or (b3["status"] == "INCONCLUSIVE" and b3["scope_exception"] != "PENDING_MARTIN_APPROVAL") or b3["we01_land_constraints_relaxed"]: f.append("b3_density_test inconsistent with the three 60-set synthetic buildings")
    for o in objs:
        if o["owner_chunk_128"] != [idx_fn((o["b"][0] + o["b"][2]) / 2, 128), idx_fn((o["b"][1] + o["b"][3]) / 2, 128)]: f.append(f"{o['id']} owner chunk")
    sc = fp["replay_scenarios"]
    if len(sc) < 5 or any(s["sim_seconds"] < 60 for s in sc): f.append("need >= 5 replay scenarios of >= 60 s simulated time")
    if sum(1 for s in sc if s["kind"] == "teleport_hold") < 1: f.append("destination-switch scenario missing")
    return f


# ------------------------------------------------------------------ triangles (A1-G12), own implementation
def samples(sc):
    if sc["kind"] == "teleport_hold": return [(x, z, 0.0) for x, z in sc["stops"] for _ in range(sc["hold_seconds"] * 2)]
    wp = sc["waypoints"]; legs = [(wp[i], wp[i + 1], math.dist(wp[i], wp[i + 1])) for i in range(len(wp) - 1)]; tot = sum(l[2] for l in legs); out = []
    for k in range(int(sc["sim_seconds"] * 2)):
        s = min(sc["speed_mps"] * k / 2, tot - 1e-6)
        for p, q, L in legs:
            if s <= L: out.append((p[0] + (q[0] - p[0]) * s / L, p[1] + (q[1] - p[1]) * s / L, math.atan2(q[1] - p[1], q[0] - p[0]))); break
            s -= L
    return out


def tri_at(pts, gx, gz, r, half=None, hd=0.0, sh_r=0):
    """Triangles at one viewpoint: view-cone/omni single pass, and the shadow-pass extra for meshes within sh_r."""
    t = sh = 0
    for x, z, pr in pts:
        d = math.hypot(x - gx, z - gz); w = TRI[pr][0 if d <= r[0] else 1 if d <= r[1] else 2]
        if d <= sh_r: sh += w
        if d <= r[2] and (half is None or d < 1e-9 or abs((math.atan2(z - gz, x - gx) - hd + math.pi) % (2 * math.pi) - math.pi) <= half): t += w
    return t, sh


def worst(pts, r, halves):
    best = {"omni": 0, **{h: 0 for h in halves}}; at = {}
    for gx in range(-1100, 600, 20):
        for gz in range(-1000, 1400, 20):
            near = []
            for x, z, pr in pts:
                dx, dz = x - gx, z - gz; dist = math.hypot(dx, dz)
                if dist <= r[2]: near.append((math.atan2(dz, dx) if dist > 1e-9 else None, TRI[pr][0 if dist <= r[0] else 1 if dist <= r[1] else 2]))
            tot = sum(t for _, t in near)
            if tot > best["omni"]: best["omni"] = tot
            todo = [h for h in halves if tot > best[h]]
            for deg in (range(0, 360, 15) if todo else ()):
                hr = math.radians(deg)
                for h in todo:
                    t = sum(w for a, w in near if a is not None and abs((a - hr + math.pi) % (2 * math.pi) - math.pi) <= h)
                    if t > best[h]: best[h] = t; at[h] = (gx, gz)
    return best, at


def v_tri(d, plan, fp, sr):
    f = []; pts = [((p["bounds_internal"][0] + p["bounds_internal"][2]) / 2, (p["bounds_internal"][1] + p["bounds_internal"][3]) / 2, p["prototype_id"]) for p in plan["parcels"] if p["phase"] <= 2]
    G0 = {"PHONE_LOW": (192650, 106000), "TABLET_MED": (226700, 143000), "DESKTOP_HIGH": (230900, 206000)}
    for name, r in LODR.items():
        halves = [math.radians(a) / 2 for a in (96, 91.5, 104.2)]; w, at = worst(pts, r, halves); t = d["triangles"]["presets"][name]
        got = (t["omni_resident_upper_bound"][0], t["view_cone"]["cone96_reference"][0], t["view_cone"]["hfov_16x9_91.5"][0], t["view_cone"]["hfov_20x9_104.2"][0])
        if got != (w["omni"], w[halves[0]], w[halves[1]], w[halves[2]]): f.append(f"{name}: triangle analysis differs {got} vs {(w['omni'], w[halves[0]], w[halves[1]], w[halves[2]])}")
        shr = sr[name.split("_")[1]]; sh = tri_at(pts, *at[halves[0]], r, sh_r=shr)[1]
        if t["shadow_range_m"] != shr or t["shadow_pass_extra_at_cone96_worst"] != sh or t["cone96_peak_viewpoint_plus_shadow_estimate"] != w[halves[0]] + sh: f.append(f"{name}: shadow estimate differs from the independent derivation")
        for sc in fp["replay_scenarios"]:
            ps = [tri_at(pts, x, z, r, halves[0], h, shr) for x, z, h in samples(sc)]; a, c = [u for u, _ in ps], [u + v for u, v in ps]; rp = t["replay_path"][sc["name"]]
            if (rp["p95"], rp["max"], rp["p95_incl_shadow"], rp["max_incl_shadow"]) != (rank(a, 95), max(a), rank(c, 95), max(c)): f.append(f"{name}/{sc['name']}: replay P95 differs from the independent derivation")
        if name in G0 and w["omni"] != G0[name][0]: f.append(f"{name}: omni upper bound {w['omni']} does not reproduce the G0 reference {G0[name][0]}")
        if name in G0 and abs(w[halves[0]] - G0[name][1]) > 0.01 * G0[name][1]: f.append(f"{name}: cone-96 {w[halves[0]]} does not reproduce G0 {G0[name][1]} within 1 %")
    return f


def v_benefit(d, fp):
    f = []; byid = {o["id"]: o for o in fp["objects"]}; paths = [samples(sc) for sc in fp["replay_scenarios"]]; ben = d["benefit"]
    if ben["assumptions"]["bodies_per_building"] != 1 or ben["assumptions"]["radii_m"] != list(RADII): f.append("benefit assumptions (1 body per building, radius list) missing")
    for n in ("40", "57", "60"):
        pts = [((byid[i]["b"][0] + byid[i]["b"][2]) / 2, (byid[i]["b"][1] + byid[i]["b"][3]) / 2) for i in fp["sets"][n]]; row = ben["sets"][n]
        if row["shared_prototype_model_resident_triangles"] != sum(sum(v) for v in TRI.values()) or row["unique_asset_model_all_resident_triangles"] != sum(sum(TRI[byid[i]["proto"]]) for i in fp["sets"][n]): f.append(f"benefit set {n}: Control A resident model differs (no duplicated resources allowed)")
        for R in RADII:
            cnt = lambda gx, gz: sum(1 for x, z in pts if math.hypot(x - gx, z - gz) <= R); peak = max(cnt(gx, gz) for gx in range(-1100, 600, 40) for gz in range(-1000, 1400, 40)); rep = [cnt(x, z) for p in paths for x, z, _ in p]; r = row["by_radius"][str(R)]
            if (r["max_active_bodies_peak_grid"], r["replay_active_p95"], r["replay_active_max"]) != (peak, rank(rep, 95), max(rep)) or not close(r["saving_peak"], round(1 - peak / len(pts), 3), 2e-3) or not close(r["saving_replay_p95"], round(1 - rank(rep, 95) / len(pts), 3), 2e-3): f.append(f"benefit set {n} r{R}: active-body numbers differ")
    return f


# ------------------------------------------------------------------ labels, budgets, protection
def walk(o, path=()):
    if isinstance(o, dict):
        yield path, o
        for k, v in o.items(): yield from walk(v, path + (k,))
    elif isinstance(o, list):
        for i, v in enumerate(o): yield from walk(v, path + (str(i),))


def v_labels(d, bud, base):
    f = []
    for sec in ("triangles", "chunks", "benefit"):
        if d[sec]["source_class"] != "ANALYTIC_ESTIMATE": f.append(f"calibration_data.{sec} must be ANALYTIC_ESTIMATE")
    if d["speed"]["code_derived_ceilings_mps"]["source_class"] != "ANALYTIC_ESTIMATE" or d["speed"]["source_constants"]["source_class"] != "SOURCE_CONFIRMED": f.append("speed classes")
    if d["speed"]["t_ready_method"]["claimed_measured"]: f.append("T_ready must not be claimed as measured")
    runs = {f"{r['model'] or 'default'}|L{r['upgrade']}|{'nitro' if r['nitro'] else 'plain'}": round(r["peak_mps"], 2) for r in base.get("speed", {}).get("runs", [])}
    if d["speed"]["measured_peak_lower_bounds_mps"]["runs"] != runs: f.append("measured speed lower bounds differ from baseline_metrics.json")
    top = d["speed"]["code_derived_ceilings_mps"]["max_upgrade_nitro"]
    if any(v > top for v in runs.values()): f.append("a measured peak speed exceeds the code-derived ceiling: the ceiling derivation is wrong")
    for path, o in walk(bud):
        c = o.get("source_class") if isinstance(o, dict) else None
        if "value" in o and c not in CLASSES: f.append(f"budget {'/'.join(path)}: missing/unknown source_class")
        if c == "MEASURED_HEADLESS" and "base_headless" not in path: f.append(f"budget {'/'.join(path)}: MEASURED_HEADLESS outside base_headless")
        if c == "PENDING_DEVICE" and o.get("value") not in ("PENDING_DEVICE", 40, 66.7): f.append(f"budget {'/'.join(path)}: device value")
    for path, o in walk(d):
        if o.get("source_class") == "MEASURED_HEADLESS" and path[:1] not in (("speed",), ("baseline_analysis",)): f.append(f"calibration_data {'/'.join(path)}: MEASURED_HEADLESS outside speed/baseline_analysis")
    if sorted(bud["presets"]) != sorted(FOUR): f.append(f"budget presets must be exactly {FOUR} (a measured preset has no budget row)")
    exp = lambda k: "PROPOSED_LIMIT" if k.startswith(("added_", "active_", "physics_", "streaming_", "lod_")) else "ANALYTIC_ESTIMATE" if k.startswith("analytic_") else "PENDING_DEVICE" if k.startswith("device_") else None
    if sorted(bud["preset_mapping"]) != sorted(PRESETS11) or any(o["source_class"] != "PROPOSED_LIMIT" for o in bud["preset_mapping"].values()): f.append("preset_mapping must cover the 11 presets, all PROPOSED_LIMIT")
    for name, p in bud["presets"].items():
        f += [f"budget {name}.{k}: expected class {exp(k)}, got {o['source_class']}" for k, o in p.items() if exp(k) and o["source_class"] != exp(k)]
        if p.get("triangle_budget_comparison", {}).get("status") != "NOT_VALIDATED": f.append(f"budget {name}: triangle budget must stay NOT_VALIDATED")
        for k in ("added_draw_calls_p95", "added_triangles_p95", "active_bodies", "active_shapes", "physics_step_median_ratio", "streaming_cpu_ms_p95", "device_avg_fps"):
            if k not in p: f.append(f"budget {name}.{k} missing")
    if bud["status"] != "PROPOSED_NOT_APPROVED": f.append("budgets must stay PROPOSED_NOT_APPROVED")
    if "a2_required_fields" not in bud["device_protocol"] or bud["device_protocol"]["fps_acceptance"]["cap_30_threshold"] != 29.1: f.append("device protocol incomplete")
    return f


def v_protected(base, files=None):
    """Byte-identity of protected files against the blobs recorded at measurement time (works without git history)."""
    f = []; rec = base["environment"]["protected_blobs_at_engineering_base"]
    for rel in ("index.html", "sw.js", "manifest.webmanifest", "manifest.zh-TW.webmanifest"):
        if rel not in rec: f.append(f"{rel}: no recorded blob")
    for rel, sha in rec.items():
        cur = (files or {}).get(rel) or (blob_sha1(ROOT / rel) if (ROOT / rel).exists() else None)
        if cur != sha: f.append(f"protected file changed: {rel}")
    return f


def v_changed_files(changed):
    return [f"unapproved change: {p}" for p in changed if not p.startswith(ALLOW)]


def git_changed():
    r = subprocess.run(["git", "diff", "--name-only", BASE], cwd=ROOT, capture_output=True, text=True)
    u = subprocess.run(["git", "ls-files", "--others", "--exclude-standard"], cwd=ROOT, capture_output=True, text=True)
    return None if r.returncode else sorted(set(r.stdout.split() + u.stdout.split()))


# ------------------------------------------------------------------ main + negative controls
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dir", default=str(ROOT / "specs/we03")); ap.add_argument("--skip-git", action="store_true"); a = ap.parse_args(); D = Path(a.dir)
    d, fp, bud, base = (J(D / n) for n in ("calibration_data.json", "fixture_plan.json", "proposed_budgets.json", "baseline_metrics.json"))
    plan = J(ROOT / "specs/we02/district_plan.json"); src = (ROOT / "index.html").read_text(); lines = src.splitlines()
    cells = {(math.floor(float(r["x_center"]) / 5), math.floor(float(r["z_center"]) / 5)): r["region_id"] for r in csv.DictReader(open(ROOT / "tools/fixtures/we01/we01a_common_l0_cells.csv"))}
    t = base.get("terrain_l0") or {}; terrain = {(math.floor(x / 5), math.floor(z / 5)): h for x, z, h in zip(t.get("x", []), t.get("z", []), t.get("height_m", []))}
    beach = J(ROOT / "tools/fixtures/we01/e_formal/map_geometry.json")["beach_regions"]; sr = dict(zip(("LOW", "MED", "HIGH", "ULTRA"), map(int, re.search(r"shadowRange: \{ LOW: (\d+), MED: (\d+), HIGH: (\d+), ULTRA: (\d+)", src).groups())))
    st = J(ROOT / "tools/fixtures/we01/e_formal/internal_streets.json"); rs = J(ROOT / "tools/fixtures/we01/e_formal/road_survey.json")
    streets = {s["street_id"]: s["corridor_geometry"]["polygon"] for r in ("B1", "B2", "B3") for s in st["scenarios"]["ENVELOPE"][r]["selected_streets"]}
    cand = {}
    for c in rs["candidate_corridors"]:
        if c["id"].startswith("CAND_"): cand.setdefault(c["id"].split("_")[1], []).append(c["polygon"])
    eng = sorted({i["id"] for ph in plan["phases"].values() for i in ph["engineering"]["items"]}); cors = {i: ([streets[i]] if i in streets else cand[i]) for i in eng}
    fails = {}
    checks = {"baseline": lambda: v_baseline(base, d), "source": lambda: v_source(lines, src, d), "chunks": lambda: v_chunks(d, plan), "fixture": lambda: v_fixture(fp, plan, cors, cells, terrain, beach),
              "triangles": lambda: v_tri(d, plan, fp, sr), "benefit": lambda: v_benefit(d, fp), "labels": lambda: v_labels(d, bud, base), "runtime": lambda: v_runtime(base, d), "protected": lambda: v_protected(base)}
    for k, fn in checks.items(): fails[k] = fn()
    changed = None if a.skip_git else git_changed()
    fails["allowlist"] = v_changed_files(changed) if changed is not None else []
    print("git allowlist:", "skipped (no history)" if changed is None else f"{len(changed)} changed paths")
    for k, v in fails.items(): print(("PASS " if not v else "FAIL ") + k, *([] if not v else [f"\n   - {m}" for m in v[:8]]))
    bad = [k for k, v in fails.items() if v]
    pc = d["baseline_analysis"]["physics_control"]; print("artifact validation:", "FAIL" if bad else "PASS", "| measurement validity: physics control", {p: pc[p]["status"] for p in FOUR}, "| frame time as hard gate:", "usable" if d["baseline_analysis"]["gate_stability"]["frame_time_usable_as_hard_gate"] else "INCONCLUSIVE", "| B3 density:", fp["b3_density_test"]["status"])
    # ---- negative controls: every mutation must turn at least one validator red
    neg = []
    def mut(name, fn, key):
        r = [m for m in fn() if key in m]; neg.append((name, bool(r)))      # red only when the validator names the expected defect
        print(("  RED   " if r else "  GREEN (control failed) ") + name + (f"  <- {r[0][:90]}" if r else ""))
    def M(o, fn): x = copy.deepcopy(o); fn(x); return x
    fx = lambda x: v_fixture(x, plan, cors, cells, terrain, beach); syn0 = lambda x: next(o for o in x["objects"] if o["kind"] == "SYNTHETIC_ONLY"); moved0 = lambda x: next(o for o in x["objects"] if o["id"] in x["placed_outside_intended_region"])
    pcd = lambda x: x["baseline_analysis"]["physics_control"]; pairs = lambda x, p="PHONE_MED": x["physics_pairs"][p]["pairs"]; inv = lambda x: x["source_inventory"]["position_reset_inventory"]
    def combo(x): k = next(iter(x["combinations"])); [x["combinations"][k]["samples"].__setitem__(n, x["combinations"][k]["samples"][n][:100]) for n in ARRAYS]; x["combinations"][k]["recorded_frames"] = 100
    def overlap(x): p = x["objects"][0]; syn0(x)["b"] = [p["b"][0] + 1, p["b"][1] + 1, p["b"][0] + 20, p["b"][1] + 20]
    for name, fn, key in (
            ("missing preset", lambda: v_source(lines, src, M(d, lambda x: x["presets"].pop("TABLET_HIGH"))), "missing from calibration_data"),
            ("missing measurement combination", lambda: v_baseline(M(base, lambda x: x["combinations"].pop("PHONE_LOW/B1/12:00"))), "missing measurement combinations"),
            ("recorded frames < 120", lambda: v_baseline(M(base, combo)), "frames"),
            ("duplicate object ID", lambda: fx(M(fp, lambda x: x["objects"].append(copy.deepcopy(x["objects"][0])))), "duplicate object ID"),
            ("negative-coordinate indexing error", lambda: v_chunks(d, plan, idx_fn=lambda v, g: int(v // g) if v >= 0 else int(-(-v // g))), "negative/boundary index"),
            ("synthetic buildings overlap", lambda: fx(M(fp, overlap)), "overlap"),
            ("wrong prototype counts", lambda: fx(M(fp, lambda x: next(o for o in x["objects"] if o["proto"] == "R05").update(proto="R01"))), "composition"),
            ("synthetic invades Site A", lambda: fx(M(fp, lambda x: syn0(x).update(b=[-540, -820, -500, -790]))), "invades Site A"),
            ("synthetic on a beach region", lambda: fx(M(fp, lambda x: syn0(x).update(b=[300, 0, 330, 30]))), "beach region"),
            ("sets not nested", lambda: fx(M(fp, lambda x: x["sets"]["60"].pop(0))), "not nested"),
            ("fallback misclassified", lambda: fx(M(fp, lambda x: moved0(x).update(classification="B3_DENSITY"))), "fallback classification"),
            ("B3 density claimed as placed", lambda: fx(M(fp, lambda x: x["b3_density_test"].update(status="PLACED"))), "b3_density_test inconsistent"),
            ("unmeasured value labelled measured", lambda: v_labels(d, M(bud, lambda x: x["presets"]["PHONE_LOW"]["active_bodies"].update(source_class="MEASURED_HEADLESS")), base), "MEASURED_HEADLESS outside base_headless"),
            ("analytic estimate labelled MEASURED", lambda: v_labels(M(d, lambda x: x["triangles"].update(source_class="MEASURED_HEADLESS")), bud, base), "must be ANALYTIC_ESTIMATE"),
            ("budget label swapped", lambda: v_labels(d, M(bud, lambda x: x["presets"]["PHONE_LOW"]["added_triangles_p95"].update(source_class="ANALYTIC_ESTIMATE")), base), "expected class PROPOSED_LIMIT"),
            ("PHONE_MED budget row dropped", lambda: v_labels(d, M(bud, lambda x: x["presets"].pop("PHONE_MED")), base), "budget presets must be exactly"),
            ("manifest.webmanifest modified", lambda: v_protected(base, {"manifest.webmanifest": "0" * 40}) + v_changed_files(["manifest.webmanifest"]), "manifest.webmanifest"),
            ("index.html modified", lambda: v_changed_files(["index.html"]), "unapproved change: index.html"),
            ("triangle analysis tampered", lambda: v_tri(M(d, lambda x: x["triangles"]["presets"]["PHONE_LOW"]["omni_resident_upper_bound"].__setitem__(0, 192651)), plan, fp, sr), "triangle analysis differs"),
            ("shadow estimate tampered", lambda: v_tri(M(d, lambda x: x["triangles"]["presets"]["PHONE_LOW"].update(shadow_pass_extra_at_cone96_worst=1)), plan, fp, sr), "shadow estimate differs"),
            ("replay P95 tampered", lambda: v_tri(M(d, lambda x: x["triangles"]["presets"]["PHONE_LOW"]["replay_path"]["S1_B1_border_sweep"].update(p95=1)), plan, fp, sr), "replay P95 differs"),
            ("benefit active bodies tampered", lambda: v_benefit(M(d, lambda x: x["benefit"]["sets"]["57"]["by_radius"]["217"].update(max_active_bodies_peak_grid=1)), fp), "active-body numbers differ"),
            ("device profile mismatch (tablet measured as iGPU)", lambda: v_runtime(M(base, lambda x: x["preset_runtime"]["TABLET_MED"]["settings"].update(fpsCap=60)), d), "preset_runtime TABLET_MED"),
            ("speed ceiling below a measured peak", lambda: v_labels(M(d, lambda x: x["speed"]["code_derived_ceilings_mps"].update(max_upgrade_nitro=81.9)), bud, base), "exceeds the code-derived ceiling"),
            ("position reset inventory incomplete", lambda: v_source(lines, src, M(d, lambda x: inv(x)["creation_or_other_sites"].pop())), "position reset inventory incomplete"),
            ("physics pairs from reused pages", lambda: v_phys(M(base, lambda x: [r.pop("session_model") for r in x["physics_pairs"].values()]), d), "session_model fresh_session_per_side"),
            ("physics pair order not alternating", lambda: v_phys(M(base, lambda x: pairs(x)[1].update(order=["A", "B"])), d), "order does not alternate"),
            ("physics sides differ in bodies", lambda: v_phys(M(base, lambda x: pairs(x)[0]["bodies"].update(B=1)), d), "bodies/shapes differ"),
            ("physics readiness not reached", lambda: v_phys(M(base, lambda x: pairs(x)[0]["ph_done"].update(A=False)), d), "readiness"),
            ("physics status faked STABLE", lambda: v_phys(base, M(d, lambda x: pcd(x)["DESKTOP_HIGH"].update(status="STABLE"))), "from the control band"),
            ("physics step protocol changed", lambda: v_phys(M(base, lambda x: x["physics_pairs"]["TABLET_MED"].update(warmup_steps=300)), d), "900 warm-up + 360 recorded"),
            ("retained revision-0 physics evidence altered", lambda: v_phys(M(base, lambda x: x["physics_pairs_v1_reused_pages"]["data"]["PHONE_LOW"]["pairs"][0].update(ratio_B_over_A=1.5)), d), "differs from PR #132"),
            ("original physics evidence dropped", lambda: v_phys(M(base, lambda x: x.pop("physics_pairs_v1_reused_pages")), d), "not retained")):
        mut(name, fn, key)
    green = [n for n, ok in neg if not ok]
    print(f"negative controls: {len(neg) - len(green)}/{len(neg)} red")
    if bad or green:
        print("FAILED:", bad, green); sys.exit(1)
    print("we03_calibration_check: all gates PASS")


if __name__ == "__main__":
    main()
