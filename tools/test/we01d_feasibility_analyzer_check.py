#!/usr/bin/env python3
"""WE-01D (T-016D) Feasibility Analyzer check suite (D01-D28, G0-D1..D16, B seed edit, 22 mutants, real samples)."""
from __future__ import annotations

import copy
import hashlib
import inspect
import json
import math
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
import we01d_feasibility_analyzer as D  # noqa: E402

FX = ROOT / "tools/fixtures/we01"
BASE_SHA = "84319439243b51aa8d119e33eb62a0637feea887"


def _check(cond: bool, msg: str = "") -> None:
    assert cond, msg


def _expect_err(label: str, fn) -> None:
    try:
        fn()
    except (AssertionError, D.FeasibilityError, C.RoadError, B.CapacityError, W.ValidationError):
        return
    raise AssertionError(f"Expected FAILURE but stayed GREEN: {label}")


def _grid_1m(gid: str, rid: str, x0: int, z0: int, x1: int, z1: int, hfn=None) -> dict:
    fn = hfn or (lambda x, z: 0.0)
    nx, nz = x1 - x0 + 1, z1 - z0 + 1
    return {
        "id": gid, "region_id": rid, "origin_x": x0, "origin_z": z0, "step_m": 1,
        "nx": nx, "nz": nz, "heights": [fn(x0 + ix, z0 + iz) for iz in range(nz) for ix in range(nx)],
        "source": "runtime_terrainHeight", "sample_method": "DIRECT_RUNTIME",
    }


def _seg(sid: str, cl: list[list[float]], w: float = 10.0, elev: str = "GROUND", fp_ids: list[str] | None = None) -> dict:
    return {
        "id": sid, "start_node_id": None, "end_node_id": None, "centerline": cl,
        "carriageway_width_m": w, "sidewalk_left_m": None, "sidewalk_right_m": None,
        "corridor_footprint_ids": list(fp_ids or []), "elevation_type": elev,
        "traffic_route_ids": [], "source_ref": "syn_road", "verification": "RUNTIME_VERIFIED",
    }


def _build_bcd_fixture(
    td: Path, tag: str, regs: list[dict], scens: dict, fps_lo: list[dict],
    fps_hi: list[dict] | None = None, segs: list[dict] | None = None,
    grids_extra: list[dict] | None = None, c_roads: dict | None = None,
    water=None, beach=None, pg_bounds=None, pg_ver: str = "RUNTIME_VERIFIED", hfn=None,
) -> tuple[list[Path], Path, Path, Path]:
    paths = []
    for pn, fps in (("PHONE_LOW", fps_lo), ("DESKTOP_HIGH", fps_lo if fps_hi is None else fps_hi)):
        d = make_dump(preset=pn, regions=regs, footprints=fps, roads={"nodes": [], "segments": segs or [], "completeness": "COMPLETE"}, water=water, beach=beach, pg_bounds=pg_bounds or [-300, -300, 400, 400], pg_ver=pg_ver, height_fn=hfn)
        if grids_extra:
            by_rid = {g["region_id"]: g for g in grids_extra if g["region_id"] != "ROAD_CORRIDOR"}
            d["height_grids"] = [by_rid.get(g["region_id"], g) for g in d["height_grids"]]
            d["height_grids"].extend(copy.deepcopy([g for g in grids_extra if g["region_id"] == "ROAD_CORRIDOR"]))
        d["metadata"]["static_fingerprint"] = W.compute_static_fingerprint(d)
        paths.append(_write_dump(td, f"{tag}_{pn}.json", d))
    b_dir, c_dir = td / f"{tag}_b", td / f"{tag}_c"
    B.analyze(paths, out_dir=b_dir, opts={"allow_custom_scenarios": True, "scenarios": scens})
    C.analyze(paths, out_dir=c_dir, capacity_inventory_path=b_dir / "capacity_inventory.json", opts={"roads": c_roads or {}, "scenarios": scens})
    return paths, b_dir / "capacity_inventory.json", b_dir / "parcel_candidates.json", c_dir / "road_survey.json"


def _reg(rid: str, b: list[int]) -> dict:
    return {"id": rid, "name": rid, "initial_polygon": _rect(*b), "survey_polygon": _rect(*b), "buffer_m": 0, "source_ref": "syn"}


