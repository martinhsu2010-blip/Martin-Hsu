#!/usr/bin/env python3
"""WE-01B (T-016B) Parcel Capacity Analyzer check suite (B01-B09, B11, B12, B17, B18, B20-B30, E1.4, E2.5, 18 mutants, real samples)."""
from __future__ import annotations

import copy
import csv
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

FX = ROOT / "tools/fixtures/we01"
BASE_SHA = "84319439243b51aa8d119e33eb62a0637feea887"


def _check(cond: bool, msg: str = "") -> None:
    assert cond, msg


def _expect_err(label: str, fn) -> None:
    try:
        fn()
    except (AssertionError, B.CapacityError, W.ValidationError):
        return
    raise AssertionError(f"Expected FAILURE but stayed GREEN: {label}")


def _reg(rid: str, b: list[int]) -> dict:
    return {"id": rid, "name": rid, "initial_polygon": _rect(*b), "survey_polygon": _rect(*b), "buffer_m": 0, "source_ref": "syn"}


def _seg(sid: str, cl: list[list[float]], width: float = 8.0, elev: str = "GROUND", fp_ids: list[str] | None = None, ver: str = "RUNTIME_VERIFIED") -> dict:
    return {
        "id": sid, "start_node_id": None, "end_node_id": None, "centerline": cl,
        "carriageway_width_m": width, "sidewalk_left_m": None, "sidewalk_right_m": None,
        "corridor_footprint_ids": list(fp_ids or []), "elevation_type": elev,
        "traffic_route_ids": [], "source_ref": "syn_road", "verification": ver,
    }


def _road_fp(fid: str, b: list[float], cat: str = "ROAD", sg: str = "ROADS", prec: str = "EXACT_OUTLINE") -> dict:
    return _fp(fid, cat, b, sg=sg, gt="POLYGON", prec=prec)


def _cor(cid: str, b: list[float], seg_id: str | None = "AVE_0", conn: str = "VERIFIED", existing: bool = True, is_rbt: bool = False, poly: list[list[float]] | None = None) -> dict:
    pts = poly if poly is not None else _rect(*b)
    return {
        "id": cid, "segment_id": seg_id, "category": "ROAD", "source_group": "ROAD_NET.roundabouts" if is_rbt else "ROADS",
        "polygon": pts, "bounds": list(W.poly_bounds(pts)), "is_rect": W.is_axis_rect(pts),
        "connectivity": conn, "existing": existing, "is_roundabout": is_rbt,
    }


def _c_opts(scen_map: dict[str, dict[str, list[int]]], **extra) -> dict:
    return {"allow_custom_scenarios": True, "scenarios": scen_map, **extra}


def _make_pair(td: Path, prefix: str, regs: list[dict], lo_kw: dict | None = None, hi_kw: dict | None = None, **shared) -> list[Path]:
    kw_lo = dict(shared, **(lo_kw or {}))
    kw_hi = dict(shared, **(hi_kw or {}))
    p_lo = _write_dump(td, f"{prefix}_lo.json", make_dump(preset="PHONE_LOW", regions=regs, **kw_lo))
    p_hi = _write_dump(td, f"{prefix}_hi.json", make_dump(preset="DESKTOP_HIGH", regions=regs, **kw_hi))
    return [p_lo, p_hi]


def _base_ave0_roads(z0: float = -10.0, z1: float = 0.0, x0: float = 0.0, x1: float = 120.0):
    rfp = _road_fp("RD_AVE_0", [x0, z0, x1, z1])
    seg = _seg("AVE_0", [[x0, 0.0, (z0 + z1) / 2.0], [x1, 0.0, (z0 + z1) / 2.0]], width=z1 - z0, fp_ids=["RD_AVE_0"])
    return [rfp], {"nodes": [], "segments": [seg], "completeness": "COMPLETE"}


