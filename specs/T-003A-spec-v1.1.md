# T-003A — Immersive Gameplay UX Specification v1.1

**Project:** VICE HORIZON VI  
**Owner:** ChatGPT  
**Reviewer:** Claude  
**Priority:** P1  
**Depends on:** T-001B  
**Design base commit:** \`5937859ff7160851e7342359b576a45c5177d423\`  
**Related decision:** D-015  
**Verification:** designed / code-inspected, not device-measured  
**Status:** Specification complete; awaiting Martin's implementation approval

## 1. Design objectives

Transform the existing UI into an immersive open-world driving experience while preserving gameplay.

Requirements:

- Third-person cameras feel closer to modern open-world driving games.
- The gameplay screen contains only essential HUD, controls and contextual notices.
- Existing utility actions move into a Game Hub opened from the minimap.
- Driving controls use a graphite-black, metallic racing-pedal appearance.
- Players can switch between English and Traditional Chinese.
- Phone and tablet performance take priority over decorative effects.
- Existing cars, missions, physics, save data and offline PWA behavior remain intact.

No new gameplay mechanics, analog throttle, vehicle physics changes or map systems are included.

## 2. T-003B — Third-person camera tuning

Centralize the camera defaults into one named configuration area.

| Mode | Distance | Pitch | Target height |
|---|---:|---:|---:|
| On-foot follow | 4.2 | 12° | 1.55 |
| Chase Near | 7.2 | 10° | 1.10 |
| Chase Far | 10.5 | 14° | 1.10 |

All distances and heights use Three.js world units.

Preserve hood and bird's-eye cameras.

Camera behavior:

- Recenter toward the vehicle heading after 2 seconds without manual camera input.
- Smooth follow lag without excessive swinging during sharp turns.
- Reduce camera shake at high speed.
- Preserve pinch/wheel zoom and manual yaw/pitch controls.
- Preserve building collision avoidance.
- Smooth camera distance recovery when an obstacle clears.
- Prevent jitter near walls, ramps, hills and overpasses.
- Prefer existing vectors and raycaster objects; avoid per-frame allocations.

Target FOV:

- Normal driving: 60°.
- Progressive high-speed widening: maximum 68°.
- Nitro: maximum 72°.
- Apply FOV changes smoothly.

These are starting tuning values, subject to visual testing.

**Acceptance:** No severe camera jumps, clipping or obstructed vehicle view during city driving, mountain roads, elevated highways, collisions or manual rotation.

## 3. T-003C — Responsive HUD and racing controls

### 3.1 Default gameplay HUD

Keep visible:

- Minimap / Game Hub entry.
- Cash balance.
- Vehicle speed and gear.
- Wanted level when active.
- Essential mission progress when active.
- Touch steering and driving controls.
- Contextual vehicle enter/exit action.
- Small, temporary reward and warning notifications.

Remove the permanent eight-button utility toolbar from gameplay.

The center of the screen should remain unobstructed during normal driving. Target at least 55% of viewport width as a clear central driving corridor.

### 3.2 Tablet landscape layout — primary requirement

The Samsung Tab S11 in landscape orientation is the principal tablet layout target.

Use CSS viewport dimensions, not physical panel pixels, for responsive sizing.

**Standard landscape tablet layout:** viewport width at least 960 CSS px and height at least 560 CSS px.

| Component | Position | Suggested CSS size |
|---|---|---|
| Minimap | Top-left | 112–128 px diameter |
| Cash + speed HUD | Top-right | 160–196 px wide |
| Steering controls | Bottom-left | 72–88 px per direction button |
| Gas pedal | Bottom-right, outer edge | 64 × 118 px |
| Brake pedal | Immediately left of gas | 64 × 100 px |
| Nitro + handbrake | Above or left of pedals | 48–56 px touch targets |
| Horn / enter-exit | Adjacent secondary control row | At least 44 × 44 px |
| Active mission information | Below minimap or top-center edge | One compact line |

Placement rules:

1. Respect \`safe-area-inset-top/right/bottom/left\`, plus 12–20 px of padding.
2. Controls anchor to the viewport corners, not fixed absolute positions.
3. Maintain at least 12 px separation between unrelated control groups.
4. Do not allow any HUD component to cover interactive controls.
5. The minimap, game status and mission banner must not overlap.
6. Steering controls and gas/brake must support simultaneous multitouch.
7. No horizontal scrolling, clipping or inaccessible buttons.
8. On landscape tablets, never enlarge controls solely because a device has a high pixel-density screen.

### 3.3 Compact landscape fallback

When viewport width is below 960 CSS px, or height below 560 CSS px:

- Minimap reduces to approximately 88–100 px.
- Steering buttons reduce to 60–72 px.
- Pedals reduce to roughly 54–60 px wide.
- Secondary actions use compact icons.
- Speed and cash become a smaller two-line display.
- Hide nonessential decorative text and effects.
- Mission indicators remain readable.

For extremely short landscape viewports (height below 430 CSS px), use an additional compact mode:

- Minimap 80–88 px.
- Pedals around 50 × 84 px.
- Steering buttons around 54–60 px.
- All touch targets must still be at least 44 × 44 CSS px.
- Optional labels may disappear, but the essential controls must remain usable.

Portrait orientation may present a rotation recommendation where appropriate. If orientation locking fails, the interface must not trap the user behind an inaccessible button or modal.

### 3.4 Control visual design

Use matte black, graphite gray and metallic silver.

Suggested palette:

- Main surface: \`#24282E\`
- Raised surface: \`#414750\`
- Metallic edge: \`#858C96\`
- Primary symbols: \`#F1F5F9\`
- Active pressed state: slightly brighter surface with reduced elevation

Gas pedal:

- Taller and narrower.
- Vertical groove design.
- Label \`GAS\` in English mode.
- Slight downward visual movement while pressed.

Brake pedal:

- Shorter and wider.
- Horizontal groove design.
- Label \`BRAKE\` in English mode.

Use CSS and existing SVG infrastructure, not new image textures.

Keep existing input bindings and binary \`INPUT\` states unchanged:

- Gas = forward.
- Brake = backward/brake.
- Steering = left/right.
- Nitro = shift.
- Handbrake = space.

No analog throttle, steering-wheel simulation or vehicle-physics change in this release.

## 4. Minimap performance rules

The current \`radar-canvas\` and \`drawRadar()\` must be reused.

Do not introduce a second minimap, an additional Three.js renderer or an extra 3D camera.

Requirements:

- Limit the normal radar refresh to approximately 10 Hz.
- On LOW quality, allow an 8 Hz refresh if needed.
- Reuse road geometry data and existing drawing logic.
- Preserve waypoint, police, delivery and mission icons.
- Keep radar size responsive without unnecessarily increasing canvas backing resolution.
- Avoid repeatedly allocating temporary arrays inside radar drawing loops where practical.
- Avoid continuous redraw while the page is hidden or the radar is not visible.

Performance target: normal radar drawing should not exceed approximately 2 ms per update on the primary test devices. This is a proposed benchmark, not a measured current value.

## 5. T-003D — Minimap-driven Game Hub

Tap the minimap to open a fullscreen Game Hub.

Suggested sections:

| Section | Contents |
|---|---|
| MAP | Existing world map, markers, fast travel, waypoints |
| MISSIONS | Delivery, race, drift, airport stunt, cancel mission |
| GARAGE | Vehicle selection, purchase, paint, upgrades |
| WORLD | Existing weather/day-night controls, police sandbox action |
| SETTINGS | Quality, FPS, camera, radio, language, debugging |

All existing features must remain accessible.

No separate time-of-day slider is required in v1; existing environmental controls move into WORLD. A direct time slider is a future optional feature.

### Tablet Game Hub layout

In landscape:

- A compact tab navigation row at the top.
- The map occupies most of the available space.
- Detail panel appears at the side when a location is selected.
- All long settings and mission content scrolls within its panel.
- Close/back control stays accessible at all times.
- Avoid rendering the world map continuously when another tab is selected.
- Preserve the original \`closeModals\` and mission/garage event behavior.

Opening a menu releases held driving inputs. Preserve existing game-time behavior for this release; changing whether missions or physics pause during menus requires a separate approved design decision.

Existing delivery restrictions must remain effective, including preventing fast travel while a delivery is active.

## 6. T-003E — Bilingual localization

Support:

- \`en\` — English.
- \`zh-TW\` — Traditional Chinese.

Add a language selector inside SETTINGS.

Recommended default policy:

- New players: English.
- Existing saves without a language preference: Traditional Chinese.
- A saved preference always overrides the default.

Store the preference in a new backward-compatible \`vh_save.language\` field, as requested in the T-003A review.

Use one centralized string table containing English and Traditional Chinese translations.

Localization scope:

- HUD and touch controls.
- Missions and reward/cooldown messages.
- Garage, purchase confirmation and upgrades.
- Map locations, districts and waypoints.
- Weather and camera settings.
- Police and vehicle notifications.
- Error and warning messages.
- PWA installation prompts and player-visible metadata.
- Accessibility labels and help text.

Switching languages must update open UI panels without needing a complete reload.

Do not translate internal IDs, object keys, save keys or model identifiers.

Introduce a CI-visible-string check that detects untranslated CJK text in player-visible HTML/JavaScript outside the approved string table. Comments and internal implementation details may remain Chinese.

Test long English labels and Traditional Chinese text against every responsive layout.

## 7. Mobile and tablet performance — hard acceptance targets

### 7.1 Supported test devices

| Device | Default preset | Target | Optional mode |
|---|---|---:|---|
| Samsung S26 Ultra | PHONE_LOW | 30 FPS | PHONE_MED |
| Samsung Tab S11 | TABLET_MED | 30 FPS | TABLET_HIGH |
| Desktop | Current desktop preset | 60 FPS | Device-dependent |

Do not treat a 60 FPS tablet option as a required default. Optional 60 FPS may be evaluated later.

Retain the current 1/60-second fixed physics timestep while rendering is capped at 30 FPS. No physics-rate reduction is approved by this task.

### 7.2 Performance pass thresholds

At the default quality and FPS cap, each primary device should satisfy:

- Median measured rendering FPS: at least 29.
- Fifth-percentile FPS: at least 24.
- At most 2% of rendered frame intervals exceed 50 ms.
- No continuous period of 2 seconds with an average below 20 FPS during ordinary gameplay.
- No freezes, WebGL context loss or crashes.
- No loss of touch input responsiveness during normal driving.
- No substantial sustained thermal degradation that makes the target unattainable.

If performance fails, the feature cannot be claimed fully verified. Record the failure, optimize the affected system or propose an approved fallback.

### 7.3 Benchmark scenarios

Run these on each primary device:

| Scene | Duration | Contents |
|---|---:|---|
| City driving | 5 minutes | Traffic, buildings, turns, minimap active |
| High-speed road | 5 minutes | Camera movement, speed FOV, highway |
| Mission / pursuit | 5 minutes | Mission HUD, traffic, physics, reward updates |

Warm up the device and game for at least 60 seconds before recording. Record actual rendered-frame intervals using a monotonic timing source; exclude intentional background-tab pauses and explicitly identify deliberate frame-rate caps.

Repeat after the principal HUD changes and compare with the same device's previous release.

Report:

- Median FPS.
- Fifth-percentile FPS.
- Proportion of frames exceeding 50 ms.
- Device and browser version.
- CSS viewport and orientation.
- Game quality preset and resolution scale.
- Approximate test duration.
- Any thermal or memory issue.

Headless-browser results must be marked \`measured (headless)\`. They cannot replace physical-device testing.

### 7.4 Performance restrictions

- No additional WebGL renderer for the minimap.
- No unnecessary per-frame DOM measurements or layout recalculations.
- No new externally hosted resources.
- Avoid expensive blur filters and complex animations on LOW quality.
- Reuse temporary objects in camera and HUD hot paths.
- Keep mobile draw calls, vehicle density and physics workload within the existing quality system.
- Preserve automatic resolution reduction when FPS falls below target.
- Avoid silently changing player-selected quality settings.

If the existing default preset cannot meet the baseline, report that separately rather than claiming the UX update caused or solved the issue. Any change to default quality parameters must be documented and tested.

## 8. Layout validation matrix

All of the following are proposed CSS viewport test cases, not claims about any device's native pixel resolution.

| Test viewport | Purpose |
|---|---|
| 1280 × 800 | Standard tablet landscape |
| 1024 × 768 | Taller tablet landscape |
| 960 × 540 | Compact landscape threshold |
| 844 × 390 | Phone landscape |
| 800 × 360 | Very short landscape |
| Tablet multi-window / resized viewport | Reflow robustness |

For each:

- No overlapping controls.
- No unreachable map or menu buttons.
- All required touch controls respond correctly.
- HUD respects safe-area insets.
- Cash/speed text remains readable.
- Both languages fit or gracefully truncate.
- Rotating or resizing does not leave stuck steering or gas input.

## 9. Sequential implementation plan

### T-003B — Camera tuning
Owner: Codex  
Reviewer: Claude  
Priority: P1  
Depends on: Approved T-003A  
Output: Camera-only PR.

Acceptance: Named camera configuration, adjusted third-person tracking, collision and FOV stability, other camera modes preserved.

### T-003C — Responsive HUD, radar optimization and pedals
Owner: Codex  
Reviewer: Claude  
Priority: P1  
Depends on: T-003B  
Output: HUD and visual-controls PR.

Acceptance: Tablet landscape layout, phone compact layout, minimap 8–10 Hz, dark racing pedals, unchanged input behavior, essential HUD only. No feature functionality removed.

### T-003D — Game Hub
Owner: Codex  
Reviewer: Claude  
Priority: P1  
Depends on: T-003C  
Output: Game Hub navigation PR.

Acceptance: All existing toolbar actions available through Hub, existing mission/garage/map/settings features preserved, correct modal and input handling.

### T-003E — Bilingual interface
Owner: Codex  
Reviewer: Claude  
Priority: P1  
Depends on: T-003D  
Output: Localization PR.

Acceptance: English and Traditional Chinese string table, persistent language setting, complete player-visible translation, old save compatibility, responsive text layout.

Only one active game-code PR at a time, per COLLAB v3.

## 10. Verification and release gates

Every PR must:

1. Start from the latest \`main\`.
2. Change only its assigned task scope.
3. Pass \`python3 tools/test/syntax_check.py\`.
4. Include a before/after check or clear test evidence.
5. Avoid regressions to saves, missions, controls and offline play.
6. Include phone/tablet performance impact notes.
7. Receive Claude's review.
8. Leave \`sw.js\` CACHE untouched in Codex's branch; Claude handles the release bump.
9. Record actual performance measurements separately from design targets.
10. Require Martin's final gameplay acceptance.

**Current result:** specification designed; implementation not yet authorized; real-device performance not measured.

## 11. Explicitly out of scope

- Analog throttle or steering sensitivity changes.
- Vehicle handling physics redesign.
- New missions, rewards or economy changes.
- New world map or GPS pathfinding engine.
- New weather simulation.
- New vehicle assets or models.
- Unapproved changes to FPS caps or physics timestep.
- Any additional renderer solely for UI effects.