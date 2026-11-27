#!/usr/bin/env python3
"""WE-01A (T-016A): Read-only runtime dump analyzer and land classifier (stdlib only)."""
from __future__ import annotations
import argparse, csv, hashlib, json, math, sys
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

ANALYZER_VERSION = "we01a-1.0"
CLASSES = ("L4", "L5", "LX", "L2", "L3", "L1", "L0")
PRIORITY = {c: i for i, c in enumerate(CLASSES)}
SLOPE_CLASSES = ("S0", "S1", "S2", "S3", "S4", "UNKNOWN")
REQ_TOP = ("schema_version", "metadata", "world", "regions", "height_grids", "footprints", "roads", "completeness", "issues")
REQ_META = ("base_sha", "game_release", "preset", "initialization_complete", "showcase_visible", "night",
            "extraction_version", "generated_at", "coordinate_unit", "generation_settings", "static_fingerprint", "source_counts", "source_fingerprints")
REQ_SC = ("WORLD.buildings", "WORLD.cityInfill", "WORLD.suburbHouses", "TREES", "TREE_COLLIDERS")
REQ_COMP = ("world_bounds", "terrain_heights", "physical_ground", "terrain_regions", "visual_occupancy",
            "physical_occupancy", "trees", "water_and_beach", "protected_areas", "roads", "traffic_routes")
LAND_REQ_COMP = ("terrain_heights", "physical_ground", "terrain_regions", "visual_occupancy",
                 "physical_occupancy", "trees", "water_and_beach", "protected_areas", "roads")
VALID_PRESETS, VALID_COMP = {"PHONE_LOW", "DESKTOP_HIGH"}, {"COMPLETE", "PARTIAL", "UNKNOWN", "NOT_APPLICABLE"}
VALID_CATS = {"BUILDING", "COLLIDER", "TREE", "ROAD", "SIDEWALK", "RAMP", "BRIDGE", "PARK",
              "WATER", "BEACH", "SITE_A", "AIRPORT", "MISSION", "FAST_TRAVEL", "BOUNDARY", "OTHER"}
VALID_PREC, VALID_ELEV = {"EXACT_OUTLINE", "CONSERVATIVE_AABB"}, {"GROUND", "ELEVATED", "RAMP", "UNKNOWN"}
DYNAMIC_FORBIDDEN = ("DYNAMIC", "PHYSICS_DYNAMIC", "DYNAMIC_BODIES", "TRAFFIC_LIVE")
CELL_STEP, CONSERVATION_TOL_M2 = 5.0, 1.0


class ValidationError(ValueError):
    """Raised on schema, BASE, fingerprint, or area-conservation violations."""


def _req(cond: bool, msg: str) -> None:
    if not cond:
        raise ValidationError(msg)


def _num(v: Any) -> bool: return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
def _int(v: Any) -> bool: return isinstance(v, int) and not isinstance(v, bool)
def _ascii(s: Any) -> bool: return isinstance(s, str) and bool(s) and s.isascii()
def _mm(x: Any) -> int | None: return None if x is None else math.floor(x * 1000 + 0.5)


def compute_static_fingerprint(d: dict[str, Any]) -> str:
    """Recompute C3 canonical static fingerprint (matches fingerprint_reference.py)."""
    poly = lambda p: [[_mm(a), _mm(b)] for a, b in p]
    by_id = lambda a: sorted(a, key=lambda o: o["id"])
    fps = []
    for x in d["footprints"]:
        o = {k: x[k] for k in ("id", "category", "source_group", "geometry_type", "geometry_precision", "visual", "physical", "protected")}
        o["polygon"] = poly(x["polygon"]) if x["polygon"] else None
        o["bounds"], o["y_min"], o["y_max"] = [_mm(v) for v in x["bounds"]], _mm(x["y_min"]), _mm(x["y_max"])
        if "parent_id" in x:
            o["parent_id"] = x["parent_id"]
        fps.append(o)
    w, r = d["world"], d["roads"]
    view = {
        "physical_ground": {"bounds": [_mm(v) for v in w["physical_ground"]["bounds"]], "top_y": _mm(w["physical_ground"]["top_y"])},
        "terrain_regions": by_id([{"id": t["id"], "polygon": poly(t["polygon"]), "margin_m": _mm(t["margin_m"]), "terrain_support_status": t["terrain_support_status"]} for t in w["terrain_regions"]]),
        "water_regions": [poly(p) for p in w["water_regions"]],
        "beach_regions": [poly(p) for p in w["beach_regions"]],
        "regions": by_id([{"id": g["id"], "name": g["name"], "initial_polygon": poly(g["initial_polygon"]), "survey_polygon": poly(g["survey_polygon"]), "buffer_m": _mm(g["buffer_m"])} for g in d["regions"]]),
        "height_grids": by_id([{"id": g["id"], "region_id": g["region_id"], "origin_x": _mm(g["origin_x"]), "origin_z": _mm(g["origin_z"]), "step_m": _mm(g["step_m"]), "nx": g["nx"], "nz": g["nz"], "heights": [_mm(h) for h in g["heights"]], "source": g["source"], "sample_method": g["sample_method"]} for g in d["height_grids"]]),
        "footprints": by_id(fps),
        "roads": {
            "completeness": r["completeness"],
            "nodes": by_id([{"id": n["id"], "x": _mm(n["x"]), "y": _mm(n["y"]), "z": _mm(n["z"]), "connected_segment_ids": sorted(n["connected_segment_ids"])} for n in r["nodes"]]),
            "segments": by_id([{"id": s["id"], "start_node_id": s["start_node_id"], "end_node_id": s["end_node_id"], "centerline": [[_mm(v) for v in p] for p in s["centerline"]], "carriageway_width_m": _mm(s["carriageway_width_m"]), "sidewalk_left_m": _mm(s["sidewalk_left_m"]), "sidewalk_right_m": _mm(s["sidewalk_right_m"]), "corridor_footprint_ids": sorted(s["corridor_footprint_ids"]), "elevation_type": s["elevation_type"], "traffic_route_ids": sorted(s["traffic_route_ids"])} for s in r["segments"]]),
        },
        "source_counts": d["metadata"]["source_counts"],
        "completeness": d["completeness"],
    }
    return hashlib.sha256(json.dumps(view, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


# -------------------- Exact 2D geometry helpers --------------------

def poly_bounds(pts: list[list[float]]) -> tuple[float, float, float, float]:
    xs, zs = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs), min(zs), max(xs), max(zs)


def poly_area(pts: list[list[float]]) -> float:
    n = len(pts)
    return 0.0 if n < 3 else abs(sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n))) * 0.5


def is_axis_rect(pts: list[list[float]]) -> bool:
    if len(pts) != 4:
        return False
    b = poly_bounds(pts)
    return abs(poly_area(pts) - (b[2] - b[0]) * (b[3] - b[1])) < 1e-6


