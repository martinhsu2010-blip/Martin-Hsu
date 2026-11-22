# Task board (rules: COLLAB.md v3.6). One Owner per task. One active code PR at a time, shared by Codex and Antigravity; each code task carries `Implementer: Codex|Gemini`.

## Gemini qualification
Current stage: 3
Last approved by Martin: 2026-11-21 18:53 ("批准 Gemini 升至階段 3，依 COLLAB v3.5，證據 PR #59、#63", promotion 2 -> 3)
Evidence PRs: #53 (T-006, Stage 1, Martin-accepted); #59 (T-007, Stage 2 #1, Martin-accepted); #63 (T-008, Stage 2 #2, Martin-accepted)
Promotion candidate: none
Rollback / blockers: none. Every Stage 3 task still needs its own Martin-approved spec and the COLLAB v3.5 §4.3 pre-start conditions (per-risk regression tests, quantified acceptance values, Claude-reproducible measurements); the first high-risk task needs a separate test-completeness assessment.

## Ready for ChatGPT
(none)

## Ready for Implementer
(none)

## In review
(none)

## Doing (Claude)
(none)

## Blocked
### T-002 Verify licenses of the Porsche / Lexus / Ford Sketchfab models
Owner: Martin
Priority: P2
Why: archives had no license text; needed before any public sharing.

## Inbox
(none)

## Done
### T-009 Midtown crosswalk pilot (Gemini Stage 3 first task; world/render) (Done; Martin accepted 2026-11-22; FPS not reported)
Owner: Gemini
Implementer: Gemini (Stage 3)
Reviewer: Claude
Priority: P2
Base commit: spec baseline `182a09e227049f99e3b46c4a76e3d27671cc1595` (re-record latest main at start)
Branch/PR: `gemini/T-009-crosswalks` / #71 (merged b729942, released vh-2026-11-22-05)
Spec: `specs/T-009-spec-v1.3.md` (v1.3 replaces the second intersection (-240,-360) with (-120,-360); approved by Martin 2026-11-21 23:26; D-030). Earlier: v1.2 (§6.2 physics gate, D-029) and v1.1 (D-028) stay in force otherwise.
Scope: `index.html` + new `tools/test/midtown_crosswalk_check.mjs` only (optional bench file only if Claude pre-approves). Claude wires the new test into CI at release.
Required Gemini stage: 3
Claude notes: Stage 3 trial verdict PASS (PR comment). 13 AGENTS checks re-run; 11 mutations red; physics medians (cap 1.25) PHONE_LOW 1.186/1.051, TABLET_MED 1.023/1.045, DESKTOP_HIGH 0.966/1.047, bodies/shapes +0; draw calls near +1 on all presets (limits +2/+4/+6), control +0. Martin accepted on devices 2026-11-22 08:36 ("通過"). `?fps=1` numbers for S26 Ultra / Tab S11 were NOT reported: FPS is recorded as unmeasured (spec §6.4), not as passed.

### T-008 Zone Arrival HUD (Gemini Stage 2 task 2 of 2; general HUD behavior) (Done, accepted)
Owner: Gemini
Implementer: Gemini (Stage 2; passive HUD notice using existing zone logic)
Reviewer: Claude
Priority: P2
Base commit: latest `main` at start (spec baseline `af6209d912a773d930a5520d0823d4ff2dedeee4`)
Branch/PR: `gemini/T-008` / #63 (merged 0803a21, released vh-2026-11-21-04)
Spec: `specs/T-008-spec-v1.md` (approved by Martin 2026-11-21 17:58; D-025).
Scope: `index.html` + new `tools/test/zone_arrival_check.mjs` only. Claude wires the new test into `.github/workflows/pwa-cache-check.yml` at release (A11).
Required Gemini stage: 2
Claude notes: Stage 2 task 2 verdict 通過 (PR comment). Claude re-ran all AGENTS checks + route_legality + both new tests; 6 independent mutations fail the test; headless real-teleport checks at 390x844, 844x390, 1280x800; no spawn popup; CI step wired and passed; D-013 re-checked 2026-11-21 10:49Z. Not device-measured. Martin accepted on his devices 2026-11-21 ("通過").

### T-007 Game Hub WORLD "Next Stop" card (Gemini Stage 2 first trial) (Done, accepted)
Owner: Gemini
Implementer: Gemini (Stage 2 trial; single small non-persistent UI feature)
Reviewer: Claude
Priority: P2
Base commit: latest `main` at start (spec baseline `20a793a5c37cf85d161532e1b683911c7ae4f5d6`)
Branch/PR: `gemini/T-007` / #59 (merged 670acbc, released vh-2026-11-21-03)
Spec: `specs/T-007-spec-v1.md` (approved by Martin 2026-11-21 16:36; D-024).
Scope: `index.html` + new `tools/test/explore_picks_check.mjs` only. Claude wires the new test into `.github/workflows/pwa-cache-check.yml` at release (A11).
Required Gemini stage: 2 (Stage 2 trial)
Claude notes: Stage 2 trial verdict 通過 (PR comment). Claude re-ran all AGENTS checks + new test; 5 independent mutations fail the test; headless 390/360/844x390/1280; CI step wired and passed; D-013 re-checked 2026-11-21 09:43Z. Not device-measured. Martin accepted on his devices 2026-11-21 ("通過t-007").

