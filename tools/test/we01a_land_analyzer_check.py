#!/usr/bin/env python3
"""WE-01A (T-016A): Fast unit, synthetic-oracle, sample-dump, and mutation tests (A01, A03-A13, A15-A18, M-A01..M-A09)."""
from __future__ import annotations
import copy, hashlib, importlib.util, json, sys, tempfile, time
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/test"))
import we01a_land_analyzer as W

BASE_SHA = "84319439243b51aa8d119e33eb62a0637feea887"
SAMPLE_LO = ROOT / "tools/fixtures/we01/sample_phone_low.json"
SAMPLE_HI = ROOT / "tools/fixtures/we01/sample_desktop_high.json"
FP_REF = ROOT / "tools/fixtures/we01/fingerprint_reference.py"


def _rect(x0, z0, x1, z1):
    return [[x0, z0], [x1, z0], [x1, z1], [x0, z1]]


def _fp(fid, cat, b, sg="TEST", gt="AABB", prec="CONSERVATIVE_AABB", vis=True, phys=True, prot=False, ver="RUNTIME_VERIFIED", poly=None):
    return {"id": fid, "category": cat, "source_group": sg, "geometry_type": gt, "geometry_precision": prec,
            "polygon": poly if poly is not None else _rect(*b), "bounds": list(b), "y_min": 0.0, "y_max": 5.0,
            "visual": vis, "physical": phys, "protected": prot, "source_ref": sg, "verification": ver}


def make_dump(preset="PHONE_LOW", regions=None, height_fn=None, footprints=None, water=None, beach=None,
              terrain_regions=None, roads=None, completeness=None, issues=None, pg_bounds=None, pg_ver="RUNTIME_VERIFIED",
              base_sha=BASE_SHA, world_height_fn=None):
    regions = regions or [{"id": "R1", "name": "Synthetic Zone", "initial_polygon": _rect(0, 0, 20, 10), "survey_polygon": _rect(0, 0, 20, 10), "buffer_m": 0, "source_ref": "syn"}]
    hfn = height_fn or (lambda x, z: 0.0)
    wfn = world_height_fn or (lambda x, z: 0.0)
    grids = [{"id": "WORLD_20M", "region_id": "WORLD", "origin_x": -100, "origin_z": -100, "step_m": 20, "nx": 11, "nz": 11,
              "heights": [wfn(-100 + ix * 20, -100 + iz * 20) for iz in range(11) for ix in range(11)],
              "source": "runtime_terrainHeight", "sample_method": "DIRECT_RUNTIME"}]
    for reg in regions:
        x0, z0, x1, z1 = W.poly_bounds(reg["survey_polygon"])
        ox, oz = int(x0) - 1, int(z0) - 1
        nx, nz = int(x1) - ox + 2, int(z1) - oz + 2
        grids.append({"id": f"{reg['id']}_1M", "region_id": reg["id"], "origin_x": ox, "origin_z": oz, "step_m": 1, "nx": nx, "nz": nz,
                      "heights": [hfn(ox + ix, oz + iz) for iz in range(nz) for ix in range(nx)],
                      "source": "runtime_terrainHeight", "sample_method": "DIRECT_RUNTIME"})
    comp = {"world_bounds": "PARTIAL", "terrain_heights": "COMPLETE", "physical_ground": "COMPLETE", "terrain_regions": "COMPLETE",
            "visual_occupancy": "COMPLETE", "physical_occupancy": "COMPLETE", "trees": "COMPLETE", "water_and_beach": "COMPLETE",
            "protected_areas": "COMPLETE", "roads": "COMPLETE", "traffic_routes": "UNKNOWN"}
    if completeness:
        comp.update(completeness)
    d = {
        "schema_version": 1,
        "metadata": {
            "base_sha": base_sha, "game_release": "vh-test", "preset": preset, "initialization_complete": True,
            "showcase_visible": True, "night": False, "extraction_version": "syn-1", "generated_at": "2026-11-27T00:00:00Z",
            "coordinate_unit": "m", "generation_settings": {"sample": True}, "static_fingerprint": "",
            "source_counts": {"WORLD.buildings": 1, "WORLD.cityInfill": 0, "WORLD.suburbHouses": 0, "TREES": 1, "TREE_COLLIDERS": 1},
            "source_fingerprints": {}, "seed": None,
        },
        "world": {
            "ground_bounds": [-100, -100, 100, 100], "playable_bounds": None, "map_ui_bounds": None,
            "physical_ground": {"shape": "BOX", "half_extents": [100, 0.5, 100], "position": [0, -0.5, 0], "top_y": 0,
                                "bounds": list(pg_bounds or [-100, -100, 100, 100]), "verification": pg_ver, "source_ref": "syn"},
            "terrain_regions": terrain_regions or [], "water_regions": water or [], "beach_regions": beach or [],
            "boundary_obstacles": [], "source_refs": ["syn"],
        },
        "regions": regions, "height_grids": grids, "footprints": footprints or [],
        "roads": roads or {"nodes": [], "segments": [], "completeness": "COMPLETE"},
        "completeness": comp, "issues": issues or [],
    }
    d["metadata"]["static_fingerprint"] = W.compute_static_fingerprint(d)
    return d


