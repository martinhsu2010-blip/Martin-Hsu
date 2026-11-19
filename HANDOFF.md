# VICE HORIZON VI — Project Handoff

Written for another AI assistant (e.g. ChatGPT) or developer picking up this project.
Last updated: 2026-11-18, game version `vh-2026-11-19-15` (see `CACHE` in `sw.js`).
Owner: martinhsu2010-blip (Traditional Chinese speaker, Taiwan). Explain things to the owner in Traditional Chinese; write prompts for Gemini in English.

## What this is
An open-world driving browser game (GTA-style): on-foot + vehicles, city, police chase, missions, radio, day/night.
- Live: https://martinhsu2010-blip.github.io/Martin-Hsu/ (GitHub Pages, installable PWA, works offline)
- Stack: Three.js r160 + cannon-es 0.20, no build step for the game itself. **Everything is in one file: `index.html`** (~8,300 lines). All libs, models, textures and fonts are vendored locally (`libs/`, `models/`, `textures/`, `fonts/`) so it runs offline.
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

## Pitfalls already learned
- cannon-es `Box` chassis does not collide with `Trimesh` terrain → handled by `supportOnTerrain()`.
- Don't use `isInContact`; use `raycastResult.hasHit`.
- New car paint materials must drop the Ferrari flake `normalMap` or they get white speckles.
- Keep draw calls low: static meshes are merged, trees/houses are InstancedMesh, far Ferrari uses a simplified LOD.
- Mobile performance matters most; check any added feature on the PHONE_* presets.

## Working agreement
See `COLLAB.md` (v3) and `AGENTS.md`. Code changes arrive as Pull Requests from Codex and are reviewed/integrated/released by Claude.

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
