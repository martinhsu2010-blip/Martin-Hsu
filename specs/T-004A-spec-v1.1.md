# T-004A spec v1.1 — Living City 2.0: Traffic, Architectural Diversity and Solid Collisions

Status: **proposed; NOT approved for implementation**. Author: ChatGPT. Base commit: `79ba05bcdf4def80ad4d2bd96cd3abba86d9baf6` (main at initial analysis, 2026-11-19). Reviewer: Claude. Priority: P1. Related: COLLAB v3.1, D-005/D-011/D-012/D-016, existing proposed T-004A v1.0, approved T-003A v1.1. This document **replaces the unapproved proposed T-004A v1.0** for discussion; no existing approved implementation requirement is changed.

Rules: All values below are proposed design thresholds, **not observed measurements**. Martin selects a suburb option and approves v1.1 explicitly before Claude registers it. Codex cannot use this proposal as implementation authorization. Units are Three.js/Cannon world units unless marked otherwise.

## 1. Goal and non-goals

Player-facing goals:
1. Make streets clearly busier without showing ordinary NPC traffic cars as Ferrari GLBs.
2. Increase downtown/old town/midtown infill without blocking roads, ramps or mission locations.
3. Offer differentiated suburban neighborhoods with recognizable silhouettes and uses, rather than cloned detached houses.
4. Make all **reachable** tree trunks and suburban/city building walls solid to player cars and pedestrians. Objects should not visually intersect their physical proxies or trap the player after fast travel.
5. Preserve 30 FPS design targets on Samsung S26 Ultra PHONE_LOW and Samsung Tab S11 TABLET_MED; desktop target 60 FPS until measured.

Non-goals: new traffic AI, new driving physics or car damage rules, new roads or expanded map, new missions or incomes, additional pedestrian count, new downloadable GLBs/texture assets, new realtime building interiors, new destructible trees/buildings, analog driving inputs, camera/HUD/Game Hub/localization edits, or persistent map edits in `vh_save`.

## 2. Fixed constraints and confirmed code facts

- One-file `index.html`, Three.js r160 / cannon-es; offline PWA. No new network dependencies or binary assets. Existing `vh_save` fields preserved.
- `spawnVehicles()` creates ordinary AI cars as Kenney types from `models/cars/kenney_traffic.glb`; the player Ferrari and special parked/selectable cars are distinct. Do not remove player Ferrari. Current ordinary AI traffic pool sizes are 10/12 on PHONE LOW/MED, 12/16/18 on TABLET, 20/26/34 on DESKTOP, 12/15/18 on IGPU.
- Existing traffic recycling checks at 1.2 s, at most 2 cars per interval, for cars >470 units away; placement candidates are 150–360 units from the player and 30 units clear of other vehicles.
- `buildSuburbs()` currently has nominal maximum 130 suburban houses on non-desktop and 260 on desktop, with sampling step 8. The current realized count is **not yet measured**. Houses use InstancedMesh wall/roof/base components.
- **Suburban houses already have Cannon static colliders**, up to 16 shapes per compound body. However `cur.addShape(..., new CANNON.Vec3(h.x - cur.position.x, hh - 1.0, h.z - cur.position.z), q)` does not include `h.y - cur.position.y` in the local vertical offset. On uneven ground the visual and physical house may be vertically misaligned; this is an identified code risk, not a proven explanation for every reported clipping incident. Large compound bodies spanning distant houses may also increase broadphase extent.
- Trees are added to `TREES.list` and rendered as InstancedMesh in `buildTrees()`. No matching tree-trunk static body creation was found in this code path. This directly explains why reachable trees may be pass-through.
- Conventional city buildings generally call `addStaticBoxCollider()` and register `WORLD.cameraBlockers`; do not assume that **all** city structures are missing collision. Verify each added building individually.
- Physics uses `CANNON.SAPBroadphase`; physics fixed step remains 1/60 s. `PHYS_DEBUG` draws actual Cannon shape wireframes, useful for verification.
- Original T-004A v1.0 still establishes a proposed 1.4× actual suburb-house count target and 210/390 house caps; those values remain proposed here.
- Existing T-003D and T-003E remain in their approved sequential pipeline. **Do not launch T-004 implementation until Martin authorizes its scheduling and COLLAB v3.1 permits the next code PR.**