def _write_dump(td: Path, name: str, d: dict) -> Path:
    p = td / name
    p.write_text(json.dumps(d), encoding="utf-8")
    return p


def _expect_fail(label: str, fn):
    try:
        fn()
    except (AssertionError, W.ValidationError):
        return
    raise AssertionError(f"Expected FAILURE but stayed GREEN: {label}")


def test_a01_schema_validation(td: Path):
    base = make_dump()
    assert W.validate_dump(base)["schema_version"] == 1
    bad_cases = [
        ("schema_version=2", lambda d: d.__setitem__("schema_version", 2)),
        ("bad_base_sha", lambda d: d["metadata"].__setitem__("base_sha", "1234")),
        ("bad_preset", lambda d: d["metadata"].__setitem__("preset", "ULTRA")),
        ("nan_height", lambda d: d["height_grids"][1]["heights"].__setitem__(0, float("nan"))),
        ("dup_fp_id", lambda d: d["footprints"].extend([_fp("F1", "TREE", [0, 0, 2, 2]), _fp("F1", "TREE", [3, 0, 5, 2])])),
        ("self_intersect_poly", lambda d: d["world"]["water_regions"].append([[0, 0], [5, 5], [5, 0], [0, 5]])),
        ("missing_field", lambda d: d.pop("completeness")),
        ("bad_road_ref", lambda d: d["roads"]["segments"].append({"id": "S1", "start_node_id": "NOPE", "end_node_id": None, "centerline": [[0, 0, 0], [5, 0, 0]], "carriageway_width_m": 7, "sidewalk_left_m": None, "sidewalk_right_m": None, "corridor_footprint_ids": [], "elevation_type": "GROUND", "traffic_route_ids": [], "source_ref": "r", "verification": "RUNTIME_VERIFIED"})),
        ("bad_precision", lambda d: d["footprints"].append(_fp("F1", "TREE", [0, 0, 2, 2], prec="GUESSED"))),
        ("bad_height_len", lambda d: d["height_grids"][1]["heights"].pop()),
        ("bad_grid_step", lambda d: d["height_grids"][1].__setitem__("step_m", 2)),
        ("dynamic_source", lambda d: d["footprints"].append(_fp("D1", "COLLIDER", [0, 0, 2, 2], sg="PHYSICS_DYNAMIC"))),
    ]
    for name, mut in bad_cases:
        c = copy.deepcopy(base)
        mut(c)
        if name != "missing_field" and name != "nan_height" and name != "bad_height_len":
            try: c["metadata"]["static_fingerprint"] = W.compute_static_fingerprint(c)
            except Exception: pass
        _expect_fail(f"A01:{name}", lambda cc=c: W.validate_dump(cc))
    # BASE SHA mismatch across two dumps rejected via CLI (non-zero exit)
    p1 = _write_dump(td, "a01_1.json", make_dump(preset="PHONE_LOW", base_sha=BASE_SHA))
    p2 = _write_dump(td, "a01_2.json", make_dump(preset="DESKTOP_HIGH", base_sha="0" * 40))
    assert W.main(["--dump", str(p1), "--dump", str(p2), "--out", str(td / "a01_out")]) != 0
    # Poor land (all water) still exits 0
    poor = _write_dump(td, "a01_poor.json", make_dump(water=[_rect(0, 0, 20, 10)]))
    assert W.main(["--dump", str(poor), "--out", str(td / "a01_poor_out")]) == 0