def validate_polygon(pts: Any, ctx: str, allow_zero_area: bool = False) -> None:
    _req(isinstance(pts, list) and len(pts) >= 3, f"{ctx}: polygon requires >=3 vertices")
    for p in pts:
        _req(isinstance(p, list) and len(p) == 2 and _num(p[0]) and _num(p[1]), f"{ctx}: invalid vertex {p!r}")
    _req(allow_zero_area or poly_area(pts) > 1e-9, f"{ctx}: degenerate zero-area polygon")
    o = lambda p, q, r: (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        for j in range(i + 2, n):
            if not (i == 0 and j == n - 1):
                c, d = pts[j], pts[(j + 1) % n]
                _req(not ((o(a, b, c) * o(a, b, d) < -1e-12) and (o(c, d, a) * o(c, d, b) < -1e-12)), f"{ctx}: self-intersecting polygon")


def _val_bounds(b: Any, ctx: str, allow_flat: bool = False) -> None:
    _req(isinstance(b, list) and len(b) == 4 and all(_num(v) for v in b), f"{ctx}: invalid bounds {b!r}")
    _req(b[0] <= b[2] and b[1] <= b[3] and (allow_flat or (b[0] < b[2] and b[1] < b[3])), f"{ctx}: inverted/empty bounds {b!r}")


def clip_poly_to_rect(pts: list[list[float]], x0: float, z0: float, x1: float, z1: float) -> list[list[float]]:
    out = pts
    edges = (
        (lambda p: p[0] >= x0, lambda a, b: [x0, a[1] + (b[1] - a[1]) * (x0 - a[0]) / (b[0] - a[0])]),
        (lambda p: p[0] <= x1, lambda a, b: [x1, a[1] + (b[1] - a[1]) * (x1 - a[0]) / (b[0] - a[0])]),
        (lambda p: p[1] >= z0, lambda a, b: [a[0] + (b[0] - a[0]) * (z0 - a[1]) / (b[1] - a[1]), z0]),
        (lambda p: p[1] <= z1, lambda a, b: [a[0] + (b[0] - a[0]) * (z1 - a[1]) / (b[1] - a[1]), z1]),
    )
    for inside, cut in edges:
        if not out:
            return []
        nxt, prev = [], out[-1]
        pin = inside(prev)
        for cur in out:
            cin = inside(cur)
            if cin:
                if not pin: nxt.append(cut(prev, cur))
                nxt.append(cur)
            elif pin:
                nxt.append(cut(prev, cur))
            prev, pin = cur, cin
        out = nxt
    return out


def poly_rect_area(pts: list[list[float]], is_rect: bool, b: tuple[float, float, float, float], x0: float, z0: float, x1: float, z1: float) -> float:
    if b[2] <= x0 or b[0] >= x1 or b[3] <= z0 or b[1] >= z1:
        return 0.0
    if is_rect:
        dx, dz = min(b[2], x1) - max(b[0], x0), min(b[3], z1) - max(b[1], z0)
        return dx * dz if dx > 0.0 and dz > 0.0 else 0.0
    return poly_area(clip_poly_to_rect(pts, x0, z0, x1, z1))


def fp_intersects_cell(pts: list[list[float]], is_rect: bool, b: tuple[float, float, float, float], x0: float, z0: float, x1: float, z1: float) -> tuple[bool, float]:
    if b[2] < x0 or b[0] > x1 or b[3] < z0 or b[1] > z1:
        return False, 0.0
    if (b[2] - b[0]) <= 1e-9 or (b[3] - b[1]) <= 1e-9:
        hit = (b[2] == b[0] and x0 < b[0] < x1 and b[3] > z0 and b[1] < z1) or (b[3] == b[1] and z0 < b[1] < z1 and b[2] > x0 and b[0] < x1)
        return hit, 0.0
    oa = poly_rect_area(pts, is_rect, b, x0, z0, x1, z1)
    return oa > 1e-9, oa


def polys_union_area_in_rect(polys: list[list[list[float]]], x0: float, z0: float, x1: float, z1: float) -> float:
    clipped = [c for p in polys if (c := clip_poly_to_rect(p, x0, z0, x1, z1)) and poly_area(c) > 1e-12]
    if len(clipped) <= 1:
        return poly_area(clipped[0]) if clipped else 0.0
    xs, edges = {x0, x1}, []
    for p in clipped:
        for i, a in enumerate(p):
            b = p[(i + 1) % len(p)]
            xs.add(a[0])
            if abs(a[0] - b[0]) > 1e-12: edges.append((a, b))
    for i, (a, b) in enumerate(edges):
        for c, d in edges[i + 1:]:
            den = (a[0] - b[0]) * (c[1] - d[1]) - (a[1] - b[1]) * (c[0] - d[0])
            if abs(den) > 1e-12:
                t = ((a[0] - c[0]) * (c[1] - d[1]) - (a[1] - c[1]) * (c[0] - d[0])) / den
                u = -((a[0] - b[0]) * (a[1] - c[1]) - (a[1] - b[1]) * (a[0] - c[0])) / den
                if 0.0 < t < 1.0 and 0.0 < u < 1.0: xs.add(a[0] + t * (b[0] - a[0]))
    sxs, total = sorted(xs), 0.0
    for xa, xb in zip(sxs, sxs[1:]):
        if xb - xa < 1e-12: continue
        xm, ivs = 0.5 * (xa + xb), []
        for p in clipped:
            ys = sorted(a[1] + (b[1] - a[1]) * (xm - a[0]) / (b[0] - a[0])
                        for i, a in enumerate(p) for b in (p[(i + 1) % len(p)],)
                        if (a[0] <= xm < b[0]) or (b[0] <= xm < a[0]))
            ivs.extend((ys[m], ys[m + 1]) for m in range(0, len(ys) - 1, 2))
        if ivs:
            ivs.sort()
            ca, cb, span = ivs[0][0], ivs[0][1], 0.0
            for ia, ib in ivs[1:]:
                if ia <= cb: cb = max(cb, ib)
                else: span += cb - ca; ca, cb = ia, ib
            total += (xb - xa) * (span + cb - ca)
    return total


def dist_point_to_poly(x: float, z: float, pts: list[list[float]]) -> float:
    inside, best, n = False, float("inf"), len(pts)
    for i in range(n):
        x1, z1 = pts[i]; x2, z2 = pts[(i + 1) % n]
        if ((z1 > z) != (z2 > z)) and (x < (x2 - x1) * (z - z1) / (z2 - z1) + x1): inside = not inside
        dx, dz = x2 - x1, z2 - z1
        l2 = dx * dx + dz * dz
        t = 0.0 if l2 < 1e-12 else max(0.0, min(1.0, ((x - x1) * dx + (z - z1) * dz) / l2))
        best = min(best, math.hypot(x - (x1 + t * dx), z - (z1 + t * dz)))
    return 0.0 if inside else best


# -------------------- Schema v1 validation (§5.12 & C3) --------------------

def validate_dump(d: Any, opts: dict[str, Any] | None = None) -> dict[str, Any]:
    opts = opts or {}
    _req(isinstance(d, dict) and all(k in d for k in REQ_TOP), "Invalid root or missing top-level field")
    _req(_int(d["schema_version"]) and d["schema_version"] == 1, f"Unsupported schema_version: {d['schema_version']!r}")
    meta = d["metadata"]
    _req(isinstance(meta, dict) and all(k in meta for k in REQ_META), "Invalid/incomplete metadata")
    sha = meta["base_sha"]
    _req(isinstance(sha, str) and len(sha) == 40 and all(c in "0123456789abcdef" for c in sha.lower()), f"Invalid base_sha: {sha!r}")
    _req(meta["preset"] in VALID_PRESETS and meta["coordinate_unit"] == "m", "Invalid preset or coordinate_unit")
    _req(all(isinstance(meta[k], bool) for k in ("initialization_complete", "showcase_visible", "night")), "Invalid metadata booleans")
    sc = meta["source_counts"]
    _req(isinstance(sc, dict) and all(k in sc and (sc[k] is None or (_int(sc[k]) and sc[k] >= 0)) for k in REQ_SC), "Invalid source_counts")
    w = d["world"]
    _req(isinstance(w, dict) and all(k in w for k in ("ground_bounds", "playable_bounds", "physical_ground", "terrain_regions", "water_regions", "beach_regions", "map_ui_bounds", "boundary_obstacles", "source_refs")), "Incomplete world object")
    for bk in ("ground_bounds", "playable_bounds", "map_ui_bounds"):
        if w[bk] is not None: _val_bounds(w[bk], f"world.{bk}")
    pg = w["physical_ground"]
    _req(isinstance(pg, dict) and pg.get("shape") == "BOX" and pg.get("verification") in {"RUNTIME_VERIFIED", "UNKNOWN"} and _num(pg.get("top_y")), "Invalid physical_ground")
    _req(isinstance(pg.get("half_extents"), list) and len(pg["half_extents"]) == 3 and all(_num(v) and v > 0 for v in pg["half_extents"]), "Invalid physical_ground.half_extents")
    _req(isinstance(pg.get("position"), list) and len(pg["position"]) == 3 and all(_num(v) for v in pg["position"]), "Invalid physical_ground.position")
    _val_bounds(pg.get("bounds"), "world.physical_ground.bounds")
    tr_ids = set()
    for tr in w["terrain_regions"]:
        _req(_ascii(tr.get("id")) and tr["id"] not in tr_ids and _num(tr.get("margin_m")) and tr["margin_m"] >= 0 and tr.get("terrain_support_status") in {"VERIFIED", "UNKNOWN", "NOT_APPLICABLE"}, f"Invalid terrain_region: {tr.get('id')!r}")
        tr_ids.add(tr["id"]); validate_polygon(tr.get("polygon"), f"terrain_region.{tr['id']}")
    for i, wp in enumerate(w["water_regions"]): validate_polygon(wp, f"world.water_regions[{i}]")
    for i, bp in enumerate(w["beach_regions"]): validate_polygon(bp, f"world.beach_regions[{i}]")
    _req(isinstance(d["regions"], list) and bool(d["regions"]), "regions must be non-empty list")
    reg_ids = {}
    for reg in d["regions"]:
        rid = reg.get("id")
        _req(_ascii(rid) and rid not in reg_ids and _num(reg.get("buffer_m")) and reg["buffer_m"] >= 0, f"Invalid/duplicate region: {rid!r}")
        validate_polygon(reg.get("initial_polygon"), f"region.{rid}.initial_polygon")
        validate_polygon(reg.get("survey_polygon"), f"region.{rid}.survey_polygon")
        reg_ids[rid] = reg
    grid_ids = set()
    for g in d["height_grids"]:
        gid, rgid = g.get("id"), g.get("region_id")
        _req(_ascii(gid) and gid not in grid_ids and rgid in (set(reg_ids) | {"WORLD", "ROAD_CORRIDOR"}), f"Invalid/duplicate height_grid: {gid!r}")
        grid_ids.add(gid)
        _req(_num(g.get("origin_x")) and _num(g.get("origin_z")) and _num(g.get("step_m")) and g["step_m"] > 0 and _int(g.get("nx")) and _int(g.get("nz")) and g["nx"] >= 2 and g["nz"] >= 2, f"Invalid grid dims on {gid}")
        _req(g.get("source") == "runtime_terrainHeight" and g.get("sample_method") == "DIRECT_RUNTIME", f"Invalid grid source on {gid}")
        hs = g.get("heights")
        _req(isinstance(hs, list) and (opts.get("allow_bad_height_len") or len(hs) == g["nx"] * g["nz"]), f"Grid {gid}: heights length mismatch")
        _req(all(h is None or _num(h) for h in hs), f"Grid {gid}: non-finite height")
        if rgid == "WORLD": _req(abs(g["step_m"] - 20.0) <= 1e-6, f"WORLD grid {gid} step_m != 20")
        elif rgid in reg_ids:
            _req(abs(g["step_m"] - 1.0) <= 1e-6, f"Region grid {gid} step_m != 1")
            sb = poly_bounds(reg_ids[rgid]["survey_polygon"])
            _req(g["origin_x"] <= sb[0] + 1e-6 and g["origin_x"] + (g["nx"] - 1) * g["step_m"] >= sb[2] - 1e-6 and g["origin_z"] <= sb[1] + 1e-6 and g["origin_z"] + (g["nz"] - 1) * g["step_m"] >= sb[3] - 1e-6, f"Region grid {gid} does not cover {rgid}")
        else: _req(abs(g["step_m"] - 1.0) <= 1e-6, f"Corridor grid {gid} step_m != 1")
    fp_ids = set()
    for fp in d["footprints"]:
        fid, sg = fp.get("id"), fp.get("source_group", "")
        _req(_ascii(fid) and fid not in fp_ids and fp.get("category") in VALID_CATS and fp.get("geometry_type") in {"POLYGON", "AABB"} and fp.get("geometry_precision") in VALID_PREC and fp.get("verification") in {"RUNTIME_VERIFIED", "UNKNOWN"}, f"Invalid footprint {fid!r}")
        _req(isinstance(sg, str) and not any(tok in sg.upper() for tok in DYNAMIC_FORBIDDEN), f"Forbidden dynamic source_group on {fid}: {sg!r}")
        _req(all(isinstance(fp.get(k), bool) for k in ("visual", "physical", "protected")) and all(fp.get(k) is None or _num(fp[k]) for k in ("y_min", "y_max")), f"Invalid footprint attrs on {fid}")
        _val_bounds(fp.get("bounds"), f"footprint.{fid}.bounds", allow_flat=True)
        if fp.get("polygon") is not None: validate_polygon(fp["polygon"], f"footprint.{fid}.polygon", allow_zero_area=(fp["geometry_type"] == "AABB"))
        fp_ids.add(fid)
    _req(all(bid in fp_ids for bid in w["boundary_obstacles"]), "Unresolved boundary_obstacles ref")
    roads = d["roads"]
    _req(isinstance(roads, dict) and roads.get("completeness") in {"COMPLETE", "PARTIAL", "UNKNOWN"}, "Invalid roads object")
    node_ids, seg_ids = set(), set()
    for n in roads.get("nodes", []):
        nid = n.get("id")
        _req(_ascii(nid) and nid not in node_ids and _num(n.get("x")) and _num(n.get("z")) and (n.get("y") is None or _num(n.get("y"))), f"Invalid road node {nid!r}")
        node_ids.add(nid)
    for s in roads.get("segments", []):
        sid, cl = s.get("id"), s.get("centerline")
        _req(_ascii(sid) and sid not in seg_ids and s.get("elevation_type") in VALID_ELEV and isinstance(cl, list) and len(cl) >= 2, f"Invalid road segment {sid!r}")
        _req(all(s.get(nk) is None or s[nk] in node_ids for nk in ("start_node_id", "end_node_id")), f"Segment {sid} unresolved node")
        _req(all(isinstance(pt, list) and len(pt) == 3 and _num(pt[0]) and _num(pt[2]) and (pt[1] is None or _num(pt[1])) for pt in cl), f"Segment {sid} invalid centerline")
        _req(all(cfid in fp_ids for cfid in s.get("corridor_footprint_ids", [])), f"Segment {sid} unresolved corridor_footprint_id")
        seg_ids.add(sid)
    for n in roads.get("nodes", []):
        _req(all(csid in seg_ids for csid in n.get("connected_segment_ids", [])), f"Node {n['id']} unresolved connected_segment_id")
    comp = d["completeness"]
    _req(isinstance(comp, dict) and all(k in comp and comp[k] in VALID_COMP for k in REQ_COMP), "Invalid completeness object")
    iss_ids = set()
    for iss in d["issues"]:
        iid = iss.get("id")
        _req(_ascii(iid) and iid not in iss_ids and iss.get("severity") in {"INFO", "WARNING", "BLOCKER"}, f"Invalid issue {iid!r}")
        if iss.get("affected_polygon") is not None: validate_polygon(iss["affected_polygon"], f"issue.{iid}.affected_polygon")
        iss_ids.add(iid)
    recomputed = compute_static_fingerprint(d)
    _req(meta["static_fingerprint"] == recomputed, f"static_fingerprint mismatch: dump={meta['static_fingerprint']} recomputed={recomputed}")
    return d


# -------------------- Height, slope & classification (§6) --------------------

def sample_height(grids: list[dict[str, Any]], region_id: str, x: float, z: float, opts: dict[str, Any] | None = None) -> tuple[float | None, str, float | None]:
    opts = opts or {}
    ordered = [g for g in grids if g["region_id"] == region_id] + [g for g in grids if g["region_id"] == "ROAD_CORRIDOR"] + [g for g in grids if g["region_id"] == "WORLD"]
    for g in ordered:
        step, nx, nz = g["step_m"], g["nx"], g["nz"]
        fx, fz = (x - g["origin_x"]) / step, (z - g["origin_z"]) / step
        if fx < -1e-9 or fz < -1e-9 or fx > nx - 1 + 1e-9 or fz > nz - 1 + 1e-9: continue
        is_1m = abs(step - 1.0) < 1e-6
        dtag = "DIRECT_RUNTIME_1M" if is_1m else "DIRECT_RUNTIME_20M"
        itag = dtag if opts.get("mislabel_interpolated") else ("INTERPOLATED_1M" if is_1m else "INTERPOLATED_20M")
        ixr, izr = round(fx), round(fz)
        if abs(fx - ixr) < 1e-9 and abs(fz - izr) < 1e-9:
            h = g["heights"][izr * nx + ixr]
            return (float(h), dtag, step) if h is not None else (None, "UNKNOWN", step)
        ix0, iz0 = max(0, min(nx - 2, math.floor(fx))), max(0, min(nz - 2, math.floor(fz)))
        tx, tz, hs = fx - ix0, fz - iz0, g["heights"]
        h00, h10, h01, h11 = hs[iz0 * nx + ix0], hs[iz0 * nx + ix0 + 1], hs[(iz0 + 1) * nx + ix0], hs[(iz0 + 1) * nx + ix0 + 1]
        if None in (h00, h10, h01, h11): return None, "UNKNOWN", step
        return float((1 - tx) * (1 - tz) * h00 + tx * (1 - tz) * h10 + (1 - tx) * tz * h01 + tx * tz * h11), itag, step
    return None, "UNKNOWN", None


def slope_class_from_pct(s: float | None) -> str:
    return "UNKNOWN" if s is None else ("S0" if s <= 5.0 else "S1" if s <= 10.0 else "S2" if s <= 20.0 else "S3" if s <= 30.0 else "S4")


def _cell_slope_1m(grid: dict[str, Any] | None, x0: float, z0: float, step_cell: float) -> tuple[float | None, bool]:
    if grid is None: return None, False
    step, nx, nz, hs = grid["step_m"], grid["nx"], grid["nz"], grid["heights"]
    ix0, ix1 = max(0, math.floor((x0 - grid["origin_x"]) / step)), min(nx - 1, math.ceil((x0 + step_cell - grid["origin_x"]) / step))
    iz0, iz1 = max(0, math.floor((z0 - grid["origin_z"]) / step)), min(nz - 1, math.ceil((z0 + step_cell - grid["origin_z"]) / step))
    if ix1 < ix0 or iz1 < iz0: return None, False
    max_s = 0.0
    for iz in range(iz0, iz1 + 1):
        row = iz * nx
        for ix in range(ix0, ix1 + 1):
            h = hs[row + ix]
            if h is None: return None, False
            hl, hr = (hs[row + ix - 1] if ix > 0 else None), (hs[row + ix + 1] if ix + 1 < nx else None)
            hd, hu = (hs[(iz - 1) * nx + ix] if iz > 0 else None), (hs[(iz + 1) * nx + ix] if iz + 1 < nz else None)
            gx = (hr - hl) / (2 * step) if (hl is not None and hr is not None) else ((hr - h) / step if hr is not None else ((h - hl) / step if hl is not None else None))
            gz = (hu - hd) / (2 * step) if (hd is not None and hu is not None) else ((hu - h) / step if hu is not None else ((h - hd) / step if hd is not None else None))
            if gx is None or gz is None: return None, False
            sp = math.hypot(gx, gz) * 100.0
            if sp > max_s: max_s = sp
    return max_s, True


def _fp_geom(fp: dict[str, Any]) -> tuple[list[list[float]], bool, tuple[float, float, float, float]]:
    if fp["polygon"] is not None:
        return fp["polygon"], is_axis_rect(fp["polygon"]), poly_bounds(fp["polygon"])
    x0, z0, x1, z1 = fp["bounds"]
    return [[x0, z0], [x1, z0], [x1, z1], [x0, z1]], True, (x0, z0, x1, z1)


def _classify_preset(d: dict[str, Any], opts: dict[str, Any]) -> dict[str, Any]:
    w, comp, pg = d["world"], d["completeness"], d["world"]["physical_ground"]
    pg_b, pg_ver = tuple(pg["bounds"]), pg["verification"] == "RUNTIME_VERIFIED"
    glob_inc = any(comp[k] in {"PARTIAL", "UNKNOWN"} for k in LAND_REQ_COMP) or comp["world_bounds"] == "UNKNOWN" or not pg_ver
    blockers = [i for i in d["issues"] if i["severity"] == "BLOCKER"]
    water_ps = [] if opts.get("ignore_water") else [(p, is_axis_rect(p), poly_bounds(p)) for p in w["water_regions"]]
    beach_ps = [(p, is_axis_rect(p), poly_bounds(p)) for p in w["beach_regions"]]
    t_regs = [(t["polygon"], float(t["margin_m"]), poly_bounds(t["polygon"])) for t in w["terrain_regions"]]
    fp_geoms = [(fp, *_fp_geom(fp)) for fp in d["footprints"]
                if not ((opts.get("ignore_buildings") and fp["category"] == "BUILDING") or (opts.get("ignore_site_a") and (fp["protected"] or fp["category"] == "SITE_A")) or (opts.get("ignore_roads") and fp["category"] in {"ROAD", "SIDEWALK"}) or (opts.get("ignore_water") and fp["category"] == "WATER"))]
    res = {}
    for reg in d["regions"]:
        rid, ip, sp = reg["id"], reg["initial_polygon"], reg["survey_polygon"]
        ir, sr, ib, sb = is_axis_rect(ip), is_axis_rect(sp), poly_bounds(ip), poly_bounds(sp)
        gx0, gz0 = math.floor(sb[0] / CELL_STEP) * CELL_STEP, math.floor(sb[1] / CELL_STEP) * CELL_STEP
        nx5, nz5 = max(1, math.ceil((sb[2] - gx0) / CELL_STEP)), max(1, math.ceil((sb[3] - gz0) / CELL_STEP))
        grid1m = next((g for g in d["height_grids"] if g["region_id"] == rid and abs(g["step_m"] - 1.0) < 1e-6), None)
        bins: dict[tuple[int, int], list[int]] = {}
        for idx, (_fp, _pts, _rect, b) in enumerate(fp_geoms):
            if b[2] < gx0 or b[0] > gx0 + nx5 * CELL_STEP or b[3] < gz0 or b[1] > gz0 + nz5 * CELL_STEP: continue
            for iz in range(max(0, math.floor((b[1] - gz0) / CELL_STEP)), min(nz5 - 1, math.floor((b[3] - gz0) / CELL_STEP)) + 1):
                for ix in range(max(0, math.floor((b[0] - gx0) / CELL_STEP)), min(nx5 - 1, math.floor((b[2] - gx0) / CELL_STEP)) + 1):
                    bins.setdefault((ix, iz), []).append(idx)
        blk_all = any((not i["affected_region_ids"] or rid in i["affected_region_ids"]) and i["affected_polygon"] is None for i in blockers)
        blk_ps = [(i["affected_polygon"], is_axis_rect(i["affected_polygon"]), poly_bounds(i["affected_polygon"]))
                  for i in blockers if i["affected_polygon"] is not None and (not i["affected_region_ids"] or rid in i["affected_region_ids"])]
        cells, init_c, surv_c = {}, {c: 0.0 for c in CLASSES}, {c: 0.0 for c in CLASSES}
        sl_a = {s: 0.0 for s in SLOPE_CLASSES}
        tz_a = {"FLAT_PHYSICAL_GROUND": 0.0, "TERRAIN_CORE": 0.0, "TERRAIN_MARGIN": 0.0, "OUTSIDE_PHYSICAL_GROUND": 0.0}
        pr_a, partial_n = {"EXACT_OUTLINE": 0.0, "CONSERVATIVE_AABB": 0.0}, 0
        for iz in range(nz5):
            z0, z1, zc = gz0 + iz * CELL_STEP, gz0 + (iz + 1) * CELL_STEP, gz0 + (iz + 0.5) * CELL_STEP
            for ix in range(nx5):
                x0, x1, xc = gx0 + ix * CELL_STEP, gx0 + (ix + 1) * CELL_STEP, gx0 + (ix + 0.5) * CELL_STEP
                sa = poly_rect_area(sp, sr, sb, x0, z0, x1, z1)
                if sa <= 1e-9: continue
                ia = poly_rect_area(ip, ir, ib, x0, z0, x1, z1)
                in_pg = pg_b[0] <= x0 + 1e-9 and x1 <= pg_b[2] + 1e-9 and pg_b[1] <= z0 + 1e-9 and z1 <= pg_b[3] + 1e-9
                tzone = "FLAT_PHYSICAL_GROUND" if in_pg else "OUTSIDE_PHYSICAL_GROUND"
                if in_pg:
                    for tp, tm, tb in t_regs:
                        if tb[0] - tm <= xc <= tb[2] + tm and tb[1] - tm <= zc <= tb[3] + tm:
                            dist = dist_point_to_poly(xc, zc, tp)
                            if dist == 0.0: tzone = "TERRAIN_CORE"; break
                            if dist <= tm + 1e-9: tzone = "TERRAIN_MARGIN"
                hc, hprov, hstep = sample_height(d["height_grids"], rid, xc, zc, opts)
                max_s, ok1m = _cell_slope_1m(grid1m, x0, z0, CELL_STEP)
                scls = slope_class_from_pct(max_s if ok1m else None)
                flags, reasons, has_ex, has_ab, is_part = set(), set(), False, False, False
                if glob_inc or blk_all or not ok1m or hc is None: flags.add("LX"); reasons.add("DATA_INCOMPLETE")
                if any(poly_rect_area(bp, br, bb, x0, z0, x1, z1) > 1e-9 for bp, br, bb in blk_ps): flags.add("LX"); reasons.add("BLOCKER_ISSUE")
                if not in_pg: flags.add("L3" if pg_ver else "LX"); reasons.add("OUTSIDE_PHYSICAL_GROUND")
                for wp, wr, wb in water_ps:
                    oa = poly_rect_area(wp, wr, wb, x0, z0, x1, z1)
                    if oa > 1e-9: flags.add("L5"); reasons.add("WATER"); is_part |= oa < sa - 1e-6
                for bp, br, bb in beach_ps:
                    oa = poly_rect_area(bp, br, bb, x0, z0, x1, z1)
                    if oa > 1e-9: flags.add("L3"); reasons.add("BEACH"); is_part |= oa < sa - 1e-6
                for fidx in bins.get((ix, iz), ()):
                    fp, pts, rect, b = fp_geoms[fidx]
                    hit, oa = fp_intersects_cell(pts, rect, b, x0, z0, x1, z1)
                    if not hit: continue
                    is_part |= oa < sa - 1e-6
                    has_ex |= fp["geometry_precision"] == "EXACT_OUTLINE"
                    has_ab |= fp["geometry_precision"] == "CONSERVATIVE_AABB"
                    cat = fp["category"]
                    if fp["protected"] or cat == "SITE_A": flags.add("L4"); reasons.add("SITE_A_PROTECTED")
                    elif fp["verification"] == "UNKNOWN": flags.add("LX"); reasons.add(f"UNVERIFIED_{cat}")
                    elif cat == "BUILDING": flags.add("L2"); reasons.add("BUILDING")
                    elif cat == "BEACH": flags.add("L3"); reasons.add("BEACH")
                    else: flags.add("L5"); reasons.add(cat)
                if scls == "S4": flags.add("L5"); reasons.add("SLOPE_S4")
                elif scls in {"S1", "S2", "S3"}: flags.add("L1"); reasons.add(f"SLOPE_{scls}")
                elif scls == "UNKNOWN": flags.add("LX"); reasons.add("SLOPE_UNKNOWN")
                primary = min(flags or {"L0"}, key=lambda c: PRIORITY[c])
                if opts.get("lx_to_l0") and primary == "LX": primary = "L0"
                if opts.get("double_count_overlaps"):
                    for fc in (flags or {"L0"}): surv_c[fc] += sa; init_c[fc] += ia
                else: surv_c[primary] += sa; init_c[primary] += ia
                sl_a[scls] += sa; tz_a[tzone] += sa; partial_n += int(is_part)
                if has_ex: pr_a["EXACT_OUTLINE"] += sa
                if has_ab: pr_a["CONSERVATIVE_AABB"] += sa
                cells[(round(x0 / CELL_STEP), round(z0 / CELL_STEP))] = {
                    "x0": x0, "z0": z0, "xc": xc, "zc": zc, "sa": sa, "ia": ia, "cls": primary,
                    "flags": sorted(flags or {"L0"}), "reasons": sorted(reasons), "h": hc, "h_prov": hprov,
                    "h_step": hstep, "slope_pct": max_s if ok1m else None, "slope_cls": scls, "tzone": tzone,
                }
        sa_tot, ia_tot = poly_area(sp), poly_area(ip)
        se, ie = abs(sum(surv_c.values()) - sa_tot), abs(sum(init_c.values()) - ia_tot)
        _req(opts.get("skip_conservation_assert") or (se <= CONSERVATION_TOL_M2 and ie <= CONSERVATION_TOL_M2), f"Area conservation failed in {rid}: survey_err={se:.3f}, init_err={ie:.3f}")
        res[rid] = {
            "id": rid, "name": reg["name"], "initial_polygon": ip, "survey_polygon": sp, "buffer_m": reg["buffer_m"],
            "initial_polygon_area_m2": round(ia_tot, 3), "survey_polygon_area_m2": round(sa_tot, 3),
            "initial_class_areas_m2": {c: round(init_c[c], 3) for c in CLASSES}, "survey_class_areas_m2": {c: round(surv_c[c], 3) for c in CLASSES},
            "slope_class_areas_m2": {s: round(sl_a[s], 3) for s in SLOPE_CLASSES}, "terrain_zone_areas_m2": {k: round(v, 3) for k, v in tz_a.items()},
            "precision_affected_areas_m2": {k: round(v, 3) for k, v in pr_a.items()}, "partial_cells_conservatively_excluded": partial_n,
            "conservation_error_m2": {"initial": round(ie, 6), "survey": round(se, 6)}, "cells": cells,
        }
    return res


def _union_summary(regs: list[dict[str, Any]], cmaps: dict[str, dict[tuple[int, int], dict[str, Any]]], opts: dict[str, Any]) -> dict[str, Any]:
    keys = sorted({gk for cm in cmaps.values() for gk in cm})
    ips, sps = [r["initial_polygon"] for r in regs], [r["survey_polygon"] for r in regs]
    ic, sc, ui, us = {c: 0.0 for c in CLASSES}, {c: 0.0 for c in CLASSES}, 0.0, 0.0
    for gk in keys:
        x0, z0 = gk[0] * CELL_STEP, gk[1] * CELL_STEP
        hits = [cm[gk] for cm in cmaps.values() if gk in cm]
        cls = min((h["cls"] for h in hits), key=lambda c: PRIORITY[c])
        sa = hits[0]["sa"] if len(hits) == 1 else polys_union_area_in_rect(sps, x0, z0, x0 + CELL_STEP, z0 + CELL_STEP)
        ia = hits[0]["ia"] if len(hits) == 1 else polys_union_area_in_rect(ips, x0, z0, x0 + CELL_STEP, z0 + CELL_STEP)
        us += sa; ui += ia
        if opts.get("double_count_overlaps"):
            sc[cls] += sum(h["sa"] for h in hits); ic[cls] += sum(h["ia"] for h in hits)
        else: sc[cls] += sa; ic[cls] += ia
    se, ie = abs(sum(sc.values()) - us), abs(sum(ic.values()) - ui)
    _req(opts.get("skip_conservation_assert") or (se <= CONSERVATION_TOL_M2 and ie <= CONSERVATION_TOL_M2), f"Union conservation failed: se={se:.3f}, ie={ie:.3f}")
    return {"initial_union_area_m2": round(ui, 3), "survey_union_area_m2": round(us, 3),
            "initial_class_areas_m2": {c: round(ic[c], 3) for c in CLASSES}, "survey_class_areas_m2": {c: round(sc[c], 3) for c in CLASSES},
            "conservation_error_m2": {"initial": round(ie, 6), "survey": round(se, 6)}}


# -------------------- SVG & Markdown deliverables (§12.2, §12.4) --------------------

def _build_svg(inv: dict[str, Any], cells: dict[str, dict[tuple[int, int], dict[str, Any]]], dumps: list[dict[str, Any]]) -> str:
    cols = {"L0": "#4ade80", "L1": "#facc15", "L2": "#fb923c", "L3": "#38bdf8", "L4": "#ef4444", "L5": "#64748b", "LX": "#c084fc"}
    regs, pw, ph, pad, hh, lh = inv["regions"], 340, 340, 28, 72, 92
    tw, th = max(760, len(regs) * (pw + pad) + pad), hh + ph + lh + 24
    fps_txt = ", ".join(f"{p['preset']}:{p['static_fingerprint'][:12]}" for p in inv["presets"])
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{tw}" height="{th}" viewBox="0 0 {tw} {th}" font-family="monospace" font-size="11">',
        '<defs>' + "".join(f'<clipPath id="clip-{escape(r["id"])}"><rect x="{pad + i * (pw + pad)}" y="{hh}" width="{pw}" height="{ph}"/></clipPath>' for i, r in enumerate(regs)) + '</defs>',
        f'<rect width="{tw}" height="{th}" fill="#0f172a"/>',
        f'<text x="16" y="22" fill="#f8fafc" font-size="14" font-weight="bold">WE-01A Land Survey (AUDIT DATA — RUNTIME DUMP) | {escape(inv["mode"])}</text>',
        f'<text x="16" y="40" fill="#cbd5e1">BASE: {escape(inv["base_sha"])} | Fingerprints: {escape(fps_txt)}</text>',
        '<text x="16" y="56" fill="#94a3b8">Grid: 5m classification over 1m runtime terrain | Existing roads solid amber; Site A red dashed; LX purple</text>',
    ]
    w_polys = dumps[0]["world"]["water_regions"]
    sa_fps = {f["id"]: f for d in dumps for f in d["footprints"] if f["protected"] or f["category"] == "SITE_A"}
    r_segs = {s["id"]: s for d in dumps for s in d["roads"]["segments"]}
    for i, reg in enumerate(regs):
        rid, ox, oy = reg["id"], pad + i * (pw + pad), hh
        sb = poly_bounds(reg["survey_polygon"])
        span = max(sb[2] - sb[0], sb[3] - sb[1], 1.0)
        sc = (pw - 52) / span
        mx, mz = (lambda x: ox + 36 + (x - sb[0]) * sc), (lambda z: oy + 16 + (z - sb[1]) * sc)
        out.append(f'<g id="panel-{escape(rid)}"><rect x="{ox}" y="{oy}" width="{pw}" height="{ph}" fill="#1e293b" stroke="#334155"/>')
        out.append(f'<text x="{ox + 8}" y="{oy + 12}" fill="#e2e8f0" font-weight="bold">{escape(rid)} — {escape(reg["name"])}</text>')
        rows: dict[int, list[tuple[int, str]]] = {}
        for (gx, gz), c in cells[rid].items(): rows.setdefault(gz, []).append((gx, c["cls"]))
        cp = CELL_STEP * sc
        for gz, items in sorted(rows.items()):
            items.sort(); k = 0
            while k < len(items):
                j = k + 1
                while j < len(items) and items[j][0] == items[j - 1][0] + 1 and items[j][1] == items[k][1]: j += 1
                out.append(f'<rect x="{mx(items[k][0]*CELL_STEP):.1f}" y="{mz(gz*CELL_STEP):.1f}" width="{(j-k)*cp:.1f}" height="{cp:.1f}" fill="{cols[items[k][1]]}" fill-opacity="0.82"/>')
                k = j
        for wp in w_polys:
            if (c := clip_poly_to_rect(wp, *sb)): out.append(f'<polygon points="{" ".join(f"{mx(p[0]):.1f},{mz(p[1]):.1f}" for p in c)}" fill="#0284c7" fill-opacity="0.30" stroke="#38bdf8"/>')
        for seg in sorted(r_segs.values(), key=lambda s: s["id"]):
            out.append(f'<polyline points="{" ".join(f"{mx(p[0]):.1f},{mz(p[2]):.1f}" for p in seg["centerline"])}" fill="none" stroke="#f59e0b" stroke-width="2" clip-path="url(#clip-{escape(rid)})"/>')
        for fp in sorted(sa_fps.values(), key=lambda f: f["id"]):
            if (c := clip_poly_to_rect(_fp_geom(fp)[0], *sb)): out.append(f'<polygon points="{" ".join(f"{mx(p[0]):.1f},{mz(p[1]):.1f}" for p in c)}" fill="none" stroke="#fecaca" stroke-width="2" stroke-dasharray="4,2"/>')
        for poly, st, da in ((reg["survey_polygon"], "#94a3b8", ' stroke-dasharray="4,3"'), (reg["initial_polygon"], "#ffffff", "")):
            out.append(f'<polygon points="{" ".join(f"{mx(p[0]):.1f},{mz(p[1]):.1f}" for p in poly)}" fill="none" stroke="{st}" stroke-width="1.5"{da}/>')
        ay, bar_m = oy + ph - 22, (100.0 if span >= 200 else 20.0)
        out.append(f'<line x1="{ox+36}" y1="{ay}" x2="{ox+pw-16}" y2="{ay}" stroke="#cbd5e1"/><line x1="{ox+36}" y1="{oy+16}" x2="{ox+36}" y2="{ay}" stroke="#cbd5e1"/>')
        out.append(f'<text x="{ox+36}" y="{ay+14}" fill="#cbd5e1">X={sb[0]:.0f}m</text><text x="{ox+pw-74}" y="{ay+14}" fill="#cbd5e1">X={sb[2]:.0f}m</text>')
        out.append(f'<text x="{ox+4}" y="{oy+28}" fill="#cbd5e1">Z={sb[1]:.0f}</text><text x="{ox+4}" y="{ay-4}" fill="#cbd5e1">Z={sb[3]:.0f}</text>')
        out.append(f'<line x1="{ox+pw-20-bar_m*sc:.1f}" y1="{oy+12}" x2="{ox+pw-20:.1f}" y2="{oy+12}" stroke="#f8fafc" stroke-width="2"/><text x="{ox+pw-20-bar_m*sc:.1f}" y="{oy+24}" fill="#f8fafc">{bar_m:.0f}m scale</text></g>')
    ly, lx = hh + ph + 18, 16
    out.append(f'<g id="legend"><text x="16" y="{ly}" fill="#f8fafc" font-weight="bold">Legend (Audit Data — L4 &gt; L5 &gt; LX &gt; L2 &gt; L3 &gt; L1 &gt; L0):</text>')
    for code, txt in (("L0", "L0 Direct"), ("L1", "L1 Slope S1-S3"), ("L2", "L2 Building"), ("L3", "L3 Beach/Expand"), ("L4", "L4 Site A Protected"), ("L5", "L5 Water/Road/Obs"), ("LX", "LX / UNKNOWN")):
        out.append(f'<rect x="{lx}" y="{ly+10}" width="12" height="12" fill="{cols[code]}"/><text x="{lx+16}" y="{ly+20}" fill="#e2e8f0">{escape(txt)}</text>')
        lx += 135 if code == "L4" else 108
    out.append(f'<line x1="16" y1="{ly+42}" x2="40" y2="{ly+42}" stroke="#f59e0b" stroke-width="2"/><text x="46" y="{ly+46}" fill="#e2e8f0">Existing Road (solid) | Candidate Roads: WE-01B | Solid white: initial | Dashed: +100m buffer</text></g></svg>')
    return "\n".join(out) + "\n"


