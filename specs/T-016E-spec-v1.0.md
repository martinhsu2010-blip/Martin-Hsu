# T-016E - WE-01E Final survey map and report builder (spec v1.0)

Entry-point spec. ChatGPT draft: `specs/T-016E-draft-v1.0-chatgpt.md` (verbatim). Where this file and the draft differ, this file wins. Approved A/B/C/D specs and D-051..D-057 win over earlier drafts. Request that produced the draft: ChatGPT E1-E10 (Claude, 2026-11-27).

## 1. Decisions and scope
- Martin ("批准" scope = start preparation, 2026-11-27 22:47; question card 2026-11-28): line ceiling combined 1,300 (builder <= 800, check <= 500); geometry via a small Claude-extracted `map_geometry.json` (builder never reads dumps). Registration itself still needs Martin's explicit "批准".
- Read-only artifact builder. New analysis, re-computation of any audit number or verdict, runtime measurement, construction, production change, CACHE bump and WE-02..WE-09 are NOT authorized.
- Base: main after the registration PR; Gemini confirms the SHA at start. Branch `gemini/T-016E-we01e-report-builder`.

## 2. Allowlist and lines
- New: `tools/test/we01e_report_builder.py` (<= 800), `tools/test/we01e_report_builder_check.py` (<= 500), combined <= 1,300. Python stdlib only. Nothing else (A/B/C/D, fixtures, extractor, game, CI, docs untouched).
- Report at about 600 combined lines and before finishing (both file sizes, tests done, projected total). Stop and return to Claude at any ceiling. No compression of tests or report content.

## 3. Inputs (G0-E2, G0-E3)
- CLI: `python3 -B tools/test/we01e_report_builder.py --input-dir DIR --out DIR`, plus `--help`. No `--dump`.
- DIR holds exactly these nine files (Claude fixtures in `tools/fixtures/we01/e_formal/`, produced by `tools/we01/we01e_geometry.py` and the formal runs): `land_inventory.json` (A), `capacity_inventory.json`, `parcel_candidates.json` (B), `road_survey.json` (C), `internal_streets.json`, `conditional_parcels.json`, `feasibility.json` (D), `map_geometry.json` (roads, Site A, beach, water; BASE + both static fingerprints; geometry identical across presets), `inputs_manifest.json` (file -> SHA-256).
- Verify before building: manifest hashes, BASE, both static fingerprints, polygon_revision 2, schema versions, D `sources` hashes equal the B/C file hashes, scenario/region ids and cross-file parcel/road references, `deterministic_sha256` fields present. Any failure or missing field: non-zero exit, no formal output files (write to a temp directory, then rename; never default a missing number to 0). The check must also accept a legitimate synthetic variant and reflect its new values (M-E02 case 2).

## 4. Authority and presentation (G0-E4, G0-E5)
- D: final layouts, streets, conditional capacity, land accounting, verdicts. B: C_direct, C_preliminary, C_upper. C: road self-verdicts and geometry (a road excluded in a D layout keeps its C state and is shown with both). A: land classification context. `C_conditional = PENDING_T016D` in B/C files is historical and never displayed as a result.
- No arithmetic that yields an audit number; formatting only (thousands separators, fixed decimals, units).
- Real-data traps the report and tests must handle: (1) buildings vs units (REVISED B3 `C_conditional` 17, `units_conditional` 29: R08 rows are four units, one building); (2) `A_eligible` vs `A_eligible_final` are different fields (REVISED totals 323,715 vs 305,858): show the exact field name; (3) the C01 exclusion (conflict B1_R02_005) is per scenario and exists in ENVELOPE and REVISED, not INITIAL; (4) all five verdicts per scenario are shown with reasons (INITIAL: land_25ha and D3 and buildings_60 NOT FEASIBLE WITHIN AUDITED BOUNDARIES, buildings_40 UNVERIFIED, road CONDITIONAL; ENVELOPE D3 CONDITIONAL; REVISED land CONDITIONAL, buildings_40/60 and D3 UNVERIFIED); (5) targets (10/12/18, 14/18/28, 250,000 m2) are read from the D JSON, never written in code; (6) B2 proxy (`proxy_used`) is labelled PROXY; (7) H01 NOT_FEASIBLE, GRADE_LIMIT_EXCEEDED, max step grade read from `road_survey.json`; (8) beach encroachment per road and total; AVE110 only as optional unverified; (9) B3 wording limited to "search insufficient, not proven impossible"; 60-building target never described as a D3 requirement.
- These values are acceptance references, never constants in the builder.