def _assert_a04_oracle(td: Path, opts=None):
    # 7 cells x 25m2 along X=[0..35], Z=[0..5]: L0, L1(10% slope), L2(bldg), L3(beach), L4(siteA), L5(water), LX(blocker)
    reg = [{"id": "Z1", "name": "AllClasses", "initial_polygon": _rect(0, 0, 35, 5), "survey_polygon": _rect(0, 0, 35, 5), "buffer_m": 0, "source_ref": "syn"}]
    hfn = lambda x, z: (x - 5.0) * 0.10 if 6 <= x <= 9 else (0.5 if x == 10 else 0.0)
    fps = [_fp("BLD1", "BUILDING", [11, 1, 14, 4], prec="EXACT_OUTLINE"), _fp("SA1", "SITE_A", [20, 0, 25, 5], prot=True, prec="EXACT_OUTLINE")]
    iss = [{"id": "BLK1", "severity": "BLOCKER", "category": "gap", "affected_region_ids": ["Z1"], "affected_polygon": _rect(30, 0, 35, 5), "message": "gap", "source_ref": "syn"}]
    p = _write_dump(td, "a04.json", make_dump(regions=reg, height_fn=hfn, footprints=fps, water=[_rect(25, 0, 30, 5)], beach=[_rect(15, 0, 20, 5)], issues=iss))
    inv = W.analyze_dumps([p], opts=opts)["inventory"]
    got = inv["regions"][0]["common_initial_class_areas_m2"]
    assert got == {"L0": 25.0, "L1": 25.0, "L2": 25.0, "L3": 25.0, "L4": 25.0, "L5": 25.0, "LX": 25.0}, f"A04 mismatch: {got}"


def _assert_a05_occupancy(td: Path, opts=None):
    reg = [{"id": "Z5", "name": "Occ", "initial_polygon": _rect(0, 0, 20, 5), "survey_polygon": _rect(0, 0, 20, 5), "buffer_m": 0, "source_ref": "syn"}]
    fps = [_fp("VIS1", "OTHER", [1, 1, 4, 4], sg="SCENE_BOX3", vis=True, phys=False),
           _fp("PHY1", "COLLIDER", [6, 1, 9, 4], sg="PHYSICS_STATIC", vis=False, phys=True),
           _fp("TR1", "TREE", [11, 1, 14, 4], sg="TREE_COLLIDERS", vis=False, phys=True)]
    p = _write_dump(td, "a05.json", make_dump(regions=reg, footprints=fps))
    ca = W.analyze_dumps([p], opts=opts)["inventory"]["regions"][0]["common_initial_class_areas_m2"]
    assert ca["L5"] == 75.0 and ca["L0"] == 25.0, f"A05 mismatch: {ca}"


def _assert_a06_site_a(td: Path, opts=None):
    reg = [{"id": "Z6", "name": "SiteA", "initial_polygon": _rect(0, 0, 10, 5), "survey_polygon": _rect(0, 0, 10, 5), "buffer_m": 0, "source_ref": "syn"}]
    fps = [_fp("SA", "SITE_A", [0, 0, 5, 5], prot=True, prec="EXACT_OUTLINE"), _fp("B", "BUILDING", [1, 1, 4, 4])]
    p = _write_dump(td, "a06.json", make_dump(regions=reg, footprints=fps))
    ca = W.analyze_dumps([p], opts=opts)["inventory"]["regions"][0]["common_initial_class_areas_m2"]
    assert ca["L4"] == 25.0 and ca["L0"] == 25.0 and ca["L2"] == 0.0, f"A06 mismatch: {ca}"


