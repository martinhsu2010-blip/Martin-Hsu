#!/usr/bin/env python3
"""WE-01B (T-016B) Parcel Capacity Analyzer — read-only offline audit tooling."""
from __future__ import annotations

import argparse
from array import array
from collections import deque
import hashlib
from itertools import accumulate
import json
import math
from operator import add
from pathlib import Path
import sys
from typing import Any, Callable

sys.path.insert(0, str(Path(__file__).resolve().parent))
from we01a_land_analyzer import (  # noqa: E402
    clip_poly_to_rect, compute_static_fingerprint, fp_intersects_cell,
    is_axis_rect, poly_area, poly_bounds, sample_height, slope_class_from_pct, validate_dump,
)

ANALYZER_VERSION = "we01b-1.0"
HANDOFF_SCHEMA_VERSION = 1
POLYGON_REVISION = 2
WE01A_COMPAT_VERSION = "we01a-1.0"
C_CONDITIONAL_STATUS = "PENDING_T016D"
ACCESS_MAX_GAP_M, ACCESS_MIN_CONTACT_M, CONSERVATION_TOL_M2 = 2.0, 8.0, 1.0
LAND_REQ_COMP = (
    "terrain_heights", "physical_ground", "terrain_regions", "visual_occupancy",
    "physical_occupancy", "trees", "water_and_beach", "protected_areas", "roads",
)
SCENARIOS: dict[str, dict[str, list[int]]] = {
    "INITIAL": {"B1": [90, 390, 930, 1230], "B2": [-900, -500, 820, 1070], "B3": [-640, -340, -810, -610]},
    "ENVELOPE": {"B1": [-10, 490, 830, 1330], "B2": [-1000, -400, 720, 1170], "B3": [-740, -240, -910, -510]},
    "REVISED": {"B1": [-10, 390, 880, 1330], "B2": [-950, -450, 770, 1120], "B3": [-640, -240, -860, -710]},
}
OBSOLETE_REVISED_V1 = {"B1": [-10, 390, 830, 1180], "B2": [-950, -450, 770, 1070], "B3": [-740, -290, -810, -560]}
PROTOTYPES: dict[str, dict[str, Any]] = {
    "R01": {"id": "R01", "name": "Urban Residence", "footprint": (32, 24), "parcel": (42, 34), "area_m2": 1428, "buildings": 1, "units": 1, "proxy": False},
    "R02": {"id": "R02", "name": "Skyline Residence", "footprint": (36, 30), "parcel": (48, 42), "area_m2": 2016, "buildings": 1, "units": 1, "proxy": False},
    "R05": {"id": "R05", "name": "Detached House", "footprint": (14, 12), "parcel": (24, 22), "area_m2": 528, "buildings": 1, "units": 1, "proxy": True},
    "R08": {"id": "R08", "name": "Four-unit Terrace Homes", "footprint": (28, 14), "parcel": (38, 24), "area_m2": 912, "buildings": 1, "units": 4, "proxy": False},
}
REGION_RULES: dict[str, dict[str, Any]] = {
    "B1": {"prototypes": ("R02", "R01"), "min": 10, "ideal": 14, "proxy": False},
    "B2": {"prototypes": ("R05",), "min": 12, "ideal": 18, "proxy": True},
    "B3": {"prototypes": ("R01", "R05", "R08"), "min": 18, "ideal": 28, "proxy": False},
}
SIDES = ("SOUTH", "NORTH", "WEST", "EAST")


class CapacityError(ValueError):
    """Raised on validation, linkage, scenario, or conservation errors."""


class ValidMask(bytearray):
    """Compact bytearray of 1 m geom_valid flags with parcel/grid metadata."""

    def __init__(self, size: int, x0: int, z0: int, w: int, h: int, pw: int, ph: int, proto_id: str, orientation: int):
        super().__init__(size)
        self.x0, self.z0, self.w, self.h = x0, z0, w, h
        self.pw, self.ph, self.proto_id, self.orientation = pw, ph, proto_id, orientation


def _req(cond: bool, msg: str) -> None:
    if not cond:
        raise CapacityError(msg)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def spec_to_internal(b: list[float] | tuple[float, float, float, float]) -> list[float]:
    _req(len(b) == 4 and b[0] < b[1] and b[2] < b[3], f"Invalid spec-order bounds: {b}")
    return [b[0], b[2], b[1], b[3]]


def internal_to_spec(b: list[float] | tuple[float, float, float, float]) -> list[float]:
    _req(len(b) == 4 and b[0] < b[2] and b[1] < b[3], f"Invalid internal-order bounds: {b}")
    return [b[0], b[2], b[1], b[3]]


def validate_scenarios(scenarios: dict[str, dict[str, list[int]]], opts: dict[str, Any] | None = None) -> None:
    opts = opts or {}
    if opts.get("allow_custom_scenarios"):
        return
    _req(set(scenarios.keys()) == {"INITIAL", "ENVELOPE", "REVISED"}, f"Unexpected scenarios: {sorted(scenarios)}")
    for sid, expected_regs in SCENARIOS.items():
        _req(set(scenarios[sid].keys()) == {"B1", "B2", "B3"}, f"Missing regions in {sid}")
        for rid, exp in expected_regs.items():
            got = list(scenarios[sid][rid])
            if sid == "REVISED" and got == OBSOLETE_REVISED_V1[rid]:
                _req(bool(opts.get("accept_revised_v1")), f"Obsolete v1.3 REVISED coordinates rejected for {rid}")
            if not opts.get("accept_revised_v1"):
                _req(got == exp, f"Frozen scenario {sid}.{rid} mismatch: {got} != {exp}")
            spec_to_internal(got)
    for sid in ("INITIAL", "REVISED"):
        for rid in ("B1", "B2", "B3"):
            x0, z0, x1, z1 = spec_to_internal(scenarios[sid][rid])
            ex0, ez0, ex1, ez1 = spec_to_internal(scenarios["ENVELOPE"][rid])
            _req(x0 >= ex0 and x1 <= ex1 and z0 >= ez0 and z1 <= ez1, f"{sid}.{rid} outside ENVELOPE")


