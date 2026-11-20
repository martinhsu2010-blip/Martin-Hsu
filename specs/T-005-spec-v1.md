# T-005 World coherence cleanup — spec v1 (DRAFT, not approved)

Status: DRAFT by Claude from ChatGPT's issue list + Martin's play reports. NOT registered. Becomes binding only after Martin says "批准 T-005 v1" (then stored verbatim, and D-019 records changed targets).
Why a new task and not a T-004E reopen: T-004E is Done, Martin-accepted and released (vh-2026-11-20-02). These issues also touch T-004B (traffic), T-004D (suburbs) and the original spawn vehicle list, and D-017's approved numbers (traffic table, building caps) are binding, so changing them needs a new decision (D-019), not a rewrite of a finished task.
Implementer: Codex (cross-system: world generation, route/traffic, spawn vehicles).
Split (one code PR at a time, and each PR stays small enough for one Codex usage window):
- **T-005A** — spawn cleanup + legal, denser traffic (Parts 1–2). Ships first.
- **T-005B** — suburb frontage + city infill coverage (Parts 3–4). Starts after T-005A is Martin-accepted.

Source of the problems: Martin's screenshots and play reports as relayed by ChatGPT. Claude has not seen the screenshots; Martin attaches them to each Codex task. Causes below marked (hypothesis) come from reading main 4c0d8db and must be confirmed by the audit in each part before fixing.

---
## T-005A

### Part 1 — Remove the yellow car behind the spawn
Facts (main 4c0d8db): the player starts on foot at (98, 22). `spawnVehicles()` parks "Ferrari GT" (red) at (103, 26) and **"Muscle 69" (yellow, `archetype: 'MUSCLE'`, black stripes, no `model`) at (103, -14)**. A vehicle without `model` gets the Ferrari GLB through `applyFerrariModel`, so the yellow Muscle 69 is the "yellow Ferrari". It is not a Kenney traffic car.
Required:
1. Delete the Muscle 69 entry from the parked list in `spawnVehicles()`. Keep Ferrari GT (103, 26), Apex 4x4 and the VCPD Shelby unchanged.
2. Keep the garage "Muscle '69" button and the `MUSCLE` archetype working (a player can still pick it; do not touch garage, saves, i18n strings or vehicle physics).
3. `WORLD.vehicles` indices shift by one for vehicles after index 1. Audit every use of fixed indices and every name lookup; update `tools/test/traffic_check.mjs` (expects the four-entry list) and any other test that assumes the old order.
4. Report every non-traffic, non-police vehicle within 60 units of (98, 22) before and after, with color and model, so no other yellow/Ferrari-looking car remains near spawn. Do not change anything else you find; list it.
Acceptance: fresh load on PHONE_LOW, TABLET_MED, DESKTOP_HIGH has no yellow car within 60 units of spawn; Ferrari GT is still enterable; saves from the current release load; garage still offers Muscle '69.

### Part 2 — Traffic only on legal roads, then more of it
Facts: traffic follows 10 fixed routes in `ROAD_NET.routes` (R0–R4 grid/coastal loops, 2 ring lanes on the elevated road, north and south loops, 1 suburb loop). `recycleTraffic()` and `findInitialTrafficSlot()` place a car on any route sample, so if a route sample is off the drivable surface, cars appear off-road. Candidate causes (hypothesis): (a) route corners rounded with radius 14 (`roundCorners`) plus lane offsets 4–7 leave the road at turns; (b) R0 joins the straight x=110 line to the coastal ribbon with a different offset (7 vs 4); (c) suburb loop lane offset 3.2 on a road of half-width 6.5, plus a loop built by concatenating two roads; (d) a car shoved or flipped by the player stays wherever it ended up (recovery only fires after 5 s stuck, and only off screen).
Required:
1. **Audit first (report before fixing).** Headless script `tools/test/route_legality.mjs` (new): for every sample of every route, test that the car footprint (use the real Kenney bounds from `traffic_harness.mjs`) lies inside the drivable surface of the road the route belongs to (grid road, ribbon, curved road, elevated ring with its own `y`, terrain road, intersection) with >= 1.0 unit margin, and that `p.y` matches the deck/terrain the car is placed on. Print violations per route with coordinates. Commit the script; it must pass at the end.
2. Fix the routes (and only the routes) so the audit has 0 violations. Do not widen roads or move any building to hide a bad route.
3. Placement guard: `findInitialTrafficSlot()` and `recycleTraffic()` must reject a slot that fails the same legality check (cheap, precomputed per route sample at init, no per-frame cost).
4. Drift guard: an AI car whose center is more than 8 units from its route polyline for more than 2 s is flagged `trafficRecovery` exactly like a stuck car (same distance/visibility/clearance gates as today; still never teleports on screen). Add `offRoute` to `__VH.trafficDiagnostics()`.
5. **More traffic** (this is what Martin asked for; legality comes first). New `DENSITY.traffic` values, proposed:

