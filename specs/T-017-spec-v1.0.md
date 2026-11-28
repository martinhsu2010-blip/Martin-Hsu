# T-017 - WE-02 World Expansion Masterplan (spec v1.0)

Entry-point spec. ChatGPT draft: `specs/T-017-draft-v1.1-chatgpt.md` (verbatim; v1.0 draft `specs/T-017-draft-v1.0-chatgpt.md`). Claude G0 reviews: `specs/T-017-g0-review-v1.0.md`, `specs/T-017-g0-rereview-v1.1.md`. Where this file and the draft differ, this file wins. WE-01 results (D-057, D-060) win over any draft number.

## 1. Decisions and scope
- Martin ("批准", 2026-11-28 19:20, in reply to Claude's request to confirm Option B / ENVELOPE as the planning direction and to approve the complete WE-02 v1.1 together with Claude conditions G0-W1..W7) approved this specification (D-061).
- Documentation and offline artifact tooling only. NOT authorized: any change to `index.html`, `sw.js`, `CACHE`, `vh_save`, game roads, houses, terrain, world boundary or buildings; changing a WE-01 verdict; WE-03..WE-09; construction; using headless FPS as device performance.
- Roles: ChatGPT = design owner (revisions of the draft); Claude = produces, verifies and registers `specs/we02/`, owns `tools/we02/`; Martin = approval and final acceptance (MP17). No Codex/Gemini assignment.
- Base: main after the registration PR. Audit Game BASE `84319439243b51aa8d119e33eb62a0637feea887`.

## 2. Deliverables (draft section 15)
`specs/we02/`: `masterplan.md`, `district_plan.json`, `masterplan.svg`, `dependency_matrix.md`, `we02_validation.md`. Gates MP01..MP18 of the draft apply, strengthened by section 3 below.

## 3. Claude conditions (G0-W1..W7; they win over the draft)
- **G0-W1 Area method.** WE-01 land areas are integer counts of 1 m raster cells (e.g. `A_new_road` 8,013), not exact polygon areas. MP12 uses the same raster rule as WE-01D (`fp_intersects_cell`, stdlib), reports exact-polygon values beside it with the difference explained, and the conservation error <= 1 m2 is judged on raster values. Phase road areas are recomputed per phase and region as unions (overlapping corridors are never added).
- **G0-W2 Phase 2 street choice is deterministic.** ST_0085 and ST_0115 are symmetric in the data (both give R01 7 / R02 7 with equal corridor union area). Rule: choose the street that adds the smaller raster area; tie -> lexicographically smaller `street_id`. The chosen id and the rule are recorded in `district_plan.json`. Phase 2 contains the Phase 1 selection unchanged.
- **G0-W3 Generator and verifier are separate.** `tools/we02/` contains a generator, a separate verifier (independent code path, as `e_verify.py` was for T-016E) and a check script with negative controls (tampering must turn red, per MP). Claude wires the check into `.github/workflows/pwa-cache-check.yml`. The final artifacts are also given to ChatGPT for a read-only consistency review before Martin's acceptance.
- **G0-W4 Line ceiling.** Combined <= 2,000 lines (generator <= 900, verifier <= 600, check <= 500). Python stdlib only, deterministic output, source hashes recorded; stop and report at any ceiling.
- **G0-W5 Buildings and units.** Targets are buildings. Reports show buildings and units: R08 is one building and four units, so Phase 1 B3 18 buildings = 30 units and Phase 1 total 40 buildings = 52 units. No unit count is used to satisfy a building target.
- **G0-W6 B1 Phase 1 has zero margin.** X01 + ENVELOPE_B1_ST_0305 give exactly R01 5 (2 direct + 1 X01 + 2 ST_0305) and R02 8. If any of those R01 parcels later fails engineering verification, B1 Phase 1 needs C02 (224 m2 beach encroachment) and one more street. Recorded in the unresolved dependencies.
- **G0-W7 Geometry contract.** In the formal data every parcel has orientation 0 or 90 (22 parcels at 90), so each parcel polygon is exactly the rectangle `bounds` ([xmin, zmin, xmax, zmax]); area = width x depth for every parcel. The verifier checks polygon overlap against that rectangle, against the corridor polygons of the roads built in that phase, and against Site A (X [-561,-441], Z [-831,-753]). Region tables in text use the spec order [xmin, xmax, zmin, zmax]; JSON keeps the original field semantics.

## 4. Pre-computed references (Claude G0 on formal e_formal data; verify, do not hard-code)
- Phase 1: B1 = 5 direct (R02 3, R01 2) + 1 X01 R01 + 2 ST_0305 R01 + 2 ST_0305 R02 -> R01 5 / R02 5; B2 = 12 of the 24 parcels that depend only on H02; B3 = R01 4 / R05 10 / R08 4 from the 25 direct parcels. Roads: X01 362.908 + H02 597.306 + ST_0305 150 = 1,110.214 m, beach encroachment 0.
- Phase 2 (cumulative): B1 R01 7 / R02 7 via X01 + ST_0305 (Phase 1) plus C02 and one of ST_0085/ST_0115 (+280 m, cumulative 1,390.214 m, beach 224 m2); B2 18 (H02 only); B3 cannot reach 28 (R01 5/6, R05 15/16, R08 5/6; short 3), stays UNVERIFIED.
- No selected parcel overlaps another, a built corridor or Site A; no dependency chain contains C01 or H01.
- Exact-polygon corridor unions (informational): Phase 1 B1 5,576.7 m2, B2 7,158.3 m2; Phase 2 B1 8,596.2 m2.

## 5. Process
- Claude builds `tools/we02/` and the artifacts in small docs/tools PRs (not Gemini/Codex), runs the independent verifier and negative controls, then asks ChatGPT for the read-only review and Martin for MP17 acceptance. A passing MP01..MP18 never turns WE-01 D3 into FEASIBLE.
