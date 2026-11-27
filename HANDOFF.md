# VICE HORIZON VI — Project Handoff

Written for another AI assistant (e.g. ChatGPT) or developer picking up this project.
Last updated: 2026-11-20, game version `vh-2026-11-20-02` (see `CACHE` in `sw.js`).
Owner: martinhsu2010-blip (Traditional Chinese speaker, Taiwan). Explain things to the owner in Traditional Chinese; write prompts for Gemini in English.

## What this is
An open-world driving browser game (GTA-style): on-foot + vehicles, city, police chase, missions, radio, day/night.
- Live: https://martinhsu2010-blip.github.io/Martin-Hsu/ (GitHub Pages, installable PWA, works offline)
- Stack: Three.js r160 + cannon-es 0.20, no build step for the game itself. **Everything is in one file: `index.html`** (~9,900 lines). All libs, models, textures and fonts are vendored locally (`libs/`, `models/`, `textures/`, `fonts/`) so it runs offline.
- History: prototyped in Gemini Canvas, then developed with Claude.

## Repo layout
- `index.html` — the whole game (HTML + CSS + JS). Section banners look like `// ==================== N. TITLE ====================`; grep for them to navigate.
- `sw.js` — service worker. **To ship an update, bump `CACHE` (line 3)**; players auto-reload on the new version.
- `models/cars/` — GLB car models: `porsche911.glb`, `lexuslc500.glb`, `fordgt500cop.glb`, `kenney_traffic.glb`. Ferrari and people/props are in `models/` too.
- `CREDITS.txt` — asset credits (Poly Haven CC0, Kenney CC0, Quaternius; Porsche/Lexus/Ford are player-provided Sketchfab models, licenses unverified).
- Note: this repo holds only the **built output**. The patch scripts that generated it live in Claude's sandbox and are not in the repo; edit `index.html` directly.

## Map of `index.html` (search for these banners)
1. Global state, input, per-device quality presets (PHONE_LOW … DESKTOP_ULTRA, `DENSITY.traffic`, etc.)
2. Web Audio: radio + RPM engine synth
3. cannon-es physics world (ground is a `CANNON.Box`)
4. Three.js renderer, Physical Sky, PMREM, post-processing; **day/night cycle** (`skyAtHour`, `updateDayCycle`, 1 game hour = 40 s, starts ~17:36)
5. Procedural PBR textures
6. City districts, road network, elevated ring expressway (12 parallel one-way ramps), terrain roads/hills, suburbs, facade kit, **tree system** (InstancedMesh, ~693 trees, wind sway)
7. People: player (Soldier.glb), NPCs
8. Vehicles: `RealisticRaycastVehicle`, Ferrari (LODs + livery shader), **new car system** (`CAR_MODELS`, `loadCarModel`, `applyCustomModel`), Kenney traffic cars
9. Physics-object sync, water, **police chase**
10. Enter/exit car, missions, third-person camera
11. **Earning systems**: delivery jobs + stunt jumps (`DELIVERY`, `STUNT`, `SAVE`)
12. World map, fast travel, waypoints
13. Touch joystick, quality toggle, weather, keyboard
14. Startup + fixed 1/60 s main loop

Debug handle: `window.__VH` exposes internals (SAVE, STUNT, DELIVERY, CAR_MODELS, TREES, DAY, loadCarModel, startDeliveryJob, …).

## Current gameplay systems
**Cars** (`CAR_MODELS` registry): Ferrari (default, free), Ford Shelby GT500 (police car, used for the chase system and roadside cop), Porsche 911 (price $25,000), Lexus LC 500 (price $18,000). Buying in the garage needs two clicks (4 s confirm window). Wheels/physics are laid out from each model's wheel nodes at load time.