## 3. Detailed requirements

### 3.1 Ambient traffic density (T-004B)

**Ordinary AI traffic pool size** excluding player/parked/selectable cars and police:

| Preset | Baseline | Proposed |
|---|---:|---:|
| PHONE_LOW | 10 | 18 |
| PHONE_MED | 12 | 24 |
| TABLET_LOW | 12 | 22 |
| TABLET_MED | 16 | 32 |
| TABLET_HIGH | 18 | 36 |
| DESKTOP_MED | 20 | 40 |
| DESKTOP_HIGH | 26 | 52 |
| DESKTOP_ULTRA | 34 | 68 |
| IGPU_LOW | 12 | 20 |
| IGPU_MED | 15 | 28 |
| IGPU_HIGH | 18 | 36 |

Requirements:
1. Preserve all 11 currently weighted Kenney traffic types and Ford police cars.
2. Every `isAI` ordinary car uses a Kenney subtype, or the existing simple geometric fallback if Kenney fails to load. Never apply Ferrari GLB to ordinary AI cars. The free/player Ferrari stays available; parked/selectable cars remain unchanged unless separately approved.
3. Initial ordinary vehicle spawn separation >=20 units center-to-center; >=25 units from the player's initial car. Search another route/slot when a site is occupied.
4. Recycle existing car instances, never create unbounded new vehicles. Do not recycle a car within 120 units of player; try not to teleport visible cars. Preserve adequate minimum 30-unit clearance around insertion points.
5. Physically active near traffic within 100 units; far physics may be frozen after 200 units only if safely activated again before entering the player's reachable path.
6. Produce measured spawned/visible nearby count diagnostics at 10 test viewpoints and report whether doubled population actually looks denser. Do not equate configuration count with visible count.
7. Avoid allocations in frame-critical traffic loops, preserve missions, saves and player controls.

### 3.2 City building density (T-004E)

Target increases are based on **successful placed counts**, comparing the exact same baseline build, rather than configured cap:

| Zone | Proposed placed-building increase | Main forms | Protection |
|---|---:|---|---|
| Downtown CBD | +20% | 2–6-story shops and offices in eligible infill parcels; not more tall towers | Keep plaza/spawn/road corridors and landmark view |
| Midtown | +40% | 3–8-story mixed-use apartments/offices, street-front shops | Keep drivable routes, intersections and 3-unit setback |
| Old Town | +35% | 2–5-story brick rowhouses and corner shops | Preserve existing low-rise character, historic block geometry |

1. Adjust `blockSpecs()` / legally vacant parcels, **not** generic overlap by reducing world-space avoidance.
2. For every addition test `rectHitsElevated()`, `rectHitsCurvedRoad()`, main roads, intersections, depots, mission checkpoints, ramps, garage access and fast-travel arrival locations. Keep at least 3 units of clearance from a building exterior to prohibited drivable corridors. If space disallows the target, record actual counts instead of forcing overlaps.
3. Use current geometry/texture/mat atlas/mesh batching and existing instanced window approach; no new GLB. Add physical static proxy for every newly accessible structure and keep `WORLD.buildings`, roofs/world-map, and camera blockers coherent. No visible walls with missing physics or solid invisible walls occupying roads.
4. Avoid dozens of independent shaders/materials. Target <=8 additional static-material draw calls on PHONE_LOW and <=16 on DESKTOP_HIGH for **city infill specifically**; compare counts with baseline.
5. Heights by zone: CBD infill 8–30 units, Midtown 12–32, Old Town 7–20 (avoid replacing existing landmarks or skyscrapers).

### 3.3 Three suburban architecture options (Martin selects one)

All three use **existing locally generated geometry** and materials (no new assets), allow colors/roof shapes to vary, and preserve the existing road network. An option controls visual variety **without** bypassing property-boundary or physics validation.

**Option A — Light residential refresh (lowest cost)**
- Four types: detached bungalow (45%), 2-story detached house (30%), duplex (15%), small corner shop (10%).
- Repeat existing wall/roof materials; <=12 additional suburban draw calls beyond baseline.
- House and small-building pool target is >=1.40× measured previous suburban house count; nominal cap 210 non-desktop / 390 desktop.
- Pros: lower scope and simpler collision geometry. Cons: neighborhood still mostly residential.

