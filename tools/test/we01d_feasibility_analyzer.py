#!/usr/bin/env python3
"""WE-01D (T-016D) Internal Streets, Conditional Capacity & Feasibility Verdicts (read-only audit tooling)."""
from __future__ import annotations

import argparse
from bisect import bisect_left
import hashlib
import json
import math
from pathlib import Path
import sys
import time
from typing import Any, Callable

sys.path.insert(0, str(Path(__file__).resolve().parent))
from we01a_land_analyzer import (  # noqa: E402
    clip_poly_to_rect, compute_static_fingerprint, dist_point_to_poly, fp_intersects_cell,
    is_axis_rect, poly_area, poly_bounds, sample_height, validate_dump,
)
from we01b_capacity_analyzer import (  # noqa: E402
    ANALYZER_VERSION as B_VERSION, POLYGON_REVISION, PROTOTYPES, REGION_RULES, SCENARIOS,
    _band, _build_region_triplet, _combine_masks, _slice_masks, _slice_valid_mask, _verify_layout,
    build_masks, build_road_graph, check_ratio, common_layout, corridors_from_graph,
    evaluate_access, geom_valid, internal_to_spec, load_dumps, place_layout, spec_to_internal,
)
from we01c_road_analyzer import (  # noqa: E402
    ANALYZER_VERSION as C_VERSION, CANDIDATE_ROADS, build_candidate_graph,
    evaluate_region_access, evaluate_road,
)

ANALYZER_VERSION = "we01d-1.0"
FEASIBILITY_SCHEMA_VERSION = 1
WE01A_COMPAT_VERSION = "we01a-1.0"
STREET_CW_M = 7.0
STREET_HW_M = 5.5
STREET_MAX_GRADE_PCT = 6.0
STREET_START_STEP_M = 25.0
STREET_LENGTHS = (30, 60, 90, 120, 150)
STREET_JUNCTION_MAX_RUN_M = 30.0
MAX_STREETS_PER_REGION = 3
CANDIDATE_BUDGET = 1280
TIER2_VERIFY_LIMIT = 24
TARGET_AREA_M2 = 250000.0
CONSERVATION_TOL_M2 = 1.0
VERDICT_NOT_FEASIBLE = "NOT FEASIBLE WITHIN AUDITED BOUNDARIES"
VERDICT_PRIORITY = {"FEASIBLE": 0, "CONDITIONAL": 1, "UNVERIFIED": 2, VERDICT_NOT_FEASIBLE: 3}


class FeasibilityError(ValueError):
    """Raised on input linkage, direct-layout mismatch, or conservation errors."""


def _req(cond: bool, msg: str) -> None:
    if not cond:
        raise FeasibilityError(msg)


def _r3(val: float | None) -> float | None:
    return None if val is None else round(float(val), 3)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _det_hash(obj: dict[str, Any]) -> str:
    return _sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def _worst_verdict(verdicts: list[str]) -> str:
    return max(verdicts, key=lambda v: VERDICT_PRIORITY[v]) if verdicts else "UNVERIFIED"


# --- Geometry & raster helpers ---

def _ensure_ccw(pts: list[list[float]]) -> list[list[float]]:
    s = sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))
    return pts if s >= 0.0 else list(reversed(pts))


def _bbox_overlaps(a: tuple[float, float, float, float], b: tuple[float, float, float, float], pad: float = 0.0) -> bool:
    return a[2] >= b[0] - pad and b[2] >= a[0] - pad and a[3] >= b[1] - pad and b[3] >= a[1] - pad


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


def _poly_overlaps_poly(a_pts: list[list[float]], a_b: tuple[float, float, float, float], b_pts: list[list[float]], b_rect: bool, b_b: tuple[float, float, float, float]) -> bool:
    if not _bbox_overlaps(a_b, b_b):
        return False
    clipped = clip_poly_to_rect(a_pts, b_b[0], b_b[1], b_b[2], b_b[3]) if b_rect else _clip_poly_by_convex(b_pts, _ensure_ccw(a_pts))
    return len(clipped) >= 3 and poly_area(clipped) > 1e-6


def _corridor_overlaps_box(cor: dict[str, Any], box: tuple[float, float, float, float]) -> bool:
    pts = cor["polygon"]
    b = tuple(cor["bounds"])
    if not _bbox_overlaps(b, box):
        return False
    hit, area = fp_intersects_cell(pts, cor.get("is_rect", is_axis_rect(pts)), b, box[0], box[1], box[2], box[3])
    return hit and area > 1e-6


def _street_rect_poly(sx: float, sz: float, ex: float, ez: float, hw: float = STREET_HW_M) -> tuple[list[list[float]], bool, tuple[float, float, float, float]]:
    dx, dz = ex - sx, ez - sz
    ds = math.hypot(dx, dz)
    nx, nz = (-dz / ds * hw, dx / ds * hw) if ds > 1e-9 else (hw, 0.0)
    pts = _ensure_ccw([[sx - nx, sz - nz], [ex - nx, ez - nz], [ex + nx, ez + nz], [sx + nx, sz + nz]])
    return pts, is_axis_rect(pts), poly_bounds(pts)


def _street_corridor_dict(street_id: str, sx: float, sz: float, ex: float, ez: float, existing: bool = False) -> dict[str, Any]:
    pts, is_r, b = _street_rect_poly(sx, sz, ex, ez, STREET_HW_M)
    pts_r = [[_r3(p[0]), _r3(p[1])] for p in pts]
    return {
        "id": street_id, "segment_id": street_id, "category": "ROAD",
        "source_group": "INTERNAL_STREETS", "polygon": pts_r, "bounds": [_r3(v) for v in b],
        "is_rect": is_r, "connectivity": "VERIFIED", "existing": existing, "is_roundabout": False,
    }


def _bor_bytes(a: bytearray, b: bytearray) -> bytearray:
    return bytearray((int.from_bytes(a, "little") | int.from_bytes(b, "little")).to_bytes(len(a), "little"))


def _bnot_bytes(a: bytearray) -> bytearray:
    return bytearray(a.translate(_FLIP_01))


_FLIP_01 = bytes.maketrans(b"\x00\x01", b"\x01\x00")


def _vert_any_to_cell(vbuf: bytearray, w: int, h: int) -> bytearray:
    out = bytearray(w * h)
    if vbuf.find(1) == -1:
        return out
    vw = w + 1
    prev = _bor_bytes(vbuf[:w], vbuf[1:w + 1])
    for iz in range(h):
        vr1 = (iz + 1) * vw
        cur = _bor_bytes(vbuf[vr1:vr1 + w], vbuf[vr1 + 1:vr1 + w + 1])
        out[iz * w:(iz + 1) * w] = _bor_bytes(prev, cur)
        prev = cur
    return out


def _paint_corridors_to_mask(buf: bytearray, x0: int, z0: int, w: int, h: int, cors: list[dict[str, Any]]) -> None:
    for c in cors:
        pts, b = c["polygon"], tuple(c["bounds"])
        is_r = bool(c["is_rect"]) if "is_rect" in c else is_axis_rect(pts)
        if b[2] < x0 or b[0] > x0 + w or b[3] < z0 or b[1] > z0 + h:
            continue
        iz0, iz1 = max(0, math.floor(b[1]) - z0), min(h - 1, math.floor(b[3]) - z0)
        if is_r:
            ix0 = max(0, math.floor(b[0]) - x0)
            ix1 = min(w - 1, math.ceil(b[2]) - 1 - x0)
            if ix1 < ix0:
                continue
            span = b"\x01" * (ix1 - ix0 + 1)
            for iz in range(iz0, iz1 + 1):
                if min(z0 + iz + 1, b[3]) - max(z0 + iz, b[1]) <= 1e-6:
                    continue
                row = iz * w
                if min(x0 + ix0 + 1, b[2]) - max(x0 + ix0, b[0]) > 1e-6 and min(x0 + ix1 + 1, b[2]) - max(x0 + ix1, b[0]) > 1e-6:
                    buf[row + ix0:row + ix1 + 1] = span
                else:
                    for ix in range(ix0, ix1 + 1):
                        if min(x0 + ix + 1, b[2]) - max(x0 + ix, b[0]) > 1e-6:
                            buf[row + ix] = 1
            continue
        edges = [(pts[i], pts[(i + 1) % len(pts)]) for i in range(len(pts))]
        for iz in range(iz0, iz1 + 1):
            za, zb = z0 + iz, z0 + iz + 1
            xs_hit: list[float] = []
            for p0, p1 in edges:
                if za <= p0[1] <= zb:
                    xs_hit.append(p0[0])
                dz = p1[1] - p0[1]
                if abs(dz) > 1e-12:
                    for zv in (za, zb):
                        t = (zv - p0[1]) / dz
                        if 0.0 <= t <= 1.0:
                            xs_hit.append(p0[0] + t * (p1[0] - p0[0]))
            if not xs_hit:
                continue
            ix0 = max(0, math.floor(min(xs_hit)) - x0)
            ix1 = min(w - 1, math.floor(max(xs_hit)) - x0)
            row = iz * w
            for ix in range(ix0, ix1 + 1):
                hit, oa = fp_intersects_cell(pts, False, b, x0 + ix, za, x0 + ix + 1, zb)
                if hit and oa > 1e-6:
                    buf[row + ix] = 1