## 5. SVG (G0-E6)
- One static file `world_survey.svg`, UTF-8, plain XML: REVISED primary section, INITIAL and ENVELOPE secondary sections, each with B1/B2/B3 panels; own scale bar per panel; +X right, +Z down, no compass or north claim; axes, legend, BASE SHA, both static fingerprints, preset marker (CROSS_PRESET_COMMON), polygon_revision, scenario id, data sources, audit-versus-schematic note. Suggested viewBox about 2400x2000 (layout, not data).
- Layers: existing roads, candidate external roads, selected internal streets, rejected/excluded roads (C01 in ENVELOPE/REVISED, H01 failed route), DIRECT and CONDITIONAL parcels with true ids (short label on the map, full id in `<title>` and in the report appendix), Site A protection and buildings, beach, water. No UNKNOWN polygon exists in the data (A_unknown = 0): show as a panel note, never invent a shape. Different line styles or hatches, not colour alone; unbuilt roads are always labelled candidate or conditional.
- Never: script, event handler, foreignObject, DOCTYPE, external entity, image, font, stylesheet or URL reference; duplicate ids. Tests parse visible `<text>`/`<title>` with an independent XML parser; `data-*` attributes may help but are never the only oracle.

## 6. Report (G0-E7)
- `survey_report.md`, Traditional Chinese; identifiers, JSON keys and verdict strings in English. Sections as draft 7.1-7.7, plus an appendix listing every DIRECT and CONDITIONAL parcel per scenario (id, prototype, status, source road, internal street, dependency), plus the fixed paragraph "Gate B8 尚待 Claude 完成正式量測，本報告不代表新增住宅已達效能目標。" with a separate placeholder section for the B8 reference. Follow-up section titled "WE-02–WE-09 後續工程建議（僅為建議，未授權）".
- `report_meta.json` (timing only) is outside every hash. SVG and Markdown contain no timestamps, paths or random ids.

## 7. Tests (G0-E9, G0-E10)
- E01-E20 and M-E01..M-E20 from the draft, plus M-E21 swap `A_eligible`/`A_eligible_final`, M-E22 show `units_conditional` as buildings, M-E23 apply the C01 exclusion to INITIAL, M-E24 display `PENDING_T016D`. All applicable mutants RED. Oracles independent of the builder formatter. Three builds byte-identical (SVG, MD). Full build on the formal inputs <= 10 s (Claude measures).
- Old test ids follow G0-D16 (B19 report/SVG part and C08 -> E; B16 unbuilt roads never EXISTING_VERIFIED -> E07; C10 budget is the approved 1,280, shown from the JSON).

## 8. Delivery order (G0-E12)
E merge -> Claude measures B8 (PHONE_LOW, TABLET_MED, DESKTOP_HIGH; six locations; WE-01 v1.2 sec.13) and writes the B8 appendix (Claude-owned, never a hand edit of the deterministic output) -> Claude B10 (independent SVG/report-vs-JSON comparison, rendering and label overlap, XML/security, 3x determinism, A-D regression, production SHA, D-013) -> Martin B11 with final SVG, report, B8 appendix, feasibility.json. Formal outputs are not committed (precedent D-051d). A passing T-016E is tool acceptance only: not a feasibility result, not WE-01 acceptance, not construction approval.