def _build_report_md(inv: dict[str, Any], diff: dict[str, Any]) -> str:
    lines = ["# WE-01A Land Classification & Runtime Dump Analysis Report", "",
             f"- **Analyzer**: `{inv['analyzer_version']}` | **BASE**: `{inv['base_sha']}` | **Mode**: `{inv['mode']}`",
             f"- **Grid**: `{inv['grid_step_m']}m` (`{inv['partial_cell_policy']}`), tolerance `<= {inv['conservation_tolerance_m2']} m²`",
             *[f"- **Preset `{p['preset']}`**: `static_fingerprint={p['static_fingerprint']}`, `file_sha256={p['file_sha256']}`" for p in inv["presets"]],
             "", "## Land Classification Summary (Common Conservative, m²)", "",
             "| Region | Scope | Gross | L0 | L1 | L2 | L3 | L4 | L5 | LX | Err |", "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in inv["regions"]:
        for sc, gk, ck, ek in (("Initial", "initial_polygon_area_m2", "common_initial_class_areas_m2", "initial"), ("Survey", "survey_polygon_area_m2", "common_survey_class_areas_m2", "survey")):
            ca = r[ck]
            lines.append(f"| {r['id']} | {sc} | {r[gk]:.1f} | {ca['L0']:.1f} | {ca['L1']:.1f} | {ca['L2']:.1f} | {ca['L3']:.1f} | {ca['L4']:.1f} | {ca['L5']:.1f} | {ca['LX']:.1f} | {r['common_conservation_error_m2'][ek]:.4f} |")
    us = inv["union_summary"]["common"]
    for sc, gk, ck, ek in (("Initial", "initial_union_area_m2", "initial_class_areas_m2", "initial"), ("Survey", "survey_union_area_m2", "survey_class_areas_m2", "survey")):
        ca = us[ck]
        lines.append(f"| **UNION** | {sc} | {us[gk]:.1f} | {ca['L0']:.1f} | {ca['L1']:.1f} | {ca['L2']:.1f} | {ca['L3']:.1f} | {ca['L4']:.1f} | {ca['L5']:.1f} | {ca['LX']:.1f} | {us['conservation_error_m2'][ek]:.4f} |")
    lines += ["", "## Terrain Zones, Precision & Revised Search Suggestions", ""]
    for r in inv["regions"]:
        tz, pr = r["terrain_zone_areas_m2"], r["precision_affected_areas_m2"]
        lines.append(f"- **{r['id']}**: flat=`{tz['FLAT_PHYSICAL_GROUND']:.1f}`, core=`{tz['TERRAIN_CORE']:.1f}`, margin=`{tz['TERRAIN_MARGIN']:.1f}`, outside_pg=`{tz['OUTSIDE_PHYSICAL_GROUND']:.1f}`; `EXACT_OUTLINE`=`{pr['EXACT_OUTLINE']:.1f}`, `CONSERVATIVE_AABB`=`{pr['CONSERVATIVE_AABB']:.1f}`; revised L0 bounds=`{r['revised_search_bounds']}`.")
    lines += ["", "## Known Data Gaps & WE-01B Handoff", *[f"- {g}" for g in inv["data_gaps"]],
              f"- Cross-preset rule (`{diff['mode']}`): obstacles = union, usable L0 = intersection; SCENE_BOX3 is conservative and inflates obstacles.",
              "- Deferred to WE-01B: 1m prefix sums, parcel placement, candidate road curves, and final feasibility verdicts."]
    return "\n".join(lines) + "\n"


def analyze_dumps(dump_paths: list[Path], out_dir: Path | None = None, opts: dict[str, Any] | None = None) -> dict[str, Any]:
    opts = opts or {}
    _req(bool(dump_paths), "At least one --dump path is required")
    dumps, metas, seen, base_sha = [], [], set(), None
    for p in dump_paths:
        raw = Path(p).read_bytes()
        d = validate_dump(json.loads(raw.decode("utf-8")), opts)
        pr = d["metadata"]["preset"]
        _req(pr not in seen, f"Duplicate preset dump: {pr}"); seen.add(pr)
        base_sha = base_sha or d["metadata"]["base_sha"]
        _req(d["metadata"]["base_sha"] == base_sha, f"BASE SHA mismatch: {base_sha} vs {d['metadata']['base_sha']}")
        dumps.append(d)
        metas.append({"preset": pr, "file_sha256": hashlib.sha256(raw).hexdigest(), "static_fingerprint": d["metadata"]["static_fingerprint"],
                      "game_release": d["metadata"]["game_release"], "extraction_version": d["metadata"]["extraction_version"],
                      "source_counts": d["metadata"]["source_counts"], "completeness": d["completeness"]})
    paired = sorted(zip(dumps, metas), key=lambda x: x[1]["preset"])
    dumps, metas = [x[0] for x in paired], [x[1] for x in paired]
    ref_regs = dumps[0]["regions"]
    sig = [(r["id"], r["initial_polygon"], r["survey_polygon"]) for r in ref_regs]
    _req(all([(r["id"], r["initial_polygon"], r["survey_polygon"]) for r in d["regions"]] == sig for d in dumps[1:]), "Region definitions differ across presets")

    per_p = {d["metadata"]["preset"]: _classify_preset(d, opts) for d in dumps}
    pnames = [m["preset"] for m in metas]
    use_p = ["PHONE_LOW"] if (opts.get("phone_low_only") and "PHONE_LOW" in per_p) else pnames
    common_cells, regs_out = {}, []
    for reg in ref_regs:
        rid = reg["id"]
        ci, cs, cmap, l0x, l0z = {c: 0.0 for c in CLASSES}, {c: 0.0 for c in CLASSES}, {}, [], []
        for gk, c0 in per_p[use_p[0]][rid]["cells"].items():
            hits = [per_p[pn][rid]["cells"][gk] for pn in use_p]
            cls = min((h["cls"] for h in hits), key=lambda c: PRIORITY[c])
            cs[cls] += c0["sa"]; ci[cls] += c0["ia"]
            if cls == "L0": l0x.extend((c0["x0"], c0["x0"] + CELL_STEP)); l0z.extend((c0["z0"], c0["z0"] + CELL_STEP))
            cmap[gk] = {**c0, "cls": cls, "flags": sorted({f for h in hits for f in h["flags"]}), "reasons": sorted({r for h in hits for r in h["reasons"]})}
        common_cells[rid] = cmap
        se, ie = abs(sum(cs.values()) - poly_area(reg["survey_polygon"])), abs(sum(ci.values()) - poly_area(reg["initial_polygon"]))
        _req(opts.get("skip_conservation_assert") or (se <= CONSERVATION_TOL_M2 and ie <= CONSERVATION_TOL_M2), f"Common conservation failed in {rid}: se={se:.3f}, ie={ie:.3f}")
        rr = per_p[use_p[0]][rid]
        regs_out.append({
            "id": rid, "name": reg["name"], "initial_polygon": reg["initial_polygon"], "survey_polygon": reg["survey_polygon"], "buffer_m": reg["buffer_m"],
            "initial_polygon_area_m2": rr["initial_polygon_area_m2"], "survey_polygon_area_m2": rr["survey_polygon_area_m2"],
            "common_initial_class_areas_m2": {c: round(ci[c], 3) for c in CLASSES}, "common_survey_class_areas_m2": {c: round(cs[c], 3) for c in CLASSES},
            "common_conservation_error_m2": {"initial": round(ie, 6), "survey": round(se, 6)},
            "per_preset": {pn: {k: v for k, v in per_p[pn][rid].items() if k != "cells"} for pn in pnames},
            "slope_class_areas_m2": rr["slope_class_areas_m2"], "terrain_zone_areas_m2": rr["terrain_zone_areas_m2"],
            "precision_affected_areas_m2": {k: round(max(per_p[pn][rid]["precision_affected_areas_m2"][k] for pn in use_p), 3) for k in ("EXACT_OUTLINE", "CONSERVATIVE_AABB")},
            "revised_search_bounds": [min(l0x), min(l0z), max(l0x), max(l0z)] if l0x else None,
        })
    usum = {"common": _union_summary(ref_regs, common_cells, opts), "per_preset": {pn: _union_summary(ref_regs, {r["id"]: per_p[pn][r["id"]]["cells"] for r in ref_regs}, opts) for pn in pnames}}
    fpsum = {}
    for d in dumps:
        pn, bc, bg, bp = d["metadata"]["preset"], {}, {}, {}
        for fp in d["footprints"]:
            bc[fp["category"]] = bc.get(fp["category"], 0) + 1; bg[fp["source_group"]] = bg.get(fp["source_group"], 0) + 1; bp[fp["geometry_precision"]] = bp.get(fp["geometry_precision"], 0) + 1
        fpsum[pn] = {"total": len(d["footprints"]), "by_category": dict(sorted(bc.items())), "by_source_group": dict(sorted(bg.items())), "by_precision": dict(sorted(bp.items()))}
    gaps = sorted({f"[{d['metadata']['preset']}] completeness.{k}={v}" for d in dumps for k, v in d["completeness"].items() if v != "COMPLETE"} | {f"[{d['metadata']['preset']}] issue.{i['id']}({i['severity']}): {i['message']}" for d in dumps for i in d["issues"]})
    inv = {"schema_version": 1, "analyzer_version": ANALYZER_VERSION, "base_sha": base_sha, "mode": "CROSS_PRESET_COMMON" if len(dumps) > 1 else "SINGLE_PRESET",
           "grid_step_m": CELL_STEP, "conservation_tolerance_m2": CONSERVATION_TOL_M2, "partial_cell_policy": "CONSERVATIVE_WHOLE_CELL_EXCLUSION",
           "presets": metas, "regions": regs_out, "union_summary": usum, "footprint_summary": fpsum, "data_gaps": gaps}
    if len(dumps) >= 2:
        d0, d1, p0, p1 = dumps[0], dumps[1], pnames[0], pnames[1]
        sck = sorted(set(d0["metadata"]["source_counts"]) | set(d1["metadata"]["source_counts"]))
        sc_diff = {k: {p0: d0["metadata"]["source_counts"].get(k), p1: d1["metadata"]["source_counts"].get(k),
                       "delta": (d1["metadata"]["source_counts"][k] - d0["metadata"]["source_counts"][k]) if (d0["metadata"]["source_counts"].get(k) is not None and d1["metadata"]["source_counts"].get(k) is not None) else None} for k in sck}
        i0, i1, g0, hdiff = {f["id"] for f in d0["footprints"]}, {f["id"] for f in d1["footprints"]}, {g["id"]: g for g in d0["height_grids"]}, {}
        for g in d1["height_grids"]:
            if g["id"] in g0 and len(g["heights"]) == len(g0[g["id"]]["heights"]):
                df = [abs(a - b) for a, b in zip(g0[g["id"]]["heights"], g["heights"]) if a is not None and b is not None]
                hdiff[g["id"]] = {"max_abs_diff_m": round(max(df), 6) if df else 0.0, "differing_points": sum(1 for v in df if v > 1e-6)}
        pdiff = {"mode": "CROSS_PRESET_DIFF", "base_sha": base_sha, "presets": pnames, "source_counts": sc_diff,
                 "footprint_diff": {f"only_in_{p0}_count": len(i0 - i1), f"only_in_{p1}_count": len(i1 - i0), "shared_count": len(i0 & i1), "by_source_group": {pn: fpsum[pn]["by_source_group"] for pn in pnames}},
                 "land_class_diff_by_region": {r["id"]: {"common_survey": r["common_survey_class_areas_m2"], "common_initial": r["common_initial_class_areas_m2"], **{pn: r["per_preset"][pn]["survey_class_areas_m2"] for pn in pnames}} for r in regs_out},
                 "height_diff": hdiff, "common_constraints": {"rule": "obstacles = union; usable L0 = intersection", "common_initial_L0_m2": usum["common"]["initial_class_areas_m2"]["L0"], "common_survey_L0_m2": usum["common"]["survey_class_areas_m2"]["L0"]}}
    else:
        pdiff = {"mode": "SINGLE_PRESET", "base_sha": base_sha, "presets": pnames, "source_counts": dumps[0]["metadata"]["source_counts"],
                 "common_constraints": {"rule": "single preset analyzed", "common_initial_L0_m2": usum["common"]["initial_class_areas_m2"]["L0"], "common_survey_L0_m2": usum["common"]["survey_class_areas_m2"]["L0"]}}
    if out_dir is not None:
        out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "land_inventory.json").write_text(json.dumps(inv, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        (out_dir / "preset_diff.json").write_text(json.dumps(pdiff, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        with (out_dir / "terrain_survey.csv").open("w", encoding="utf-8", newline="") as fh:
            wr = csv.writer(fh, lineterminator="\n")
            wr.writerow(["region_id", "x", "z", "height_m", "slope_pct", "slope_class", "step_m", "sample_method", "land_class", "terrain_zone"])
            for reg in ref_regs:
                rid = reg["id"]
                for (_gx, _gz), c in sorted(common_cells[rid].items(), key=lambda kv: (kv[1]["zc"], kv[1]["xc"])):
                    wr.writerow([rid, f"{c['xc']:.3f}", f"{c['zc']:.3f}", "" if c["h"] is None else f"{c['h']:.3f}", "" if c["slope_pct"] is None else f"{c['slope_pct']:.3f}", c["slope_cls"], "" if c["h_step"] is None else f"{c['h_step']:.0f}", c["h_prov"], c["cls"], c["tzone"]])
        (out_dir / "land_survey.svg").write_text(_build_svg(inv, common_cells, dumps), encoding="utf-8")
        (out_dir / "land_report.md").write_text(_build_report_md(inv, pdiff), encoding="utf-8")
    return {"inventory": inv, "preset_diff": pdiff, "common_cells": common_cells}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="WE-01A (T-016A): Read-only runtime dump analyzer and land classifier.")
    ap.add_argument("--dump", action="append", required=True, type=Path, help="Path to schema-v1 dump JSON (repeatable).")
    ap.add_argument("--out", required=True, type=Path, help="Output directory for deliverables.")
    args = ap.parse_args(argv)
    try:
        res = analyze_dumps(args.dump, args.out)
    except (ValidationError, OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    us = res["inventory"]["union_summary"]["common"]
    print(f"OK [{res['inventory']['mode']}] BASE={res['inventory']['base_sha'][:8]} init_L0={us['initial_class_areas_m2']['L0']:.1f}m2 survey_L0={us['survey_class_areas_m2']['L0']:.1f}m2 out={args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