def test_g0d1_signatures_and_b_seeds(td: Path) -> None:
    # Pin exact parameter names of all 6 approved B underscore helpers + place_layout(seed_parcels)
    expected_params = {
        "_build_region_triplet": ["d_lo", "d_hi", "sid", "rid", "b_int", "opts"],
        "_slice_masks": ["env", "scenario_id", "bounds_internal"],
        "_slice_valid_mask": ["env_vm", "bounds_internal", "allow_oob"],
        "_combine_masks": ["lo", "hi", "opts"],
        "_band": ["a", "b"],
        "_verify_layout": ["parcels", "masks", "corridors", "graph", "region_id", "require_access", "opts"],
        "place_layout": ["valid_by_proto", "access_fn", "region_id", "order", "opts", "seed_parcels"],
    }
    for name, exp in expected_params.items():
        got = list(inspect.signature(getattr(B, name)).parameters.keys())
        assert got == exp, f"Signature pin mismatch for B.{name}: {got} != {exp}"
    # Mutant: changing pinned signature turns pin assertion RED
    _expect_fail("M:signature_pin", lambda: _check(list(inspect.signature(B.place_layout).parameters.keys()) == expected_params["place_layout"][:-1]))

    # B seed_parcels test: B3 needs R01+R05+R08 >= 20%; with 1 R01 + 1 R08 seeds, adding 1 R05 succeeds & keeps seed IDs
    d = make_dump(regions=[_reg("B3", [0, 0, 140, 40])], pg_bounds=[-200, -200, 200, 200])
    m = B.build_masks(d, "S", "B3", [0, 0, 140, 40])
    v = {p: {o: B.geom_valid(m, p, o) for o in (0, 90)} for p in ("R01", "R05", "R08")}
    seeds = [
        {"id": "B3_R01_001", "prototype": "R01", "orientation": 0, "center": [21, 17], "bounds": [0, 0, 42, 34], "area_m2": 1428, "buildings": 1, "units": 1, "status": "DIRECT", "access": None, "reasons": []},
        {"id": "B3_R08_002", "prototype": "R08", "orientation": 0, "center": [61, 12], "bounds": [42, 0, 80, 24], "area_m2": 912, "buildings": 1, "units": 4, "status": "DIRECT", "access": None, "reasons": []},
    ]
    # Only allow R05 in remaining mask [80..108, 0..26]: without seeds 1 R05 fails B3 ratio; with seeds it passes!
    v_only_r05 = {"R01": {}, "R08": {}, "R05": {0: v["R05"][0]}}
    no_seed_res = B.place_layout(v_only_r05, None, "B3")
    assert no_seed_res["count"] == 0, "Single R05 without seeds must be trimmed by B3 ratio"
    seeded_res = B.place_layout(v_only_r05, None, "B3", seed_parcels=seeds)
    assert seeded_res["count"] >= 3 and seeded_res["ratio_ok"]
    assert seeded_res["parcels"][0]["id"] == "B3_R01_001" and seeded_res["parcels"][1]["id"] == "B3_R08_002"
    assert seeded_res["parcels"][2]["id"] == "B3_R05_003"
    # Seeds are never trimmed even if ratio cannot be satisfied (e.g. 1 R01 seed alone with empty valid masks)
    untrim = B.place_layout({"R01": {}, "R05": {}, "R08": {}}, None, "B3", seed_parcels=[seeds[0]])
    assert len(untrim["parcels"]) == 1 and untrim["parcels"][0]["id"] == "B3_R01_001"


def test_d01_to_d05_d23_candidates_and_budget(td: Path) -> None:
    # D01: frozen scenarios
    assert D.SCENARIOS == B.SCENARIOS and D.spec_to_internal([90, 390, 930, 1230]) == [90, 930, 390, 1230]

    # D03, D04, D05: start every 25 m + final endpoint, region filter inclusive, dedup across sources, deterministic order
    src_a = {"id": "SRC_A", "source_type": "EXISTING_ROAD", "centerline": [[0.0, 0.0], [60.0, 0.0]], "carriageway_width_m": 10.0, "corridors": [], "dependency_chains": [[]], "beach_encroachment_m2": 0.0}
    src_b = {"id": "SRC_B", "source_type": "EXISTING_ROAD", "centerline": [[0.0, 0.0], [60.0, 0.0]], "carriageway_width_m": 10.0, "corridors": [], "dependency_chains": [[]], "beach_encroachment_m2": 0.0}
    # Starts on [0,60]: 0, 25, 50, 60 (4 starts) x 2 sides x 5 lengths = 40 unique (SRC_B deduped; SRC_A wins)
    cands, tot, ex = D.generate_street_candidates([src_b, src_a], [0, 0, 100, 100], "S", "B2")
    assert tot == 40 and not ex and all(c["source_road_id"] == "SRC_A" for c in cands)
    assert set(c["length_m"] for c in cands) == {30, 60, 90, 120, 150}
    # Region filter excludes starts outside [10, 0, 45, 100] (only d=25 passes -> 10 cands); mutant allow_outside_start fails
    c_filt, tot_f, _ = D.generate_street_candidates([src_a], [10, 0, 45, 100], "S", "B2")
    assert tot_f == 10 and all(10.0 <= c["start"][0] <= 45.0 for c in c_filt)
    _expect_fail("M:allow_outside_start", lambda: _check(D.generate_street_candidates([src_a], [10, 0, 45, 100], "S", "B2", {"allow_outside_start": True})[1] == 10))
    # Mutant: > 150 m street length
    _expect_fail("M:length_gt_150", lambda: _check(max(c["length_m"] for c in D.generate_street_candidates([src_a], [0, 0, 100, 100], "S", "B2", {"street_lengths": (30, 60, 90, 120, 150, 180)})[0]) <= 150))

    # D02 + D04 + D23: max 3 streets per region (+ mutant 4th street) & budget exhaustion never proves NOT FEASIBLE
    # Wide 400x160 B2 region with AVE_0 along z=0 (starts at 0,25,50,...400); 4 disjoint lanes at x=50,150,250,350
    rfp = _fp("RD_AVE0", "ROAD", [0, -5, 400, 5], sg="ROADS", gt="POLYGON", prec="EXACT_OUTLINE")
    seg = _seg("AVE_0", [[0, 0, 0], [400, 0, 0]], w=10.0, fp_ids=["RD_AVE0"])
    scens = {"S": {"B2": [0, 400, 0, 160]}}
    # Trees at z=16 leaving 16 m gaps (< 22 m min parcel width) centered at x=50,150,250,350 -> 0 direct parcels, 4 disjoint street slots
    tx = {sx - 10 for sx in (50, 150, 250, 350)} | {sx + 8 for sx in (50, 150, 250, 350)}
    tx |= {x for x in range(8, 400, 18) if all(abs(x + 1 - sx) > 10 for sx in (50, 150, 250, 350))}
    trees = [_fp(f"TR_{x}", "TREE", [x, 16, x + 2, 18], prec="EXACT_OUTLINE", sg="TREE_COLLIDERS") for x in sorted(tx)]
    g1m = _grid_1m("B2_1M", "B2", -20, -20, 420, 180)
    paths, ci, pc, rs = _build_bcd_fixture(td, "d02", [_reg("B2", [0, 0, 400, 160])], scens, [rfp] + trees, segs=[seg], grids_extra=[g1m])

    res3 = D.analyze(paths, ci, pc, rs, opts={"scenarios": scens})
    st3 = res3["internal_streets"]["scenarios"]["S"]["B2"]
    assert st3["selected_count"] == 3 and sum(s["length_m"] for s in st3["selected_streets"]) <= 450
    _expect_fail("M:allow_4th_street", lambda: _check(D.analyze(paths, ci, pc, rs, opts={"scenarios": scens, "max_streets_per_region": 4})["internal_streets"]["scenarios"]["S"]["B2"]["selected_count"] <= 3))

    # D23: budget exhausted -> SEARCH_BUDGET_EXHAUSTED, verdict UNVERIFIED (never NOT FEASIBLE) + mutant
    res_ex = D.analyze(paths, ci, pc, rs, opts={"scenarios": scens, "candidate_budget": 2})
    assert res_ex["internal_streets"]["scenarios"]["S"]["B2"]["search_budget_exhausted"] is True
    assert res_ex["feasibility"]["scenarios"]["S"]["verdicts"]["buildings_40"]["verdict"] == "UNVERIFIED"
    _expect_fail("M:budget_exhausted_not_feasible", lambda: _check(D.analyze(paths, ci, pc, rs, opts={"scenarios": scens, "candidate_budget": 2, "budget_exhausted_as_not_feasible": True})["feasibility"]["scenarios"]["S"]["verdicts"]["buildings_40"]["verdict"] == "UNVERIFIED"))


