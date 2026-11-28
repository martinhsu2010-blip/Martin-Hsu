#!/usr/bin/env python3
"""Claude-owned check for the T-017 (WE-02) generator and verifier: determinism, unit checks on the
formal data, and negative controls (every tampering must turn the verifier red).
Usage: python3 -B tools/we02/we02_check.py   (run from the repository root; needs full git history)
"""
import copy, importlib.util, json, os, shutil, subprocess, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
INDIR = os.path.join(REPO, "tools", "fixtures", "we01", "e_formal")
CLI = [sys.executable, "-B", os.path.join(HERE, "we02_generate.py")]


def mod(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, name + ".py"))
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


G, V = mod("we02_generate"), mod("we02_verify")
fails, n = [], 0


def ok(cond, msg):
    global n
    n += 1
    if not cond:
        fails.append(msg)


def gen(out, indir=INDIR):
    return subprocess.run(CLI + ["--input-dir", indir, "--out", out], capture_output=True, text=True)


def read(d, f):
    return open(os.path.join(d, f), "rb").read()


def verify(plandir):
    R, _, _ = V.verify(INDIR, plandir, REPO)
    return R


def mutated(base, mut):
    d = tempfile.mkdtemp(prefix="we02m_")
    for f in os.listdir(base):
        shutil.copy(os.path.join(base, f), d)
    mut(d)
    return d


def edit_plan(fn):
    def m(d):
        p = json.load(open(os.path.join(d, "district_plan.json")))
        fn(p)
        open(os.path.join(d, "district_plan.json"), "w").write(json.dumps(p, indent=1, sort_keys=True, ensure_ascii=False) + "\n")
    return m


def edit_text(f, a, b):
    def m(d):
        t = open(os.path.join(d, f), encoding="utf-8").read()
        assert a in t, f"mutation target missing in {f}: {a}"
        open(os.path.join(d, f), "w", encoding="utf-8").write(t.replace(a, b, 1))
    return m


def parcel(p, region, phase, proto=None, status=None):
    for x in p["parcels"]:
        if x["region"] == region and x["phase"] == phase and (proto is None or x["prototype_id"] == proto) and (status is None or x["we01_status"] == status):
            return x
    raise KeyError((region, phase, proto))