### T-006 zh-TW label fix: `shared_space` "Space" -> "空白鍵" (Gemini Stage 1 trial) (Done, accepted)
Owner: Gemini
Implementer: Gemini (Stage 1 trial; strings only)
Reviewer: Claude
Priority: P3
Base commit: latest `main` at start (spec baseline `6b669b8f4f796bd6e6cd6dcf07e1517f2804843d`)
Branch/PR: `gemini/T-006` / #53 (merged ffbe3f4, released vh-2026-11-21-02)
Spec: `specs/T-006-spec-v1.md` (approved by Martin 2026-11-21 15:32; D-022).
Scope: index.html only, +1/-1: zh-TW `shared_space` value. en table and HTML fallback unchanged.
Required Gemini stage: 1
Claude notes: diff exactly index.html +1/-1; Claude re-ran syntax, i18n (py+mjs), hud checks and a headless zh-TW/en probe (label 33 px, row scrollWidth == clientWidth at 390x844 forced-visible and 1280x800, 0 errors); CI green; D-013 protection re-checked 2026-11-21 08:04Z (PR required, enforce_admins true, no force push/deletion, rulesets 0). Martin accepted on his devices 2026-11-21 ("通過").

### T-005B Suburb frontage + city infill coverage (Done)
Owner: Codex
Implementer: Codex (world generation, never Gemini)
Reviewer: Claude
Priority: P1
Base commit: `0cc9aff09338ade85fd78826470053d3e5d68208`
Branch/PR: `codex/T-005B-coverage` / #47 (merged be87c2f, released vh-2026-11-21-01)
Depends on: T-005A (Done, Martin-accepted 2026-11-20)
Spec: Parts 1-3 `specs/T-005-spec-v1.md`; Part 4 `specs/T-005-spec-v2.1.md` (approved by Martin 2026-11-21 09:02; D-019).
Claude notes: round 1 (c8e395f) changes requested: physics cost of 40-unit collider cells, verge terrain fit, residual city lots; round 2 (e9a2dd4) approved. Do not weaken any hard rule if a later task revisits coverage.
Verification: code-reviewed + Claude's independent headless checks at e9a2dd4 (not device): all AGENTS checks and route legality pass; `coverage_audit --details` exit 0 (parks cover 17/101/27 phone, 27/101/43 desktop residual centers, 0 untreated); paired Cannon step median ratio 1.13 phone / 1.06 desktop (limit 1.35), city infill bodies +70/+52 (round 1: +333); full-scene draw calls vs base: suburb <= +3, city <= +5 on both profiles; verge clearance exactly +0.04 over the terrain triangles; no console errors. Martin accepted on S26 Ultra / Tab S11 on 2026-11-21 ("通過"); he did not report the `?fps=1` numbers, so no device FPS figures are recorded.

### T-005A Spawn cleanup + legal, denser traffic
Owner: Codex
Implementer: Codex (traffic/spawn/world, never Gemini)
Reviewer: Claude
Priority: P1
Depends on: T-004E (Done)
Base commit: `4c0d8db8bc603fa5786fe0a2e52ed035951a7e07`
Branch/PR: `codex/T-005A-traffic-legal` / #43 (merged d57d0db, released vh-2026-11-20-03)
Spec: `specs/T-005-spec-v1.md` Parts 1-2 (approved by Martin 2026-11-20 14:06; D-019).
Claude notes: (1) Audit script first (`tools/test/route_legality.mjs`): report route violations with coordinates before fixing; legality before density. (2) The yellow "Ferrari" is the parked Muscle 69 at (103, -14), remove only that parked car; keep the garage Muscle '69 option, saves and i18n; update `traffic_check.mjs` (vehicle list) and every fixed `WORLD.vehicles` index. (3) Traffic table in Part 2 is approved; the performance guard (+12 draw calls / +25 % physics step per preset) lets a preset keep its old count, say so in the PR. (4) Do not edit `sw.js` CACHE or docs; spec causes marked "hypothesis" must be confirmed by the audit. Martin attaches his screenshots to the Codex task.
Verification: Martin accepted on S26 Ultra / Tab S11 on 2026-11-20 ("通過", no numbers reported). Earlier: code-reviewed + headless/real-Chrome checks by Claude, round 1 R1 ramp stall fixed in e3cd24d. Known pre-existing, not fixed: R4 stall near (-4, 629), R5 (elevated ring lane) near (-572, 228). Five presets keep their old traffic count under the +12-draw guard.