def test_d06_to_d18_legality_conflicts_cross_preset_accounting(td: Path) -> None:
    # Build a B2 160x140 region with AVE_0 along z=0 (starts 0,25,50,75,100,125,150), 1 direct parcel [0..24, 5..27]
    rfp = _fp("RD_AVE0", "ROAD", [0, -5, 160, 5], sg="ROADS", gt="POLYGON", prec="EXACT_OUTLINE")
    seg = _seg("AVE_0", [[0, 0, 0], [160, 0, 0]], w=10.0, fp_ids=["RD_AVE0"])
    # Trees at z=16 leaving [0..34] for 1 direct parcel [0..24, 5..27] (conflicts with x=25) and 16 m street slots at x=50, 100
    trees = [_fp(f"TR_{x}", "TREE", [x, 16, x + 2, 18], prec="EXACT_OUTLINE", sg="TREE_COLLIDERS") for x in (34, 40, 58, 76, 90, 108, 126, 144)]
    # DESKTOP_HIGH-only obstacle band blocking upper-right parcels to test cross-preset common layout (D16) + mutant single_preset_only
    hi_extra = [_fp("HI_TREE", "TREE", [85, 50, 155, 125], prec="EXACT_OUTLINE", sg="TREE_COLLIDERS")]
    scens = {"S": {"B2": [0, 160, 0, 140]}}
    g1m = _grid_1m("B2_1M", "B2", -20, -20, 180, 160)
    paths, ci, pc, rs = _build_bcd_fixture(td, "d06", [_reg("B2", [0, 0, 160, 140])], scens, [rfp] + trees, fps_hi=[rfp] + trees + hi_extra, segs=[seg], grids_extra=[g1m])

    res = D.analyze(paths, ci, pc, rs, opts={"scenarios": scens})
    cp = res["conditional_parcels"]["scenarios"]["S"]["B2"]
    la = res["feasibility"]["scenarios"]["S"]["land_accounting"]["regions"]["B2"]
    st = res["internal_streets"]["scenarios"]["S"]["B2"]

    # D13, D14, D16, D28: direct parcel preserved, C_conditional includes C_direct, unbuilt streets never existing, zero parcel/street overlap
    assert cp["C_direct"] == 1 and cp["C_conditional"] > cp["C_direct"] and cp["C_additional"] == cp["C_conditional"] - cp["C_direct"]
    assert cp["parcels"][0]["status"] == "DIRECT" and cp["parcels"][0]["parcel_id"] == "B2_R05_001"
    assert cp["preset_validation"]["PHONE_LOW"]["ok"] and cp["preset_validation"]["DESKTOP_HIGH"]["ok"]
    assert cp["C_phone_low"] > cp["C_common"] and cp["C_desktop_high"] >= cp["C_common"]
    assert st["selected_count"] >= 1 and all(not s["existing"] and s["verification_status"] == "CONDITIONAL_VERIFIED" for s in st["selected_streets"])
    st_parcels = [p for p in cp["parcels"] if p["status"] == "INTERNAL_STREET_REQUIRED"]
    assert st_parcels and all(not p["access"]["existing_only"] and p["dependency_chain"] for p in st_parcels)
    for p in cp["parcels"]:
        pb = tuple(p["bounds"])
        for s in st["selected_streets"]:
            sb = tuple(s["corridor_geometry"]["bounds"])
            assert pb[2] <= sb[0] + 1e-6 or pb[0] >= sb[2] - 1e-6 or pb[3] <= sb[1] + 1e-6 or pb[1] >= sb[3] - 1e-6, "Parcel overlaps street"

    # G0-D7 street vs direct seed conflict at x=25 (+ mutant allow_street_seed_overlap)
    assert st["rejection_summary"].get("DIRECT_PARCEL_CONFLICT", 0) >= 1
    _expect_err("M:allow_street_seed_overlap", lambda: _check(D.analyze(paths, ci, pc, rs, opts={"scenarios": scens, "allow_street_seed_overlap": True})["internal_streets"]["scenarios"]["S"]["B2"]["rejection_summary"].get("DIRECT_PARCEL_CONFLICT", 0) >= 1))

    # D16 mutant: single_preset_only exceeds DESKTOP_HIGH capacity
    _expect_fail("M:single_preset_only", lambda: _check(D.analyze(paths, ci, pc, rs, opts={"scenarios": scens, "single_preset_only": True})["conditional_parcels"]["scenarios"]["S"]["B2"]["C_conditional"] <= cp["C_desktop_high"]))

    # D17 & D18: exclusive land accounting & conservation <= 1 m2 + mutants
    assert la["A_new_road"] > 0 and la["conservation_error_m2"] <= 1.0 and D.CONSERVATION_TOL_M2 <= 1.0
    assert abs(la["A_eligible_final"] - (la["A_eligible"] - la["A_new_road"])) <= 1e-6
    _expect_fail("M:ignore_new_road_area", lambda: _check(D.analyze(paths, ci, pc, rs, opts={"scenarios": scens, "ignore_new_road_area": True})["feasibility"]["scenarios"]["S"]["land_accounting"]["regions"]["B2"]["A_new_road"] > 0))
    _expect_fail("M:double_count_dir_cond", lambda: _check(D.analyze(paths, ci, pc, rs, opts={"scenarios": scens, "double_count_direct_and_conditional": True})["conditional_parcels"]["scenarios"]["S"]["B2"]["C_conditional"] == cp["C_common"]))
    _expect_fail("M:drop_direct_seeds", lambda: _check(D.analyze(paths, ci, pc, rs, opts={"scenarios": scens, "drop_direct_seeds": True})["conditional_parcels"]["scenarios"]["S"]["B2"]["parcels"][0]["status"] == "DIRECT"))
    _expect_fail("M:drop_dependency_chains", lambda: _check(all(len(p["dependency_chain"]) >= 1 for p in D.analyze(paths, ci, pc, rs, opts={"scenarios": scens, "drop_dependency_chains": True})["conditional_parcels"]["scenarios"]["S"]["B2"]["parcels"] if p["status"] == "INTERNAL_STREET_REQUIRED")))
    _expect_fail("M:enforce_land_use_ratio", lambda: _check(D.analyze(paths, ci, pc, rs, opts={"scenarios": scens, "enforce_land_use_ratio": True})["conditional_parcels"]["scenarios"]["S"]["B2"]["C_conditional"] == cp["C_conditional"]))

    # 1. Beach strip along road shoulder z=[0..4] -> streets rejected with BEACH_ENCROACHMENT_NOT_APPROVED unless accept_beach_street=True
    p_bch, ci_b, pc_b, rs_b = _build_bcd_fixture(td, "d_bch", [_reg("B2", [0, 0, 160, 140])], scens, [rfp] + trees, segs=[seg], grids_extra=[g1m], beach=[_rect(0, 0, 160, 4)])
    r_bch = D.analyze(p_bch, ci_b, pc_b, rs_b, opts={"scenarios": scens})["internal_streets"]["scenarios"]["S"]["B2"]
    assert r_bch["selected_count"] == 0 and r_bch["rejection_summary"].get("BEACH_ENCROACHMENT_NOT_APPROVED", 0) >= 1
    _expect_fail("M:accept_beach_street", lambda: _check(D.analyze(p_bch, ci_b, pc_b, rs_b, opts={"scenarios": scens, "accept_beach_street": True})["internal_streets"]["scenarios"]["S"]["B2"]["selected_count"] == 0))

    # 2. Site A band across z=[32..42] blocks all north-going streets (+ mutant ignore_site_a)
    sa_fp = _fp("SA_BAND", "SITE_A", [0, 32, 160, 42], prot=True, prec="EXACT_OUTLINE")
    p_sa, ci_sa, pc_sa, rs_sa = _build_bcd_fixture(td, "d_sa", [_reg("B2", [0, 0, 160, 140])], scens, [rfp, sa_fp] + trees, segs=[seg], grids_extra=[g1m])
    assert D.analyze(p_sa, ci_sa, pc_sa, rs_sa, opts={"scenarios": scens})["internal_streets"]["scenarios"]["S"]["B2"]["selected_count"] == 0
    _expect_fail("M:ignore_site_a", lambda: _check(D.analyze(p_sa, ci_sa, pc_sa, rs_sa, opts={"scenarios": scens, "ignore_street_obstacles": True, "ignore_site_a": True})["internal_streets"]["scenarios"]["S"]["B2"]["selected_count"] == 0))

    # 3. 7% slope ramp z=[5..40] + flat plateau z=[40..140] -> blocks streets (>6%) & S1 foundation stays UNVERIFIED (+ both mutants)
    g_slope = _grid_1m("B2_1M", "B2", -20, -20, 180, 160, lambda x, z: round(min(35.0, max(0.0, z - 5.0)) * 0.07, 4))
    p_sl, ci_sl, pc_sl, rs_sl = _build_bcd_fixture(td, "d_sl", [_reg("B2", [0, 0, 160, 140])], scens, [rfp] + trees, segs=[seg], grids_extra=[g_slope])
    r_sl = D.analyze(p_sl, ci_sl, pc_sl, rs_sl, opts={"scenarios": scens})
    assert r_sl["internal_streets"]["scenarios"]["S"]["B2"]["selected_count"] == 0
    assert r_sl["conditional_parcels"]["scenarios"]["S"]["B2"]["foundation_unverified_cells_m2"] > 0
    assert r_sl["conditional_parcels"]["scenarios"]["S"]["B2"]["C_conditional"] == r_sl["conditional_parcels"]["scenarios"]["S"]["B2"]["C_direct"] == 0
    _expect_fail("M:ignore_street_grade", lambda: _check(D.analyze(p_sl, ci_sl, pc_sl, rs_sl, opts={"scenarios": scens, "ignore_street_grade": True})["internal_streets"]["scenarios"]["S"]["B2"]["selected_count"] == 0))
    _expect_fail("M:count_foundation_in_cond", lambda: _check(D.analyze(p_sl, ci_sl, pc_sl, rs_sl, opts={"scenarios": scens, "count_foundation_in_conditional": True})["conditional_parcels"]["scenarios"]["S"]["B2"]["C_conditional"] == 0))

    # 4. G0-D6 30 m street junction run cap (wide 90 m source -> 45 m run rejected at 30 m, accepted at 100 m via opts AND module-constant mutation)
    assert D.STREET_JUNCTION_MAX_RUN_M == 30.0 and D.MAX_STREETS_PER_REGION == 3 and D.STREET_LENGTHS == (30, 60, 90, 120, 150) and D.CANDIDATE_BUDGET == 1280 and D.TARGET_AREA_M2 == 250000.0
    wide_cor = {"id": "WIDE_RD", "segment_id": "WIDE", "polygon": _rect(-10, -45, 170, 45), "bounds": [-10, -45, 170, 45], "is_rect": True}
    src_w = {"id": "WIDE", "source_type": "EXISTING_ROAD", "centerline": [[0.0, 0.0], [100.0, 0.0]], "carriageway_width_m": 90.0, "corridors": [wide_cor], "dependency_chains": [[]], "beach_encroachment_m2": 0.0}
    cand_w = {"street_id": "ST_W", "source": src_w, "start": [50.0, 0.0], "end": [50.0, 120.0]}
    steps_w = D._street_steps(50.0, 0.0, 50.0, 120.0)
    ok_30, run_w, _, _, err_30 = D._check_street_junction_and_bounds(cand_w, steps_w, [0, 0, 160, 140], [], {})
    assert not ok_30 and err_30 == "STREET_JUNCTION_RUN_EXCEEDED" and 40.0 <= run_w <= 60.0
    _expect_fail("M:street_run_cap_100m", lambda: _check(not D._check_street_junction_and_bounds(cand_w, steps_w, [0, 0, 160, 140], [], {"street_junction_max_run_m": 100.0})[0]))
    orig_cap = D.STREET_JUNCTION_MAX_RUN_M
    try:
        D.STREET_JUNCTION_MAX_RUN_M = 100.0
        _expect_fail("M:const_run_cap_100m", lambda: _check(not D._check_street_junction_and_bounds(cand_w, steps_w, [0, 0, 160, 140], [], {})[0]))
    finally:
        D.STREET_JUNCTION_MAX_RUN_M = orig_cap

    # 5. G0-D7 candidate road overlapping direct seed parcel -> excluded with DIRECT_PARCEL_CONFLICT
    cand_conflict_rd = {"CR_OVL": {"id": "CR_OVL", "kind": "NORMAL", "control_points": [[12.0, 0.0], [12.0, 120.0]], "carriageway_width_m": 7.0, "corridor_half_width_m": 5.5, "min_radius_m": 25.0, "max_grade_pct": 6.0, "is_existing_reuse": False}}
    cg_cr = _grid_1m("COR_CR_OVL_1M", "ROAD_CORRIDOR", -15, -15, 50, 145)
    p_cf, ci_cf, pc_cf, rs_cf = _build_bcd_fixture(td, "d_cf", [_reg("B2", [0, 0, 160, 140])], scens, [rfp] + trees, segs=[seg], grids_extra=[g1m, cg_cr], c_roads=cand_conflict_rd)
    res_cf = D.analyze(p_cf, ci_cf, pc_cf, rs_cf, opts={"scenarios": scens})
    assert "CR_OVL" in res_cf["feasibility"]["scenarios"]["S"]["excluded_sources"]
    assert res_cf["feasibility"]["scenarios"]["S"]["excluded_sources"]["CR_OVL"]["reason"] == "DIRECT_PARCEL_CONFLICT"
    _expect_err("M:allow_road_seed_conflict", lambda: _check("CR_OVL" in D.analyze(p_cf, ci_cf, pc_cf, rs_cf, opts={"scenarios": scens, "allow_road_seed_conflict": True})["feasibility"]["scenarios"]["S"]["excluded_sources"]))

    # 6. D15 R08 counts as 1 building / 4 units (+ mutant r08_as_four_buildings)
    scens_b3 = {"S": {"B3": [0, 140, 0, 45]}}
    g_b3 = _grid_1m("B3_1M", "B3", -20, -20, 160, 65)
    rfp3 = _fp("RD_AVE0", "ROAD", [-10, -10, 150, 0], sg="ROADS", gt="POLYGON", prec="EXACT_OUTLINE")
    seg3 = _seg("AVE_0", [[-10, 0, -5], [150, 0, -5]], w=10.0, fp_ids=["RD_AVE0"])
    p_b3, ci_b3, pc_b3, rs_b3 = _build_bcd_fixture(td, "d15_b3", [_reg("B3", [0, 0, 140, 45])], scens_b3, [rfp3], segs=[seg3], grids_extra=[g_b3])
    cp3 = D.analyze(p_b3, ci_b3, pc_b3, rs_b3, opts={"scenarios": scens_b3})["conditional_parcels"]["scenarios"]["S"]["B3"]
    assert cp3["C_conditional"] == len(cp3["parcels"]) and cp3["C_conditional"] >= 3
    _expect_fail("M:r08_as_four", lambda: _check(D.analyze(p_b3, ci_b3, pc_b3, rs_b3, opts={"scenarios": scens_b3, "r08_as_four_buildings": True})["conditional_parcels"]["scenarios"]["S"]["B3"]["C_conditional"] == len(cp3["parcels"])))


