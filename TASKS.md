# Task board (rules: COLLAB.md v3.1). One Owner per task. One active code PR at a time.

## Ready for ChatGPT
(none)

## Ready for Codex
(none)

## In review
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

Verification: `code-reviewed` + headless (Chrome/SwiftShader, not a device): Claude approved PR #10. CI check+syntax pass; `camera_check.mjs` PASS. Headless full-game run: no startup errors, saves reload intact, near/far distance 7.5/10.8, FOV rest 60 and 66.9 at 216 km/h, 21 spots x 4 headings x 100 frames with 0 obstructed frames (baseline main: 4), teleport first-frame distance 7.5 (baseline 545). NOT verified: real touch, S26 Ultra / Tab S11 feel and FPS, long drives (mountain, elevated road, collisions), enter/exit-car camera transition feel (>=40-unit teleports now cut instead of easing, by design). AWAITING Martin's device acceptance; T-003C stays blocked until he accepts.

## Doing (Claude)
(none)

## Blocked
### T-002 Verify licenses of the Porsche / Lexus / Ford Sketchfab models
Owner: Martin
Priority: P2
Why: archives had no license text; needed before any public sharing.

### T-003C Responsive HUD, radar optimization and pedals
Owner: Codex
Reviewer: Claude
Priority: P1
Depends on: T-003B (released; waiting for Martin's device acceptance)
Spec: `specs/T-003A-spec-v1.1.md` sections 3, 4, 8, 10. Acceptance in spec section 9: tablet landscape layout, phone compact layout, minimap 8-10 Hz, dark racing pedals, unchanged input behavior, essential HUD only, no feature functionality removed.
Claude notes (apply when unlocked): (1) Spec removes the permanent 8-button toolbar here but the Hub arrives only in T-003D, and "no functionality removed" also applies: this task must keep every action reachable through an interim entry (e.g. tapping the minimap opens a simple panel with the existing actions) which T-003D then replaces. (2) Reuse `radar-canvas` / `drawRadar()`; the canvas backing is 140x140, enough for the 112-128 CSS px target. (3) No `safe-area` handling exists today; add it. (4) Validate the matrix in spec section 8.
Verification: `designed`.

### T-003D Minimap-driven Game Hub
Owner: Codex
Reviewer: Claude
Priority: P1
Depends on: T-003C
Spec: `specs/T-003A-spec-v1.1.md` sections 5, 8, 10. All existing toolbar actions through the Hub; mission/garage/map/settings preserved; correct modal and input handling; `closeModals` flow and the delivery fast-travel block preserved.
Claude note: spec lists an "airport stunt" mission; no such name exists in code today. Map it to the existing STUNT mission and do not add a new one.
Verification: `designed`.

### T-003E Bilingual interface (English / Traditional Chinese)
Owner: Codex
Reviewer: Claude
Priority: P1
Depends on: T-003D
Spec: `specs/T-003A-spec-v1.1.md` sections 6, 8, 10. String table, language selector in SETTINGS, `vh_save.language` (new field, default-safe), complete player-visible translation, CI check for leftover CJK, live panel refresh, old saves keep working.
Claude notes: (1) Default policy needs "new player vs existing save": decide by whether `vh_save` existed before this load (no key = new = English; key without `language` = existing = zh-TW). (2) Dynamic strings (e.g. `showBanner` calls, delivery/mission text, reward messages from T-001B) must go through the table. (3) Existing `vh_settings` holds other settings; keep language in `vh_save` as specified.
Verification: `designed`.

## Inbox
(none)

## Done
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