**Option B — Mixed American small town (RECOMMENDED DEFAULT)**
- Seven types and exact target shares of the **new suburban structure pool**: 1-story bungalow 30%, 2-story detached home 20%, duplex 15%, connected townhouse 12%, 2–3-story walk-up apartment 10%, corner convenience store 8%, auto workshop / small storage shed 5%. Shares total 100%.
- A small gas station with forecourt may be added **in place of** one convenience store, only if it fits existing flat road-adjacent land and can be built using existing geometry; otherwise keep the store. No interactive fueling feature.
- Place shops/workshops near suburban main routes, duplex/townhouses near intersections, bungalows on minor roads, and apartments only on relatively flat parcels. No storefronts on steep mountain or narrow residential roads.
- Nominal maximum pool: 210 non-desktop, 390 desktop. Achieve >=1.40× **actually placed** structures vs comparable baseline; preserve residential house minimum >=75% of placed total.
- Maximum +20 distinct suburban draw calls over baseline on PHONE_LOW; +30 on desktop. Share at most 6 opaque materials and 2 roof materials across variants; use instancing per geometry/material batch.
- Pros: visibly different suburbs and plausible land use, without imports. Cons: needs parcel-specific collider variations and careful placement.

**Option C — Full neighborhood identity (higher cost; NOT the default)**
- Ten types: A/B set plus neighborhood clinic, local supermarket, low-rise motel. Allocate 6% of new pool to those 3 types by reducing bungalow/house shares as reviewed.
- Target >=1.65× successfully placed pool; cap 240 non-desktop / 430 desktop, subject to safety checks.
- Requires an extra visual/performance review and may not meet 30 FPS without reducing other effects. C is not authorized by the present recommended B scope unless Martin explicitly selects it and Claude reviews revised numbers.

**Default proposal: Option B.** To approve A or C instead, issue a revised v1.2 with new counts/costs; don't silently switch option inside Codex.

### 3.4 Shared suburban placement requirements (T-004D)

1. Sample candidate roadside positions with step 5 (previously 8), while maintaining property orientation toward roads, bounds, collision and terrain checks.
2. Keep `nearestTerrainRoadDist >=8.5` minimum unless a more accurate swept-footprint/road polygon test is added; acceptable terrain height range <=3.5 world units across sampled parcel corners.
3. Use rotated footprints appropriate to each type and require >=3 units of open separation between structure exterior footprints. Do not rely solely on center-distance `tooClose()` with a constant 17.
4. Preserve driveable sidewalks/routes, player spawn, garages, seven ramps, six delivery depots, mission areas, waypoints, fast-travel pads and overpass structures.
5. All accessible building shells must be solid. Use a small number of appropriate oriented static `CANNON.Box` shapes per building, grouped spatially for performance. Roofs do not need to be separately driveable unless accessible.
6. Existing `WORLD.suburbHouses` should remain meaningful for map rendering; if mixed categories require a new collection, keep a compatible alias or map integration. Log actual placed count by building type and zone, not merely the cap.
7. Do not allocate new lights per structure or repeated unique texture canvases. Texture/material variations should be cached/shared. Reuse InstancedMesh for the repeating elements.

### 3.5 Tree trunk physics and suburb collider repair (T-004C, implement **before** density additions)