def test_b01_to_b06(td: Path) -> None:
    # B01: parcel dimensions & orientation swap
    assert B.PROTOTYPES["R01"]["parcel"] == (42, 34) and B.PROTOTYPES["R01"]["area_m2"] == 1428
    assert B.PROTOTYPES["R02"]["parcel"] == (48, 42) and B.PROTOTYPES["R02"]["area_m2"] == 2016
    assert B.PROTOTYPES["R05"]["parcel"] == (24, 22) and B.PROTOTYPES["R05"]["area_m2"] == 528 and B.PROTOTYPES["R05"]["proxy"] is True
    assert B.PROTOTYPES["R08"]["parcel"] == (38, 24) and B.PROTOTYPES["R08"]["buildings"] == 1 and B.PROTOTYPES["R08"]["units"] == 4

    # B02: prefix sums vs brute force on mixed obstacles / Site A / water / unknown
    fps = [
        _fp("SA1", "SITE_A", [0, 0, 10, 10], prot=True, prec="EXACT_OUTLINE"),
        _fp("OB1", "BUILDING", [15, 5, 22, 14], prec="EXACT_OUTLINE"),
        _fp("UK1", "OTHER", [30, 10, 35, 16], ver="UNKNOWN"),
    ]
    d2 = make_dump(regions=[_reg("B2", [0, 0, 50, 30])], footprints=fps, water=[_rect(40, 20, 48, 28)], pg_bounds=[-100, -100, 100, 100])
    m2 = B.build_masks(d2, "S", "B2", [0, 0, 50, 30])
    for rx0, rz0, rx1, rz1 in ((0, 0, 50, 30), (5, 5, 25, 20), (10, 0, 15, 10), (22, 14, 30, 25), (-5, -5, 12, 12)):
        brute = sum(0 if m2.is_base_free(x, z) else 1 for z in range(rz0, rz1) for x in range(rx0, rx1))
        assert m2.rect_blocked(rx0, rz0, rx1, rz1) == brute, f"B02 prefix sum mismatch on {(rx0, rz0, rx1, rz1)}"

    # B03 + B04 + M-B02: non-overlap & obstacle / Site A protection
    rfps, roads = _base_ave0_roads(-10, 0, 0, 120)
    obs = [_fp("SA_B2", "SITE_A", [24, 0, 36, 24], prot=True, prec="EXACT_OUTLINE"), _fp("TR_B2", "TREE", [62, 4, 68, 12])]
    pair = _make_pair(td, "b03", [_reg("B2", [0, 0, 120, 50])], footprints=rfps + obs, roads=roads, pg_bounds=[-200, -200, 200, 200])
    opts = _c_opts({"S": {"B2": [0, 120, 0, 50]}})
    inv = B.analyze(pair, opts=opts)
    r = inv["scenarios"]["S"]["regions"]["B2"]
    ps = r["direct_parcels"]
    assert len(ps) >= 2 and r["areas_m2"]["A_protected"] == 288.0
    for i, a in enumerate(ps):
        ax0, az0, ax1, az1 = a["bounds"]
        pw, ph = B.PROTOTYPES[a["prototype"]]["parcel"]
        assert (ax1 - ax0, az1 - az0) == ((pw, ph) if a["orientation"] == 0 else (ph, pw))
        assert not (ax0 < 36 and ax1 > 24 and az0 < 24 and az1 > 0), "B04 Site A violated"
        assert not (ax0 < 68 and ax1 > 62 and az0 < 12 and az1 > 4), "B04 obstacle violated"
        for b in ps[i + 1:]:
            bx0, bz0, bx1, bz1 = b["bounds"]
            assert ax1 <= bx0 or bx1 <= ax0 or az1 <= bz0 or bz1 <= az0, "B03 overlap"

    pair_ov = _make_pair(td, "b03_ov", [_reg("B2", [0, 0, 28, 24])], footprints=rfps, roads=roads, pg_bounds=[-100, -100, 100, 100])
    opts_ov = _c_opts({"S": {"B2": [0, 28, 0, 24]}})

    def _assert_no_overlap(o: dict) -> None:
        ps_o = B.analyze(pair_ov, opts=o)["scenarios"]["S"]["regions"]["B2"]["direct_parcels"]
        for i, a in enumerate(ps_o):
            for b in ps_o[i + 1:]:
                assert a["bounds"][2] <= b["bounds"][0] or b["bounds"][2] <= a["bounds"][0] or a["bounds"][3] <= b["bounds"][1] or b["bounds"][3] <= a["bounds"][1]

    _assert_no_overlap(opts_ov)
    _expect_fail("M-B02 allow_overlap", lambda: _assert_no_overlap(dict(opts_ov, allow_overlap=True)))

    # B05 + B06 + M-B03: prototype mix ratios & R08 = 1 building / 4 units
    assert B.check_ratio({"R02": 2, "R01": 1}, "B1") and not B.check_ratio({"R02": 1, "R01": 2}, "B1")
    assert B.check_ratio({"R05": 4}, "B2") and not B.check_ratio({"R05": 3, "R01": 1}, "B2")
    assert not B.check_ratio({"R01": 1, "R05": 1}, "B3") and B.check_ratio({"R01": 1, "R05": 1, "R08": 1}, "B3")
    assert B.check_ratio({"R01": 1, "R05": 3, "R08": 1}, "B3") and not B.check_ratio({"R01": 1, "R05": 4, "R08": 1}, "B3")

    rfps3, roads3 = _base_ave0_roads(-10, 0, 0, 140)
    pair3 = _make_pair(td, "b06", [_reg("B3", [0, 0, 140, 45])], footprints=rfps3, roads=roads3, pg_bounds=[-200, -200, 200, 200])
    opts3 = _c_opts({"S": {"B3": [0, 140, 0, 45]}})

    def _assert_b06(o: dict) -> None:
        r3 = B.analyze(pair3, opts=o)["scenarios"]["S"]["regions"]["B3"]
        c3 = r3["capacities"]
        assert c3["C_direct"] == len(r3["direct_parcels"]) and c3["C_direct"] >= 3
        r08_n = c3["prototype_counts_direct"].get("R08", 0)
        assert r08_n >= 1 and c3["units_direct"] == c3["C_direct"] + 3 * r08_n
        assert all(p["buildings"] == 1 and p["units"] == 4 for p in r3["direct_parcels"] if p["prototype"] == "R08")

    _assert_b06(opts3)
    _expect_fail("M-B03 r08_as_four_buildings", lambda: _assert_b06(dict(opts3, r08_as_four_buildings=True)))


def test_b07_linkage(td: Path) -> None:
    # Real WE-01A artifacts linked to dump pair; changing file_sha256 only must STILL pass
    we01a_out = td / "we01a"
    lo_src, hi_src = _make_pair(td, "b07", [_reg("B2", [0, 0, 30, 20])], pg_bounds=[-100, -100, 100, 100])
    assert W.main(["--dump", str(lo_src), "--dump", str(hi_src), "--out", str(we01a_out)]) == 0
    li_path, lr_path = we01a_out / "land_inventory.json", we01a_out / "land_report.md"
    li_sha = hashlib.sha256(li_path.read_bytes()).hexdigest()
    lr_sha = hashlib.sha256(lr_path.read_bytes()).hexdigest()

    # Copy dump with altered generated_at & whitespace -> different file_sha256, identical static_fingerprint
    lo_copy_d = json.loads(lo_src.read_text(encoding="utf-8"))
    lo_copy_d["metadata"]["generated_at"] = "2099-12-31T00:00:00Z"
    lo_copy = td / "lo_diff_filesha.json"
    lo_copy.write_text(json.dumps(lo_copy_d, indent=2), encoding="utf-8")
    assert hashlib.sha256(lo_copy.read_bytes()).hexdigest() != hashlib.sha256(lo_src.read_bytes()).hexdigest()
    dumps = B.load_dumps([lo_copy, hi_src], land_inventory_path=li_path, land_report_path=lr_path, opts={"expected_artifact_hashes": {"land_inventory": li_sha, "land_report": lr_sha}})
    assert set(dumps.keys()) == {"PHONE_LOW", "DESKTOP_HIGH"}

    # Reject single preset, BASE mismatch, tampered fingerprint, declared hash mismatch, and land_inventory fingerprint mismatch
    _expect_err("B07:single_preset", lambda: B.load_dumps([lo_src]))
    bad_base = _write_dump(td, "bad_base.json", make_dump(preset="DESKTOP_HIGH", base_sha="0" * 40))
    _expect_err("B07:base_mismatch", lambda: B.load_dumps([lo_src, bad_base]))
    bad_fp_d = copy.deepcopy(lo_copy_d)
    bad_fp_d["height_grids"][1]["heights"][0] = 99.0
    bad_fp = _write_dump(td, "bad_fp.json", bad_fp_d)
    _expect_err("B07:stale_fp", lambda: B.load_dumps([bad_fp, hi_src]))
    _expect_err("B07:declared_hash", lambda: B.load_dumps([lo_src, hi_src], land_inventory_path=li_path, opts={"expected_artifact_hashes": {"land_inventory": "0" * 64}}))

    bad_li = json.loads(li_path.read_text(encoding="utf-8"))
    bad_li["presets"][0]["static_fingerprint"] = "f" * 64
    bad_li_p = td / "bad_li.json"
    bad_li_p.write_text(json.dumps(bad_li), encoding="utf-8")
    _expect_err("B07:land_inv_fp_mismatch", lambda: B.load_dumps([lo_src, hi_src], land_inventory_path=bad_li_p))
    # M-B11: skip_land_linkage_check must make our linkage rejection test go RED
    _expect_fail("M-B11 skip_land_linkage_check", lambda: _expect_err("must_reject", lambda: B.load_dumps([lo_src, hi_src], land_inventory_path=bad_li_p, opts={"skip_land_linkage_check": True})))