def load_dumps(
    paths: list[str | Path], land_inventory_path: str | Path | None = None,
    land_report_path: str | Path | None = None, opts: dict[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    opts = opts or {}
    _req(len(paths) >= 1, "At least one dump path is required")
    dumps: dict[str, dict[str, Any]] = {}
    base_sha: str | None = None
    for p in paths:
        fp = Path(p)
        raw = fp.read_bytes()
        d = json.loads(raw.decode("utf-8"))
        try:
            validate_dump(d)
        except Exception as exc:
            raise CapacityError(f"Dump validation failed ({fp.name}): {exc}") from exc
        preset = d["metadata"]["preset"]
        _req(preset not in dumps, f"Duplicate preset {preset}")
        base_sha = d["metadata"]["base_sha"] if base_sha is None else base_sha
        _req(d["metadata"]["base_sha"] == base_sha, "BASE SHA mismatch across dumps")
        d["_file_sha256"] = _sha256_bytes(raw)
        dumps[preset] = d
    if not opts.get("allow_single_preset"):
        _req(set(dumps.keys()) == {"PHONE_LOW", "DESKTOP_HIGH"}, f"Required PHONE_LOW & DESKTOP_HIGH, got {sorted(dumps)}")
    exp_h = opts.get("expected_artifact_hashes") or {}
    if land_inventory_path is not None:
        raw = Path(land_inventory_path).read_bytes()
        if "land_inventory" in exp_h:
            _req(_sha256_bytes(raw) == exp_h["land_inventory"], "Declared land_inventory SHA-256 mismatch")
        if not opts.get("skip_land_linkage_check"):
            inv = json.loads(raw.decode("utf-8"))
            _req(inv.get("base_sha") == base_sha and inv.get("analyzer_version") == WE01A_COMPAT_VERSION and inv.get("schema_version") == 1, "land_inventory compatibility mismatch")
            inv_ps = inv.get("presets") or {}
            by_pn = {p["preset"]: p for p in inv_ps if isinstance(p, dict) and "preset" in p} if isinstance(inv_ps, list) else inv_ps
            for pn, d in dumps.items():
                _req((by_pn.get(pn) or {}).get("static_fingerprint") == d["metadata"]["static_fingerprint"], f"land_inventory fingerprint mismatch ({pn})")
    if land_report_path is not None:
        raw = Path(land_report_path).read_bytes()
        if "land_report" in exp_h:
            _req(_sha256_bytes(raw) == exp_h["land_report"], "Declared land_report SHA-256 mismatch")
        if not opts.get("skip_land_linkage_check"):
            txt = raw.decode("utf-8")
            _req(base_sha in txt and all(d["metadata"]["static_fingerprint"] in txt for d in dumps.values()), "land_report BASE/fingerprint mismatch")
    return dumps


# --- Road graph & corridors ---

def _pt_seg_dist2(px: float, pz: float, ax: float, az: float, bx: float, bz: float) -> float:
    dx, dz = bx - ax, bz - az
    l2 = dx * dx + dz * dz
    if l2 <= 1e-18:
        return (px - ax) ** 2 + (pz - az) ** 2
    t = max(0.0, min(1.0, ((px - ax) * dx + (pz - az) * dz) / l2))
    return (px - (ax + t * dx)) ** 2 + (pz - (az + t * dz)) ** 2


def _seg_intersect_xz(a: list[float], b: list[float], c: list[float], d: list[float]) -> bool:
    ax, az, bx, bz, cx, cz, dx, dz = a[0], a[2], b[0], b[2], c[0], c[2], d[0], d[2]
    eps = 1e-9
    if max(ax, bx) < min(cx, dx) - eps or max(cx, dx) < min(ax, bx) - eps or max(az, bz) < min(cz, dz) - eps or max(cz, dz) < min(az, bz) - eps:
        return False
    ccw = lambda x0, z0, x1, z1, x2, z2: (x1 - x0) * (z2 - z0) - (z1 - z0) * (x2 - x0)
    o1, o2, o3, o4 = ccw(ax, az, bx, bz, cx, cz), ccw(ax, az, bx, bz, dx, dz), ccw(cx, cz, dx, dz, ax, az), ccw(cx, cz, dx, dz, bx, bz)
    if (o1 * o2 < -1e-12) and (o3 * o4 < -1e-12):
        return True
    on = lambda x0, z0, x1, z1, px, pz: min(x0, x1) - eps <= px <= max(x0, x1) + eps and min(z0, z1) - eps <= pz <= max(z0, z1) + eps
    return (abs(o1) <= eps and on(ax, az, bx, bz, cx, cz)) or (abs(o2) <= eps and on(ax, az, bx, bz, dx, dz)) or (abs(o3) <= eps and on(cx, cz, dx, dz, ax, az)) or (abs(o4) <= eps and on(cx, cz, dx, dz, bx, bz))


def _pt_polyline_dist_xz(px: float, pz: float, cl: list[list[float]]) -> float:
    return math.sqrt(min(_pt_seg_dist2(px, pz, cl[i][0], cl[i][2], cl[i + 1][0], cl[i + 1][2]) for i in range(len(cl) - 1)))


def _pt_poly_dist(px: float, pz: float, pts: list[list[float]]) -> float:
    inside, n, best = False, len(pts), float("inf")
    for i in range(n):
        ax, az = pts[i]
        bx, bz = pts[(i + 1) % n]
        if ((az > pz) != (bz > pz)) and (px < (bx - ax) * (pz - az) / (bz - az) + ax):
            inside = not inside
        d2 = _pt_seg_dist2(px, pz, ax, az, bx, bz)
        if d2 < best:
            best = d2
    return 0.0 if inside else math.sqrt(best)


def _is_roundabout_fp(fp: dict[str, Any]) -> bool:
    sg, fid, cat = str(fp.get("source_group") or ""), str(fp.get("id") or ""), str(fp.get("category") or "")
    return bool(fp.get("is_roundabout")) or "roundabout" in sg.lower() or fid.startswith("RBT_") or cat == "ROUNDABOUT"


def _fp_geom(fp: dict[str, Any]) -> tuple[list[list[float]], bool, tuple[float, float, float, float]]:
    if fp.get("polygon") is not None:
        return fp["polygon"], is_axis_rect(fp["polygon"]), poly_bounds(fp["polygon"])
    x0, z0, x1, z1 = fp["bounds"]
    return [[x0, z0], [x1, z0], [x1, z1], [x0, z1]], True, (x0, z0, x1, z1)


def build_road_graph(dump: dict[str, Any], opts: dict[str, Any] | None = None) -> dict[str, Any]:
    opts = opts or {}
    raw_segs = sorted((dump.get("roads") or {}).get("segments", []), key=lambda s: s["id"])
    alias_map, duplicates, reps, key_to_rep = {}, {}, {}, {}
    for seg in raw_segs:
        pts = tuple((round(p[0] * 1000), round(p[1] * 1000), round(p[2] * 1000)) for p in seg["centerline"])
        ckey = (min(pts, pts[::-1]), round((seg.get("carriageway_width_m") or 0.0) * 1000), seg.get("elevation_type"))
        if not opts.get("keep_duplicate_segments") and ckey in key_to_rep:
            rep = key_to_rep[ckey]
            alias_map[seg["id"]] = rep
            duplicates[rep].append(seg["id"])
        else:
            rep = seg["id"]
            key_to_rep[ckey] = rep
            alias_map[rep], duplicates[rep], reps[rep] = rep, [rep], seg

    allow_x = bool(opts.get("allow_elevated_planar_connect"))
    g_ids = sorted(
        rid for rid, s in reps.items()
        if (allow_x or s.get("elevation_type") == "GROUND") and s.get("verification") != "UNKNOWN"
        and all(len(p) == 3 and all(p[k] is not None and math.isfinite(p[k]) for k in range(3)) for p in s["centerline"])
    )
    cl_b = {r: (min(p[0] for p in reps[r]["centerline"]), min(p[2] for p in reps[r]["centerline"]), max(p[0] for p in reps[r]["centerline"]), max(p[2] for p in reps[r]["centerline"])) for r in g_ids}
    adj: dict[str, set[str]] = {r: set() for r in g_ids}
    edges: list[list[str]] = []
    for i, a_id in enumerate(g_ids):
        cla, ba, hwa = reps[a_id]["centerline"], cl_b[a_id], (reps[a_id].get("carriageway_width_m") or 0.0) * 0.5
        for b_id in g_ids[i + 1:]:
            clb, bb, hwb = reps[b_id]["centerline"], cl_b[b_id], (reps[b_id].get("carriageway_width_m") or 0.0) * 0.5
            pad = max(hwa, hwb) + 1.1
            if ba[2] < bb[0] - pad or bb[2] < ba[0] - pad or ba[3] < bb[1] - pad or bb[3] < ba[1] - pad:
                continue
            conn = any(_seg_intersect_xz(cla[ia], cla[ia + 1], clb[ib], clb[ib + 1]) for ia in range(len(cla) - 1) for ib in range(len(clb) - 1))
            if not conn:
                conn = any(_pt_polyline_dist_xz(ep[0], ep[2], clb) <= hwb + 1.0 + 1e-9 for ep in (cla[0], cla[-1])) or any(_pt_polyline_dist_xz(ep[0], ep[2], cla) <= hwa + 1.0 + 1e-9 for ep in (clb[0], clb[-1]))
            if conn:
                adj[a_id].add(b_id)
                adj[b_id].add(a_id)
                edges.append([a_id, b_id])

    main_set: set[str] = set()
    ave0 = alias_map.get("AVE_0")
    if ave0 in adj:
        q = deque([ave0])
        main_set.add(ave0)
        while q:
            for nb in sorted(adj[q.popleft()]):
                if nb not in main_set:
                    main_set.add(nb)
                    q.append(nb)

    connectivity = {rid: ("VERIFIED" if rid in main_set else "UNVERIFIED") for rid in sorted(reps)}
    fp_by_id = {fp["id"]: fp for fp in dump.get("footprints", [])}
    corridors_all, seg_fp_b = [], {}
    for rid in sorted(reps):
        for fid in reps[rid].get("corridor_footprint_ids", []):
            fp = fp_by_id.get(fid)
            if fp is None or _is_roundabout_fp(fp) or fp.get("verification") == "UNKNOWN":
                continue
            pts, rect, b = _fp_geom(fp)
            seg_fp_b.setdefault(rid, []).append(b)
            corridors_all.append({
                "id": fid, "segment_id": rid, "category": fp["category"],
                "source_group": fp.get("source_group", ""), "polygon": pts, "bounds": list(b),
                "is_rect": rect, "connectivity": connectivity[rid], "existing": True, "is_roundabout": False,
            })

    seen_swk: set[Any] = set()
    raw_by_len = sorted(alias_map.keys(), key=lambda k: (-len(k), k))
    for fp in sorted(dump.get("footprints", []), key=lambda f: f["id"]):
        if fp.get("category") != "SIDEWALK" or _is_roundabout_fp(fp) or fp.get("verification") == "UNKNOWN":
            continue
        pts, rect, b = _fp_geom(fp)
        skey = tuple((round(p[0] * 1000), round(p[1] * 1000)) for p in pts)
        if not opts.get("keep_duplicate_segments") and skey in seen_swk:
            continue
        seen_swk.add(skey)
        owner = next((alias_map[rk] for rk in raw_by_len if fp["id"].startswith(f"SWK_{rk}_")), None)
        if owner is None:
            owner = next((rid for rid in sorted(seg_fp_b) if any(b[0] <= rb[2] + 0.5 and b[2] >= rb[0] - 0.5 and b[1] <= rb[3] + 0.5 and b[3] >= rb[1] - 0.5 for rb in seg_fp_b[rid])), None)
        corridors_all.append({
            "id": fp["id"], "segment_id": owner, "category": "SIDEWALK",
            "source_group": fp.get("source_group", ""), "polygon": pts, "bounds": list(b),
            "is_rect": rect, "connectivity": connectivity.get(owner, "UNVERIFIED") if owner else "UNVERIFIED",
            "existing": True, "is_roundabout": False,
        })

    return {
        "raw_segment_count": len(raw_segs), "dedup_node_count": len(reps),
        "raw_ground_count": sum(1 for s in raw_segs if s.get("elevation_type") == "GROUND"),
        "dedup_ground_count": sum(1 for s in reps.values() if s.get("elevation_type") == "GROUND"),
        "raw_main_component_count": sum(1 for sid in alias_map if alias_map[sid] in main_set),
        "dedup_main_component_count": len(main_set),
        "alias_map": dict(sorted(alias_map.items())),
        "duplicates": {k: sorted(v) for k, v in sorted(duplicates.items()) if len(v) > 1},
        "representatives": reps, "edges": sorted(edges), "main_component": sorted(main_set),
        "connectivity": connectivity, "raw_connectivity": {sid: connectivity[alias_map[sid]] for sid in sorted(alias_map)},
        "corridors_all": sorted(corridors_all, key=lambda c: c["id"]),
    }


def corridors_from_graph(graph: dict[str, Any], include_unverified: bool = False) -> list[dict[str, Any]]:
    return [dict(c) for c in graph.get("corridors_all", []) if not c.get("is_roundabout") and (include_unverified or c.get("connectivity") == "VERIFIED")]


# --- Layer 2: Road access evaluation ---

def _merge_intervals(ivs: list[tuple[float, float, str, float]]) -> list[tuple[float, float, list[str], float]]:
    if not ivs:
        return []
    ivs.sort(key=lambda t: (t[0], t[1]))
    merged: list[tuple[float, float, set[str], float]] = []
    for a, b, cid, gap in ivs:
        if not merged or a > merged[-1][1] + 1e-9:
            merged.append((a, b, {cid}, gap))
        else:
            pa, pb, pids, pgap = merged[-1]
            pids.add(cid)
            merged[-1] = (pa, max(pb, b), pids, min(pgap, gap))
    return [(a, b, sorted(ids), g) for a, b, ids, g in merged]


def _side_contact(px0: float, pz0: float, px1: float, pz1: float, corridors: list[dict[str, Any]], max_gap: float):
    best_side, best_len, best_gap, best_ids, best_ex = None, 0.0, None, [], True
    by_id = {c["id"]: c for c in corridors}
    eps = 1e-9
    side_specs = (("SOUTH", True, pz0, px0, px1), ("NORTH", True, pz1, px0, px1), ("WEST", False, px0, pz0, pz1), ("EAST", False, px1, pz0, pz1))
    for side, horiz, const_c, t0, t1 in side_specs:
        pa, ta = (1, 0) if horiz else (0, 1)
        ivs: list[tuple[float, float, str, float]] = []
        for c in corridors:
            pts, rect, cb = _fp_geom(c)
            if cb[pa + 2] < const_c - max_gap - eps or cb[pa] > const_c + max_gap + eps or cb[ta + 2] < t0 - max_gap - eps or cb[ta] > t1 + max_gap + eps:
                continue
            if rect:
                d_perp = max(0.0, cb[pa] - const_c, const_c - cb[pa + 2])
                if d_perp <= max_gap + eps:
                    allow = math.sqrt(max(0.0, max_gap * max_gap - d_perp * d_perp))
                    ia, ib = max(t0, cb[ta] - allow), min(t1, cb[ta + 2] + allow)
                    if ib > ia + eps:
                        ivs.append((ia, ib, c["id"], d_perp))
                continue
            step, n_pts = 0.25, max(1, int(math.floor((t1 - t0) / 0.25)))
            run_s, run_g = None, float("inf")
            for k in range(n_pts + 1):
                tk = min(t1, t0 + k * step)
                d = _pt_poly_dist(tk, const_c, pts) if horiz else _pt_poly_dist(const_c, tk, pts)
                if d <= max_gap + eps:
                    if run_s is None:
                        run_s, run_g = tk, d
                    elif d < run_g:
                        run_g = d
                elif run_s is not None:
                    pt = min(t1, t0 + (k - 1) * step)
                    if pt > run_s + eps:
                        ivs.append((run_s, pt, c["id"], run_g))
                    run_s = None
            if run_s is not None and min(t1, t0 + n_pts * step) > run_s + eps:
                ivs.append((run_s, min(t1, t0 + n_pts * step), c["id"], run_g))
        for a, b, cids, g in _merge_intervals(ivs):
            clen = b - a
            if clen > best_len + eps or (abs(clen - best_len) <= eps and (best_gap is None or g < best_gap - eps)):
                best_side, best_len, best_gap, best_ids = side, clen, g, cids
                best_ex = all(by_id[cid].get("existing", True) for cid in cids)
    return best_side, best_len, best_gap, best_ids, best_ex


def evaluate_access(
    parcel: dict[str, Any] | list[float] | tuple[float, float, float, float],
    corridors: list[dict[str, Any]], graph: dict[str, Any] | None = None, opts: dict[str, Any] | None = None,
) -> dict[str, Any]:
    opts = opts or {}
    bounds = parcel["bounds"] if isinstance(parcel, dict) else parcel
    px0, pz0, px1, pz1 = float(bounds[0]), float(bounds[1]), float(bounds[2]), float(bounds[3])
    max_gap = float(opts.get("access_max_gap_m", ACCESS_MAX_GAP_M))
    min_c = float(opts.get("access_min_contact_m", ACCESS_MIN_CONTACT_M))
    eps = 1e-9
    verified, unverified, roundabouts = [], [], []
    for c in corridors:
        pts, rect, cb = _fp_geom(c)
        hit, oa = fp_intersects_cell(pts, rect, cb, px0, pz0, px1, pz1)
        if hit and oa > eps:
            return {"ok": False, "side": None, "gap_m": None, "contact_m": 0.0, "corridor_ids": [c["id"]], "connectivity": "UNVERIFIED", "existing_only": False, "reasons": ["CORRIDOR_OVERLAP"]}
        if _is_roundabout_fp(c):
            roundabouts.append(c)
            continue
        conn = c.get("connectivity", "UNVERIFIED")
        if graph is not None and c.get("segment_id") is not None:
            rep = graph.get("alias_map", {}).get(c["segment_id"], c["segment_id"])
            conn = graph.get("connectivity", {}).get(rep, conn)
        (verified if conn == "VERIFIED" else unverified).append(c)

    side, clen, gap, cids, ex_only = _side_contact(px0, pz0, px1, pz1, verified, max_gap)
    if clen >= min_c - eps:
        return {"ok": True, "side": side, "gap_m": round(gap, 3) if gap is not None else None, "contact_m": round(clen, 3), "corridor_ids": cids, "connectivity": "VERIFIED", "existing_only": ex_only, "reasons": []}
    u_side, u_len, u_gap, u_ids, _ = _side_contact(px0, pz0, px1, pz1, unverified, max_gap)
    if u_len >= min_c - eps:
        return {"ok": False, "side": u_side, "gap_m": round(u_gap, 3) if u_gap is not None else None, "contact_m": round(u_len, 3), "corridor_ids": u_ids, "connectivity": "UNVERIFIED", "existing_only": False, "reasons": ["ROAD_UNVERIFIED"]}
    reasons = []
    if _side_contact(px0, pz0, px1, pz1, roundabouts, max_gap)[1] >= min_c - eps:
        reasons.append("ROUNDABOUT_NOT_USABLE")
    reasons.append("CONTACT_LENGTH_INSUFFICIENT" if clen > eps else ("NO_ROAD_ACCESS" if not reasons else ""))
    return {"ok": False, "side": side, "gap_m": round(gap, 3) if gap is not None else None, "contact_m": round(clen, 3), "corridor_ids": cids, "connectivity": "UNVERIFIED", "existing_only": False, "reasons": sorted({r for r in reasons if r})}


# --- Layer 1: 1 m Occupancy Rasters, Vertex Slopes & Prefix Sums ---

_FLIP_01 = bytes.maketrans(b"\x00\x01", b"\x01\x00")


def _band(a: bytearray, b: bytearray) -> bytearray:
    return bytearray((int.from_bytes(a, "little") & int.from_bytes(b, "little")).to_bytes(len(a), "little"))


def _bor(a: bytearray, b: bytearray) -> bytearray:
    return bytearray((int.from_bytes(a, "little") | int.from_bytes(b, "little")).to_bytes(len(a), "little"))


def _bnot(a: bytearray) -> bytearray:
    return bytearray(a.translate(_FLIP_01))


def _prefix_sum_2d(buf: bytearray, w: int, h: int) -> array:
    s = w + 1
    ps = array("i", [0]) * (s * (h + 1))
    if buf.find(1) == -1:
        return ps
    prev_row = [0] * w
    for iz in range(h):
        cur_row = list(map(add, prev_row, accumulate(buf[iz * w:(iz + 1) * w])))
        ps[(iz + 1) * s + 1:(iz + 2) * s] = array("i", cur_row)
        prev_row = cur_row
    return ps


def _vert_to_cell(vbuf: bytearray, w: int, h: int, op: Callable[[bytearray, bytearray], bytearray]) -> bytearray:
    out = bytearray(w * h)
    if vbuf.find(1) == -1:
        return out
    vw = w + 1
    prev = op(vbuf[:w], vbuf[1:w + 1])
    for iz in range(h):
        vr1 = (iz + 1) * vw
        cur = op(vbuf[vr1:vr1 + w], vbuf[vr1 + 1:vr1 + w + 1])
        out[iz * w:(iz + 1) * w] = op(prev, cur)
        prev = cur
    return out


def _paint_poly(
    buf: bytearray, w: int, h: int, x0: int, z0: int,
    pts: list[list[float]], rect: bool, b: tuple[float, float, float, float],
    full_buf: bytearray | None = None,
) -> None:
    if b[2] < x0 or b[0] > x0 + w or b[3] < z0 or b[1] > z0 + h:
        return
    ix0, ix1 = max(0, math.floor(b[0]) - x0), min(w - 1, math.floor(b[2]) - x0)
    iz0, iz1 = max(0, math.floor(b[1]) - z0), min(h - 1, math.floor(b[3]) - z0)
    if ix1 < ix0 or iz1 < iz0:
        return
    fx0 = fx1 = fz0 = fz1 = 0
    if rect and (b[2] - b[0]) > 1e-9 and (b[3] - b[1]) > 1e-9:
        fx0, fx1 = max(ix0, math.ceil(b[0] - 1e-9) - x0), min(ix1 + 1, math.floor(b[2] + 1e-9) - x0)
        fz0, fz1 = max(iz0, math.ceil(b[1] - 1e-9) - z0), min(iz1 + 1, math.floor(b[3] + 1e-9) - z0)
        if fx1 > fx0 and fz1 > fz0:
            ones = b"\x01" * (fx1 - fx0)
            for iz in range(fz0, fz1):
                st = iz * w + fx0
                buf[st:st + (fx1 - fx0)] = ones
                if full_buf is not None:
                    full_buf[st:st + (fx1 - fx0)] = ones
    for iz in range(iz0, iz1 + 1):
        in_z, row = (fz0 <= iz < fz1), iz * w
        for ix in range(ix0, ix1 + 1):
            if in_z and fx0 <= ix < fx1:
                continue
            hit, oa = fp_intersects_cell(pts, rect, b, x0 + ix, z0 + iz, x0 + ix + 1, z0 + iz + 1)
            if hit:
                buf[row + ix] = 1
                if full_buf is not None and oa >= 1.0 - 1e-6:
                    full_buf[row + ix] = 1


class RegionMasks:
    """1 m raster masks, vertex slope masks, lazy prefix sums, and geom_valid cache."""

    def __init__(
        self, scenario_id: str, region_id: str, preset: str, bounds: tuple[int, int, int, int],
        layers: tuple[bytearray, ...], v_slope: array, grid1m: dict[str, Any] | None,
        h_offset: float, opts: dict[str, Any],
    ):
        self.scenario_id, self.region_id, self.preset, self.bounds = scenario_id, region_id, preset, bounds
        self.x0, self.z0, self.x1, self.z1 = bounds
        self.w, self.h = self.x1 - self.x0, self.z1 - self.z0
        (self.base_free, self.protected, self.unknown_cell, self.unavail_cell,
         self.proven_excl, self.v_unknown, self.v_s1_3, self.v_s4) = layers
        self.blocked = _bnot(self.base_free)
        self.v_slope, self.grid1m, self.h_offset, self.opts = v_slope, grid1m, h_offset, opts
        self._ps_blocked: array | None = None
        self._ps_cache: dict[str, array] = {}
        self.ps_hard_blocked: array | None = None
        self.geom_valid_cache: dict[tuple[str, int], ValidMask] = {}
        self.geom_valid_builds: dict[tuple[str, int], int] = {}

    @property
    def ps_blocked(self) -> array:
        if self._ps_blocked is None:
            self._ps_blocked = _prefix_sum_2d(self.blocked, self.w, self.h)
        return self._ps_blocked

    def _vps(self, name: str) -> array:
        if name not in self._ps_cache:
            buf = (_bor(self.v_unknown, _bor(self.v_s1_3, self.v_s4)) if name == "not_s0"
                   else (_bor(self.v_s1_3, self.v_s4) if name == "s1_4" else getattr(self, f"v_{name}")))
            self._ps_cache[name] = _prefix_sum_2d(buf, self.w + 1, self.h + 1)
        return self._ps_cache[name]

    ps_v_unknown = property(lambda self: self._vps("unknown"))
    ps_v_s1_3 = property(lambda self: self._vps("s1_3"))
    ps_v_s4 = property(lambda self: self._vps("s4"))

    def is_base_free(self, x: int, z: int) -> bool:
        return self.x0 <= x < self.x1 and self.z0 <= z < self.z1 and bool(self.base_free[(z - self.z0) * self.w + (x - self.x0)])

    def rect_blocked(self, x0: int, z0: int, x1: int, z1: int) -> int:
        if x1 <= x0 or z1 <= z0:
            return 0
        total = (x1 - x0) * (z1 - z0)
        ax0, az0, ax1, az1 = max(self.x0, x0), max(self.z0, z0), min(self.x1, x1), min(self.z1, z1)
        if ax1 <= ax0 or az1 <= az0:
            return total
        s, ps = self.w + 1, self.ps_blocked
        a, b, c, d = ax0 - self.x0, ax1 - self.x0, az0 - self.z0, az1 - self.z0
        return (total - (ax1 - ax0) * (az1 - az0)) + (ps[d * s + b] - ps[c * s + b] - ps[d * s + a] + ps[c * s + a])

    def vert_sum(self, ps: array, x0: int, z0: int, x1: int, z1: int) -> int:
        if x0 < self.x0 or z0 < self.z0 or x1 > self.x1 or z1 > self.z1:
            return 1
        vs = self.w + 2
        a, b, c, d = x0 - self.x0, x1 - self.x0 + 1, z0 - self.z0, z1 - self.z0 + 1
        return ps[d * vs + b] - ps[c * vs + b] - ps[d * vs + a] + ps[c * vs + a]

    def height_at(self, x: int, z: int) -> float | None:
        g = self.grid1m
        if g is None:
            return None
        ix, iz = x - int(g["origin_x"]), z - int(g["origin_z"])
        if ix < 0 or iz < 0 or ix >= g["nx"] or iz >= g["nz"]:
            return None
        h = g["heights"][iz * g["nx"] + ix]
        return None if h is None else float(h) + self.h_offset

    def parcel_terrain(self, x0: int, z0: int, x1: int, z1: int) -> dict[str, Any]:
        ch = self.height_at((x0 + x1) // 2, (z0 + z1) // 2)
        ok = self.vert_sum(self.ps_v_unknown, x0, z0, x1, z1) == 0
        min_h, max_h, max_s = float("inf"), float("-inf"), 0.0
        if ok:
            vw = self.w + 1
            for vz in range(z0, z1 + 1):
                vrow = (vz - self.z0) * vw
                for vx in range(x0, x1 + 1):
                    hv = self.height_at(vx, vz)
                    if hv is not None:
                        min_h, max_h = min(min_h, hv), max(max_h, hv)
                    max_s = max(max_s, self.v_slope[vrow + (vx - self.x0)])
        return {
            "min_h_m": round(min_h, 3) if ok and min_h != float("inf") else None,
            "max_h_m": round(max_h, 3) if ok and max_h != float("-inf") else None,
            "center_h_m": round(ch, 3) if ch is not None else None,
            "max_slope_pct": round(max_s, 3) if ok else None,
            "slope_cls": slope_class_from_pct(max_s if ok else None),
            "height_source": "DIRECT_RUNTIME_1M" if ok else "UNKNOWN",
        }


def _build_vertex_slopes(grid1m: dict[str, Any] | None, x0: int, z0: int, w: int, h: int) -> tuple[bytearray, bytearray, bytearray, array]:
    vw, vh = w + 1, h + 1
    v_unknown, v_s1_3, v_s4 = bytearray(vw * vh), bytearray(vw * vh), bytearray(vw * vh)
    v_slope = array("f", [0.0]) * (vw * vh)
    if grid1m is None:
        v_unknown[:] = b"\x01" * (vw * vh)
        return v_unknown, v_s1_3, v_s4, v_slope
    gnx, gnz, hs = grid1m["nx"], grid1m["nz"], grid1m["heights"]
    gox, goz = int(grid1m["origin_x"]), int(grid1m["origin_z"])
    vx_lo, vx_hi = max(0, gox - x0), min(vw, gox + gnx - x0)
    ones_l, ones_r = b"\x01" * vx_lo, b"\x01" * max(0, vw - vx_hi)
    for vz in range(vh):
        iz, vrow = (z0 + vz) - goz, vz * vw
        if iz < 0 or iz >= gnz or vx_hi <= vx_lo:
            v_unknown[vrow:vrow + vw] = b"\x01" * vw
            continue
        if vx_lo:
            v_unknown[vrow:vrow + vx_lo] = ones_l
        if vx_hi < vw:
            v_unknown[vrow + vx_hi:vrow + vw] = ones_r
        grow = iz * gnx
        for vx in range(vx_lo, vx_hi):
            ix = (x0 + vx) - gox
            if (hv := hs[grow + ix]) is None:
                v_unknown[vrow + vx] = 1
                continue
            hl, hr = (hs[grow + ix - 1] if ix > 0 else None), (hs[grow + ix + 1] if ix + 1 < gnx else None)
            hd, hu = (hs[(iz - 1) * gnx + ix] if iz > 0 else None), (hs[(iz + 1) * gnx + ix] if iz + 1 < gnz else None)
            gx = (hr - hl) * 0.5 if (hl is not None and hr is not None) else ((hr - hv) if hr is not None else ((hv - hl) if hl is not None else None))
            gz = (hu - hd) * 0.5 if (hd is not None and hu is not None) else ((hu - hv) if hu is not None else ((hv - hd) if hd is not None else None))
            if gx is None or gz is None:
                v_unknown[vrow + vx] = 1
                continue
            if gx == 0.0 and gz == 0.0:
                continue
            sp = round(math.hypot(gx, gz) * 100.0, 9)
            v_slope[vrow + vx] = sp
            scls = slope_class_from_pct(sp)
            if scls == "S4":
                v_s4[vrow + vx] = 1
            elif scls in ("S1", "S2", "S3"):
                v_s1_3[vrow + vx] = 1
    return v_unknown, v_s1_3, v_s4, v_slope


def build_masks(
    dump: dict[str, Any], scenario_id: str, region_id: str,
    bounds_internal: list[int] | tuple[int, int, int, int] | None = None,
    opts: dict[str, Any] | None = None,
    _cached_slopes: tuple[dict[str, Any] | None, tuple[bytearray, bytearray, bytearray, array]] | None = None,
) -> RegionMasks:
    opts = opts or {}
    if bounds_internal is None:
        scens = opts.get("scenarios") or SCENARIOS
        _req(scenario_id in scens and region_id in scens[scenario_id], f"Unknown scenario/region: {scenario_id}/{region_id}")
        b = spec_to_internal(scens[scenario_id][region_id])
    else:
        b = list(bounds_internal)
    x0, z0, x1, z1 = (int(v) for v in b)
    w, h, n_cells, vw = x1 - x0, z1 - z0, (x1 - x0) * (z1 - z0), x1 - x0 + 1
    h_offset = float(opts.get("height_offset_m", 0.0))

    grid1m = next((g for g in dump.get("height_grids", []) if g["region_id"] == region_id and abs(g["step_m"] - 1.0) < 1e-6), None)
    if _cached_slopes is not None and _cached_slopes[0] == grid1m:
        v_unknown, v_s1_3, v_s4, v_slope = _cached_slopes[1]
    else:
        v_unknown, v_s1_3, v_s4, v_slope = _build_vertex_slopes(grid1m, x0, z0, w, h)

    protected, unknown_cell, unavail_cell, proven_excl = bytearray(n_cells), bytearray(n_cells), bytearray(n_cells), bytearray(n_cells)
    world, comp, pg = dump["world"], dump["completeness"], dump["world"]["physical_ground"]
    pg_b, pg_ver = tuple(pg["bounds"]), pg["verification"] == "RUNTIME_VERIFIED"
    glob_inc = any(comp[k] in {"PARTIAL", "UNKNOWN"} for k in LAND_REQ_COMP) or comp["world_bounds"] == "UNKNOWN" or not pg_ver
    blockers = [i for i in dump.get("issues", []) if i["severity"] == "BLOCKER" and (not i["affected_region_ids"] or region_id in i["affected_region_ids"])]
    if glob_inc or any(i["affected_polygon"] is None for i in blockers):
        unknown_cell[:] = b"\x01" * n_cells
    for i in blockers:
        if i["affected_polygon"] is not None:
            bp = i["affected_polygon"]
            _paint_poly(unknown_cell, w, h, x0, z0, bp, is_axis_rect(bp), poly_bounds(bp))

    reg_obj = next((r for r in dump.get("regions", []) if r["id"] == region_id), None)
    if reg_obj is not None:
        sp, sp_in = reg_obj["survey_polygon"], bytearray(n_cells)
        _paint_poly(sp_in, w, h, x0, z0, sp, is_axis_rect(sp), poly_bounds(sp))
        if sp_in.find(0) != -1:
            unknown_cell = _bor(unknown_cell, _bnot(sp_in))

    if not opts.get("ignore_physical_ground"):
        pg_in = bytearray(n_cells)
        pg_poly = [[pg_b[0], pg_b[1]], [pg_b[2], pg_b[1]], [pg_b[2], pg_b[3]], [pg_b[0], pg_b[3]]]
        _paint_poly(pg_in, w, h, x0, z0, pg_poly, True, pg_b)
        if pg_in.find(0) != -1:
            if pg_ver:
                unavail_cell = _bor(unavail_cell, _bnot(pg_in))
            else:
                unknown_cell = _bor(unknown_cell, _bnot(pg_in))

    for wp in world.get("water_regions", []):
        _paint_poly(unavail_cell, w, h, x0, z0, wp, is_axis_rect(wp), poly_bounds(wp), proven_excl)
    for bp in world.get("beach_regions", []):
        _paint_poly(unavail_cell, w, h, x0, z0, bp, is_axis_rect(bp), poly_bounds(bp))

    excl_cons = bool(opts.get("exclude_conservative_in_upper"))
    for fp in dump.get("footprints", []):
        pts, rect, fb = _fp_geom(fp)
        if fb[2] < x0 or fb[0] > x1 or fb[3] < z0 or fb[1] > z1:
            continue
        cat = fp["category"]
        if fp.get("protected") or cat == "SITE_A":
            _paint_poly(protected, w, h, x0, z0, pts, rect, fb, proven_excl)
        elif fp.get("verification") == "UNKNOWN":
            _paint_poly(unknown_cell, w, h, x0, z0, pts, rect, fb)
        else:
            p_full = proven_excl if (cat == "WATER" or fp.get("geometry_precision") == "EXACT_OUTLINE" or excl_cons) else None
            _paint_poly(unavail_cell, w, h, x0, z0, pts, rect, fb, p_full)

    if v_unknown.find(1) != -1 and not opts.get("allow_missing_height"):
        unknown_cell = _bor(unknown_cell, _vert_to_cell(v_unknown, w, h, _bor))
    if v_s4.find(1) != -1:
        proven_excl = _bor(proven_excl, _vert_to_cell(v_s4, w, h, _band))

    base_free = _bnot(_bor(protected, _bor(unknown_cell, unavail_cell)))
    return RegionMasks(
        scenario_id, region_id, dump["metadata"]["preset"], (x0, z0, x1, z1),
        (base_free, protected, unknown_cell, unavail_cell, proven_excl, v_unknown, v_s1_3, v_s4),
        v_slope, grid1m, h_offset, opts,
    )


def _slice_2d(buf: Any, sw: int, ox: int, oz: int, w: int, h: int, is_arr: bool = False) -> Any:
    out = array("f", [0.0]) * (w * h) if is_arr else bytearray(w * h)
    for iz in range(h):
        src = (oz + iz) * sw + ox
        out[iz * w:(iz + 1) * w] = buf[src:src + w]
    return out


def _slice_masks(env: RegionMasks, scenario_id: str, bounds_internal: list[int]) -> RegionMasks:
    x0, z0, x1, z1 = (int(v) for v in bounds_internal)
    ox, oz, w, h = x0 - env.x0, z0 - env.z0, x1 - x0, z1 - z0
    cells = tuple(_slice_2d(b, env.w, ox, oz, w, h) for b in (env.base_free, env.protected, env.unknown_cell, env.unavail_cell, env.proven_excl))
    verts = tuple(_slice_2d(b, env.w + 1, ox, oz, w + 1, h + 1) for b in (env.v_unknown, env.v_s1_3, env.v_s4))
    return RegionMasks(scenario_id, env.region_id, env.preset, (x0, z0, x1, z1), cells + verts,
                       _slice_2d(env.v_slope, env.w + 1, ox, oz, w + 1, h + 1, True), env.grid1m, env.h_offset, env.opts)


def _slice_valid_mask(env_vm: ValidMask, bounds_internal: list[int], allow_oob: bool = False) -> ValidMask:
    x0, z0, x1, z1 = (int(v) for v in bounds_internal)
    ox, oz, w, h = x0 - env_vm.x0, z0 - env_vm.z0, x1 - x0, z1 - z0
    vm = ValidMask(w * h, x0, z0, w, h, env_vm.pw, env_vm.ph, env_vm.proto_id, env_vm.orientation)
    hw, hh = env_vm.pw // 2, env_vm.ph // 2
    iz_lo, iz_hi = (0, h) if allow_oob else (hh, min(h - hh + 1, h))
    ix_lo, ix_hi = (0, w) if allow_oob else (hw, min(w - hw + 1, w))
    if iz_hi > iz_lo and ix_hi > ix_lo:
        span = ix_hi - ix_lo
        for iz in range(iz_lo, iz_hi):
            src = (oz + iz) * env_vm.w + (ox + ix_lo)
            vm[iz * w + ix_lo:iz * w + ix_hi] = env_vm[src:src + span]
    return vm


def _combine_masks(lo: RegionMasks, hi: RegionMasks, opts: dict[str, Any] | None = None) -> RegionMasks:
    opts = opts or {}
    swap = bool(opts.get("swap_union_intersection"))
    bf = _bor(lo.base_free, hi.base_free) if swap else _band(lo.base_free, hi.base_free)
    unav = _band(lo.unavail_cell, hi.unavail_cell) if swap else _bor(lo.unavail_cell, hi.unavail_cell)
    layers = (
        bf, _bor(lo.protected, hi.protected), _bor(lo.unknown_cell, hi.unknown_cell),
        unav, _bor(lo.proven_excl, hi.proven_excl),
        _bor(lo.v_unknown, hi.v_unknown), _bor(lo.v_s1_3, hi.v_s1_3), _bor(lo.v_s4, hi.v_s4),
    )
    vs = lo.v_slope if lo.v_slope == hi.v_slope else array("f", (max(a, b) for a, b in zip(lo.v_slope, hi.v_slope)))
    return RegionMasks(lo.scenario_id, lo.region_id, "COMMON", lo.bounds, layers, vs, lo.grid1m, lo.h_offset, opts)


def _compute_geom_mask(
    masks: RegionMasks, prototype_id: str, orientation: int,
    ps_blk: array, check_unk: bool, use_opts: dict[str, Any], free_hint: bytearray | None = None,
) -> ValidMask:
    pw0, ph0 = PROTOTYPES[prototype_id]["parcel"]
    pw, ph = (pw0, ph0) if orientation == 0 else (ph0, pw0)
    hw, hh = pw // 2, ph // 2
    vm = ValidMask(masks.w * masks.h, masks.x0, masks.z0, masks.w, masks.h, pw, ph, prototype_id, orientation)
    allow_oob = bool(use_opts.get("allow_out_of_bounds"))
    allow_mh = bool(use_opts.get("allow_missing_height"))
    relax_s0 = bool(use_opts.get("relax_slope_s0"))
    baked = use_opts.get("bake_access_into_geom_valid")
    iz_lo, iz_hi = (0, masks.h) if allow_oob else (hh, min(masks.h - hh + 1, masks.h))
    ix_lo, ix_hi = (0, masks.w) if allow_oob else (hw, min(masks.w - hw + 1, masks.w))
    if ps_blk[-1] == masks.w * masks.h or iz_hi <= iz_lo or ix_hi <= ix_lo:
        return vm
    s, vs = masks.w + 1, masks.w + 2
    if not relax_s0:
        ps_v = masks._vps("not_s0") if (check_unk and not allow_mh) else masks._vps("s1_4")
    else:
        ps_v = _prefix_sum_2d(_bor(masks.v_unknown, masks.v_s4), masks.w + 1, masks.h + 1) if (check_unk and not allow_mh) else masks.ps_v_s4
    check_v, ones_row = ps_v[-1] != 0, b"\x01" * (ix_hi - ix_lo)
    fh = free_hint if (not allow_oob and free_hint is not None) else None
    for iz in range(iz_lo, iz_hi):
        rz0, rz1 = (max(0, iz - hh), min(masks.h, iz + hh)) if allow_oob else (iz - hh, iz + hh)
        row, b0, b1, v0, v1 = iz * masks.w, rz0 * s, rz1 * s, rz0 * vs, (rz1 + 1) * vs
        strip_blk = ps_blk[b1 + masks.w] - ps_blk[b0 + masks.w]
        if not allow_oob and strip_blk == masks.w * ph:
            continue
        if strip_blk == 0 and (not check_v or ps_v[v1 + masks.w + 1] - ps_v[v0 + masks.w + 1] == 0) and baked is None and fh is None:
            vm[row + ix_lo:row + ix_hi] = ones_row
            continue
        ix, row_end = ix_lo, row + ix_hi
        while ix < ix_hi:
            if fh is not None:
                p = fh.find(1, row + ix, row_end)
                if p == -1:
                    break
                ix = p - row
            rx0, rx1 = (max(0, ix - hw), min(masks.w, ix + hw)) if allow_oob else (ix - hw, ix + hw)
            if ps_blk[b1 + rx1] - ps_blk[b0 + rx1] - ps_blk[b1 + rx0] + ps_blk[b0 + rx0] == 0:
                if not check_v or (ps_v[v1 + rx1 + 1] - ps_v[v0 + rx1 + 1] - ps_v[v1 + rx0] + ps_v[v0 + rx0]) == 0:
                    if baked is None or evaluate_access((masks.x0 + ix - hw, masks.z0 + iz - hh, masks.x0 + ix + hw, masks.z0 + iz + hh), baked)["ok"]:
                        vm[row + ix] = 1
            ix += 1
    return vm


def geom_valid(masks: RegionMasks, prototype_id: str, orientation: int, opts: dict[str, Any] | None = None) -> ValidMask:
    _req(prototype_id in PROTOTYPES and orientation in (0, 90), f"Invalid prototype/orientation: {prototype_id}/{orientation}")
    key = (prototype_id, orientation)
    if opts is None and key in masks.geom_valid_cache:
        return masks.geom_valid_cache[key]
    vm = _compute_geom_mask(masks, prototype_id, orientation, masks.ps_blocked, True, opts if opts is not None else masks.opts, masks.base_free)
    if opts is None:
        masks.geom_valid_cache[key] = vm
        masks.geom_valid_builds[key] = masks.geom_valid_builds.get(key, 0) + 1
    return vm


# --- Ratio, C_upper, Placement, Common Layout ---

def check_ratio(counts: dict[str, int], region_id: str) -> bool:
    n = sum(counts.values())
    if n == 0:
        return True
    if any(k not in REGION_RULES[region_id]["prototypes"] and v > 0 for k, v in counts.items()):
        return False
    if region_id == "B1":
        return counts.get("R02", 0) >= math.ceil(0.5 * n)
    if region_id == "B2":
        return counts.get("R05", 0) == n
    need = math.ceil(0.2 * n)
    return all(counts.get(p, 0) >= need for p in ("R01", "R05", "R08"))


def min_area_for_count(region_id: str, n: int) -> int | None:
    if n <= 0:
        return 0
    if region_id == "B1":
        k = math.ceil(n / 2)
        return 2016 * k + 1428 * (n - k)
    if region_id == "B2":
        return 528 * n
    m = math.ceil(0.2 * n)
    return None if n < 3 * m else m * (1428 + 528 + 912) + 528 * (n - 3 * m)


def compute_c_upper(region_id: str, a_possible: float) -> int:
    best = 0
    for n in range(1, int(a_possible // 528) + 2):
        req = min_area_for_count(region_id, n)
        if req is not None and req <= a_possible + 1e-9:
            best = n
    return best


def _make_access_fn(corridors: list[dict[str, Any]] | None, graph: dict[str, Any] | None, opts: dict[str, Any]) -> Callable | None:
    if corridors is None:
        return None
    empty = {"ok": False, "side": None, "gap_m": None, "contact_m": 0.0, "corridor_ids": [], "connectivity": "UNVERIFIED", "existing_only": False, "reasons": ["NO_ROAD_ACCESS"]}
    if not corridors:
        fn0: Any = lambda _b: empty
        fn0.corridor_bboxes = []
        return fn0
    pad = float(opts.get("access_max_gap_m", ACCESS_MAX_GAP_M)) + 0.01
    bboxes = [(c["bounds"][0] - pad, c["bounds"][1] - pad, c["bounds"][2] + pad, c["bounds"][3] + pad) for c in corridors]
    ux0, uz0, ux1, uz1 = min(b[0] for b in bboxes), min(b[1] for b in bboxes), max(b[2] for b in bboxes), max(b[3] for b in bboxes)
    def fn(box: tuple[int, int, int, int]) -> dict[str, Any]:
        if box[2] < ux0 or box[0] > ux1 or box[3] < uz0 or box[1] > uz1:
            return empty
        near = [c for c, bb in zip(corridors, bboxes) if box[2] >= bb[0] and box[0] <= bb[2] and box[3] >= bb[1] and box[1] <= bb[3]]
        return evaluate_access(box, near, graph=graph, opts=opts) if near else empty
    fn.corridor_bboxes = bboxes  # type: ignore[attr-defined]
    return fn


def _corridor_near_mask(x0: int, z0: int, w: int, h: int, bboxes: list[tuple[float, float, float, float]], hw: int, hh: int) -> bytearray:
    buf = bytearray(w * h)
    for bx0, bz0, bx1, bz1 in bboxes:
        ix0, ix1 = max(0, math.floor(bx0 - hw) - x0), min(w, math.ceil(bx1 + hw) - x0 + 1)
        iz0, iz1 = max(0, math.floor(bz0 - hh) - z0), min(h, math.ceil(bz1 + hh) - z0 + 1)
        if ix1 > ix0 and iz1 > iz0:
            ones = b"\x01" * (ix1 - ix0)
            for iz in range(iz0, iz1):
                buf[iz * w + ix0:iz * w + ix1] = ones
    return buf


def place_layout(
    valid_by_proto: dict[str, dict[int, ValidMask]], access_fn: Callable | None,
    region_id: str, order: str | None = None, opts: dict[str, Any] | None = None,
    seed_parcels: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    opts, order = opts or {}, order or "row_major"
    protos = [p for p in REGION_RULES[region_id]["prototypes"] if p in valid_by_proto]
    allow_ov = bool(opts.get("allow_overlap"))
    seeds = [dict(s) for s in (seed_parcels or [])]
    n_seeds, placed, boxes = len(seeds), list(seeds), [tuple(s["bounds"]) for s in seeds]
    counts, cursors, exhausted = {p: 0 for p in protos}, {p: 0 for p in protos}, set()
    for s in seeds:
        counts[s["prototype"]] = counts.get(s["prototype"], 0) + 1
    cbboxes = getattr(access_fn, "corridor_bboxes", None) if access_fn is not None else None
    either: dict[str, bytearray] = {}
    for p in protos:
        m0, m90 = valid_by_proto[p].get(0), valid_by_proto[p].get(90)
        ref = m0 or m90
        if ref is None:
            continue
        em = _bor(m0, m90) if (m0 is not None and m90 is not None) else bytearray(ref)
        if cbboxes is not None:
            hw = max(m0.pw // 2 if m0 else 0, m90.pw // 2 if m90 else 0)
            hh = max(m0.ph // 2 if m0 else 0, m90.ph // 2 if m90 else 0)
            em = _band(em, _corridor_near_mask(ref.x0, ref.z0, ref.w, ref.h, cbboxes, hw, hh))
        either[p] = em

    def prio() -> list[str]:
        n1 = sum(counts.values()) + 1
        if region_id == "B2":
            return ["R05"]
        if region_id == "B1":
            return ["R02", "R01"] if counts.get("R02", 0) < math.ceil(0.5 * n1) else ["R01", "R02"]
        need = math.ceil(0.2 * n1)
        req = [p for d, _, p in sorted(((need - counts.get(p, 0), PROTOTYPES[p]["area_m2"], p) for p in ("R01", "R08", "R05")), key=lambda t: (-t[0], -t[1], t[2])) if d > 0]
        return req + [p for p in ("R05", "R08", "R01") if p not in req]

    def find_next(proto: str) -> dict[str, Any] | None:
        m0, m90 = valid_by_proto[proto].get(0), valid_by_proto[proto].get(90)
        ref = m0 or m90
        if ref is None or proto not in either:
            return None
        w, h, x0, z0, total, pos, em = ref.w, ref.h, ref.x0, ref.z0, ref.w * ref.h, cursors[proto], either[proto]
        min_hw = min(m0.pw // 2 if m0 else 999, m90.pw // 2 if m90 else 999)
        min_hh = min(m0.ph // 2 if m0 else 999, m90.ph // 2 if m90 else 999)
        while pos < total:
            if order != "col_major":
                pos = em.find(1, pos)
                if pos == -1:
                    break
                iz, ix = divmod(pos, w)
                idx = pos
            else:
                ix, iz = divmod(pos, h)
                idx = iz * w + ix
                if not em[idx]:
                    pos += 1
                    continue
            skip_x = 0
            for orient, vm in ((0, m0), (90, m90)):
                if vm is None or not vm[idx]:
                    continue
                px0, pz0 = x0 + ix - vm.pw // 2, z0 + iz - vm.ph // 2
                px1, pz1 = px0 + vm.pw, pz0 + vm.ph
                ov_box = None if allow_ov else next((b for b in boxes if pz0 < b[3] and pz1 > b[1] and px0 < b[2] and px1 > b[0]), None)
                if ov_box is not None:
                    if (z0 + iz - min_hh < ov_box[3]) and (z0 + iz + min_hh > ov_box[1]):
                        cs = ov_box[2] + min_hw - x0
                        if skip_x == 0 or cs < skip_x:
                            skip_x = cs
                    continue
                skip_x = -1
                box = (px0, pz0, px1, pz1)
                acc = access_fn(box) if access_fn is not None else None
                if acc is not None and not (acc["ok"] and acc.get("existing_only", True)):
                    continue
                cursors[proto] = pos + 1
                return {
                    "id": f"{region_id}_{proto}_{len(placed) + 1:03d}", "prototype": proto, "orientation": orient,
                    "center": [x0 + ix, z0 + iz], "bounds": list(box), "area_m2": PROTOTYPES[proto]["area_m2"],
                    "buildings": 4 if (proto == "R08" and opts.get("r08_as_four_buildings")) else PROTOTYPES[proto]["buildings"],
                    "units": PROTOTYPES[proto]["units"], "status": "DIRECT" if acc is not None else "GEOM_VALID",
                    "access": acc, "reasons": [],
                }
            pos = iz * w + min(w, skip_x) if (order != "col_major" and skip_x > ix + 1) else pos + 1
        cursors[proto] = total
        return None

    while len(exhausted) < len(protos):
        moved = False
        for p in prio():
            if p in exhausted:
                continue
            item = find_next(p)
            if item is not None:
                placed.append(item)
                boxes.append(tuple(item["bounds"]))
                counts[p] += 1
                moved = True
                break
            exhausted.add(p)
        if not moved:
            break

    while len(placed) > n_seeds and not check_ratio(counts, region_id):
        rem = next((i for i in range(len(placed) - 1, n_seeds - 1, -1) if check_ratio({k: v - (1 if k == placed[i]["prototype"] else 0) for k, v in counts.items()}, region_id)), len(placed) - 1)
        counts[placed.pop(rem)["prototype"]] -= 1
    for idx in range(n_seeds, len(placed)):
        placed[idx]["id"] = f"{region_id}_{placed[idx]['prototype']}_{idx + 1:03d}"
    return {
        "parcels": placed, "count": sum(i["buildings"] for i in placed),
        "units": sum(i["units"] for i in placed), "prototype_counts": dict(sorted(counts.items())),
        "ratio_ok": check_ratio(counts, region_id), "order": order,
        "tie_breaking": "deficit_then_area_desc_then_orient_0_90",
    }


def _verify_layout(
    parcels: list[dict[str, Any]], masks: RegionMasks, corridors: list[dict[str, Any]] | None,
    graph: dict[str, Any] | None, region_id: str, require_access: bool, opts: dict[str, Any],
) -> tuple[bool, list[str]]:
    if not parcels:
        return True, []
    errs, boxes, counts = [], [], {}
    for p in parcels:
        pw0, ph0 = PROTOTYPES[p["prototype"]]["parcel"]
        pw, ph = (pw0, ph0) if p["orientation"] == 0 else (ph0, pw0)
        x0, z0, x1, z1 = p["bounds"]
        if (x1 - x0, z1 - z0) != (pw, ph):
            errs.append(f"DIM:{p['id']}")
        if not opts.get("allow_out_of_bounds") and (x0 < masks.x0 or z0 < masks.z0 or x1 > masks.x1 or z1 > masks.z1):
            errs.append(f"OOB:{p['id']}")
        if masks.rect_blocked(x0, z0, x1, z1) != 0:
            errs.append(f"BLK:{p['id']}")
        if not opts.get("allow_missing_height") and masks.vert_sum(masks.ps_v_unknown, x0, z0, x1, z1) != 0:
            errs.append(f"NOH:{p['id']}")
        if masks.vert_sum(masks.ps_v_s4, x0, z0, x1, z1) != 0 or (not opts.get("relax_slope_s0") and masks.vert_sum(masks.ps_v_s1_3, x0, z0, x1, z1) != 0):
            errs.append(f"SLOPE:{p['id']}")
        if not opts.get("allow_overlap") and any(x0 < bx1 and x1 > bx0 and z0 < bz1 and z1 > bz0 for bx0, bz0, bx1, bz1 in boxes):
            errs.append(f"OVL:{p['id']}")
        boxes.append((x0, z0, x1, z1))
        counts[p["prototype"]] = counts.get(p["prototype"], 0) + 1
        if require_access and corridors is not None:
            acc = evaluate_access((x0, z0, x1, z1), corridors, graph=graph, opts=opts)
            if not (acc["ok"] and acc.get("existing_only", True)):
                errs.append(f"ACC:{p['id']}")
    if not check_ratio(counts, region_id):
        errs.append("RATIO")
    return len(errs) == 0, errs


def common_layout(
    masks_lo: RegionMasks, masks_hi: RegionMasks, masks_common: RegionMasks,
    valid_lo: dict[str, dict[int, ValidMask]], valid_hi: dict[str, dict[int, ValidMask]], valid_common: dict[str, dict[int, ValidMask]],
    corridors_lo: list[dict[str, Any]] | None, corridors_hi: list[dict[str, Any]] | None, corridors_common: list[dict[str, Any]] | None,
    graph_lo: dict[str, Any] | None, graph_hi: dict[str, Any] | None,
    region_id: str, require_access: bool = True, order: str | None = None, opts: dict[str, Any] | None = None,
) -> dict[str, Any]:
    opts = opts or {}
    af_com = _make_access_fn(corridors_common if require_access else None, graph_lo, opts)
    af_lo = _make_access_fn(corridors_lo if require_access else None, graph_lo, opts)
    af_hi = _make_access_fn(corridors_hi if require_access else None, graph_hi, opts)
    lay_com = place_layout(valid_common, af_com, region_id, order=order, opts=opts)
    ok_lo, e_lo = _verify_layout(lay_com["parcels"], masks_lo, corridors_lo, graph_lo, region_id, require_access, opts)
    ok_hi, e_hi = _verify_layout(lay_com["parcels"], masks_hi, corridors_hi, graph_hi, region_id, require_access, opts)
    lay_lo = place_layout(valid_lo, af_lo, region_id, order=order, opts=opts)
    lay_hi = place_layout(valid_hi, af_hi, region_id, order=order, opts=opts)
    if lay_com["count"] > lay_lo["count"]:
        lay_lo = dict(lay_com, adopted_common=True)
    if lay_com["count"] > lay_hi["count"]:
        lay_hi = dict(lay_com, adopted_common=True)
    return {
        "L_common": lay_com, "L_phone_low": lay_lo, "L_desktop_high": lay_hi,
        "C_common": lay_com["count"], "C_phone_low": lay_lo["count"], "C_desktop_high": lay_hi["count"],
        "preset_validation": {"PHONE_LOW": {"ok": ok_lo, "errors": e_lo}, "DESKTOP_HIGH": {"ok": ok_hi, "errors": e_hi}},
    }


def _compute_areas(m: RegionMasks) -> dict[str, float]:
    n = m.w * m.h
    c_s4, c_s13 = _vert_to_cell(m.v_s4, m.w, m.h, _bor), _vert_to_cell(m.v_s1_3, m.w, m.h, _bor)
    a_prot = m.protected.count(1)
    a_unk = _band(m.unknown_cell, _bnot(m.protected)).count(1)
    t1 = _bor(m.protected, m.unknown_cell)
    unav_raw = _bor(m.unavail_cell, c_s4)
    a_unav = _band(unav_raw, _bnot(t1)).count(1)
    a_cond = _band(c_s13, _bnot(_bor(t1, unav_raw))).count(1)
    a_dir = n - a_prot - a_unk - a_unav - a_cond
    a_gross, a_possible = float(n), float(n - m.proven_excl.count(1))
    err = abs((a_prot + a_unk + a_unav + a_cond + a_dir) - a_gross)
    _req(err <= CONSERVATION_TOL_M2, f"Area conservation error {err:.3f} > {CONSERVATION_TOL_M2}")
    return {
        "A_gross": round(a_gross, 3), "A_direct": round(float(a_dir), 3),
        "A_conditional": round(float(a_cond), 3), "A_protected": round(float(a_prot), 3),
        "A_unavailable": round(float(a_unav), 3), "A_unknown": round(float(a_unk), 3),
        "A_eligible": round(float(a_dir + a_cond), 3), "A_possible": round(a_possible, 3),
        "conservation_error_m2": round(err, 6),
    }


def _build_report_md(inv: dict[str, Any]) -> str:
    rg = inv["road_graph"]
    lines = [
        "# WE-01B (T-016B) Parcel Capacity Audit Report", "",
        f"- Analyzer: `{inv['analyzer_version']}` (handoff v{inv['handoff_schema_version']}, WE-01A `{inv['we01a_analyzer_version']}`)",
        f"- Game BASE: `{inv['base_sha']}` | Polygon revision: `{inv['polygon_revision']}`",
        f"- PHONE_LOW fingerprint: `{inv['presets']['PHONE_LOW']['static_fingerprint']}`",
        f"- DESKTOP_HIGH fingerprint: `{inv['presets']['DESKTOP_HIGH']['static_fingerprint']}`",
        f"- Land artifacts SHA-256: inventory=`{inv['land_artifacts']['land_inventory_sha256']}`, report=`{inv['land_artifacts']['land_report_sha256']}`",
        f"- C_conditional: `{C_CONDITIONAL_STATUS}` (deferred to T-016D; no final 25 ha / 40 / 60 / D3 verdicts)",
        "- C_unknown definition: `max(0, greedy_count_if_unknown_and_unverified_roads_free - C_direct)`",
        f"- Road graph: raw={rg['raw_segment_count']} (GROUND={rg['raw_ground_count']}), dedup={rg['dedup_node_count']} (GROUND={rg['dedup_ground_count']}), AVE_0 main={rg['dedup_main_component_count']} nodes ({rg['raw_main_component_count']} raw), duplicates=`{rg['duplicates']}`",
        "", "| Scenario | Region | Bounds (spec) | C_pre | C_dir | C_lo | C_hi | C_cond | C_up | C_unk | Units | A_gross | A_dir | A_cond | A_prot | A_unav | A_unk | A_elig |",
        "|---|---|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for sid, sc in inv["scenarios"].items():
        for rid, r in sc["regions"].items():
            c, a = r["capacities"], r["areas_m2"]
            lines.append(
                f"| {sid} | {rid} | `{r['bounds_spec']}` | {c['C_preliminary']} | {c['C_direct']} | "
                f"{c['C_phone_low']} | {c['C_desktop_high']} | {c['C_conditional']} | {c['C_upper']} | "
                f"{c['C_unknown']} | {c['units_direct']} | {a['A_gross']:.1f} | {a['A_direct']:.1f} | "
                f"{a['A_conditional']:.1f} | {a['A_protected']:.1f} | {a['A_unavailable']:.1f} | "
                f"{a['A_unknown']:.1f} | {a['A_eligible']:.1f} |"
            )
    lines.append("\n- B2 Note: flat R05 capacity is PROXY only; hillside housing vision requires separate terrain engineering.\n")
    return "\n".join(lines)


def _build_relaxed_valid(m_com: RegionMasks, protos: tuple[str, ...], rel_bboxes: list[tuple[float, float, float, float]], opts: dict[str, Any]) -> dict[str, dict[int, ValidMask]]:
    hard_blk = _bor(m_com.protected, m_com.unavail_cell)
    m_com.ps_hard_blocked = _prefix_sum_2d(hard_blk, m_com.w, m_com.h)
    hard_free = _bnot(hard_blk)
    out: dict[str, dict[int, ValidMask]] = {}
    for p in protos:
        pw, ph = PROTOTYPES[p]["parcel"]
        near = _corridor_near_mask(m_com.x0, m_com.z0, m_com.w, m_com.h, rel_bboxes, max(pw, ph) // 2, max(pw, ph) // 2)
        out[p] = {o: _compute_geom_mask(m_com, p, o, m_com.ps_hard_blocked, False, opts, _band(hard_free, near)) for o in (0, 90)}
    return out


def _build_region_triplet(d_lo: dict[str, Any], d_hi: dict[str, Any], sid: str, rid: str, b_int: list[int], opts: dict[str, Any]):
    protos = REGION_RULES[rid]["prototypes"]
    m_lo = build_masks(d_lo, sid, rid, b_int, opts=opts)
    m_hi = build_masks(d_hi, sid, rid, b_int, opts=opts, _cached_slopes=(m_lo.grid1m, (m_lo.v_unknown, m_lo.v_s1_3, m_lo.v_s4, m_lo.v_slope)))
    m_com = _combine_masks(m_lo, m_hi, opts=opts)
    same_g = (m_lo.base_free == m_hi.base_free and m_lo.v_unknown == m_hi.v_unknown and m_lo.v_s1_3 == m_hi.v_s1_3 and m_lo.v_s4 == m_hi.v_s4)
    v_lo = {p: {o: geom_valid(m_lo, p, o) for o in (0, 90)} for p in protos}
    v_hi = v_lo if same_g else {p: {o: geom_valid(m_hi, p, o) for o in (0, 90)} for p in protos}
    if opts.get("swap_union_intersection"):
        v_com = {p: {o: geom_valid(m_com, p, o) for o in (0, 90)} for p in protos}
    elif same_g:
        v_com = v_lo
    else:
        v_com = {}
        for p in protos:
            v_com[p] = {}
            for o in (0, 90):
                a, b = v_lo[p][o], v_hi[p][o]
                vm = ValidMask(len(a), a.x0, a.z0, a.w, a.h, a.pw, a.ph, p, o)
                vm[:] = _band(a, b)
                v_com[p][o] = vm
    return (m_lo, m_hi, m_com), (v_lo, v_hi, v_com)


def analyze(
    dump_paths: list[str | Path], out_dir: str | Path | None = None,
    opts: dict[str, Any] | None = None,
    land_inventory_path: str | Path | None = None, land_report_path: str | Path | None = None,
) -> dict[str, Any]:
    opts = opts or {}
    scenarios = opts.get("scenarios") or SCENARIOS
    validate_scenarios(scenarios, opts=opts)
    dumps = load_dumps(dump_paths, land_inventory_path=land_inventory_path, land_report_path=land_report_path, opts=opts)
    d_lo, d_hi = dumps["PHONE_LOW"], dumps["DESKTOP_HIGH"]
    base_sha = d_lo["metadata"]["base_sha"]

    graph_lo, graph_hi = build_road_graph(d_lo, opts=opts), build_road_graph(d_hi, opts=opts)
    cors_lo, cors_hi = corridors_from_graph(graph_lo), corridors_from_graph(graph_hi)
    hi_ids = {c["id"] for c in cors_hi}
    cors_common = [c for c in cors_lo if c["id"] in hi_ids]
    cors_relaxed = [dict(c, connectivity="VERIFIED") for c in corridors_from_graph(graph_lo, include_unverified=True)]
    acc_relaxed = _make_access_fn(cors_relaxed, None, opts)
    rel_bboxes = getattr(acc_relaxed, "corridor_bboxes", []) if acc_relaxed is not None else []
    near_any = lambda b: any(bb[2] >= b[0] and bb[0] <= b[2] and bb[3] >= b[1] and bb[1] <= b[3] for bb in rel_bboxes)

    env_data, env_unk_valid, allow_oob = {}, {}, bool(opts.get("allow_out_of_bounds"))
    if "ENVELOPE" in scenarios:
        for rid in sorted(scenarios["ENVELOPE"]):
            be = spec_to_internal(scenarios["ENVELOPE"][rid])
            ms, vs = _build_region_triplet(d_lo, d_hi, "ENVELOPE", rid, be, opts)
            env_data[rid] = (ms, vs)
            if near_any(be) and (ms[2].unknown_cell.find(1) != -1 or len(cors_relaxed) > len(cors_common)):
                env_unk_valid[rid] = _build_relaxed_valid(ms[2], REGION_RULES[rid]["prototypes"], rel_bboxes, opts)

    scen_out, cand_out = {}, {}
    for sid in scenarios:
        reg_out, reg_cand, gross_u = {}, {}, 0.0
        for rid in sorted(scenarios[sid]):
            b_spec, b_int = list(scenarios[sid][rid]), spec_to_internal(scenarios[sid][rid])
            gross_u += (b_int[2] - b_int[0]) * (b_int[3] - b_int[1])
            protos = REGION_RULES[rid]["prototypes"]
            if sid == "ENVELOPE" and rid in env_data:
                (m_lo, m_hi, m_com), (v_lo, v_hi, v_com) = env_data[rid]
            elif rid in env_data:
                (m_lo, m_hi, m_com) = tuple(_slice_masks(m, sid, b_int) for m in env_data[rid][0])
                (v_lo, v_hi, v_com) = tuple({p: {o: _slice_valid_mask(v[p][o], b_int, allow_oob) for o in (0, 90)} for p in protos} for v in env_data[rid][1])
            else:
                (m_lo, m_hi, m_com), (v_lo, v_hi, v_com) = _build_region_triplet(d_lo, d_hi, sid, rid, b_int, opts)

            prelim = common_layout(m_lo, m_hi, m_com, v_lo, v_hi, v_com, None, None, None, None, None, rid, require_access=False, opts=opts)
            direct = common_layout(m_lo, m_hi, m_com, v_lo, v_hi, v_com, cors_lo, cors_hi, cors_common, graph_lo, graph_hi, rid, require_access=True, opts=opts)
            areas = _compute_areas(m_com)
            if opts.get("enforce_land_use_ratio"):
                sh = 100.0 * sum(p["area_m2"] for p in direct["L_common"]["parcels"]) / areas["A_gross"] if areas["A_gross"] else 0.0
                if sh < 15.0 or sh > 30.0:
                    direct["L_common"]["parcels"], direct["L_common"]["count"], direct["C_common"] = [], 0, 0

            c_direct = direct["C_common"]
            if (areas["A_unknown"] == 0 and len(cors_relaxed) == len(cors_common)) or not near_any(b_int):
                c_unknown = 0
            else:
                v_unk = (env_unk_valid[rid] if sid == "ENVELOPE" else {p: {o: _slice_valid_mask(env_unk_valid[rid][p][o], b_int, allow_oob) for o in (0, 90)} for p in protos}) if rid in env_unk_valid else _build_relaxed_valid(m_com, protos, rel_bboxes, opts)
                c_unknown = max(0, place_layout(v_unk, acc_relaxed, rid, opts=opts)["count"] - c_direct)

            c_upper = compute_c_upper(rid, areas["A_possible"])
            min_t, ideal_t = REGION_RULES[rid]["min"], REGION_RULES[rid]["ideal"]
            bstat = "DIRECT_MET" if c_direct >= min_t else ("UPPER_BOUND_BELOW_MIN" if c_upper < min_t else ("NOT_FEASIBLE" if opts.get("search_fail_as_infeasible") else "SEARCH_INSUFFICIENT_UNPROVEN"))

            for p_it in direct["L_common"]["parcels"]:
                p_it["terrain"] = m_com.parcel_terrain(*p_it["bounds"])
            for p_it in prelim["L_common"]["parcels"]:
                p_it["terrain"] = m_com.parcel_terrain(*p_it["bounds"])
                acc = evaluate_access(p_it["bounds"], cors_common, graph=graph_lo, opts=opts)
                p_it["access"] = acc
                p_it["status"] = "DIRECT" if (acc["ok"] and acc.get("existing_only", True)) else "INTERNAL_STREET_REQUIRED"
                p_it["reasons"] = [] if p_it["status"] == "DIRECT" else (acc["reasons"] or ["NO_ROAD_ACCESS"])

            gv_cnts = {f"{p}_{o}": v_com[p][o].count(1) for p in protos for o in (0, 90)}
            dir_area = sum(p["area_m2"] for p in direct["L_common"]["parcels"])
            excl = [r for r, cnd in (("SITE_A_PROTECTED", areas["A_protected"] > 0), ("OBSTACLES_WATER_BEACH_OR_S4", areas["A_unavailable"] > 0), ("DATA_INCOMPLETE_OR_UNKNOWN", areas["A_unknown"] > 0), ("SLOPE_S1_TO_S3_FOUNDATION_REQUIRED", areas["A_conditional"] > 0), ("INTERNAL_STREET_REQUIRED", prelim["C_common"] > c_direct)) if cnd]
            reg_out[rid] = {
                "bounds_spec": b_spec, "bounds_internal": b_int, "gross_area_m2": areas["A_gross"],
                "capacities": {"C_preliminary": prelim["C_common"], "C_direct": c_direct, "C_conditional": C_CONDITIONAL_STATUS, "C_upper": c_upper, "C_unknown": c_unknown, "C_phone_low": direct["C_phone_low"], "C_desktop_high": direct["C_desktop_high"], "C_common": c_direct, "units_direct": direct["L_common"]["units"], "prototype_counts_direct": direct["L_common"]["prototype_counts"], "prototype_mix_ok": direct["L_common"]["ratio_ok"], "proxy_used": REGION_RULES[rid]["proxy"]},
                "capacity_bound_status": bstat, "meets_min_direct": c_direct >= min_t, "meets_ideal_direct": c_direct >= ideal_t,
                "land_use_reference": {"residential_parcel_area_m2": round(float(dir_area), 3), "residential_parcel_share_pct": round(100.0 * dir_area / areas["A_gross"], 3) if areas["A_gross"] else 0.0, "reference_band_pct": [15, 30], "informational_only": True, "hard_gate": False},
                "areas_m2": areas,
                "conditional_candidates_summary": {"INTERNAL_STREET_REQUIRED_parcels": sum(1 for p in prelim["L_common"]["parcels"] if p["status"] == "INTERNAL_STREET_REQUIRED"), "FOUNDATION_REQUIRED_cells_m2": int(areas["A_conditional"]), "geom_valid_center_counts": gv_cnts, "reasons": [r for r in ("INTERNAL_STREET_REQUIRED", "SLOPE_S1..S3") if (r == "INTERNAL_STREET_REQUIRED" and prelim["C_common"] > c_direct) or (r == "SLOPE_S1..S3" and areas["A_conditional"] > 0)]},
                "b2_hillside_note": "B2 flat R05 capacity is PROXY only; hillside housing vision requires separate terrain/foundation engineering." if rid == "B2" else None,
                "exclusion_reasons": sorted(excl),
                "unknown_data_summary": {"A_unknown_m2": areas["A_unknown"], "C_unknown": c_unknown, "unverified_road_segments": sorted(k for k, v in graph_lo["connectivity"].items() if v != "VERIFIED")},
                "preset_validation": direct["preset_validation"], "direct_parcels": direct["L_common"]["parcels"],
            }
            reg_cand[rid] = {"direct_parcels": direct["L_common"]["parcels"], "preliminary_parcels": prelim["L_common"]["parcels"], "center_counts": gv_cnts, "foundation_cells_m2": int(areas["A_conditional"]), "status_note": f"C_conditional={C_CONDITIONAL_STATUS}"}
        tot_dir = sum(r["capacities"]["C_direct"] for r in reg_out.values())
        all_min = (tot_dir >= 40) if opts.get("allow_cross_region_offset") else all(r["meets_min_direct"] for r in reg_out.values())
        scen_out[sid] = {"gross_union_area_m2": round(gross_u, 3), "regions": reg_out, "totals": {"C_preliminary": sum(r["capacities"]["C_preliminary"] for r in reg_out.values()), "C_direct": tot_dir, "C_conditional": C_CONDITIONAL_STATUS, "C_upper": sum(r["capacities"]["C_upper"] for r in reg_out.values()), "all_regions_meet_min_direct": all_min}}
        cand_out[sid] = reg_cand

    compat = {"base_sha": base_sha, "phone_low_static_fingerprint": d_lo["metadata"]["static_fingerprint"], "desktop_high_static_fingerprint": d_hi["metadata"]["static_fingerprint"], "we01a_analyzer_version": WE01A_COMPAT_VERSION, "handoff_schema_version": HANDOFF_SCHEMA_VERSION, "schema_version": 1, "polygon_revision": POLYGON_REVISION}
    inv = {
        "analyzer_version": ANALYZER_VERSION, "handoff_schema_version": HANDOFF_SCHEMA_VERSION,
        "schema_version": 1, "we01a_analyzer_version": WE01A_COMPAT_VERSION,
        "polygon_revision": POLYGON_REVISION, "base_sha": base_sha, "compatibility_key": compat,
        "presets": {p: {"static_fingerprint": dumps[p]["metadata"]["static_fingerprint"], "file_sha256": dumps[p]["_file_sha256"]} for p in ("PHONE_LOW", "DESKTOP_HIGH")},
        "land_artifacts": {"land_inventory_sha256": _sha256_bytes(Path(land_inventory_path).read_bytes()) if land_inventory_path else None, "land_report_sha256": _sha256_bytes(Path(land_report_path).read_bytes()) if land_report_path else None},
        "scenarios_spec_order": scenarios, "scenarios_internal_order": {s: {r: spec_to_internal(b) for r, b in regs.items()} for s, regs in scenarios.items()},
        "prototypes": PROTOTYPES, "road_graph": {k: v for k, v in graph_lo.items() if k not in ("representatives", "corridors_all")},
        "placement_policy": {"order": "row_major", "tie_breaking": "deficit_then_area_desc_then_orient_0_90"}, "scenarios": scen_out,
    }
    if out_dir is not None:
        od = Path(out_dir)
        od.mkdir(parents=True, exist_ok=True)
        (od / "capacity_inventory.json").write_text(json.dumps(inv, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (od / "parcel_candidates.json").write_text(json.dumps({"analyzer_version": ANALYZER_VERSION, "handoff_schema_version": HANDOFF_SCHEMA_VERSION, "schema_version": 1, "we01a_analyzer_version": WE01A_COMPAT_VERSION, "polygon_revision": POLYGON_REVISION, "base_sha": base_sha, "compatibility_key": compat, "presets": inv["presets"], "scenarios": cand_out}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (od / "capacity_report.md").write_text(_build_report_md(inv), encoding="utf-8")
    return inv


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="WE-01B (T-016B) Parcel Capacity Analyzer (read-only audit tool).")
    ap.add_argument("--dump", action="append", required=True, help="Runtime dump JSON path (PHONE_LOW & DESKTOP_HIGH).")
    ap.add_argument("--out", required=True, help="Output directory.")
    ap.add_argument("--land-inventory", default=None, help="Optional WE-01A land_inventory.json.")
    ap.add_argument("--land-report", default=None, help="Optional WE-01A land_report.md.")
    args = ap.parse_args(argv)
    try:
        analyze(args.dump, out_dir=args.out, land_inventory_path=args.land_inventory, land_report_path=args.land_report)
    except CapacityError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
