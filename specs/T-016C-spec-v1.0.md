# T-016C — WE-01C Road Feasibility Survey: registered specification and Claude conditions

**Registered by Claude 2026-11-27 (D-054).** Approved by Martin ("批准", 2026-11-27 16:00) for **T-016C only**, on the basis of the ChatGPT draft `specs/T-016C-draft-v1.0-chatgpt.md` plus the Claude conditions below (G0 review `T-016C_G0_review` delivered to Martin). T-016D (internal streets, conditional capacity, final verdicts, final SVG/report) is **not** registered or approved.

## 0. Source documents and precedence

1. This file (Claude conditions, wins on any conflict).
2. `specs/T-016C-draft-v1.0-chatgpt.md` (scope, fixed roads, parameters, verdict names, tests R01-R18, mutations).
3. `specs/T-016B-spec-v1.4.md` (merged T-016B interface and conventions) and `specs/WE-01-v1.4-errata-T016B.md`, `specs/WE-01-v1.4-amendment.md` (sections E, F), `specs/WE-01-v1.3-amendment.md` (R8, R9), `specs/WE-01-spec-v1.2.md` (section 8, B13-B16, C-tests that concern roads).
4. `tools/fixtures/we01/SCHEMA_NOTES.md`.

Corrections to the draft decided at G0:
- The draft statement "C02/X01 must keep the AVE110 dependency" is replaced by G0-C7: C02 and X01 connect to the AVE_0 main component **without** the AVE110 extension (via C01 -> RIB_0, or X01 west end -> existing junction (-240,880)); AVE110_EXTENSION_REQUIRED only labels the optional link (110,960) <-> AVE_110.
- Numbers quoted in the draft (62.3 m, 433 m, 14.4 %, 134.9 %) are evidence only; tests and reports never assert them on real data.
- Decided by Martin: line ceiling 1,400 combined (D-054); beach encroachment is **not** a failure (G0-C10).

## 1. Scope, allowlist, budget

- Implementer: Gemini (Stage 3, per-task exception continues, D-054). Reviewer: Claude. Risk LOW, volume SMALL.
- Branch `gemini/T-016C-we01c-road-analyzer`, base = latest `main` at start (Claude gives the SHA).
- Only two new files: `tools/test/we01c_road_analyzer.py` and `tools/test/we01c_road_analyzer_check.py`. Python standard library only. No change to any existing file (analyzers, checks, fixtures, extractor, production, `sw.js`, CI, docs, specs). Run with `python3 -B`; never commit dumps, outputs or `__pycache__`.
- Lines (both files combined): target 1,150, **hard ceiling 1,400 with sub-limits analyzer <= 850 and check <= 550** (Martin, D-054; the T-016B exceptions D-052a/D-052b do not carry over). Report `wc -l` of both files at about 700 lines and again before finishing. Over a sub-limit or 1,400 -> STOP and return to Claude. No compression, no weakened or deleted tests to fit.
- Allowed imports:
  - From `we01a_land_analyzer`: `validate_dump`, `compute_static_fingerprint`, `sample_height` (call with region id `"ROAD_CORRIDOR"`), `fp_intersects_cell`, `clip_poly_to_rect`, `poly_bounds`, `poly_area`, `is_axis_rect`, `dist_point_to_poly`.
  - From `we01b_capacity_analyzer`: `load_dumps`, `build_road_graph`, `corridors_from_graph`, `SCENARIOS`, `spec_to_internal`, `internal_to_spec`, `POLYGON_REVISION`, `ANALYZER_VERSION` (import as `B_VERSION`).
  - **No underscore (private) names** from any module. Centerline-intersection and endpoint-distance helpers are rewritten locally and locked by a test to agree with T-016B on the existing network (same main component).
  - Check script only: `make_dump`, `_rect`, `_fp`, `_write_dump`, `_expect_fail` from `we01a_land_analyzer_check` (read-only), plus the public names above.

## 2. Binding rules (Claude conditions G0-C1 .. G0-C10)

All coordinates X/Z in metres. The six roads, control points, carriageway widths, corridor half-widths, radii and grade limits are exactly the draft's section 4-5 tables (C01 17 m / 12.5 m; C02 and X01 7 m / 5.5 m; H01, H02 8 m / 6 m; U01 existing). Control points are never moved; no seventh road.

