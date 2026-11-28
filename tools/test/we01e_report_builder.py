#!/usr/bin/env python3
"""WE-01E (T-016E) Final Survey Map & Report Builder — read-only, deterministic, Python stdlib only."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import time
from typing import Any
import xml.etree.ElementTree as ET

BUILDER_VERSION = "we01e-1.0"
MANIFEST_FILE = "inputs_manifest.json"
DATA_FILES = (
    "land_inventory.json",
    "capacity_inventory.json",
    "parcel_candidates.json",
    "road_survey.json",
    "internal_streets.json",
    "conditional_parcels.json",
    "feasibility.json",
    "map_geometry.json",
)
SCENARIO_ORDER = ("INITIAL", "ENVELOPE", "REVISED")
REGION_ORDER = ("B1", "B2", "B3")
VERDICT_ORDER = ("land_25ha", "buildings_40", "buildings_60", "road_connectivity", "D3")
FIXED_B8_PARAGRAPH = "Gate B8 尚待 Claude 完成正式量測，本報告不代表新增住宅已達效能目標。"
FOLLOWUP_HEADING = "WE-02–WE-09 後續工程建議（僅為建議，未授權）"
PENDING_TOKEN = "PENDING_" + "T016D"


class BuildError(ValueError):
    """Raised on input integrity, schema, missing-field, or reference failures."""


def _req(cond: bool, msg: str) -> None:
    if not cond:
        raise BuildError(msg)


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _is_hex64(val: Any) -> bool:
    return isinstance(val, str) and len(val) == 64 and all(c in "0123456789abcdef" for c in val)


def _get(obj: Any, *keys: str) -> Any:
    cur = obj
    path = []
    for k in keys:
        path.append(k)
        if not isinstance(cur, dict) or k not in cur:
            raise BuildError(f"Missing required field: {'.'.join(path)}")
        cur = cur[k]
    return cur


def _num(obj: Any, *keys: str) -> float:
    val = _get(obj, *keys)
    if isinstance(val, bool) or not isinstance(val, (int, float)) or not math.isfinite(val):
        raise BuildError(f"Invalid numeric field {'.'.join(keys)}: {val!r}")
    return float(val)


def _int(obj: Any, *keys: str) -> int:
    val = _get(obj, *keys)
    if isinstance(val, bool) or not isinstance(val, int):
        raise BuildError(f"Invalid integer field {'.'.join(keys)}: {val!r}")
    return int(val)


def _str(obj: Any, *keys: str) -> str:
    val = _get(obj, *keys)
    if not isinstance(val, str) or not val:
        raise BuildError(f"Invalid string field {'.'.join(keys)}: {val!r}")
    return val


def _fmt_int(v: int | float) -> str:
    return f"{int(round(v)):,}"


def _fmt_m2(v: float) -> str:
    return f"{int(round(v)):,}" if abs(v - round(v)) < 1e-6 else f"{v:,.1f}"


def _fmt_num(v: float, dp: int = 1) -> str:
    return f"{v:,.{dp}f}"


def _esc(val: Any) -> str:
    return html.escape(str(val), quote=True)


def _sanitize_text(text: str) -> str:
    _req(PENDING_TOKEN not in text, "Forbidden historical placeholder leaked into output")
    return text


# --- Integrity & cross-file verification (G0-E2, G0-E3) ---

def load_and_verify_inputs(input_dir: str | Path) -> dict[str, Any]:
    in_dir = Path(input_dir)
    _req(in_dir.is_dir(), f"Input directory does not exist: {in_dir}")
    mf_path = in_dir / MANIFEST_FILE
    _req(mf_path.is_file(), f"Missing manifest: {MANIFEST_FILE}")
    try:
        manifest = json.loads(mf_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise BuildError(f"Invalid JSON in {MANIFEST_FILE}: {exc}") from exc

    _req(_get(manifest, "kind") == "we01e_inputs_manifest", "Invalid manifest kind")
    _req(_int(manifest, "schema_version") == 1, "Manifest schema_version must be 1")
    base_sha = _str(manifest, "base_sha")
    mf_files = _get(manifest, "files")
    _req(isinstance(mf_files, dict) and set(mf_files.keys()) == set(DATA_FILES), "Manifest file set mismatch")

    docs: dict[str, Any] = {}
    file_hashes: dict[str, str] = {}
    for fn in DATA_FILES:
        fp = in_dir / fn
        _req(fp.is_file(), f"Missing required input file: {fn}")
        raw = fp.read_bytes()
        sha = _sha256_bytes(raw)
        exp_sha = _str(mf_files, fn)
        _req(_is_hex64(exp_sha) and sha == exp_sha, f"SHA-256 mismatch for {fn}: got {sha}, expected {exp_sha}")
        file_hashes[fn] = sha
        try:
            docs[fn] = json.loads(raw.decode("utf-8"))
        except Exception as exc:
            raise BuildError(f"Invalid JSON in {fn}: {exc}") from exc

    li = docs["land_inventory.json"]
    ci = docs["capacity_inventory.json"]
    pc = docs["parcel_candidates.json"]
    rs = docs["road_survey.json"]
    st = docs["internal_streets.json"]
    cp = docs["conditional_parcels.json"]
    fe = docs["feasibility.json"]
    mg = docs["map_geometry.json"]

    # Base SHA, schema_version, polygon_revision, analyzer_version
    for fn, doc in docs.items():
        _req(_int(doc, "schema_version") == 1 and _str(doc, "base_sha") == base_sha, f"{fn} schema_version/base_sha mismatch")
    _req(_get(mg, "kind") == "we01e_map_geometry" and _get(mg, "geometry_identical_across_presets") is True, "map_geometry kind/preset mismatch")
    fp_lo, fp_hi = _str(mg, "phone_low_static_fingerprint"), _str(mg, "desktop_high_static_fingerprint")
    _req(_is_hex64(fp_lo) and _is_hex64(fp_hi), "Invalid static fingerprints in map_geometry")

    a_presets = _get(li, "presets")
    _req(isinstance(a_presets, list), "land_inventory presets must be a list")
    a_fp_map = {str(_get(p, "preset")): _str(p, "static_fingerprint") for p in a_presets}
    _req(a_fp_map.get("PHONE_LOW") == fp_lo and a_fp_map.get("DESKTOP_HIGH") == fp_hi and _str(li, "analyzer_version"), "land_inventory provenance mismatch")

    for fn in ("capacity_inventory.json", "parcel_candidates.json", "road_survey.json", "internal_streets.json", "conditional_parcels.json", "feasibility.json"):
        doc = docs[fn]
        ck = _get(doc, "compatibility_key")
        _req(
            _int(doc, "polygon_revision") == 2 and _str(doc, "analyzer_version")
            and _str(doc, "presets", "PHONE_LOW", "static_fingerprint") == fp_lo
            and _str(doc, "presets", "DESKTOP_HIGH", "static_fingerprint") == fp_hi
            and _str(ck, "base_sha") == base_sha and _int(ck, "polygon_revision") == 2
            and _str(ck, "phone_low_static_fingerprint") == fp_lo and _str(ck, "desktop_high_static_fingerprint") == fp_hi,
            f"{fn} provenance/compatibility_key mismatch",
        )

    _req(_int(ci, "handoff_schema_version") == 1 and _int(pc, "handoff_schema_version") == 1 and _int(rs, "road_schema_version") == 1, "B/C sub-schema version mismatch")
    _req(_str(rs, "t016b_source", "sha256") == file_hashes["capacity_inventory.json"], "C t016b_source sha256 mismatch")

    for fn in ("internal_streets.json", "conditional_parcels.json", "feasibility.json"):
        doc, srcs = docs[fn], _get(docs[fn], "sources")
        _req(_is_hex64(_get(doc, "deterministic_sha256")), f"{fn} missing valid deterministic_sha256")
        for sk, target_fn in (("capacity_inventory_sha256", "capacity_inventory.json"), ("parcel_candidates_sha256", "parcel_candidates.json"), ("road_survey_sha256", "road_survey.json")):
            _req(_str(srcs, sk) == file_hashes[target_fn], f"{fn} {sk} mismatch")

    _req({_str(r, "id") for r in _get(li, "regions")} == set(REGION_ORDER), "land_inventory region IDs mismatch")
    for fn, key in (("capacity_inventory.json", "scenarios"), ("parcel_candidates.json", "scenarios"), ("road_survey.json", "regional_access"), ("internal_streets.json", "scenarios"), ("conditional_parcels.json", "scenarios"), ("feasibility.json", "scenarios")):
        _req(set(_get(docs[fn], key).keys()) == set(SCENARIO_ORDER), f"{fn}.{key} scenario set mismatch")

    road_ids = set(_get(rs, "roads").keys())
    known_road_ids = road_ids | {_str(r, "id") for r in _get(mg, "roads")} | set(_get(ci, "road_graph", "main_component"))
    area_keys = ("A_gross", "A_direct", "A_conditional", "A_new_road", "A_protected", "A_unavailable", "A_unknown", "A_eligible", "A_eligible_final", "A_possible", "beach_encroachment_m2")
    for sid in SCENARIO_ORDER:
        for label, rmap in (
            ("B.regions", _get(ci, "scenarios", sid, "regions")), ("B.bounds", _get(ci, "scenarios_internal_order", sid)),
            ("PC", _get(pc, "scenarios", sid)), ("C.access", _get(rs, "regional_access", sid)),
            ("D.streets", _get(st, "scenarios", sid)), ("D.parcels", _get(cp, "scenarios", sid)),
            ("D.land", _get(fe, "scenarios", sid, "land_accounting", "regions")), ("D.cap", _get(fe, "scenarios", sid, "capacities")),
        ):
            _req(set(rmap.keys()) == set(REGION_ORDER), f"{label}.{sid} regions mismatch")

        all_direct_ids = {_str(dp, "id") for rid in REGION_ORDER for dp in _get(pc, "scenarios", sid, rid, "direct_parcels")}
        for erid, edet in _get(fe, "scenarios", sid, "excluded_sources").items():
            _req(erid in road_ids, f"Excluded road {erid} in {sid} not in road_survey.roads")
            for pid in _get(edet, "conflicting_parcel_ids"):
                _req(pid in all_direct_ids, f"Conflicting parcel {pid} in {sid}/{erid} not in direct_parcels")

        v_map = _get(fe, "scenarios", sid, "verdicts")
        for vk in VERDICT_ORDER:
            _str(v_map, vk, "verdict")
        for lk in ("A_gross_total", "A_possible_total", "A_direct_total", "A_conditional_total"):
            _num(v_map, "land_25ha", lk)
        for bk in ("buildings_40", "buildings_60"):
            for rid in REGION_ORDER:
                _int(_get(v_map, bk, "targets"), rid)
        for tk in area_keys:
            _num(fe, "scenarios", sid, "land_accounting", "totals", tk)

        for rid in REGION_ORDER:
            sel_ids: set[str] = set()
            for srec in _get(st, "scenarios", sid, rid, "selected_streets"):
                _req(_str(srec, "source_road_id") in known_road_ids, f"Unknown street source road: {srec['source_road_id']}")
                _num(srec, "length_m")
                sel_ids.add(_str(srec, "street_id"))
            cp_r = _get(cp, "scenarios", sid, rid)
            for ck_int in ("C_direct", "C_conditional", "C_additional", "C_phone_low", "C_desktop_high", "C_common", "C_upper", "units_conditional"):
                _int(cp_r, ck_int)
            la_r = _get(fe, "scenarios", sid, "land_accounting", "regions", rid)
            for ak in area_keys + ("conservation_error_m2",):
                _num(la_r, ak)
            p_ids: set[str] = set()
            for p in _get(cp_r, "parcels"):
                pid = _str(p, "parcel_id")
                _req(pid not in p_ids, f"Duplicate parcel_id {pid} in {sid}/{rid}")
                p_ids.add(pid)
                _str(p, "prototype_id")
                _str(p, "status")
                _int(p, "buildings")
                _int(p, "units")
                ist = _get(p, "internal_street_id")
                _req(ist is None or ist in sel_ids, f"Parcel {pid} references unknown street {ist} in {sid}/{rid}")
            for dp in _get(pc, "scenarios", sid, rid, "direct_parcels"):
                _req(_str(dp, "id") in p_ids, f"Direct parcel {dp['id']} missing from conditional_parcels in {sid}/{rid}")

    return {
        "manifest": manifest, "file_hashes": file_hashes, "base_sha": base_sha,
        "fp_lo": fp_lo, "fp_hi": fp_hi,
        "land_inventory": li, "capacity_inventory": ci, "parcel_candidates": pc,
        "road_survey": rs, "internal_streets": st, "conditional_parcels": cp,
        "feasibility": fe, "map_geometry": mg,
    }


# --- SVG Builder (G0-E6) ---

def _poly_pts(pts: list[list[float]], tx: Any, tz: Any) -> str:
    return " ".join(f"{tx(p[0]):.2f},{tz(p[1]):.2f}" for p in pts)


def _line_pts_3d(pts: list[list[float]], tx: Any, tz: Any) -> str:
    return " ".join(f"{tx(p[0]):.2f},{tz(p[-1]):.2f}" for p in pts)


def _nice_scale_m(world_w: float) -> int:
    target = world_w * 0.22
    for step in (25, 50, 100, 200, 250, 500):
        if step >= target * 0.65:
            return step
    return 500


def _short_parcel_label(pid: str) -> str:
    parts = pid.split("_")
    return parts[-1] if len(parts) >= 3 else pid


def _pts_in_view(pts: list[list[float]], wx0: float, wz0: float, wx1: float, wz1: float) -> bool:
    xs, zs = [p[0] for p in pts], [p[-1] for p in pts]
    return max(xs) >= wx0 and min(xs) <= wx1 and max(zs) >= wz0 and min(zs) <= wz1


def _draw_bg_layers(
    out: list[str], uid_fn: Any, mg: dict[str, Any], prefix: str,
    tx: Any, tz: Any, scale: float, view: tuple[float, float, float, float] | None,
) -> None:
    def _vis(pts: list[list[float]]) -> bool:
        return True if view is None else _pts_in_view(pts, *view)

    for i, wp in enumerate(mg["water_regions"]):
        if _vis(wp):
            out.append(f'<polygon id="{uid_fn(f"water-{prefix}-{i}")}" points="{_poly_pts(wp, tx, tz)}" fill="url(#pat-water)" stroke="#2b6cb0" stroke-width="0.9" data-layer="water"/>')
    for i, bp in enumerate(mg["beach_regions"]):
        if _vis(bp):
            out.append(f'<polygon id="{uid_fn(f"beach-{prefix}-{i}")}" points="{_poly_pts(bp, tx, tz)}" fill="url(#pat-beach)" stroke="#b7791f" stroke-width="0.9" stroke-dasharray="6,3" data-layer="beach"/>')
    for s_obj in mg["site_a"]:
        if _vis(s_obj["polygon"]):
            sid_a = s_obj["id"]
            out.append(f'<polygon id="{uid_fn(f"sitea-{prefix}-{sid_a}")}" points="{_poly_pts(s_obj["polygon"], tx, tz)}" fill="url(#pat-sitea)" stroke="#6b46c1" stroke-width="1.2" stroke-dasharray="5,2" data-layer="site_a" data-entity-id="{_esc(sid_a)}"><title>{_esc(sid_a)} (Site A Protected)</title></polygon>')
    for r_obj in mg["roads"]:
        if _vis(r_obj["centerline"]):
            sw = max(1.6, float(r_obj["carriageway_width_m"]) * scale * 0.45)
            out.append(f'<polyline id="{uid_fn(f"exrd-{prefix}-{r_obj["id"]}")}" points="{_line_pts_3d(r_obj["centerline"], tx, tz)}" fill="none" stroke="#4a5568" stroke-width="{sw:.2f}" stroke-linecap="round" data-layer="existing_road" data-entity-id="{_esc(r_obj["id"])}"><title>Existing road {_esc(r_obj["id"])} ({_esc(r_obj["elevation_type"])})</title></polyline>')


def _render_panel(
    out: list[str], used_ids: set[str], data: dict[str, Any],
    sid: str, rid: str, px: float, py: float, pw: float, ph: float, is_primary: bool,
) -> None:
    def _uid(raw: str) -> str:
        _req(raw not in used_ids, f"Duplicate SVG id: {raw}")
        used_ids.add(raw)
        return raw

    ci, rs, st, cp, fe, mg = data["capacity_inventory"], data["road_survey"], data["internal_streets"], data["conditional_parcels"], data["feasibility"], data["map_geometry"]
    rx0, rz0, rx1, rz1 = [float(v) for v in ci["scenarios_internal_order"][sid][rid]]
    pad_w = max(rx1 - rx0, rz1 - rz0) * 0.08
    wx0, wz0, wx1, wz1 = rx0 - pad_w, rz0 - pad_w, rx1 + pad_w, rz1 + pad_w
    hdr_h, ftr_h = (46.0 if is_primary else 38.0), 26.0
    vx, vy, vw, vh = px + 38.0, py + hdr_h, pw - 52.0, ph - hdr_h - ftr_h
    scale = min(vw / (wx1 - wx0), vh / (wz1 - wz0))
    ox, oz = vx + (vw - (wx1 - wx0) * scale) * 0.5, vy + (vh - (wz1 - wz0) * scale) * 0.5
    tx, tz = (lambda x: ox + (x - wx0) * scale), (lambda z: oz + (z - wz0) * scale)

    cp_r, la_r, st_r, excl = cp["scenarios"][sid][rid], fe["scenarios"][sid]["land_accounting"]["regions"][rid], st["scenarios"][sid][rid], fe["scenarios"][sid]["excluded_sources"]
    proxy_tag = " [PROXY]" if cp_r["proxy_used"] else ""
    clip_id, panel_id = _uid(f"clip-{sid}-{rid}"), _uid(f"panel-{sid}-{rid}")

    out.append(f'<g id="{panel_id}" data-scenario="{sid}" data-region="{rid}" data-wx0="{wx0:.3f}" data-wz0="{wz0:.3f}" data-ox="{ox:.3f}" data-oz="{oz:.3f}" data-scale="{scale:.6f}">')
    out.append(f'<rect x="{px:.1f}" y="{py:.1f}" width="{pw:.1f}" height="{ph:.1f}" rx="6" fill="#fcfcfa" stroke="#b8c0cc" stroke-width="1.2"/>')
    title_t = f"{sid} {rid}{proxy_tag} — C_dir={cp_r['C_direct']} | C_cond={cp_r['C_conditional']} ({cp_r['units_conditional']}u) | C_up={cp_r['C_upper']} | St={st_r['selected_count']}"
    out.append(f'<text x="{px + 10:.1f}" y="{py + 18:.1f}" font-size="{12.5 if is_primary else 10.5}" font-weight="700" fill="#1a2433">{_esc(title_t)}</text>')
    sub_t = f"A_elig={_fmt_m2(la_r['A_eligible'])} | A_elig_fin={_fmt_m2(la_r['A_eligible_final'])} m² | A_unknown={_fmt_m2(la_r['A_unknown'])} m² (no UNKNOWN polygon)"
    out.append(f'<text x="{px + 10:.1f}" y="{py + 33:.1f}" font-size="{9.5 if is_primary else 8.5}" fill="#4a5568">{_esc(sub_t)}</text>')
    out.append(f'<clipPath id="{clip_id}"><rect x="{vx:.2f}" y="{vy:.2f}" width="{vw:.2f}" height="{vh:.2f}"/></clipPath>')
    out.append(f'<rect x="{vx:.2f}" y="{vy:.2f}" width="{vw:.2f}" height="{vh:.2f}" fill="#f4f6f2" stroke="#cbd5e1" stroke-width="0.9"/>')
    out.append(f'<g clip-path="url(#{clip_id})">')

    view = (wx0, wz0, wx1, wz1)
    _draw_bg_layers(out, _uid, mg, f"{sid}-{rid}", tx, tz, scale, view)
    out.append(f'<rect id="{_uid(f"regbox-{sid}-{rid}")}" x="{tx(rx0):.2f}" y="{tz(rz0):.2f}" width="{(rx1 - rx0) * scale:.2f}" height="{(rz1 - rz0) * scale:.2f}" fill="none" stroke="#1e293b" stroke-width="1.6" stroke-dasharray="8,4"/>')

    # Candidate external roads (blue dashed for active conditional; red dotted for excluded or NOT_FEASIBLE)
    for cr_id in sorted(rs["roads"]):
        r_info = rs["roads"][cr_id]
        cl = r_info["centerline_info"]["centerline"]
        if r_info["is_existing_reuse"] or not cl or not _pts_in_view(cl, *view):
            continue
        is_nf, is_ex = (r_info["state"] == "NOT_FEASIBLE"), (cr_id in excl)
        if is_nf or is_ex:
            col, dash, cls_lbl = "#c53030", "4,4", ("NOT_FEASIBLE" if is_nf else "EXCLUDED_IN_D")
            reason_s = ",".join(r_info["reasons"]) if is_nf else f"{excl[cr_id]['reason']}({','.join(excl[cr_id]['conflicting_parcel_ids'])})"
            tag = f"{cr_id} [candidate/{cls_lbl}: {reason_s}]"
        else:
            col, dash, cls_lbl = "#2563eb", "10,5", "CONDITIONAL_CANDIDATE"
            tag = f"{cr_id} [candidate/conditional, C={r_info['state']}]"
        out.append(f'<polyline id="{_uid(f"crd-{sid}-{rid}-{cr_id}")}" points="{_poly_pts(cl, tx, tz)}" fill="none" stroke="{col}" stroke-width="3.0" stroke-dasharray="{dash}" data-layer="candidate_road" data-road-state="{cls_lbl}" data-entity-id="{_esc(cr_id)}"><title>{_esc(tag)}</title></polyline>')
        mid = cl[len(cl) // 2]
        if wx0 <= mid[0] <= wx1 and wz0 <= mid[1] <= wz1:
            lbl = f"{cr_id}({'X' if (is_nf or is_ex) else 'cand'})"
            out.append(f'<text x="{tx(mid[0]) + 4:.1f}" y="{tz(mid[1]) - 4:.1f}" font-size="{9.0 if is_primary else 7.5}" font-weight="700" fill="{col}">{_esc(lbl)}</text>')

    # Selected internal streets (purple solid with outer candidate-dashed casing)
    for srec in st_r["selected_streets"]:
        stid, cg, a, b = srec["street_id"], srec["corridor_geometry"], srec["start"], srec["end"]
        out.append(f'<polygon id="{_uid(f"stpoly-{sid}-{rid}-{stid}")}" points="{_poly_pts(cg["polygon"], tx, tz)}" fill="#e9d8fd" fill-opacity="0.7" stroke="#6b21a8" stroke-width="1.6" stroke-dasharray="6,2" data-layer="internal_street" data-entity-id="{_esc(stid)}"><title>{_esc(stid)} [candidate/unbuilt internal street, src={_esc(srec["source_road_id"])}, L={srec["length_m"]}m]</title></polygon>')
        out.append(f'<line x1="{tx(a[0]):.2f}" y1="{tz(a[1]):.2f}" x2="{tx(b[0]):.2f}" y2="{tz(b[1]):.2f}" stroke="#6b21a8" stroke-width="2.0"/>')

    # Parcels (DIRECT green solid; CONDITIONAL orange dashed border; real ID in <title> + short label)
    for p in cp_r["parcels"]:
        pid = p["parcel_id"]
        b0, b1, b2, b3 = [float(v) for v in p["bounds"]]
        fill, stroke, dash = ("#48bb78", "#22543d", "") if p["status"] == "DIRECT" else ("#f6ad55", "#9c4221", ' stroke-dasharray="3,2"')
        tt = f"{pid} | {p['prototype_id']} | {p['status']} | {sid}/{rid} | bldg={p['buildings']} units={p['units']}"
        out.append(f'<rect id="{_uid(f"parcel-{sid}-{rid}-{pid}")}" x="{tx(b0):.2f}" y="{tz(b1):.2f}" width="{(b2 - b0) * scale:.2f}" height="{(b3 - b1) * scale:.2f}" fill="{fill}" fill-opacity="0.78" stroke="{stroke}" stroke-width="1.0"{dash} data-layer="parcel" data-status="{_esc(p["status"])}" data-prototype="{_esc(p["prototype_id"])}" data-entity-id="{_esc(pid)}"><title>{_esc(tt)}</title></rect>')
        if is_primary and (b2 - b0) * scale >= 16.0:
            out.append(f'<text x="{tx((b0 + b2) * 0.5):.1f}" y="{tz((b1 + b3) * 0.5) + 3:.1f}" text-anchor="middle" font-size="7.2" fill="#1a202c">{_esc(_short_parcel_label(pid))}</text>')
    out.append("</g>")

    # Axes ticks (+X right, +Z down, no compass claim) & own scale bar
    out.append(f'<text x="{vx + 2:.1f}" y="{vy + vh + 11:.1f}" font-size="8.0" fill="#475569">X={int(rx0)}</text>')
    out.append(f'<text x="{vx + vw - 2:.1f}" y="{vy + vh + 11:.1f}" text-anchor="end" font-size="8.0" fill="#475569">X={int(rx1)} (+X →)</text>')
    out.append(f'<text x="{px + 4:.1f}" y="{vy + 10:.1f}" font-size="7.8" fill="#475569">Z={int(rz0)}</text>')
    out.append(f'<text x="{px + 4:.1f}" y="{vy + vh - 2:.1f}" font-size="7.8" fill="#475569">Z={int(rz1)}</text>')
    sb_m = _nice_scale_m(wx1 - wx0)
    sb_px = sb_m * scale
    sb_x, sb_y = vx + vw - sb_px - 8.0, vy + vh - 10.0
    out.append(f'<g id="{_uid(f"scale-{sid}-{rid}")}" data-scale-m="{sb_m}"><rect x="{sb_x - 4:.1f}" y="{sb_y - 12:.1f}" width="{sb_px + 8:.1f}" height="18" fill="#ffffff" fill-opacity="0.88" stroke="#94a3b8" stroke-width="0.6"/><line x1="{sb_x:.1f}" y1="{sb_y:.1f}" x2="{sb_x + sb_px:.1f}" y2="{sb_y:.1f}" stroke="#0f172a" stroke-width="2.0"/><text x="{sb_x + sb_px * 0.5:.1f}" y="{sb_y - 3:.1f}" text-anchor="middle" font-size="8.0" fill="#0f172a">{sb_m} m</text></g></g>')


def build_svg(data: dict[str, Any]) -> str:
    used_ids: set[str] = set()

    def _uid(raw: str) -> str:
        _req(raw not in used_ids, f"Duplicate SVG id: {raw}")
        used_ids.add(raw)
        return raw

    ci, rs, fe, mg, li = data["capacity_inventory"], data["road_survey"], data["feasibility"], data["map_geometry"], data["land_inventory"]
    p1 = f"BASE={data['base_sha']} | Mode={li['mode']} | polygon_revision={fe['polygon_revision']} | Axes: +X right, +Z down (world X/Z, no compass/north claim)"
    p2 = f"PHONE_LOW={data['fp_lo']} | DESKTOP_HIGH={data['fp_hi']}"
    p3 = f"Sources: A={li['analyzer_version']} B={ci['analyzer_version']} C={rs['analyzer_version']} D={fe['analyzer_version']} E={BUILDER_VERSION} | Audit panels show exact world geometry; Overview panel is schematic."
    out: list[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 2400 2180" width="2400" height="2180" font-family="DejaVu Sans, Noto Sans CJK TC, Arial, sans-serif">',
        "<title>VICE HORIZON VI — WE-01 Final Survey Map (CROSS_PRESET_COMMON)</title>",
        "<defs>",
        '<pattern id="pat-sitea" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="8" height="8" fill="#ede9fe"/><line x1="0" y1="0" x2="0" y2="8" stroke="#6b46c1" stroke-width="2.2"/></pattern>',
        '<pattern id="pat-beach" width="10" height="10" patternUnits="userSpaceOnUse"><rect width="10" height="10" fill="#fef3c7"/><circle cx="3" cy="3" r="1.1" fill="#b7791f"/><circle cx="8" cy="8" r="1.1" fill="#b7791f"/></pattern>',
        '<pattern id="pat-water" width="12" height="8" patternUnits="userSpaceOnUse"><rect width="12" height="8" fill="#dbeafe"/><line x1="0" y1="4" x2="12" y2="4" stroke="#3b82f6" stroke-width="0.9" stroke-dasharray="4,2"/></pattern>',
        '<pattern id="pat-unknown" width="8" height="8" patternUnits="userSpaceOnUse"><rect width="8" height="8" fill="#e2e8f0"/><path d="M0,0 L8,8 M8,0 L0,8" stroke="#64748b" stroke-width="1.2"/></pattern>',
        "</defs>",
        '<rect x="0" y="0" width="2400" height="2180" fill="#ffffff"/>',
        '<g id="svg-header"><rect x="18" y="14" width="2364" height="102" rx="6" fill="#0f172a"/>',
        '<text x="34" y="42" font-size="20" font-weight="700" fill="#f8fafc">VICE HORIZON VI — WE-01 Final Survey Map (REVISED Primary / INITIAL &amp; ENVELOPE Secondary)</text>',
        f'<text x="34" y="66" font-size="11.5" fill="#cbd5e1">{_esc(p1)}</text>',
        f'<text x="34" y="85" font-size="10.5" fill="#94a3b8">{_esc(p2)}</text>',
        f'<text x="34" y="104" font-size="10.5" fill="#94a3b8">{_esc(p3)}</text></g>',
    ]

    rev_v = fe["scenarios"]["REVISED"]["verdicts"]
    out.append(f'<text x="22" y="142" font-size="15" font-weight="700" fill="#0f172a">PRIMARY SCENARIO: REVISED — D3={_esc(rev_v["D3"]["verdict"])} | 25ha={_esc(rev_v["land_25ha"]["verdict"])} | 40={_esc(rev_v["buildings_40"]["verdict"])} | 60={_esc(rev_v["buildings_60"]["verdict"])} | Road={_esc(rev_v["road_connectivity"]["verdict"])}</text>')
    for idx, rid in enumerate(REGION_ORDER):
        _render_panel(out, used_ids, data, "REVISED", rid, 20.0 + idx * 792.0, 150.0, 776.0, 720.0, True)

    for row_i, sid in enumerate(("INITIAL", "ENVELOPE")):
        y_top = 898.0 + row_i * 448.0
        sv = fe["scenarios"][sid]["verdicts"]
        out.append(f'<text x="22" y="{y_top:.1f}" font-size="13.5" font-weight="700" fill="#1e293b">SECONDARY SCENARIO: {sid} — D3={_esc(sv["D3"]["verdict"])} | 25ha={_esc(sv["land_25ha"]["verdict"])} | 40={_esc(sv["buildings_40"]["verdict"])} | 60={_esc(sv["buildings_60"]["verdict"])} | Road={_esc(sv["road_connectivity"]["verdict"])}</text>')
        for idx, rid in enumerate(REGION_ORDER):
            _render_panel(out, used_ids, data, sid, rid, 20.0 + idx * 792.0, y_top + 8.0, 776.0, 412.0, False)

    # Bottom band: Global Road Overview (Schematic), Legend, Verdict Comparison & Limitations
    by, bh = 1796.0, 368.0
    ov_x, ov_y, ov_w, ov_h = 20.0, by, 776.0, bh
    all_x = [p[0] for r in mg["roads"] for p in r["centerline"]] + [v for b in ci["scenarios_internal_order"]["ENVELOPE"].values() for v in (b[0], b[2])]
    all_z = [p[-1] for r in mg["roads"] for p in r["centerline"]] + [v for b in ci["scenarios_internal_order"]["ENVELOPE"].values() for v in (b[1], b[3])]
    gx0, gx1, gz0, gz1 = min(all_x) - 60.0, max(all_x) + 60.0, min(all_z) - 60.0, max(all_z) + 60.0
    gvx, gvy, gvw, gvh = ov_x + 36.0, ov_y + 38.0, ov_w - 50.0, ov_h - 62.0
    gsc = min(gvw / (gx1 - gx0), gvh / (gz1 - gz0))
    gox, goz = gvx + (gvw - (gx1 - gx0) * gsc) * 0.5, gvy + (gvh - (gz1 - gz0) * gsc) * 0.5
    gtx, gtz = (lambda x: gox + (x - gx0) * gsc), (lambda z: goz + (z - gz0) * gsc)
    out.append(f'<g id="panel-global-overview" data-schematic="true"><rect x="{ov_x:.1f}" y="{ov_y:.1f}" width="{ov_w:.1f}" height="{ov_h:.1f}" rx="6" fill="#fcfcfa" stroke="#94a3b8" stroke-width="1.2"/>')
    out.append(f'<text x="{ov_x + 10:.1f}" y="{ov_y + 18:.1f}" font-size="11.5" font-weight="700" fill="#0f172a">Global Road Overview — 示意／非完整審計覆蓋 (Schematic, known geometry only)</text>')
    out.append(f'<text x="{ov_x + 10:.1f}" y="{ov_y + 31:.1f}" font-size="9.0" fill="#475569">World +X right / +Z down (no compass claim); un-audited areas omitted</text>')
    out.append(f'<clipPath id="clip-global-ov"><rect x="{gvx:.2f}" y="{gvy:.2f}" width="{gvw:.2f}" height="{gvh:.2f}"/></clipPath>')
    out.append(f'<rect x="{gvx:.2f}" y="{gvy:.2f}" width="{gvw:.2f}" height="{gvh:.2f}" fill="#f8fafc" stroke="#cbd5e1" stroke-width="0.9"/><g clip-path="url(#clip-global-ov)">')
    _draw_bg_layers(out, _uid, mg, "global", gtx, gtz, gsc, None)
    for cr_id in sorted(rs["roads"]):
        r_info = rs["roads"][cr_id]
        if r_info["is_existing_reuse"] or not r_info["centerline_info"]["centerline"]:
            continue
        col, dash = ("#c53030", "3,3") if r_info["state"] == "NOT_FEASIBLE" else ("#2563eb", "6,3")
        out.append(f'<polyline id="{_uid(f"ov-crd-{cr_id}")}" points="{_poly_pts(r_info["centerline_info"]["centerline"], gtx, gtz)}" fill="none" stroke="{col}" stroke-width="2.0" stroke-dasharray="{dash}"/>')
    for rid in REGION_ORDER:
        b0, b1, b2, b3 = [float(v) for v in ci["scenarios_internal_order"]["REVISED"][rid]]
        out.append(f'<rect x="{gtx(b0):.2f}" y="{gtz(b1):.2f}" width="{(b2 - b0) * gsc:.2f}" height="{(b3 - b1) * gsc:.2f}" fill="none" stroke="#0f172a" stroke-width="1.4" stroke-dasharray="5,3"/><text x="{gtx((b0 + b2) * 0.5):.1f}" y="{gtz((b1 + b3) * 0.5):.1f}" text-anchor="middle" font-size="10.5" font-weight="700" fill="#0f172a">{rid}</text>')
    out.append("</g>")
    gsb_m = _nice_scale_m(gx1 - gx0)
    gsb_px = gsb_m * gsc
    out.append(f'<g id="scale-global-ov" data-scale-m="{gsb_m}"><line x1="{gvx + gvw - gsb_px - 8:.1f}" y1="{gvy + gvh - 8:.1f}" x2="{gvx + gvw - 8:.1f}" y2="{gvy + gvh - 8:.1f}" stroke="#0f172a" stroke-width="2.0"/><text x="{gvx + gvw - gsb_px * 0.5 - 8:.1f}" y="{gvy + gvh - 12:.1f}" text-anchor="middle" font-size="8.5" fill="#0f172a">{gsb_m} m</text></g><text x="{gvx:.1f}" y="{gvy + gvh + 13:.1f}" font-size="8.5" fill="#475569">+X → (m) | +Z ↓ (m)</text></g>')

    # 2. Global Legend
    lg_x, lg_y, lg_w = 812.0, by, 776.0
    out.append(f'<g id="panel-legend"><rect x="{lg_x:.1f}" y="{lg_y:.1f}" width="{lg_w:.1f}" height="{bh:.1f}" rx="6" fill="#fcfcfa" stroke="#94a3b8" stroke-width="1.2"/><text x="{lg_x + 12:.1f}" y="{lg_y + 22:.1f}" font-size="13" font-weight="700" fill="#0f172a">Global Legend (Line styles + Hatches + Text; never colour alone)</text>')
    leg_items = [
        ("line", "#4a5568", "", "Existing verified road (solid dark grey)"),
        ("line", "#2563eb", "10,5", "Candidate external road — unbuilt / conditional (blue dashed)"),
        ("rect", "#e9d8fd", "#6b21a8", "Selected internal street — unbuilt / candidate (purple solid + dashed border)"),
        ("line", "#c53030", "4,4", "Rejected / excluded / NOT_FEASIBLE candidate road (red dotted + reason)"),
        ("rect", "#48bb78", "#22543d", "DIRECT residential parcel (green solid border; full ID in title &amp; report)"),
        ("rect_dash", "#f6ad55", "#9c4221", "CONDITIONAL residential parcel (orange dashed border; full ID in title &amp; report)"),
        ("pat", "url(#pat-sitea)", "#6b46c1", "Site A protection &amp; buildings (purple diagonal hatch)"),
        ("pat", "url(#pat-beach)", "#b7791f", "Beach region (sand stipple + dashed outline)"),
        ("pat", "url(#pat-water)", "#2b6cb0", "Water region (blue horizontal dash hatch)"),
        ("pat", "url(#pat-unknown)", "#64748b", "LX / UNKNOWN (cross-hatch; no UNKNOWN polygon in data -> panel note only, no invented shape)"),
    ]
    for i, (kind, c1, c2, lbl) in enumerate(leg_items):
        ry = lg_y + 44.0 + i * 31.0
        if kind == "line":
            da = f' stroke-dasharray="{c2}"' if c2 else ""
            out.append(f'<line x1="{lg_x + 16:.1f}" y1="{ry:.1f}" x2="{lg_x + 62:.1f}" y2="{ry:.1f}" stroke="{c1}" stroke-width="3.2"{da}/>')
        elif kind == "rect":
            out.append(f'<rect x="{lg_x + 16:.1f}" y="{ry - 8:.1f}" width="46" height="16" fill="{c1}" stroke="{c2}" stroke-width="1.5"/>')
        elif kind == "rect_dash":
            out.append(f'<rect x="{lg_x + 16:.1f}" y="{ry - 8:.1f}" width="46" height="16" fill="{c1}" stroke="{c2}" stroke-width="1.5" stroke-dasharray="3,2"/>')
        else:
            out.append(f'<rect x="{lg_x + 16:.1f}" y="{ry - 8:.1f}" width="46" height="16" fill="{c1}" stroke="{c2}" stroke-width="1.2"/>')
        out.append(f'<text x="{lg_x + 74:.1f}" y="{ry + 4:.1f}" font-size="10.5" fill="#1e293b">{lbl}</text>')
    out.append("</g>")

    # 3. Scenario Verdicts & Key Limitations Summary
    vx_b, vy_b, vw_b = 1604.0, by, 776.0
    out.append('<g id="panel-verdicts">')
    out.append(f'<rect x="{vx_b:.1f}" y="{vy_b:.1f}" width="{vw_b:.1f}" height="{bh:.1f}" rx="6" fill="#fcfcfa" stroke="#94a3b8" stroke-width="1.2"/>')
    out.append(f'<text x="{vx_b + 12:.1f}" y="{vy_b + 22:.1f}" font-size="13" font-weight="700" fill="#0f172a">Scenario Verdicts, Road Exclusions &amp; Audit Limitations</text>')
    cy = vy_b + 44.0
    for sid in SCENARIO_ORDER:
        sv = fe["scenarios"][sid]["verdicts"]
        la_t = fe["scenarios"][sid]["land_accounting"]["totals"]
        ex_s = fe["scenarios"][sid]["excluded_sources"]
        ex_txt = ", ".join(f"{k}:{v['reason']}({','.join(v['conflicting_parcel_ids'])})" for k, v in sorted(ex_s.items())) or "none"
        out.append(f'<text x="{vx_b + 14:.1f}" y="{cy:.1f}" font-size="10.5" font-weight="700" fill="#0f172a">{sid}: D3={_esc(sv["D3"]["verdict"])}</text>')
        cy += 15.0
        l_v = f"  25ha={sv['land_25ha']['verdict']} (A_pos={_fmt_m2(la_t['A_possible'])}) | 40={sv['buildings_40']['verdict']} | 60={sv['buildings_60']['verdict']} | Road={sv['road_connectivity']['verdict']}"
        out.append(f'<text x="{vx_b + 14:.1f}" y="{cy:.1f}" font-size="9.2" fill="#334155">{_esc(l_v)}</text>')
        cy += 14.0
        el_v = f"  A_eligible={_fmt_m2(la_t['A_eligible'])} / A_eligible_final={_fmt_m2(la_t['A_eligible_final'])} m² | Excl: {ex_txt}"
        out.append(f'<text x="{vx_b + 14:.1f}" y="{cy:.1f}" font-size="9.0" fill="#475569">{_esc(el_v)}</text>')
        cy += 20.0
    nf_lines = [f"{k}: {v['state']} ({','.join(v['reasons'])}; max_grade={v['grade_info']['max_step_grade_pct']}%)" for k, v in sorted(rs["roads"].items()) if v["state"] == "NOT_FEASIBLE"]
    opt_targets = sorted({o["target_segment_id"] for r in rs["roads"].values() for o in r["optional_extension_links"]})
    notes = [
        "Failed candidate roads: " + ("; ".join(nf_lines) if nf_lines else "none"),
        f"Road beach total (C): {_fmt_m2(rs['summary']['total_beach_encroachment_m2'])} m² | Optional UNVERIFIED: {','.join(opt_targets) or 'none'}",
        "UNVERIFIED = search insufficient (not proven impossible). 60-building target does not gate D3.",
        "Regions with proxy_used=true (PROXY) represent flat proxy capacity only, not verified hillside construction.",
        FIXED_B8_PARAGRAPH,
        f"{FOLLOWUP_HEADING} — Study output is NOT construction authorization.",
    ]
    cy += 6.0
    for note in notes:
        out.append(f'<text x="{vx_b + 14:.1f}" y="{cy:.1f}" font-size="9.3" fill="#1e293b">{_esc(note)}</text>')
        cy += 18.0
    out.append("</g></svg>\n")
    return _sanitize_text("\n".join(out))


# --- Markdown Report Builder (G0-E7) ---

def _tbl(lines: list[str], headers: list[str], rows: list[list[Any]]) -> None:
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join("---" for _ in headers) + " |")
    for r in rows:
        lines.append("| " + " | ".join(str(c) for c in r) + " |")
    lines.append("")


def build_markdown(data: dict[str, Any]) -> str:
    li, ci, rs, st, cp, fe, mg = (
        data["land_inventory"], data["capacity_inventory"], data["road_survey"],
        data["internal_streets"], data["conditional_parcels"], data["feasibility"], data["map_geometry"],
    )
    lines: list[str] = [
        "# VICE HORIZON VI — WE-01 最終勘查報告（Final Survey Report）", "",
        "## 0. 來源溯源與完整性資訊（Provenance）", "",
    ]
    prov_rows = [
        ["Audit Game BASE", f"`{data['base_sha']}`"],
        ["PHONE_LOW `static_fingerprint`", f"`{data['fp_lo']}`"],
        ["DESKTOP_HIGH `static_fingerprint`", f"`{data['fp_hi']}`"],
        ["Preset Mode", f"`{li['mode']}`"],
        ["`polygon_revision`", f"`{fe['polygon_revision']}`"],
        ["Builder Version", f"`{BUILDER_VERSION}`"],
    ] + [[f"`{fn}` SHA-256", f"`{data['file_hashes'][fn]}`"] for fn in DATA_FILES]
    _tbl(lines, ["項目", "數值"], prov_rows)

    # 7.1 Executive summary
    lines += [
        "## 1. 執行摘要（Executive Summary）", "",
        "本報告為 WE-01（T-016A/B/C/D）已完成唯讀離線審計產物之統整呈現，**未重算任何面積、容量、坡度或裁定**，亦不構成施工授權或世界擴張批准。`ENVELOPE` 之 `CONDITIONAL` 裁定僅表示在調查外框下具備條件可行路徑，不得解讀為已批准全面擴張；`REVISED` 為主要規劃研究情境，目前尚未取得完整可行性證明。", "",
    ]
    _tbl(lines, ["Scenario", "`land_25ha`", "`buildings_40`", "`buildings_60` (不門控 D3)", "`road_connectivity`", "`D3`"], [
        [f"`{sid}`"] + [f"`{fe['scenarios'][sid]['verdicts'][vk]['verdict']}`" for vk in VERDICT_ORDER]
        for sid in SCENARIO_ORDER
    ])

    # 7.2 A/B/C/D staged results
    lines += [
        "## 2. A/B/C/D 分階段審計結果", "",
        f"### 2.1 T-016A 土地分類（`land_inventory.json`, `{li['analyzer_version']}`）", "",
        f"跨畫質共同模式 `{li['mode']}`（網格步長 `{li['grid_step_m']} m`，面積守恆容差 `{li['conservation_tolerance_m2']} m²`）：", "",
    ]
    a_rows = []
    cls_k = ("L0", "L1", "L2", "L3", "L4", "L5", "LX")
    for r in sorted(li["regions"], key=lambda x: REGION_ORDER.index(x["id"])):
        for scope, ak, ck in (("initial", "initial_polygon_area_m2", "common_initial_class_areas_m2"), ("survey", "survey_polygon_area_m2", "common_survey_class_areas_m2")):
            a_rows.append([f"`{r['id']}`", f"`{scope}`", _fmt_m2(r[ak])] + [_fmt_m2(r[ck][k]) for k in cls_k] + [_fmt_num(r["common_conservation_error_m2"][scope], 3)])
    uc = li["union_summary"]["common"]
    for scope, ak, ck in (("initial", "initial_union_area_m2", "initial_class_areas_m2"), ("survey", "survey_union_area_m2", "survey_class_areas_m2")):
        a_rows.append(["`UNION`", f"`{scope}`", _fmt_m2(uc[ak])] + [_fmt_m2(uc[ck][k]) for k in cls_k] + [_fmt_num(uc["conservation_error_m2"][scope], 3)])
    _tbl(lines, ["區域", "範圍", "總面積 (m²)", "L0", "L1", "L2", "L3", "L4", "L5", "LX", "守恆誤差 (m²)"], a_rows)

    lines += [
        f"### 2.2 T-016B 直接與初步住宅容量（`capacity_inventory.json`, `{ci['analyzer_version']}`）", "",
        "T-016B 提供直接容量 `C_direct`、初步容量 `C_preliminary` 與容量上界 `C_upper`（中間階段分析；最終條件容量 `C_conditional` 一律以 T-016D 為準）：", "",
    ]
    _tbl(lines, ["Scenario", "Region", "`C_direct`", "`units_direct`", "`C_preliminary`", "`C_upper`", "`proxy_used`"], [
        [f"`{sid}`", f"`{rid}`", _fmt_int(bc["C_direct"]), _fmt_int(bc["units_direct"]), _fmt_int(bc["C_preliminary"]), _fmt_int(bc["C_upper"]), f"`{'PROXY' if bc['proxy_used'] else 'false'}`"]
        for sid in SCENARIO_ORDER for rid in REGION_ORDER for bc in (ci["scenarios"][sid]["regions"][rid]["capacities"],)
    ])

    lines += [
        f"### 2.3 T-016C 外部候選道路分析（`road_survey.json`, `{rs['analyzer_version']}`）", "",
        f"候選道路總新增長度 `{_fmt_num(rs['summary']['total_new_road_length_m'], 3)} m`，總走廊面積 `{_fmt_num(rs['summary']['total_new_corridor_area_m2'], 3)} m²`，總海灘侵占 `{_fmt_m2(rs['summary']['total_beach_encroachment_m2'])} m²`（T-016D 在特定情境配置排除道路時，不改寫 T-016C 自身工程裁定）：", "",
    ]
    c_rows = []
    for cr_id in sorted(rs["roads"]):
        r = rs["roads"][cr_id]
        opts = ", ".join(f"{o['target_segment_id']}:{o['status']}({o['reason']})" for o in r["optional_extension_links"]) or "none"
        mg_pct = r["grade_info"]["max_step_grade_pct"]
        c_rows.append([f"`{cr_id}`", f"`{r['state']}`", f"`{r['geom_corridor_state']}`", _fmt_num(r["new_length_m"], 3), _fmt_num(r["new_corridor_area_m2"], 3), ("N/A" if mg_pct is None else f"{mg_pct:.3f}%"), _fmt_m2(r["beach_encroachment_m2"]), f"`{', '.join(r['reasons']) or 'none'}`", f"`{opts}`"])
    _tbl(lines, ["Road ID", "C `state`", "`geom_corridor_state`", "`new_length_m`", "`new_corridor_area_m2`", "`max_step_grade_pct`", "`beach_encroachment_m2`", "`reasons`", "`optional_extension_links`"], c_rows)

    lines += [
        f"### 2.4 T-016D 內部街道與搜尋限制（`internal_streets.json`, `{st['analyzer_version']}`）", "",
        "T-016D 依已核准候選預算上限（1,280／區／情境；每區最多 3 條、每條 30–150 m）進行確定性貪婪搜尋。保留 D23 規則：`SEARCH_BUDGET_EXHAUSTED` 不等於 `NOT FEASIBLE`，有界搜尋未找到解亦不構成全域不可行證明。", "",
    ]
    _tbl(lines, ["Scenario", "Region", "`candidate_count`", "`checked_count`", "`tier1_passed_count`", "`zero_gain_count`", "`tier2_verified_count`", "`selected_count`", "`search_budget_exhausted`"], [
        [f"`{sid}`", f"`{rid}`", _fmt_int(sr["candidate_count"]), _fmt_int(sr["checked_count"]), _fmt_int(sr["tier1_passed_count"]), _fmt_int(sr["zero_gain_count"]), _fmt_int(sr["tier2_verified_count"]), _fmt_int(sr["selected_count"]), f"`{sr['search_budget_exhausted']}`"]
        for sid in SCENARIO_ORDER for rid in REGION_ORDER for sr in (st["scenarios"][sid][rid],)
    ])

    # 7.3 Regional land & capacity per scenario
    lur0 = fe["scenarios"]["REVISED"]["land_accounting"]["regions"]["B1"]["land_use_reference"]
    rb_res, rb_rd = lur0["reference_bands_pct"]["residential"], lur0["reference_bands_pct"]["roads"]
    lines += [
        "## 3. 各情境分區土地與住宅容量明細", "",
        f"注意：`C_conditional` **已包含** `C_direct`（`C_additional = C_conditional - C_direct`），嚴禁重複加總；`buildings`（棟數）與 `units_conditional`（戶數，如 R08 為 1 棟 4 戶）分欄呈現；`A_eligible` 與 `A_eligible_final` 以原欄位名分別呈現。土地利用參考帶（residential {rb_res[0]}–{rb_res[1]}%、roads {rb_rd[0]}–{rb_rd[1]}%）僅供參考（`informational_only: {str(lur0['informational_only']).lower()}`, `hard_gate: {str(lur0['hard_gate']).lower()}`）。", "",
    ]
    la_cols = ("A_gross", "A_direct", "A_conditional", "A_new_road", "A_protected", "A_unavailable", "A_unknown", "A_eligible", "A_eligible_final", "A_possible")
    for idx, sid in enumerate(SCENARIO_ORDER, 1):
        la_s = fe["scenarios"][sid]["land_accounting"]
        lines += [f"### 3.{idx} 情境 `{sid}`", "", "#### 土地面積守恆（`feasibility.json` `land_accounting`）", ""]
        l_rows = [
            [f"`{rid}`"] + [_fmt_m2(la_s["regions"][rid][k]) for k in la_cols] + [
                _fmt_num(la_s["regions"][rid]["conservation_error_m2"], 3),
                _fmt_m2(la_s["regions"][rid]["beach_encroachment_m2"]),
                f"{la_s['regions'][rid]['land_use_reference']['residential_share_pct']:.3f}% / {la_s['regions'][rid]['land_use_reference']['new_road_share_pct']:.3f}%",
            ]
            for rid in REGION_ORDER
        ]
        l_rows.append(["`TOTAL`"] + [_fmt_m2(la_s["totals"][k]) for k in la_cols] + ["—", _fmt_m2(la_s["totals"]["beach_encroachment_m2"]), "—"])
        _tbl(lines, ["Region"] + [f"`{k}`" for k in la_cols] + ["`conservation_error_m2`", "`beach_encroachment_m2`", "參考占比 res/road (info)"], l_rows)

        lines += ["#### 分區住宅容量（`conditional_parcels.json` + B `C_preliminary`）", ""]
        ext_acc = fe["scenarios"][sid]["verdicts"]["road_connectivity"]["per_region_external"]
        cap_rows = []
        for rid in REGION_ORDER:
            pr, c_pre = cp["scenarios"][sid][rid], ci["scenarios"][sid]["regions"][rid]["capacities"]["C_preliminary"]
            p_mix = ", ".join(f"{k}:{v}" for k, v in sorted(pr["prototype_counts"].items())) or "none"
            pxy = "PROXY（平地代理，非已驗證山坡施工）" if pr["proxy_used"] else "false"
            cap_rows.append([f"`{rid}`", _fmt_int(pr["C_direct"]), _fmt_int(c_pre), _fmt_int(pr["C_conditional"]), _fmt_int(pr["C_additional"]), _fmt_int(pr["units_conditional"]), _fmt_int(pr["C_upper"]), _fmt_int(pr["C_phone_low"]), _fmt_int(pr["C_desktop_high"]), _fmt_int(pr["C_common"]), f"`{p_mix}`", pxy, f"`{ext_acc[rid]}`"])
        _tbl(lines, ["Region", "`C_direct`", "`C_preliminary`", "`C_conditional` (棟)", "`C_additional`", "`units_conditional` (戶)", "`C_upper`", "`C_phone_low`", "`C_desktop_high`", "`C_common` (`CROSS_PRESET_COMMON`)", "`prototype_counts`", "`proxy_used`", "外部道路接入"], cap_rows)

    # 7.4 Roads, beach, exclusions & engineering dependencies
    opt_targets = sorted({o["target_segment_id"] for r in rs["roads"].values() for o in r["optional_extension_links"]})
    lines += [
        "## 4. 道路、海灘侵占與工程相依報告", "",
        f"- 既有道路幾何（`map_geometry.json`）：共 `{len(mg['roads'])}` 條既有路段；Site A 保護區與建物共 `{len(mg['site_a'])}` 個多邊形；海灘 `{len(mg['beach_regions'])}` 區、水域 `{len(mg['water_regions'])}` 區。",
        f"- 可選未驗證延伸連接（`optional_extension_links`）：`{', '.join(opt_targets) or 'none'}` 僅列為可選且 `status: UNVERIFIED`，非所有候選道路之必要工程。", "",
        "### 4.1 逐情境排除道路與衝突地塊（`excluded_sources`）", "",
    ]
    ex_rows = []
    for sid in SCENARIO_ORDER:
        excl = fe["scenarios"][sid]["excluded_sources"]
        if not excl:
            ex_rows.append([f"`{sid}`", "`none`", "—", "—", "—", "本情境無候選道路因直接地塊衝突遭排除"])
        else:
            for erid, edet in sorted(excl.items()):
                c_st = rs["roads"][erid]["state"]
                ex_rows.append([f"`{sid}`", f"`{erid}`", f"`{c_st}`", f"`{edet['reason']}`", f"`{', '.join(edet['conflicting_parcel_ids'])}`", f"保留直接地塊不刪除或移動；C 自身裁定維持 `{c_st}`"])
    _tbl(lines, ["Scenario", "Excluded Road", "C 自身狀態", "D 排除原因", "衝突直接地塊 ID", "說明"], ex_rows)

    lines += ["### 4.2 選定內部街道（未建造／候選工程）", ""]
    st_rows = [
        [f"`{sid}`", f"`{rid}`", f"`{sr['street_id']}`", f"`{sr['source_road_id']}`", _fmt_num(sr["length_m"], 1), f"{sr['max_grade_pct']:.3f}%", _fmt_num(sr["junction_run_m"], 3), f"`{sr['external_connection']}`", f"`{' -> '.join(sr['dependency_chain']) or 'none'}`", f"`{sr['verification_status']}`", f"`{sr['existing']}`"]
        for sid in SCENARIO_ORDER for rid in REGION_ORDER for sr in st["scenarios"][sid][rid]["selected_streets"]
    ]
    _tbl(lines, ["Scenario", "Region", "`street_id`", "`source_road_id`", "`length_m`", "`max_grade_pct`", "`junction_run_m`", "`external_connection`", "`dependency_chain`", "`verification_status`", "`existing`"], st_rows)

    # 7.5 Feasibility verdicts
    lines += [
        "## 5. 可行性裁定（Feasibility Verdicts）", "",
        "所有裁定原樣取自 `feasibility.json`，不進行重新計算。`buildings_60` 為理想目標，依 `gates_d3` 欄位單獨呈報且**不作為 `D3` 門控條件**。`UNVERIFIED`（如 `SEARCH_INSUFFICIENT_UNPROVEN`）僅代表搜尋不足、尚未完成可行性證明，不等於已證明不可行。", "",
    ]
    for idx, sid in enumerate(SCENARIO_ORDER, 1):
        sv = fe["scenarios"][sid]["verdicts"]
        v25, vr, vd3 = sv["land_25ha"], sv["road_connectivity"], sv["D3"]
        v_rows = [[
            "`land_25ha`", f"`{v25['verdict']}`",
            f"`A_gross_total`={_fmt_m2(v25['A_gross_total'])}, `A_possible_total`={_fmt_m2(v25['A_possible_total'])}, `A_direct_total`={_fmt_m2(v25['A_direct_total'])}, `A_conditional_total`={_fmt_m2(v25['A_conditional_total'])} m²",
            f"`{', '.join(v25['reasons'])}`",
        ]]
        for bk in ("buildings_40", "buildings_60"):
            vb = sv[bk]
            tg = ", ".join(f"{r}:{vb['targets'][r]}" for r in REGION_ORDER)
            ex = [f"{k}={vb[k]}" for k in ("C_direct_total", "C_conditional_total", "gates_d3") if k in vb]
            ex += [f"{k}={','.join(vb[k])}" for k in ("regions_short", "regions_below_c_upper") if vb.get(k)]
            v_rows.append([f"`{bk}`", f"`{vb['verdict']}`", f"targets=({tg}); {'; '.join(ex)}", f"`{vb['reason']}`"])
        ext_s = ", ".join(f"{r}:{vr['per_region_external'][r]}" for r in REGION_ORDER)
        v_rows.append(["`road_connectivity`", f"`{vr['verdict']}`", f"per_region_external=({ext_s}); `uses_conditional_roads_or_streets`={vr['uses_conditional_roads_or_streets']}", "`T-016C + D chains`"])
        v_rows.append(["`D3`", f"`{vd3['verdict']}`", f"inputs=({', '.join(f'{k}:{v}' for k, v in sorted(vd3['inputs'].items()))})", "`worst(land_25ha, buildings_40, road_connectivity)`"])
        lines += [f"### 5.{idx} 情境 `{sid}` 裁定與原始證據", ""]
        _tbl(lines, ["Verdict Item", "Verdict", "Targets / Evidence", "Reasons"], v_rows)

    # 7.6 Performance baseline (Gate B8) & 7.7 Follow-up recommendations (NOT authorized)
    excl_ids = sorted({erid for sid in SCENARIO_ORDER for erid in fe["scenarios"][sid]["excluded_sources"]})
    nf_ids = sorted(k for k, v in rs["roads"].items() if v["state"] == "NOT_FEASIBLE")
    proxy_regs = sorted({rid for sid in SCENARIO_ORDER for rid in REGION_ORDER if cp["scenarios"][sid][rid]["proxy_used"]})
    lines += [
        "## 6. 效能基準狀態（Gate B8）", "",
        FIXED_B8_PARAGRAPH, "",
        "T-016E 為純離線唯讀報告建構工具，不執行遊戲 runtime 效能量測，亦不使用估計 FPS 或 headless FPS 取代實測數據。", "",
        "### 6.1 Gate B8 正式量測附錄引用（待 Claude 合併 E 後獨立量測補附）", "",
        "- 狀態：`PENDING`（由 Claude 依 WE-01 v1.2 §13 於 `PHONE_LOW` / `TABLET_MED` / `DESKTOP_HIGH` 六處地點量測後另附獨立 B8 附錄，不手改本確定性報告）。", "",
        f"## 7. {FOLLOWUP_HEADING}", "",
        "以下項目**僅為基於本次審計 JSON 證據之後續研究建議，尚未登記任務，亦未獲任何施工或製作授權**：", "",
        "1. **低於目標分區之額外合法地塊或候選區邊界研究**：針對處於 `UNVERIFIED`（搜尋不足，未證明不可行）之分區，評估是否以替代街道幾何或候選邊界修訂提升可達容量。",
        f"2. **直接地塊衝突道路替代方案**：針對配置衝突遭排除之外部候選道路（`{', '.join(excl_ids) or 'none'}`），評估改線或保留既有接點方案。",
        f"3. **山坡地形與地基工程研究**：針對平地代理分區（`{', '.join(proxy_regs) or 'none'}` `PROXY`）及 `NOT_FEASIBLE` 道路（`{', '.join(nf_ids) or 'none'}`），另案研究地形整地、地基與線型工程。",
        f"4. **海灘景觀保護與可選延伸連接權衡**：檢視候選道路海灘侵占與景觀保留取捨，以及可選未驗證延伸（`{', '.join(opt_targets) or 'none'}`）之獨立可行性。",
        "5. **區域串流與住宅 LOD 規劃**：配合未來 Gate B8 實測基準評估行動裝置繪製與物理負載。",
        "6. **`ENVELOPE` 與 `REVISED` 範圍比較**：比較外框條件可行方案與修訂方案之土地與工程需求，再由專案擁有者決定後續方向。", "",
        "## 8. 附錄：各情境地塊明細（Parcel Appendix）", "",
    ]
    for idx, sid in enumerate(SCENARIO_ORDER, 1):
        lines += [f"### 8.{idx} 情境 `{sid}` 地塊清單", ""]
        p_rows = [
            [f"`{rid}`", f"`{p['parcel_id']}`", f"`{p['prototype_id']}`", f"`{p['status']}`", p["buildings"], p["units"], f"`{p['source_road_id'] or 'none'}`", f"`{p['internal_street_id'] or 'none'}`", f"`{' -> '.join(p['dependency_chain']) or 'none'}`"]
            for rid in REGION_ORDER for p in cp["scenarios"][sid][rid]["parcels"]
        ]
        _tbl(lines, ["Region", "`parcel_id`", "`prototype_id`", "`status`", "`buildings`", "`units`", "`source_road_id`", "`internal_street_id`", "`dependency_chain`"], p_rows)

    return _sanitize_text("\n".join(lines))


# --- Atomic build & CLI ---

def build_artifacts(input_dir: str | Path, out_dir: str | Path) -> dict[str, Any]:
    t0 = time.monotonic()
    in_p = Path(input_dir).resolve()
    out_p = Path(out_dir).resolve()
    _req(in_p != out_p, "Output directory must not equal input directory")

    data = load_and_verify_inputs(in_p)
    svg_text = build_svg(data)
    md_text = build_markdown(data)

    # Self-verify XML well-formedness before promoting from temp dir
    try:
        ET.fromstring(svg_text.encode("utf-8"))
    except ET.ParseError as exc:
        raise BuildError(f"Generated SVG failed XML parse: {exc}") from exc

    svg_bytes = svg_text.encode("utf-8")
    md_bytes = md_text.encode("utf-8")
    elapsed = round(time.monotonic() - t0, 4)
    meta = {
        "builder_version": BUILDER_VERSION,
        "elapsed_s": elapsed,
        "world_survey_svg_sha256": _sha256_bytes(svg_bytes),
        "survey_report_md_sha256": _sha256_bytes(md_bytes),
    }
    meta_bytes = (json.dumps(meta, indent=2, sort_keys=True) + "\n").encode("utf-8")

    out_p.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=out_p, prefix=".we01e_tmp_") as td:
        td_p = Path(td)
        (td_p / "world_survey.svg").write_bytes(svg_bytes)
        (td_p / "survey_report.md").write_bytes(md_bytes)
        (td_p / "report_meta.json").write_bytes(meta_bytes)
        for fn in ("world_survey.svg", "survey_report.md", "report_meta.json"):
            os.replace(td_p / fn, out_p / fn)
    return meta


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="WE-01E (T-016E) Final Survey Map (world_survey.svg) & Report (survey_report.md) Builder.")
    ap.add_argument("--input-dir", required=True, help="Directory holding the 9 verified WE-01E input JSON files.")
    ap.add_argument("--out", required=True, help="Output directory for world_survey.svg, survey_report.md, report_meta.json.")
    args = ap.parse_args(argv)
    try:
        meta = build_artifacts(args.input_dir, args.out)
    except BuildError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"OK [WE-01E] svg={meta['world_survey_svg_sha256'][:12]} md={meta['survey_report_md_sha256'][:12]} elapsed={meta['elapsed_s']:.3f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