### T-004E City district infill
Owner: Codex
Reviewer: Claude
Priority: P1
Depends on: T-004D (Done, Martin-accepted 2026-11-20)
Base commit: `5a8041d8177e38af14215a282082395fba798700`
Branch/PR: `codex/T-004E-urban-infill` / PR #34 (squash-merged dd4918d, released as `vh-2026-11-20-02`)
Spec: `specs/T-004A-spec-v1.1.md` §3.2, §3.6, §4 (T-004E row).
Claude notes: (1) Report placed building counts per district (CBD / Midtown / Old Town) for the exact same baseline build and the new build, and the increase vs the +20 / +40 / +35 % targets; record shortfalls instead of forcing overlaps (§3.2.2). (2) Every new building needs a static collider matching its visible shell down to its visible base (as in T-004C/D) and must appear in `WORLD.buildings` (map, camera blockers, facade LOD) like existing buildings; extend `collision_check.mjs` with impacts on new city buildings. (3) Clearance audit for every addition: `rectHitsElevated`, `rectHitsCurvedRoad`, grid roads and intersections with >= 3 units, depots, mission checkpoints, ramps (takeoff and landing), garage access, fast-travel arrivals, spawn and the CBD plaza. (4) Reuse the existing facade/window batching; report draw calls added on PHONE_LOW (<= 8) and DESKTOP_HIGH (<= 16) for city infill, measured with `renderer.info.render.calls` if a browser works, otherwise a structural count clearly labelled. (5) Traffic, trees, suburbs, camera, HUD, Hub, localization, economy and saves unchanged.
Verification: `code-reviewed` + headless full game (Chrome/SwiftShader, not a device). Status: Done. Martin accepted on S26 Ultra / Tab S11 on 2026-11-20 (verdict "通過", no numbers reported), including the desktop Old Town shortfall (+2.3% vs +35% target) which the release report asked him to accept or reject.
Claude review (2026-11-20): infill is a separate initialization-only parcel pass over vacant parts of the original blocks (original `blockSpecs()` results untouched): 10x10 shells, heights CBD 16 / Midtown 20 / Old Town 12, one static box each from ground to wall top, registered in `WORLD.buildings`, `WORLD.roofs` (map, facade, camera blockers); three instanced shell batches reusing existing wall materials. Placed counts, PHONE_LOW: CBD 10->12 (+20.0%), Midtown 12->17 (+41.7%), Old Town 30->41 (+36.7%); DESKTOP_HIGH: CBD 27->33 (+22.2%), Midtown 18->26 (+44.4%), **Old Town 87->89 (+2.3%, 29 short of the +35% target)**. The desktop Old Town shortfall is real: of the candidates tried, 2259 failed the 3-unit gap to an original building, 773 the 10-unit street-tree/sidewalk strip, 225 had no facade cell, 116 hit elevated/curved road; no clearance was relaxed (§3.2.2). Claude fixed one defect (1af0de3): infill facades were flush with the shell wall and z-fought on tablet/desktop quality (the facade kit is skipped on PHONE_LOW); infill facade offset is now 0.06. Real `renderer.info.render.calls`, PR minus base at the same pose: DESKTOP_HIGH +1..+2, TABLET/MED +1..+3 (budget +8 / +16). 216 full-game impacts on all 18 PHONE_LOW shells (4 axes x 20/60/120 km/h): 0 runs without contact, 0 pass-through; no prop, lamp or tree inside any footprint; smoke + offline OK. NOT verified: device FPS/heat, real-device look, PWA update on an installed app. Cosmetic: facade window frames on infill show the flat shell colour (no interior-mapped glass) and 16/20 m shells have a plain wall above the 12 m facade band.

### T-004D Suburban variety (Option B) and increased structure density
Owner: Codex
Reviewer: Claude
Priority: P1
Depends on: T-004C (Done, Martin-accepted 2026-11-19)
Base commit: `dab2ba607ac77e706e82a947c3ce171ef5c45311`
Branch/PR: `codex/T-004D-suburb-variety` / PR #31 (squash-merged 17c16b3, released as `vh-2026-11-20-01`)
Spec: `specs/T-004A-spec-v1.1.md` §3.3 Option B, §3.4, §3.6, §4 (T-004D row).
Claude notes: (1) Every new structure needs a collider that covers its visible foundation on slopes, like the T-004C house fix (box from base bottom to wall top, base footprint); keep `house.collider`-style mapping for each structure so alignment can be tested, and extend `collision_check.mjs` to all seven types. (2) Keep `WORLD.suburbHouses` usable by the world map (§3.4.6) and keep the T-004C spatial grouping (<=16 shapes per body); report the new body count. (3) Trees: new parcels must not overlap existing tree trunks; drop or skip a parcel rather than moving trees unless the tree sits on a road. (4) Report placed counts per type and zone against the Option B shares and the >=1.40x baseline, draw calls added on PHONE_LOW and DESKTOP (limits +20 / +30), and headless physics step cost.
Verification: `Martin-accepted` (2026-11-20, S26 Ultra / Tab S11 device test) + `code-reviewed` + headless full game (Chrome/SwiftShader).
Claude review (2026-11-20): seven Option B types at exact shares (210 phone / 390 desktop, 1.62x / 1.81x baseline, residential 87%); placement rules per §3.4; one foundation-to-wall-top box per structure; 2 opaque + 1 roof material, vertex colors, no per-building textures. Claude fixed one defect (2916bab): candidates were taken in road order, so on phones Maple Ave fell from 39 to 20 houses (aerial view almost empty), Hillcrest was bungalows only and Valley Loop empty; a golden-ratio stride now spreads each type. Zones Main/Maple/Hillcrest/Valley: phone 50/39/41/0 -> 47/35/60/68, desktop 50/39/62/64 -> 96/75/102/117, all mixed. PHONE_LOW renderer draw calls at 8 suburb views: +7 at most (limit +20). Full game: 42/42 downhill foundation impacts (2 steepest per type x 30/60/120 km/h) stopped outside, upright; smoke + offline OK. Walls are flat vertex colours with box windows/doors (old siding texture removed). NOT verified: desktop draw calls (headless fell back to mobile profile), device FPS/heat, reachability of 28-unit rear rows on foot.