def _mask_out_corridors_from_vm(vm: Any, cors: list[dict[str, Any]]) -> Any:
    if not cors or vm.find(1) == -1:
        return vm
    out = type(vm)(len(vm), vm.x0, vm.z0, vm.w, vm.h, vm.pw, vm.ph, vm.proto_id, vm.orientation)
    out[:] = vm
    hw, hh, x0, z0, w, h = vm.pw // 2, vm.ph // 2, vm.x0, vm.z0, vm.w, vm.h
    for c in cors:
        pts, is_r, b = c["polygon"], c.get("is_rect", is_axis_rect(c["polygon"])), tuple(c["bounds"])
        ix0, ix1 = max(0, math.floor(b[0] - hw) - x0), min(w - 1, math.ceil(b[2] + hw) - x0)
        iz0, iz1 = max(0, math.floor(b[1] - hh) - z0), min(h - 1, math.ceil(b[3] + hh) - z0)
        for iz in range(iz0, iz1 + 1):
            row, cz = iz * w, z0 + iz
            for ix in range(ix0, ix1 + 1):
                if out[row + ix]:
                    cx = x0 + ix
                    hit, oa = fp_intersects_cell(pts, is_r, b, cx - hw, cz - hh, cx + hw, cz + hh)
                    if hit and oa > 1e-6:
                        out[row + ix] = 0
    return out


# --- G0-D2: Input validation & linkage ---

def load_and_verify_inputs(
    dump_paths: list[str | Path], capacity_inventory_path: str | Path,
    parcel_candidates_path: str | Path, road_survey_path: str | Path,
    opts: dict[str, Any] | None = None,
) -> dict[str, Any]:
    opts = opts or {}
    if opts.get("skip_fingerprint_check"):
        dumps = {d["metadata"]["preset"]: d for d in (json.loads(Path(p).read_text(encoding="utf-8")) for p in dump_paths)}
    else:
        try:
            dumps = load_dumps(dump_paths, opts=opts)
        except Exception as exc:
            raise FeasibilityError(f"Dump loading/validation failed: {exc}") from exc

    base_sha = dumps["PHONE_LOW"]["metadata"]["base_sha"]
    fp_lo = dumps["PHONE_LOW"]["metadata"]["static_fingerprint"]
    fp_hi = dumps["DESKTOP_HIGH"]["metadata"]["static_fingerprint"]
    exp_hashes = opts.get("expected_artifact_hashes") or {}

    def _read_art(key: str, path: str | Path, exp_ver: str, schema_field: str) -> tuple[dict[str, Any], str]:
        raw = Path(path).read_bytes()
        sha = _sha256(raw)
        if key in exp_hashes:
            _req(sha == exp_hashes[key], f"Declared {key} SHA-256 mismatch")
        obj = json.loads(raw.decode("utf-8"))
        if not opts.get("skip_linkage_check"):
            _req(obj.get("analyzer_version") == exp_ver, f"{key} analyzer_version mismatch: {obj.get('analyzer_version')} != {exp_ver}")
            _req(obj.get("schema_version") == 1 and obj.get(schema_field) == 1, f"{key} schema version mismatch")
            _req(obj.get("base_sha") == base_sha and obj.get("polygon_revision") == POLYGON_REVISION, f"{key} BASE/polygon mismatch")
            ck = obj.get("compatibility_key") or {}
            _req(ck.get("base_sha") == base_sha and ck.get("phone_low_static_fingerprint") == fp_lo and ck.get("desktop_high_static_fingerprint") == fp_hi, f"{key} compatibility_key mismatch")
            ps = obj.get("presets") or {}
            _req((ps.get("PHONE_LOW") or {}).get("static_fingerprint") == fp_lo and (ps.get("DESKTOP_HIGH") or {}).get("static_fingerprint") == fp_hi, f"{key} preset fingerprint mismatch")
        return obj, sha

    cap_inv, cap_sha = _read_art("capacity_inventory", capacity_inventory_path, B_VERSION, "handoff_schema_version")
    par_cand, par_sha = _read_art("parcel_candidates", parcel_candidates_path, B_VERSION, "handoff_schema_version")
    road_svy, road_sha = _read_art("road_survey", road_survey_path, C_VERSION, "road_schema_version")
    return {
        "dumps": dumps, "base_sha": base_sha, "fp_lo": fp_lo, "fp_hi": fp_hi,
        "capacity_inventory": cap_inv, "parcel_candidates": par_cand, "road_survey": road_svy,
        "hashes": {"capacity_inventory_sha256": cap_sha, "parcel_candidates_sha256": par_sha, "road_survey_sha256": road_sha},
    }


# --- G0-D3 & G0-D4: Legal source extraction & deterministic candidate generation ---

def _extract_sources(graph: dict[str, Any], road_survey: dict[str, Any], excluded_road_ids: set[str], opts: dict[str, Any]) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    reps = graph["representatives"]
    ex_cor_by_seg: dict[str, list[dict[str, Any]]] = {}
    for c in corridors_from_graph(graph, include_unverified=False):
        sid = c.get("segment_id")
        if sid:
            ex_cor_by_seg.setdefault(sid, []).append(c)

    # 1. Existing VERIFIED GROUND segments in AVE_0 main component
    for seg_id in sorted(graph["main_component"]):
        seg = reps.get(seg_id)
        if not seg or seg.get("elevation_type") != "GROUND" or seg.get("verification") == "UNKNOWN":
            continue
        cl2 = [[float(p[0]), float(p[2])] for p in seg["centerline"]]
        if len(cl2) >= 2:
            sources.append({
                "id": seg_id, "source_type": "EXISTING_ROAD", "centerline": cl2,
                "carriageway_width_m": float(seg.get("carriageway_width_m") or 0.0),
                "corridors": ex_cor_by_seg.get(seg_id, []), "dependency_chains": [[]],
                "beach_encroachment_m2": 0.0,
            })

    # 2. T-016C CONDITIONAL_VERIFIED roads (chosen purely by state, never by id)
    cand_cor_by_seg: dict[str, list[dict[str, Any]]] = {}
    for c in road_survey.get("candidate_corridors", []):
        cand_cor_by_seg.setdefault(c["segment_id"], []).append(c)
    roads_map = road_survey.get("roads") or {}
    allow_unver_src = bool(opts.get("allow_unverified_sources"))
    for rid in sorted(roads_map):
        r = roads_map[rid]
        if rid in excluded_road_ids:
            continue
        if r.get("is_existing_reuse"):
            continue
        st = r.get("state")
        if st != "CONDITIONAL_VERIFIED" and not (allow_unver_src and st in ("NOT_FEASIBLE", "UNVERIFIED")):
            continue
        valid_chains = [ch for ch in (r.get("dependency_chains") or []) if not any(tok in excluded_road_ids for tok in ch)]
        if st == "CONDITIONAL_VERIFIED" and not valid_chains and not opts.get("drop_dependency_chains"):
            continue
        cl = [[float(p[0]), float(p[1])] for p in (r.get("centerline_info") or {}).get("centerline", [])]
        if len(cl) >= 2:
            sources.append({
                "id": rid, "source_type": "CONDITIONAL_ROAD", "centerline": cl,
                "carriageway_width_m": float(r.get("carriageway_width_m") or STREET_CW_M),
                "corridors": cand_cor_by_seg.get(rid, []),
                "dependency_chains": valid_chains or [[]],
                "beach_encroachment_m2": float(r.get("beach_encroachment_m2") or 0.0),
            })
    sources.sort(key=lambda s: s["id"])
    return sources


def _sample_polyline_starts(cl: list[list[float]], step_m: float = STREET_START_STEP_M) -> list[tuple[float, float, float, float, float]]:
    """Return [(dist, sx, sz, tx, tz)] every step_m from start plus final endpoint (once)."""
    cum = [0.0]
    for i in range(len(cl) - 1):
        cum.append(cum[-1] + math.hypot(cl[i + 1][0] - cl[i][0], cl[i + 1][1] - cl[i][1]))
    total = cum[-1]
    if total <= 1e-9:
        return []
    dists = []
    d = 0.0
    while d < total - 1e-6:
        dists.append(d)
        d += step_m
    dists.append(total)
    out = []
    seg_i = 0
    for target in dists:
        while seg_i < len(cl) - 2 and cum[seg_i + 1] < target - 1e-9:
            seg_i += 1
        a, b = cl[seg_i], cl[seg_i + 1]
        slen = cum[seg_i + 1] - cum[seg_i]
        if slen <= 1e-9:
            continue
        t = max(0.0, min(1.0, (target - cum[seg_i]) / slen))
        sx, sz = a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])
        tx, tz = (b[0] - a[0]) / slen, (b[1] - a[1]) / slen
        out.append((target, sx, sz, tx, tz))
    return out