**Money / save** (`localStorage` key `vh_save`: cash, owned[], jumps{}, deliveries, upgrade):
- *Delivery jobs*: 6 depots on roads. Drive into a depot (<7.5 m, <45 km/h) → random destination 320–1500 m away. Reward = round((350 + dist×1.2)/10)×10; time limit = round(75 + dist/9) s; ×1.2 (rounded to 10) if >35% time left, ×0.5 if late. Fast travel is blocked during a job. Deliver within 10 m at <35 km/h.
- *Economy (D-014, T-001B)*: crates $400 (persisted in `SAVE.collectedCrates`); missions DRIFT 1200 / RACE 1400 / STUNT 1600 (300 s cooldown each); police escape 600 (600 s); ramps first $900, repeat min(450, 180+10·round(dist/20)) (120 s, shared 90 s with airtime); airtime min(400, round(t·150)) if ≥0.65 s, 90 s cooldown. Cooldowns live in `SAVE.rewardCooldowns` (Date.now-based).
- *Stunt jumps* (7 ramps): first clear $1,500; later $300 + distance×0.4. Landing detection uses `wheel.raycastResult.hasHit` (cannon-es `isInContact` is always false).

**Traffic**: Kenney low-poly cars (11 types, weighted). Density per device, e.g. phone 10 … desktop-ultra 34. Cars farther than 470 m are recycled to route points 150–360 m from the player; AI cars >430 m from the camera have physics removed from the world.

**World**: large city with CBD skyscrapers, old town, midtown, hotels, suburbs/hills, Mount Chiliad road, elevated ring road, coastal road, sea. Roads are all connected. Map screen with fast travel and waypoints.

## Code map (function/section names; line numbers as of `vh-2026-11-20-02` drift, so `grep -n` the name)
- Quality/device: `detectDevice` (~1509), `QUALITY_CONFIG` (~1473), `DENSITY` (~1560), `SAVE` (~1563). Preset names `PHONE_LOW`, `TABLET_MED`, `DESKTOP_HIGH`, `IGPU_*`. Poly Haven models (facade kit, lamps) are skipped on PHONE+LOW.
- Language: `STRINGS` table at the top (~20, a separate `<script>`), `tr()`, `changeLanguage` (~8102).
- World/physics helpers: `WORLD` (~2052), `ROAD_NET` (~2577), `addStaticBoxCollider` (~2479), `onCurvedRoad`/`rectHitsCurvedRoad` (~2643/2657), `rectHitsElevated` (~3023).
- City: `buildKitFacades` + `updateFacadeLOD` (~3779/3957), `blockSpecs` (~4060), `cityInfillParcels`/`buildCityInfill` (~4096/4137), `cityParcels` collected in the city build (~5200-5400).
- Trees and suburbs: `addTree` (~4211), `buildTrees` (~4381), `initTreeColliders`/`refreshTreeColliders` (~4459/4522), `buildHouseColliders` (~4553), `buildSuburbParcels`/`buildSuburbMeshes` (~4611/4679).
- Vehicles and traffic: `spawnVehicles` (~7631), `TRAFFIC` (~8738), `updateTrafficPhysics` (~8772), `recycleTraffic` (~8833); vehicle class has `supportOnTerrain` (~7367).
- Gameplay: `startMission` (~8174), `teleportTo` (~8267), `CAM` + `updateCameraAndLights` (~8308/8350), `STUNT`/`DELIVERY` (~8543/8592), `startDeliveryJob` (~8641).
- Map/Hub: `drawWorldMap` (~9070), `fastTravelTo` (~9191); HUD/Hub/touch controls live in section 11 (~9307); startup and main loop in section 12 (~9796).
- Tests: `tools/test/` (one `*_check.mjs` per system plus `*_harness.mjs`; `hud_layout_check.py` needs a browser). Headless Chrome can reach DESKTOP/HIGH only with a spoofed discrete GPU name (see City infill notes).

## Pitfalls already learned
- cannon-es `Box` chassis does not collide with `Trimesh` terrain → handled by `supportOnTerrain()`.
- Don't use `isInContact`; use `raycastResult.hasHit`.
- New car paint materials must drop the Ferrari flake `normalMap` or they get white speckles.
- Keep draw calls low: static meshes are merged, trees/houses are InstancedMesh, far Ferrari uses a simplified LOD.
- Mobile performance matters most; check any added feature on the PHONE_* presets.