def test_b08_b09_b11(td: Path) -> None:
    # B08 + M-B01 + M-B06: independent analytical height oracle h(x,z) = 1.5 + 0.02*x + 0.01*z (slope ~2.24% = S0)
    hfn = lambda x, z: round(1.5 + 0.02 * x + 0.01 * z, 4)
    rfps, roads = _base_ave0_roads(-10, 0, 0, 60)
    pair = _make_pair(td, "b08", [_reg("B2", [0, 0, 60, 40])], height_fn=hfn, footprints=rfps, roads=roads, pg_bounds=[-100, -100, 100, 100])
    opts = _c_opts({"S": {"B2": [0, 60, 0, 40]}})

    def _assert_b08(o: dict) -> None:
        r = B.analyze(pair, opts=o)["scenarios"]["S"]["regions"]["B2"]
        assert r["capacities"]["C_direct"] >= 1
        p0 = r["direct_parcels"][0]
        x0, z0, x1, z1 = p0["bounds"]
        cx, cz = (x0 + x1) // 2, (z0 + z1) // 2
        assert abs(p0["terrain"]["min_h_m"] - hfn(x0, z0)) <= 0.01
        assert abs(p0["terrain"]["max_h_m"] - hfn(x1, z1)) <= 0.01
        assert abs(p0["terrain"]["center_h_m"] - hfn(cx, cz)) <= 0.01

    _assert_b08(opts)
    _expect_fail("M-B01 height_offset_m", lambda: _assert_b08(dict(opts, height_offset_m=0.5)))

    # M-B06: missing height (None) at center (15, 11) of 30x26 region intersects every R05 placement
    pair_mh = _make_pair(td, "b08_mh", [_reg("B2", [0, 0, 30, 26])], height_fn=lambda x, z: None if (x == 15 and z == 11) else 0.0, footprints=rfps, roads=roads, pg_bounds=[-100, -100, 100, 100])
    opts_mh = _c_opts({"S": {"B2": [0, 30, 0, 26]}})

    def _assert_mh(o: dict) -> None:
        assert B.analyze(pair_mh, opts=o)["scenarios"]["S"]["regions"]["B2"]["capacities"]["C_direct"] == 0

    _assert_mh(opts_mh)
    _expect_fail("M-B06 allow_missing_height", lambda: _assert_mh(dict(opts_mh, allow_missing_height=True)))

    # B09 + M-B09: flat physical ground outside terrain_regions accepted; outside physical_ground or UNKNOWN rejected
    pair_pg_ok = _make_pair(td, "b09_ok", [_reg("B2", [0, 0, 30, 26])], terrain_regions=[], footprints=rfps, roads=roads, pg_bounds=[-100, -100, 100, 100])
    assert B.analyze(pair_pg_ok, opts=opts_mh)["scenarios"]["S"]["regions"]["B2"]["capacities"]["C_direct"] >= 1
    pair_pg_out = _make_pair(td, "b09_out", [_reg("B2", [0, 0, 30, 26])], footprints=rfps, roads=roads, pg_bounds=[-100, -100, 10, 100])
    pair_pg_unk = _make_pair(td, "b09_unk", [_reg("B2", [0, 0, 30, 26])], footprints=rfps, roads=roads, pg_bounds=[-100, -100, 100, 100], pg_ver="UNKNOWN")
    assert B.analyze(pair_pg_unk, opts=opts_mh)["scenarios"]["S"]["regions"]["B2"]["capacities"]["C_direct"] == 0

    def _assert_pg_out(o: dict) -> None:
        assert B.analyze(pair_pg_out, opts=o)["scenarios"]["S"]["regions"]["B2"]["capacities"]["C_direct"] == 0

    _assert_pg_out(opts_mh)
    _expect_fail("M-B09 ignore_physical_ground", lambda: _assert_pg_out(dict(opts_mh, ignore_physical_ground=True)))

    # B11 + M-B05: B1 + B2 total >= 40 but B3 < 18 -> all_regions_meet_min_direct MUST be False
    # B2 strip 624x22 fits 26 R05; B1 strip 672x42 fits 14 R02 -> total 40 >= 40, B3 = 0 < 18
    rfps11 = [_road_fp("RD_AVE_0", [0, -10, 680, 0]), _road_fp("RD_S2", [0, 30, 680, 40])]
    segs11 = [
        _seg("AVE_0", [[0, 0, -5], [680, 0, -5]], width=10, fp_ids=["RD_AVE_0"]),
        _seg("CONN_V", [[5, 0, -5], [5, 0, 35]], width=8, fp_ids=[]),
        _seg("S2", [[0, 0, 35], [680, 0, 35]], width=10, fp_ids=["RD_S2"]),
    ]
    regs11 = [_reg("B1", [0, 40, 672, 82]), _reg("B2", [0, 0, 624, 22]), _reg("B3", [0, 100, 30, 125])]
    pair11 = _make_pair(td, "b11", regs11, footprints=rfps11, roads={"nodes": [], "segments": segs11, "completeness": "COMPLETE"}, pg_bounds=[-100, -100, 750, 200])
    opts11 = _c_opts({"S": {"B1": [0, 672, 40, 82], "B2": [0, 624, 0, 22], "B3": [0, 30, 100, 125]}})

    def _assert_b11(o: dict) -> None:
        sc = B.analyze(pair11, opts=o)["scenarios"]["S"]
        assert sc["totals"]["C_direct"] >= 40 and sc["regions"]["B3"]["capacities"]["C_direct"] == 0
        assert sc["totals"]["all_regions_meet_min_direct"] is False

    _assert_b11(opts11)
    _expect_fail("M-B05 allow_cross_region_offset", lambda: _assert_b11(dict(opts11, allow_cross_region_offset=True)))


