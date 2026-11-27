# T-016B — WE-01B Parcel Capacity Analyzer: registered specification and Claude conditions

**Registered by Claude 2026-11-27 (D-052).** Approved by Martin ("批准", 2026-11-27 13:46) for **T-016B only**: WE-01 v1.2 + v1.3 amendment + v1.4 amendment + v1.4 Errata E1-E3 (T-016B), with the REVISED-v2 polygons. T-016C (roads) and T-016D (internal streets, conditional capacity, final verdicts, final SVG/report) are **not** registered or approved.

## 0. Source documents and precedence

Gemini reads all of these (they are the specification; this file only adds binding conditions):

1. `specs/WE-01-spec-v1.2.md` (base; sections 6, 7, 14.2, 15-18 apply to T-016B as listed below).
2. `specs/WE-01-v1.3-amendment.md`
3. `specs/WE-01-v1.4-amendment.md`
4. `specs/WE-01-v1.4-errata-T016B.md`
5. This file (Claude conditions, wins on any conflict).
6. `tools/fixtures/we01/SCHEMA_NOTES.md` (dump schema notes, fixtures).

Precedence on conflict: this file > errata > v1.4 > v1.3 > v1.2. Explicit supersessions that matter:

- Scenario `REVISED` uses the **REVISED-v2** polygons of v1.4 section A (v1.3 REVISED coordinates are obsolete and must be rejected by B23).
- Road access distance is **2.0 m** (v1.4 section B) and contact length **8.0 m**; v1.3's 1.0 m is obsolete.
- `C_conditional` is the literal string `"PENDING_T016D"` (not `PENDING_T016C`) in every output and test.
- Anything in v1.3/v1.4 that belongs to T-016C or T-016D (candidate road curves, internal streets, final 25 ha / 40 / 60 verdicts, D3, final SVG, tests C01-C18, M-C01-M-C09) is **out of scope** for T-016B.

## 1. Scope, allowlist, budget

- Implementer: Gemini (Stage 3, per-task exception continues, D-052). Reviewer: Claude. Risk LOW, volume SMALL.
- Branch `gemini/T-016B-we01b-capacity-analyzer`, base = latest `main` at start (Claude gives the SHA in the prompt).
- Only two new files: `tools/test/we01b_capacity_analyzer.py` and `tools/test/we01b_capacity_analyzer_check.py`. Python standard library only. No change to any existing file (WE-01A files, fixtures, production, `sw.js`, CI, docs, specs).
- Lines (both files combined): **revised by Martin 2026-11-27 (D-052a): hard ceiling 1,600** (was 1,050); progress report at about 1,300 lines and before finishing; over 1,600 -> stop and return to Claude. No compression of code, no weakened or deleted tests to fit. (Original: target 900, ceiling 1,050.) Progress reports at about half progress and before finishing (errata E3.3). 
- Allowed imports from `we01a_land_analyzer`: `validate_dump`, `compute_static_fingerprint`, `poly_bounds`, `poly_area`, `is_axis_rect`, `clip_poly_to_rect`, `fp_intersects_cell`, `sample_height`, `slope_class_from_pct`. Nothing else (no underscore functions).
- The check script may additionally import (read-only) `make_dump`, `_rect`, `_fp`, `_write_dump`, `_expect_fail` from `we01a_land_analyzer_check` (it has a `__main__` guard). It must not change that file.
- Never commit dumps, generated outputs, `__pycache__`, browser caches. Run with `python3 -B`.

## 2. Frozen scenario table (D-052) and conventions

Spec order `[xmin, xmax, zmin, zmax]`; analyzer-internal order `[xmin, zmin, xmax, zmax]` (the order used by `we01_extract.js`, `regions[].initial_polygon` rectangles and the `we01a_*` helpers). Convert explicitly with `spec_to_internal` / `internal_to_spec`.

| Scenario | B1 | B2 | B3 |
|---|---|---|---|
| INITIAL | [90,390,930,1230] | [-900,-500,820,1070] | [-640,-340,-810,-610] |
| ENVELOPE | [-10,490,830,1330] | [-1000,-400,720,1170] | [-740,-240,-910,-510] |
| REVISED (`polygon_revision = 2`) | [-10,390,880,1330] | [-950,-450,770,1120] | [-640,-240,-860,-710] |