def _assert_a07_water(td: Path, opts=None):
    reg = [{"id": "Z7", "name": "Water", "initial_polygon": _rect(0, 0, 10, 5), "survey_polygon": _rect(0, 0, 10, 5), "buffer_m": 0, "source_ref": "syn"}]
    p = _write_dump(td, "a07.json", make_dump(regions=reg, water=[_rect(0, 0, 5, 5)], beach=[_rect(0, 0, 10, 5)]))
    ca = W.analyze_dumps([p], opts=opts)["inventory"]["regions"][0]["common_initial_class_areas_m2"]
    assert ca["L5"] == 25.0 and ca["L3"] == 25.0 and ca["L0"] == 0.0, f"A07 mismatch: {ca}"


def _assert_a08_roads(td: Path, opts=None):
    reg = [{"id": "Z8", "name": "Road", "initial_polygon": _rect(0, 0, 15, 5), "survey_polygon": _rect(0, 0, 15, 5), "buffer_m": 0, "source_ref": "syn"}]
    fps = [_fp("RD1", "ROAD", [0, 0, 5, 5], prec="EXACT_OUTLINE"), _fp("SW1", "SIDEWALK", [5, 0, 10, 5])]
    p = _write_dump(td, "a08.json", make_dump(regions=reg, footprints=fps))
    ca = W.analyze_dumps([p], opts=opts)["inventory"]["regions"][0]["common_initial_class_areas_m2"]
    assert ca["L5"] == 50.0 and ca["L0"] == 25.0, f"A08 mismatch: {ca}"


def _assert_a09_a10_conservation_and_overlaps(td: Path, opts=None):
    # Two overlapping regions: [0,0,20,10]=200m2 and [10,0,30,10]=200m2 -> exact union = 300m2; plus 5 overlapping obstacles on cell [0..5,0..5]
    regs = [{"id": "OV1", "name": "O1", "initial_polygon": _rect(0, 0, 20, 10), "survey_polygon": _rect(0, 0, 20, 10), "buffer_m": 0, "source_ref": "s"},
            {"id": "OV2", "name": "O2", "initial_polygon": _rect(10, 0, 30, 10), "survey_polygon": _rect(10, 0, 30, 10), "buffer_m": 0, "source_ref": "s"}]
    fps = [_fp("B1", "BUILDING", [1, 1, 4, 4]), _fp("T1", "TREE", [1, 1, 4, 4]), _fp("C1", "COLLIDER", [1, 1, 4, 4])]
    p = _write_dump(td, "a09.json", make_dump(regions=regs, footprints=fps, water=[_rect(0, 0, 5, 5)], beach=[_rect(0, 0, 5, 5)]))
    inv = W.analyze_dumps([p], opts=opts)["inventory"]
    us = inv["union_summary"]["common"]
    assert abs(us["initial_union_area_m2"] - 300.0) <= 1e-3, f"Union area != 300: {us}"
    assert abs(sum(us["initial_class_areas_m2"].values()) - 300.0) <= 1.0, f"A09/A10 conservation failed: {us}"
    assert us["initial_class_areas_m2"]["L5"] == 25.0 and us["initial_class_areas_m2"]["L0"] == 275.0, f"A10 overlap double-count: {us}"
    # Non-grid-aligned trapezoid: vertices (1,1),(16,1),(11,11),(1,11) -> exact area = (15+10)/2 * 10 = 125.0 m2
    trap = [[1, 1], [16, 1], [11, 11], [1, 11]]
    pt = _write_dump(td, "a09_trap.json", make_dump(regions=[{"id": "TR", "name": "Trap", "initial_polygon": trap, "survey_polygon": trap, "buffer_m": 0, "source_ref": "s"}]))
    r0 = W.analyze_dumps([pt], opts=opts)["inventory"]["regions"][0]
    assert abs(r0["initial_polygon_area_m2"] - 125.0) < 1e-6 and r0["common_conservation_error_m2"]["initial"] <= 1.0