def main():
    t0 = time.time()
    tmp = tempfile.mkdtemp(prefix="we02_")
    outs = [os.path.join(tmp, f"o{i}") for i in range(3)]
    for o in outs:
        r = gen(o)
        ok(r.returncode == 0 and r.stdout.startswith("OK [WE02]"), f"generator run failed: {r.stderr[-200:]}")
    names = ("district_plan.json", "masterplan.svg", "masterplan.md", "dependency_matrix.md")
    ok(all(read(outs[0], f) == read(o, f) for o in outs[1:] for f in names), "E01 three runs are byte-identical")
    base = outs[0]
    R = verify(base)
    ok(not R.fails and R.n > 400, f"E02 verifier green on the formal output ({R.n} checks, fails {R.fails[:2]})")
    plan = json.load(open(os.path.join(base, "district_plan.json")))
    # unit checks
    ok(G.clip_area([[0, 0], [2, 0], [2, 2], [0, 2]], 0, 0, 1, 1) == 1.0 and abs(G.clip_area([[0, 0], [2, 0], [0, 2]], 0, 0, 1, 1) - 1.0) < 1e-9, "U01 clip_area")
    ok(plan["we01_reproduction_control"] == {r: {"raster": v["we01_A_new_road"], "we01_A_new_road": v["we01_A_new_road"]} for r, v in plan["we01_reproduction_control"].items()}
       and plan["we01_reproduction_control"]["B1"]["raster"] == 8013 and plan["we01_reproduction_control"]["B2"]["raster"] == 10555, "U02 full ENVELOPE raster reproduces WE-01 8,013 / 10,555")
    ok(plan["street_choice_phase2"]["chosen"] == "ENVELOPE_B1_ST_0085" and len({c["added_cells_vs_c02_only"] for c in plan["street_choice_phase2"]["candidates"]}) == 1, "U03 symmetric streets resolved by street_id")
    ok([plan["phases"][p]["buildings_total"] for p in "12"] == [40, 57] and plan["phases"]["2"]["deficit_by_prototype"]["B3"] == {"R01": 1, "R05": 1, "R08": 1}, "U04 40 / 57 buildings, B3 deficit 1 each")
    ok([round(plan["phases"][p]["engineering"]["length_m"], 3) for p in "12"] == [1110.214, 1390.214], "U05 engineering lengths")
    ok(plan["phases"]["1"]["units_total"] == 52 and plan["reserved_parcels"] == [], "U06 52 units, no reserved parcels")
    # generator input tampering
    bad = os.path.join(tmp, "in_bad")
    shutil.copytree(INDIR, bad)
    t = open(os.path.join(bad, "conditional_parcels.json")).read()
    open(os.path.join(bad, "conditional_parcels.json"), "w").write(t.replace('"B1_R02_001"', '"B1_R02_00X"', 1))
    r = gen(os.path.join(tmp, "o_bad"), bad)
    ok(r.returncode != 0 and not os.path.exists(os.path.join(tmp, "o_bad", "district_plan.json")), "N00 tampered input is refused, no output")
    # negative controls: every mutation must make the verifier fail
    p1b1_r01 = lambda p: parcel(p, "B1", 1, "R01", "DIRECT")
    cases = {
        "N01 prototype changed": edit_plan(lambda p: parcel(p, "B2", 1).update(prototype_id="R01")),
        "N02 parcel moved onto another parcel": edit_plan(lambda p: (lambda a, b: (b.update(bounds_internal=list(a["bounds_internal"]), polygon=a["polygon"])))(parcel(p, "B3", 1, "R05"), [x for x in p["parcels"] if x["region"] == "B3" and x is not parcel(p, "B3", 1, "R05")][0])),
        "N03 C01 added to a chain": edit_plan(lambda p: (parcel(p, "B1", 1, status="CANDIDATE_ROAD_REQUIRED").update(engineering_required=["C01", "X01"]))),
        "N04 Phase 1 parcel dropped": edit_plan(lambda p: p["parcels"].remove(parcel(p, "B2", 1))),
        "N05 parcel placed inside Site A": edit_plan(lambda p: parcel(p, "B3", 1, "R05").update(bounds_internal=[-540, -800, -516, -778], polygon=[[-540, -800], [-516, -800], [-516, -778], [-540, -778]])),
        "N06 R06 appears in B2": edit_plan(lambda p: parcel(p, "B2", 2).update(prototype_id="R06")),
        "N07 B3 Phase 2 deficit hidden": edit_plan(lambda p: p["phases"]["2"]["deficit_by_prototype"].update(B3={})),
        "N08 B3 Phase 2 promoted": edit_plan(lambda p: p["phases"]["2"]["status"].update(B3="CONDITIONAL")),
        "N09 road raster tampered": edit_plan(lambda p: p["phases"]["1"]["land_accounting"]["B1"].update(A_new_road_raster=3000)),
        "N10 area conservation broken": edit_plan(lambda p: p["phases"]["1"]["land_accounting"]["B2"].update(A_other_eligible=1)),
        "N11 SVG phase tampered": edit_text("masterplan.svg", 'data-phase="1" data-prototype', 'data-phase="2" data-prototype'),
        "N12 markdown number tampered": edit_text("masterplan.md", "1110.214", "1100.000"),
        "N13 reserved parcel added": edit_plan(lambda p: p["reserved_parcels"].append({"parcel_id": "X"})),
        "N14 B1 R02 ratio broken": edit_plan(lambda p: [x.update(prototype_id="R01") for x in p["parcels"] if x["region"] == "B1" and x["phase"] == 1 and x["prototype_id"] == "R02"][:3]),
        "N15 Phase 2 parcel moved into Phase 1": edit_plan(lambda p: [x for x in p["parcels"] if x["region"] == "B1" and x["phase"] == 2 and x["internal_street_id"] == "ENVELOPE_B1_ST_0085"][0].update(phase=1)),
        "N16 Phase 1 engineering gains C02": edit_plan(lambda p: p["phases"]["1"]["engineering"]["items"].append(copy.deepcopy([e for e in p["phases"]["2"]["engineering"]["items"] if e["id"] == "C02"][0]))),
        "N17 input hash tampered": edit_plan(lambda p: p["inputs"].update({"road_survey.json": "0" * 64})),
        "N18 forbidden road in Phase 2 set": edit_plan(lambda p: p["phases"]["2"]["engineering"]["items"].append({"id": "H01", "kind": "EXTERNAL_CANDIDATE_ROAD", "region": "B2", "length_m": 431.421, "status": "NOT_FEASIBLE", "built": False, "beach_encroachment_m2": 0.0})),
        "N19 polygon not equal to footprint": edit_plan(lambda p: parcel(p, "B1", 1).update(polygon=[[0, 0], [1, 0], [1, 1], [0, 1]])),
        "N20 dependency chain endpoint broken": edit_plan(lambda p: parcel(p, "B1", 1, status="CANDIDATE_ROAD_REQUIRED").update(dependency_chain=["X01"])),
        "N21 BASE changed": edit_plan(lambda p: p.update(base_sha="0" * 40)),
        "N22 SVG gains a script": edit_text("masterplan.svg", '<rect id="region-B1"', '<script>1</script><rect id="region-B1"'),
    }
    for name, mut in cases.items():
        d = mutated(base, mut)
        R2 = verify(d)  # an exception here is a verifier bug and fails the check run
        ok(len(R2.fails) > 0, f"{name} must turn the verifier red")
        shutil.rmtree(d, ignore_errors=True)

    # generator code mutants: a wrong generator must be caught by the independent verifier
    gsrc = open(os.path.join(HERE, "we02_generate.py"), encoding="utf-8").read()
    mutants = {
        "M01 Phase 1 B1 R01 target 4": ('1: {"B1": {"R01": 5, "R02": 5}', '1: {"B1": {"R01": 4, "R02": 5}'),
        "M02 Phase 1 engineering gains C02": ('PHASE1_ENG = {"X01", "H02", "ENVELOPE_B1_ST_0305"}', 'PHASE1_ENG = {"X01", "H02", "ENVELOPE_B1_ST_0305", "C02"}'),
        "M03 street choice prefers larger id": ('key=lambda c: (c["added_cells_vs_c02_only"], c["street_id"]))', 'key=lambda c: (c["added_cells_vs_c02_only"], c["street_id"]), reverse=True)'),
        "M04 beach cells not excluded": ("return cells - gone, gone", "return cells, gone"),
        "M05 parcel pool ignores dependency closure": ("eng_of(p) <= allowed)", "True)"),
        "M06 B3 Phase 2 promoted": ('"B3": "VERIFIED_DIRECT" if ph == 1 else "UNVERIFIED"', '"B3": "VERIFIED_DIRECT" if ph == 1 else "CONDITIONAL"'),
        "M07 Site A shifted": ("SITE_A = (-561, -831, -441, -753)", "SITE_A = (-561, -831, -441, -700)"),
    }
    for name, (a, b) in mutants.items():
        ok(gsrc.count(a) == 1, f"{name}: mutation target present")
        mdir = tempfile.mkdtemp(prefix="we02g_")
        open(os.path.join(mdir, "g.py"), "w", encoding="utf-8").write(gsrc.replace(a, b, 1))
        r = subprocess.run([sys.executable, "-B", os.path.join(mdir, "g.py"), "--input-dir", INDIR, "--out", os.path.join(mdir, "o")], capture_output=True, text=True)
        if r.returncode != 0:
            ok(True, name)  # the generator refused (no feasible plan)
        else:
            ok(len(verify(os.path.join(mdir, "o")).fails) > 0, f"{name} must turn the verifier red")
        shutil.rmtree(mdir, ignore_errors=True)
    # registered artifacts must equal a fresh deterministic build (when they exist)
    reg = os.path.join(REPO, "specs", "we02")
    if os.path.isdir(reg):
        ok(all(read(base, f) == read(reg, f) for f in names), "E03 specs/we02 artifacts equal a fresh build")
        vtmp = os.path.join(tmp, "val_reg.md")
        V.main(["--input-dir", INDIR, "--plan-dir", base, "--out-validation", vtmp, "--repo", REPO])
        ok(open(vtmp, "rb").read() == read(reg, "we02_validation.md"), "E04 we02_validation.md equals a fresh verification")
    # validation report is produced and mentions every gate
    vf = os.path.join(tmp, "val.md")
    rc = V.main(["--input-dir", INDIR, "--plan-dir", base, "--out-validation", vf, "--repo", REPO])
    txt = open(vf, encoding="utf-8").read()
    ok(rc == 0 and all(f"MP{k:02d}" in txt for k in range(1, 19)) and "失敗 0" in txt, "R01 validation report covers MP01..MP18")
    shutil.rmtree(tmp, ignore_errors=True)
    print(("RESULT: PASS" if not fails else "RESULT: FAIL") + f" (WE-02 E01-E02, U01-U06, N00-N22 artifact tampering, M01-M07 generator mutants, {n} checks in {time.time() - t0:.1f}s)")
    for f in fails:
        print("  FAIL", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
