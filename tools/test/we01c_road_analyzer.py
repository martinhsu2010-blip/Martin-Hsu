#!/usr/bin/env python3
"""WE-01C (T-016C) Road Feasibility Survey — read-only offline geometry audit tooling."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from we01a_land_analyzer import (  # noqa: E402
    clip_poly_to_rect, compute_static_fingerprint, dist_point_to_poly, fp_intersects_cell,
    is_axis_rect, poly_area, poly_bounds, sample_height, validate_dump,
)
from we01b_capacity_analyzer import (  # noqa: E402
    ANALYZER_VERSION as B_VERSION, POLYGON_REVISION, SCENARIOS, build_road_graph,
    corridors_from_graph, internal_to_spec, load_dumps, spec_to_internal,
)

ANALYZER_VERSION = "we01c-1.0"
ROAD_SCHEMA_VERSION = 1
WE01A_COMPAT_VERSION = "we01a-1.0"
C_CONDITIONAL_STATUS = "PENDING_T016D"
COR_MARGIN_M = 5.0
ELEV_TOL_M = 0.5
ACCESS_GAP_M = 2.0
MAX_SAMPLE_SPACING_M = 3.0
JUNCTION_MAX_RUN_M = 100.0
REQ_COMP = (
    "terrain_heights", "physical_ground", "visual_occupancy",
    "physical_occupancy", "trees", "water_and_beach", "protected_areas", "roads",
)

CANDIDATE_ROADS: dict[str, dict[str, Any]] = {
    "C01": {"id": "C01", "kind": "NORMAL", "control_points": [[221.0, 890.0], [240.0, 960.0], [240.0, 1200.0]], "carriageway_width_m": 17.0, "corridor_half_width_m": 12.5, "min_radius_m": 25.0, "max_grade_pct": 6.0, "is_existing_reuse": False},
    "C02": {"id": "C02", "kind": "NORMAL", "control_points": [[110.0, 960.0], [170.0, 960.0], [240.0, 960.0]], "carriageway_width_m": 7.0, "corridor_half_width_m": 5.5, "min_radius_m": 25.0, "max_grade_pct": 6.0, "is_existing_reuse": False},
    "H01": {"id": "H01", "kind": "HILLSIDE", "control_points": [[-635.0, 682.0], [-800.0, 800.0], [-800.0, 1030.0]], "carriageway_width_m": 8.0, "corridor_half_width_m": 6.0, "min_radius_m": 18.0, "max_grade_pct": 9.0, "is_existing_reuse": False},
    "H02": {"id": "H02", "kind": "HILLSIDE", "control_points": [[-800.0, 1030.0], [-420.0, 1000.0], [-240.0, 880.0]], "carriageway_width_m": 8.0, "corridor_half_width_m": 6.0, "min_radius_m": 18.0, "max_grade_pct": 9.0, "is_existing_reuse": False},
    "X01": {"id": "X01", "kind": "NORMAL", "control_points": [[-240.0, 880.0], [0.0, 960.0], [110.0, 960.0]], "carriageway_width_m": 7.0, "corridor_half_width_m": 5.5, "min_radius_m": 25.0, "max_grade_pct": 6.0, "is_existing_reuse": False},
    "U01": {"id": "U01", "kind": "EXISTING_REUSE", "control_points": [[-600.0, -720.0], [-510.0, -720.0], [-420.0, -720.0]], "carriageway_width_m": None, "corridor_half_width_m": None, "min_radius_m": None, "max_grade_pct": None, "is_existing_reuse": True},
}


class RoadError(ValueError):
    """Raised on validation, linkage, or internal contract errors."""


def _req(cond: bool, msg: str) -> None:
    if not cond:
        raise RoadError(msg)


def _r3(val: float | None) -> float | None:
    return None if val is None else round(float(val), 3)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# --- Local geometry helpers (no private imports from WE-01A/WE-01B) ---

def _pt_seg_closest(px: float, pz: float, ax: float, az: float, bx: float, bz: float, ay: float | None = None, by: float | None = None) -> tuple[float, float, float, float | None]:
    dx, dz = bx - ax, bz - az
    l2 = dx * dx + dz * dz
    if l2 <= 1e-18:
        return math.hypot(px - ax, pz - az), ax, az, ay
    t = max(0.0, min(1.0, ((px - ax) * dx + (pz - az) * dz) / l2))
    cx, cz = ax + t * dx, az + t * dz
    cy = None if (ay is None or by is None) else ay + t * (by - ay)
    return math.hypot(px - cx, pz - cz), cx, cz, cy


def _pt_polyline_closest(px: float, pz: float, cl: list[list[float]], is_3d: bool = False) -> tuple[float, float, float, float | None]:
    best = (float("inf"), 0.0, 0.0, None)
    for i in range(len(cl) - 1):
        a, b = cl[i], cl[i + 1]
        cand = (_pt_seg_closest(px, pz, a[0], a[2], b[0], b[2], a[1], b[1]) if is_3d
                else _pt_seg_closest(px, pz, a[0], a[1], b[0], b[1], a[2] if len(a) >= 3 else None, b[2] if len(b) >= 3 else None))
        if cand[0] < best[0]:
            best = cand
    return best


def _seg_intersection_pt_xz(ax: float, az: float, bx: float, bz: float, cx: float, cz: float, dx: float, dz: float) -> tuple[float, float, float, float] | None:
    eps = 1e-9
    if max(ax, bx) < min(cx, dx) - eps or max(cx, dx) < min(ax, bx) - eps or max(az, bz) < min(cz, dz) - eps or max(cz, dz) < min(az, bz) - eps:
        return None
    rx, rz, sx, sz = bx - ax, bz - az, dx - cx, dz - cz
    denom = rx * sz - rz * sx
    qpx, qpz = cx - ax, cz - az
    if abs(denom) > 1e-12:
        t, u = (qpx * sz - qpz * sx) / denom, (qpx * rz - qpz * rx) / denom
        if -eps <= t <= 1.0 + eps and -eps <= u <= 1.0 + eps:
            tc, uc = max(0.0, min(1.0, t)), max(0.0, min(1.0, u))
            return ax + tc * rx, az + tc * rz, tc, uc
        return None
    if abs(qpx * rz - qpz * rx) > 1e-7:
        return None
    for px, pz, tab, ucd in ((ax, az, 0.0, None), (bx, bz, 1.0, None), (cx, cz, None, 0.0), (dx, dz, None, 1.0)):
        if _pt_seg_closest(px, pz, ax, az, bx, bz)[0] <= 1e-6 and _pt_seg_closest(px, pz, cx, cz, dx, dz)[0] <= 1e-6:
            ta = math.hypot(px - ax, pz - az) / max(1e-12, math.hypot(rx, rz)) if tab is None else tab
            uc = math.hypot(px - cx, pz - cz) / max(1e-12, math.hypot(sx, sz)) if ucd is None else ucd
            return px, pz, max(0.0, min(1.0, ta)), max(0.0, min(1.0, uc))
    return None


def _ensure_ccw(pts: list[list[float]]) -> list[list[float]]:
    s = sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))
    return pts if s >= 0.0 else list(reversed(pts))


def _clip_poly_by_convex(subject: list[list[float]], clip_ccw: list[list[float]]) -> list[list[float]]:
    out = [list(p) for p in subject]
    n = len(clip_ccw)
    for i in range(n):
        if not out:
            return []
        ax, az = clip_ccw[i]
        bx, bz = clip_ccw[(i + 1) % n]
        ex, ez = bx - ax, bz - az
        inp, out = out, []
        prev, prev_in = inp[-1], ex * (inp[-1][1] - az) - ez * (inp[-1][0] - ax) >= -1e-12
        for cur in inp:
            cur_in = ex * (cur[1] - az) - ez * (cur[0] - ax) >= -1e-12
            if cur_in != prev_in:
                dx, dz = cur[0] - prev[0], cur[1] - prev[1]
                den = ex * dz - ez * dx
                if abs(den) > 1e-15:
                    t = (ex * (az - prev[1]) - ez * (ax - prev[0])) / den
                    out.append([prev[0] + t * dx, prev[1] + t * dz])
            if cur_in:
                out.append(cur)
            prev, prev_in = cur, cur_in
    return out


def _bbox_overlaps(a: tuple[float, float, float, float], b: tuple[float, float, float, float], pad: float = 0.0) -> bool:
    return a[2] >= b[0] - pad and b[2] >= a[0] - pad and a[3] >= b[1] - pad and b[3] >= a[1] - pad


def _fp_polygon(fp: dict[str, Any]) -> tuple[list[list[float]], bool, tuple[float, float, float, float]]:
    if fp.get("polygon") is not None:
        return fp["polygon"], is_axis_rect(fp["polygon"]), poly_bounds(fp["polygon"])
    x0, z0, x1, z1 = fp["bounds"]
    return [[x0, z0], [x1, z0], [x1, z1], [x0, z1]], True, (x0, z0, x1, z1)


def _piece_overlaps_poly(p_pts: list[list[float]], p_b: tuple[float, float, float, float], t_pts: list[list[float]], t_rect: bool, t_b: tuple[float, float, float, float]) -> bool:
    if not _bbox_overlaps(p_b, t_b):
        return False
    clipped = clip_poly_to_rect(p_pts, t_b[0], t_b[1], t_b[2], t_b[3]) if t_rect else _clip_poly_by_convex(t_pts, p_pts)
    return len(clipped) >= 3 and poly_area(clipped) > 1e-6


def existing_main_component_local(dump: dict[str, Any]) -> list[str]:
    """Recompute the existing GROUND AVE_0 main component using only local geometry helpers."""
    graph = build_road_graph(dump)
    reps = graph["representatives"]
    g_ids = sorted(rid for rid, s in reps.items() if s.get("elevation_type") == "GROUND" and s.get("verification") != "UNKNOWN")
    adj: dict[str, set[str]] = {r: set() for r in g_ids}
    for i, aid in enumerate(g_ids):
        cla, hwa = reps[aid]["centerline"], (reps[aid].get("carriageway_width_m") or 0.0) * 0.5
        for bid in g_ids[i + 1:]:
            clb, hwb = reps[bid]["centerline"], (reps[bid].get("carriageway_width_m") or 0.0) * 0.5
            hit = any(_seg_intersection_pt_xz(cla[ia][0], cla[ia][2], cla[ia + 1][0], cla[ia + 1][2], clb[ib][0], clb[ib][2], clb[ib + 1][0], clb[ib + 1][2]) is not None for ia in range(len(cla) - 1) for ib in range(len(clb) - 1))
            if not hit:
                hit = any(_pt_polyline_closest(ep[0], ep[2], clb, True)[0] <= hwb + 1.0 + 1e-9 for ep in (cla[0], cla[-1])) or any(_pt_polyline_closest(ep[0], ep[2], cla, True)[0] <= hwa + 1.0 + 1e-9 for ep in (clb[0], clb[-1]))
            if hit:
                adj[aid].add(bid)
                adj[bid].add(aid)
    ave0 = graph["alias_map"].get("AVE_0")
    if ave0 not in adj:
        return []
    seen, stack = {ave0}, [ave0]
    while stack:
        for nb in sorted(adj[stack.pop()]):
            if nb not in seen:
                seen.add(nb)
                stack.append(nb)
    return sorted(seen)


# --- G0-C1: Centerline construction & fillets ---

def _resample_line(a: list[float], b: list[float], max_step: float) -> list[list[float]]:
    dist = math.hypot(b[0] - a[0], b[1] - a[1])
    n = max(1, math.ceil(dist / max_step)) if dist > 1e-9 else 1
    return [[a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n] for k in range(n + 1)]


def build_centerline(road_spec: dict[str, Any], opts: dict[str, Any] | None = None) -> dict[str, Any]:
    opts = opts or {}
    cpts = [[float(p[0]), float(p[1])] for p in road_spec["control_points"]]
    _req(len(cpts) >= 2, f"Road {road_spec.get('id')} needs >= 2 control points")
    max_step = float(opts.get("sample_spacing_m", MAX_SAMPLE_SPACING_M))
    orig_lens = [math.hypot(cpts[i + 1][0] - cpts[i][0], cpts[i + 1][1] - cpts[i][1]) for i in range(len(cpts) - 1)]

    if road_spec.get("is_existing_reuse"):
        pts = [cpts[0]]
        for i in range(len(cpts) - 1):
            pts.extend(_resample_line(cpts[i], cpts[i + 1], max_step)[1:])
        seglens = [math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1)]
        max_sp = max(seglens) if seglens else 0.0
        reasons = [] if (max_sp <= MAX_SAMPLE_SPACING_M + 1e-9 or opts.get("allow_overspaced_samples")) else ["SAMPLE_SPACING_EXCEEDED"]
        return {
            "control_points": [[_r3(p[0]), _r3(p[1])] for p in cpts], "centerline": [[_r3(p[0]), _r3(p[1])] for p in pts],
            "centerline_exact": pts, "fillets": [], "min_radius_m": None,
            "total_length_m": _r3(sum(seglens)), "max_sample_spacing_m": _r3(max_sp),
            "geometry_ok": not reasons, "reasons": reasons,
        }

    req_r = float(opts.get("override_radius_m", road_spec["min_radius_m"]))
    min_r = 18.0 if road_spec.get("kind") == "HILLSIDE" else 25.0
    reasons: list[str] = [] if (opts.get("ignore_radius_check") or req_r >= min_r - 1e-9) else ["RADIUS_BELOW_MINIMUM"]
    fillets: list[dict[str, Any]] = []
    tangents = [0.0] * len(cpts)
    for i in range(1, len(cpts) - 1):
        pp, pc, pn = cpts[i - 1], cpts[i], cpts[i + 1]
        lp, ln = orig_lens[i - 1], orig_lens[i]
        u_in, u_out = [(pc[0] - pp[0]) / lp, (pc[1] - pp[1]) / lp], [(pn[0] - pc[0]) / ln, (pn[1] - pc[1]) / ln]
        theta = math.acos(max(-1.0, min(1.0, u_in[0] * u_out[0] + u_in[1] * u_out[1])))
        if theta < 1e-9:
            fillets.append({"vertex_index": i, "collinear": True, "deflection_rad": 0.0, "radius_m": None, "tangent_length_m": 0.0, "arc_length_m": 0.0, "fits": True})
            continue
        t_len = req_r * math.tan(theta * 0.5)
        tangents[i] = t_len
        fits = (t_len <= lp * 0.5 + 1e-9) and (t_len <= ln * 0.5 + 1e-9)
        if not fits and not opts.get("ignore_radius_check"):
            reasons.append("ARC_DOES_NOT_FIT")
        sgn = 1.0 if (u_in[0] * u_out[1] - u_in[1] * u_out[0]) >= 0.0 else -1.0
        t1 = [pc[0] - u_in[0] * t_len, pc[1] - u_in[1] * t_len]
        t2 = [pc[0] + u_out[0] * t_len, pc[1] + u_out[1] * t_len]
        center = [t1[0] - u_in[1] * sgn * req_r, t1[1] + u_in[0] * sgn * req_r]
        arc_len = req_r * theta
        fillets.append({
            "vertex_index": i, "collinear": False, "deflection_rad": _r3(theta), "radius_m": _r3(req_r),
            "tangent_length_m": _r3(t_len), "arc_length_m": _r3(arc_len), "fits": fits,
            "_t1": t1, "_t2": t2, "_center": center, "_a1": math.atan2(t1[1] - center[1], t1[0] - center[0]),
            "_sgn": sgn, "_theta": theta, "_arc_len": arc_len,
        })
    for j in range(len(orig_lens)):
        if tangents[j] + tangents[j + 1] > orig_lens[j] + 1e-9 and not opts.get("ignore_radius_check"):
            reasons.append("ARC_DOES_NOT_FIT")

    geom_ok = "ARC_DOES_NOT_FIT" not in reasons and "RADIUS_BELOW_MINIMUM" not in reasons
    pts, cur_pt = [cpts[0]], cpts[0]
    if geom_ok:
        for f in fillets:
            if f["collinear"]:
                pv = cpts[f["vertex_index"]]
                pts.extend(_resample_line(cur_pt, pv, max_step)[1:])
                cur_pt = pv
                continue
            pts.extend(_resample_line(cur_pt, f["_t1"], max_step)[1:])
            k_arc = max(1, math.ceil(f["_arc_len"] / max_step))
            cx, cz, a1, sgn, th = f["_center"][0], f["_center"][1], f["_a1"], f["_sgn"], f["_theta"]
            for k in range(1, k_arc):
                ang = a1 + sgn * th * k / k_arc
                pts.append([cx + req_r * math.cos(ang), cz + req_r * math.sin(ang)])
            pts.append(f["_t2"])
            cur_pt = f["_t2"]
        pts.extend(_resample_line(cur_pt, cpts[-1], max_step)[1:])
    else:
        for i in range(len(cpts) - 1):
            pts.extend(_resample_line(cpts[i], cpts[i + 1], max_step)[1:])

    seglens = [math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1)]
    max_sp = max(seglens) if seglens else 0.0
    if max_sp > MAX_SAMPLE_SPACING_M + 1e-9 and not opts.get("allow_overspaced_samples"):
        reasons.append("SAMPLE_SPACING_EXCEEDED")
    clean_f = [{k: v for k, v in f.items() if not k.startswith("_")} for f in fillets]
    used_r = [f["radius_m"] for f in clean_f if f["radius_m"] is not None]
    return {
        "control_points": [[_r3(p[0]), _r3(p[1])] for p in cpts], "centerline": [[_r3(p[0]), _r3(p[1])] for p in pts],
        "centerline_exact": pts, "fillets": clean_f, "min_radius_m": min(used_r) if used_r else None,
        "total_length_m": _r3(sum(seglens)), "max_sample_spacing_m": _r3(max_sp),
        "geometry_ok": not reasons, "reasons": sorted(set(reasons)),
    }


# --- G0-C2: Grade sampling from 1 m ROAD_CORRIDOR grids ---

def sample_grades(centerline: list[list[float]], grids: list[dict[str, Any]], max_grade_pct: float | None, opts: dict[str, Any] | None = None) -> dict[str, Any]:
    opts = opts or {}
    cor_grids = [g for g in grids if g.get("region_id") == "ROAD_CORRIDOR" and abs(float(g.get("step_m", 0)) - 1.0) < 1e-6]
    heights, provs = [], []
    for x, z in centerline:
        h, prov, step = sample_height(cor_grids, "ROAD_CORRIDOR", x, z)
        if h is None or prov not in ("DIRECT_RUNTIME_1M", "INTERPOLATED_1M") or step is None or abs(step - 1.0) > 1e-6:
            heights.append(None)
            provs.append("UNKNOWN")
        else:
            heights.append(float(h))
            provs.append(prov)
    missing = sum(1 for h in heights if h is None)
    step_grades, total_h = [], 0.0
    for i in range(len(centerline) - 1):
        ds = math.hypot(centerline[i + 1][0] - centerline[i][0], centerline[i + 1][1] - centerline[i][1])
        total_h += ds
        if ds > 1e-9 and heights[i] is not None and heights[i + 1] is not None:
            step_grades.append(round(100.0 * abs(heights[i + 1] - heights[i]) / ds, 9))
    max_g = max(step_grades) if step_grades else None
    avg_g = round(100.0 * abs(heights[-1] - heights[0]) / total_h, 9) if (total_h > 1e-9 and heights[0] is not None and heights[-1] is not None) else None
    reasons = ["HEIGHT_MISSING"] if missing > 0 else []
    g_val = avg_g if opts.get("use_average_grade") else max_g
    if max_grade_pct is not None and g_val is not None and not opts.get("ignore_grade_limit") and g_val > float(max_grade_pct) + 1e-9:
        reasons.append("GRADE_LIMIT_EXCEEDED")
    return {
        "heights_m": [_r3(h) for h in heights], "heights_exact": heights,
        "height_provenances": sorted(set(provs)), "missing_height_count": missing,
        "max_step_grade_pct": _r3(max_g), "net_average_grade_pct": _r3(avg_g),
        "grade_limit_pct": max_grade_pct, "height_ok": missing == 0,
        "grade_ok": "GRADE_LIMIT_EXCEEDED" not in reasons, "reasons": sorted(set(reasons)),
    }


# --- G0-C3: Corridor polygon construction (ordered per-step rects + 16-gon disks) ---

def build_corridor(centerline: list[list[float]], half_width_m: float, n_disk: int = 16) -> dict[str, Any]:
    hw = float(half_width_m)
    unit = [(math.cos(2.0 * math.pi * k / n_disk), math.sin(2.0 * math.pi * k / n_disk)) for k in range(n_disk)]
    disks = [{"kind": "DISK", "polygon": [[x + ux * hw, z + uz * hw] for ux, uz in unit], "bounds": (x - hw, z - hw, x + hw, z + hw)} for x, z in centerline]
    steps: list[dict[str, Any]] = []
    pieces: list[dict[str, Any]] = []
    for i in range(len(centerline) - 1):
        a, b = centerline[i], centerline[i + 1]
        dx, dz = b[0] - a[0], b[1] - a[1]
        ds = math.hypot(dx, dz)
        step_pieces = [disks[i]]
        if ds > 1e-9:
            nx, nz = -dz / ds * hw, dx / ds * hw
            rect = _ensure_ccw([[a[0] - nx, a[1] - nz], [b[0] - nx, b[1] - nz], [b[0] + nx, b[1] + nz], [a[0] + nx, a[1] + nz]])
            rp = {"kind": "RECT", "polygon": rect, "bounds": poly_bounds(rect)}
            step_pieces.append(rp)
            pieces.append(rp)
        if i == len(centerline) - 2:
            step_pieces.append(disks[i + 1])
        sb = (min(p["bounds"][0] for p in step_pieces), min(p["bounds"][1] for p in step_pieces), max(p["bounds"][2] for p in step_pieces), max(p["bounds"][3] for p in step_pieces))
        steps.append({"index": i, "length_m": ds, "pieces": step_pieces, "bounds": sb})
    pieces.extend(disks)
    xs, zs = [p[0] for p in centerline], [p[1] for p in centerline]
    return {"half_width_m": hw, "pieces": pieces, "steps": steps, "bounds": (min(xs) - hw, min(zs) - hw, max(xs) + hw, max(zs) + hw)}


def _build_handoff_corridors(road_id: str, centerline: list[list[float]], half_width_m: float, opts: dict[str, Any]) -> list[dict[str, Any]]:
    runs: list[tuple[list[float], list[float]]] = []
    for i in range(len(centerline) - 1):
        a, b = centerline[i], centerline[i + 1]
        if math.hypot(b[0] - a[0], b[1] - a[1]) <= 1e-9:
            continue
        if runs:
            pa, pb = runs[-1]
            ux, uz, vx, vz = pb[0] - pa[0], pb[1] - pa[1], b[0] - a[0], b[1] - a[1]
            lu, lv = math.hypot(ux, uz), math.hypot(vx, vz)
            if lu > 1e-9 and lv > 1e-9 and abs(ux * vz - uz * vx) <= 1e-6 * lu * lv and (ux * vx + uz * vz) > 0:
                runs[-1] = (pa, b)
                continue
        runs.append((a, b))
    hw, as_ex, out = float(half_width_m), bool(opts.get("mark_candidate_existing")), []
    for idx, (a, b) in enumerate(runs):
        dx, dz = b[0] - a[0], b[1] - a[1]
        ds = math.hypot(dx, dz)
        nx, nz = -dz / ds * hw, dx / ds * hw
        pts_r = [[_r3(p[0]), _r3(p[1])] for p in _ensure_ccw([[a[0] - nx, a[1] - nz], [b[0] - nx, b[1] - nz], [b[0] + nx, b[1] + nz], [a[0] + nx, a[1] + nz]])]
        out.append({
            "id": f"CAND_{road_id}_{idx}", "segment_id": road_id, "category": "ROAD",
            "source_group": "CANDIDATE_ROADS", "polygon": pts_r, "bounds": [_r3(v) for v in poly_bounds(pts_r)],
            "is_rect": is_axis_rect(pts_r), "connectivity": "VERIFIED", "existing": as_ex, "is_roundabout": False,
        })
    return out


# --- G0-C3..C6, G0-C10: Per-road evaluation ---

def _cor_margin_ok(road_id: str, centerline: list[list[float]], hw: float, grids: list[dict[str, Any]]) -> tuple[bool, float | None, list[str]]:
    own = [g for g in grids if g.get("id") == f"COR_{road_id}_1M" and abs(float(g.get("step_m", 0)) - 1.0) < 1e-6]
    cands = own if own else [g for g in grids if g.get("region_id") == "ROAD_CORRIDOR" and abs(float(g.get("step_m", 0)) - 1.0) < 1e-6]
    if not cands:
        return False, None, []
    rects = [(float(g["origin_x"]), float(g["origin_z"]), float(g["origin_x"] + (g["nx"] - 1) * g["step_m"]), float(g["origin_z"] + (g["nz"] - 1) * g["step_m"])) for g in cands]
    offs = ((1.0, 0.0), (-1.0, 0.0), (0.0, 1.0), (0.0, -1.0), (0.7071, 0.7071), (-0.7071, 0.7071), (0.7071, -0.7071), (-0.7071, -0.7071))
    min_m = float("inf")
    for x, z in centerline:
        best = max(min((x - hw) - gx0, gx1 - (x + hw), (z - hw) - gz0, gz1 - (z + hw)) for gx0, gz0, gx1, gz1 in rects)
        if best < COR_MARGIN_M - 1e-9 and len(rects) > 1:
            r_need = hw + COR_MARGIN_M - 1e-9
            if all(any(gx0 <= x + ox * r_need <= gx1 and gz0 <= z + oz * r_need <= gz1 for gx0, gz0, gx1, gz1 in rects) for ox, oz in offs):
                best = COR_MARGIN_M
        min_m = min(min_m, best)
    return min_m >= COR_MARGIN_M - 1e-9, _r3(min_m), sorted(g["id"] for g in cands)


def _beach_area_m2(corridor: dict[str, Any], centerline: list[list[float]], beach_regions: list[list[list[float]]]) -> float:
    if not beach_regions:
        return 0.0
    cb, hw = corridor["bounds"], corridor["half_width_m"]
    hit_b = [(bp, is_axis_rect(bp), poly_bounds(bp)) for bp in beach_regions if _bbox_overlaps(cb, poly_bounds(bp))]
    if not hit_b:
        return 0.0
    area = 0
    for iz in range(math.floor(cb[1]), math.ceil(cb[3])):
        cz = iz + 0.5
        for ix in range(math.floor(cb[0]), math.ceil(cb[2])):
            cx = ix + 0.5
            if any(bb[0] <= cx <= bb[2] and bb[1] <= cz <= bb[3] and (is_r or dist_point_to_poly(cx, cz, bp) <= 1e-9) for bp, is_r, bb in hit_b):
                if _pt_polyline_closest(cx, cz, centerline, False)[0] <= hw + 1e-9:
                    area += 1
    return float(area)


def _overlapping_step_indices(corridor: dict[str, Any], pts: list[list[float]], is_rect: bool, b: tuple[float, float, float, float]) -> list[int]:
    if not _bbox_overlaps(corridor["bounds"], b):
        return []
    return [st["index"] for st in corridor["steps"] if _bbox_overlaps(st["bounds"], b) and any(_piece_overlaps_poly(p["polygon"], p["bounds"], pts, is_rect, b) for p in st["pieces"])]


def _check_run_from_anchor(hit_indices: set[int], steps: list[dict[str, Any]], anchor_idx: int, opts: dict[str, Any]) -> tuple[bool, float]:
    """D-054a G0-C5: hit_indices must be ONE contiguous run containing anchor_idx with total length <= 100 m."""
    if not hit_indices:
        return True, 0.0
    run_len = sum(steps[i]["length_m"] for i in hit_indices)
    lo, hi = min(hit_indices), max(hit_indices)
    is_contig = (len(hit_indices) == hi - lo + 1) and (lo - 1 <= anchor_idx <= hi + 1)
    if not is_contig and not opts.get("accept_reentry"):
        return False, run_len
    if run_len > JUNCTION_MAX_RUN_M + 1e-9 and not opts.get("no_junction_run_limit"):
        return False, run_len
    return True, run_len


def _make_junc(
    jid: str, kind: str, ra: str, rb: str, pt: tuple[float, float], target_pt: tuple[float, float],
    dist: float, thresh: float, ha: float | None, hb: float | None, opts: dict[str, Any],
    endpoint: str | None = None, seg_elev: str | None = None, seg_conn: str | None = None,
) -> dict[str, Any]:
    skip_elev = bool(opts.get("skip_elevation_check"))
    if not skip_elev and (ha is None or hb is None):
        status, reason = "UNVERIFIED", "JUNCTION_HEIGHT_MISSING"
    elif not skip_elev and abs(ha - hb) > ELEV_TOL_M + 1e-9:
        status, reason = "REJECTED", "ELEVATION_MISMATCH"
    elif seg_conn is not None and seg_conn != "VERIFIED":
        status, reason = "UNVERIFIED", "EXISTING_SEGMENT_UNVERIFIED"
    else:
        status, reason = "VERIFIED", None
    rec: dict[str, Any] = {
        "id": jid, "kind": kind, "road_a": ra, "road_b": rb,
        "point": [_r3(pt[0]), _r3(pt[1])], "nearest_on_target": [_r3(target_pt[0]), _r3(target_pt[1])],
        "distance_m": _r3(dist), "threshold_m": _r3(thresh),
        "height_a_m": _r3(ha), "height_b_m": _r3(hb),
        "height_diff_m": _r3(abs(ha - hb)) if (ha is not None and hb is not None) else None,
        "status": status, "reason": reason,
    }
    if endpoint is not None:
        rec["endpoint"] = endpoint
    if seg_elev is not None:
        rec["target_elevation_type"] = seg_elev
    if seg_conn is not None:
        rec["target_connectivity"] = seg_conn
    return rec


def _find_existing_connections(
    road_id: str, cl: list[list[float]], heights: list[float | None], cw_hw: float,
    graph: dict[str, Any], opts: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, set[str]], list[dict[str, Any]]]:
    reps, conn_map = graph["representatives"], graph["connectivity"]
    allow_elev = bool(opts.get("allow_elevated_connect"))
    junctions: list[dict[str, Any]] = []
    ep_conn: dict[str, set[str]] = {"START": set(), "END": set()}
    opt_links: list[dict[str, Any]] = []
    cl_3d = [[cl[i][0], cl[i][1], heights[i]] for i in range(len(cl))]

    for seg_id in sorted(reps):
        seg = reps[seg_id]
        if seg.get("verification") == "UNKNOWN":
            continue
        is_ground = seg.get("elevation_type") == "GROUND"
        if not is_ground and not allow_elev:
            continue
        scl, shw = seg["centerline"], float(seg.get("carriageway_width_m") or 0.0) * 0.5
        seg_conn, matched = conn_map.get(seg_id, "UNVERIFIED"), False

        for ep_name, ep, ep_h in (("START", cl[0], heights[0]), ("END", cl[-1], heights[-1])):
            dist, jx, jz, seg_h = _pt_polyline_closest(ep[0], ep[1], scl, True)
            if dist <= shw + 1.0 + 1e-9:
                matched = True
                jn = _make_junc(f"J:{road_id}->{seg_id}@{ep_name}", "CANDIDATE_TO_EXISTING", road_id, seg_id, (ep[0], ep[1]), (jx, jz), dist, shw + 1.0, ep_h, seg_h, opts, ep_name, seg.get("elevation_type"), seg_conn)
                junctions.append(jn)
                if jn["status"] == "VERIFIED":
                    ep_conn[ep_name].add(seg_id)
            elif not opts.get("drop_ave110_link") and seg_conn == "VERIFIED" and is_ground and (shw + 1.0 < dist <= 100.0):
                for sep in (scl[0], scl[-1]):
                    if abs(ep[0] - sep[0]) <= 2.0 and abs(ep[1] - sep[2]) > shw + 1.0 and abs(math.hypot(ep[0] - sep[0], ep[1] - sep[2]) - dist) <= 1.0:
                        opt_links.append({"endpoint": [_r3(ep[0]), _r3(ep[1])], "endpoint_label": ep_name, "target_segment_id": seg_id, "gap_m": _r3(dist), "status": "UNVERIFIED", "reason": "AVE110_EXTENSION_REQUIRED"})
        if not matched:
            for sep in (scl[0], scl[-1]):
                dist, jx, jz, ch = _pt_polyline_closest(sep[0], sep[2], cl_3d, False)
                if dist <= cw_hw + 1.0 + 1e-9:
                    matched = True
                    junctions.append(_make_junc(f"J:{road_id}->{seg_id}@EXT_END", "CANDIDATE_TO_EXISTING", road_id, seg_id, (jx, jz), (sep[0], sep[2]), dist, cw_hw + 1.0, ch, sep[1], opts, "EXISTING_END", seg.get("elevation_type"), seg_conn))
                    break
        if not matched:
            for ia in range(len(cl) - 1):
                for ib in range(len(scl) - 1):
                    inter = _seg_intersection_pt_xz(cl[ia][0], cl[ia][1], cl[ia + 1][0], cl[ia + 1][1], scl[ib][0], scl[ib][2], scl[ib + 1][0], scl[ib + 1][2])
                    if inter is not None:
                        jx, jz, ta, ub = inter
                        ch = None if (heights[ia] is None or heights[ia + 1] is None) else heights[ia] + ta * (heights[ia + 1] - heights[ia])
                        sh = scl[ib][1] + ub * (scl[ib + 1][1] - scl[ib][1])
                        junctions.append(_make_junc(f"J:{road_id}->{seg_id}@CROSS", "CANDIDATE_TO_EXISTING", road_id, seg_id, (jx, jz), (jx, jz), 0.0, 0.0, ch, sh, opts, "CROSSING", seg.get("elevation_type"), seg_conn))
                        matched = True
                        break
                if matched:
                    break
    return junctions, ep_conn, opt_links


def _union_footprints(dumps: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    seen, out = set(), []
    for pn in ("PHONE_LOW", "DESKTOP_HIGH"):
        for fp in dumps[pn].get("footprints", []):
            pts, is_r, b = _fp_polygon(fp)
            gkey = (fp["category"], fp.get("geometry_precision"), bool(fp.get("physical")), bool(fp.get("protected")), fp.get("verification"), fp.get("source_group"), tuple((round(p[0] * 100), round(p[1] * 100)) for p in pts))
            if gkey not in seen:
                seen.add(gkey)
                out.append({"fp": fp, "pts": pts, "is_rect": is_r, "bounds": b, "preset": pn})
    return out


def evaluate_road(
    road_spec: dict[str, Any], dumps: dict[str, dict[str, Any]],
    graph: dict[str, Any], opts: dict[str, Any] | None = None,
    _union_fps: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    opts = opts or {}
    rid = road_spec["id"]
    d_lo = dumps["PHONE_LOW"]
    cl_res = build_centerline(road_spec, opts=opts)
    cl = cl_res["centerline_exact"]
    gr_res = sample_grades(cl, d_lo.get("height_grids", []), road_spec.get("max_grade_pct"), opts=opts)
    heights = gr_res["heights_exact"]

    if road_spec.get("is_existing_reuse"):
        matched_id, matched_hw = None, 0.0
        for sid in sorted(graph["main_component"]):
            seg = graph["representatives"][sid]
            if seg.get("elevation_type") != "GROUND":
                continue
            shw, scl = float(seg.get("carriageway_width_m") or 0.0) * 0.5, seg["centerline"]
            if all(_pt_polyline_closest(px, pz, scl, True)[0] <= shw + 1e-6 and (heights[i] is None or _pt_polyline_closest(px, pz, scl, True)[3] is None or abs(heights[i] - _pt_polyline_closest(px, pz, scl, True)[3]) <= ELEV_TOL_M + 1e-9) for i, (px, pz) in enumerate(cl)):
                matched_id, matched_hw = sid, shw
                break
        cw_hw = matched_hw if matched_hw > 0 else 11.0
        cor = build_corridor(cl, cw_hw)
        cor_ok, cor_margin, cor_ids = _cor_margin_ok(rid, cl, cw_hw, d_lo.get("height_grids", []))
        reasons = list(cl_res["reasons"]) + list(gr_res["reasons"])
        if not cor_ok and not opts.get("ignore_cor_margin"):
            reasons.append("COR_MARGIN")
        if matched_id is None:
            reasons.append("EXISTING_SEGMENT_NOT_FOUND")
        state = "EXISTING_VERIFIED" if (not reasons and matched_id is not None) else ("NOT_FEASIBLE" if not cl_res["geometry_ok"] else "UNVERIFIED")
        cnt_new = bool(opts.get("count_u01_as_new"))
        return {
            "id": rid, "kind": road_spec["kind"], "is_existing_reuse": True, "existing": True,
            "matched_existing_segment_id": matched_id, "carriageway_width_m": _r3(cw_hw * 2.0) if matched_id else None,
            "corridor_half_width_m": _r3(cw_hw), "min_radius_m": None, "max_grade_limit_pct": None,
            "centerline_info": {k: v for k, v in cl_res.items() if k != "centerline_exact"},
            "grade_info": {k: v for k, v in gr_res.items() if k != "heights_exact"},
            "corridor_bounds": [_r3(v) for v in cor["bounds"]],
            "cor_margin_ok": cor_ok, "cor_margin_m": cor_margin, "cor_grid_ids": cor_ids,
            "physical_ground_ok": True, "beach_encroachment_m2": _r3(_beach_area_m2(cor, cl, d_lo["world"].get("beach_regions", []))),
            "obstacles": {"blocking": [], "conservative": [], "advisory_street_furniture": [], "junction_overlaps": []},
            "junctions": [], "optional_extension_links": [],
            "new_length_m": cl_res["total_length_m"] if cnt_new else 0.0,
            "new_corridor_area_m2": _r3((cl_res["total_length_m"] or 0.0) * cw_hw * 2.0) if cnt_new else 0.0,
            "geom_corridor_state": state, "state": state, "dependency_chains": [], "reasons": sorted(set(reasons)),
            "_corridor": cor, "_centerline": cl, "_heights": heights, "_handoff": [],
        }

    cw_hw, hw = float(road_spec["carriageway_width_m"]) * 0.5, float(road_spec["corridor_half_width_m"])
    cor = build_corridor(cl, hw)
    cb, steps = cor["bounds"], cor["steps"]
    reasons_nf = list(cl_res["reasons"]) if not cl_res["geometry_ok"] else []
    reasons_unv = ["HEIGHT_MISSING"] if not gr_res["height_ok"] else []
    if not gr_res["grade_ok"]:
        reasons_nf.append("GRADE_LIMIT_EXCEEDED")

    pg = d_lo["world"]["physical_ground"]
    pg_b = tuple(pg["bounds"])
    pg_ok = (pg["verification"] == "RUNTIME_VERIFIED") and (cb[0] >= pg_b[0] - 1e-9 and cb[2] <= pg_b[2] + 1e-9 and cb[1] >= pg_b[1] - 1e-9 and cb[3] <= pg_b[3] + 1e-9)
    if pg["verification"] != "RUNTIME_VERIFIED":
        reasons_unv.append("PHYSICAL_GROUND_UNVERIFIED")
    elif not pg_ok:
        reasons_unv.append("OUTSIDE_PHYSICAL_GROUND")
    for pn in ("PHONE_LOW", "DESKTOP_HIGH"):
        if any(dumps[pn]["completeness"].get(k) in ("PARTIAL", "UNKNOWN") for k in REQ_COMP):
            reasons_unv.append("DATA_INCOMPLETE")
    cor_ok, cor_margin, cor_ids = _cor_margin_ok(rid, cl, hw, d_lo.get("height_grids", []))
    if not cor_ok and not opts.get("ignore_cor_margin"):
        reasons_unv.append("COR_MARGIN")

    junctions, ep_conn, opt_links = _find_existing_connections(rid, cl, heights, cw_hw, graph, opts)
    if any(j["status"] == "UNVERIFIED" and j["reason"] == "JUNCTION_HEIGHT_MISSING" for j in junctions):
        reasons_unv.append("JUNCTION_HEIGHT_MISSING")

    # Map ROAD/SIDEWALK footprint id -> segment_id from corridors_from_graph (verified main component)
    verified_owner = {c["id"]: c.get("segment_id") for c in corridors_from_graph(graph, include_unverified=False)}
    union_fps = _union_fps if _union_fps is not None else _union_footprints(dumps)
    blocking, conservative, advisory, j_overlaps = [], [], [], []
    cl_only = bool(opts.get("centerline_only"))
    start_hits: set[int] = set()
    end_hits: set[int] = set()
    start_fps, end_fps = [], []

    for wp in d_lo["world"].get("water_regions", []):
        wb, wr = poly_bounds(wp), is_axis_rect(wp)
        hit = any(dist_point_to_poly(px, pz, wp) <= 1e-6 for px, pz in cl) if cl_only else bool(_overlapping_step_indices(cor, wp, wr, wb))
        if hit:
            blocking.append({"id": "WATER", "category": "WATER", "precision": "EXACT_OUTLINE"})
            reasons_nf.append("CORRIDOR_WATER")

    for entry in union_fps:
        fp, pts, is_r, fb = entry["fp"], entry["pts"], entry["is_rect"], entry["bounds"]
        if not _bbox_overlaps(cb, fb):
            continue
        if cl_only:
            hit_steps = [i for i, (px, pz) in enumerate(cl[:-1]) if fb[0] <= px <= fb[2] and fb[1] <= pz <= fb[3] and (is_r or dist_point_to_poly(px, pz, pts) <= 1e-6)]
        else:
            hit_steps = _overlapping_step_indices(cor, pts, is_r, fb)
        if not hit_steps:
            continue
        cat, prec, phys, sg = fp["category"], fp.get("geometry_precision"), bool(fp.get("physical")), fp.get("source_group", "")
        if fp.get("protected") or cat == "SITE_A":
            if not opts.get("ignore_site_a"):
                blocking.append({"id": fp["id"], "category": "SITE_A", "precision": prec})
                reasons_nf.append("SITE_A_VIOLATION")
            continue
        if fp.get("verification") == "UNKNOWN":
            conservative.append({"id": fp["id"], "category": cat, "precision": "UNKNOWN"})
            reasons_unv.append("CORRIDOR_UNKNOWN_OBSTACLE")
            continue
        if cat in ("ROAD", "SIDEWALK"):
            owner = verified_owner.get(fp["id"])
            in_s, in_e = owner in ep_conn["START"], owner in ep_conn["END"]
            if in_s or in_e:
                if in_s:
                    start_hits.update(hit_steps)
                    start_fps.append({"id": fp["id"], "segment_id": owner, "category": cat})
                if in_e:
                    end_hits.update(hit_steps)
                    end_fps.append({"id": fp["id"], "segment_id": owner, "category": cat})
            elif any(j["road_b"] == owner and j["status"] == "UNVERIFIED" and j["reason"] == "JUNCTION_HEIGHT_MISSING" for j in junctions):
                reasons_unv.append("JUNCTION_HEIGHT_MISSING")
            else:
                blocking.append({"id": fp["id"], "category": cat, "segment_id": owner, "precision": prec})
                reasons_nf.append("CORRIDOR_BLOCKED_ROAD")
            continue
        if cat == "OTHER" and not phys:
            advisory.append({"id": fp["id"], "source_group": sg})
            continue
        if cat == "BUILDING" and opts.get("ignore_buildings"):
            continue
        is_exact = (prec == "EXACT_OUTLINE") and (cat not in ("TREE", "COLLIDER") or sg in ("PHYSICS_STATIC", "TREE_COLLIDERS"))
        if is_exact or opts.get("conservative_as_not_feasible"):
            blocking.append({"id": fp["id"], "category": cat, "precision": prec, "source_group": sg})
            reasons_nf.append("CORRIDOR_BLOCKED")
        else:
            conservative.append({"id": fp["id"], "category": cat, "precision": prec, "source_group": sg})
            reasons_unv.append("CORRIDOR_CONSERVATIVE_OBSTACLE")

    # D-054a G0-C5: evaluate contiguous single-run <= 100 m from START and END endpoints
    for ep_label, hits, fps_list, anchor in (("START", start_hits, start_fps, 0), ("END", end_hits, end_fps, max(0, len(steps) - 1))):
        if not hits:
            continue
        ok_run, run_len = _check_run_from_anchor(hits, steps, anchor, opts)
        if ok_run:
            j_overlaps.append({"endpoint": ep_label, "kind": "JUNCTION_OVERLAP", "run_length_m": _r3(run_len), "footprints": fps_list})
        else:
            blocking.append({"id": f"JUNCTION_RUN_{ep_label}", "category": "ROAD", "run_length_m": _r3(run_len), "footprints": fps_list})
            reasons_nf.append("CORRIDOR_BLOCKED_ROAD")

    beach_m2 = _beach_area_m2(cor, cl, d_lo["world"].get("beach_regions", []))
    if beach_m2 > 0 and opts.get("beach_as_failure"):
        reasons_nf.append("BEACH_ENCROACHMENT")
    gc_state = "NOT_FEASIBLE" if reasons_nf else ("UNVERIFIED" if reasons_unv else "LEGAL")
    return {
        "id": rid, "kind": road_spec["kind"], "is_existing_reuse": False, "existing": False,
        "matched_existing_segment_id": None, "carriageway_width_m": _r3(road_spec["carriageway_width_m"]),
        "corridor_half_width_m": _r3(hw), "min_radius_m": road_spec["min_radius_m"],
        "max_grade_limit_pct": road_spec["max_grade_pct"],
        "centerline_info": {k: v for k, v in cl_res.items() if k != "centerline_exact"},
        "grade_info": {k: v for k, v in gr_res.items() if k != "heights_exact"},
        "corridor_bounds": [_r3(v) for v in cb],
        "cor_margin_ok": cor_ok, "cor_margin_m": cor_margin, "cor_grid_ids": cor_ids,
        "physical_ground_ok": pg_ok, "beach_encroachment_m2": _r3(beach_m2),
        "obstacles": {"blocking": blocking, "conservative": conservative, "advisory_street_furniture": advisory, "junction_overlaps": j_overlaps},
        "junctions": junctions, "optional_extension_links": opt_links,
        "new_length_m": cl_res["total_length_m"], "new_corridor_area_m2": _r3((cl_res["total_length_m"] or 0.0) * hw * 2.0),
        "geom_corridor_state": gc_state, "state": gc_state, "dependency_chains": [],
        "reasons": sorted(set(reasons_nf + reasons_unv)),
        "_corridor": cor, "_centerline": cl, "_heights": heights, "_handoff": _build_handoff_corridors(rid, cl, hw, opts),
    }


# --- G0-C5/C6/C7: Candidate graph, junctions & dependency chains ---

def _cand_pair_junction(a: dict[str, Any], b: dict[str, Any], opts: dict[str, Any]) -> dict[str, Any] | None:
    cla, clb, ha, hb = a["_centerline"], b["_centerline"], a["_heights"], b["_heights"]
    cwa, cwb = float(a["carriageway_width_m"]) * 0.5, float(b["carriageway_width_m"]) * 0.5
    cl3_a = [[cla[i][0], cla[i][1], ha[i]] for i in range(len(cla))]
    cl3_b = [[clb[i][0], clb[i][1], hb[i]] for i in range(len(clb))]
    cands: list[tuple[float, float, float, float | None, float | None, float]] = []
    for ep, eh in ((cla[0], ha[0]), (cla[-1], ha[-1])):
        dist, _, _, th = _pt_polyline_closest(ep[0], ep[1], cl3_b, False)
        if dist <= cwb + 1.0 + 1e-9:
            cands.append((dist, ep[0], ep[1], eh, th, cwb + 1.0))
    for ep, eh in ((clb[0], hb[0]), (clb[-1], hb[-1])):
        dist, _, _, th = _pt_polyline_closest(ep[0], ep[1], cl3_a, False)
        if dist <= cwa + 1.0 + 1e-9:
            cands.append((dist, ep[0], ep[1], th, eh, cwa + 1.0))
    if not cands:
        for ia in range(len(cla) - 1):
            for ib in range(len(clb) - 1):
                inter = _seg_intersection_pt_xz(cla[ia][0], cla[ia][1], cla[ia + 1][0], cla[ia + 1][1], clb[ib][0], clb[ib][1], clb[ib + 1][0], clb[ib + 1][1])
                if inter is not None:
                    jx, jz, ta, ub = inter
                    cha = None if (ha[ia] is None or ha[ia + 1] is None) else ha[ia] + ta * (ha[ia + 1] - ha[ia])
                    chb = None if (hb[ib] is None or hb[ib + 1] is None) else hb[ib] + ub * (hb[ib + 1] - hb[ib])
                    cands.append((0.0, jx, jz, cha, chb, 0.0))
                    break
            if cands:
                break
    if not cands:
        return None
    dist, jx, jz, cha, chb, thresh = min(cands, key=lambda t: t[0])
    return _make_junc(f"J:{a['id']}<->{b['id']}", "CANDIDATE_TO_CANDIDATE", a["id"], b["id"], (jx, jz), (jx, jz), dist, thresh, cha, chb, opts)


def _nearest_step_index(cl: list[list[float]], pt: list[float]) -> int:
    return min(range(len(cl) - 1), key=lambda i: _pt_seg_closest(pt[0], pt[1], cl[i][0], cl[i][1], cl[i + 1][0], cl[i + 1][1])[0])


def build_candidate_graph(road_results: dict[str, dict[str, Any]], graph: dict[str, Any], opts: dict[str, Any] | None = None) -> dict[str, Any]:
    opts = opts or {}
    c_ids = sorted(rid for rid, r in road_results.items() if not r["is_existing_reuse"])
    cand_juncs, pair_junc, cand_ovl = [], {}, []

    for i, aid in enumerate(c_ids):
        ra = road_results[aid]
        for bid in c_ids[i + 1:]:
            rb = road_results[bid]
            jn = _cand_pair_junction(ra, rb, opts)
            if jn is not None:
                cand_juncs.append(jn)
                pair_junc[(aid, bid)] = jn
                ra["junctions"].append(jn)
                rb["junctions"].append(jn)
            if ra["geom_corridor_state"] == "NOT_FEASIBLE" or rb["geom_corridor_state"] == "NOT_FEASIBLE":
                continue
            ca, cb = ra["_corridor"], rb["_corridor"]
            if not _bbox_overlaps(ca["bounds"], cb["bounds"]):
                continue
            hits_a, hits_b = set(), set()
            for sa in ca["steps"]:
                if not _bbox_overlaps(sa["bounds"], cb["bounds"]):
                    continue
                for sb in cb["steps"]:
                    if _bbox_overlaps(sa["bounds"], sb["bounds"]) and any(_piece_overlaps_poly(pa["polygon"], pa["bounds"], pb["polygon"], False, pb["bounds"]) for pa in sa["pieces"] for pb in sb["pieces"]):
                        hits_a.add(sa["index"])
                        hits_b.add(sb["index"])
            if not hits_a:
                continue
            if jn is not None and jn["status"] == "UNVERIFIED":
                # D-054a: missing height at candidate-to-candidate junction stays UNVERIFIED, never NOT_FEASIBLE
                for rr in (ra, rb):
                    if rr["geom_corridor_state"] == "LEGAL":
                        rr["geom_corridor_state"] = "UNVERIFIED"
                    rr["reasons"] = sorted(set(rr["reasons"] + ["JUNCTION_HEIGHT_MISSING"]))
                continue
            if jn is not None and jn["status"] == "VERIFIED":
                ok_a, len_a = _check_run_from_anchor(hits_a, ca["steps"], _nearest_step_index(ra["_centerline"], jn["point"]), opts)
                ok_b, len_b = _check_run_from_anchor(hits_b, cb["steps"], _nearest_step_index(rb["_centerline"], jn["point"]), opts)
                if ok_a and ok_b:
                    cand_ovl.append({"road_a": aid, "road_b": bid, "kind": "JUNCTION_OVERLAP_CANDIDATE", "junction_id": jn["id"], "run_a_m": _r3(len_a), "run_b_m": _r3(len_b)})
                    continue
            for rr, other in ((ra, bid), (rb, aid)):
                rr["obstacles"]["blocking"].append({"id": other, "category": "CANDIDATE_ROAD", "precision": "EXACT_OUTLINE"})
                rr["reasons"] = sorted(set(rr["reasons"] + ["CORRIDOR_BLOCKED_CANDIDATE"]))
                rr["geom_corridor_state"] = "NOT_FEASIBLE"

    legal_ids = [rid for rid in c_ids if road_results[rid]["geom_corridor_state"] == "LEGAL"]
    adj_cand: dict[str, list[tuple[str, str]]] = {rid: [] for rid in legal_ids}
    direct_ex: dict[str, list[str]] = {rid: [j["id"] for j in road_results[rid]["junctions"] if j["kind"] == "CANDIDATE_TO_EXISTING" and j["status"] == "VERIFIED"] for rid in legal_ids}
    for (aid, bid), jn in pair_junc.items():
        if aid in adj_cand and bid in adj_cand and jn["status"] == "VERIFIED":
            adj_cand[aid].append((bid, jn["id"]))
            adj_cand[bid].append((aid, jn["id"]))

    for rid in c_ids:
        r = road_results[rid]
        if r["geom_corridor_state"] != "LEGAL":
            r["state"], r["dependency_chains"] = r["geom_corridor_state"], []
            continue
        chains: list[list[str]] = []

        def _dfs(cur: str, path: list[str], vis: set[str]) -> None:
            for ej in sorted(direct_ex[cur]):
                chains.append(path + [ej])
            for nb, jid in sorted(adj_cand[cur]):
                if nb not in vis:
                    _dfs(nb, path + [jid, nb], vis | {nb})

        _dfs(rid, [rid], {rid})
        chains.sort(key=lambda ch: (len(ch), ch))
        r["dependency_chains"] = chains
        if chains:
            r["state"] = "EXISTING_VERIFIED" if opts.get("mark_candidate_existing") else "CONDITIONAL_VERIFIED"
        else:
            r["state"] = "UNVERIFIED"
            r["reasons"] = sorted(set(r["reasons"] + ["NO_MAIN_COMPONENT_CHAIN"]))

    return {
        "nodes": {rid: road_results[rid]["state"] for rid in c_ids},
        "existing_connections": {rid: sorted(direct_ex.get(rid, [])) for rid in c_ids},
        "candidate_edges": sorted([a, b, j["id"]] for (a, b), j in pair_junc.items() if j["status"] == "VERIFIED"),
        "candidate_junctions": cand_juncs, "candidate_overlaps": cand_ovl,
        "separate_from_existing_graph": True,
    }


# --- G0-C8: Regional external-access verdicts ---

def _poly_dist_to_rect(pts: list[list[float]], is_rect: bool, b: tuple[float, float, float, float], r: list[float]) -> float:
    if fp_intersects_cell(pts, is_rect, b, r[0], r[1], r[2], r[3])[0]:
        return 0.0
    if is_rect:
        return math.hypot(max(0.0, b[0] - r[2], r[0] - b[2]), max(0.0, b[1] - r[3], r[1] - b[3]))
    r_pts = [[r[0], r[1]], [r[2], r[1]], [r[2], r[3]], [r[0], r[3]]]
    best = min(dist_point_to_poly(px, pz, pts) for px, pz in r_pts)
    return min(best, *(math.hypot(max(0.0, r[0] - px, px - r[2]), max(0.0, r[1] - pz, pz - r[3])) for px, pz in pts))


def evaluate_region_access(
    road_results: dict[str, dict[str, Any]], graph: dict[str, Any],
    dumps: dict[str, dict[str, Any]], scenarios: dict[str, dict[str, list[int]]] | None = None,
    cap_inv: dict[str, Any] | None = None, opts: dict[str, Any] | None = None,
) -> dict[str, Any]:
    opts = opts or {}
    scens = scenarios or SCENARIOS
    ex_cors = corridors_from_graph(graph, include_unverified=False)
    comp_ok = all(all(dumps[pn]["completeness"].get(k) == "COMPLETE" for k in REQ_COMP) for pn in ("PHONE_LOW", "DESKTOP_HIGH"))
    ave0_ok = len(graph.get("main_component", [])) > 0
    out: dict[str, Any] = {}

    for sid, regs in scens.items():
        reg_out: dict[str, Any] = {}
        for rid, b_spec in regs.items():
            rect = spec_to_internal(b_spec)
            rect_poly = [[rect[0], rect[1]], [rect[2], rect[1]], [rect[2], rect[3]], [rect[0], rect[3]]]
            ex_hits = [c["segment_id"] or c["id"] for c in ex_cors if _poly_dist_to_rect(*_fp_polygon(c), rect) <= ACCESS_GAP_M + 1e-9]
            for r_id, rr in sorted(road_results.items()):
                if rr["state"] == "EXISTING_VERIFIED" and any(_poly_dist_to_rect(p["polygon"], False, p["bounds"], rect) <= ACCESS_GAP_M + 1e-9 for p in rr["_corridor"]["pieces"]):
                    ex_hits.append(r_id)
            ex_hits = sorted(set(ex_hits))

            cond_hits, unv_hits, nf_hits = [], [], []
            for r_id, rr in sorted(road_results.items()):
                if not rr["is_existing_reuse"] and _overlapping_step_indices(rr["_corridor"], rect_poly, True, tuple(rect)):
                    if rr["state"] == "CONDITIONAL_VERIFIED":
                        cond_hits.append(r_id)
                    elif rr["state"] == "UNVERIFIED":
                        unv_hits.append(r_id)
                    elif rr["state"] == "NOT_FEASIBLE":
                        nf_hits.append(r_id)

            if opts.get("verdict_from_parcel_counts") and cap_inv is not None:
                c_dir = (((cap_inv.get("scenarios") or {}).get(sid) or {}).get("regions") or {}).get(rid, {}).get("capacities", {}).get("C_direct", 0)
                verdict, reasons = ("FEASIBLE", ["DERIVED_FROM_PARCEL_COUNTS"]) if c_dir > 0 else ("NOT FEASIBLE WITHIN AUDITED BOUNDARIES", ["DERIVED_FROM_PARCEL_COUNTS"])
            elif ex_hits:
                verdict, reasons = "FEASIBLE", ["EXISTING_MAIN_COMPONENT_ACCESS"]
            elif cond_hits:
                verdict, reasons = "CONDITIONAL", ["CONDITIONAL_CANDIDATE_ACCESS"]
            elif nf_hits and not unv_hits and comp_ok and ave0_ok:
                verdict, reasons = "NOT FEASIBLE WITHIN AUDITED BOUNDARIES", sorted({rs for r_id in nf_hits for rs in road_results[r_id]["reasons"]})
            else:
                verdict, reasons = "UNVERIFIED", (["NO_VERIFIED_ACCESS"] if not unv_hits else sorted({rs for r_id in unv_hits for rs in road_results[r_id]["reasons"]}))

            reg_out[rid] = {
                "bounds_spec": list(b_spec), "bounds_internal": rect, "verdict": verdict,
                "C_conditional": C_CONDITIONAL_STATUS, "existing_access_sources": ex_hits,
                "conditional_access_roads": cond_hits, "unverified_roads": unv_hits, "not_feasible_roads": nf_hits,
                "dependency_chains": {r_id: road_results[r_id]["dependency_chains"] for r_id in cond_hits}, "reasons": reasons,
            }
        out[sid] = reg_out
    return out


# --- Top-level analyze & CLI ---

def _validate_capacity_inventory(path: str | Path, dumps: dict[str, dict[str, Any]], opts: dict[str, Any]) -> tuple[dict[str, Any], str]:
    raw = Path(path).read_bytes()
    inv = json.loads(raw.decode("utf-8"))
    if not opts.get("skip_linkage_check"):
        _req(inv.get("base_sha") == dumps["PHONE_LOW"]["metadata"]["base_sha"], "capacity_inventory BASE SHA mismatch")
        _req(inv.get("polygon_revision") == POLYGON_REVISION and inv.get("analyzer_version") == B_VERSION, "capacity_inventory version/polygon mismatch")
        for pn in ("PHONE_LOW", "DESKTOP_HIGH"):
            _req(((inv.get("presets") or {}).get(pn) or {}).get("static_fingerprint") == dumps[pn]["metadata"]["static_fingerprint"], f"capacity_inventory fingerprint mismatch ({pn})")
    return inv, _sha256(raw)


def analyze(
    dump_paths: list[str | Path], out_dir: str | Path | None = None,
    capacity_inventory_path: str | Path | None = None, opts: dict[str, Any] | None = None,
) -> dict[str, Any]:
    opts = opts or {}
    if opts.get("skip_fingerprint_check"):
        dumps = {d["metadata"]["preset"]: d for d in (json.loads(Path(p).read_text(encoding="utf-8")) for p in dump_paths)}
    else:
        try:
            dumps = load_dumps(dump_paths, opts=opts)
        except Exception as exc:
            raise RoadError(f"Dump loading/validation failed: {exc}") from exc

    cap_inv, cap_sha = _validate_capacity_inventory(capacity_inventory_path, dumps, opts) if capacity_inventory_path is not None else (None, None)
    d_lo, d_hi = dumps["PHONE_LOW"], dumps["DESKTOP_HIGH"]
    base_sha = d_lo["metadata"]["base_sha"]
    graph_lo, graph_hi = build_road_graph(d_lo), build_road_graph(d_hi)
    road_specs, union_fps = opts.get("roads") or CANDIDATE_ROADS, _union_footprints(dumps)

    road_results = {rid: evaluate_road(spec, dumps, graph_lo, opts=opts, _union_fps=union_fps) for rid, spec in sorted(road_specs.items())}
    cand_graph = build_candidate_graph(road_results, graph_lo, opts=opts)
    reg_verdicts = evaluate_region_access(road_results, graph_lo, dumps, scenarios=opts.get("scenarios"), cap_inv=cap_inv, opts=opts)

    cand_corridors, excluded_roads, roads_out = [], {}, {}
    tot_new_len = tot_new_area = tot_beach = 0.0
    for rid, rr in sorted(road_results.items()):
        roads_out[rid] = {k: v for k, v in rr.items() if not k.startswith("_")}
        tot_new_len += float(rr["new_length_m"] or 0.0)
        tot_new_area += float(rr["new_corridor_area_m2"] or 0.0)
        tot_beach += float(rr["beach_encroachment_m2"] or 0.0)
        if rr["state"] == "CONDITIONAL_VERIFIED":
            cand_corridors.extend(rr["_handoff"])
        elif rr["state"] != "EXISTING_VERIFIED":
            excluded_roads[rid] = {"state": rr["state"], "reasons": rr["reasons"]}

    compat = {
        "base_sha": base_sha, "phone_low_static_fingerprint": d_lo["metadata"]["static_fingerprint"],
        "desktop_high_static_fingerprint": d_hi["metadata"]["static_fingerprint"],
        "we01a_analyzer_version": WE01A_COMPAT_VERSION, "t016b_analyzer_version": B_VERSION,
        "schema_version": 1, "road_schema_version": ROAD_SCHEMA_VERSION, "polygon_revision": POLYGON_REVISION,
    }
    survey = {
        "schema_version": 1, "road_schema_version": ROAD_SCHEMA_VERSION,
        "analyzer_version": ANALYZER_VERSION, "t016b_analyzer_version": B_VERSION,
        "polygon_revision": POLYGON_REVISION, "base_sha": base_sha,
        "C_conditional": C_CONDITIONAL_STATUS, "compatibility_key": compat,
        "presets": {p: {"static_fingerprint": dumps[p]["metadata"]["static_fingerprint"], "file_sha256": dumps[p].get("_file_sha256")} for p in ("PHONE_LOW", "DESKTOP_HIGH")},
        "t016b_source": {"path": str(capacity_inventory_path) if capacity_inventory_path else None, "sha256": cap_sha},
        "existing_road_graph": {k: v for k, v in graph_lo.items() if k not in ("representatives", "corridors_all")},
        "existing_road_graph_desktop_high_main_count": graph_hi["dedup_main_component_count"],
        "candidate_road_graph": cand_graph,
        "summary": {
            "road_ids": sorted(roads_out), "states": {rid: roads_out[rid]["state"] for rid in sorted(roads_out)},
            "total_new_road_length_m": _r3(tot_new_len), "total_new_corridor_area_m2": _r3(tot_new_area),
            "total_beach_encroachment_m2": _r3(tot_beach),
        },
        "roads": roads_out, "candidate_corridors": cand_corridors,
        "excluded_roads": excluded_roads, "regional_access": reg_verdicts,
        "limitations": ["External road access survey only; internal streets, conditional capacity (C_conditional=PENDING_T016D), and final residential feasibility verdicts are deferred to T-016D.", "AVE110_EXTENSION_REQUIRED optional link is never generated or verified here."],
    }
    if out_dir is not None:
        od = Path(out_dir)
        od.mkdir(parents=True, exist_ok=True)
        (od / "road_survey.json").write_text(json.dumps(survey, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return survey


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="WE-01C (T-016C) Road Feasibility Survey (read-only audit tool).")
    ap.add_argument("--dump", action="append", required=True, help="Runtime dump JSON path (PHONE_LOW & DESKTOP_HIGH).")
    ap.add_argument("--out", required=True, help="Output directory for road_survey.json.")
    ap.add_argument("--capacity-inventory", default=None, help="Optional T-016B capacity_inventory.json.")
    args = ap.parse_args(argv)
    try:
        analyze(args.dump, out_dir=args.out, capacity_inventory_path=args.capacity_inventory)
    except RoadError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
