#!/usr/bin/env python3
"""WE-01E (T-016E) independent check suite: E01-E20 & mutants M-E01..M-E24 (Python stdlib only)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/test"))
import we01e_report_builder as E  # noqa: E402

E_FORMAL = ROOT / "tools/fixtures/we01/e_formal"
SCENARIOS = ("INITIAL", "ENVELOPE", "REVISED")
REGIONS = ("B1", "B2", "B3")
VERDICTS = ("land_25ha", "buildings_40", "buildings_60", "road_connectivity", "D3")
B8_FIXED = "Gate B8 尚待 Claude 完成正式量測，本報告不代表新增住宅已達效能目標。"
FOLLOWUP_TITLE = "WE-02–WE-09 後續工程建議（僅為建議，未授權）"
PENDING_STR = "PENDING_" + "T016D"
SVG_NS = "{http://www.w3.org/2000/svg}"


def _sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _fmt_m2_ind(v: float) -> str:
    return f"{int(round(v)):,}" if abs(v - round(v)) < 1e-6 else f"{v:,.1f}"


def _parse_md_tables(md: str) -> list[tuple[str, list[str], list[list[str]]]]:
    """Independent Markdown table parser returning (heading_path, headers, rows)."""
    tables: list[tuple[str, list[str], list[list[str]]]] = []
    h_stack: dict[int, str] = {}
    lines = md.splitlines()
    i, n = 0, len(lines)
    while i < n:
        ln = lines[i].strip()
        if ln.startswith("#"):
            lvl = len(ln) - len(ln.lstrip("#"))
            h_stack[lvl] = ln
            for k in [k for k in h_stack if k > lvl]:
                del h_stack[k]
            i += 1
            continue
        if ln.startswith("|") and i + 1 < n and lines[i + 1].strip().startswith("| ---"):
            hdr = [c.strip().strip("`") for c in ln.strip("|").split("|")]
            i += 2
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append([c.strip().strip("`") for c in lines[i].strip().strip("|").split("|")])
                i += 1
            heading = " / ".join(h_stack[k] for k in sorted(h_stack))
            tables.append((heading, hdr, rows))
            continue
        i += 1
    return tables


def _find_table(tables: list[tuple[str, list[str], list[list[str]]]], heading_sub: str, col_sub: str) -> list[list[str]]:
    for h, hdr, rows in tables:
        if heading_sub in h and any(col_sub in c for c in hdr):
            return rows
    raise AssertionError(f"Missing Markdown table under {heading_sub!r} with col {col_sub!r}")


def verify_outputs(in_dir: Path, out_dir: Path) -> None:
    """Independent oracle comparing world_survey.svg (XML) and survey_report.md directly against input JSONs."""
    li = json.loads((in_dir / "land_inventory.json").read_text(encoding="utf-8"))
    ci = json.loads((in_dir / "capacity_inventory.json").read_text(encoding="utf-8"))
    rs = json.loads((in_dir / "road_survey.json").read_text(encoding="utf-8"))
    st = json.loads((in_dir / "internal_streets.json").read_text(encoding="utf-8"))
    cp = json.loads((in_dir / "conditional_parcels.json").read_text(encoding="utf-8"))
    fe = json.loads((in_dir / "feasibility.json").read_text(encoding="utf-8"))
    mg = json.loads((in_dir / "map_geometry.json").read_text(encoding="utf-8"))
    mf = json.loads((in_dir / "inputs_manifest.json").read_text(encoding="utf-8"))

    svg_p, md_p, meta_p = out_dir / "world_survey.svg", out_dir / "survey_report.md", out_dir / "report_meta.json"
    assert svg_p.is_file() and md_p.is_file() and meta_p.is_file(), "Missing formal output files"
    svg_txt = svg_p.read_text(encoding="utf-8")
    md_txt = md_p.read_text(encoding="utf-8")

    # E10 & E11: XML validity, security, portability, determinism cleanliness (M-E14, M-E15, M-E24)
    svg_no_ns = svg_txt.replace('xmlns="http://www.w3.org/2000/svg"', "", 1)
    for bad_pat, label in (
        (r"<!DOCTYPE", "DOCTYPE"), (r"<!ENTITY", "ENTITY"), (r"<script\b", "script"),
        (r"<foreignObject\b", "foreignObject"), (r"<image\b", "image"),
        (r"https?://", "http_url"), (r"file://", "file_url"), (r"@import", "css_import"),
        (r"\bon[a-z]+\s*=", "event_handler"), (r"generated_at", "generated_at"),
        (r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", "iso_timestamp"), (r"/home/|/tmp/", "abs_path"),
    ):
        assert not re.search(bad_pat, svg_no_ns, re.I), f"SVG forbidden pattern: {label}"
        assert not re.search(bad_pat, md_txt, re.I), f"MD forbidden pattern: {label}"
    assert PENDING_STR not in svg_txt and PENDING_STR not in md_txt, "PENDING_T016D leaked"

    root = ET.fromstring(svg_txt.encode("utf-8"))
    assert root.tag == f"{SVG_NS}svg", f"Unexpected root tag {root.tag}"
    ids = [el.attrib["id"] for el in root.iter() if "id" in el.attrib]
    assert len(ids) == len(set(ids)), "Duplicate SVG element IDs"
    id_set = set(ids)
    for el in root.iter():
        for av in el.attrib.values():
            for ref in re.findall(r"url\(#([^)]+)\)", av):
                assert ref in id_set, f"Dangling local SVG ref #{ref}"

    # Collect visible <text> and <title> strings (E04, E12, E13, M-E04)
    vis_texts = ["".join(el.itertext()) for el in root.iter(f"{SVG_NS}text")]
    vis_blob = "\n".join(vis_texts)
    assert fe["base_sha"] in vis_blob, "BASE SHA missing from SVG visible text"
    assert mg["phone_low_static_fingerprint"] in vis_blob, "PHONE_LOW fp missing from SVG"
    assert mg["desktop_high_static_fingerprint"] in vis_blob, "DESKTOP_HIGH fp missing from SVG"
    assert li["mode"] in vis_blob and f"polygon_revision={fe['polygon_revision']}" in vis_blob
    assert "+X" in vis_blob and "+Z" in vis_blob and not re.search(r"\bNorth\b|地理北方", vis_blob)
    assert "panel-legend" in id_set and "panel-global-overview" in id_set and "panel-verdicts" in id_set
    assert "示意" in vis_blob and B8_FIXED in vis_blob and FOLLOWUP_TITLE in vis_blob

    # E12/E13/E14/E15/E16: Panels, scale bars, layers, geometry transform, parcel titles, no invented UNKNOWN
    by_id = {el.attrib["id"]: el for el in root.iter() if "id" in el.attrib}
    all_layers = {el.attrib.get("data-layer") for el in root.iter() if "data-layer" in el.attrib}
    assert {"water", "beach", "site_a", "existing_road", "candidate_road", "internal_street", "parcel"} <= all_layers
    assert "unknown" not in all_layers, "Invented UNKNOWN geometry shape present"

    for sid in SCENARIOS:
        sv = fe["scenarios"][sid]["verdicts"]
        la_t = fe["scenarios"][sid]["land_accounting"]["totals"]
        assert f"{sid}: D3={sv['D3']['verdict']}" in vis_blob, f"SVG missing visible D3 verdict for {sid}"
        assert f"A_eligible={_fmt_m2_ind(la_t['A_eligible'])} / A_eligible_final={_fmt_m2_ind(la_t['A_eligible_final'])}" in vis_blob
        excl = fe["scenarios"][sid]["excluded_sources"]
        for erid, edet in excl.items():
            assert f"{erid}:{edet['reason']}({','.join(edet['conflicting_parcel_ids'])})" in vis_blob
        for rid in REGIONS:
            pid_panel = f"panel-{sid}-{rid}"
            assert pid_panel in by_id and f"scale-{sid}-{rid}" in by_id, f"Missing panel/scale {sid}/{rid}"
            p_el = by_id[pid_panel]
            p_vis = "\n".join("".join(t.itertext()) for t in p_el.iter(f"{SVG_NS}text"))
            cp_r = cp["scenarios"][sid][rid]
            la_r = fe["scenarios"][sid]["land_accounting"]["regions"][rid]
            assert f"C_dir={cp_r['C_direct']} | C_cond={cp_r['C_conditional']} ({cp_r['units_conditional']}u)" in p_vis
            assert f"A_elig={_fmt_m2_ind(la_r['A_eligible'])} | A_elig_fin={_fmt_m2_ind(la_r['A_eligible_final'])}" in p_vis
            assert f"A_unknown={_fmt_m2_ind(la_r['A_unknown'])}" in p_vis
            if cp_r["proxy_used"]:
                assert "[PROXY]" in p_vis

            # E07: Every candidate road in panel must be dashed & labelled candidate (never solid existing)
            for cr_el in p_el.iter(f"{SVG_NS}polyline"):
                if cr_el.attrib.get("data-layer") == "candidate_road":
                    assert cr_el.attrib.get("stroke-dasharray"), f"Candidate road {cr_el.attrib['id']} drawn solid!"
                    tt = cr_el.findtext(f"{SVG_NS}title", "")
                    assert "candidate" in tt and "EXISTING_VERIFIED" not in tt
                    ent = cr_el.attrib.get("data-entity-id")
                    if ent in excl:
                        assert cr_el.attrib.get("data-road-state") == "EXCLUDED_IN_D"

            # E14 & E15: Independent world->SVG geometry fidelity + exact parcel identity for every parcel
            wx0, wz0 = float(p_el.attrib["data-wx0"]), float(p_el.attrib["data-wz0"])
            ox, oz, sc = float(p_el.attrib["data-ox"]), float(p_el.attrib["data-oz"]), float(p_el.attrib["data-scale"])
            found_pids: set[str] = set()
            for r_el in p_el.iter(f"{SVG_NS}rect"):
                if r_el.attrib.get("data-layer") != "parcel":
                    continue
                found_pids.add(r_el.attrib["data-entity-id"])
            expected_pids = {p["parcel_id"] for p in cp_r["parcels"]}
            assert found_pids == expected_pids, f"SVG parcel set mismatch in {sid}/{rid}"
            for p in cp_r["parcels"]:
                rel = by_id[f"parcel-{sid}-{rid}-{p['parcel_id']}"]
                b0, b1, b2, b3 = [float(v) for v in p["bounds"]]
                assert abs(float(rel.attrib["x"]) - (ox + (b0 - wx0) * sc)) <= 0.15, f"Geometry x shift on {p['parcel_id']}"
                assert abs(float(rel.attrib["y"]) - (oz + (b1 - wz0) * sc)) <= 0.15, f"Geometry y shift on {p['parcel_id']}"
                assert abs(float(rel.attrib["width"]) - (b2 - b0) * sc) <= 0.15
                assert abs(float(rel.attrib["height"]) - (b3 - b1) * sc) <= 0.15
                tt = rel.findtext(f"{SVG_NS}title", "")
                for tok in (p["parcel_id"], p["prototype_id"], p["status"], f"{sid}/{rid}"):
                    assert tok in tt, f"Missing {tok} in SVG parcel title {tt!r}"

    # Check failed roads (e.g. H01) in SVG visible text
    for cr_id, r_info in rs["roads"].items():
        if r_info["state"] == "NOT_FEASIBLE":
            assert cr_id in vis_blob and "NOT_FEASIBLE" in vis_blob
            for rsn in r_info["reasons"]:
                assert rsn in vis_blob

    # Independent Markdown verification (E04-E09, E15, E17, E18, M-E03..M-E24)
    assert B8_FIXED in md_txt and f"## 7. {FOLLOWUP_TITLE}" in md_txt
    assert "Gate B8 PASS" not in md_txt and "已授權施工" not in md_txt and "無法建造第18棟" not in md_txt
    assert "已驗證山坡住宅施工" not in md_txt and "不得解讀為已批准全面擴張" in md_txt
    for fn, sha in mf["files"].items():
        assert sha in md_txt, f"Manifest SHA missing in MD for {fn}"

    tables = _parse_md_tables(md_txt)
    exec_rows = {r[0]: r[1:] for r in _find_table(tables, "1. 執行摘要", "land_25ha")}
    for sid in SCENARIOS:
        sv = fe["scenarios"][sid]["verdicts"]
        assert exec_rows[sid] == [sv[vk]["verdict"] for vk in VERDICTS], f"MD exec verdict mismatch for {sid}"
        v_rows = {r[0]: r for r in _find_table(tables, f"情境 `{sid}` 裁定", "Verdict Item")}
        for vk in VERDICTS:
            assert v_rows[vk][1] == sv[vk]["verdict"], f"MD §5 verdict mismatch {sid}/{vk}"
        if sv["buildings_40"]["verdict"] == "UNVERIFIED":
            assert "NOT FEASIBLE" not in v_rows["buildings_40"][1]

        # §3 Land accounting table (exact A_eligible vs A_eligible_final column check -> M-E21)
        land_rows = {r[0]: r for r in _find_table(tables, f"情境 `{sid}`", "A_eligible_final")}
        la_cols = ("A_gross", "A_direct", "A_conditional", "A_new_road", "A_protected", "A_unavailable", "A_unknown", "A_eligible", "A_eligible_final", "A_possible")
        for rid in REGIONS:
            lr = fe["scenarios"][sid]["land_accounting"]["regions"][rid]
            for ci_col, key in enumerate(la_cols, 1):
                assert land_rows[rid][ci_col] == _fmt_m2_ind(lr[key]), f"MD land mismatch {sid}/{rid}/{key}: {land_rows[rid][ci_col]}"
        lt = fe["scenarios"][sid]["land_accounting"]["totals"]
        for ci_col, key in enumerate(la_cols, 1):
            assert land_rows["TOTAL"][ci_col] == _fmt_m2_ind(lt[key]), f"MD land total mismatch {sid}/{key}"

        # §3 Capacity table (exact C_direct, C_conditional, units_conditional, PROXY -> M-E10, M-E18, M-E22)
        cap_rows = {r[0]: r for r in _find_table(tables, f"情境 `{sid}`", "units_conditional")}
        for rid in REGIONS:
            pr = cp["scenarios"][sid][rid]
            b_pre = ci["scenarios"][sid]["regions"][rid]["capacities"]["C_preliminary"]
            row = cap_rows[rid]
            assert row[1] == f"{pr['C_direct']:,}" and row[2] == f"{b_pre:,}"
            assert row[3] == f"{pr['C_conditional']:,}" and row[4] == f"{pr['C_additional']:,}"
            assert row[5] == f"{pr['units_conditional']:,}" and row[6] == f"{pr['C_upper']:,}"
            assert row[7] == f"{pr['C_phone_low']:,}" and row[8] == f"{pr['C_desktop_high']:,}" and row[9] == f"{pr['C_common']:,}"
            if pr["proxy_used"]:
                assert "PROXY" in row[11] and "非已驗證山坡施工" in row[11]

        # §8 Parcel appendix completeness (M-E13)
        app_rows = _find_table(tables, f"情境 `{sid}` 地塊清單", "parcel_id")
        exp_app = {(rid, p["parcel_id"], p["prototype_id"], p["status"]) for rid in REGIONS for p in cp["scenarios"][sid][rid]["parcels"]}
        got_app = {(r[0], r[1], r[2], r[3]) for r in app_rows}
        assert got_app == exp_app, f"MD parcel appendix mismatch in {sid}"

    # §4.1 Excluded roads per scenario (M-E08, M-E23)
    ex_rows = _find_table(tables, "4.1 逐情境排除道路", "Excluded Road")
    by_sc_ex: dict[str, list[list[str]]] = {}
    for r in ex_rows:
        by_sc_ex.setdefault(r[0], []).append(r)
    for sid in SCENARIOS:
        excl = fe["scenarios"][sid]["excluded_sources"]
        if not excl:
            assert len(by_sc_ex[sid]) == 1 and by_sc_ex[sid][0][1] == "none", f"Unexpected exclusion listed in {sid}"
        else:
            got_ex = {r[1]: (r[2], r[3], r[4]) for r in by_sc_ex[sid]}
            for erid, edet in excl.items():
                assert erid in got_ex and got_ex[erid][0] == rs["roads"][erid]["state"]
                assert got_ex[erid][1] == edet["reason"] and got_ex[erid][2] == ", ".join(edet["conflicting_parcel_ids"])

    # §2.3 Road table (M-E09)
    rd_rows = {r[0]: r for r in _find_table(tables, "2.3 T-016C", "geom_corridor_state")}
    for cr_id, r_info in rs["roads"].items():
        assert rd_rows[cr_id][1] == r_info["state"]
        for rsn in r_info["reasons"]:
            assert rsn in rd_rows[cr_id][7]


def _copy_formal(dst: Path) -> Path:
    shutil.copytree(E_FORMAL, dst)
    return dst


def _expect_build_fail(label: str, in_dir: Path, out_dir: Path) -> None:
    rc = E.main(["--input-dir", str(in_dir), "--out", str(out_dir)])
    assert rc != 0, f"Expected build rejection but got rc=0: {label}"
    for fn in ("world_survey.svg", "survey_report.md", "report_meta.json"):
        assert not (out_dir / fn).exists(), f"Left formal output {fn} after failure: {label}"


def _expect_red(label: str, base_in: Path, base_out: Path, td: Path, mut_fn) -> None:
    md_dir = td / f"mut_{re.sub(r'[^a-zA-Z0-9_]', '_', label)}"
    md_dir.mkdir(parents=True, exist_ok=True)
    svg_s = (base_out / "world_survey.svg").read_text(encoding="utf-8")
    md_s = (base_out / "survey_report.md").read_text(encoding="utf-8")
    svg2, md2 = mut_fn(svg_s, md_s)
    assert (svg2 != svg_s) or (md2 != md_s), f"Mutant transform was a no-op: {label}"
    (md_dir / "world_survey.svg").write_text(svg2, encoding="utf-8")
    (md_dir / "survey_report.md").write_text(md2, encoding="utf-8")
    shutil.copy2(base_out / "report_meta.json", md_dir / "report_meta.json")
    try:
        verify_outputs(base_in, md_dir)
    except (AssertionError, ET.ParseError):
        return
    raise AssertionError(f"Mutant stayed GREEN: {label}")


def test_e01_e02_e20_input_rejections(td: Path) -> None:
    # --help & out_dir == input_dir
    cp_help = subprocess.run([sys.executable, "-B", str(ROOT / "tools/test/we01e_report_builder.py"), "--help"], capture_output=True, text=True, check=False)
    assert cp_help.returncode == 0 and "--input-dir" in cp_help.stdout and "--dump" not in cp_help.stdout
    in0 = _copy_formal(td / "in_same")
    assert E.main(["--input-dir", str(in0), "--out", str(in0)]) != 0

    def _tamper(tag: str, fn: str, mut) -> None:
        d = _copy_formal(td / f"bad_{tag}")
        mut(d, fn)
        _expect_build_fail(tag, d, td / f"out_bad_{tag}")

    # E01/E02/M-E01/M-E02(1)/M-E20: missing file, bad manifest SHA, bad BASE, bad fp, bad schema, bad D->B hash, missing field
    _tamper("missing_file", "feasibility.json", lambda d, f: (d / f).unlink())
    _tamper("M-E02_1_manifest_sha", "feasibility.json", lambda d, f: (d / f).write_text((d / f).read_text(encoding="utf-8") + " ", encoding="utf-8"))

    def _edit_and_rehash(d: Path, fn: str, fn_edit) -> None:
        obj = json.loads((d / fn).read_text(encoding="utf-8"))
        fn_edit(obj)
        (d / fn).write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        mf = json.loads((d / "inputs_manifest.json").read_text(encoding="utf-8"))
        mf["files"][fn] = _sha256(d / fn)
        (d / "inputs_manifest.json").write_text(json.dumps(mf, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    _tamper("M-E01_bad_base", "feasibility.json", lambda d, f: _edit_and_rehash(d, f, lambda o: o.__setitem__("base_sha", "0" * 40)))
    _tamper("M-E01_bad_fp", "map_geometry.json", lambda d, f: _edit_and_rehash(d, f, lambda o: o.__setitem__("phone_low_static_fingerprint", "a" * 64)))
    _tamper("E01_bad_schema", "road_survey.json", lambda d, f: _edit_and_rehash(d, f, lambda o: o.__setitem__("schema_version", 9)))
    _tamper("E02_bad_polyrev", "feasibility.json", lambda d, f: _edit_and_rehash(d, f, lambda o: o.__setitem__("polygon_revision", 1)))
    _tamper("E02_bad_d_src_sha", "feasibility.json", lambda d, f: _edit_and_rehash(d, f, lambda o: o["sources"].__setitem__("road_survey_sha256", "b" * 64)))
    _tamper("M-E20_missing_num", "feasibility.json", lambda d, f: _edit_and_rehash(d, f, lambda o: o["scenarios"]["REVISED"]["land_accounting"]["regions"]["B1"].pop("A_eligible_final")))


def test_e03_to_e20_and_all_mutants(td: Path) -> None:
    in_dir = _copy_formal(td / "formal_copy")
    before = {p.name: _sha256(p) for p in sorted(in_dir.glob("*.json"))}

    # E19 & E20: 3x deterministic CLI builds, timing <= 10.0 s, read-only input integrity (E03)
    hashes = []
    for k in range(3):
        od = td / f"build_{k}"
        t0 = time.monotonic()
        assert E.main(["--input-dir", str(in_dir), "--out", str(od)]) == 0
        dt = time.monotonic() - t0
        assert dt <= 10.0, f"Build {k} exceeded 10 s: {dt:.2f}s"
        hashes.append((_sha256(od / "world_survey.svg"), _sha256(od / "survey_report.md")))
    assert hashes[0] == hashes[1] == hashes[2], "E19 determinism failed across 3 builds"
    after = {p.name: _sha256(p) for p in sorted(in_dir.glob("*.json"))}
    assert before == after, "E03 read-only input integrity violated"

    out_0 = td / "build_0"
    verify_outputs(in_dir, out_0)

    # M-E02 case 2: Legitimate synthetic fixture change -> builder reflects new values; stale report fails RED!
    syn_in = _copy_formal(td / "syn_legit")
    fe_s = json.loads((syn_in / "feasibility.json").read_text(encoding="utf-8"))
    cp_s = json.loads((syn_in / "conditional_parcels.json").read_text(encoding="utf-8"))
    fe_s["scenarios"]["REVISED"]["land_accounting"]["regions"]["B1"]["A_eligible_final"] += 123.0
    fe_s["scenarios"]["REVISED"]["land_accounting"]["totals"]["A_eligible_final"] += 123.0
    cp_s["scenarios"]["REVISED"]["B3"]["units_conditional"] += 4
    (syn_in / "feasibility.json").write_text(json.dumps(fe_s, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (syn_in / "conditional_parcels.json").write_text(json.dumps(cp_s, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    mf_s = json.loads((syn_in / "inputs_manifest.json").read_text(encoding="utf-8"))
    mf_s["files"]["feasibility.json"] = _sha256(syn_in / "feasibility.json")
    mf_s["files"]["conditional_parcels.json"] = _sha256(syn_in / "conditional_parcels.json")
    (syn_in / "inputs_manifest.json").write_text(json.dumps(mf_s, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    syn_out = td / "syn_out"
    assert E.main(["--input-dir", str(syn_in), "--out", str(syn_out)]) == 0
    verify_outputs(syn_in, syn_out)
    # Stale old output against updated legitimate inputs MUST fail (M-E02 case 2)
    try:
        verify_outputs(syn_in, out_0)
        raise AssertionError("M-E02 case 2 stayed GREEN with stale report")
    except AssertionError as exc:
        assert "stayed GREEN" not in str(exc)

    # All output/presentation mutants M-E03..M-E19 and M-E21..M-E24 must turn RED
    mutants = [
        ("M-E03_md_num", lambda s, m: (s, m.replace("305,858", "305,999", 1))),
        ("M-E04_svg_vis", lambda s, m: (s.replace("A_eligible_final=305,858", "A_eligible_final=305,999", 1), m)),
        ("M-E05_rev_feasible", lambda s, m: (s, m.replace("| `REVISED` | `CONDITIONAL` | `UNVERIFIED` | `UNVERIFIED` | `CONDITIONAL` | `UNVERIFIED` |", "| `REVISED` | `CONDITIONAL` | `FEASIBLE` | `UNVERIFIED` | `CONDITIONAL` | `FEASIBLE` |", 1))),
        ("M-E06_b3_not_feas", lambda s, m: (s, m + "\nB3 無法建造第18棟。\n")),
        ("M-E06_verdict_nf", lambda s, m: (s, m.replace("| `buildings_40` | `UNVERIFIED` |", "| `buildings_40` | `NOT FEASIBLE WITHIN AUDITED BOUNDARIES` |", 1))),
        ("M-E07_cand_solid", lambda s, m: (re.sub(r'stroke-dasharray="[^"]+"(\s+data-layer="candidate_road")', r"\1", s, count=1), m)),
        ("M-E08_drop_c01_excl", lambda s, m: (s, m.replace("B1_R02_005", "REMOVED_ID"))),
        ("M-E09_drop_h01_rsn", lambda s, m: (s, m.replace("GRADE_LIMIT_EXCEEDED", "NONE"))),
        ("M-E10_double_count", lambda s, m: (s, m.replace("| `B1` | 5 | 72 | 21 |", "| `B1` | 5 | 72 | 26 |", 1))),
        ("M-E11_drop_region", lambda s, m: (s.replace('id="panel-REVISED-B3"', 'id="panel-DROPPED"'), m)),
        ("M-E12_drop_sitea", lambda s, m: (s.replace('data-layer="site_a"', 'data-layer="other"'), m)),
        ("M-E12_drop_unknown_note", lambda s, m: (s.replace("A_unknown=0", "A_unk_removed", 1), m)),
        ("M-E13_drop_parcel_id", lambda s, m: (s.replace("B1_R02_005", "PARCEL_X"), m)),
        ("M-E14_script", lambda s, m: (s.replace("</svg>", "<script>alert(1)</script></svg>"), m)),
        ("M-E14_onclick", lambda s, m: (s.replace("<svg ", '<svg onclick="x()" ', 1), m)),
        ("M-E14_foreignObj", lambda s, m: (s.replace("</svg>", "<foreignObject/></svg>"), m)),
        ("M-E14_doctype", lambda s, m: (s.replace("<svg ", "<!DOCTYPE svg><svg ", 1), m)),
        ("M-E14_ext_url", lambda s, m: (s.replace("</svg>", "<text>https://example.com</text></svg>"), m)),
        ("M-E15_timestamp", lambda s, m: (s, m + "\ngenerated_at: 2026-11-28T00:00:00Z\n")),
        ("M-E16_b8_pass", lambda s, m: (s, m.replace(B8_FIXED, "Gate B8 PASS"))),
        ("M-E17_authorized", lambda s, m: (s, m.replace(FOLLOWUP_TITLE, "WE-02–WE-09 已授權施工"))),
        ("M-E18_b2_proxy", lambda s, m: (s, m.replace("PROXY（平地代理，非已驗證山坡施工）", "已驗證山坡住宅施工"))),
        ("M-E19_geom_shift", lambda s, m: (re.sub(r'(id="parcel-REVISED-B1-B1_R02_001" x=")([0-9.]+)"', lambda mo: f'{mo.group(1)}{float(mo.group(2)) + 15.0:.2f}"', s, count=1), m)),
        ("M-E21_swap_elig", lambda s, m: (s, m.replace("| 323,715 | 305,858 |", "| 305,858 | 323,715 |", 1))),
        ("M-E22_units_as_bldg", lambda s, m: (s, m.replace("| `B3` | 17 | 25 | 17 | 0 | 29 |", "| `B3` | 17 | 25 | 29 | 0 | 29 |", 1))),
        ("M-E23_c01_in_init", lambda s, m: (s, m.replace("| `INITIAL` | `none` | — | — | — | 本情境無候選道路因直接地塊衝突遭排除 |", "| `INITIAL` | `C01` | `CONDITIONAL_VERIFIED` | `DIRECT_PARCEL_CONFLICT` | `B1_R02_005` | bad |", 1))),
        ("M-E24_pending_tok", lambda s, m: (s, m + f"\n{PENDING_STR}\n")),
    ]
    for label, mut_fn in mutants:
        _expect_red(label, in_dir, out_0, td, mut_fn)


def main() -> int:
    t0 = time.monotonic()
    with tempfile.TemporaryDirectory() as tmp:
        td = Path(tmp)
        for label, fn in (
            ("E01/E02/E20 input rejections & M-E01/M-E02(1)/M-E20", test_e01_e02_e20_input_rejections),
            ("E03-E20 independent SVG/MD oracles, M-E02(2) & M-E03..M-E24 RED", test_e03_to_e20_and_all_mutants),
        ):
            ts = time.monotonic()
            fn(td)
            print(f"PASS [{label}] ({time.monotonic() - ts:.2f}s)")
    print(f"RESULT: PASS (WE-01E E01-E20 + M-E01..M-E24 all RED + 3x determinism in {time.monotonic() - t0:.2f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