def test_d19_to_d22_verdicts_and_priority(td: Path) -> None:
    # Independent hand-crafted oracle for all 4 verdicts of 25 ha, 40, 60, and D3 priority
    def _mk_inputs(a_pos, a_dir, a_cond, a_unk, c_dirs, c_conds, c_ups, ext_v, has_cond_p=False, b_ex=False):
        rids = ("B1", "B2", "B3")
        rl = {r: {"A_gross": 120000.0, "A_possible": a_pos[i], "A_direct": a_dir[i], "A_conditional": a_cond[i], "A_unknown": a_unk[i]} for i, r in enumerate(rids)}
        rc = {r: {"C_direct": c_dirs[i], "C_conditional": c_conds[i], "C_upper": c_ups[i], "parcels": [{"status": "INTERNAL_STREET_REQUIRED" if has_cond_p else "DIRECT"}]} for i, r in enumerate(rids)}
        rv = {r: {"verdict": ext_v[i]} for i, r in enumerate(rids)}
        rs = {r: {"search_budget_exhausted": b_ex} for r in rids}
        return rl, rc, rv, rs

    # 1. All FEASIBLE -> D3 = FEASIBLE (even if 60 ideal is UNVERIFIED!)
    v1 = D.compute_verdicts(*_mk_inputs((100000, 100000, 100000), (90000, 90000, 90000), (0, 0, 0), (0, 0, 0), (10, 12, 18), (10, 12, 18), (40, 40, 40), ("FEASIBLE", "FEASIBLE", "FEASIBLE")))
    assert v1["land_25ha"]["verdict"] == "FEASIBLE" and v1["buildings_40"]["verdict"] == "FEASIBLE" and v1["buildings_60"]["verdict"] == "UNVERIFIED" and v1["D3"]["verdict"] == "FEASIBLE"
    # Mutant: gating D3 on 60 turns FEASIBLE into UNVERIFIED
    _expect_fail("M:gate_d3_on_60", lambda: _check(D.compute_verdicts(*_mk_inputs((100000, 100000, 100000), (90000, 90000, 90000), (0, 0, 0), (0, 0, 0), (10, 12, 18), (10, 12, 18), (40, 40, 40), ("FEASIBLE", "FEASIBLE", "FEASIBLE")), opts={"gate_d3_on_60": True})["D3"]["verdict"] == "FEASIBLE"))

    # 2. All CONDITIONAL -> D3 = CONDITIONAL
    v2 = D.compute_verdicts(*_mk_inputs((100000, 100000, 100000), (70000, 70000, 70000), (20000, 20000, 20000), (0, 0, 0), (5, 0, 17), (10, 12, 18), (40, 40, 40), ("FEASIBLE", "CONDITIONAL", "FEASIBLE"), has_cond_p=True))
    assert v2["land_25ha"]["verdict"] == "CONDITIONAL" and v2["buildings_40"]["verdict"] == "CONDITIONAL" and v2["road_connectivity"]["verdict"] == "CONDITIONAL" and v2["D3"]["verdict"] == "CONDITIONAL"

    # 3. 25 ha proven NOT FEASIBLE (sum A_possible = 210,000 < 250,000) -> D3 = NOT FEASIBLE
    v3 = D.compute_verdicts(*_mk_inputs((70000, 70000, 70000), (60000, 60000, 60000), (0, 0, 0), (0, 0, 0), (10, 12, 18), (10, 12, 18), (40, 40, 40), ("FEASIBLE", "FEASIBLE", "FEASIBLE")))
    assert v3["land_25ha"]["verdict"] == D.VERDICT_NOT_FEASIBLE and v3["D3"]["verdict"] == D.VERDICT_NOT_FEASIBLE

    # 4. D20 cross-region non-offset: total 50 >= 40 (B1=20, B2=20, B3=10 < 18) -> UNVERIFIED (C_upper>=18), NOT FEASIBLE/CONDITIONAL (+ mutant)
    inp4 = _mk_inputs((100000, 100000, 100000), (90000, 90000, 90000), (0, 0, 0), (0, 0, 0), (20, 20, 10), (20, 20, 10), (40, 40, 40), ("FEASIBLE", "FEASIBLE", "FEASIBLE"))
    v4 = D.compute_verdicts(*inp4)
    assert v4["buildings_40"]["verdict"] == "UNVERIFIED" and v4["D3"]["verdict"] == "UNVERIFIED"
    _expect_fail("M:cross_region_offset", lambda: _check(D.compute_verdicts(*inp4, opts={"allow_cross_region_offset": True})["buildings_40"]["verdict"] == "UNVERIFIED"))

    # 5. C_upper below target -> 40 verdict NOT FEASIBLE
    v5 = D.compute_verdicts(*_mk_inputs((100000, 100000, 100000), (90000, 90000, 90000), (0, 0, 0), (0, 0, 0), (10, 12, 10), (10, 12, 10), (40, 40, 15), ("FEASIBLE", "FEASIBLE", "FEASIBLE")))
    assert v5["buildings_40"]["verdict"] == D.VERDICT_NOT_FEASIBLE and v5["D3"]["verdict"] == D.VERDICT_NOT_FEASIBLE


