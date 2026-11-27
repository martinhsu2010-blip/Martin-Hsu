# T-014B3 spec v1.2 — Site A Commercial + Office facade geometry (recessed glazing, projecting frames, Near/Far LOD)

> **REGISTRATION NOTE (Claude, 2026-11-27):** Approved by Martin ("批准", 2026-11-27 08:54) as T-014B3 v1.2 (D-048). ChatGPT's v1.2 reached Claude as a structured summary (the full prose text was not relayed); this file records that summary verbatim plus Claude's binding G0 conditions below. Where the summary is silent, the G0 conditions and the repo rules (COLLAB v3.6, AGENTS.md, D-043/D-045) decide. NOT ART PASS. Residential is out of scope.

Baseline: main 6205bc5, release vh-2026-11-27-01 (D-046 / D-047). Implementer: Gemini Stage 3 (single-task exception, D-026/D-043/D-045). Risk: HIGH. Volume: SMALL. Reviewer/releaser: Claude. Device/ART judge: Martin.

## Scope
- Commercial Building A and Office Building B only; shared facade layout data; real recessed glazing and projecting frames; Near/Far geometry LOD with hysteresis; preserve B2.1 textures and night appearance.

## Group architecture
- Immutable B1 marker block (`// T-014B1` .. `// T-014B1_END`). Original `sc.group` contains exactly 6 meshes; original `sc.meshes` registry unchanged.
- Near meshes live in a separate sibling group; group and meshes use `userData.noBatch = true`, castShadow=false, receiveShadow=true. Scene child count stable after initialization. `setVisible`/`isVisible` respect both groups.
- <=4 new meshes, <=10 stored meshes, <=6 simultaneously drawn; <=5 existing materials, zero new materials/textures/lights/shadow casters.

## Render suppression
- The original six meshes keep `visible=true`. Exclusive render-layer switching: active level on layer 0, inactive level on layer 31 (layer 1 is DETAIL_LAYER and must not be used). Both main and mirror cameras exclude layer 31. Main/mirror `renderer.info` evidence required. Existing B1/B2 tests byte-identical and green in CI.

## Showcase OFF
- Near geometry is built once during initialization (together with the Site A build; `?showcase=0` builds then hides, as today). Both groups hidden when OFF; zero rendered Site A meshes when OFF; LOD updates skipped while hidden. Report Near buffer bytes and init-time cost.

## Golden hashes
- SHA-256 of raw RGBA canvas pixels (getImageData of the 1024 atlas canvas) and SHA-256 of raw R8 mask bytes (maskTexture.image.data, 262,144 bytes). Both must equal the values recorded from main 6205bc5 (see D-048a): atlas `61304bdf8a180a6e6ad2973a494d7841d591827fbe60b49b82bd94204024f7d9`, mask `920923f2d6351b6eb062357e43620a70db622c656186b9883a0cafe003f057ea`. CI-Chromium values to be confirmed on first CI run.

## Geometry
- Recess 0.15–0.25 m; frame projection 0.08–0.12 m; no z-fighting at 15 m and 35 m. A Near (shell + roof) <=6000 triangles; B Near (shell + roof) <=8000; Site A Near total <=14064; Far total <=520.

## LOD
- Distance from the main render camera to the building footprint AABB. Enter Near <=35 m; enter Far >=50 m; keep previous state in between. First-frame reset after teleport/fast-travel/ON. Mirror pass reuses the main-camera LOD state. Only one level drawn per building.

## Luminance
- Reuse the B2 test camera poses and window projection (`v.project(camera)`); sample corresponding screenshot mask rects; day and night linear mean luminance within >=0.90 and <=1.05 x B2.1. Claude measures independently.

## Hard gates
- Main draw-call delta vs B2.1 = 0 (mirror measured separately); physics bodies/shapes delta = 0; paired physics median <=1.25 with baseline control <=1.10; device FPS >=30 day and night (ON/OFF via `?showcase=0`, Martin).

## Workflow
- Gemini runs fast checks only (syntax_check.py, i18n_check, new layout test); no full Playwright (about 12 h), no waiting on the heavy B1 Node test (CI is the authority). Push immediately and open the PR. Allowlist: `index.html` + new test file(s); no `sw.js`, docs, specs or CI config. Browser CI PHONE_LOW only; Claude measures TABLET_MED/DESKTOP_HIGH independently and owns the CACHE/CI release commit.

## Claude G0 binding conditions (D-048)
1. Layer 31 is the inactive layer; layer 1 (DETAIL_LAYER) stays untouched. The active level must be on layer 0 so the mirror pass follows the same state; verify with pass-separated `renderer.info`.
2. Golden hashes above are fixed pre-start values.
3. Luminance sampling reuses the B2 test cameras and window projection.
4. Layout -> geometry window rects -> UV -> mask texel alignment test with mutation tests RED.

HANDOFF ChatGPT -> Claude (registered).