### T-004C Tree and existing house collision repair
Owner: Codex
Reviewer: Claude
Priority: P1
Depends on: T-004B (Done, Martin-accepted 2026-11-19)
Base commit: `e9c8229b218946954e8d6d3a80dab096379fab76`
Branch/PR: `codex/T-004C-collisions` / PR #28 (squash-merged 06e0514, released as `vh-2026-11-19-19`)
Spec: `specs/T-004A-spec-v1.1.md` §3.5, §3.6, §4 (T-004C row), §5.1 items 4–7.
Claude notes: prefer upright `CANNON.Box` trunks over `CANNON.Cylinder` (box chassis vs cylinder is a costly convex test); preallocated pool, add/remove only on the 0.5 s grid refresh, update AABBs after moving static bodies, immediate refresh on teleport; house compound bodies regrouped by spatial cell must not increase total body count.
Claude note (T-004B context): ordinary traffic now freezes off screen and is woken by `updateTrafficPhysics()` (see HANDOFF "Traffic (T-004B)"). Tree trunk bodies must collide with active traffic too; a frozen traffic car is out of the world, so §3.5 "do not deactivate colliders near an AI car physically interacting with the tree" only concerns active cars. Keep the house-collider Y fix and spatial regrouping in this PR; do not change traffic rules.
Verification: `Martin-accepted` (2026-11-19, S26 Ultra / Tab S11 device test) + `code-reviewed` + headless full game (Chrome/SwiftShader).
Claude review (2026-11-19): one preallocated upright Box per tree (693 phone / 1,216 desktop), 32-unit grid, 0.5 s refresh, 140/180 hysteresis, immediate refresh on init/teleport, occupancy deferral, retention near active cars; house bodies spatially regrouped (same body count, <=16 shapes) with the Y offset fixed; two trees on the Chiliad link moved off the road with their proxies. Claude fixed one defect (1f9634b): house boxes started at the foundation top, so on slopes (up to 2.49 units of grey foundation exposed; 70 of 130 houses > 0.8) the car went under the wall box and 1.1 units into the foundation; boxes now span y - 2.8 to the wall top with the foundation footprint. Full game: 6 steepest houses x 30/60/120 km/h stop outside the foundation, upright; 36/36 trunk runs (4 palm, 4 pine, 4 broadleaf x 20/60/120 km/h) hit with no pass-through; walking blocked; PHYS_DEBUG aligned; smoke and offline reload OK. Physics step + managers (headless median ms): PHONE_LOW 4.1 -> 4.2 spawn, 3.9 -> 4.3 suburb, 3.1 -> 3.5 hill; TABLET_MED within noise. NOT verified: device FPS/heat, feel of scraping along walls.