def test_d24_d25_d26_and_real_samples(td: Path) -> None:
    # Real sample_roads B -> C -> D end-to-end + D24 linkage + D25 schema + D26 determinism + file_sha256 independence
    lo, hi = FX / "sample_roads_phone_low.json", FX / "sample_roads_desktop_high.json"
    b_dir, c_dir = td / "sr_b", td / "sr_c"
    B.analyze([lo, hi], out_dir=b_dir)
    C.analyze([lo, hi], out_dir=c_dir, capacity_inventory_path=b_dir / "capacity_inventory.json")
    ci, pc, rs = b_dir / "capacity_inventory.json", b_dir / "parcel_candidates.json", c_dir / "road_survey.json"

    # D26: 3x CLI determinism + D25 JSON completeness
    det_hashes = []
    for k in range(3):
        od = td / f"sr_d_{k}"
        assert D.main(["--dump", str(lo), "--dump", str(hi), "--capacity-inventory", str(ci), "--parcel-candidates", str(pc), "--road-survey", str(rs), "--out", str(od)]) == 0
        f_st = json.loads((od / "internal_streets.json").read_text(encoding="utf-8"))
        f_cp = json.loads((od / "conditional_parcels.json").read_text(encoding="utf-8"))
        f_fe = json.loads((od / "feasibility.json").read_text(encoding="utf-8"))
        assert f_st["schema_version"] == 1 and f_cp["schema_version"] == 1 and f_fe["schema_version"] == 1
        assert "runtime_meta" in f_fe and "elapsed_s" in f_fe["runtime_meta"]
        det_hashes.append((f_st["deterministic_sha256"], f_cp["deterministic_sha256"], f_fe["deterministic_sha256"]))
    assert det_hashes[0] == det_hashes[1] == det_hashes[2], "D26 determinism failed"

    # Verify properties on sample_roads (no hard-coded formal numbers)
    fe = json.loads((td / "sr_d_0/feasibility.json").read_text(encoding="utf-8"))
    assert fe["scenarios"]["INITIAL"]["verdicts"]["land_25ha"]["verdict"] == D.VERDICT_NOT_FEASIBLE
    assert fe["scenarios"]["REVISED"]["verdicts"]["D3"]["verdict"] in D.VERDICT_PRIORITY
    for sid, sc in fe["scenarios"].items():
        for rid, lr in sc["land_accounting"]["regions"].items():
            assert lr["conservation_error_m2"] <= 1.0, f"Conservation failed {sid}/{rid}"
    # Verify H01 (NOT_FEASIBLE) is never a source and per-scenario/region diagnostic summary is present
    st_doc = json.loads((td / "sr_d_0/internal_streets.json").read_text(encoding="utf-8"))
    assert "summary" in st_doc
    for sid, regs in st_doc["scenarios"].items():
        for rid, r in regs.items():
            assert all(s["source_road_id"] != "H01" for s in r["selected_streets"])
            sm = st_doc["summary"][sid][rid]
            for k in ("candidate_count", "tier1_passed_count", "zero_gain_count", "tier2_verified_count", "selected_count", "tier1_rejection_counts", "tier2_rejection_counts", "rejection_summary"):
                assert k in r and k in sm and sm[k] == r[k]

    # D24: file_sha256 change alone passes; tampered fingerprint / declared hash / mismatched direct parcel IDs rejected
    lo_alt_d = json.loads(lo.read_text(encoding="utf-8"))
    lo_alt_d["metadata"]["generated_at"] = "2099-12-31T00:00:00Z"
    lo_alt = td / "lo_alt.json"
    lo_alt.write_text(json.dumps(lo_alt_d, indent=2), encoding="utf-8")
    assert hashlib.sha256(lo_alt.read_bytes()).hexdigest() != hashlib.sha256(lo.read_bytes()).hexdigest()
    D.load_and_verify_inputs([lo_alt, hi], ci, pc, rs)

    bad_rs = json.loads(rs.read_text(encoding="utf-8"))
    bad_rs["presets"]["PHONE_LOW"]["static_fingerprint"] = "0" * 64
    bad_rs_p = td / "bad_rs.json"
    bad_rs_p.write_text(json.dumps(bad_rs), encoding="utf-8")
    _expect_err("D24:bad_rs_fp", lambda: D.load_and_verify_inputs([lo, hi], ci, pc, bad_rs_p))
    _expect_err("D24:bad_declared_hash", lambda: D.load_and_verify_inputs([lo, hi], ci, pc, rs, opts={"expected_artifact_hashes": {"road_survey": "0" * 64}}))

    bad_pc = json.loads(pc.read_text(encoding="utf-8"))
    bad_pc["scenarios"]["REVISED"]["B1"]["direct_parcels"] = [{"id": "FAKE_001"}]
    bad_pc_p = td / "bad_pc.json"
    bad_pc_p.write_text(json.dumps(bad_pc), encoding="utf-8")
    _expect_err("D24:direct_id_mismatch", lambda: D.analyze([lo, hi], ci, bad_pc_p, rs))

    bad_d = copy.deepcopy(lo_alt_d)
    bad_d["regions"][0]["name"] = "TAMPERED_REGION"
    bad_dp = _write_dump(td, "bad_d.json", bad_d)
    _expect_err("D24:bad_dump_fp", lambda: D.load_and_verify_inputs([bad_dp, hi], ci, pc, rs))
    _expect_fail("M:skip_fingerprint_check", lambda: _expect_err("must_reject_fp", lambda: D.load_and_verify_inputs([bad_dp, hi], ci, pc, rs, opts={"skip_fingerprint_check": True})))

    # Mutant: unverified / NOT_FEASIBLE source (H01) accepted when allow_unverified_sources=True
    d_lo = json.loads(lo.read_text(encoding="utf-8"))
    g_lo = B.build_road_graph(d_lo)
    rs_obj = json.loads(rs.read_text(encoding="utf-8"))
    assert all(s["id"] != "H01" for s in D._extract_sources(g_lo, rs_obj, set(), {}))
    _expect_fail("M:allow_unverified_sources", lambda: _check(all(s["id"] != "H01" for s in D._extract_sources(g_lo, rs_obj, set(), {"allow_unverified_sources": True}))))