Areas: INITIAL 250,000; ENVELOPE 720,000; REVISED 415,000 m2 (180,000 + 175,000 + 60,000). INITIAL and REVISED are inside ENVELOPE (B23 asserts it). Gemini never changes, moves or optimizes these polygons.

Evidence recorded by Claude (WE-01A common L0, 5 m conservative, D-051e, **not** capacity): REVISED L0 B1 136,700 / B2 155,500 / B3 25,975 = 318,175 m2; INITIAL 170,575; ENVELOPE 401,000.

## 3. Binding definitions (resolve ambiguity; the real-data oracle depends on them)

3.1 **Raster.** One 1 m raster per scenario x region x preset. Cell `(i, j)` covers `[x, x+1] x [z, z+1]` with integer lower-left corner. A cell is *blocked by a footprint* iff the imported `fp_intersects_cell` says the footprint intersects it (same convention as WE-01A, so zero-area planes and tangency behave identically and invariant B22 holds by construction). Use compact arrays (`bytearray`, `array('i')`); no Python list-of-lists grids.

3.2 **Base-free mask (B22).** A cell is free iff: inside the scenario polygon; not blocked by any footprint of the union of both presets (obstacles = union); not water, not beach (L3), not protected (Site A); inside the confirmed physical ground; required data present. The base mask applies **no** slope, access or prototype rule. Invariant B22: for every cell listed in `tools/fixtures/we01/we01a_common_l0_cells.csv` (5 m cell centre +/- 2.5 m; its 25 1 m cells), all 25 are free in the base mask for the scenarios that contain them; and per region the base-free area is >= the WE-01A common L0 area in the same range.

3.3 **Parcels.** Prototype parcel dimensions are the v1.2 section 7.1 values (all even). Candidate centres are integer `(cx, cz)`; orientations 0 and 90 degrees; the parcel is the union of the whole 1 m cells it covers. Every parcel is entirely inside the scenario polygon (the whole parcel rectangle, never only its centre; v1.4 H.2).