## Working agreement
See `COLLAB.md` (v3.6) and `AGENTS.md`. Code changes arrive as Pull Requests from Codex (or Gemini via Antigravity Remote Agents for low-risk tasks) and are reviewed/integrated/released by Claude.

T-006 (zh-TW `shared_space` label) is the first Gemini Stage 1 trial; see `TASKS.md` and `specs/T-006-spec-v1.md`.

## Release process (how updates are shipped)
1. Edit `index.html` (and assets if needed).
2. Bump `CACHE` in `sw.js`.
3. Commit to `main`; GitHub Pages deploys in ~1–2 min. Confirm by fetching `/sw.js` on the live site.

## Done so far (newest last)
Facade/terrain/ring-road expansion → world map + fast travel → new trees, more traffic, connected roads, angled interchange ramps, day/night cycle → Porsche/Lexus (purchasable), Ford police car, Kenney traffic, delivery jobs, stunt-jump rewards, re-verified jump placement, save game.

## Open ideas (nothing committed)
- Balance prices/rewards after real play.
- More purchasable cars or upgrades.
- Verify licenses of the three Sketchfab car models before any public release.

## Camera (T-003B)
All third-person camera defaults live in `CAMERA_CONFIG` (near the `PerspectiveCamera` creation): foot 4.2 / 12°, chase near 7.2 / 10°, far 10.5 / 14° (distance / pitch, world units), FOV 60 → 68 (nitro 72), recenter after 2 s idle, collision padding 0.6 with immediate pull-in and eased recovery. Hood and bird views keep their old optics. Regression harness: `node tools/test/camera_check.mjs <base-sha>` (Node only, not a browser test).

## HUD (T-003C)
The permanent toolbar is gone: tapping the minimap (`radar-container`, now a button) opens the interim `#quick-actions` dialog with the original buttons and IDs (quality, missions, garage, cop chase, radio, camera, sky, settings) plus map, the crate counter, RPM/nitro bars and keyboard help. T-003D replaces this dialog with the Game Hub. Layout sizes are CSS variables in `:root` (`--radar-size`, `--steer-size`, `--gas-*`, `--brake-*`, `--aux-size`) with three modes: tablet landscape (>= 960x560), compact, and short (< 430 px high; pursuit bar moves under the minimap). Safe areas use `env(safe-area-inset-*)`. Radar state is in `RADAR` (cached context, 10 Hz / 8 Hz LOW, skips drawing while hidden or behind a dialog/overlay). `releaseHudControls()` clears held input on resize/orientation/blur/hidden. Tests: `node tools/test/hud_check.mjs`, and `python3 tools/test/hud_layout_check.py http://127.0.0.1:8765` with a local server (`CHROMIUM_BIN=/usr/bin/google-chrome`).

## Game Hub (T-003D)
`#quick-actions` is now the fullscreen Game Hub (native `<dialog>`). Tabs (`HUB_TABS`): `quick-actions-map`, `pill-mission`, `pill-garage`, `hub-world-tab`, `pill-settings`; panels (`HUB_PANELS`): `world-map`, `missions-modal`, `garage-modal`, `hub-world`, `settings-modal`. `openGameHub(panel)` releases input, hides panels, starts the 500 ms map redraw only on MAP; `closeModals()` is the single close path (Escape via `cancel`, M, ✕, `wm-close`, mission start, summon, fast travel). WORLD holds sky/day-cycle, cop chase, crate counter and RPM/nitro bars; SETTINGS holds quality, camera, radio plus the old settings. Because the dialog is in the top layer, `#notice-area` is moved inside it while open and back to `body` on close — anything else that must show over the Hub has to do the same.