def test_b12_b17_b20(td: Path) -> None:
    # B12: exact hand-computed C_upper oracle
    assert B.min_area_for_count("B1", 1) == 2016 and B.min_area_for_count("B1", 2) == 3444 and B.min_area_for_count("B1", 3) == 5460
    assert B.compute_c_upper("B1", 3443) == 1 and B.compute_c_upper("B1", 3444) == 2 and B.compute_c_upper("B1", 5460) == 3
    assert B.compute_c_upper("B2", 1583) == 2 and B.compute_c_upper("B2", 1584) == 3
    assert B.min_area_for_count("B3", 1) is None and B.min_area_for_count("B3", 2) is None
    assert B.min_area_for_count("B3", 3) == 2868 and B.min_area_for_count("B3", 5) == 3924 and B.min_area_for_count("B3", 6) == 5736
    assert B.compute_c_upper("B3", 2867) == 0 and B.compute_c_upper("B3", 2868) == 3 and B.compute_c_upper("B3", 5735) == 5 and B.compute_c_upper("B3", 5736) == 6

    # Search fail != NOT_FEASIBLE (+ M-B08) & CONSERVATIVE_AABB does NOT shrink C_upper (+ extra mutant)
    # 100x80 = 8000 m2 -> C_upper(B2) = 15 >= min(12), no road -> C_direct = 0 -> SEARCH_INSUFFICIENT_UNPROVEN
    fps_ca = [_fp("AABB1", "BUILDING", [0, 0, 50, 80], prec="CONSERVATIVE_AABB")]
    pair_ca = _make_pair(td, "b12_ca", [_reg("B2", [0, 0, 100, 80])], footprints=fps_ca, pg_bounds=[-200, -200, 200, 200])
    opts_ca = _c_opts({"S": {"B2": [0, 100, 0, 80]}})

    def _assert_b12(o: dict) -> None:
        r = B.analyze(pair_ca, opts=o)["scenarios"]["S"]["regions"]["B2"]
        assert r["capacities"]["C_direct"] == 0 and r["capacities"]["C_upper"] == 15
        assert r["areas_m2"]["A_possible"] == 8000.0
        assert r["capacity_bound_status"] == "SEARCH_INSUFFICIENT_UNPROVEN"

    _assert_b12(opts_ca)
    _expect_fail("M-B08 search_fail_as_infeasible", lambda: _assert_b12(dict(opts_ca, search_fail_as_infeasible=True)))
    _expect_fail("EXTRA exclude_conservative_in_upper", lambda: _assert_b12(dict(opts_ca, exclude_conservative_in_upper=True)))

    # EXACT_OUTLINE DOES shrink A_possible & C_upper
    pair_ex = _make_pair(td, "b12_ex", [_reg("B2", [0, 0, 100, 80])], footprints=[_fp("EX1", "BUILDING", [0, 0, 50, 80], prec="EXACT_OUTLINE")], pg_bounds=[-200, -200, 200, 200])
    r_ex = B.analyze(pair_ex, opts=opts_ca)["scenarios"]["S"]["regions"]["B2"]
    assert r_ex["areas_m2"]["A_possible"] == 4000.0 and r_ex["capacities"]["C_upper"] == 7 and r_ex["capacity_bound_status"] == "UPPER_BOUND_BELOW_MIN"

    # B20 + M-B10: land-use ratio informational only (24x22=528 in 30x25=750 -> share 70.4% > 30% STILL accepted)
    rfps, roads = _base_ave0_roads(-10, 0, 0, 40)
    pair20 = _make_pair(td, "b20", [_reg("B2", [0, 0, 30, 25])], footprints=rfps, roads=roads, pg_bounds=[-100, -100, 100, 100])
    opts20 = _c_opts({"S": {"B2": [0, 30, 0, 25]}})

    def _assert_b20(o: dict) -> None:
        r20 = B.analyze(pair20, opts=o)["scenarios"]["S"]["regions"]["B2"]
        assert r20["capacities"]["C_direct"] == 1
        assert r20["land_use_reference"]["residential_parcel_share_pct"] > 50.0
        assert r20["land_use_reference"]["informational_only"] is True and r20["land_use_reference"]["hard_gate"] is False

    _assert_b20(opts20)
    _expect_fail("M-B10 enforce_land_use_ratio", lambda: _assert_b20(dict(opts20, enforce_land_use_ratio=True)))

    # B17: 3x determinism -> byte-identical SHA-256 across all 3 output files
    hashes = []
    for i in range(3):
        od = td / f"b17_{i}"
        B.analyze(pair20, out_dir=od, opts=opts20)
        fs = sorted(od.iterdir())
        assert [f.name for f in fs] == ["capacity_inventory.json", "capacity_report.md", "parcel_candidates.json"]
        hashes.append({f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in fs})
    assert hashes[0] == hashes[1] == hashes[2], "B17 determinism failed"