def _assert_a11_unknown(td: Path, opts=None):
    # Case 1: missing (None) height; Case 2: PARTIAL required completeness; Case 3: UNKNOWN physical_ground
    reg = [{"id": "ZU", "name": "Unk", "initial_polygon": _rect(0, 0, 10, 5), "survey_polygon": _rect(0, 0, 10, 5), "buffer_m": 0, "source_ref": "s"}]
    p1 = _write_dump(td, "a11_h.json", make_dump(regions=reg, height_fn=lambda x, z: None if x < 5 else 0.0))
    c1 = W.analyze_dumps([p1], opts=opts)["inventory"]["regions"][0]["common_initial_class_areas_m2"]
    assert c1["LX"] == 25.0 and c1["L0"] == 25.0, f"A11 missing height: {c1}"
    p2 = _write_dump(td, "a11_c.json", make_dump(regions=reg, completeness={"visual_occupancy": "PARTIAL"}))
    c2 = W.analyze_dumps([p2], opts=opts)["inventory"]["regions"][0]["common_initial_class_areas_m2"]
    assert c2["LX"] == 50.0 and c2["L0"] == 0.0, f"A11 partial comp: {c2}"
    p3 = _write_dump(td, "a11_pg.json", make_dump(regions=reg, pg_ver="UNKNOWN"))
    c3 = W.analyze_dumps([p3], opts=opts)["inventory"]["regions"][0]["common_initial_class_areas_m2"]
    assert c3["LX"] == 50.0 and c3["L0"] == 0.0, f"A11 unknown pg: {c3}"


def _assert_a12_preset_diff(td: Path, opts=None):
    reg = [{"id": "ZP", "name": "Preset", "initial_polygon": _rect(0, 0, 20, 5), "survey_polygon": _rect(0, 0, 20, 5), "buffer_m": 0, "source_ref": "s"}]
    p_lo = _write_dump(td, "a12_lo.json", make_dump(preset="PHONE_LOW", regions=reg, footprints=[_fp("LO1", "TREE", [1, 1, 4, 4])]))
    p_hi = _write_dump(td, "a12_hi.json", make_dump(preset="DESKTOP_HIGH", regions=reg, footprints=[_fp("HI1", "TREE", [6, 1, 9, 4])]))
    res = W.analyze_dumps([p_lo, p_hi], opts=opts)
    r = res["inventory"]["regions"][0]
    assert r["per_preset"]["PHONE_LOW"]["initial_class_areas_m2"]["L0"] == 75.0
    assert r["per_preset"]["DESKTOP_HIGH"]["initial_class_areas_m2"]["L0"] == 75.0
    assert r["common_initial_class_areas_m2"]["L0"] == 50.0 and r["common_initial_class_areas_m2"]["L5"] == 50.0
    assert res["preset_diff"]["footprint_diff"]["only_in_DESKTOP_HIGH_count"] == 1


def _assert_a13_height_provenance(opts=None):
    d = make_dump(height_fn=lambda x, z: float(x), world_height_fn=lambda x, z: 10.0)
    gs = d["height_grids"]
    h1, p1, s1 = W.sample_height(gs, "R1", 4.0, 3.0, opts)
    h2, p2, s2 = W.sample_height(gs, "R1", 4.5, 3.5, opts)
    h3, p3, s3 = W.sample_height(gs, "R1", -80.0, -80.0, opts)
    h4, p4, s4 = W.sample_height(gs, "R1", -70.0, -70.0, opts)
    h5, p5, _ = W.sample_height(gs, "R1", 500.0, 500.0, opts)
    assert (h1, p1, s1) == (4.0, "DIRECT_RUNTIME_1M", 1)
    assert abs(h2 - 4.5) < 1e-9 and p2 == "INTERPOLATED_1M" and s2 == 1
    assert (h3, p3, s3) == (10.0, "DIRECT_RUNTIME_20M", 20)
    assert abs(h4 - 10.0) < 1e-9 and p4 == "INTERPOLATED_20M" and s4 == 20
    assert (h5, p5) == (None, "UNKNOWN")