## Language (T-003E)
All player-visible text lives in one table, `STRINGS` = {en, zh-TW} (between `I18N_TABLE_*` markers near the top of `index.html`); use `tr('key')` (or `VH_I18N.text`). `VH_I18N` reads `vh_save` once at startup: no key = English, a save without a valid `language` = zh-TW, a valid choice wins. `changeLanguage(lang)` (selector `#language-select` in SETTINGS) writes `SAVE.language`, converts copied names through `VH_I18N.name`, and refreshes panels, aria/title via `data-i18n*` attributes, map chips/selection, garage, HUD, pursuit text and the active banner. Banners must be passed as callbacks (`showBanner(() => tr('k'), () => ...)`) so they re-render on a switch. New text must be added to both languages; CI (`tools/test/i18n_check.py`, `i18n_check.mjs`) fails on raw CJK outside the table or on mismatched keys. `manifest.webmanifest` is English, `manifest.zh-TW.webmanifest` Chinese; the `<link rel=manifest>` href follows the language.

## Traffic (T-004B)
Ordinary traffic pool sizes are `DENSITY.traffic` per preset (spec T-004A §3.1). Ordinary AI (`isAI && !isPolice`) is always `modelKey 'kenney'`; `setDetail`/`applyFerrariModel` return early for it, and a missing Kenney subtype keeps the geometric fallback. `TRAFFIC` holds the rules: spawn via `findInitialTrafficSlot` (20 units between cars, 25 from the player's car), `recycleTraffic` every 1.2 s moves at most 2 cars that are > 470 units away (or flagged `trafficRecovery`) and not on screen, to an off-screen slot 125-260 units away with 30-unit clearance, never within 120. `updateTrafficPhysics()` runs every frame before `physicsWorld.step`: a car wakes within 160 units or as soon as it is on screen; it freezes only beyond 200 units after `hideGrace` (2 s) off screen. "On screen" = camera frustum and within the 420-unit AI draw distance. Diagnostics: `__VH.trafficDiagnostics()`. Test: `node tools/test/traffic_check.mjs`.

## Collisions (T-004C)
Trees: `addTree()` moves a tree that lands on a terrain road to the roadside (3 units clear), keeping its ground embed; `buildTrees()` records the trunk geometry on each tree. `initTreeColliders()` (after `spawnVehicles()`) preallocates one static upright `CANNON.Box` per tree in `TREE_COLLIDERS` (32-unit grid). `refreshTreeColliders(dt)` runs before `physicsWorld.step` every 0.5 s (and immediately from `teleportTo`): trunks within 140 units of the player or near any active car join the world, those beyond 180 and not near an active car leave; a trunk occupied by a car or the walking player is deferred. Diagnostics: `__VH.treeColliderDiagnostics()`. Houses: `buildHouseColliders()` splits `WORLD.suburbHouses` into spatial cells (ceil(n/16) bodies, <=16 shapes); each box covers walls plus foundation (y - 2.8 to wall top, footprint 5.8 x 4.55, scaled for big houses); `house.collider` maps to body/shape/instance. New structures in T-004D/E must cover their visible foundations the same way. Test: `node tools/test/collision_check.mjs` (needs full git history for the baseline).

## Suburbs (T-004D)
`buildSuburbs()` still runs the old house layout only to seed tree exclusions; the rendered/physical structures come from `buildSuburbParcels()` (Option B, `SUBURB_TYPES` with shares, sizes, floors, units, roof kind) and `buildSuburbMeshes()`. Candidates: every 5th road point, both sides, setbacks 12 and 28, rotated SAT gap >= 3, road and terrain checks, pads/depots and existing trunks kept clear; each type's candidates are ordered by a golden-ratio stride so types spread over all roads; quotas by largest remainder, total from the cap (210 / 390) down to 1.4x baseline until every quota fills. Stats: `WORLD.suburbStats`. `WORLD.suburbHouses` holds the placed structures (map-compatible) with `ti`, `type`, `bottom`, `wallMesh/wallInstance`, `baseMesh/baseInstance` and `collider`. Tests: `node tools/test/suburb_check.mjs`, `collision_check.mjs`.

## City infill (T-004E)
`buildCityInfill(original, ...)` runs at the end of the city build, after the original `blockSpecs()` buildings (collected as `cityParcels`). `cityInfillParcels()` samples vacant offsets inside the original blocks (CBD / MID / OLD), 10x10 footprint, heights 16 / 20 / 12, only in cells that already have facade batches; it keeps >= 3 units of facade-envelope gap to original and added buildings, the 10-unit street-tree/sidewalk strip beside grid roads, elevated/curved roads, protected points (arrivals, depots, spawn, garage, ramps), the CBD plaza, the airport runway, three stunt corridors and tree trunks. Each shell is one instance in a per-district `InstancedMesh` reusing existing wall materials, plus a static box (ground to wall top), and is pushed to `WORLD.buildings`, `WORLD.roofs` (`infill: true`; map, facades) and `WORLD.cameraBlockers`. Facade kit offset for infill is 0.06 (0 would z-fight with the shell). Diagnostics: `WORLD.cityInfill`, `WORLD.cityInfillMeshes`, `WORLD.cityInfillStats` (baseline / target / added / shortfall per district). Test: `node tools/test/urban_check.mjs`. Testing notes: the Poly Haven facade kit is NOT loaded on PHONE+LOW, so check facades on TABLET/MED or DESKTOP/HIGH; headless Chrome reaches DESKTOP/HIGH only if `WEBGL_debug_renderer_info` is spoofed to a discrete GPU name (SwiftShader makes it IGPU).

## City coverage and fps readout (T-005B)
Suburb: first-row parcels are filled before setback-28 sites; `buildSuburbVerges()` builds one lawn mesh (`WORLD.suburbVerge`) clipped to the terrain cells and set +0.04 above the rendered terrain triangles (flat 0.04 over the city ground outside the terrain mesh). City: the coverage shells come from the offline layout in `tools/test/coverage_plan.mjs`; each shell's height/colour comes from the seed-5019 rule (FNV-1a per district), windows are recomputed from the final height (H=9 has none); `coverageColliders()` groups static boxes per 120x120 cell, at most 16 shapes per body. `WORLD.coveragePark` is one InstancedMesh with polygonOffset -2/-4 that covers every residual empty lot (`coverage_audit.mjs --details` must report 0 untreated). `?fps=1` (see `createFpsReadout()`) shows average FPS, lowest 1 s FPS over the last minute and the preset, and skips the auto quality / dynamic resolution loops while active. Tests: `coverage_audit.mjs`, `coverage_plan.mjs`, `coverage_browser.py`, CI workflow `coverage-render.yml`.

## Traffic legality (T-005A)
Routes live in `ROAD_NET.routes` (R0-R4 city/coast loops, R5/R6 the two elevated-ring lanes, R7/R8 north/south loops, R9/R10 suburb loops that turn back inside their own roadbed with `tightTurn` samples; see `buildExtraRoutes`). At startup `trafficSurfaceIndex()` (road triangles) + `trafficSampleLegal()` (oriented Kenney envelope, 1-unit margin) mark each sample `trafficLegal`, and `elevatedTrafficClearance()` (built with the elevated ring colliders) clears samples where a ring/spur slab, rail, median, column or pier cap would hit a car. `findInitialTrafficSlot()` and `recycleTraffic()` skip illegal samples. `updateTrafficPhysics()` checks every 0.2 s (`nextRouteCheck`) whether an AI car is more than 8 units from its route (`outsideTrafficRoute`) and requests recovery after 2 s; `__VH.trafficDiagnostics().offRoute` counts such cars. Tools: `node tools/test/route_legality.mjs [--base <sha> --all] [--drive-r1]` (CI), `traffic_endurance.mjs`, `traffic_audit.mjs <base> --guard [--proposed]`. Limit: the legality audit only knows asphalt and the ring structures; props or other obstacles on a street are not modelled (R4 near (-4, 629) and the R5 elevated lane near (-572, 228) stall there on every build).

## Midtown pilot status (T-010..T-013)
Released vh-2026-11-22-09. Device FPS (`?fps=1`, single run, Midtown West): Tab S11 TABLET_MED 46-50, S26 Ultra PHONE_MED 71-74; lowest-1s values (32 / 1) look like load hitches. T-013 is closed as a technical test with no ART PASS (D-042); do not roll out beyond the two pilot buildings.

## T-014B1 status
Released vh-2026-11-23-01 (PR #93, D-044). Site A showcase: two procedural buildings + 100 m visual street, no collision, fast-travel chip `Showcase Site A (No Collision)` / `展示區 A（無碰撞）`; test-only toggle `__VH.setShowcaseSiteAVisible`. Awaiting Martin device FPS and massing review; no ART PASS. Next phases T-014B2/B3 not approved; T-015 lighting still a separate draft. Measurement lesson: read draw calls with `renderer.info.autoReset=false`; mirror pass can re-draw showcase meshes.

## T-014B3 status
Released vh-2026-11-27-02 (PR #102, D-049). Near geometry (recessed glazing, projecting frames) for Site A Commercial A + Office B, sibling group `showcase_site_a_near`, layer-31 Near/Far switching (Far = the six B1 meshes untouched), shared layout `buildShowcaseFacadeLayout`; golden hashes unchanged; new CI test t014b3. Known deviation: Building A day window brightness above 1.05 x B2.1 (Martin accepted). Device FPS accepted by Martin (D-050; phone day avg 68.4, tablet night avg 65.6 / low 58; no ON/OFF pair). Art accepted provisionally by Martin (D-050a, "先暫時定案"); not a rollout authorization; residential and further phases not approved.

## T-014B2 status
Update 2026-11-27: Martin tested B2 on device (ON/OFF) and felt no performance impact (subjective, no FPS number). T-014B2.1 (PR #99, D-047, vh-2026-11-27-01) adds anisotropic filtering to the facade atlas only; awaiting Martin's oblique-wall sharpness check on Tab S11. B3 geometry proposal (ChatGPT) reviewed for feasibility only, not registered/approved.

Released vh-2026-11-26-01 (PR #97, D-046). Site A facades: Building A Commercial, Building B Office, shared 1024 atlas + 512 R8 night mask on the existing materials; `?showcase=0` hides Site A for device ON/OFF FPS pairs; `WORLD.showcaseSiteA.atlas` exposes seed/islands. Browser CI job `t014b2-facade.yml` (PHONE_LOW). Awaiting Martin device FPS (>=30, day and night, ON/OFF via ?showcase=0) and ART judgement; B3 (residential, more variety) not approved. Gemini in Antigravity cannot be stopped from the phone: use a new conversation and tell it to push and open the PR before any long test.

## WE-01 status
2026-11-27: WE-01A (T-016A, D-051) registered from `specs/WE-01-spec-v1.2.md` (read-only land audit of the three residential districts B1/B2/B3). Claude supplies runtime dumps (`window.__VH`: `__th`, WORLD lists, ROAD_NET, TREES, TREE_COLLIDERS, mass-0 physics bodies) for PHONE_LOW and DESKTOP_HIGH; Gemini writes `tools/test/we01a_land_analyzer*.py` only. Facts: physical ground is `CANNON.Box(2400,0.5,2400)` at y=-0.5 over the whole map (flat); only hill/suburb terrainRegions (+20 m) have non-flat height; static (mass 0) bodies are deterministic, dynamic ones jitter ~0.1 m. WE-01B (T-016B) not approved yet. 2026-11-27: PR #106 merged (e4764a0, D-051c); analyzer check runs in CI; A10 accepted by Martin 2026-11-27 (D-051d); formal outputs and hashes in D-051d; WE-01B was split into T-016B (capacity) and T-016C (roads and verdict) by Martin; v1.3 is in G0 re-review, not registered. D-051e: full-dump fingerprints changed (road elevation types resolved), WE-01A land areas unchanged; new fixtures in `tools/fixtures/we01/` (`sample_b3mid_*`, `sample_roads_*`, `we01a_common_l0_cells.csv`).
Extractor and fixtures: `tools/we01/we01_run.py full|sample OUTDIR` (Claude-owned, writes JSON dumps only), samples + `SCHEMA_NOTES.md` + `fingerprint_reference.py` in `tools/fixtures/we01/`. Real world facts from the first dumps: B3 sits inside the existing city grid, B1 flat and empty, B2 buffer has hill-margin heights; see D-051a.