def test_b21_b22_b26(td: Path) -> None:
    # B21 + B26 + M-B13: PHONE_LOW blocks left [0..26], DESKTOP_HIGH blocks right [54..80]
    # Region 80x26 along south AVE_0: PHONE_LOW fits 2 on [26..80], DESKTOP_HIGH fits 2 on [0..54], COMMON fits 1 on [26..54]
    rfps, roads = _base_ave0_roads(-10, 0, 0, 80)
    pair = _make_pair(
        td, "b21", [_reg("B2", [0, 0, 80, 26])], roads=roads, pg_bounds=[-200, -200, 200, 200],
        lo_kw={"footprints": rfps + [_fp("LO_OBS", "TREE", [0, 0, 26, 26])]},
        hi_kw={"footprints": rfps + [_fp("HI_OBS", "TREE", [54, 0, 80, 26])]},
    )
    opts = _c_opts({"S": {"B2": [0, 80, 0, 26]}})

    def _assert_b21(o: dict) -> None:
        r = B.analyze(pair, opts=o)["scenarios"]["S"]["regions"]["B2"]
        c = r["capacities"]
        assert c["C_phone_low"] == 2 and c["C_desktop_high"] == 2 and c["C_common"] == 1
        assert c["C_common"] <= min(c["C_phone_low"], c["C_desktop_high"])
        assert r["preset_validation"]["PHONE_LOW"]["ok"] and r["preset_validation"]["DESKTOP_HIGH"]["ok"]

    _assert_b21(opts)
    _expect_fail("M-B13 swap_union_intersection", lambda: _assert_b21(dict(opts, swap_union_intersection=True)))

    # B22 synthetic: every WE-01A 5 m L0 cell has all 25 1 m cells free in masks.base_free
    fps22 = [_fp("B_EX", "BUILDING", [10, 5, 16, 12], prec="EXACT_OUTLINE"), _fp("SA_22", "SITE_A", [25, 0, 30, 10], prot=True, prec="EXACT_OUTLINE")]
    p22 = _write_dump(td, "b22.json", make_dump(regions=[_reg("B2", [0, 0, 40, 20])], footprints=fps22, water=[_rect(0, 15, 10, 20)], pg_bounds=[-100, -100, 100, 100]))
    a_res = W.analyze_dumps([p22])
    l0_area = a_res["inventory"]["regions"][0]["common_initial_class_areas_m2"]["L0"]
    m22 = B.build_masks(json.loads(p22.read_text(encoding="utf-8")), "S", "B2", [0, 0, 40, 20])
    assert m22.base_free.count(1) >= l0_area and l0_area > 0
    for cell in a_res["common_cells"]["B2"].values():
        if cell["cls"] == "L0":
            x0, z0 = int(round(cell["x0"])), int(round(cell["z0"]))
            assert all(m22.is_base_free(x, z) for z in range(z0, z0 + 5) for x in range(x0, x0 + 5)), f"B22 failed at {(x0, z0)}"


def test_b23_scenarios(td: Path) -> None:
    assert B.POLYGON_REVISION == 2
    assert B.spec_to_internal([90, 390, 930, 1230]) == [90, 930, 390, 1230]
    assert B.internal_to_spec([90, 930, 390, 1230]) == [90, 390, 930, 1230]
    B.validate_scenarios(B.SCENARIOS)

    def _area(b: list[int]) -> int:
        return (b[1] - b[0]) * (b[3] - b[2])

    assert sum(_area(b) for b in B.SCENARIOS["INITIAL"].values()) == 250000
    assert sum(_area(b) for b in B.SCENARIOS["ENVELOPE"].values()) == 720000
    assert _area(B.SCENARIOS["REVISED"]["B1"]) == 180000
    assert _area(B.SCENARIOS["REVISED"]["B2"]) == 175000
    assert _area(B.SCENARIOS["REVISED"]["B3"]) == 60000
    assert sum(_area(b) for b in B.SCENARIOS["REVISED"].values()) == 415000

    # Reject obsolete v1.3 REVISED coordinates + extra mutant accept_revised_v1
    bad_v1 = copy.deepcopy(B.SCENARIOS)
    bad_v1["REVISED"] = copy.deepcopy(B.OBSOLETE_REVISED_V1)
    _expect_err("B23:reject_revised_v1", lambda: B.validate_scenarios(bad_v1))
    _expect_fail("EXTRA accept_revised_v1", lambda: _expect_err("must_reject_v1", lambda: B.validate_scenarios(bad_v1, opts={"accept_revised_v1": True})))

    # M-B15: whole parcel must lie inside scenario polygon (20x20 too small for R05 24x22)
    d_small = make_dump(regions=[_reg("B2", [0, 0, 20, 20])], pg_bounds=[-100, -100, 100, 100])
    m_small = B.build_masks(d_small, "S", "B2", [0, 0, 20, 20])
    assert B.geom_valid(m_small, "R05", 0).count(1) == 0
    _expect_fail("M-B15 allow_out_of_bounds", lambda: _check(B.geom_valid(m_small, "R05", 0, opts={"allow_out_of_bounds": True}).count(1) == 0))


def test_b24_b27_b28(td: Path) -> None:
    # B24 + M-B14 (slope): exact S0..S4 boundaries 5.0%, 5.2%, 15%, 25%, 30.5%
    rfps, roads = _base_ave0_roads(-10, 0, 0, 40)
    for pct, exp_dir, exp_cond, exp_unav in ((5.0, 1, False, False), (5.2, 0, True, False), (15.0, 0, True, False), (25.0, 0, True, False), (30.5, 0, False, True)):
        p = _make_pair(td, f"b24_{int(pct * 10)}", [_reg("B2", [0, 0, 30, 26])], height_fn=lambda x, z, k=pct / 100.0: round(x * k, 4), footprints=rfps, roads=roads, pg_bounds=[-100, -100, 100, 100])
        r = B.analyze(p, opts=_c_opts({"S": {"B2": [0, 30, 0, 26]}}))["scenarios"]["S"]["regions"]["B2"]
        assert r["capacities"]["C_direct"] == exp_dir, f"B24 {pct}% C_direct mismatch"
        assert (r["areas_m2"]["A_conditional"] > 0) == exp_cond, f"B24 {pct}% A_conditional mismatch"
        assert (r["areas_m2"]["A_unavailable"] > 0) == exp_unav, f"B24 {pct}% A_unavailable mismatch"
        if pct == 5.2:
            # M-B14 slope: relaxing S0 to allow S1 must break the 5.2% rejection check
            _expect_fail("M-B14 relax_slope_s0", lambda pp=p: _check(B.analyze(pp, opts=_c_opts({"S": {"B2": [0, 30, 0, 26]}}, relax_slope_s0=True))["scenarios"]["S"]["regions"]["B2"]["capacities"]["C_direct"] == 0))

    # Closed parcel vertices: single vertex bump on boundary x=24 -> slope > 5% rejects R05 at [0..24, 0..22]
    d_bnd = make_dump(regions=[_reg("B2", [0, 0, 24, 22])], height_fn=lambda x, z: 0.2 if x >= 24 else 0.0, pg_bounds=[-100, -100, 100, 100])
    m_bnd = B.build_masks(d_bnd, "S", "B2", [0, 0, 24, 22])
    assert B.geom_valid(m_bnd, "R05", 0).count(1) == 0

    # B27: geom_valid built once and cached
    assert B.geom_valid(m_bnd, "R05", 0) is B.geom_valid(m_bnd, "R05", 0)
    assert m_bnd.geom_valid_builds[("R05", 0)] == 1

    # B28: C_conditional == "PENDING_T016D", conditional candidates never mixed into C_direct or C_conditional
    pair28 = _make_pair(td, "b28", [_reg("B2", [0, 0, 40, 30])], height_fn=lambda x, z: round(x * 0.08, 4) if x >= 28 else 0.0, pg_bounds=[-100, -100, 100, 100])
    od28 = td / "b28_out"
    inv28 = B.analyze(pair28, out_dir=od28, opts=_c_opts({"S": {"B2": [0, 40, 0, 30]}}))
    r28 = inv28["scenarios"]["S"]["regions"]["B2"]
    assert r28["capacities"]["C_conditional"] == "PENDING_T016D"
    assert inv28["scenarios"]["S"]["totals"]["C_conditional"] == "PENDING_T016D"
    assert r28["capacities"]["C_direct"] == 0 and r28["capacities"]["C_preliminary"] == 1
    assert r28["conditional_candidates_summary"]["INTERNAL_STREET_REQUIRED_parcels"] == 1
    assert r28["conditional_candidates_summary"]["FOUNDATION_REQUIRED_cells_m2"] > 0
    assert "PENDING_T016D" in (od28 / "capacity_report.md").read_text(encoding="utf-8")