def test_a03_a15_a16_a17_a18(td: Path):
    # A03 Determinism (3 runs -> identical SHA-256 on all 5 files) + A15 SVG completeness + A16 Footprint precision
    reg = [{"id": "ZD", "name": "Det", "initial_polygon": _rect(0, 0, 20, 10), "survey_polygon": _rect(0, 0, 20, 10), "buffer_m": 0, "source_ref": "s"}]
    fps = [_fp("EX1", "BUILDING", [1, 1, 4, 4], gt="POLYGON", prec="EXACT_OUTLINE"),
           _fp("AB1", "OTHER", [6, 1, 9, 4], sg="SCENE_BOX3", gt="AABB", prec="CONSERVATIVE_AABB"),
           _fp("SA1", "SITE_A", [15, 0, 20, 5], gt="POLYGON", prec="EXACT_OUTLINE", prot=True)]
    p_in = _write_dump(td, "det.json", make_dump(regions=reg, footprints=fps))
    hashes = []
    for run in range(3):
        od = td / f"run_{run}"
        assert W.main(["--dump", str(p_in), "--out", str(od)]) == 0
        files = sorted(od.iterdir())
        assert [f.name for f in files] == ["land_inventory.json", "land_report.md", "land_survey.svg", "preset_diff.json", "terrain_survey.csv"]
        hashes.append({f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in files})
    assert hashes[0] == hashes[1] == hashes[2], "A03 determinism failed"
    # A15 SVG check
    svg_txt = (td / "run_0/land_survey.svg").read_text(encoding="utf-8")
    root_el = ET.fromstring(svg_txt)
    assert root_el.tag.endswith("svg")
    for tok in (BASE_SHA, "scale", "Legend", "Site A", "LX / UNKNOWN", "Existing Road", "AUDIT DATA", "X=0m", "Z=0"):
        assert tok in svg_txt, f"A15 SVG missing {tok!r}"
    # A16 Precision check
    inv = json.loads((td / "run_0/land_inventory.json").read_text(encoding="utf-8"))
    assert inv["footprint_summary"]["PHONE_LOW"]["by_precision"] == {"CONSERVATIVE_AABB": 1, "EXACT_OUTLINE": 2}
    assert inv["regions"][0]["precision_affected_areas_m2"] == {"CONSERVATIVE_AABB": 25.0, "EXACT_OUTLINE": 50.0}
    assert inv["regions"][0]["common_initial_class_areas_m2"]["L0"] == 125.0  # AABB excluded 25m2, never proved free

    # A17 Static fingerprint matches reference on BOTH real sample dumps, ignores non-static fields, rejects tamper
    spec = importlib.util.spec_from_file_location("fp_ref", FP_REF)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    for sp in (SAMPLE_LO, SAMPLE_HI):
        sd = json.loads(sp.read_text(encoding="utf-8"))
        ref_fp = mod.fingerprint(sd)
        got_fp = W.compute_static_fingerprint(sd)
        assert got_fp == ref_fp == sd["metadata"]["static_fingerprint"], f"A17 mismatch on {sp.name}"
    d_mod = make_dump()
    fp0 = d_mod["metadata"]["static_fingerprint"]
    d_mod["metadata"]["generated_at"] = "2099-01-01T00:00:00Z"
    d_mod["metadata"]["seed"] = 999
    d_mod["issues"].append({"id": "I_IGN", "severity": "INFO", "category": "x", "affected_region_ids": [], "affected_polygon": None, "message": "m", "source_ref": "r"})
    assert W.compute_static_fingerprint(d_mod) == fp0, "A17 non-static field changed fingerprint"
    d_bad = copy.deepcopy(d_mod)
    d_bad["height_grids"][1]["heights"][0] = 1.234
    _expect_fail("A17:stale_fp", lambda: W.validate_dump(d_bad))

    # A18 Flat physical ground outside terrain_regions is valid L0 (and distinguishes core/margin/outside)
    reg18 = [{"id": "Z18", "name": "Flat", "initial_polygon": _rect(0, 0, 40, 5), "survey_polygon": _rect(0, 0, 40, 5), "buffer_m": 0, "source_ref": "s"}]
    tr18 = [{"id": "TR1", "polygon": _rect(0, 0, 10, 5), "margin_m": 10, "source_ref": "t", "terrain_support_status": "VERIFIED"}]
    p18 = _write_dump(td, "a18.json", make_dump(regions=reg18, terrain_regions=tr18, pg_bounds=[-100, -100, 35, 100]))
    r18 = W.analyze_dumps([p18])["inventory"]["regions"][0]
    assert r18["terrain_zone_areas_m2"] == {"TERRAIN_CORE": 50.0, "TERRAIN_MARGIN": 50.0, "FLAT_PHYSICAL_GROUND": 75.0, "OUTSIDE_PHYSICAL_GROUND": 25.0}
    assert r18["common_initial_class_areas_m2"]["L0"] == 175.0 and r18["common_initial_class_areas_m2"]["L3"] == 25.0


