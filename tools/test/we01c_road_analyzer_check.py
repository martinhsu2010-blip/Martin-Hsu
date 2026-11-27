#!/usr/bin/env python3
"""WE-01C (T-016C) Road Feasibility Survey check suite (R01-R18, D-054a G0-C1..C10, 21 mutants, real samples)."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/test"))
import we01a_land_analyzer as W  # noqa: E402
from we01a_land_analyzer_check import _expect_fail, _fp, _rect, _write_dump, make_dump  # noqa: E402
import we01b_capacity_analyzer as B  # noqa: E402
import we01c_road_analyzer as C  # noqa: E402

FX = ROOT / "tools/fixtures/we01"
BASE_SHA = "84319439243b51aa8d119e33eb62a0637feea887"


def _check(cond: bool, msg: str = "") -> None:
    assert cond, msg


def _expect_err(label: str, fn) -> None:
    try:
        fn()
    except (AssertionError, C.RoadError, B.CapacityError, W.ValidationError):
        return
    raise AssertionError(f"Expected FAILURE but stayed GREEN: {label}")


def _cor_grid(gid: str, x0: int, z0: int, x1: int, z1: int, hfn=None) -> dict:
    fn = hfn or (lambda x, z: 0.0)
    nx, nz = x1 - x0 + 1, z1 - z0 + 1
    return {
        "id": gid, "region_id": "ROAD_CORRIDOR", "origin_x": x0, "origin_z": z0, "step_m": 1,
        "nx": nx, "nz": nz, "heights": [fn(x0 + ix, z0 + iz) for iz in range(nz) for ix in range(nx)],
        "source": "runtime_terrainHeight", "sample_method": "DIRECT_RUNTIME",
    }


def _seg(sid: str, cl: list[list[float]], w: float = 10.0, elev: str = "GROUND", fp_ids: list[str] | None = None, ver: str = "RUNTIME_VERIFIED") -> dict:
    return {
        "id": sid, "start_node_id": None, "end_node_id": None, "centerline": cl,
        "carriageway_width_m": w, "sidewalk_left_m": None, "sidewalk_right_m": None,
        "corridor_footprint_ids": list(fp_ids or []), "elevation_type": elev,
        "traffic_route_ids": [], "source_ref": "syn_road", "verification": ver,
    }


def _road_spec(rid: str, cpts: list[list[float]], kind: str = "NORMAL", cw: float = 7.0, hw: float = 5.5, r: float = 25.0, g: float = 6.0, reuse: bool = False) -> dict:
    return {"id": rid, "kind": kind, "control_points": cpts, "carriageway_width_m": cw, "corridor_half_width_m": hw, "min_radius_m": r, "max_grade_pct": g, "is_existing_reuse": reuse}


def _syn_pair(td: Path, tag: str, cor_grids: list[dict], fps_lo: list[dict], fps_hi: list[dict] | None = None, segs: list[dict] | None = None, water=None, beach=None, pg_bounds=None, pg_ver: str = "RUNTIME_VERIFIED", comp=None) -> list[Path]:
    paths = []
    for pn, fps in (("PHONE_LOW", fps_lo), ("DESKTOP_HIGH", fps_lo if fps_hi is None else fps_hi)):
        d = make_dump(preset=pn, footprints=fps, roads={"nodes": [], "segments": segs or [], "completeness": "COMPLETE"}, water=water, beach=beach, pg_bounds=pg_bounds or [-300, -300, 300, 300], pg_ver=pg_ver, completeness=comp)
        d["height_grids"].extend(copy.deepcopy(cor_grids))
        d["metadata"]["static_fingerprint"] = W.compute_static_fingerprint(d)
        paths.append(_write_dump(td, f"{tag}_{pn}.json", d))
    return paths


def _ave0_base() -> tuple[list[dict], list[dict]]:
    # AVE_0 along x=0, z in [-100, 100], width=10 -> x in [-5, 5]
    return [_fp("RD_AVE0", "ROAD", [-5, -100, 5, 100], sg="ROADS", gt="POLYGON", prec="EXACT_OUTLINE")], [_seg("AVE_0", [[0, 0, -100], [0, 0, 100]], w=10.0, fp_ids=["RD_AVE0"])]


def test_r01_to_r04_geometry_and_fillets(td: Path) -> None:
    # R01 + R02: six fixed candidate roads, exact control points, C01 17 m / 12.5 m
    assert sorted(C.CANDIDATE_ROADS) == ["C01", "C02", "H01", "H02", "U01", "X01"]
    c01 = C.CANDIDATE_ROADS["C01"]
    assert c01["carriageway_width_m"] == 17.0 and c01["corridor_half_width_m"] == 12.5 and c01["min_radius_m"] == 25.0 and c01["max_grade_pct"] == 6.0
    assert C.CANDIDATE_ROADS["H01"]["min_radius_m"] == 18.0 and C.CANDIDATE_ROADS["H01"]["max_grade_pct"] == 9.0
    assert C.CANDIDATE_ROADS["U01"]["is_existing_reuse"] is True

    # Mutant 1: C01 carriageway width changed back to 14 m (no analyzer hook: pass mutated road_spec directly)
    fps, segs = _ave0_base()
    cg = [_cor_grid("COR_C01_1M", 180, 860, 280, 1240)]
    p_c01 = _syn_pair(td, "r02", cg, fps, segs=segs, pg_bounds=[-300, -300, 400, 1400])
    d_c01 = C.load_dumps(p_c01)
    g_c01 = B.build_road_graph(d_c01["PHONE_LOW"])
    r_c01 = C.evaluate_road(c01, d_c01, g_c01)
    assert r_c01["carriageway_width_m"] == 17.0 and r_c01["corridor_half_width_m"] == 12.5
    c01_14 = dict(c01, carriageway_width_m=14.0, corridor_half_width_m=11.0)
    _expect_fail("M:c01_width_14", lambda: _check(C.evaluate_road(c01_14, d_c01, g_c01)["carriageway_width_m"] == 17.0))

    # R03 + R04: fillets, collinear (C02 -> no arc), tangent > L/2 fails (never shrink R), spacing <= 3 m
    cl_c02 = C.build_centerline(C.CANDIDATE_ROADS["C02"])
    assert cl_c02["geometry_ok"] and cl_c02["fillets"][0]["collinear"] is True and cl_c02["fillets"][0]["arc_length_m"] == 0.0
    assert cl_c02["max_sample_spacing_m"] <= 3.0 and cl_c02["centerline"][0] == [110.0, 960.0] and cl_c02["centerline"][-1] == [240.0, 960.0]

    # 90-degree bend with L=40 m and R=25 m -> tangent t=25 > 40/2=20 -> ARC_DOES_NOT_FIT
    tight = _road_spec("T1", [[0, 0], [40, 0], [40, 40]], r=25.0)
    cl_tight = C.build_centerline(tight)
    assert not cl_tight["geometry_ok"] and "ARC_DOES_NOT_FIT" in cl_tight["reasons"]
    # Two bends sharing a 40 m middle segment: R=18, 90-deg each -> t1+t2=36 <= 40 passes, L=30 fails
    s_ok = C.build_centerline(_road_spec("S_OK", [[0, 0], [40, 0], [40, 40], [80, 40]], kind="HILLSIDE", r=18.0))
    s_bad = C.build_centerline(_road_spec("S_BAD", [[0, 0], [40, 0], [40, 30], [80, 30]], kind="HILLSIDE", r=18.0))
    assert s_ok["geometry_ok"] and not s_bad["geometry_ok"] and "ARC_DOES_NOT_FIT" in s_bad["reasons"]

    # Mutants 2 & 3: radius below minimum accepted; overspaced samples accepted
    low_r = C.build_centerline(_road_spec("LR", [[0, 0], [60, 0], [60, 60]], r=10.0))
    assert not low_r["geometry_ok"] and "RADIUS_BELOW_MINIMUM" in low_r["reasons"]
    _expect_fail("M:ignore_radius_check", lambda: _check(not C.build_centerline(_road_spec("LR", [[0, 0], [60, 0], [60, 60]], r=10.0), opts={"ignore_radius_check": True})["geometry_ok"]))
    ov_sp = C.build_centerline(C.CANDIDATE_ROADS["C02"], opts={"sample_spacing_m": 5.0})
    assert not ov_sp["geometry_ok"] and "SAMPLE_SPACING_EXCEEDED" in ov_sp["reasons"]
    _expect_fail("M:allow_overspaced_samples", lambda: _check(not C.build_centerline(C.CANDIDATE_ROADS["C02"], opts={"sample_spacing_m": 5.0, "allow_overspaced_samples": True})["geometry_ok"]))


def test_r05_r06_g0c10_grades_margin_beach(td: Path) -> None:
    # R05: bilinear 1 m interpolation, exact 6.0% passes / 6.001% fails, avg grade never rescues, missing height -> UNVERIFIED
    cl_flat = C.build_centerline(_road_spec("G1", [[0.5, 0.5], [30.5, 0.5]]))["centerline_exact"]
    g60 = C.sample_grades(cl_flat, [_cor_grid("COR_G1_1M", -10, -10, 45, 15, lambda x, z: round(x * 0.06, 6))], 6.0)
    g601 = C.sample_grades(cl_flat, [_cor_grid("COR_G1_1M", -10, -10, 45, 15, lambda x, z: round(x * 0.06001, 6))], 6.0)
    assert g60["grade_ok"] and "INTERPOLATED_1M" in g60["height_provenances"] and g60["max_step_grade_pct"] == 6.0
    assert not g601["grade_ok"] and "GRADE_LIMIT_EXCEEDED" in g601["reasons"]

    # Steep bump in middle (20% step) with 0% net average grade -> must FAIL; mutants 4 & 5 turn RED
    bump_grid = [_cor_grid("COR_G1_1M", -10, -10, 45, 15, lambda x, z: 0.6 if 14 <= x <= 16 else 0.0)]
    gb = C.sample_grades(cl_flat, bump_grid, 6.0)
    assert not gb["grade_ok"] and gb["net_average_grade_pct"] == 0.0 and gb["max_step_grade_pct"] > 6.0
    _expect_fail("M:ignore_grade_limit", lambda: _check(not C.sample_grades(cl_flat, bump_grid, 6.0, opts={"ignore_grade_limit": True})["grade_ok"]))
    _expect_fail("M:use_average_grade", lambda: _check(not C.sample_grades(cl_flat, bump_grid, 6.0, opts={"use_average_grade": True})["grade_ok"]))

    # Missing height -> HEIGHT_MISSING (never falls back to WORLD_20M)
    gm = C.sample_grades(cl_flat, [_cor_grid("COR_G1_1M", -10, -10, 45, 15, lambda x, z: None if x == 10 else 0.0)], 6.0)
    assert not gm["height_ok"] and "HEIGHT_MISSING" in gm["reasons"]

    # R06 + G0-C10: COR 5 m margin (pass vs fail + mutant 6) & beach encroachment reported without failure (+ mutant 7)
    fps, segs = _ave0_base()
    rd = _road_spec("R_TEST", [[0, 0], [40, 0]], hw=5.5)
    # hw=5.5, margin=5.0 -> need x in [-10.5, 50.5], z in [-10.5, 10.5]
    p_ok = _syn_pair(td, "r06_ok", [_cor_grid("COR_R_TEST_1M", -12, -12, 52, 12)], fps, segs=segs, beach=[_rect(15, -20, 25, 20)])
    p_thin = _syn_pair(td, "r06_thin", [_cor_grid("COR_R_TEST_1M", -12, -9, 52, 9)], fps, segs=segs)
    r_ok = C.analyze(p_ok, opts={"roads": {"R_TEST": rd}})["roads"]["R_TEST"]
    assert r_ok["state"] == "CONDITIONAL_VERIFIED" and r_ok["cor_margin_ok"] and r_ok["beach_encroachment_m2"] > 80.0
    _expect_fail("M:beach_as_failure", lambda: _check(C.analyze(p_ok, opts={"roads": {"R_TEST": rd}, "beach_as_failure": True})["roads"]["R_TEST"]["state"] == "CONDITIONAL_VERIFIED"))

    r_thin = C.analyze(p_thin, opts={"roads": {"R_TEST": rd}})["roads"]["R_TEST"]
    assert r_thin["state"] == "UNVERIFIED" and "COR_MARGIN" in r_thin["reasons"]
    _expect_fail("M:ignore_cor_margin", lambda: _check(C.analyze(p_thin, opts={"roads": {"R_TEST": rd}, "ignore_cor_margin": True})["roads"]["R_TEST"]["state"] == "UNVERIFIED"))

    p_pg_out = _syn_pair(td, "r06_pgout", [_cor_grid("COR_R_TEST_1M", -12, -12, 52, 12)], fps, segs=segs, pg_bounds=[-100, -100, 20, 100])
    p_pg_unk = _syn_pair(td, "r06_pgunk", [_cor_grid("COR_R_TEST_1M", -12, -12, 52, 12)], fps, segs=segs, pg_ver="UNKNOWN")
    assert "OUTSIDE_PHYSICAL_GROUND" in C.analyze(p_pg_out, opts={"roads": {"R_TEST": rd}})["roads"]["R_TEST"]["reasons"]
    assert "PHYSICAL_GROUND_UNVERIFIED" in C.analyze(p_pg_unk, opts={"roads": {"R_TEST": rd}})["roads"]["R_TEST"]["reasons"]


def test_r07_g0c4_corridor_obstacles(td: Path) -> None:
    fps_base, segs = _ave0_base()
    rd = _road_spec("R_OB", [[0, 0], [50, 0]], hw=5.5)
    cg = [_cor_grid("COR_R_OB_1M", -15, -15, 65, 15)]

    # 1. Off-centerline EXACT building at z in [3, 8] (centerline z=0 is clear, corridor edge z=5.5 hits!) + mutants 8 & 10
    p_bld = _syn_pair(td, "ob_bld", cg, fps_base + [_fp("BLD1", "BUILDING", [20, 3, 28, 8], prec="EXACT_OUTLINE")], segs=segs)
    assert C.analyze(p_bld, opts={"roads": {"R_OB": rd}})["roads"]["R_OB"]["state"] == "NOT_FEASIBLE"
    _expect_fail("M:centerline_only", lambda: _check(C.analyze(p_bld, opts={"roads": {"R_OB": rd}, "centerline_only": True})["roads"]["R_OB"]["state"] == "NOT_FEASIBLE"))
    _expect_fail("M:ignore_buildings", lambda: _check(C.analyze(p_bld, opts={"roads": {"R_OB": rd}, "ignore_buildings": True})["roads"]["R_OB"]["state"] == "NOT_FEASIBLE"))

    # 2. Site A off-centerline -> NOT_FEASIBLE (SITE_A_VIOLATION) + mutant 9
    p_sa = _syn_pair(td, "ob_sa", cg, fps_base + [_fp("SA1", "SITE_A", [20, 3, 28, 8], prot=True, prec="EXACT_OUTLINE")], segs=segs)
    r_sa = C.analyze(p_sa, opts={"roads": {"R_OB": rd}})["roads"]["R_OB"]
    assert r_sa["state"] == "NOT_FEASIBLE" and "SITE_A_VIOLATION" in r_sa["reasons"]
    _expect_fail("M:ignore_site_a", lambda: _check(C.analyze(p_sa, opts={"roads": {"R_OB": rd}, "ignore_site_a": True})["roads"]["R_OB"]["state"] == "NOT_FEASIBLE"))

    # 3. CONSERVATIVE_AABB building -> UNVERIFIED (never NOT_FEASIBLE) + mutant 11
    p_cons = _syn_pair(td, "ob_cons", cg, fps_base + [_fp("BLD_C", "BUILDING", [20, 2, 28, 8], prec="CONSERVATIVE_AABB")], segs=segs)
    r_cons = C.analyze(p_cons, opts={"roads": {"R_OB": rd}})["roads"]["R_OB"]
    assert r_cons["state"] == "UNVERIFIED" and "CORRIDOR_CONSERVATIVE_OBSTACLE" in r_cons["reasons"]
    _expect_fail("M:conservative_as_not_feasible", lambda: _check(C.analyze(p_cons, opts={"roads": {"R_OB": rd}, "conservative_as_not_feasible": True})["roads"]["R_OB"]["state"] == "UNVERIFIED"))

    # 4. Non-physical OTHER (street furniture) -> advisory only, road stays CONDITIONAL_VERIFIED; water -> NOT_FEASIBLE
    p_adv = _syn_pair(td, "ob_adv", cg, fps_base + [_fp("LAMP1", "OTHER", [20, -1, 22, 1], phys=False, sg="SCENE_BOX3")], segs=segs)
    r_adv = C.analyze(p_adv, opts={"roads": {"R_OB": rd}})["roads"]["R_OB"]
    assert r_adv["state"] == "CONDITIONAL_VERIFIED" and len(r_adv["obstacles"]["advisory_street_furniture"]) == 1
    p_wat = _syn_pair(td, "ob_wat", cg, fps_base, segs=segs, water=[_rect(25, -10, 35, 10)])
    assert C.analyze(p_wat, opts={"roads": {"R_OB": rd}})["roads"]["R_OB"]["state"] == "NOT_FEASIBLE"


def test_r08_r09_g0c5_g0c6_junctions(td: Path) -> None:
    fps_base, segs_base = _ave0_base()
    # G0-C6: ELEVATED/RAMP/UNKNOWN planar crossings never connect (+ mutant 13); 0.5 m elevation tolerance & missing height (+ mutant 12)
    segs_ex = segs_base + [
        _seg("EL_1", [[30, 6, -50], [30, 6, 50]], w=8.0, elev="ELEVATED"),
        _seg("RMP_1", [[38, 2, -50], [38, 2, 50]], w=8.0, elev="RAMP"),
        _seg("UNK_1", [[46, 0, -50], [46, 0, 50]], w=8.0, elev="UNKNOWN"),
    ]
    rd_el = _road_spec("R_EL", [[30, 0], [50, 0]], hw=5.5)
    p_el = _syn_pair(td, "j_el", [_cor_grid("COR_R_EL_1M", 15, -15, 65, 15)], fps_base, segs=segs_ex)
    r_el = C.analyze(p_el, opts={"roads": {"R_EL": rd_el}})["roads"]["R_EL"]
    assert r_el["state"] == "UNVERIFIED" and not any(j["road_b"] in ("EL_1", "RMP_1", "UNK_1") for j in r_el["junctions"])
    _expect_fail("M:allow_elevated_connect", lambda: _check(not any(j["road_b"] == "EL_1" for j in C.analyze(p_el, opts={"roads": {"R_EL": rd_el}, "allow_elevated_connect": True})["roads"]["R_EL"]["junctions"])))

    rd_h = _road_spec("R_H", [[0, 0], [40, 0]], hw=5.5)
    p_h_ok = _syn_pair(td, "j_h05", [_cor_grid("COR_R_H_1M", -15, -15, 55, 15, lambda x, z: 0.5)], fps_base, segs=segs_base)
    p_h_bad = _syn_pair(td, "j_h06", [_cor_grid("COR_R_H_1M", -15, -15, 55, 15, lambda x, z: 0.6)], fps_base, segs=segs_base)
    p_h_mis = _syn_pair(td, "j_hmis", [_cor_grid("COR_R_H_1M", -15, -15, 55, 15, lambda x, z: None if x == 0 else 0.0)], fps_base, segs=segs_base)
    assert C.analyze(p_h_ok, opts={"roads": {"R_H": rd_h}})["roads"]["R_H"]["state"] == "CONDITIONAL_VERIFIED"
    r_bad = C.analyze(p_h_bad, opts={"roads": {"R_H": rd_h}})["roads"]["R_H"]
    assert r_bad["state"] != "CONDITIONAL_VERIFIED" and any(j["status"] == "REJECTED" and j["reason"] == "ELEVATION_MISMATCH" for j in r_bad["junctions"])
    r_mis = C.analyze(p_h_mis, opts={"roads": {"R_H": rd_h}})["roads"]["R_H"]
    assert r_mis["state"] == "UNVERIFIED" and "JUNCTION_HEIGHT_MISSING" in r_mis["reasons"]
    _expect_fail("M:skip_elevation_check", lambda: _check(C.analyze(p_h_bad, opts={"roads": {"R_H": rd_h}, "skip_elevation_check": True})["roads"]["R_H"]["state"] != "CONDITIONAL_VERIFIED"))

    # D-054a G0-C5: (1) shallow-angle ~72 m contiguous run PASSES; (2) > 100 m run BLOCKED (+ mutant 14);
    # (3) re-entry after gap BLOCKED (+ mutant 15); (4) overlap with unconnected segment BLOCKED
    # CRS_E along z=0 (width 22 -> z in [-11, 11], x in [-10, 260]) connected to AVE_0
    fps_c5 = fps_base + [_fp("RD_CRSE", "ROAD", [-10, -11, 260, 11], sg="ROADS", gt="POLYGON", prec="EXACT_OUTLINE")]
    segs_c5 = segs_base + [_seg("CRS_E", [[-10, 0, 0], [260, 0, 0]], w=22.0, fp_ids=["RD_CRSE"])]
    cg_c5 = [_cor_grid("COR_SHAL_1M", -20, -25, 280, 120)]
    # Shallow 16.7 deg run (~57 m inside z<=11 + hw=5.5 -> ~60-72 m contiguous run <= 100 m)
    rd_shal = _road_spec("SHAL", [[0, 0], [200, 60]], hw=5.5)
    p_c5 = _syn_pair(td, "c5", cg_c5, fps_c5, segs=segs_c5, pg_bounds=[-300, -300, 400, 400])
    r_shal = C.analyze(p_c5, opts={"roads": {"SHAL": rd_shal}})["roads"]["SHAL"]
    assert r_shal["state"] == "CONDITIONAL_VERIFIED" and 45.0 <= r_shal["obstacles"]["junction_overlaps"][0]["run_length_m"] <= 85.0

    # Run > 100 m (very shallow 6 deg -> stays overlapping CRS_E for ~160 m) -> BLOCKED (+ mutant 14)
    rd_long = _road_spec("SHAL", [[0, 0], [240, 25]], hw=5.5)
    assert C.analyze(p_c5, opts={"roads": {"SHAL": rd_long}})["roads"]["SHAL"]["state"] == "NOT_FEASIBLE"
    _expect_fail("M:no_junction_run_limit", lambda: _check(C.analyze(p_c5, opts={"roads": {"SHAL": rd_long}, "no_junction_run_limit": True})["roads"]["SHAL"]["state"] == "NOT_FEASIBLE"))

    # Re-entry after gap: leaves CRS_E then bends back into CRS_E -> BLOCKED (+ mutant 15)
    rd_re = _road_spec("SHAL", [[0, 0], [40, 40], [80, 40], [120, 5]], hw=5.5, r=18.0, kind="HILLSIDE")
    assert C.analyze(p_c5, opts={"roads": {"SHAL": rd_re}})["roads"]["SHAL"]["state"] == "NOT_FEASIBLE"
    _expect_fail("M:accept_reentry", lambda: _check(C.analyze(p_c5, opts={"roads": {"SHAL": rd_re}, "accept_reentry": True})["roads"]["SHAL"]["state"] == "NOT_FEASIBLE"))

    # Overlap with another (unconnected) ROAD footprint -> BLOCKED
    p_oth = _syn_pair(td, "c5_oth", [_cor_grid("COR_R_H_1M", -15, -15, 85, 15)], fps_base + [_fp("RD_OTH", "ROAD", [56, -50, 64, 50], prec="EXACT_OUTLINE")], segs=segs_base + [_seg("OTH_1", [[60, 0, -50], [60, 0, 50]], w=8.0, fp_ids=["RD_OTH"])])
    assert C.analyze(p_oth, opts={"roads": {"R_H": _road_spec("R_H", [[0, 0], [70, 0]], hw=5.5)}})["roads"]["R_H"]["state"] == "NOT_FEASIBLE"

    # Candidate-to-candidate junction with missing height stays UNVERIFIED (not NOT_FEASIBLE); non-junction parallel overlap BLOCKED
    p_cmis = _syn_pair(td, "c5_cmis", [_cor_grid("COR_G_1M", -15, -15, 95, 45, lambda x, z: None if (x == 40 and z == 0) else 0.0)], fps_base, segs=segs_base)
    res_cmis = C.analyze(p_cmis, opts={"roads": {"RA": _road_spec("RA", [[0, 0], [40, 0]]), "RB": _road_spec("RB", [[40, 0], [80, 0]])}})
    assert res_cmis["roads"]["RA"]["state"] == "UNVERIFIED" and res_cmis["roads"]["RB"]["state"] == "UNVERIFIED"
    p_cpar = _syn_pair(td, "c5_cpar", [_cor_grid("COR_P_1M", -15, -15, 65, 30)], fps_base, segs=segs_base)
    res_cpar = C.analyze(p_cpar, opts={"roads": {"PA": _road_spec("PA", [[0, 0], [50, 0]], hw=5.5), "PB": _road_spec("PB", [[0, 8], [50, 8]], hw=5.5)}})
    assert res_cpar["roads"]["PA"]["state"] == "NOT_FEASIBLE" and "CORRIDOR_BLOCKED_CANDIDATE" in res_cpar["roads"]["PA"]["reasons"]


def test_r11_to_r18_chains_verdicts_handoff(td: Path) -> None:
    # R15 + G0-C8: all 4 regional verdicts on compact synthetic scenarios + mutant 20 (verdict_from_parcel_counts)
    fps, segs = _ave0_base()
    cg = [_cor_grid("COR_ALL_1M", -15, -15, 115, 115, lambda x, z: round(max(0.0, (x - 50) * 0.25), 4) if z >= 75 else 0.0)]
    p_v = _syn_pair(td, "verdicts", cg, fps, segs=segs, pg_bounds=[-200, -200, 250, 250])
    scens = {"S": {"B1": [2, 35, 0, 25], "B2": [30, 65, 30, 55], "B3": [60, 95, 78, 102]}}
    scens_unv = {"S": {"B1": [2, 35, 0, 25], "B2": [140, 175, 30, 55], "B3": [60, 95, 78, 102]}}
    roads_v = {
        "RC": _road_spec("RC", [[0, 42], [55, 42]], hw=5.5),      # CONDITIONAL_VERIFIED into B2
        "RNF": _road_spec("RNF", [[0, 90], [85, 90]], hw=5.5),    # NOT_FEASIBLE (25% grade) into B3
    }
    sv = C.analyze(p_v, opts={"roads": roads_v, "scenarios": scens})
    rv = sv["regional_access"]["S"]
    assert rv["B1"]["verdict"] == "FEASIBLE" and rv["B2"]["verdict"] == "CONDITIONAL" and rv["B3"]["verdict"] == "NOT FEASIBLE WITHIN AUDITED BOUNDARIES"
    assert C.analyze(p_v, opts={"roads": roads_v, "scenarios": scens_unv})["regional_access"]["S"]["B2"]["verdict"] == "UNVERIFIED"

    # Mutant 20: verdict derived from T-016B parcel counts (fake cap_inv with C_direct=0 on B1)
    cap_fake = {"base_sha": BASE_SHA, "polygon_revision": 2, "analyzer_version": B.ANALYZER_VERSION,
                "presets": {k: {"static_fingerprint": v["static_fingerprint"]} for k, v in sv["presets"].items()},
                "scenarios": {"S": {"regions": {"B1": {"capacities": {"C_direct": 0}}, "B2": {"capacities": {"C_direct": 5}}, "B3": {"capacities": {"C_direct": 0}}}}}}
    cap_p = td / "cap_inv.json"
    cap_p.write_text(json.dumps(cap_fake), encoding="utf-8")
    _expect_fail("M:verdict_from_parcel_counts", lambda: _check(C.analyze(p_v, capacity_inventory_path=cap_p, opts={"roads": roads_v, "scenarios": scens, "verdict_from_parcel_counts": True})["regional_access"]["S"]["B1"]["verdict"] == "FEASIBLE"))

    # R14 + mutant 19: candidate corridor dict format == corridors_from_graph keys, existing=False, feeds B.evaluate_access with existing_only=False
    g_v = B.build_road_graph(json.loads(p_v[0].read_text(encoding="utf-8")))
    ex_keys = set(B.corridors_from_graph(g_v)[0].keys())
    assert len(sv["candidate_corridors"]) >= 1 and set(sv["candidate_corridors"][0].keys()) == ex_keys
    assert sv["candidate_corridors"][0]["existing"] is False and sv["candidate_corridors"][0]["connectivity"] == "VERIFIED"
    acc = B.evaluate_access([15.0, 48.0, 39.0, 70.0], sv["candidate_corridors"])
    assert acc["ok"] is True and acc["existing_only"] is False
    _expect_fail("M:mark_candidate_existing", lambda: _check(C.analyze(p_v, opts={"roads": roads_v, "scenarios": scens, "mark_candidate_existing": True})["roads"]["RC"]["state"] == "CONDITIONAL_VERIFIED"))

    # R16 + R17 + R18 + mutant 21: capacity_inventory linkage, file_sha256 independence, bad fingerprint rejected, 3x CLI determinism
    lo_alt_d = json.loads(p_v[0].read_text(encoding="utf-8"))
    lo_alt_d["metadata"]["generated_at"] = "2099-12-31T00:00:00Z"
    lo_alt = td / "lo_alt_sha.json"
    lo_alt.write_text(json.dumps(lo_alt_d, indent=2), encoding="utf-8")
    assert hashlib.sha256(lo_alt.read_bytes()).hexdigest() != hashlib.sha256(p_v[0].read_bytes()).hexdigest()
    od_good = td / "det_0"
    assert C.main(["--dump", str(lo_alt), "--dump", str(p_v[1]), "--capacity-inventory", str(cap_p), "--out", str(od_good)]) == 0
    out_j = json.loads((od_good / "road_survey.json").read_text(encoding="utf-8"))
    assert out_j["analyzer_version"] == "we01c-1.0" and out_j["road_schema_version"] == 1 and out_j["C_conditional"] == "PENDING_T016D"
    assert out_j["t016b_source"]["sha256"] == hashlib.sha256(cap_p.read_bytes()).hexdigest()

    bad_cap = copy.deepcopy(cap_fake)
    bad_cap["presets"]["PHONE_LOW"]["static_fingerprint"] = "0" * 64
    bad_cap_p = td / "bad_cap.json"
    bad_cap_p.write_text(json.dumps(bad_cap), encoding="utf-8")
    _expect_err("R16:bad_cap_fp", lambda: C.analyze(p_v, capacity_inventory_path=bad_cap_p))

    bad_d = json.loads(p_v[0].read_text(encoding="utf-8"))
    bad_d["metadata"]["static_fingerprint"] = "f" * 64
    bad_dp = _write_dump(td, "bad_fp_dump.json", bad_d)
    _expect_err("R16:bad_dump_fp", lambda: C.analyze([bad_dp, p_v[1]]))
    _expect_fail("M:skip_fingerprint_check", lambda: _expect_err("must_reject_fp", lambda: C.analyze([bad_dp, p_v[1]], opts={"skip_fingerprint_check": True})))

    # R18: 3x determinism
    hashes = []
    for k in range(3):
        od = td / f"det_run_{k}"
        C.analyze(p_v, out_dir=od, opts={"roads": roads_v, "scenarios": scens})
        hashes.append(hashlib.sha256((od / "road_survey.json").read_bytes()).hexdigest())
    assert hashes[0] == hashes[1] == hashes[2], "R18 determinism failed"


def test_real_samples_and_mutants(td: Path) -> None:
    lo_r, hi_r = FX / "sample_roads_phone_low.json", FX / "sample_roads_desktop_high.json"
    # Local road graph agreement with T-016B build_road_graph on real sample
    d_lo_r = json.loads(lo_r.read_text(encoding="utf-8"))
    assert C.existing_main_component_local(d_lo_r) == B.build_road_graph(d_lo_r)["main_component"]

    # Real sample_roads run + R10/R11/R12/R13 + mutants 16, 17, 18
    od_r = td / "real_roads"
    sr = C.analyze([lo_r, hi_r], out_dir=od_r)
    rds = sr["roads"]
    assert rds["C01"]["state"] == "CONDITIONAL_VERIFIED" and any(j["road_b"] == "RIB_0" and j["status"] == "VERIFIED" for j in rds["C01"]["junctions"])
    assert rds["C01"]["beach_encroachment_m2"] > 0 and rds["C02"]["state"] == "CONDITIONAL_VERIFIED"
    assert rds["H01"]["state"] == "NOT_FEASIBLE" and "GRADE_LIMIT_EXCEEDED" in rds["H01"]["reasons"]
    assert rds["H02"]["state"] == "CONDITIONAL_VERIFIED" and rds["X01"]["state"] == "CONDITIONAL_VERIFIED"
    assert rds["U01"]["state"] == "EXISTING_VERIFIED" and rds["U01"]["new_length_m"] == 0.0 and rds["U01"]["new_corridor_area_m2"] == 0.0
    assert any(l["reason"] == "AVE110_EXTENSION_REQUIRED" for l in rds["C02"]["optional_extension_links"])
    assert any(l["reason"] == "AVE110_EXTENSION_REQUIRED" for l in rds["X01"]["optional_extension_links"])
    assert any("C01" in ch for ch in rds["C02"]["dependency_chains"]) and any("X01" in ch for ch in rds["C02"]["dependency_chains"])
    assert "H01" in sr["excluded_roads"] and sr["regional_access"]["REVISED"]["B2"]["verdict"] == "CONDITIONAL"
    assert sr["existing_road_graph"]["duplicates"] == {"HILL_ROAD": ["HILL_ROAD", "TRD_0"]}

    # Fast mutant checks on loaded sample_roads data (avoid re-parsing JSON twice)
    dumps_r = C.load_dumps([lo_r, hi_r])
    g_r = B.build_road_graph(dumps_r["PHONE_LOW"])
    _expect_fail("M:drop_ave110_link", lambda: _check(any(l["reason"] == "AVE110_EXTENSION_REQUIRED" for l in C.evaluate_road(C.CANDIDATE_ROADS["C02"], dumps_r, g_r, opts={"drop_ave110_link": True})["optional_extension_links"])))
    _expect_fail("M:count_u01_as_new", lambda: _check(C.evaluate_road(C.CANDIDATE_ROADS["U01"], dumps_r, g_r, opts={"count_u01_as_new": True})["new_length_m"] == 0.0))
    # H01 failing must not fail B2 (no analyzer hook: verify generic verdict rules on road_results)
    rr_for_b2 = {k: C.evaluate_road(C.CANDIDATE_ROADS[k], dumps_r, g_r) for k in ("H01", "H02")}
    C.build_candidate_graph(rr_for_b2, g_r)
    assert C.evaluate_region_access(rr_for_b2, g_r, dumps_r)["REVISED"]["B2"]["verdict"] == "CONDITIONAL"
    assert C.evaluate_region_access({"H01": rr_for_b2["H01"]}, g_r, dumps_r)["REVISED"]["B2"]["verdict"] == "NOT FEASIBLE WITHIN AUDITED BOUNDARIES"
    rr_b2_mut = {"H01": rr_for_b2["H01"], "H02": dict(rr_for_b2["H02"], state="NOT_FEASIBLE")}
    _expect_fail("M:h01_fails_b2", lambda: _check(C.evaluate_region_access(rr_b2_mut, g_r, dumps_r)["REVISED"]["B2"]["verdict"] == "CONDITIONAL"))

    # Real sample_b3mid run (U01 present in COR_U01_1M, no AVE_0 -> UNVERIFIED; C01/C02 stay UNVERIFIED on missing heights)
    sb = C.analyze([FX / "sample_b3mid_phone_low.json", FX / "sample_b3mid_desktop_high.json"])
    assert sb["C_conditional"] == "PENDING_T016D"
    assert sb["roads"]["U01"]["state"] == "UNVERIFIED" and sb["roads"]["C01"]["state"] == "UNVERIFIED" and sb["roads"]["C02"]["state"] == "UNVERIFIED"


def main() -> int:
    t0 = time.monotonic()
    suites = [
        ("R01-R04 geometry, fillets, spacing + 3 mutants", test_r01_to_r04_geometry_and_fillets),
        ("R05-R06/G0-C10 grades, COR margin, beach + 4 mutants", test_r05_r06_g0c10_grades_margin_beach),
        ("R07/G0-C4 corridor obstacles & advisory + 4 mutants", test_r07_g0c4_corridor_obstacles),
        ("R08-R09/G0-C5/G0-C6 junctions & D-054a runs + 4 mutants", test_r08_r09_g0c5_g0c6_junctions),
        ("R14-R18 verdicts, handoff, linkage, determinism + 3 mutants", test_r11_to_r18_chains_verdicts_handoff),
        ("R10-R13 real samples + local graph parity + 3 mutants", test_real_samples_and_mutants),
    ]
    with tempfile.TemporaryDirectory() as tmp:
        td = Path(tmp)
        for label, fn in suites:
            ts = time.monotonic()
            fn(td)
            print(f"PASS [{label}] ({time.monotonic() - ts:.2f}s)")
    elapsed = time.monotonic() - t0
    assert elapsed <= 10.0, f"Runtime exceeded 10.0s: {elapsed:.2f}s"
    print(f"RESULT: PASS (WE-01C R01-R18 + D-054a G0-C1..C10 + 21 mutants RED + real samples in {elapsed:.2f}s <= 10.0s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