3.4 **Slope (S0).** Slope at a grid vertex = `100 * hypot(gx, gz)` with central differences on the 1 m grid and one-sided differences at the grid edge (identical to WE-01A's convention; implement locally, do not import the private helper). A parcel is S0 iff every vertex in the closed parcel rectangle is <= 5.0 % (`slope_class_from_pct`). Any vertex with missing height -> `UNVERIFIED`. A parcel with any vertex in S1-S3 and none above 30 % is `FOUNDATION_REQUIRED` (recorded as a conditional candidate with reason `SLOPE_S1..S3`, never in `geom_valid`, never in `C_direct`); any vertex > 30 % -> excluded. Read heights straight from the grid arrays (`index = iz * nx + ix`); use `sample_height` only for spot checks.

3.5 **Layer 1 `geom_valid` (errata E1.1).** Per scenario, region, preset, prototype and orientation: a `bytearray` over candidate centres, true iff the whole parcel is free (3.2), S0 (3.4), physically supported, in the scenario polygon, and all required data are present. It contains no road-access condition. The cross-preset mask is the AND of the two preset masks computed from the union obstacles / intersection usable rule (v1.3 R5). Compute each mask once (v1.3 R10); occupancy queries use prefix sums (O(1) per rectangle).

3.6 **Layer 2 road access (errata E1.2).** `evaluate_access(parcel, corridors)` is separate from layer 1 and takes a replaceable list of corridors. A corridor is a polygon from the dump with an id (ROAD footprints, SIDEWALK footprints; roundabouts never count). For a parcel side, the *contact length* is the length of the part of that side whose Euclidean distance to the corridor region is <= 2.0 m; the side qualifies iff its longest continuous run is >= 8.0 m; runs on different sides or separated runs never add up; corner-only contact never qualifies. Exact interval arithmetic is required for axis-aligned corridor rectangles (B25 asserts 8.0 passes and 7.999 fails); for rotated quads a sampling at <= 0.25 m is allowed provided the contact length is rounded **down** (never overestimated). A parcel that overlaps a corridor is rejected regardless of distance. Result fields: `ok`, `side`, `gap_m`, `contact_m`, `corridor_ids`, `connectivity` (`VERIFIED` | `UNVERIFIED`), `reasons`.

3.7 **Road graph (errata E2, v1.4 C.1).** Nodes are existing segments after deduplication of geometrically identical segments (keep alias map `alias_id -> representative_id`; the representative is the lexicographically smallest id). Only `elevation_type == "GROUND"` segments enter the graph. Edge iff the centrelines intersect in the XZ plane, or an endpoint of one lies within `half_width + 1 m` of the other's centreline (use the half width of the segment being entered). The *main component* is the component containing `AVE_0`. A segment not provably in it has connectivity `UNVERIFIED` and gives no `C_direct`. Do not hard-code the counts (19 / 16 / 12) or the ids of the real dump.

3.8 **Parcel status** values: `DIRECT` (geom_valid + access ok + verified connectivity), `INTERNAL_STREET_REQUIRED` (geom_valid, no qualifying existing road), `FOUNDATION_REQUIRED`, `UNVERIFIED`, `EXCLUDED`. Only `DIRECT` parcels count in `C_direct`. Obstructions proven only by a CONSERVATIVE_AABB footprint may exclude a parcel from `C_direct` but must **not** reduce `C_upper`.

3.9 **Capacity numbers per scenario x region** (v1.2 section 7.7): `C_preliminary` = deterministic greedy count over `geom_valid` ignoring road access; `C_direct` = largest ratio-compliant deterministic layout from `DIRECT` parcels; `C_conditional = "PENDING_T016D"`; `C_unknown` = parcels that would be placeable if UNKNOWN / unverified-connectivity data were treated as free, minus `C_direct` (>= 0; document the definition in the report); `C_upper` = the largest `n` such that the minimum required parcel area `f(n)` fits in `A_possible`, where `A_possible` = polygon cells minus cells **proven** excluded (Site A protection, water, cells fully covered by EXACT_OUTLINE obstacles or roads, cells with all covering vertices > 30 %). `f(n)`: B1 `2016*ceil(n/2) + 1428*(n - ceil(n/2))`; B2 `528*n`; B3 with `m = ceil(0.2*n)`: `m*(1428+528+912) + 528*(n - 3*m)` for `n >= 3m`. Per preset: `C_phone_low`, `C_desktop_high`, `C_common` with `C_p = max(greedy on own mask, |L_common|)` (v1.3 R5). `C_unknown` and `C_upper` never lower than `C_direct`. Ratios (v1.2 section 7.3) use integer ceiling on the final count. Search failure never means NOT FEASIBLE.

3.10 **Areas** (`A_gross`, `A_direct`, `A_conditional` candidate, `A_protected`, `A_unavailable`, `A_unknown`, `A_eligible` candidate): mutually exclusive land classes, conservation error <= 1 m2 per region; `A_eligible` is a derived union, never added again; Site A never counts as eligible land.

## 4. Inputs, CLI, outputs

- CLI: `python3 tools/test/we01b_capacity_analyzer.py --dump PHONE_LOW.json --dump DESKTOP_HIGH.json --out OUTDIR [--land-inventory PATH --land-report PATH]`. The analyzer validates each dump with `validate_dump`, recomputes the static fingerprint, and refuses mismatching BASE / preset sets. Compatibility key = game BASE + both `static_fingerprint`s + WE-01A version `we01a-1.0` + schema + polygon_revision; `file_sha256` of a dump is never the compatibility key. If `--land-inventory` / `--land-report` are given, record their SHA-256 and reject an input whose recorded fingerprints differ.
- Outputs (deterministic, sorted keys, 3 decimals): `capacity_inventory.json`, `parcel_candidates.json`, `capacity_report.md`. Required content: errata G.1 / v1.4 B29 list, handoff block (E1.3), `analyzer_version = "we01b-1.0"`, `handoff_schema_version = 1`, `polygon_revision = 2`, exact parcel lists with ids, prototype, orientation, centre, internal-order bounds, status, access result, terrain result, reasons.
- Real dumps and the formal outputs are produced and reviewed by Claude; Gemini's script must also run on the small real fixtures (3.11).

## 5. Public interface (binding names; internals free)

`we01b_capacity_analyzer` exposes at module level (T-016C/D import them read-only; the two-layer separation is mandatory, errata E1.3):

| Name | Contract |
|---|---|
| `ANALYZER_VERSION`, `HANDOFF_SCHEMA_VERSION`, `POLYGON_REVISION` | `"we01b-1.0"`, `1`, `2` |
| `SCENARIOS` | scenario id -> region id -> spec-order bounds (table in section 2) |
| `PROTOTYPES` | prototype id -> footprint and parcel dimensions, `proxy` flag (R05 in B2 = PROXY) |
| `spec_to_internal(b)`, `internal_to_spec(b)` | explicit conversion of the two rectangle orders |
| `load_dumps(paths)` | `{preset: validated dump}`; enforces BASE and fingerprint rules |
| `build_masks(dump, scenario_id, region_id)` | 1 m raster with prefix sums; exposes `rect_blocked(x0, z0, x1, z1)` and the base-free mask |
| `geom_valid(masks, prototype_id, orientation)` | layer 1 mask (no road access) |
| `build_road_graph(dump)` | graph with `alias_map`, `representatives`, `main_component`, per-segment `connectivity` |
| `corridors_from_graph(graph)` | list of corridor polygons with stable ids for existing verified roads |
| `evaluate_access(parcel, corridors, graph=None)` | layer 2 result of 3.6 |
| `place_layout(valid_by_proto, access_fn, region_id, order=None)` | deterministic greedy; records order and tie-breaking |
| `common_layout(...)` | the R5 algorithm, returns `L_common` and per-preset validation |
| `analyze(dump_paths, out_dir=None, opts=None)` | full run; returns the inventory dict |
| `main(argv=None)` | CLI |

The `opts` hooks used by mutation tests (`M-B*`) follow the WE-01A style (`opts` dict, documented).

## 6. Tests (all must pass in `python3 -B tools/test/we01b_capacity_analyzer_check.py`, <= 10 s on a normal CPU)

- Inherited from v1.2 section 14.2: B01-B09, B11, B12, B17, B18 (script-level part; the full-dump run is Claude's), B20, B21. B08 uses an independent fixed-height oracle; Claude does the live `__th` cross-check (>= 100 samples per preset, error <= 0.01 m).
- v1.3 new: B22-B28. v1.4 / errata: updated B07 (key set of section 4), B23 (frozen table, both rectangle orders, areas and union areas, REVISED inside ENVELOPE, Site A unchanged, v1.3 REVISED coordinates must FAIL), B25 (2.0 m / 8.0 m cases listed in v1.4 B.3), B29, B30 (+ errata E2.5 and E1.4 assertions). B19 report-completeness for the three outputs is covered by B29.
- Mutation tests that must be caught: M-B01, M-B02, M-B03, M-B05, M-B06, M-B08, M-B09, M-B10, M-B11, M-B13, M-B14, M-B15, M-B16. Plus (Claude requirement) mutants for: access baked into `geom_valid`; 7.999 m contact accepted; conservative-AABB obstacle shrunk in `C_upper`; duplicates counted twice; REVISED v1 coordinates accepted.
- Real-sample runs (must pass, small, in the check script): `sample_phone_low.json` + `sample_desktop_high.json` and `sample_b3mid_phone_low.json` + `sample_b3mid_desktop_high.json` (both pairs share fingerprints with the WE-01A fixtures; do not edit them).

## 7. Claude's verification (Gemini does not run these) and gates mapping

On the formal D-051e dumps: run time <= 60 s (v1.2 Gate B6; explicit exception only if Martin approves), B22 on the 16,040 common L0 cells, independent re-placement check of every `DIRECT` parcel (geometry, S0, access, overlaps, both presets), >= 100 live height samples per preset, independent oracle for `C_upper`, mutation sweep of my own, CI wiring of the check (Claude only), main-protection re-check on the review, production integrity (no `index.html` / `sw.js` / CACHE change). v1.2 gates covered at this stage: B1, B2, B3, B6, B7, B9, B12 (B4 roads -> T-016C; B5, B10, B11 -> T-016D; B8 baseline -> final task).

## 8. Out of scope / not authorised

No residential, road, terrain or art construction; no production change; no candidate road curve analysis, no internal streets, no final feasibility verdict, no final SVG (T-016C / T-016D). A passing T-016B is **not** a feasibility result. T-016C and T-016D need their own G0 (open items C1-C3 of `WE-01_v1.4_G0_rereview.md`: line-budget split, 1,024 candidate budget, performance), approval and registration; T-016C starts only after T-016B is merged and accepted by Martin.