**G0-C1 Fillets.** Interior vertex deflection angle `theta` (0..pi); tangent length `t = R * tan(theta/2)` with `R` = 25 m (C01, C02, X01) or 18 m (H01, H02). Require `t <= L_prev/2` and `t <= L_next/2` using the **original** control-segment lengths, and, where two fillets share one segment, the two tangent lengths together `<= that segment's length`. `theta < 1e-9` (collinear, e.g. C02) -> no arc. A violation -> `GEOMETRY_INVALID` (reason `ARC_DOES_NOT_FIT`); never shrink `R`. Arc samples every <= 3 m (`ceil(arc_length/3)` pieces); straight pieces are resampled to <= 3 m. Keep both endpoints and the tangent points. Report control points, centerline, radius, tangent length, arc length, total length and maximum sample spacing. No splines, no optimisation, no re-routing.

**G0-C2 Grade.** Heights from the dump's 1 m `ROAD_CORRIDOR` grids via `sample_height(grids, "ROAD_CORRIDOR", x, z)` (bilinear; tag `INTERPOLATED_1M`, never a design height). `max_step_grade` = maximum over consecutive centerline samples of `100 * |dh| / horizontal distance`. A road passes the grade test iff `max_step_grade <= limit + 1e-9` (6 % normal, 9 % hillside; exactly 6.0 passes, 6.001 fails). Also report `net_average_grade` (`100*|h_end-h_start|/length`); it never rescues a road whose step grade exceeds the limit. Any sample without height -> `UNVERIFIED` (reason `HEIGHT_MISSING`). Failing grade -> `NOT_FEASIBLE` with reason `GRADE_LIMIT_EXCEEDED`.

**G0-C3 Corridor.** Corridor = centerline buffered by the corridor half-width, built as the union of one rectangle per consecutive sample pair plus a 16-gon disk of radius = half-width at every sample (covers the outer wedge of arcs). Overlap tests use **positive area** (touching is not overlap). The whole corridor must lie inside the dump's `physical_ground` bounds and inside the union of the road's own COR grid; its outer edge must be >= 5 m from the COR grid boundary, otherwise `UNVERIFIED` (reason `COR_MARGIN`). Missing support or elevation evidence never passes automatically.

**G0-C4 Obstacle classes for corridors.** For every footprint of both presets (union; ids are not stable across presets, compare geometry):
- `BLOCKING` -> road `NOT_FEASIBLE` (reason `CORRIDOR_BLOCKED`): categories BUILDING, TREE, COLLIDER with `physical = true`, SITE_A / `protected`, and water regions, when `geometry_precision = EXACT_OUTLINE` (a TREE or COLLIDER collider counts as exact for this rule only when its source is `PHYSICS_STATIC`/`TREE_COLLIDERS` and the footprint is not a CONSERVATIVE_AABB).
- A blocking category proven only by a `CONSERVATIVE_AABB` footprint -> road `UNVERIFIED` (reason `CORRIDOR_CONSERVATIVE_OBSTACLE`), never `NOT_FEASIBLE` (same rule as T-016B: conservative obstacles never prove infeasibility).
- Non-physical `OTHER` footprints (street furniture such as lamp parts, `physical = false`) -> advisory `STREET_FURNITURE_RELOCATION` (count and ids), not a failure.
- ROAD / SIDEWALK footprints: see G0-C5.
- Beach: see G0-C10.

**G0-C5 Junction overlap.** The *connected existing segments* of a candidate endpoint are the existing VERIFIED GROUND segments that satisfy the G0-C6 connection rule at that endpoint. Overlap of the candidate corridor with ROAD or SIDEWALK footprints of those segments is allowed (`JUNCTION_OVERLAP`) only where the overlap lies within `J = corridor_half_width + existing_carriageway_half_width + 1 m` of the endpoint; overlap beyond `J`, or with ROAD/SIDEWALK of any other segment, is `BLOCKING`. Candidate-to-candidate corridor overlap is allowed only within `corridor_half_width_a + corridor_half_width_b + 1 m` of their shared junction point and is reported as `JUNCTION_OVERLAP_CANDIDATE`; elsewhere it is `BLOCKING`.