| Preset | now | proposed |
|---|---|---|
| PHONE_LOW | 18 | 22 |
| PHONE_MED | 24 | 30 |
| TABLET_LOW | 22 | 28 |
| TABLET_MED | 32 | 40 |
| TABLET_HIGH | 36 | 46 |
| DESKTOP_MED | 40 | 50 |
| DESKTOP_HIGH | 52 | 64 |
| DESKTOP_ULTRA | 68 | 80 |
| IGPU_LOW | 20 | 24 |
| IGPU_MED | 28 | 34 |
| IGPU_HIGH | 36 | 44 |

   Allowed: up to 3 new legal routes (for example Maple Ave and Valley Loop, which have no traffic today), spacing and rules unchanged (20 units between cars, 25 from the player's car, recycle rules unchanged, ordinary AI stays Kenney-only, 0 Ferrari).
   Performance guard (reviewer-set, adjust only with Claude's approval): report `renderer.info.render.calls` on PHONE_LOW / TABLET_MED / DESKTOP_HIGH before/after in a real browser if one works (otherwise a clearly labelled structural count), and physics step time from `tools/test/traffic_audit.mjs`. If a preset adds more than 12 draw calls or its physics step grows more than 25 %, keep that preset's old count and say so; do not trade away frame rate.
6. Existing tests stay green: `traffic_check.mjs` (update its expected table), `collision_check.mjs`, `i18n_check.mjs`, `syntax_check.py`; offline start unaffected.
Acceptance: `route_legality.mjs` 0 violations; 10-minute headless run per preset (cars only, no player) shows 0 cars beyond 8 units from their route and `offRoute` 0 at the end; counts equal the table (or the per-preset exception above); Martin drives the main loops and the suburb on S26 Ultra and Tab S11 and sees no car off the road surface.

Out of scope for T-005A: buildings, trees, suburbs, camera, HUD, Hub, economy, saves, police, NPC pedestrians.

---
## T-005B (written now so ChatGPT and Martin see the whole plan; Codex starts it only after T-005A is Done)

### Part 3 — Suburb houses face the road, no bare strip in front
Facts: `buildSuburbParcels()` offers each road side two setbacks (12 and 28 from the road edge). Candidates of all setbacks are shuffled by a golden-ratio stride (`h.order`) before the quotas are filled, so a house on the 28-unit row can be chosen while the 12-unit parcel in front of it stays empty (hypothesis for "lots of bare ground between road and houses"). The old `buildSuburbs()` pass also seeds trees with a fixed 12-unit offset.
Required:
1. **Audit first:** per suburban road (Suburb Main, Maple Ave, Hillcrest Loop, Valley Loop) and side, list the continuous road-edge runs with no structure within 14 units of the road edge, why (slope > 3.5, junction, depot/fast-travel/protected clearance, tree, shuffled-away, cap) and the total/maximum run. Report for PHONE_LOW and DESKTOP_HIGH.
2. Fill order: a second-row parcel (setback 28) may only be used if the first-row parcel in front of it along the same road is already used or illegal. Front face of a first-row house should sit 6–12 units from the road edge (compute the setback from the house depth instead of a constant).
3. Remaining bare frontage: add a cheap roadside verge (sidewalk/lawn strip, merged or instanced, no per-house meshes) along suburban roads so the ground between road edge and house front reads as a yard, not raw terrain. Draw-call limit for this part: +4 on PHONE_LOW, +8 on DESKTOP_HIGH.
4. Counts: placed houses must not drop below the T-004D result. The caps (210 phone / 390 desktop) and the Option B shares stay. If the audit shows the cap itself is what leaves frontage bare, report it and propose a new cap; do not raise it silently (that is a Martin decision).
5. Keep every T-004D collider rule (collider from the base bottom to the wall top, <= 16 shapes per body, `WORLD.suburbHouses` for the map) and the tree-trunk clearance rule.
Acceptance: after the fix, max bare frontage run <= 45 units on roads where terrain is legal, down from the reported audit; screenshots from the same camera positions as Martin's.

### Part 4 — City parcels that look forgotten
Facts: T-004E accepted a shortfall on DESKTOP_HIGH (placed CBD 33, Midtown 26, Old Town 89) because of soft rules: a 3-unit facade-envelope gap, a 10-unit street-tree/sidewalk strip, plus the hard rules (elevated/curved road, protected points, plaza, runway, stunt corridors, trees). Martin still sees legal empty lots.
Required:
1. **Audit first:** for CBD / Midtown / Old Town, grid every block interior at 2-unit steps and list rectangles >= 10 x 10 that are legal under the hard rules but empty, with the rule that rejected them (histogram by rule). Report per preset.
2. Relax only the soft rules, in this order, and re-measure after each: 3-unit facade gap to 2; allow an 8 x 8 shell variant when 10 x 10 does not fit; shrink the street-tree strip where no tree exists. Never overlap a road, elevated/curved road, protected point, plaza, runway or stunt corridor; never force an overlap to hit a number.
3. Targets: no remaining legal empty 10 x 10 lot in any district under the hard rules (audit proves it); report new placed counts per district per preset against the T-004E counts.
4. Same rules as T-004E for every new building: static collider matching the visible shell down to its base, in `WORLD.buildings` / roofs / camera blockers, facade offset 0.06, batched shells. Draw-call budget stays T-004E's (+8 PHONE_LOW, +16 DESKTOP_HIGH) counted from the *current* build, measured with `renderer.info.render.calls`.
5. Extend `collision_check.mjs` impacts to the new shells (0 pass-through).
Acceptance: audit shows 0 legal empty lots; Martin confirms on Tab S11 that the blocks no longer look unfinished.

---
## Task entries to register after approval (TASKS.md "Ready for Codex")
### T-005A Spawn cleanup + legal, denser traffic
Owner: Codex | Priority: P1 | Reviewer: Claude | Depends on: T-004E (Done) | Branch: `codex/T-005A-traffic-legal` | Spec: `specs/T-005-spec-v1.md` Parts 1–2.
Claude notes: audit script first (report violations before fixing); legality before density; keep the garage Muscle '69; update the traffic test's vehicle list; do not edit sw.js CACHE or docs.
### T-005B Suburb frontage + city infill coverage
Owner: Codex | Priority: P1 | Reviewer: Claude | Depends on: T-005A (Done) | Branch: `codex/T-005B-coverage` | Spec: `specs/T-005-spec-v1.md` Parts 3–4.
Claude notes: audits first; relax soft rules only; no silent cap increase; collider and draw-call rules as T-004D/E.

## DECISIONS entry to register after approval
D-019 | approved | Changes to D-017 numbers: ordinary traffic table raised as in T-005 Part 2 (per-preset exception allowed by the performance guard); suburban caps unchanged unless a later audit proposes otherwise; city infill soft gap rules may be relaxed as in T-005 Part 4. The parked Muscle 69 is removed from the spawn area (garage option stays).