def test_b25_e14_access_and_layers(td: Path) -> None:
    parcel = [0.0, 0.0, 24.0, 22.0]
    # Exact axis-aligned gaps: 0, 1, 2 PASS; 2.001 FAIL (+ M-B14 gap)
    for gap, ok in ((0.0, True), (1.0, True), (2.0, True), (2.001, False)):
        res = B.evaluate_access(parcel, [_cor("R1", [4.0, -8.0 - gap, 16.0, -gap])])
        assert res["ok"] is ok, f"B25 gap {gap} expected {ok}, got {res}"
    _expect_fail("M-B14 access_max_gap_m", lambda: _check(B.evaluate_access(parcel, [_cor("R1", [4.0, -10.001, 16.0, -2.001])], opts={"access_max_gap_m": 2.5})["ok"] is False))

    # Exact contact lengths: 8.0 PASS; 7.999 FAIL (+ extra mutant access_min_contact_m=7.99)
    assert B.evaluate_access(parcel, [_cor("R8", [5.0, -10.0, 13.0, -2.0])])["ok"] is True
    assert B.evaluate_access(parcel, [_cor("R7999", [5.0, -10.0, 12.999, -2.0])])["ok"] is False
    _expect_fail("EXTRA access_min_contact_m", lambda: _check(B.evaluate_access(parcel, [_cor("R7999", [5.0, -10.0, 12.999, -2.0])], opts={"access_min_contact_m": 7.99})["ok"] is False))

    # Disjoint runs (4.5 + 4.5), multi-side (5 south + 5 east), corner-only
    assert B.evaluate_access(parcel, [_cor("D1", [0.0, -10.0, 4.5, -2.0]), _cor("D2", [10.0, -10.0, 14.5, -2.0])])["ok"] is False
    assert B.evaluate_access(parcel, [_cor("MS1", [2.0, -10.0, 7.0, -2.0]), _cor("MS2", [26.0, 2.0, 34.0, 7.0])])["ok"] is False
    assert B.evaluate_access(parcel, [_cor("CRN", [25.0, -9.0, 33.0, -1.0])])["ok"] is False

    # Roundabout, overlap, unverified
    rbt = B.evaluate_access(parcel, [_cor("RBT_1", [2.0, -9.0, 20.0, -1.0], is_rbt=True)])
    assert not rbt["ok"] and "ROUNDABOUT_NOT_USABLE" in rbt["reasons"]
    ovl = B.evaluate_access(parcel, [_cor("OVL", [2.0, -2.0, 20.0, 2.0])])
    assert not ovl["ok"] and "CORRIDOR_OVERLAP" in ovl["reasons"]
    unv = B.evaluate_access(parcel, [_cor("UNV", [2.0, -9.0, 20.0, -1.0], conn="UNVERIFIED")])
    assert not unv["ok"] and "ROAD_UNVERIFIED" in unv["reasons"]

    # Rotated quad (<= 0.25 m rounded down, never overestimates):
    # Top edge (9.0,-1.6)..(14.7,-1.8) has true Euclidean <=2m contact span ~7.77 m (< 8.0 m) -> must FAIL
    rot_short = [[9.0, -1.6], [14.7, -1.8], [14.5, -5.8], [8.8, -5.6]]
    rot_long = [[4.0, -1.0], [18.0, -1.5], [17.8, -6.5], [3.8, -6.0]]
    rs_res = B.evaluate_access(parcel, [_cor("RS", [0, 0, 1, 1], poly=rot_short)])
    assert rs_res["ok"] is False and rs_res["contact_m"] <= 7.80
    assert B.evaluate_access(parcel, [_cor("RL", [0, 0, 1, 1], poly=rot_long)])["ok"] is True

    # E1.4: Two-layer separation + extra mutant bake_access_into_geom_valid
    d_sep = make_dump(regions=[_reg("B2", [0, 0, 40, 40])], pg_bounds=[-100, -100, 100, 100])
    m_sep = B.build_masks(d_sep, "S", "B2", [0, 0, 40, 40])
    vm_far = B.geom_valid(m_sep, "R05", 0)
    assert vm_far.count(1) > 0, "E1.4: parcel far from all roads must stay in geom_valid"
    far_cor = [_cor("FAR", [200.0, -10.0, 240.0, 0.0])]
    _expect_fail("EXTRA bake_access_into_geom_valid", lambda: _check(B.geom_valid(m_sep, "R05", 0, opts={"bake_access_into_geom_valid": far_cor}).count(1) > 0))

    # Replacing corridors preserves Layer 1; new non-existing corridor passes Layer 2 (existing_only=False) but NOT C_direct
    new_cor = [_cor("NEW_RD", [0.0, -9.0, 40.0, -1.0], existing=False)]
    acc_new = B.evaluate_access([0.0, 0.0, 24.0, 22.0], new_cor)
    assert acc_new["ok"] is True and acc_new["existing_only"] is False
    assert B.place_layout({"R05": {0: vm_far}}, lambda box: B.evaluate_access(box, new_cor), "B2")["count"] == 0
    assert B.geom_valid(m_sep, "R05", 0) == vm_far
    assert not B.evaluate_access([0.0, 0.0, 24.0, 22.0], [_cor("NEW_OVL", [5.0, 5.0, 15.0, 15.0], existing=False)])["ok"]