def test_mutations_ma01_to_ma09(td: Path):
    _expect_fail("M-A01: ignore buildings", lambda: _assert_a04_oracle(td, {"ignore_buildings": True}))
    _expect_fail("M-A02: ignore water", lambda: _assert_a07_water(td, {"ignore_water": True}))
    _expect_fail("M-A03: ignore Site A", lambda: _assert_a06_site_a(td, {"ignore_site_a": True}))
    _expect_fail("M-A04: ignore roads", lambda: _assert_a08_roads(td, {"ignore_roads": True}))
    _expect_fail("M-A05: double-count overlaps", lambda: _assert_a09_a10_conservation_and_overlaps(td, {"double_count_overlaps": True, "skip_conservation_assert": True}))
    _expect_fail("M-A06: classify LX as L0", lambda: _assert_a11_unknown(td, {"lx_to_l0": True}))
    _expect_fail("M-A07: PHONE_LOW only, ignore DESKTOP_HIGH", lambda: _assert_a12_preset_diff(td, {"phone_low_only": True}))
    _expect_fail("M-A08: label interpolated as direct", lambda: _assert_a13_height_provenance({"mislabel_interpolated": True}))
    bad_len = make_dump()
    bad_len["height_grids"][1]["heights"].pop()
    bad_len["metadata"]["static_fingerprint"] = W.compute_static_fingerprint(bad_len)
    _expect_fail("A01_bad_len_oracle", lambda: W.validate_dump(bad_len))
    _expect_fail("M-A09: accept wrong height length", lambda: _expect_fail("must_reject_bad_len", lambda: W.validate_dump(bad_len, {"allow_bad_height_len": True})))


def test_real_sample_dumps(td: Path):
    od = td / "real_samples"
    assert W.main(["--dump", str(SAMPLE_LO), "--dump", str(SAMPLE_HI), "--out", str(od)]) == 0
    inv = json.loads((od / "land_inventory.json").read_text(encoding="utf-8"))
    assert inv["mode"] == "CROSS_PRESET_COMMON" and [r["id"] for r in inv["regions"]] == ["B1", "B2", "B3"]
    assert inv["union_summary"]["common"]["conservation_error_m2"]["initial"] <= 1.0
    assert inv["union_summary"]["common"]["conservation_error_m2"]["survey"] <= 1.0
    ET.fromstring((od / "land_survey.svg").read_text(encoding="utf-8"))


def main() -> int:
    t0 = time.monotonic()
    with tempfile.TemporaryDirectory() as tmp:
        td = Path(tmp)
        test_a01_schema_validation(td); print("PASS [A01] schema validation & CLI exit codes")
        _assert_a04_oracle(td); print("PASS [A04] L0-L5/LX classification oracle")
        _assert_a05_occupancy(td); print("PASS [A05] static visual/physical occupancy")
        _assert_a06_site_a(td); print("PASS [A06] Site A protection (L4)")
        _assert_a07_water(td); print("PASS [A07] water protection (L5 > L3, never L0)")
        _assert_a08_roads(td); print("PASS [A08] road & sidewalk protection")
        _assert_a09_a10_conservation_and_overlaps(td); print("PASS [A09/A10] exact area conservation & overlap accounting")
        _assert_a11_unknown(td); print("PASS [A11] missing/partial/unknown -> LX")
        _assert_a12_preset_diff(td); print("PASS [A12] two-preset obstacle union / L0 intersection")
        _assert_a13_height_provenance(); print("PASS [A13] height provenance (direct vs interpolated)")
        test_a03_a15_a16_a17_a18(td); print("PASS [A03/A15/A16/A17/A18] determinism, SVG, precision, C3 fingerprint, flat physical ground")
        test_mutations_ma01_to_ma09(td); print("PASS [M-A01..M-A09] all 9 mutations turned RED")
        test_real_sample_dumps(td); print("PASS [REAL-SAMPLES] sample_phone_low + sample_desktop_high end-to-end")
    print(f"RESULT: PASS (WE-01A A01, A03-A13, A15-A18 + M-A01..M-A09 RED + real samples in {time.monotonic() - t0:.2f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
