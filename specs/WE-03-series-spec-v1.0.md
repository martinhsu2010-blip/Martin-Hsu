# WE-03 / T-018 series - C+ Hybrid World Streaming Architecture (series spec v1.0)

Entry-point spec for the T-018 series. ChatGPT draft: `specs/WE-03-draft-v1.0-chatgpt.md` (verbatim). Claude G0 review: `specs/WE-03-g0-review-v1.0.md` (full text of every condition below). Where this file or the review differs from the draft, **this file and the review win**.

## 1. Decisions and scope
- Martin selected architecture C+ (hybrid layered streaming with a future-HLOD data contract, no HLOD runtime). Martin ("批准", 2026-11-28 21:20) approved the Claude G0 conditions below as binding series constraints and approved the corrected T-018A1 (D-065).
- This approval registers only the umbrella T-018 (not a code task) and T-018A1. Every other subtask needs its own self-contained spec, Martin's approval, a single implementer, a single PR and Claude review; each is registered only then.
- NOT authorized: any change to `index.html`, `sw.js`, `CACHE`, `vh_save`, roads, terrain, buildings, WE-01/WE-02 artifacts or verdicts; T-018A2 and later subtasks; WE-04..WE-09; construction; using headless numbers as device FPS. Closing WE-03 does not authorize WE-04.
- Engineering BASE: main `e8d5250fce0ea5f07f68840481cb95d2eca803fb` (game source equals the historical Audit BASE `84319439243b51aa8d119e33eb62a0637feea887`; `CACHE` `vh-2026-11-27-02`). Every subtask spec lists its own baseline SHA; a baseline measured earlier is reusable only while the game source is byte-identical.

## 2. Binding Claude conditions (details and evidence in `specs/WE-03-g0-review-v1.0.md`)
- **B1** Synthetic prototype assets, test loader, URL test flag and replay driver (and a test-only teleport, since no road reaches B1-B3) belong to a new subtask T-018C2. Default off; off means zero new bodies/shapes/draw calls; no `vh_save` or localStorage key; 60/120-building extras are deterministic, non-overlapping, never written to `district_plan.json`.
- **B2** Each subtask ships its own tests with identifiable failing assertions; Claude wires them into CI. WS map: B: WS01-05, WS25; C1: WS08-10; C2: WS26 and loader isolation; C3/C4: WS05-07, WS11; D: WS12-13; E1: WS14; E2: WS15-16; F1: cross-system stress and negative controls (automation of WS17-22); F2: WS23-24, WS27-28.
- **B4** Device FPS acceptance is cap-aware: average >= 97% of the FPS cap (29.1 at a 30 cap); other thresholds unchanged. Device runs use `?fps=1` (auto-quality and dynamic resolution off) with a manually fixed preset and record `resScale`, `fpsCap`, refresh rate, release/CACHE.
- **B5** T-018A2 (device frame-time diagnostics, extending `?fps=1`) is required, runs right after A1 and before B, and may not change frame pacing, quality or physics.
- **B6** Original C2 is split into C3 (visual chunk lifecycle) and C4 (LOD controller). index.html ceilings (added + changed): A2 250; B 350; C1 400; C2 500; C3 450; C4 450; D 500; E1 450; E2 350. The streaming core lives in begin/end banner blocks in `index.html` (Node tests extract them like `collision_harness.mjs`); no new runtime files; `sw.js` PRECACHE unchanged.
- **N1-N11** (per-subtask BASE; 11 real presets with 7 unmapped; velocity look-ahead for LOD; define "async"; registry owns only its own resources; collision safe point before the single `physicsWorld.step`; scheduler and atlas upload; fast travel and reset-path rules; measurement validity; benefit-gate expectation; offline/save/CI; triangle metric N11) are binding as written in the review. Draft section 22 numbers stay provisional until WE-03A is accepted and Martin confirms revised budgets.
- **Chunk contract (C-S03)** goes into the T-018B spec: owner = chunk containing the footprint centre, half-open `[k*128,(k+1)*128)`; coverage `floor(min/128)..ceil(max/128)-1`; parent index `Math.floor(c/2)`.

## 3. Subtasks (IDs are fixed; one code PR at a time)
| ID | Content | Implementer | Risk / Volume |
|---|---|---|---|
| T-018 | Series umbrella (not a code task) | - | - |
| T-018A1 | Baseline and architecture calibration (tools + reports, no game files) | Claude | LOW / LARGE |
| T-018A2 | Device frame-time diagnostics | Codex | HIGH / SMALL |
| T-018B | Chunk registry | Codex | HIGH / SMALL |
| T-018C1 | Asset registry | Codex | HIGH / SMALL |
| T-018C2 | Synthetic prototypes, test loader, replay driver | Codex | HIGH / SMALL |
| T-018C3 | Visual chunk lifecycle | Codex | HIGH / SMALL |
| T-018C4 | LOD controller | Codex | HIGH / SMALL |
| T-018D | Collision streaming | Codex | HIGH / SMALL |
| T-018E1 | Predictive scheduler | Codex | HIGH / SMALL |
| T-018E2 | Destination readiness (test path) | Codex | HIGH / SMALL |
| T-018F1 | Stress fixtures and scripts | Gemini | LOW / LARGE |
| T-018F2 | Integration and device acceptance | Claude (Martin on device) | - |

## 4. Process
Order A1 -> A2 -> B -> C1 -> C2 -> C3 -> C4 -> D -> E1 -> E2 -> F1 -> F2. Final WE-03 acceptance needs WS01-WS28, Claude's independent verification, CI evidence, Martin's device acceptance and unchanged WE-01/WE-02 verdicts (draft section 28).