**G0-C6 Connection rule (R8 for candidates).** Two roads are connected iff (a) their (filleted) centerlines intersect, or (b) an endpoint of one lies within `carriageway_width/2 + 1 m` of the **filleted** centerline of the other (carriageway half-width, **not** corridor half-width; this is the T-016B convention); both must be GROUND with compatible elevation: the heights at the junction point differ by <= 0.5 m (the extractor's GROUND/ELEVATED threshold); missing height -> `UNVERIFIED`. ELEVATED, RAMP and UNKNOWN segments never connect by planar crossing. Roads outside the audit windows are never inferred. A candidate whose endpoint connects to nothing is a free end (allowed, reported). Existing segments are taken from `build_road_graph(dump)` (aliases, main component); candidate roads are kept in a **separate** candidate graph and never added to the existing graph.

**G0-C7 Road states and dependency chains.** Each road gets exactly one state: `EXISTING_VERIFIED` (U01 only, if its endpoints and geometry check out against the existing graph; never new length or new area), `CONDITIONAL_VERIFIED` (geometry legal under G0-C1..C5 **and** at least one complete dependency chain to the AVE_0 main component), `UNVERIFIED`, `NOT_FEASIBLE`. A dependency chain is an ordered list of candidate road ids and junction ids that would have to be built; several alternative chains may exist and all are listed (e.g. C02: `[C01 + junction C01/RIB_0]` or `[X01 + junction X01/(-240,880)]`). Unbuilt candidates are never `EXISTING_VERIFIED`, never marked `existing: true`, never `FEASIBLE` on their own. `AVE110_EXTENSION_REQUIRED` is attached only to the optional link between (110,960) and AVE_110 (about 68 m, never generated or verified here). A road whose chain passes through a `NOT_FEASIBLE` or `UNVERIFIED` road is itself not complete via that chain. One failing road never changes another road's state or a region's verdict (H01 failing does not fail H02 or B2). H01's start junction is on HILL_ROAD/TRD_0, which are not in the AVE_0 main component, so H01 cannot be a legal source in any case.

**G0-C8 Regional external-access verdicts** (3 scenarios x 3 regions, frozen REVISED-v2 table via `SCENARIOS`; `polygon_revision = 2`):
- `FEASIBLE`: some `EXISTING_VERIFIED` road or existing main-component corridor (ROAD or SIDEWALK footprint of a main-component segment) intersects the scenario polygon or lies within 2.0 m of it (the R7 gap).
- `CONDITIONAL`: no such existing access, but at least one `CONDITIONAL_VERIFIED` candidate corridor intersects the scenario polygon with a complete dependency chain.
- `NOT FEASIBLE WITHIN AUDITED BOUNDARIES`: only with positive evidence that every route into the region fails; failing to find a candidate is never enough.
- `UNVERIFIED`: everything else.
Never derive a verdict from T-016B parcel counts, region centres or mere planar passage. Each verdict lists its evidence (road ids, chain, reasons). External access only; no capacity statement (`C_conditional` stays `PENDING_T016D`).

**G0-C9 No hard-coding.** Road lengths, grades, state or verdict values, segment ids of the real dump and numbers from the draft/G0 are never constants in the analyzer. Exact numbers are asserted only on synthetic fixtures; on real fixtures only properties (for example H01 is `NOT_FEASIBLE` with `GRADE_LIMIT_EXCEEDED`, H02 is `CONDITIONAL_VERIFIED`, C01 starts connected to RIB_0). Real sample dumps may have a 25 m COR band; the margin rule is applied as written.

**G0-C10 Beach.** The preserved beach (`world.beach_regions`) is **not** a failure for roads (Martin, D-054). Report per road `beach_encroachment_m2` (corridor area inside the beach polygons, 1 m cell centres) and a top-level total; T-016D must handle area exclusivity. The beach never turns a road `NOT_FEASIBLE` or `UNVERIFIED`.

## 3. Interface and outputs

- CLI: `python3 tools/test/we01c_road_analyzer.py --dump PHONE_LOW.json --dump DESKTOP_HIGH.json --out OUTDIR [--capacity-inventory PATH]`. Validates both dumps with `validate_dump`, recomputes `static_fingerprint` (same compatibility key as T-016B: BASE + both fingerprints + `we01a-1.0` + schema + `polygon_revision`; `file_sha256` is never the key). With `--capacity-inventory`, records its SHA-256 and rejects an inventory whose BASE/fingerprints/`polygon_revision`/analyzer version differ; without it the T-016B source fields are `null`.
- Output `road_survey.json` (deterministic, sorted keys, 3 decimals), at least the draft's section 11 list plus: `analyzer_version = "we01c-1.0"`, `road_schema_version = 1`, `t016b_analyzer_version`, per-road state/reasons/advisories, `beach_encroachment_m2`, `dependency_chains`, `junctions` (point, kind, heights, evidence), and `candidate_corridors`: the list of corridors of `CONDITIONAL_VERIFIED` roads in **the same dict format as `corridors_from_graph`** (`id`, `segment_id`, `category`, `polygon`, `bounds`, `is_rect`, `connectivity`, `existing`, `is_roundabout`) with `existing: false` and `connectivity: "VERIFIED"`, so T-016D can feed them to T-016B `evaluate_access` (which then never produces `existing_only = true`). Roads in any other state are listed under `excluded_roads` with reasons and are never output as corridor sources. No SVG, no markdown report in this task.
- Module-level names T-016D may import read-only: `ANALYZER_VERSION`, `ROAD_SCHEMA_VERSION`, `CANDIDATE_ROADS`, `build_centerline`, `sample_grades`, `build_corridor`, `evaluate_road`, `build_candidate_graph`, `evaluate_region_access`, `analyze`, `main` (signatures are the implementer's, documented in the PR).

## 4. Tests (all in `python3 -B tools/test/we01c_road_analyzer_check.py`, <= 10 s)

- Draft R01-R18 (merge into fewer test functions if wanted, no assertion dropped) plus the inherited road tests (B13-B16, C01-C05, C07, C18).
- Added by Claude: grade boundary (6.0 passes, 6.001 fails) on a synthetic slope; synthetic cases for G0-C4 (exact vs conservative obstacle, street furniture advisory), G0-C5 (overlap within `J` allowed, beyond `J` blocking), G0-C6 (0.5 m elevation tolerance, missing height), G0-C7 (alternative chains, failing road not affecting others, AVE110 attached only to the optional link), G0-C8 (all four verdict names on synthetic regions), G0-C10 (beach area reported, no failure); agreement with `build_road_graph` on the existing network (same main component on the real sample); candidate corridor dict format equals `corridors_from_graph` keys.
- Mutants that must be caught (draft list plus): junction-overlap zone unlimited; BUILDING overlap ignored; conservative-AABB obstruction treated as `NOT_FEASIBLE`; verdict derived from parcel counts; candidate corridor marked `existing: true`; beach treated as failure; step grade replaced by average grade.
- Real-sample runs (small, in the check script): `tools/fixtures/we01/sample_roads_phone_low.json` + `sample_roads_desktop_high.json` (six corridors, RIB_0, CRS_880, AVE_-240, CRS_-720, HILL_ROAD/TRD_0 duplicates) and `sample_b3mid_*` (U01). Do not edit fixtures. Region verdicts on the tiny sample regions are tested only as properties; the three-scenario verdict table on the formal dumps is Claude's check.

## 5. Claude's verification (Gemini does not run these) and gates

On the formal D-051e dumps (PHONE_LOW `e473d222...`, DESKTOP_HIGH `52653bc5...`): run time <= 60 s and B+C cumulative recorded (expected far below), independent re-measurement of the six roads (fillet, step grades, corridor overlaps, junction legality, own graph and chains), independent region verdicts for all nine scenario-regions, `road_survey.json` completeness and determinism (three runs, two loads), mutation sweep of my own, CI wiring (Claude only), main-protection re-check, production integrity (no `index.html`/`sw.js`/CACHE change). Gates: B4 main, plus re-check of the applicable B1, B6, B7, B9. B5, B10, B11 and the final B8 stay with T-016D.

## 6. Out of scope

Internal streets, new parcel placement, `C_conditional`, final 25 ha / 40 / 60 verdicts, final D3, final `world_survey.svg`, final world-expansion report, any production, extractor or fixture change, any generation or verification of the AVE110 extension. A passing T-016C is not a residential feasibility verdict. T-016D needs its own G0 (open items from `WE-01_v1.4_G0_rereview.md`: candidate budget 1,024 filtered to the scenario polygon, line budget, performance) and Martin's approval.