def generate_street_candidates(
    sources: list[dict[str, Any]], reg_rect: list[int],
    scenario_id: str, region_id: str, opts: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], int, bool]:
    opts = opts or {}
    rx0, rz0, rx1, rz1 = reg_rect
    lengths = tuple(opts.get("street_lengths", STREET_LENGTHS))
    budget = int(opts.get("candidate_budget", CANDIDATE_BUDGET))
    allow_outside_start = bool(opts.get("allow_outside_start"))
    seen_keys: set[tuple[Any, ...]] = set()
    cands: list[dict[str, Any]] = []
    for src in sorted(sources, key=lambda s: s["id"]):
        starts = _sample_polyline_starts(src["centerline"], STREET_START_STEP_M)
        for dist_m, sx, sz, tx, tz in starts:
            if not allow_outside_start and not (rx0 - 1e-9 <= sx <= rx1 + 1e-9 and rz0 - 1e-9 <= sz <= rz1 + 1e-9):
                continue
            for side_idx, (side_name, dx, dz) in enumerate((("LEFT", -tz, tx), ("RIGHT", tz, -tx))):
                for length in lengths:
                    dkey = (round(sx, 2), round(sz, 2), round(dx, 3), round(dz, 3), int(length))
                    if dkey in seen_keys:
                        continue
                    seen_keys.add(dkey)
                    ex, ez = sx + dx * length, sz + dz * length
                    cands.append({
                        "street_id": f"{scenario_id}_{region_id}_ST_{len(cands) + 1:04d}",
                        "order_index": len(cands), "source_road_id": src["id"],
                        "source_type": src["source_type"], "source": src,
                        "distance_along_source_m": _r3(dist_m), "side": side_name, "side_order": side_idx,
                        "length_m": int(length), "start": [sx, sz], "end": [ex, ez], "dir": [dx, dz],
                    })
    total_filtered = len(cands)
    exhausted = total_filtered > budget
    return cands[:budget], total_filtered, exhausted


# --- G0-D5 & G0-D6: Two-tier internal street legality ---

def _street_steps(sx: float, sz: float, ex: float, ez: float, hw: float = STREET_HW_M) -> list[dict[str, Any]]:
    dx, dz = ex - sx, ez - sz
    dist = math.hypot(dx, dz)
    n = max(1, math.ceil(dist / 3.0))
    ds = dist / n
    nx, nz = (-dz / dist * hw, dx / dist * hw) if dist > 1e-9 else (hw, 0.0)
    is_r = abs(dx) < 1e-9 or abs(dz) < 1e-9
    steps = []
    for i in range(n):
        t0, t1 = i / n, (i + 1) / n
        ax, az, bx, bz = sx + dx * t0, sz + dz * t0, sx + dx * t1, sz + dz * t1
        p0, p1, p2, p3 = [ax - nx, az - nz], [bx - nx, bz - nz], [bx + nx, bz + nz], [ax + nx, az + nz]
        poly = _ensure_ccw([p0, p1, p2, p3])
        pb = (min(p0[0], p1[0], p2[0], p3[0]), min(p0[1], p1[1], p2[1], p3[1]), max(p0[0], p1[0], p2[0], p3[0]), max(p0[1], p1[1], p2[1], p3[1]))
        steps.append({"index": i, "length_m": ds, "polygon": poly, "is_rect": is_r, "bounds": pb, "a": [ax, az], "b": [bx, bz]})
    return steps


def _check_street_junction_and_bounds(
    cand: dict[str, Any], steps: list[dict[str, Any]], reg_rect: list[int],
    other_cors: list[dict[str, Any]], opts: dict[str, Any],
    full_b: tuple[float, float, float, float] | None = None,
) -> tuple[bool, float, bool, int, str | None]:
    """G0-D6: contiguous source-overlap run from step 0 <= 30 m; post-run inside closed reg_rect; no other road overlap."""
    if full_b is None:
        _, _, full_b = _street_rect_poly(cand["start"][0], cand["start"][1], cand["end"][0], cand["end"][1], STREET_HW_M)
    near_src = []
    for c in cand["source"]["corridors"]:
        cb = tuple(c["bounds"])
        if _bbox_overlaps(full_b, cb):
            near_src.append((c["polygon"], bool(c["is_rect"]) if "is_rect" in c else is_axis_rect(c["polygon"]), cb))
    max_run = float(opts.get("street_junction_max_run_m", STREET_JUNCTION_MAX_RUN_M))
    src_hits = [st["index"] for st in steps if any(_poly_overlaps_poly(st["polygon"], st["bounds"], cp, cr, cb) for cp, cr, cb in near_src)]
    run_len = sum(steps[i]["length_m"] for i in src_hits)
    if src_hits:
        if src_hits != list(range(len(src_hits))) and not opts.get("accept_reentry"):
            return False, run_len, False, 0, "STREET_JUNCTION_REENTRY"
        if run_len > max_run + 1e-9:
            return False, run_len, False, 0, "STREET_JUNCTION_RUN_EXCEEDED"
    post_start = len(src_hits)
    rx0, rz0, rx1, rz1 = reg_rect
    ext_outside = any(steps[i]["bounds"][0] < rx0 - 1e-9 or steps[i]["bounds"][2] > rx1 + 1e-9 or steps[i]["bounds"][1] < rz0 - 1e-9 or steps[i]["bounds"][3] > rz1 + 1e-9 for i in range(post_start))
    if post_start >= len(steps):
        return False, run_len, ext_outside, post_start, "STREET_ENTIRELY_IN_JUNCTION"
    for st in steps[post_start:]:
        sb = st["bounds"]
        if sb[0] < rx0 - 1e-9 or sb[2] > rx1 + 1e-9 or sb[1] < rz0 - 1e-9 or sb[3] > rz1 + 1e-9:
            return False, run_len, ext_outside, post_start, "STREET_OUTSIDE_REGION"
    # Check no overlap with OTHER roads/sidewalks (beyond own source junction run)
    for oc in other_cors:
        ob = tuple(oc["bounds"])
        if _bbox_overlaps(full_b, ob):
            o_rect = bool(oc["is_rect"]) if "is_rect" in oc else is_axis_rect(oc["polygon"])
            if any(_poly_overlaps_poly(st["polygon"], st["bounds"], oc["polygon"], o_rect, ob) for st in steps[post_start:]):
                return False, run_len, ext_outside, post_start, "STREET_OVERLAPS_OTHER_ROAD"
    return True, run_len, ext_outside, post_start, None


def _tier1_check_street(
    cand: dict[str, Any], m_com: Any, reg_rect: list[int],
    seed_boxes: list[tuple[int, int, int, int]], sel_cors: list[dict[str, Any]],
    other_cors: list[dict[str, Any]], beach_regions: list[list[list[float]]],
    opts: dict[str, Any],
) -> tuple[bool, dict[str, Any]]:
    sx, sz = cand["start"]
    ex, ez = cand["end"]
    cor_dict = _street_corridor_dict(cand["street_id"], sx, sz, ex, ez, existing=False)
    full_pts, is_axis, full_b = cor_dict["polygon"], cor_dict["is_rect"], tuple(cor_dict["bounds"])

    # Direct parcel conflict check (G0-D7)
    if not opts.get("allow_street_seed_overlap"):
        for sb in seed_boxes:
            if _corridor_overlaps_box(cor_dict, sb):
                return False, {"reason": "DIRECT_PARCEL_CONFLICT"}
    # Selected street overlap check
    for sc in sel_cors:
        if _poly_overlaps_poly(full_pts, full_b, sc["polygon"], sc["is_rect"], tuple(sc["bounds"])):
            return False, {"reason": "SELECTED_STREET_OVERLAP"}

    steps = _street_steps(sx, sz, ex, ez, STREET_HW_M)
    ok_jb, run_len, ext_out, post_i, jb_err = _check_street_junction_and_bounds(cand, steps, reg_rect, other_cors, opts, full_b=full_b)
    if not ok_jb:
        return False, {"reason": jb_err}

    # Beach check (G0-D5: streets must not use beach unless mutated)
    if beach_regions and not opts.get("accept_beach_street"):
        for bp in beach_regions:
            bb = poly_bounds(bp)
            if _poly_overlaps_poly(full_pts, full_b, bp, is_axis_rect(bp), bb):
                return False, {"reason": "BEACH_ENCROACHMENT_NOT_APPROVED"}

    # Post-run polygon for raster check on m_com (B masks: blocked / unknown / S1-S4 / outside physical support)
    pa, pb = steps[post_i]["a"], steps[-1]["b"]
    post_pts, post_axis, post_b = _street_rect_poly(pa[0], pa[1], pb[0], pb[1], STREET_HW_M)
    if not opts.get("ignore_street_obstacles"):
        if post_axis:
            ix0, iz0 = math.floor(post_b[0]), math.floor(post_b[1])
            ix1, iz1 = math.ceil(post_b[2]), math.ceil(post_b[3])
            if m_com.rect_blocked(ix0, iz0, ix1, iz1) != 0:
                return False, {"reason": "TIER1_BLOCKED_OR_UNKNOWN"}
            if not opts.get("ignore_street_grade"):
                if m_com.vert_sum(m_com.ps_v_unknown, ix0, iz0, ix1, iz1) != 0 or m_com.vert_sum(m_com.ps_v_s1_3, ix0, iz0, ix1, iz1) != 0 or m_com.vert_sum(m_com.ps_v_s4, ix0, iz0, ix1, iz1) != 0:
                    return False, {"reason": "TIER1_SLOPE_OR_HEIGHT"}
        else:
            x0, z0, w, vw = m_com.x0, m_com.z0, m_com.w, m_com.w + 1
            ix0, ix1 = max(0, math.floor(post_b[0]) - x0), min(w - 1, math.floor(post_b[2]) - x0)
            iz0, iz1 = max(0, math.floor(post_b[1]) - z0), min(m_com.h - 1, math.floor(post_b[3]) - z0)
            for iz in range(iz0, iz1 + 1):
                row, vr0, vr1 = iz * w, iz * vw, (iz + 1) * vw
                for ix in range(ix0, ix1 + 1):
                    hit, oa = fp_intersects_cell(post_pts, False, post_b, x0 + ix, z0 + iz, x0 + ix + 1, z0 + iz + 1)
                    if not (hit and oa > 1e-6):
                        continue
                    if not m_com.base_free[row + ix]:
                        return False, {"reason": "TIER1_BLOCKED_OR_UNKNOWN"}
                    if not opts.get("ignore_street_grade"):
                        if (m_com.v_unknown[vr0 + ix] or m_com.v_unknown[vr0 + ix + 1] or m_com.v_unknown[vr1 + ix] or m_com.v_unknown[vr1 + ix + 1]
                                or m_com.v_s1_3[vr0 + ix] or m_com.v_s1_3[vr0 + ix + 1] or m_com.v_s1_3[vr1 + ix] or m_com.v_s1_3[vr1 + ix + 1]
                                or m_com.v_s4[vr0 + ix] or m_com.v_s4[vr0 + ix + 1] or m_com.v_s4[vr1 + ix] or m_com.v_s4[vr1 + ix + 1]):
                            return False, {"reason": "TIER1_SLOPE_OR_HEIGHT"}

    return True, {
        "corridor": cor_dict, "steps": steps, "junction_run_m": _r3(run_len),
        "external_connection_outside_region": ext_out, "post_start_idx": post_i,
    }