**Tree collision:**
1. Every tree reachable within the near interaction zone must have a physical trunk proxy; leaves/branches remain visual-only. Use a low-cost upright `CANNON.Box` or correctly oriented `CANNON.Cylinder` with radius-equivalent 0.35–0.65 world units before per-tree scale and trunk height 3.0–6.0 world units, adjusted to visible trunk type (palm, pine, broadleaf). Do not simulate foliage as a mesh collider.
2. To keep the roughly hundreds of tree colliders affordable on phones, use grid-indexed **nearby** static collision activation, not creation/destruction per frame: partition trees into 32 × 32 unit cells; refresh eligible bodies every 0.5 seconds; keep collision within 140 units of the player/active vehicle, allow hysteresis removal only beyond 180 units. On teleport or scene initialization refresh immediately. Do not deactivate colliders near an AI car physically interacting with the tree. If these radii fail the high-speed test, increase the activation distance rather than allowing tunneling.
3. Pool collider objects (or use a stable preallocated set if cheaper), update Cannon SAP broadphase/AABB correctly after activation/repositioning. Never place a proxy inside an occupied vehicle at activation. Nearby trees must be solid even at LOW quality.
4. Target <=1 additional tree-collider manager update every 0.5 seconds. No distance scans across all trees every rendered frame. Record active-collider counts; never claim collision coverage if cap truncates near trees.
5. Collision applies to player car and walking player; avoid triggering unsolicited money changes or changing damage values. At high speed, verify the fixed-step collider can stop/deflect the vehicle without passing through; if ordinary static proxies cannot pass tests, report need for a separate swept-collision change rather than silently widening proxies so much they block the road.

**Suburban building collision:**
1. Keep grouped static compound bodies for houses (maximum 16 shapes per body), but group by **spatial neighborhood**; no one compound body should span unrelated distant plots.
2. For each house `h`, ensure shape local offset accounts for `h.y - body.position.y` and center height. Compute physics orientation from actual placed building rotation; shape extents correspond to visible wall footprint/height (including scaled large houses).
3. Verify no collision overlaps on normal terrain and slopes. Expose or use debug inspection to compare collider centers to visible instance matrices (horizontal/vertical center deviation <=0.35 world units and effective footprint boundary deviation <=0.5 world units).
4. Verify physics collider is actually registered and active; keep static bodies on proper collision filter groups/masks. Touching walls must not trap vehicles underground or cause unstable bounce.
5. City buildings already have box colliders in general. Audit reachable missed objects/doorways; do not add duplicate colliders over an already correctly protected city structure.

**Protected spaces / anti-regression:**
- Minimum 3.0 world units between structure/trunk physical proxy and any designated vehicle travel corridor where that object is not physically present in the intended scene. Visible street-side trees may remain close to roads only if their colliders match visuals and don't intrude into the lane.
- No invisible collision in parking, fast-travel arrival, deliveries, race checkpoints or stunt takeoff/landing zones.
- Collision diagnostics should include tree type and collider proxy positions. If physics performance degrades, optimize pooling/spatial partitioning before reducing collision fidelity near the player.

### 3.6 Performance and stability limits

- Samsung S26 Ultra / PHONE_LOW and Tab S11 / TABLET_MED retain default 30 FPS cap. Physical-device performance target: median rendered FPS >=29, p5 >=24, proportion of frame intervals >50 ms <=2%, and no sustained 2-second interval below 20 FPS average. Desktop 60 FPS remains a target.
- No WebGL context loss, no new CDNs, no save resets, no new render pass, no per-frame construction of geometry/materials/physics bodies, no mass creation of physics bodies at runtime.
- Test baseline and candidate after 60 seconds warmup: 5-minute downtown drive, 5-minute suburban residential drive with tree/building interactions, 5-minute high-speed highway/urban route. Report device, browser version, orientation, quality preset, dynamic resolution scale, FPS median/p5/long-frame share and crash/stutter observations. Do not call a headless run real-device measured.
- If current baseline fails on a particular device, document baseline separately and avoid claiming the new feature met target. Changes to approved density numbers or traffic pool after acceptance need Martin approval of an updated version.

## 4. Sequential implementation tasks (one code PR at a time)

| Task | Owner | Dependency | Deliverable and numbered acceptance |
|---|---|---|---|
| **T-004A** Design/review | ChatGPT; reviewer Claude | T-003 pipeline scheduling | This file, options A/B/C, code-inspected risks; await Martin approval |
| **T-004B** Traffic population + Ferrari exclusion | Codex; reviewer Claude | Approved T-004A, no active code PR | §3.1 count table exactly; 0 ordinary AI Ferrari, test 5 fresh/5 recycled loads, spawn/route separation, syntax + offline, compare nearby counts |
| **T-004C** Tree and existing house collision repair | Codex; reviewer Claude | T-004B accepted | §3.5 physical tree trunks and corrected house Y offsets; physics wireframe tests, near/far activation and high-speed contact tests; syntax + no save regressions |
| **T-004D** Suburban variety and increased structure density | Codex; reviewer Claude | T-004C accepted | §3.3 Option B (or separately approved alternative), §3.4 7 types, counts >=1.40× baseline when parcels safe, real collider per accessible structure, no protected-area overlap; syntax+layout/map+FPS report |
| **T-004E** City district infill | Codex; reviewer Claude | T-004D accepted | §3.2 city placed count targets: CBD +20%, Midtown +40%, Old Town +35% when valid; preserved road corridors, physical proxies, skyboxes/views, syntax+performance report |