def test_perf_oblique_500x500_and_parity(td: Path) -> None:
    # 1. Exact brute-force parity of oblique SAT + 3-way convex R7 scoring across 8deg, 14deg, and 45deg streets
    for ang in (8.0, 14.0, 45.0):
        rad = math.radians(ang)
        st_pt, en_pt = [10.0, 50.0], [10.0 + 80.0 * math.cos(rad), 50.0 + 80.0 * math.sin(rad)]
        cor = D._street_corridor_dict(f"PAR_{int(ang)}", st_pt[0], st_pt[1], en_pt[0], en_pt[1])
        rows = {cz: (list(range(0, 100, 3)), [[(12, 11), (11, 12)] for _ in range(0, 100, 3)]) for cz in range(0, 100, 3)}
        fast = D._score_street_candidate(cor, st_pt, en_pt, rows, 12, 12, {})
        brute = {
            (cx, cz)
            for cz, (xs, szs) in rows.items()
            for cx, szl in zip(xs, szs)
            if any(B.evaluate_access((cx - hw, cz - hh, cx + hw, cz + hh), [cor])["ok"] for hw, hh in szl)
        }
        assert fast == brute, f"Oblique scoring parity mismatch at {ang}deg: fast={len(fast)} brute={len(brute)}"

    # 2. Synthetic 500m x 500m flat oblique performance regression (both 8deg selecting 3 streets & 45deg zero-gain)
    g1m = _grid_1m("B2_1M", "B2", -20, -20, 520, 520)

    def _run_stress(sx: float, sz: float, ex: float, ez: float) -> tuple[dict, float, int]:
        dx, dz = ex - sx, ez - sz
        seg_l = math.hypot(dx, dz)
        nx, nz = -dz / seg_l * 5.0, dx / seg_l * 5.0
        rpoly = [[sx - nx, sz - nz], [ex - nx, ez - nz], [ex + nx, ez + nz], [sx + nx, sz + nz]]
        rfp = _fp("RD_OBL", "ROAD", list(W.poly_bounds(rpoly)), sg="ROADS", gt="POLYGON", prec="EXACT_OUTLINE")
        rfp["polygon"] = rpoly
        seg = _seg("AVE_0", [[sx, 0, sz], [ex, 0, ez]], w=10.0, fp_ids=["RD_OBL"])
        d_lo = make_dump(preset="PHONE_LOW", regions=[_reg("B2", [0, 0, 500, 500])], footprints=[rfp], roads={"nodes": [], "segments": [seg], "completeness": "COMPLETE"}, pg_bounds=[-100, -100, 600, 600])
        d_lo["height_grids"] = [g1m]
        d_lo["metadata"]["static_fingerprint"] = W.compute_static_fingerprint(d_lo)
        d_hi = dict(d_lo, metadata=dict(d_lo["metadata"], preset="DESKTOP_HIGH"))
        d_hi["metadata"]["static_fingerprint"] = W.compute_static_fingerprint(d_hi)
        dumps = {"PHONE_LOW": d_lo, "DESKTOP_HIGH": d_hi}
        graph = B.build_road_graph(d_lo)
        ex_cors = B.corridors_from_graph(graph, include_unverified=False)
        m = B.build_masks(d_lo, "S", "B2", [0, 0, 500, 500])
        v = {p: {o: B.geom_valid(m, p, o) for o in (0, 90)} for p in B.REGION_RULES["B2"]["prototypes"]}
        src = {"id": "AVE_0", "source_type": "EXISTING_ROAD", "centerline": [[sx, sz], [ex, ez]], "carriageway_width_m": 10.0, "corridors": ex_cors, "dependency_chains": [[]], "beach_encroachment_m2": 0.0}

        orig_ea = D.evaluate_access
        calls = [0]

        def _counted_ea(*args, **kwargs):
            calls[0] += 1
            return orig_ea(*args, **kwargs)

        D.evaluate_access = _counted_ea
        try:
            t0 = time.monotonic()
            res = D.select_internal_streets("S", "B2", [0, 0, 500, 500], [src], m, v, ex_cors, [], dumps, graph, {})
            dt = time.monotonic() - t0
        finally:
            D.evaluate_access = orig_ea
        return res, dt, calls[0]

    # 8deg oblique: 180 candidates, >20k unserved lattice centers, selects 3 oblique streets under <= 5.0 s & <= 3000 calls
    res8, dt8, calls8 = _run_stress(40.0, 210.0, 460.0, 270.0)
    assert res8["candidate_count"] >= 150 and res8["tier1_passed_count"] >= 150 and res8["unserved_lattice_centers_initial"] >= 5000
    assert res8["selected_count"] == 3 and res8["tier2_verified_count"] >= 3
    assert dt8 <= 5.0, f"500x500 8deg oblique exceeded 5.0 s budget: {dt8:.2f}s"
    assert calls8 <= 3000, f"500x500 8deg oblique evaluate_access calls exceeded bound: {calls8}"

    # 45deg oblique: 250 candidates, >20k unserved lattice centers, all T1 survivors zero-gain, <= 5.0 s & <= 500 calls
    res45, dt45, calls45 = _run_stress(40.0, 40.0, 460.0, 460.0)
    assert res45["candidate_count"] >= 150 and res45["tier1_passed_count"] >= 150 and res45["zero_gain_count"] == res45["tier1_passed_count"]
    assert res45["selected_count"] == 0 and dt45 <= 5.0 and calls45 <= 500
    print(f"  [PERF] 500x500 8deg: {dt8:.2f}s ({calls8} calls, 3 sel) | 45deg: {dt45:.2f}s ({calls45} calls, 0 sel)")


