# T-011 spec v1 — Midtown West fast-travel QA entry

**Status:** PROPOSED — NOT Martin-approved. **Author:** ChatGPT. **Project:** VICE HORIZON VI.

**Repository:** `martinhsu2010-blip/Martin-Hsu`  
**Baseline `main`:** `965c90e98e5e34d06345d1e97a1a984556fcb6b7` (2026-11-22; verify and re-record latest `main` before starting).  
**Risk:** LOW. **Volume:** SMALL. **Implementer:** **Codex** (Martin's explicit assignment; a tightly bounded existing-data/UI change, despite Gemini being the routine low-risk UI implementer). **Reviewer, integrator, releaser:** Claude.  
**Dependency:** T-010 façade pilot has been merged/released (`ae3951a`, `vh-2026-11-22-06`), but `TASKS.md` currently records **Martin device acceptance pending**. Do not start this code task until the shared PR lock is free **and** the previous task has completed the required Martin acceptance gate.  
**Proposed branch:** `codex/T-011-midtown-west-travel` → PR to `main`. **One task, one implementer, one code PR.**

## 1. Goal and non-goals

Add one convenient **Midtown West** fast-travel destination to inspect the *east-facing façades* of the six T-010 pilot buildings from the avenue immediately east of their block. It must be selectable through **both** the World Map fast-travel chip/list and the **Missions & fast travel** modal.

This is a location/UI data addition only. **Not in scope:** modifying `teleportTo`, `snapToRoad`, `fastTravelTo`, driving/vehicle physics, collision bodies, building positions/geometry, world generation, road/traffic/AI, map interactions, camera logic, save data or schema, renderer/scene meshes, draw calls, delivery rules, quality settings or assets. No new network resources or runtime dependencies.

## 2. Source-verified interface and exact content

At baseline, `index.html` contains:

- Bilingual `VH_I18N` string tables, with English keys near line 140 and Traditional Chinese keys near line 470.
- Shared `FAST_TRAVEL` array near line 10005, whose entries use `{ id, get name() { return tr('...'); }, icon, x, z, h }`.
- `setupWorldMap()`, which **automatically** creates World Map chips from `FAST_TRAVEL`, and `drawWorldMap()`, which paints their map markers.
- A **separate, static** `Missions & fast travel` HTML button list (`.tp-btn[data-tp]`, near line 1185) wired to the same `FAST_TRAVEL` entries. **Adding an array item alone does not place a button in this modal.**
- Existing `fastTravelTo(t)` guards against `DELIVERY.job` and forwards `t.x, t.z, t.h` to `teleportTo()`. Neither function is to be modified.

Required new values (exact, case-sensitive):

| Property | Value |
|---|---|
| `id` | `MIDTOWN_W` |
| `icon` | `🏢` |
| i18n key | `midtown_west` |
| English | `Midtown West` |
| Traditional Chinese | `中城西側` |
| Target position | Avenue at approximately `(x=-240, z=-300)`; **candidate** `(-235, -300)` |
| Heading | Face **west** toward the buildings' east faces: **`h = -Math.PI / 2` radians** |
| Height | Ordinary ground-level travel; omit optional `y` (use existing `teleportTo` terrain-height behavior) |

The T-010 pilot block has building centers satisfying `-420 < x < -240` and `-360 < z < -240`. Its enhanced faces point east, toward the `x=-240` avenue. `ROAD_NET.avenuesX` includes `-240` and `avenueHalf=12`. The existing `snapToRoad(-240,-300)` is expected to provide a candidate on the avenue's **east side**, around `(-235,-300)`, but **that is a prediction, not a verified live-world landing**.

**Implementer must determine and report final exact `(x,z,h)` from the actual runtime**. Inspect `snapToRoad`'s output and the existing `fastTravelTo` → `teleportTo` path; verify that the chosen fixed coordinates are on the paved roadway, outside all **actually placed** building footprints, and leave the car/person facing west after teleport. For a changed coordinate, remain on the `x≈-240` avenue within `|z+300|≤15` and within `|x+240|≤10` (avoid the `z=-360` and `z=-240` intersections). If no safe, west-facing point exists within this bounded area, **stop and request a spec revision**; do not alter the road, buildings or teleport machinery.

## 3. Implementation boundary

1. **`index.html` i18n:** add precisely `midtown_west` to **both** `en` and `zh-TW` tables, with the strings above. Do not rename any old key or change existing translations.
2. **`index.html` FAST_TRAVEL:** append exactly one item with unique `id: 'MIDTOWN_W'`, dynamic `get name() { return tr('midtown_west'); }`, icon `🏢`, the verified fixed `x,z`, and `h: -Math.PI / 2`. Leave all pre-existing items unchanged, including ordering and headings.
3. **`index.html` Missions modal:** add exactly one `.tp-btn` with `data-tp="MIDTOWN_W"` and a visible icon `🏢` and localized `midtown_west` label, using the existing styles and listener. Since language changes replace text of `[data-i18n]` elements, **keep the emoji separate from the `[data-i18n="midtown_west"]` label** so the icon remains visible after language switching. Do not change the event handler or any pre-existing button.
4. **No new WebGL object:** the new World Map icon is drawn by the **existing canvas map code**; it is not a new Three.js mesh. Existing render calls, 3D geometry, Cannon bodies/shapes and `vh_save` state must be unchanged.
5. **File allowlist:** `index.html` and a single new failure-capable test `tools/test/midtown_west_travel_check.mjs`. No other production/test files. In particular, no `sw.js`, `specs/`, `TASKS.md`, `DECISIONS.md`, `LOG.md`, `.github/`, binary assets or cache edits by Codex. Claude alone handles documentation, CI wiring and release/cache updates via the approved process.

## 4. Verification and acceptance

### 4.1 Automated regression — `node tools/test/midtown_west_travel_check.mjs`

Reuse a repo-provided harness, where practical, and evaluate **actual production** data/functions rather than a hand-written mock copy. The test must contain failing assertions for each item below:

- **Identity and translations:** exactly one `FAST_TRAVEL` entry has `id === 'MIDTOWN_W'`; its icon is `🏢`, its dynamic name resolves exactly to `Midtown West` in `en` and `中城西側` in `zh-TW` (not an untranslated key). Both i18n tables actually contain `midtown_west`.
- **Two entry points:** the World Map's shared `FAST_TRAVEL` source includes the entry, and the Missions modal contains exactly one `.tp-btn[data-tp="MIDTOWN_W"]` with an i18n-bound name and visible `🏢` icon. The button's ID must resolve to the real entry, not the `FAST_TRAVEL[0]` fallback.
- **Safe coordinates:** the entry's actual fixed `x,z,h` are finite, within the bounded Midtown test corridor from §2, with west-facing heading (`-π/2`, numeric tolerance `1e-6`). For at least **PHONE_LOW** and **DESKTOP_HIGH** world profiles, obtain real placed `WORLD.cityInfill`/`WORLD.roofs` parcels (not just unplaced `CITY_COVERAGE_LOTS` candidates); assert the point is **not inside any building parcel**, using each parcel's `x,z,w,d` footprint. Evaluate or invoke actual `snapToRoad` to confirm it lies on the intended paved avenue, with a snap displacement **≤ 6 m**. If a profile cannot be evaluated with the harness, report the blocker; do not silently skip the assertion.
- **Existing entries unchanged:** compare all original `FAST_TRAVEL` entry IDs, positions, headings and icons with the baseline revision (via `git show <base>:index.html` or an equivalent genuine baseline evaluation). Exactly one entry may be added; no existing item may disappear, move or change. No extra `vh_save` fields or CANNON objects may be introduced.
- **Mutation sensitivity:** demonstrate at least **two** temporary failures, e.g. remove `midtown_west` from `zh-TW` → FAIL, and change `MIDTOWN_W.x` to a known building center → FAIL. Do not commit mutations and do not relax existing test assertions.

If the harness needs access to private `FAST_TRAVEL`, `snapToRoad` or `CITY` internals, evaluate the same production source with the existing VM/Three.js harness rather than modifying `window.__VH` unnecessarily. Keep the test scoped and reviewable.

### 4.2 Required existing checks

Codex runs, and Claude independently checks, all required `AGENTS.md` commands on the code PR:

```text
python3 tools/test/syntax_check.py
python3 tools/test/i18n_check.py
node tools/test/i18n_check.mjs
node tools/test/hud_check.mjs
node tools/test/camera_check.mjs <actual-base-main-SHA>
node tools/test/traffic_check.mjs
node tools/test/collision_check.mjs
node tools/test/suburb_check.mjs
node tools/test/urban_check.mjs
node tools/test/route_legality.mjs
node tools/test/midtown_west_travel_check.mjs
```

All required checks must pass; report real command output or failures honestly. Do not weaken prior checks. Claude wires the new test into `.github/workflows/pwa-cache-check.yml` in its own integration/release PR and verifies the CI step actually runs and passes.

### 4.3 Browser / device acceptance

In a real browser, check `en` and `zh-TW`, and confirm the new label/icon appears in **both** the World Map and Missions & fast travel menu. Test selecting the destination in **on-foot and vehicle modes**: it must reach the verified road coordinate, face west toward the façades, avoid building/collision overlap, and create no console/runtime error. After language switching, both destinations' labels update and icons remain visible.

With an active delivery job, **both** entry points must retain the existing blocked-fast-travel behavior; no teleport is allowed and no delivery state changes. Confirm at least one older destination still works and all existing entries remain present. No unexpected change in 3D draw calls or body/shape counts; this task does **not** require a new physics/render benchmark because it does not alter those systems. Martin's S26 Ultra/Tab S11 usability check is recommended after release; device FPS can only be recorded if actually measured.

**Acceptance criteria:** A1–A5 automated assertions pass; A6 both menus and both languages visible; A7 successful on-foot + car teleport with final `(x,z,h)` reported; A8 delivery remains blocked; A9 original entries and full AGENTS suite pass; A10 no physics/world/save/draw-call change, no new offline dependency, CI/new test wired; A11 Claude review + Martin device acceptance according to COLLAB v3.6 workflow.

## 5. Stop rules, ownership and risks

- Risk LOW, volume SMALL applies **only while changes stay within `FAST_TRAVEL`, two i18n entries and one static Missions button**; changing physics, collision, road geometry, renderer or world generation is **not approved** and requires a new review/spec under the relevant risk gates.
- Do not guess that `(-235,-300)` is collision-safe merely because it is near a road. Confirm the runtime snap, actual building parcels and final orientation; if blocked, stop and return evidence for a spec amendment.
- A zero-body/shape and unchanged-world check is an invariant; the task creates no scene decoration or new runtime asset.
- On any failing test, unsupported environment, inaccessible baseline, unapproved diff, or inconsistent menus, Claude requests corrections; no merge before requirements pass. Claude checks D-013 branch protection and the single active code-PR lock. PR/code review ≤ 2 correction rounds before escalation to Martin.
- The T-010 spec previously mentioned a **future** T-011 façade rollout only as roadmap text. **This spec explicitly repurposes T-011 for the fast-travel QA entry**, as Martin requested; no facade rollout is authorized by T-011.

## HANDOFF ChatGPT -> Claude

```text
HANDOFF ChatGPT -> Claude
Task: T-011-spec-v1 — Midtown West fast-travel QA entry
Status: PROPOSED — NOT Martin-approved
Repo: martinhsu2010-blip/Martin-Hsu
Baseline main: 965c90e98e5e34d06345d1e97a1a984556fcb6b7
Read: COLLAB.md v3.6, AGENTS.md, TASKS.md, DECISIONS.md,
      specs/TEMPLATE.md, specs/T-010-spec-v1.1.md
Implementer: Codex; Risk: LOW; Volume: SMALL
Dependency: T-010 released, Martin device acceptance still pending
Scope: one FAST_TRAVEL entry (MIDTOWN_W), two i18n strings,
       one Missions modal button, and one failure-capable test.
Source finding: World Map auto-generates chips from FAST_TRAVEL;
                Missions menu needs its own static data-tp button.
Location: candidate (-235,-300), west h=-PI/2; Codex must verify
          actual snapToRoad, paved surface, parcel clearance and
          report exact final coordinates/heading.
Review: tests must detect missing translation and building overlap;
        old destinations unchanged; delivery block preserved.
Claude owns: spec review, Martin approval request, docs-only
             registration, independent review, CI wiring, release.
Do not register or start a code PR without Martin's explicit
approval of T-011 v1 and completion of the previous-task gate.
SPEC: attached T-011-spec-v1.md
```