def _make_street_dumps(dumps: dict[str, dict[str, Any]], region_id: str, reg_rect: list[int]) -> dict[str, dict[str, Any]]:
    """Shallow view adding region_id 1 m grid as ROAD_CORRIDOR and culling footprints > 50 m outside reg_rect."""
    rb = tuple(reg_rect)
    out = {}
    for pn, d in dumps.items():
        extra = [dict(g, region_id="ROAD_CORRIDOR") for g in d.get("height_grids", []) if g.get("region_id") == region_id and abs(float(g.get("step_m", 0)) - 1.0) < 1e-6]
        fps = [fp for fp in d.get("footprints", []) if _bbox_overlaps(tuple(fp["bounds"]), rb, pad=50.0)]
        out[pn] = dict(d, height_grids=list(d.get("height_grids", [])) + extra, footprints=fps)
    return out


def _tier2_verify_street(
    cand: dict[str, Any], t1_info: dict[str, Any], street_dumps: dict[str, dict[str, Any]],
    graph: dict[str, Any], opts: dict[str, Any],
) -> tuple[bool, dict[str, Any]]:
    road_spec = {
        "id": cand["street_id"], "kind": "NORMAL",
        "control_points": [cand["start"], cand["end"]],
        "carriageway_width_m": STREET_CW_M, "corridor_half_width_m": STREET_HW_M,
        "min_radius_m": 25.0, "max_grade_pct": STREET_MAX_GRADE_PCT, "is_existing_reuse": False,
    }
    c_opts = {}
    if opts.get("ignore_street_grade"):
        c_opts["ignore_grade_limit"] = True
    if opts.get("ignore_site_a"):
        c_opts["ignore_site_a"] = True
    res = evaluate_road(road_spec, street_dumps, graph, opts=c_opts)
    reasons = list(res["reasons"])
    if not opts.get("accept_beach_street") and (res.get("beach_encroachment_m2") or 0.0) > 0.0:
        reasons.append("BEACH_ENCROACHMENT_NOT_APPROVED")
    max_run = float(opts.get("street_junction_max_run_m", STREET_JUNCTION_MAX_RUN_M))
    for jo in res["obstacles"]["junction_overlaps"]:
        if (jo.get("run_length_m") or 0.0) > max_run + 1e-9:
            reasons.append("STREET_JUNCTION_RUN_EXCEEDED")
    ok = (res["geom_corridor_state"] == "LEGAL") and not reasons and not res["obstacles"]["blocking"] and not res["obstacles"]["conservative"]
    return ok, {"eval": res, "reasons": sorted(set(reasons))}


# --- G0-D8: Greedy street scoring & selection ---

def _make_cond_access_fn(corridors: list[dict[str, Any]], graph: dict[str, Any] | None, opts: dict[str, Any]) -> Callable:
    """Wrapper over public evaluate_access that returns existing_only=True for place_layout while preserving real flag."""
    empty = {"ok": False, "side": None, "gap_m": None, "contact_m": 0.0, "corridor_ids": [], "connectivity": "UNVERIFIED", "existing_only": False, "real_existing_only": False, "reasons": ["NO_ROAD_ACCESS"]}
    if not corridors:
        fn0: Any = lambda _b: empty
        fn0.corridor_bboxes = []
        return fn0
    pad = 2.01
    bboxes = [(c["bounds"][0] - pad, c["bounds"][1] - pad, c["bounds"][2] + pad, c["bounds"][3] + pad) for c in corridors]
    ux0, uz0, ux1, uz1 = min(b[0] for b in bboxes), min(b[1] for b in bboxes), max(b[2] for b in bboxes), max(b[3] for b in bboxes)

    def fn(box: tuple[int, int, int, int]) -> dict[str, Any]:
        if box[2] < ux0 or box[0] > ux1 or box[3] < uz0 or box[1] > uz1:
            return empty
        near = [c for c, bb in zip(corridors, bboxes) if box[2] >= bb[0] and box[0] <= bb[2] and box[3] >= bb[1] and box[1] <= bb[3]]
        if not near:
            return empty
        acc = evaluate_access(box, near, graph=graph, opts=opts)
        acc["real_existing_only"] = bool(acc.get("existing_only", False))
        if acc["ok"]:
            acc["existing_only"] = True
        return acc

    fn.corridor_bboxes = bboxes  # type: ignore[attr-defined]
    return fn


def _rect_access_ok(px0: float, pz0: float, px1: float, pz1: float, sx0: float, sz0: float, sx1: float, sz1: float) -> bool:
    if px0 < sx1 - 1e-9 and px1 > sx0 + 1e-9 and pz0 < sz1 - 1e-9 and pz1 > sz0 + 1e-9:
        return False
    dz = max(0.0, sz0 - pz1, pz0 - sz1)
    if dz <= 2.0 + 1e-9:
        allow = math.sqrt(max(0.0, 4.0 - dz * dz))
        if min(px1, sx1 + allow) - max(px0, sx0 - allow) >= 8.0 - 1e-9:
            return True
    dx = max(0.0, sx0 - px1, px0 - sx1)
    if dx <= 2.0 + 1e-9:
        allow = math.sqrt(max(0.0, 4.0 - dx * dx))
        if min(pz1, sz1 + allow) - max(pz0, sz0 - allow) >= 8.0 - 1e-9:
            return True
    return False


def _unserved_by_z(v_com: dict[str, dict[int, Any]], base_cors: list[dict[str, Any]], seed_boxes: list[tuple[int, int, int, int]], graph: dict[str, Any], opts: dict[str, Any]) -> dict[int, tuple[list[int], list[list[tuple[int, int]]]]]:
    """Build row-bucketed {cz: (sorted_cx_list, sizes_list)} of unserved geom-valid centers."""
    af = _make_cond_access_fn(base_cors, graph, opts)
    near_bbs = getattr(af, "corridor_bboxes", [])
    rows: dict[int, dict[int, list[tuple[int, int]]]] = {}
    for p, orients in v_com.items():
        for o, vm in orients.items():
            vm_clean = _mask_out_corridors_from_vm(vm, base_cors)
            hw, hh, x0, z0, w = vm_clean.pw // 2, vm_clean.ph // 2, vm_clean.x0, vm_clean.z0, vm_clean.w
            pos = 0
            while True:
                pos = vm_clean.find(1, pos)
                if pos == -1:
                    break
                iz, ix = divmod(pos, w)
                cx, cz = x0 + ix, z0 + iz
                box = (cx - hw, cz - hh, cx + hw, cz + hh)
                pos += 1
                if seed_boxes and any(box[0] < sb[2] and box[2] > sb[0] and box[1] < sb[3] and box[3] > sb[1] for sb in seed_boxes):
                    continue
                if near_bbs and any(box[2] >= bb[0] and box[0] <= bb[2] and box[3] >= bb[1] and box[1] <= bb[3] for bb in near_bbs):
                    if af(box)["ok"]:
                        continue
                rows.setdefault(cz, {}).setdefault(cx, []).append((hw, hh))
    out: dict[int, tuple[list[int], list[list[tuple[int, int]]]]] = {}
    for cz, xmap in rows.items():
        xs = sorted(xmap)
        out[cz] = (xs, [xmap[x] for x in xs])
    return out