def test_b29_outputs(td: Path) -> None:
    rfps, roads = _base_ave0_roads(-10, 0, 0, 60)
    fps = rfps + [_fp("SA_29", "SITE_A", [40, 0, 60, 20], prot=True, prec="EXACT_OUTLINE")]
    pair = _make_pair(td, "b29", [_reg("B2", [0, 0, 60, 40])], footprints=fps, roads=roads, height_fn=lambda x, z: round(x * 0.08, 4) if z >= 26 else 0.0, pg_bounds=[-100, -100, 100, 100])
    od = td / "b29_out"
    inv = B.analyze(pair, out_dir=od, opts=_c_opts({"S": {"B2": [0, 60, 0, 40]}}))
    cand = json.loads((od / "parcel_candidates.json").read_text(encoding="utf-8"))
    rep = (od / "capacity_report.md").read_text(encoding="utf-8")

    assert inv["analyzer_version"] == "we01b-1.0" and inv["handoff_schema_version"] == 1 and inv["polygon_revision"] == 2
    assert cand["compatibility_key"] == inv["compatibility_key"]
    r = inv["scenarios"]["S"]["regions"]["B2"]
    a = r["areas_m2"]
    assert a["conservation_error_m2"] <= 1.0
    assert abs((a["A_direct"] + a["A_conditional"] + a["A_protected"] + a["A_unavailable"] + a["A_unknown"]) - a["A_gross"]) <= 1.0
    assert abs(a["A_eligible"] - (a["A_direct"] + a["A_conditional"])) <= 1e-6
    assert a["A_protected"] == 400.0 and a["A_eligible"] + a["A_protected"] <= a["A_gross"] + 1e-6
    assert r["direct_parcels"] == cand["scenarios"]["S"]["B2"]["direct_parcels"]
    for tok in (BASE_SHA, "we01b-1.0", "PENDING_T016D", "C_unknown", "PROXY", inv["presets"]["PHONE_LOW"]["static_fingerprint"], inv["presets"]["DESKTOP_HIGH"]["static_fingerprint"]):
        assert tok in rep, f"B29 report missing {tok!r}"


def test_b30_e25_road_graph(td: Path) -> None:
    # GROUND graph: AVE_0 intersects S_INT, endpoint S_END within half_w(4)+1=5 m, S_FAR at 5.2 m fails,
    # S_ELEV (ELEVATED) & S_RAMP & S_UNK cross AVE_0 planarly (rejected), S_DUP duplicates S_INT (deduped to S_DUP)
    segs = [
        _seg("AVE_0", [[0, 0, 0], [100, 0, 0]], width=8.0, fp_ids=["FP_AVE"]),
        _seg("S_INT", [[50, 0, -20], [50, 0, 20]], width=8.0, fp_ids=["FP_INT"]),
        _seg("S_DUP", [[50, 0, 20], [50, 0, -20]], width=8.0, fp_ids=["FP_DUP"]),
        _seg("S_END", [[105.0, 0, 0], [140, 0, 0]], width=8.0, fp_ids=["FP_END"]),
        _seg("S_FAR", [[105.2, 0, 20], [140, 0, 20]], width=8.0, fp_ids=["FP_FAR"]),
        _seg("S_ELEV", [[20, 6, -20], [20, 6, 20]], width=8.0, elev="ELEVATED", fp_ids=["FP_EL"]),
        _seg("S_RAMP", [[30, 2, -20], [30, 2, 20]], width=8.0, elev="RAMP", fp_ids=["FP_RM"]),
        _seg("S_UNK", [[40, 0, -20], [40, 0, 20]], width=8.0, elev="UNKNOWN", fp_ids=["FP_UN"]),
        _seg("S_ISO", [[300, 0, 300], [340, 0, 300]], width=8.0, fp_ids=["FP_IS"]),
    ]
    fps = [
        _road_fp("FP_AVE", [0, -4, 100, 4]), _road_fp("FP_INT", [46, -20, 54, 20]), _road_fp("FP_DUP", [46, -20, 54, 20]),
        _road_fp("FP_END", [105, -4, 140, 4]), _road_fp("FP_FAR", [105.2, 16, 140, 24]), _road_fp("FP_EL", [16, -20, 24, 20]),
        _road_fp("FP_RM", [26, -20, 34, 20]), _road_fp("FP_UN", [36, -20, 44, 20]), _road_fp("FP_IS", [300, 296, 340, 304]),
    ]
    d = make_dump(regions=[_reg("B2", [0, 0, 40, 40])], footprints=fps, roads={"nodes": [], "segments": segs, "completeness": "COMPLETE"}, pg_bounds=[-100, -100, 400, 400])

    def _assert_b30(o: dict | None = None) -> None:
        g = B.build_road_graph(d, opts=o)
        assert g["raw_segment_count"] == 9 and g["dedup_node_count"] == 8
        assert g["alias_map"]["S_INT"] == "S_DUP" and g["duplicates"] == {"S_DUP": ["S_DUP", "S_INT"]}
        assert g["main_component"] == ["AVE_0", "S_DUP", "S_END"]
        for bad_id in ("S_FAR", "S_ELEV", "S_RAMP", "S_UNK", "S_ISO"):
            assert g["connectivity"][bad_id] == "UNVERIFIED", f"B30 {bad_id} should be UNVERIFIED"

    _assert_b30()
    _expect_fail("M-B16 allow_elevated_planar_connect", lambda: _assert_b30({"allow_elevated_planar_connect": True}))
    _expect_fail("EXTRA keep_duplicate_segments", lambda: _assert_b30({"keep_duplicate_segments": True}))

    # Window-cutoff (missing AVE_0 bridge) -> UNVERIFIED and 0 C_direct; duplicate corridors do not inflate capacity
    rfps_cut = [_road_fp("RD_ISO_1", [0, -10, 60, 0]), _road_fp("RD_ISO_2", [0, -10, 60, 0])]
    segs_cut = [_seg("ISO_A", [[0, 0, -5], [60, 0, -5]], width=10, fp_ids=["RD_ISO_1"]), _seg("ISO_B", [[0, 0, -5], [60, 0, -5]], width=10, fp_ids=["RD_ISO_2"])]
    pair_cut = _make_pair(td, "b30_cut", [_reg("B2", [0, 0, 60, 30])], footprints=rfps_cut, roads={"nodes": [], "segments": segs_cut, "completeness": "COMPLETE"}, pg_bounds=[-100, -100, 100, 100])
    r_cut = B.analyze(pair_cut, opts=_c_opts({"S": {"B2": [0, 60, 0, 30]}}))["scenarios"]["S"]["regions"]["B2"]
    assert r_cut["capacities"]["C_direct"] == 0 and r_cut["capacities"]["C_unknown"] >= 1