### T-004B Traffic population + Ferrari exclusion
Owner: Codex
Reviewer: Claude
Priority: P1
Depends on: T-004A (approved, D-017); no other active code PR
Base commit: `5dd882ac9c1cf66ed910c600f6f619f4dfa2a5a7`
Branch/PR: `codex/T-004B-traffic` / PR #25 (squash-merged 89f1a18, released as `vh-2026-11-19-18`)
Spec: `specs/T-004A-spec-v1.1.md` §3.1, §3.6, §4 (T-004B row), §5.1 items 1–3 and 8.
Acceptance (spec §4): §3.1 pool table exactly; 0 ordinary AI Ferrari; 5 fresh / 5 recycled loads; spawn separation (>=20 units between cars, >=25 from player's car) and 30-unit insertion clearance; no recycle within 120 units; syntax + offline; measured nearby/visible counts at 10 viewpoints vs baseline.
Claude notes: (1) Every ordinary AI car is a full `RaycastVehicle` (4 wheel raycasts per physics step); doubling the pool is the main phone-CPU risk, so §3.1 item 5 (physics active only near the player, safe re-activation of frozen far cars) must be implemented, and the PR must report `physicsWorld.step` cost before/after (headless numbers labelled as headless). (2) Current code already gives ordinary traffic `model: 'kenney'`; find and fix the real path where Ferrari appears on NPC traffic (or show none exists) instead of assuming. Parked/selectable cars and the player Ferrari stay unchanged. (3) No per-frame allocations in traffic loops; saves, missions, police and controls unchanged.
Verification: `Martin-accepted` (2026-11-19, S26 Ultra / Tab S11 device test) + `code-reviewed` + headless full game (Chrome/SwiftShader).
Claude review (2026-11-19): pool table exact; ordinary AI forced to Kenney with both Ferrari paths guarded (Ferrari investigation: no current ordinary-AI Ferrari path; 0 Ferrari in every run); spawn 20/25, insertion 30, no recycle within 120 or while visible; freeze/wake reuses the preStep callback and resets body/wheel state. Claude fixed one defect (19b4a97): freezing every car beyond 200 units froze most cars the player could see (TABLET_MED downtown: 10 of 13 on screen standing still); now cars beyond 200 freeze only after 2 s off screen and wake when they come on screen (`TRAFFIC.hideGrace`). Full game, 10 viewpoints summed: nearby cars PHONE_LOW 8 -> 51, TABLET_MED 12 -> 97; on screen 8 -> 19 / 10 -> 24, none frozen. Full-city physics step + vehicle updates (headless, median ms): PHONE_LOW about equal to baseline (4.7 -> 4.6 downtown), TABLET_MED +7-28% (6.2 -> 6.6 downtown). Smoke: driving, fast travel (no frozen car within 160), race, delivery, police, garage, save reload, offline reload, no errors. Suburbs/highway still show little traffic on screen. NOT verified: device FPS/heat (spec §3.6 routes), visible wake-up pop-in, rendering cost of more cars on screen.

### T-004A Living City 2.0 Specification v1.1
Owner: ChatGPT
Reviewer: Claude
Priority: P1
Depends on: T-003 pipeline (Done)
Base commit: design base `79ba05bcdf4def80ad4d2bd96cd3abba86d9baf6`; spec archived on `main` in PR #23 (a53d0ba)
Branch/PR: PR #23 (docs, archive); registered in the docs PR that follows it
Output: `specs/T-004A-spec-v1.1.md` (verbatim) defining T-004B..E. Suburban style: **Option B — Mixed American Small Town** (Martin, 2026-11-19 17:28).
Verification: `designed / Martin approved` (2026-11-19). Nothing measured; no code written.
Review notes: code facts checked against main 30514a9 — traffic pool table in §2 matches `DENSITY` presets; suburb collider Y-offset bug and missing tree trunk bodies confirmed. Ordinary AI traffic is created with `model: 'kenney'` and does not reach `applyFerrariModel()` in current code, so T-004B must first locate where Ferrari traffic is actually seen. Spec text still says "proposed; NOT approved" and §2/§6.5 still describe T-003D/E as pending because it is stored verbatim; approval and scheduling are recorded in D-017 and here. All approved numbers (traffic table, building shares/caps, collider tolerances, activation radii, FPS targets) are binding as written.

### T-003E Bilingual interface (English / Traditional Chinese)
Owner: Codex
Reviewer: Claude
Priority: P1
Depends on: T-003D (Done, Martin-accepted 2026-11-19)
Base commit: `4bf6d967935c0e678ad29a2c420d17ad630c76da`
Branch/PR: `codex/T-003E-i18n` / PR #20 (squash-merged a9de637, released as `vh-2026-11-19-17`)
Spec: `specs/T-003A-spec-v1.1.md` sections 6, 8, 10. String table, language selector in SETTINGS, `vh_save.language` (new field, default-safe), complete player-visible translation, CI check for leftover CJK, live panel refresh, old saves keep working.
Claude notes: (1) Default policy needs "new player vs existing save": decide by whether `vh_save` existed before this load (no key = new = English; key without `language` = existing = zh-TW). (2) Dynamic strings (e.g. `showBanner` calls, delivery/mission text, reward messages from T-001B) must go through the table. (3) Existing `vh_settings` holds other settings; keep language in `vh_save` as specified.
Claude note (4): the language selector goes in the SETTINGS tab of the Game Hub (`#settings-modal` inside `#quick-actions`, see HANDOFF "Game Hub (T-003D)"); Hub tab labels, Hub title/close aria-labels, map chips/detail text, and the T-003C/D aria-labels are player-visible and must be translated too. `hud_layout_check.py` already sets English-length labels; keep it passing with the real strings.
Verification: `Martin-accepted` (2026-11-19, S26 Ultra / Tab S11 device test) + `code-reviewed` + headless (Chrome/SwiftShader).
Claude review (2026-11-19): approved with no code changes. 318-key en/zh-TW table; new player = English, existing save without language = zh-TW, valid choice wins, only `SAVE.language` added and unknown fields preserved; live refresh of panels, aria, map chips/selection, garage, mission/delivery/pursuit HUD and active banner; manifest href and `<html lang>` follow the language; both manifests precached. All five automated checks PASS (i18n_check .py/.mjs, syntax, hud, camera); `hud_layout_check.py` PASS with real strings, 11 viewports x 2 languages; live headless: new-player English with no CJK left in visible DOM/Hub (only full-width "＋" on map zoom, cosmetic), legacy save boots zh-TW with all fields kept, language persists across reload, delivery and map selection switch live, both manifests served offline. CACHE bumped for the PRECACHE change. NOT verified: real device, whether an already-installed PWA picks up a runtime manifest href change, FPS.

### T-003D Minimap-driven Game Hub
Owner: Codex
Reviewer: Claude
Priority: P1
Depends on: T-003C (Done, Martin-accepted 2026-11-19)
Base commit: `d96335833dba1207ab693a70dd0d77c91d477019`
Branch/PR: `codex/T-003D-game-hub` / PR #17 (squash-merged 872ab73, released as `vh-2026-11-19-16`)
Spec: `specs/T-003A-spec-v1.1.md` sections 5, 8, 10. All existing toolbar actions through the Hub; mission/garage/map/settings preserved; correct modal and input handling; `closeModals` flow and the delivery fast-travel block preserved.
Claude note: T-003C left an interim `#quick-actions` dialog (opened by tapping `#radar-container`) holding all old toolbar buttons with their original IDs, the crate counter and RPM/nitro bars; the Game Hub replaces this dialog, keeps those IDs/handlers working, and keeps the radar draw skip while the Hub is open (`RADAR` in index.html, see HANDOFF "HUD (T-003C)").
Claude note: spec lists an "airport stunt" mission; no such name exists in code today. Map it to the existing STUNT mission and do not add a new one.
Verification: `Martin-accepted` (2026-11-19, S26 Ultra / Tab S11 device test) + `code-reviewed` + headless (Chrome/SwiftShader).
Claude review (2026-11-19): one `<dialog id="quick-actions">` with MAP/MISSIONS/GARAGE/WORLD/SETTINGS tabs holding the original panels and IDs; `closeModals` is the single close path (Escape, M, ✕, wm-close); opening releases held input; map timer and pointers cleared off the MAP tab; radar suppressed while open; delivery fast-travel block kept (message also in the map panel). Claude fixed one defect (9eae832): banners were hidden under the modal's top layer, so "not enough cash", purchase, upgrade, quality, camera and sky feedback was invisible; `#notice-area` now moves into the Hub while it is open. `hud_layout_check.py` PASS for 11 viewports x 2 label languages, including all five panels; live headless flows: Esc/M/focus, garage insufficient cash/purchase/paint/upgrade/summon, WORLD/SETTINGS, race start/cancel, delivery blocks travel, no errors. NOT verified: real touch pan/pinch, notch safe areas, device FPS.
Notes: at 800x360 the map area is small but usable; the 3D scene still renders behind the opaque Hub (skipping it would need a design decision, spec §5).

### T-003C Responsive HUD, radar optimization and pedals
Owner: Codex
Reviewer: Claude
Priority: P1
Depends on: T-003B (done, accepted by Martin 2026-11-19)
Base commit: `b05cfd559ef7dcce516be7507dc17b924433ff27`
Branch/PR: `codex/T-003C-hud` / PR #14 (squash-merged db06aa2, released as `vh-2026-11-19-15`)
Spec: `specs/T-003A-spec-v1.1.md` sections 3 (HUD, tablet landscape, compact fallback, pedal design), 4 (minimap rules), 8 (layout matrix), 10 (release gates), 11 (out of scope). The spec file is the authority; this entry points to it and adds Claude's clarifications.
Output: HUD and visual-controls PR only. No camera, Game Hub, localization, economy, physics or input-logic changes.

Acceptance (from spec sections 3, 4, 8, 9, 10):
1. Default gameplay HUD shows only: minimap/Hub entry, cash, speed and gear, wanted level when active, essential mission progress when active, touch steering and driving controls, contextual enter/exit, short reward/warning notices. At least 55% of viewport width stays clear in the centre.
2. Tablet landscape (viewport >= 960 x 560 CSS px) uses the spec's component placement and sizes (minimap 112-128 px top-left, cash+speed 160-196 px top-right, steering 72-88 px bottom-left, gas 64x118 and brake 64x100 bottom-right, nitro/handbrake 48-56 px, horn/enter-exit >= 44x44). Safe-area insets plus 12-20 px padding, no overlaps, no horizontal scroll.
3. Compact fallback below 960 x 560 and the extra-short mode below 430 px height as specified; every touch target >= 44x44 CSS px; steering and gas/brake stay multitouch-capable.
4. Validate the matrix in spec section 8 (1280x800, 1024x768, 960x540, 844x390, 800x360, resized/multi-window) with no overlap, no unreachable buttons, readable text, and no stuck steering/gas after rotate or resize.
5. Pedals: graphite/metal CSS look (palette in spec 3.4), GAS taller and narrower with vertical grooves, BRAKE shorter and wider with horizontal grooves, slight press movement. Look and position only: `INPUT.forward/backward/left/right`, nitro (shift) and handbrake (space) bindings and behavior unchanged. No analog throttle.
6. Minimap reuses the existing `radar-canvas` and `drawRadar()`: ~10 Hz normally, 8 Hz allowed on LOW quality, no second minimap, no extra Three.js renderer or 3D camera, no continuous redraw while hidden, keep waypoint/police/delivery/mission icons, no growth of canvas backing resolution.
7. No feature functionality removed (see Claude clarification 1). Saves, missions, offline play unchanged.
8. `python3 tools/test/syntax_check.py` passes; `sw.js` CACHE untouched; PR reports phone/tablet performance impact honestly. Headless numbers are labelled `measured (headless)`; real-device FPS is Martin's.

Claude clarifications (reviewer notes, 2026-11-19):
1. The spec removes the permanent 8-button toolbar here but the Game Hub arrives only in T-003D. This task must keep every existing action reachable through an interim entry (for example tapping the minimap opens a simple panel with the existing actions: quality, mission, garage, cop chase, radio, camera, sky, settings). T-003D replaces that panel with the full Hub. Do not delete the underlying handlers or element IDs.
2. `radar-canvas` is 140x140 backing pixels, enough for the 112-128 CSS px target; do not enlarge it.
3. No `safe-area` handling exists in `index.html` today; add it.
4. Existing HUD element IDs used by code and tests (`hud-cash`, `hud-speed`, `hud-gear`, `hud-stars`, `hud-crates`, `mission-panel`, `pursuit-hud-panel`) should stay so game logic keeps working.
5. Verified existing behavior to keep: `touch-action`/pointer handling on `touch-controls` (steering and gas/brake simultaneously), `bindHold('btn-drive-gas','forward')`, `bindHold('btn-drive-brake','backward')`.
6. Real-device S26 Ultra / Tab S11 FPS and layout acceptance belong to Martin after release.

Verification: `Martin-accepted` (2026-11-19, S26 Ultra / Tab S11 device test) + `code-reviewed` + headless (Chrome/SwiftShader).
Claude review (2026-11-19): spec sizes match (tablet 120/80/64x118/64x100/50, compact 96/64/58x100/60x88, short 84/56/50x84/54x74, targets >= 44 px); radar reuses the 140x140 canvas, 10 Hz / 8 Hz LOW, no draw while hidden/dialog/overlay; bindings unchanged plus pointercancel and resize/orientation/blur/visibility release. Claude fixed one defect (eb8b04d, CSS only): at 800x360 the pursuit bar covered horn/enter-exit, and on narrow/portrait screens the mission line covered the pursuit bar. `hud_layout_check.py` then PASS for 11 viewports x 2 label languages (1280x800, 1024x768, 960x540, 915x412, 844x390, 800x360, 667x375, 568x320, 640x480, 540x768, 412x915); live headless run: no errors, all dialog actions work, gas+steer together and release, keyboard W/M work, seeded save survives reload. NOT verified: radar Hz under real rendering (headless ~0.6 FPS), real multitouch, notch safe areas, S26 Ultra / Tab S11 FPS and feel.
Visible changes for Martin to judge: the 8-button toolbar, nitro/RPM bars and crate counter now live in the minimap menu (tap the minimap); long enter/exit labels truncate with an ellipsis.

### T-003B Third-person camera tuning
Owner: Codex
Reviewer: Claude
Priority: P1
Depends on: T-003A (approved, done)
Base commit: latest `main` (Claude reports the SHA when this task is unlocked)
Branch/PR: `codex/T-003B-camera` / PR #10 (squash-merged d0e97c1, released as `vh-2026-11-19-14`)
Spec: `specs/T-003A-spec-v1.1.md` section 2 (camera), section 10 (release gates), section 11 (out of scope). The spec file is the authority; this entry only points to it.
Output: Camera-only PR. No HUD, minimap, Hub, localization, input or physics changes.

Acceptance (from spec section 2 and 10):
1. One named camera configuration block holds all defaults: on-foot 4.2 / 12° / 1.55; Chase Near 7.2 / 10° / 1.10; Chase Far 10.5 / 14° / 1.10 (distance / pitch / target height, world units).
2. Hood and bird's-eye cameras unchanged. Pinch/wheel zoom and manual yaw/pitch preserved.
3. Recenter to heading after 2 s without camera input; smooth follow lag; less high-speed shake.
4. FOV: 60° normal, progressive widening to max 68°, nitro max 72°, applied smoothly.
5. Building collision avoidance preserved; smooth distance recovery when an obstacle clears; no jitter near walls, ramps, hills, overpasses.
6. No per-frame allocations in the camera path.
7. `python3 tools/test/syntax_check.py` passes; `sw.js` CACHE untouched; saves, missions, controls and offline play unchanged.
8. PR states phone/tablet performance impact honestly; no `measured` claims. Martin does final hand acceptance on S26 Ultra and Tab S11 (city, mountain road, elevated highway, collisions, manual rotation).

Claude reviewer notes (from `index.html`, 2026-11-19):
- Mode map today: `STATE.cameraMode` 0 = near (dist 8.8, pitch 0.24 rad), 1 = far (13.5, 0.36 rad), 2 = hood, 3 = bird. Recenter delay today 1.5 s; FOV today 62 base, up to +14 with speed, +6 nitro; shake above 150 km/h.
- The hood/bird branch currently does `new THREE.Vector3(...)` every frame inside `updateCameraAndLights`; reuse a module-level vector while touching this function (in scope: spec item "avoid per-frame allocations").
- Existing camera collision uses `CAM.raycaster` against `WORLD.cameraBlockers`; keep it, add smoothing on the recovery side only.

Verification: `code-reviewed` + headless (Chrome/SwiftShader, not a device): Claude approved PR #10. CI check+syntax pass; `camera_check.mjs` PASS. Headless full-game run: no startup errors, saves reload intact, near/far distance 7.5/10.8, FOV rest 60 and 66.9 at 216 km/h, 21 spots x 4 headings x 100 frames with 0 obstructed frames (baseline main: 4), teleport first-frame distance 7.5 (baseline 545). NOT verified: real touch, S26 Ultra / Tab S11 feel and FPS, long drives (mountain, elevated road, collisions), enter/exit-car camera transition feel (>=40-unit teleports now cut instead of easing, by design). Martin accepted T-003B by hand on his devices on 2026-11-19 (verdict only; no FPS numbers reported, so nothing is `measured`).

### T-003A Immersive Gameplay UX Specification v1.1
Owner: ChatGPT
Reviewer: Claude
Priority: P1
Depends on: T-001B
Base commit: design base `5937859ff7160851e7342359b576a45c5177d423`; spec archived on `main` in PR #8 (ea43ece)
Branch/PR: PR #8 (docs, archive); registered in the docs PR that follows it
Output: `specs/T-003A-spec-v1.1.md` (verbatim) defining T-003B..E.
Verification: `designed / Martin approved` (2026-11-19). Not device-measured; no code written. Spec targets: Samsung S26 Ultra and Samsung Tab S11, 30 FPS default; tablet landscape layouts 1280x800, 1024x768, 960x540; real-device FPS must be reported by Martin before anything is marked `measured`.
Review notes: spec names verified against `index.html` (`radar-canvas`, `drawRadar`, device presets, existing 30 FPS cap for phone/tablet). Spec text still says "awaiting Martin's approval" because it is stored verbatim; the approval is recorded in D-015.

- T-000 Collaboration docs created and migrated to COLLAB v2 (2026-11-18)

### T-001B Economy implementation
Owner: Codex
Reviewer: Claude
Priority: P1
Depends on: T-001A
Base commit: Latest `main` after approved documentation is merged
Branch/PR: `codex/T-001B-economy` / PR #3 (squash-merged 0412cbd)
Output: Minimal implementation PR following the complete approved T-001A specification above.

Acceptance:

1. Apply all approved reward and time formulas.
2. Preserve existing car prices, six depots and game features.
3. Implement ramp, airtime, mission and police reward cooldowns.
4. Prevent duplicate rewards and fast-travel delivery shortcuts.
5. Preserve all existing save fields and owned cars.
6. Persist new crate and cooldown information safely.
7. Pass `python3 tools/test/syntax_check.py`.
8. Report actual automated/headless checks without claiming unperformed real-device testing.
9. Claude reviews correctness, regressions, mobile effects, and save compatibility.
10. Martin performs final gameplay acceptance.

Verification: Claude review approved. CI check+syntax pass. Headless Chrome on the PR build: delivery 974 m → reward 1520, limit 183, early pay 1820 (matches formula); DRIFT/RACE/STUNT pay 1200/1400/1600 once, replay inside cooldown pays $0; crate +$400 once, persists across reload; no page errors. Claude fixed stale mission-menu reward text. NOT auto-verified: airborne reward trigger/cap, ramp repeat cooldown feel, real-device performance → Martin to check in play. Non-blocking: clamp cooldown if system clock moves backwards.

### T-001A Economy balance spec
Owner: ChatGPT
Reviewer: Claude
Priority: P1
Depends on: —
Base commit: `265b61289f7ce9edb8c105bb8fc1939365289aa8`
Branch/PR: Not applicable to design
Verification: `designed` — source code reviewed, Martin approved 2026-11-18. No human playtest or performance measurement completed.
Output: Approved Economy Balance Specification v1.0, reproduced below.

**Approved specification**

**A. Starting economy and progression**

- Starting cash: $3,500.
- Lexus LC 500: $18,000.
- Porsche 911: $25,000.
- Default Ferrari remains free.
- Engine upgrades remain $1,000 per level.
- First Lexus purchase target: 20–35 minutes of mixed gameplay.
- Porsche purchase target: 55–90 minutes cumulative gameplay, assuming Lexus was bought first.

**B. Delivery jobs**

Keep all six depots, existing pickup and delivery conditions, and destination range of 320–1,500 metres.

- BaseReward = roundTo10(350 + Distance × 1.2)
- TimeLimit = round(75 + Distance / 9) seconds
- Early delivery (remaining time >35% of initial limit): 1.20× base
- On-time delivery: 1.00× base
- Late delivery: 0.50× base
- Round final payment to nearest $10.
- No automatic expiration for late deliveries.
- Disable fast travel during an active delivery.
- Distance refers to straight-line distance; no route-finding algorithm is required in this release.

| Distance | Base | Limit | Early | Late |
|---|---:|---:|---:|---:|
| 320 m | $730 | 111 s | $880 | $370 |
| 900 m | $1,430 | 175 s | $1,720 | $720 |
| 1,500 m | $2,150 | 242 s | $2,580 | $1,080 |

**C. Stunt jumps**

- First successful completion of each unique ramp: $900.
- Seven unique ramps; total initial-completion reward: $6,300.
- Repeat reward = min(450, 180 + 10 × round(Distance / 20)).
- Same ramp: maximum one repeat payout every 120 seconds.
- Repeat ramps and generic airtime rewards share a 90-second global payout cooldown.
- First-time ramp completion is exempt from repeat-reward cooldown restrictions.
- One jump must not pay both ramp and generic airtime rewards.

**D. Generic airtime rewards**

- Reward = min(400, round(AirTime × 150)).
- Minimum qualifying airtime: 0.65 seconds.
- Require genuine airborne and landing detection using `raycastResult.hasHit`.
- Maximum payout: $400 per landing.
- Shared 90-second global cooldown with repeat ramp rewards.
- Do not use cannon-es `isInContact`.

**E. Other income sources**

| Source | Approved payment |
|---|---:|
| Collectible crate | $400 |
| Race mission | $1,400 |
| Drift mission | $1,200 |
| Airport stunt mission | $1,600 |
| Successful police escape | $600 |
| Arrest fine | -$300 |

- Fifteen collectible crates, collectible once per save.
- Each mission type has its own 300-second payout cooldown.
- Police escape payout cooldown: 600 seconds.
- Replaying a mission during cooldown remains allowed without an additional payout.
- Cooldown information must be understandable in the UI.
- Cooldowns must remain effective after reloading the game.

**F. Save compatibility**

Preserve `localStorage` key `vh_save` and all existing fields: `cash`, `owned`, `jumps`, `deliveries`, `upgrade`.

Add compatible fields with safe defaults:

- `collectedCrates`
- `rewardCooldowns`

Do not reset current cash, owned cars, jump progress, deliveries or upgrades. Older saves lack crate history; initialize new tracking safely without claiming old collections can be reconstructed.

**G. Progression reference scenarios (design estimates)**

First purchase:

- 7 normal 900 m deliveries: $10,010
- 3 first-time ramps: $2,700
- 2 crates: $800
- 1 race: $1,400
- Total earned: $14,910
- Starting cash + earnings: $18,410
- Lexus purchase leaves $410.

Second purchase after Lexus:

- 12 normal 900 m deliveries: $17,160
- 4 first-time ramps: $3,600
- Airport stunt: $1,600
- Drift mission: $1,200
- 2 crates: $800
- Police escape: $600
- Total earned: $24,960
- With $410 balance: $25,370
- Porsche purchase leaves $370.

These are planning calculations, not measured gameplay results.