def _score_street_candidate(cor_dict: dict[str, Any], unserved_rows: dict[int, tuple[list[int], list[list[tuple[int, int]]]]], max_hw: int, max_hh: int, opts: dict[str, Any]) -> set[tuple[int, int]]:
    cb = cor_dict["bounds"]
    sx0, sz0, sx1, sz1 = cb[0], cb[1], cb[2], cb[3]
    is_rect = bool(cor_dict.get("is_rect"))
    x_lo, x_hi = math.floor(sx0 - max_hw - 2.01), math.ceil(sx1 + max_hw + 2.01)
    z_lo, z_hi = math.floor(sz0 - max_hh - 2.01), math.ceil(sz1 + max_hh + 2.01)
    gained: set[tuple[int, int]] = set()
    for cz in range(z_lo, z_hi + 1):
        row = unserved_rows.get(cz)
        if row is None:
            continue
        xs, szs = row
        idx = bisect_left(xs, x_lo)
        n = len(xs)
        while idx < n and xs[idx] <= x_hi:
            cx = xs[idx]
            for hw, hh in szs[idx]:
                if is_rect:
                    if _rect_access_ok(cx - hw, cz - hh, cx + hw, cz + hh, sx0, sz0, sx1, sz1):
                        gained.add((cx, cz))
                        break
                elif evaluate_access((cx - hw, cz - hh, cx + hw, cz + hh), [cor_dict], opts=opts)["ok"]:
                    gained.add((cx, cz))
                    break
            idx += 1
    return gained