def test_real_samples_and_b22_csv(td: Path) -> None:
    # 1. sample_roads_phone_low.json road graph
    sr = json.loads((FX / "sample_roads_phone_low.json").read_text(encoding="utf-8"))
    g_sr = B.build_road_graph(sr)
    assert g_sr["raw_segment_count"] == 11 and g_sr["dedup_node_count"] == 10
    assert g_sr["dedup_main_component_count"] == 9 and "AVE_0" in g_sr["main_component"]
    assert g_sr["duplicates"] == {"HILL_ROAD": ["HILL_ROAD", "TRD_0"]} and g_sr["alias_map"]["TRD_0"] == "HILL_ROAD"

    # Load WE-01A common L0 CSV once
    csv_cells: dict[str, list[tuple[int, int]]] = {"B1": [], "B2": [], "B3": []}
    with (FX / "we01a_common_l0_cells.csv").open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            csv_cells[row["region_id"]].append((int(round(float(row["x_center"]) - 2.5)), int(round(float(row["z_center"]) - 2.5))))

    # 2. Both real sample pairs end-to-end + B22 CSV invariant
    checked_csv = 0
    for tag, lo_n, hi_n in (("sample", "sample_phone_low.json", "sample_desktop_high.json"), ("b3mid", "sample_b3mid_phone_low.json", "sample_b3mid_desktop_high.json")):
        lo_p, hi_p = FX / lo_n, FX / hi_n
        od = td / f"real_{tag}"
        inv = B.analyze([lo_p, hi_p], out_dir=od)
        assert inv["analyzer_version"] == "we01b-1.0" and inv["polygon_revision"] == 2
        for sid, sc in inv["scenarios"].items():
            assert sc["totals"]["C_conditional"] == "PENDING_T016D"
            for rid, r in sc["regions"].items():
                c, a = r["capacities"], r["areas_m2"]
                assert c["C_conditional"] == "PENDING_T016D"
                assert c["C_direct"] == 0  # AVE_0 not inside these small sample windows -> conservative UNVERIFIED
                assert c["C_upper"] >= c["C_direct"] and c["C_unknown"] >= 0
                assert a["conservation_error_m2"] <= 1.0
        assert (od / "capacity_inventory.json").exists() and (od / "parcel_candidates.json").exists() and (od / "capacity_report.md").exists()

        # B22 CSV check on every CSV cell inside this sample's survey rectangle
        d_lo, d_hi = json.loads(lo_p.read_text(encoding="utf-8")), json.loads(hi_p.read_text(encoding="utf-8"))
        for reg in d_lo["regions"]:
            rid = reg["id"]
            sb = [int(v) for v in W.poly_bounds(reg["survey_polygon"])]
            m_lo, m_hi = B.build_masks(d_lo, "CSV", rid, sb), B.build_masks(d_hi, "CSV", rid, sb)
            for x0, z0 in csv_cells.get(rid, []):
                if sb[0] <= x0 and x0 + 5 <= sb[2] and sb[1] <= z0 and z0 + 5 <= sb[3]:
                    checked_csv += 1
                    assert m_lo.rect_blocked(x0, z0, x0 + 5, z0 + 5) == 0 and m_hi.rect_blocked(x0, z0, x0 + 5, z0 + 5) == 0, f"B22 CSV fail {tag}/{rid} at {(x0, z0)}"
    assert checked_csv >= 3000, f"Expected >= 3000 CSV cells verified, got {checked_csv}"


def main() -> int:
    t0 = time.monotonic()
    tests = [
        ("B01-B06 + M-B02/M-B03", test_b01_to_b06),
        ("B07 + M-B11", test_b07_linkage),
        ("B08/B09/B11 + M-B01/M-B05/M-B06/M-B09", test_b08_b09_b11),
        ("B12/B17/B20 + M-B08/M-B10/EXTRA-AABB", test_b12_b17_b20),
        ("B21/B22-syn/B26 + M-B13", test_b21_b22_b26),
        ("B23 + M-B15/EXTRA-V1", test_b23_scenarios),
        ("B24/B27/B28 + M-B14-slope", test_b24_b27_b28),
        ("B25/E1.4 + M-B14-gap/EXTRA-7999/EXTRA-bake", test_b25_e14_access_and_layers),
        ("B29 outputs & conservation", test_b29_outputs),
        ("B30/E2.5 + M-B16/EXTRA-dup", test_b30_e25_road_graph),
        ("REAL-SAMPLES + sample_roads + B22-CSV", test_real_samples_and_b22_csv),
    ]
    with tempfile.TemporaryDirectory() as tmp:
        td = Path(tmp)
        for label, fn in tests:
            ts = time.monotonic()
            fn(td)
            print(f"PASS [{label}] ({time.monotonic() - ts:.2f}s)")
    elapsed = time.monotonic() - t0
    assert elapsed <= 10.0, f"B18 runtime exceeded 10.0s: {elapsed:.2f}s"
    print(f"RESULT: PASS (WE-01B all 26 test IDs + 18 mutants RED + both real-sample pairs + sample_roads + B22 CSV in {elapsed:.2f}s <= 10.0s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