def main() -> int:
    t0 = time.monotonic()
    suites = [
        ("G0-D1 signature pin & B seed_parcels", test_g0d1_signatures_and_b_seeds),
        ("D01-D05/D23 candidates, 3-street cap, budget", test_d01_to_d05_d23_candidates_and_budget),
        ("D06-D18/D27-D28 legality, conflicts, cross-preset, accounting", test_d06_to_d18_legality_conflicts_cross_preset_accounting),
        ("D19-D22 verdicts (25ha/40/60/D3) & priority", test_d19_to_d22_verdicts_and_priority),
        ("PERF 500x500 oblique stress & exact brute-force parity", test_perf_oblique_500x500_and_parity),
        ("D24-D26 linkage, schema, determinism & real sample_roads", test_d24_d25_d26_and_real_samples),
    ]
    with tempfile.TemporaryDirectory() as tmp:
        td = Path(tmp)
        for label, fn in suites:
            ts = time.monotonic()
            fn(td)
            print(f"PASS [{label}] ({time.monotonic() - ts:.2f}s)")
    elapsed = time.monotonic() - t0
    print(f"RESULT: PASS (WE-01D D01-D28 + G0-D1..D16 + B seed_parcels + perf 500x500 oblique + all mutants RED + real sample_roads in {elapsed:.2f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