def select_internal_streets(
    scenario_id: str, region_id: str, reg_rect: list[int],
    sources: list[dict[str, Any]], m_com: Any, v_com: dict[str, dict[int, Any]],
    base_cors: list[dict[str, Any]], seed_parcels: list[dict[str, Any]],
    dumps: dict[str, dict[str, Any]], graph: dict[str, Any],
    opts: dict[str, Any] | None = None,
) -> dict[str, Any]:
    opts = opts or {}
    cands, total_filtered, budget_exhausted = generate_street_candidates(sources, reg_rect, scenario_id, region_id, opts)
    seed_boxes = [tuple(p["bounds"]) for p in seed_parcels]
    beach_regions = dumps["PHONE_LOW"]["world"].get("beach_regions", [])
    street_dumps = _make_street_dumps(dumps, region_id, reg_rect)
    max_streets = int(opts.get("max_streets_per_region", MAX_STREETS_PER_REGION))

    all_ex_cors = corridors_from_graph(graph, include_unverified=True)
    all_cond_cors = [c for s in sources if s["source_type"] == "CONDITIONAL_ROAD" for c in s["corridors"]]
    all_road_cors = all_ex_cors + all_cond_cors

    protos = REGION_RULES[region_id]["prototypes"]
    max_hw = max(max(PROTOTYPES[p]["parcel"]) // 2 for p in protos)
    unserved_rows = _unserved_by_z(v_com, base_cors, seed_boxes, graph, opts)

    # Run Tier-1 prefilter once (Round 0) and cache surviving candidates across rounds
    t1_pool: list[tuple[dict[str, Any], dict[str, Any]]] = []
    rejection_counts: dict[str, int] = {}
    for cand in cands:
        src_ids = {c["id"] for c in cand["source"]["corridors"]}
        other_cors = [c for c in all_road_cors if c["id"] not in src_ids]
        ok1, info1 = _tier1_check_street(cand, m_com, reg_rect, seed_boxes, [], other_cors, beach_regions, opts)
        if ok1:
            t1_pool.append((cand, info1))
        else:
            r_key = str(info1.get("reason") or "TIER1_REJECTED")
            rejection_counts[r_key] = rejection_counts.get(r_key, 0) + 1

    selected: list[dict[str, Any]] = []
    sel_cors: list[dict[str, Any]] = []
    tier2_verified = 0

    for _round in range(max_streets):
        if not unserved_rows or not t1_pool:
            break
        scored: list[tuple[int, int, int, dict[str, Any], dict[str, Any], set[tuple[int, int]]]] = []
        for cand, info1 in t1_pool:
            gained = _score_street_candidate(info1["corridor"], unserved_rows, max_hw, max_hw, opts)
            if gained:
                scored.append((-len(gained), cand["length_m"], cand["order_index"], cand, info1, gained))
        if not scored:
            break
        scored.sort(key=lambda t: (t[0], t[1], t[2]))

        chosen = None
        checks_this_round = 0
        failed_t2: set[str] = set()
        for neg_sc, _len, _ord, cand, info1, gained in scored:
            if checks_this_round >= TIER2_VERIFY_LIMIT:
                break
            checks_this_round += 1
            tier2_verified += 1
            ok2, info2 = _tier2_verify_street(cand, info1, street_dumps, graph, opts)
            if not ok2:
                failed_t2.add(cand["street_id"])
                for rs in info2["reasons"]:
                    rejection_counts[rs] = rejection_counts.get(rs, 0) + 1
                continue
            chosen = (cand, info1, info2, gained, -neg_sc)
            break
        if failed_t2:
            t1_pool = [(c, inf) for c, inf in t1_pool if c["street_id"] not in failed_t2]
        if chosen is None:
            break

        cand, info1, info2, gained, score_val = chosen
        ev = info2["eval"]
        src = cand["source"]
        chain = list(src["dependency_chains"][0]) if src["source_type"] == "CONDITIONAL_ROAD" else []
        ext_conn = chain[-1] if chain else src["id"]
        st_rec = {
            "street_id": cand["street_id"], "scenario_id": scenario_id, "region_id": region_id,
            "start": [_r3(cand["start"][0]), _r3(cand["start"][1])],
            "end": [_r3(cand["end"][0]), _r3(cand["end"][1])],
            "source_road_id": src["id"], "source_type": src["source_type"],
            "length_m": cand["length_m"], "corridor_width_m": STREET_HW_M * 2.0,
            "corridor_geometry": info1["corridor"],
            "max_grade_pct": ev["grade_info"]["max_step_grade_pct"],
            "obstacle_intersections": ev["obstacles"],
            "junction_run_m": info1["junction_run_m"],
            "external_connection": ext_conn,
            "external_connection_outside_region": info1["external_connection_outside_region"],
            "dependency_chain": chain, "dependent_parcel_ids": [], "score_new_centers": score_val,
            "verification_status": "CONDITIONAL_VERIFIED", "existing": False, "rejection_reasons": [],
        }
        selected.append(st_rec)
        new_cor = info1["corridor"]
        sel_cors.append(new_cor)
        nc_b = tuple(new_cor["bounds"])
        # Prune newly served and overlapping centers from row buckets
        z_lo, z_hi = math.floor(nc_b[1] - max_hw - 2.01), math.ceil(nc_b[3] + max_hw + 2.01)
        for cz in list(unserved_rows):
            if cz < z_lo or cz > z_hi:
                continue
            xs, szs = unserved_rows[cz]
            nxs, nszs = [], []
            for cx, sizes in zip(xs, szs):
                if (cx, cz) in gained:
                    continue
                kept = [(hw, hh) for hw, hh in sizes if not _corridor_overlaps_box(new_cor, (cx - hw, cz - hh, cx + hw, cz + hh))]
                if kept:
                    nxs.append(cx)
                    nszs.append(kept)
            if nxs:
                unserved_rows[cz] = (nxs, nszs)
            else:
                del unserved_rows[cz]
        # Remove selected street and any remaining candidate overlapping it
        t1_pool = [(c, inf) for c, inf in t1_pool if c["street_id"] != cand["street_id"] and not _poly_overlaps_poly(inf["corridor"]["polygon"], tuple(inf["corridor"]["bounds"]), new_cor["polygon"], new_cor["is_rect"], nc_b)]

    return {
        "candidate_count": total_filtered, "checked_count": min(total_filtered, int(opts.get("candidate_budget", CANDIDATE_BUDGET))),
        "selected_count": len(selected), "search_budget_exhausted": budget_exhausted,
        "tier2_verified_count": tier2_verified, "rejection_summary": dict(sorted(rejection_counts.items())),
        "selected_streets": selected,
    }


# --- G0-D9..D14: Conditional layout, land accounting, verdicts ---

def _compute_land_accounting(
    m_com: Any, new_road_cors: list[dict[str, Any]], a_possible_b: float,
    beach_used_m2: float, cond_parcel_area_m2: float, opts: dict[str, Any],
) -> dict[str, Any]:
    n = m_com.w * m_com.h
    c_s4 = _vert_any_to_cell(m_com.v_s4, m_com.w, m_com.h)
    c_s13 = _vert_any_to_cell(m_com.v_s1_3, m_com.w, m_com.h)
    nr_mask = bytearray(n)
    if not opts.get("ignore_new_road_area"):
        _paint_corridors_to_mask(nr_mask, m_com.x0, m_com.z0, m_com.w, m_com.h, new_road_cors)

    not_prot = _bnot_bytes(m_com.protected)
    a_prot = m_com.protected.count(1)
    unk_ex = _band(m_com.unknown_cell, not_prot)
    a_unk = unk_ex.count(1)
    t1 = _bor_bytes(m_com.protected, m_com.unknown_cell)
    unav_raw = _bor_bytes(m_com.unavail_cell, c_s4)
    a_unav = _band(unav_raw, _bnot_bytes(t1)).count(1)
    elig_raw = _bnot_bytes(_bor_bytes(t1, unav_raw))
    cond_raw = _band(c_s13, elig_raw)
    dir_raw = _band(elig_raw, _bnot_bytes(c_s13))

    nr_in_elig = _band(nr_mask, elig_raw)
    not_nr = _bnot_bytes(nr_mask)
    a_new_road = nr_in_elig.count(1)
    a_cond_final = _band(cond_raw, not_nr).count(1)
    a_dir_final = _band(dir_raw, not_nr).count(1)
    a_elig_b = dir_raw.count(1) + cond_raw.count(1)
    a_elig_final = a_dir_final + a_cond_final

    err = abs((a_prot + a_unk + a_unav + a_cond_final + a_new_road + a_dir_final) - float(n))
    _req(err <= CONSERVATION_TOL_M2, f"Land area conservation error {err:.3f} > {CONSERVATION_TOL_M2}")
    return {
        "A_gross": round(float(n), 3), "A_direct": round(float(a_dir_final), 3),
        "A_conditional": round(float(a_cond_final), 3), "A_new_road": round(float(a_new_road), 3),
        "A_protected": round(float(a_prot), 3), "A_unavailable": round(float(a_unav), 3),
        "A_unknown": round(float(a_unk), 3), "A_eligible": round(float(a_elig_b), 3),
        "A_eligible_final": round(float(a_elig_final), 3), "A_possible": round(float(a_possible_b), 3),
        "conservation_error_m2": round(err, 6), "beach_encroachment_m2": round(float(beach_used_m2), 3),
        "land_use_reference": {
            "residential_parcel_area_m2": round(float(cond_parcel_area_m2), 3),
            "residential_share_pct": round(100.0 * cond_parcel_area_m2 / n, 3) if n else 0.0,
            "new_road_share_pct": round(100.0 * a_new_road / n, 3) if n else 0.0,
            "reference_bands_pct": {"residential": [15, 30], "roads": [20, 30]},
            "informational_only": True, "hard_gate": False,
        },
    }


def _annotate_conditional_parcels(
    parcels: list[dict[str, Any]], n_seeds: int, scenario_id: str, region_id: str,
    ex_cor_map: dict[str, dict[str, Any]], cond_cor_map: dict[str, dict[str, Any]],
    street_map: dict[str, dict[str, Any]], road_chains: dict[str, list[list[str]]],
    opts: dict[str, Any],
) -> list[dict[str, Any]]:
    out = []
    for idx, p in enumerate(parcels):
        is_seed = idx < n_seeds
        acc = dict(p.get("access") or {})
        cids = list(acc.get("corridor_ids") or [])
        if "real_existing_only" in acc:
            acc["existing_only"] = bool(acc.pop("real_existing_only"))
        if is_seed:
            st, src_id, st_id = "DIRECT", (ex_cor_map[cids[0]].get("segment_id") if cids and cids[0] in ex_cor_map else None), None
            chain, req_eng, ext_id = [], [], src_id
        else:
            st_hits = [cid for cid in cids if cid in street_map]
            cr_hits = [cid for cid in cids if cid in cond_cor_map]
            if st_hits:
                srec = street_map[st_hits[0]]
                st, st_id, src_id = "INTERNAL_STREET_REQUIRED", srec["street_id"], srec["source_road_id"]
                chain = [] if opts.get("drop_dependency_chains") else [srec["street_id"]] + list(srec["dependency_chain"])
                req_eng = ["INTERNAL_STREET"] + (["EXTERNAL_CANDIDATE_ROAD"] if srec["source_type"] == "CONDITIONAL_ROAD" else [])
                ext_id = srec["external_connection"]
                srec["dependent_parcel_ids"].append(p["id"])
            elif cr_hits:
                seg_id = cond_cor_map[cr_hits[0]]["segment_id"]
                st, st_id, src_id = "CANDIDATE_ROAD_REQUIRED", None, seg_id
                chains = road_chains.get(seg_id) or []
                chain = [] if opts.get("drop_dependency_chains") else (list(chains[0]) if chains else [])
                req_eng = ["EXTERNAL_CANDIDATE_ROAD"]
                ext_id = chain[-1] if chain else None
            else:
                seg_id = ex_cor_map[cids[0]].get("segment_id") if cids and cids[0] in ex_cor_map else None
                st, st_id, src_id, chain, req_eng, ext_id = "DIRECT", None, seg_id, [], [], seg_id
        out.append({
            "parcel_id": p["id"], "id": p["id"], "scenario_id": scenario_id, "region_id": region_id,
            "prototype_id": p["prototype"], "orientation": p["orientation"],
            "center": p["center"], "bounds": p["bounds"], "area_m2": p["area_m2"],
            "buildings": p["buildings"], "units": p["units"],
            "status": st, "source_road_id": src_id, "internal_street_id": st_id,
            "external_connection_id": ext_id, "required_engineering": req_eng,
            "dependency_chain": chain, "verification_status": "VERIFIED" if st == "DIRECT" else "CONDITIONAL_VERIFIED",
            "access": acc, "reasons": [] if st == "DIRECT" else [st],
        })
    return out


def compute_verdicts(
    reg_land: dict[str, dict[str, Any]], reg_cap: dict[str, dict[str, Any]],
    road_reg_verdicts: dict[str, dict[str, Any]], reg_streets: dict[str, dict[str, Any]],
    opts: dict[str, Any] | None = None,
) -> dict[str, Any]:
    opts = opts or {}
    rids = sorted(reg_land)
    tot_gross = sum(reg_land[r]["A_gross"] for r in rids)
    tot_possible = sum(reg_land[r]["A_possible"] for r in rids)
    tot_dir = sum(reg_land[r]["A_direct"] for r in rids)
    tot_cond = sum(reg_land[r]["A_conditional"] for r in rids)
    tot_unk = sum(reg_land[r]["A_unknown"] for r in rids)

    # G0-D12: 25 ha verdict
    if tot_gross < TARGET_AREA_M2 - 1e-9 or tot_possible < TARGET_AREA_M2 - 1e-9:
        v25, r25 = VERDICT_NOT_FEASIBLE, ["PROVEN_AREA_BELOW_25HA"]
    elif tot_dir >= TARGET_AREA_M2 - 1e-9 and all(reg_cap[r]["C_direct"] >= 1 for r in rids) and tot_unk == 0:
        v25, r25 = "FEASIBLE", ["DIRECT_LAND_AND_PARCELS_MET"]
    elif (tot_dir + tot_cond) >= TARGET_AREA_M2 - 1e-9 and all(reg_cap[r]["C_conditional"] >= 1 for r in rids):
        v25, r25 = "CONDITIONAL", ["CONDITIONAL_LAND_AND_LAYOUTS_MET"]
    else:
        v25, r25 = "UNVERIFIED", ["INSUFFICIENT_VERIFIED_LAND_OR_LAYOUT"]

    # G0-D13: 40 (min) and 60 (ideal) building targets, regions independent
    def _bldg_verdict(target_key: str) -> tuple[str, dict[str, Any]]:
        targets = {r: REGION_RULES[r][target_key] for r in rids}
        tot_target = sum(targets.values())
        if opts.get("allow_cross_region_offset"):
            if sum(reg_cap[r]["C_direct"] for r in rids) >= tot_target:
                return "FEASIBLE", {"targets": targets, "reason": "CROSS_REGION_OFFSET"}
            if sum(reg_cap[r]["C_conditional"] for r in rids) >= tot_target:
                return "CONDITIONAL", {"targets": targets, "reason": "CROSS_REGION_OFFSET"}
        if all(reg_cap[r]["C_direct"] >= targets[r] for r in rids):
            return "FEASIBLE", {"targets": targets, "reason": "ALL_REGIONS_DIRECT_MET"}
        if all(reg_cap[r]["C_conditional"] >= targets[r] for r in rids):
            return "CONDITIONAL", {"targets": targets, "reason": "ALL_REGIONS_CONDITIONAL_MET"}
        below_upper = [r for r in rids if reg_cap[r]["C_upper"] < targets[r]]
        if below_upper:
            return VERDICT_NOT_FEASIBLE, {"targets": targets, "regions_below_c_upper": below_upper, "reason": "C_UPPER_BELOW_TARGET"}
        budget_ex = [r for r in rids if reg_streets[r]["search_budget_exhausted"]]
        if opts.get("budget_exhausted_as_not_feasible") and budget_ex:
            return VERDICT_NOT_FEASIBLE, {"targets": targets, "regions_budget_exhausted": budget_ex, "reason": "SEARCH_BUDGET_EXHAUSTED"}
        return "UNVERIFIED", {"targets": targets, "regions_short": [r for r in rids if reg_cap[r]["C_conditional"] < targets[r]], "regions_budget_exhausted": budget_ex, "reason": "SEARCH_INSUFFICIENT_UNPROVEN"}

    v40, e40 = _bldg_verdict("min")
    v60, e60 = _bldg_verdict("ideal")

    # G0-D14: Road connectivity & overall D3 (60 never gates D3 unless mutated)
    ext_vs = [road_reg_verdicts[r]["verdict"] for r in rids if r in road_reg_verdicts]
    v_road = _worst_verdict(ext_vs) if ext_vs else "UNVERIFIED"
    uses_cond_road = any(p["status"] in ("CANDIDATE_ROAD_REQUIRED", "INTERNAL_STREET_REQUIRED") for r in rids for p in reg_cap[r]["parcels"])
    if v_road == "FEASIBLE" and uses_cond_road:
        v_road = "CONDITIONAL"
    d3_inputs = [v25, v40, v_road] + ([v60] if opts.get("gate_d3_on_60") else [])
    v_d3 = _worst_verdict(d3_inputs)
    return {
        "land_25ha": {"verdict": v25, "reasons": r25, "A_gross_total": round(tot_gross, 3), "A_possible_total": round(tot_possible, 3), "A_direct_total": round(tot_dir, 3), "A_conditional_total": round(tot_cond, 3)},
        "buildings_40": {"verdict": v40, **e40, "C_direct_total": sum(reg_cap[r]["C_direct"] for r in rids), "C_conditional_total": sum(reg_cap[r]["C_conditional"] for r in rids)},
        "buildings_60": {"verdict": v60, **e60, "gates_d3": bool(opts.get("gate_d3_on_60"))},
        "road_connectivity": {"verdict": v_road, "per_region_external": {r: road_reg_verdicts.get(r, {}).get("verdict", "UNVERIFIED") for r in rids}, "uses_conditional_roads_or_streets": uses_cond_road},
        "D3": {"verdict": v_d3, "inputs": {"land_25ha": v25, "buildings_40": v40, "road_connectivity": v_road}},
    }


# --- Top-level analyze & CLI ---

def analyze(
    dump_paths: list[str | Path], capacity_inventory_path: str | Path,
    parcel_candidates_path: str | Path, road_survey_path: str | Path,
    out_dir: str | Path | None = None, opts: dict[str, Any] | None = None,
) -> dict[str, Any]:
    t0 = time.monotonic()
    opts = opts or {}
    loaded = load_and_verify_inputs(dump_paths, capacity_inventory_path, parcel_candidates_path, road_survey_path, opts)
    dumps = loaded["dumps"]
    d_lo, d_hi = dumps["PHONE_LOW"], dumps["DESKTOP_HIGH"]
    cap_inv, par_cand, road_svy = loaded["capacity_inventory"], loaded["parcel_candidates"], loaded["road_survey"]
    scenarios = opts.get("scenarios") or SCENARIOS
    graph_lo, graph_hi = build_road_graph(d_lo), build_road_graph(d_hi)
    ex_cors_lo, ex_cors_hi = corridors_from_graph(graph_lo), corridors_from_graph(graph_hi)
    hi_ex_ids = {c["id"] for c in ex_cors_hi}
    ex_cors_com = [c for c in ex_cors_lo if c["id"] in hi_ex_ids]
    ex_cor_map = {c["id"]: c for c in ex_cors_com}
    cond_cors_all = list(road_svy.get("candidate_corridors", []))

    # Build ENVELOPE triplets once (reusing B's approved underscore helpers)
    env_data: dict[str, Any] = {}
    if "ENVELOPE" in scenarios:
        for rid in sorted(scenarios["ENVELOPE"]):
            env_data[rid] = _build_region_triplet(d_lo, d_hi, "ENVELOPE", rid, spec_to_internal(scenarios["ENVELOPE"][rid]), {})

    streets_out, parcels_out, feas_scen_out = {}, {}, {}
    for sid in scenarios:
        # Step 1: recompute & verify direct layouts across all regions in sid (G0-D2) and detect direct-parcel conflicts (G0-D7)
        scen_reg_data: dict[str, Any] = {}
        all_seed_parcels: list[dict[str, Any]] = []
        for rid in sorted(scenarios[sid]):
            b_int = spec_to_internal(scenarios[sid][rid])
            protos = REGION_RULES[rid]["prototypes"]
            if sid == "ENVELOPE" and rid in env_data:
                (m_lo, m_hi, m_com), (v_lo, v_hi, v_com) = env_data[rid]
            elif rid in env_data:
                m_lo, m_hi, m_com = tuple(_slice_masks(m, sid, b_int) for m in env_data[rid][0])
                v_lo, v_hi, v_com = tuple({p: {o: _slice_valid_mask(v[p][o], b_int) for o in (0, 90)} for p in protos} for v in env_data[rid][1])
            else:
                (m_lo, m_hi, m_com), (v_lo, v_hi, v_com) = _build_region_triplet(d_lo, d_hi, sid, rid, b_int, {})

            direct = common_layout(m_lo, m_hi, m_com, v_lo, v_hi, v_com, ex_cors_lo, ex_cors_hi, ex_cors_com, graph_lo, graph_hi, rid, require_access=True, opts={})
            direct_ps = direct["L_common"]["parcels"]
            if not opts.get("skip_direct_recheck"):
                exp_ps = (((par_cand.get("scenarios") or {}).get(sid) or {}).get(rid) or {}).get("direct_parcels") or []
                _req([p["id"] for p in direct_ps] == [p["id"] for p in exp_ps], f"Direct parcel IDs mismatch in {sid}/{rid}")
            all_seed_parcels.extend(direct_ps)
            scen_reg_data[rid] = (b_int, (m_lo, m_hi, m_com), (v_lo, v_hi, v_com), direct_ps)

        # G0-D7: exclude candidate roads whose corridor overlaps any direct seed parcel in scenario sid
        excluded_sources: dict[str, dict[str, Any]] = {}
        if not opts.get("allow_road_seed_conflict"):
            by_seg: dict[str, list[dict[str, Any]]] = {}
            for c in cond_cors_all:
                by_seg.setdefault(c["segment_id"], []).append(c)
            for cr_id, clist in sorted(by_seg.items()):
                hits = [sp["id"] for sp in all_seed_parcels if any(_corridor_overlaps_box(c, tuple(sp["bounds"])) for c in clist)]
                if hits:
                    excluded_sources[cr_id] = {"reason": "DIRECT_PARCEL_CONFLICT", "conflicting_parcel_ids": sorted(hits)}

        sources = _extract_sources(graph_lo, road_svy, set(excluded_sources), opts)
        active_src_ids = {s["id"] for s in sources if s["source_type"] == "CONDITIONAL_ROAD"}
        active_cond_cors = [c for c in cond_cors_all if c["segment_id"] in active_src_ids]
        cond_cor_map = {c["id"]: c for c in active_cond_cors}
        road_chains = {s["id"]: s["dependency_chains"] for s in sources if s["source_type"] == "CONDITIONAL_ROAD"}
        base_cors = ex_cors_com + active_cond_cors

        reg_streets_s, reg_parcels_s, reg_land_s = {}, {}, {}
        for rid in sorted(scenarios[sid]):
            b_int, (m_lo, m_hi, m_com), (v_lo, v_hi, v_com), direct_ps = scen_reg_data[rid]
            seeds = [] if opts.get("drop_direct_seeds") else list(direct_ps)
            st_res = select_internal_streets(sid, rid, b_int, sources, m_com, v_com, base_cors, seeds, dumps, graph_lo, opts)
            sel_streets = st_res["selected_streets"]
            sel_cors = [s["corridor_geometry"] for s in sel_streets]
            street_map = {s["street_id"]: s for s in sel_streets}
            new_road_cors = active_cond_cors + sel_cors
            all_cors_com = ex_cors_com + new_road_cors
            all_cors_lo = ex_cors_lo + new_road_cors
            all_cors_hi = ex_cors_hi + new_road_cors

            # Mask out new road corridors from valid masks before seeded placement
            vc_masked = {p: {o: _mask_out_corridors_from_vm(v_com[p][o], new_road_cors) for o in (0, 90)} for p in v_com}
            vl_masked = {p: {o: _mask_out_corridors_from_vm(v_lo[p][o], new_road_cors) for o in (0, 90)} for p in v_lo}
            vh_masked = {p: {o: _mask_out_corridors_from_vm(v_hi[p][o], new_road_cors) for o in (0, 90)} for p in v_hi}

            pl_opts = {"r08_as_four_buildings": True} if opts.get("r08_as_four_buildings") else {}
            af_com = _make_cond_access_fn(all_cors_com, graph_lo, opts)
            af_lo = _make_cond_access_fn(all_cors_lo, graph_lo, opts)
            af_hi = _make_cond_access_fn(all_cors_hi, graph_hi, opts)

            lay_lo = place_layout(vl_masked, af_lo, rid, opts=pl_opts, seed_parcels=seeds)
            lay_hi = place_layout(vh_masked, af_hi, rid, opts=pl_opts, seed_parcels=seeds)
            lay_com = lay_lo if opts.get("single_preset_only") else place_layout(vc_masked, af_com, rid, opts=pl_opts, seed_parcels=seeds)

            # G0-D10: cross-preset verification with _verify_layout (existing:True only inside verification call)
            ver_cors_lo = [dict(c, existing=True) for c in all_cors_lo]
            ver_cors_hi = [dict(c, existing=True) for c in all_cors_hi]
            ok_lo, err_lo = _verify_layout(lay_com["parcels"], m_lo, ver_cors_lo, graph_lo, rid, True, pl_opts)
            ok_hi, err_hi = (True, []) if opts.get("single_preset_only") else _verify_layout(lay_com["parcels"], m_hi, ver_cors_hi, graph_hi, rid, True, pl_opts)
            _req(ok_lo and ok_hi, f"Cross-preset _verify_layout failed in {sid}/{rid}: lo={err_lo} hi={err_hi}")

            c_dir = sum(p["buildings"] for p in direct_ps)
            c_com = sum(4 if p["prototype"] == "R08" else p["buildings"] for p in lay_com["parcels"]) if opts.get("r08_as_four_buildings") else lay_com["count"]
            c_lo = max(lay_lo["count"], c_com)
            c_hi = lay_hi["count"] if opts.get("single_preset_only") else max(lay_hi["count"], c_com)
            c_cond = (c_com + c_dir) if opts.get("double_count_direct_and_conditional") else c_com
            if opts.get("count_foundation_in_conditional"):
                c_cond += int(_vert_any_to_cell(m_com.v_s1_3, m_com.w, m_com.h).count(1) // 528)
            if opts.get("enforce_land_use_ratio"):
                n_area = float(m_com.w * m_com.h)
                sh = 100.0 * sum(p["area_m2"] for p in lay_com["parcels"]) / n_area
                rsh = 100.0 * sum(s["length_m"] * STREET_HW_M * 2.0 for s in sel_streets) / n_area
                if sh < 15.0 or sh > 30.0 or rsh < 20.0 or rsh > 30.0:
                    c_cond, lay_com["parcels"] = c_dir, list(direct_ps)

            b_reg = (((cap_inv.get("scenarios") or {}).get(sid) or {}).get("regions") or {}).get(rid) or {}
            c_upper = int((b_reg.get("capacities") or {}).get("C_upper", 0))
            a_possible_b = float((b_reg.get("areas_m2") or {}).get("A_possible", m_com.w * m_com.h))

            ann_parcels = _annotate_conditional_parcels(lay_com["parcels"], len(seeds), sid, rid, ex_cor_map, cond_cor_map, street_map, road_chains, opts)
            used_cond_ids = {rc for p in ann_parcels for rc in ([p["source_road_id"]] + list(p["dependency_chain"])) if rc in active_src_ids}
            beach_used = sum(float((road_svy["roads"].get(cr) or {}).get("beach_encroachment_m2") or 0.0) for cr in sorted(used_cond_ids))
            land_rec = _compute_land_accounting(m_com, new_road_cors, a_possible_b, beach_used, sum(p["area_m2"] for p in ann_parcels), opts)

            st_res["excluded_sources"] = excluded_sources
            reg_streets_s[rid] = st_res
            reg_land_s[rid] = land_rec
            reg_parcels_s[rid] = {
                "C_direct": c_dir, "C_conditional": c_cond, "C_additional": c_cond - c_dir,
                "C_phone_low": c_lo, "C_desktop_high": c_hi, "C_common": c_com, "C_upper": c_upper,
                "units_conditional": sum(p["units"] for p in ann_parcels),
                "prototype_counts": lay_com["prototype_counts"], "prototype_mix_ok": lay_com["ratio_ok"],
                "proxy_used": REGION_RULES[rid]["proxy"],
                "foundation_unverified_cells_m2": int(land_rec["A_conditional"]),
                "preset_validation": {"PHONE_LOW": {"ok": ok_lo, "errors": err_lo}, "DESKTOP_HIGH": {"ok": ok_hi, "errors": err_hi}},
                "parcels": ann_parcels,
            }

        verdicts = compute_verdicts(reg_land_s, reg_parcels_s, (road_svy.get("regional_access") or {}).get(sid) or {}, reg_streets_s, opts)
        req_eng = sorted({e for r in reg_parcels_s.values() for p in r["parcels"] for e in p["required_engineering"]})
        unv_items = sorted({f"{rid}:SEARCH_BUDGET_EXHAUSTED" for rid, st in reg_streets_s.items() if st["search_budget_exhausted"]} | {f"{rid}:FOUNDATION_UNVERIFIED" for rid, pr in reg_parcels_s.items() if pr["foundation_unverified_cells_m2"] > 0} | {f"{rid}:DATA_UNKNOWN" for rid, lr in reg_land_s.items() if lr["A_unknown"] > 0})

        streets_out[sid] = reg_streets_s
        parcels_out[sid] = reg_parcels_s
        feas_scen_out[sid] = {
            "land_accounting": {"regions": reg_land_s, "totals": {k: round(sum(reg_land_s[r][k] for r in reg_land_s), 3) for k in ("A_gross", "A_direct", "A_conditional", "A_new_road", "A_protected", "A_unavailable", "A_unknown", "A_eligible", "A_eligible_final", "A_possible", "beach_encroachment_m2")}},
            "capacities": {r: {k: v for k, v in reg_parcels_s[r].items() if k != "parcels"} for r in reg_parcels_s},
            "excluded_sources": excluded_sources, "verdicts": verdicts,
            "required_engineering": req_eng, "unverified_items": unv_items,
            "verdict_evidence": {"road_access": (road_svy.get("regional_access") or {}).get(sid) or {}, "selected_streets_count": {r: reg_streets_s[r]["selected_count"] for r in reg_streets_s}},
        }

    compat = {
        "base_sha": loaded["base_sha"], "phone_low_static_fingerprint": loaded["fp_lo"],
        "desktop_high_static_fingerprint": loaded["fp_hi"], "we01a_analyzer_version": WE01A_COMPAT_VERSION,
        "t016b_analyzer_version": B_VERSION, "t016c_analyzer_version": C_VERSION,
        "t016d_analyzer_version": ANALYZER_VERSION, "schema_version": FEASIBILITY_SCHEMA_VERSION,
        "polygon_revision": POLYGON_REVISION,
    }
    common_hdr = {
        "schema_version": FEASIBILITY_SCHEMA_VERSION, "analyzer_version": ANALYZER_VERSION,
        "base_sha": loaded["base_sha"], "polygon_revision": POLYGON_REVISION,
        "compatibility_key": compat, "sources": {"t016b_analyzer_version": B_VERSION, "t016c_analyzer_version": C_VERSION, **loaded["hashes"]},
        "presets": {p: {"static_fingerprint": dumps[p]["metadata"]["static_fingerprint"], "file_sha256": dumps[p].get("_file_sha256")} for p in ("PHONE_LOW", "DESKTOP_HIGH")},
    }
    int_st_doc = dict(common_hdr, scenarios=streets_out)
    int_st_doc["deterministic_sha256"] = _det_hash(int_st_doc)
    cond_p_doc = dict(common_hdr, scenarios=parcels_out)
    cond_p_doc["deterministic_sha256"] = _det_hash(cond_p_doc)
    feas_det = dict(common_hdr, scenarios=feas_scen_out)
    feas_doc = dict(feas_det, deterministic_sha256=_det_hash(feas_det), runtime_meta={"elapsed_s": round(time.monotonic() - t0, 3)})

    if out_dir is not None:
        od = Path(out_dir)
        od.mkdir(parents=True, exist_ok=True)
        (od / "internal_streets.json").write_text(json.dumps(int_st_doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (od / "conditional_parcels.json").write_text(json.dumps(cond_p_doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (od / "feasibility.json").write_text(json.dumps(feas_doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"internal_streets": int_st_doc, "conditional_parcels": cond_p_doc, "feasibility": feas_doc}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="WE-01D (T-016D) Internal Streets, Conditional Capacity & Feasibility Verdicts.")
    ap.add_argument("--dump", action="append", required=True, help="Runtime dump JSON path (PHONE_LOW & DESKTOP_HIGH).")
    ap.add_argument("--capacity-inventory", required=True, help="T-016B capacity_inventory.json.")
    ap.add_argument("--parcel-candidates", required=True, help="T-016B parcel_candidates.json.")
    ap.add_argument("--road-survey", required=True, help="T-016C road_survey.json.")
    ap.add_argument("--out", required=True, help="Output directory.")
    args = ap.parse_args(argv)
    try:
        analyze(args.dump, args.capacity_inventory, args.parcel_candidates, args.road_survey, out_dir=args.out)
    except FeasibilityError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