For each step Codex opens `codex/T-004B-traffic`, `codex/T-004C-collisions`, `codex/T-004D-suburb-variety`, or `codex/T-004E-urban-infill` from the **latest** `main`; Codex never merges and never edits docs, binary assets, or `sw.js` CACHE. Claude reviews/merges/releases through COLLAB v3.1. Martin physically accepts each release before the next code PR starts.

## 5. Verification plan

### 5.1 Automated / headless tests
1. `python3 tools/test/syntax_check.py` prints `RESULT: PASS`.
2. Reuse existing camera/HUD checks; no modification of existing functional tests unless associated features legitimately changed.
3. Static/procedural spawn audit counts vehicle classes and new buildings by zone; verify 0 `isAI` Ferrari visuals.
4. For each of 10 evenly sampled playable positions and at least 4 view headings, check road/protected-zone overlaps and building/tree collider alignment.
5. In a headless physics-capable run, drive vehicle into at least 10 trunks (palm/pine/broadleaf), 10 suburban walls including 5 on slopes, and 5 new urban buildings at test speeds 20, 60 and 120 km/h; verify no full pass-through. Run high-speed 180 km/h smoke tests and report any tunneling separately; do not claim an unperformed 180 km/h pass.
6. Confirm `PHYS_DEBUG` cyan shapes align with accessible building walls and trunks, with no invisible solid obstruction over roads.
7. After teleport, verify nearby colliders activate before the vehicle resumes movement; walking player must not move through normal walls/trunks.
8. Verify normal delivery, missions, police pursuit, purchases, saved cars and offline PWA still work.

### 5.2 Martin's real-device evaluation
- Samsung S26 Ultra (PHONE_LOW) and Tab S11 (TABLET_MED), landscape. 60-second warmup; then each of 3 scenes for 5 minutes under same route/settings as previous release. Record median FPS, p5 FPS, >50 ms rendered frames %, qualitative stutter/heat and any crash.
- Test street driving at night/day, traffic intersections, tree collisions in all three species, suburban structure collisions on flat and sloped land, fast travel near suburb, entry/exit car beside buildings, delivery/police driving and terrain slopes.
- Submit screenshots of the same city/suburban viewpoints before/after and a short count table; subjective urban density and regional variety need Martin's explicit acceptance, not inferred from counts.
- `Verification` stays `designed` until code reviewed; real-device numbers are not marked measured unless Martin supplies them.

## 6. Risks, review issues and approval questions

1. **Current tree pass-through is code-supported; house pass-through is not universally proved.** Existing house compound colliders exist, but Y-offset mismatch and grouping require testing before root cause is finalized.
2. Tree proximity activation interacts with 30 FPS budget, SAP broadphase and player teleports. Claude must review the proposed 140/180-unit activation radii and whether an always-static simplified collider is cheaper in this codebase.
3. Increased vehicles and static structures may regress performance. Prioritize correct near-player collisions and the 30 FPS measured target; if incompatible with density targets, propose a new reviewed version rather than silently changing numeric requirements.
4. **Martin decision:** select Option A, B or C for suburban style. This v1.1 recommends **B**, and all detailed acceptance for T-004D assumes B until Martin approves another option with an updated spec.
5. **Martin/Claude scheduling:** the currently approved T-003D Game Hub and T-003E localization remain ahead in the existing pipeline; T-004 work stays queued until Martin/Claude explicitly reprioritize at an allowed gate.
6. No game code was changed by this design. Nothing in this file claims that collision, density or FPS targets have been measured or achieved.
