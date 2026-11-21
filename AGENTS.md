# AGENTS.md — rules for Codex and Antigravity/Gemini (and any coding agent) working on VICE HORIZON VI

Read `COLLAB.md` (v3.4) first; this file is the short version for the coding agent. Your spec is the file named in your task message under `specs/` plus the task entry in `TASKS.md`; if either is missing or contradicts the other, stop and say so in the PR description.

## Project
Open-world driving browser game: Three.js r160 + cannon-es 0.20, one file `index.html` (~9,900 lines, search for `// ====` banners; function/section map in `HANDOFF.md`), PWA served by GitHub Pages from `main`. Architecture and current systems: `HANDOFF.md`. Task you are working on: `TASKS.md`. Decisions you must respect: `DECISIONS.md`.

## Your job
Implement ONE approved task at a time exactly as specified in `TASKS.md` / the linked decision. Do not add unrequested features. If the spec is ambiguous or seems wrong, stop and say so in the PR description instead of guessing.

## Workflow rules
- Work on a branch named `codex/T-<id>-<short-name>` (Codex) or `gemini/T-<id>-<short-name>` (Gemini; if the tool picks its own name, say which in the PR) from the latest `main`. Never push to `main`. Never merge your own PR. Open a PR using the template and keep it small.
- One active code PR at a time. If another PR is open, wait. One task = one session = one PR; never start a second task in the same PR.
- What Gemini (Antigravity) may implement depends on the stage Martin has approved in `TASKS.md` (`Gemini qualification`, COLLAB v3.5 §4; D-021); use the stage table to decide the forbidden areas. If your task turns out to touch physics, traffic, collisions, world generation, save format, camera or more than one or two systems **outside your current stage**, **stop and say so in the PR description**; do not push through.
- Do NOT edit `sw.js` `CACHE` or the docs (`TASKS.md`, `DECISIONS.md`, `LOG.md`, `HANDOFF.md`, `COLLAB.md`, `specs/`); the maintainer (Claude) does that when integrating.
- Do not add or change binary assets (models, textures, fonts, libs). List what you would need in the PR instead.
- Do not reformat or reorder unrelated code; the file is large and diffs must stay reviewable.

## Secondary implementer (Antigravity / Gemini) — D-020, replaced in scope by D-021 (COLLAB v3.5 §4)
Applies only when `TASKS.md` says `Implementer: Gemini`; everything else in this file applies to you too. Your stage is the `Current stage` in the `Gemini qualification` block of `TASKS.md`; if it is missing or unclear, you are in Stage 1.
- **Stage 1 (allowed, whole task only):** zh/en UI strings and translations (`STRINGS`/`tr()`); wording polish of missions/UI text; purely static HUD/menu CSS tweaks. No JavaScript logic, events, DOM behaviour, storage, new files or assets.
- **Stage 2 (only after Martin's recorded promotion):** whole non-critical features (menus, settings that do not change the save schema, mission/interaction systems, general HUD behaviour). The first Stage 2 task is a trial (single, small, no persistence).
- **Stage 3 (only after Martin's recorded promotion and the test gate in COLLAB v3.5 §4.3):** Codex-equivalent scope.
- **Always forbidden at Stages 1-2, stop and report instead of opening a PR:** `cannon-es` physics, collisions, vehicle handling, traffic/police AI, world/terrain/road generation, draw calls/rendering performance, `vh_save` schema changes (even adding defaulted fields). If the spec touches any of these, say so and do nothing else.
- **Branch and diff:** branch `gemini/<task-id>` from the latest `main`. Stage 1: minimal diff to `index.html` only. Stages 2-3: `index.html` plus new or updated test code in `tools/test/` where the spec requires it. Never edit `sw.js`, the docs, `specs/`, `.github/` or binary assets. No reformatting, reordering or "cleanup" of unrelated code; PR to `main` with the template; never merge, never push to `main`.
- The one-active-code-PR lock is shared with Codex: if any code PR is open, wait.

## Hard constraints (the reviewer checks these)
- Mobile performance first: no per-frame allocations in hot loops, keep draw calls low (use InstancedMesh / merged static meshes), keep physics cost low (cannon-es `step` is the main cost). Say how your change affects phones.
- Existing saves (`localStorage` key `vh_save`: cash, owned[], jumps{}, deliveries, upgrade) must keep loading. Add fields with defaults; never rename or remove.
- cannon-es notes: `wheelInfos[i].isInContact` is always false; use `raycastResult.hasHit`. The Box chassis does not collide with Trimesh terrain (handled by `supportOnTerrain()`).
- Keep the game working offline (everything is vendored; do not add CDN URLs).
- Window debug handle `window.__VH` may be extended for testing.

## Checks to run before opening the PR
```
python3 tools/test/syntax_check.py        # must print RESULT: PASS
python3 tools/test/i18n_check.py && node tools/test/i18n_check.mjs
node tools/test/hud_check.mjs
node tools/test/camera_check.mjs <base main SHA>
node tools/test/traffic_check.mjs && node tools/test/collision_check.mjs
node tools/test/suburb_check.mjs && node tools/test/urban_check.mjs
```
All must pass (CI runs syntax, i18n, traffic, collision, suburb and urban; `hud_check` and `camera_check` are run by hand; `camera_check` and `collision_check` need the full git history). If a check cannot run in your environment, say so; never claim a PASS you did not see.
If you can run a headless browser, also load `index.html` via a local static server and confirm there are no console errors on startup; otherwise say that you could not. The reviewer runs the real game test; do not claim performance numbers you did not measure.

## Token Efficiency Guidelines
These save tokens, never quality. They sit on top of the workflow, constraints and checks above and never weaken them.
1. **Targeted code reading:** use `HANDOFF.md` as the code map; locate functions with `rg`/`grep`, then read small line ranges instead of re-reading the whole `index.html`.
2. **No redundant exploration:** do not re-inspect files, functions or docs you already understand unless new evidence requires it.
3. **Focused execution:** stay inside the approved task scope; no unrelated refactoring, speculative improvements or dependency exploration.
4. **Efficient testing:** run every mandatory check from this file and the task spec. Keep complete output for any failure; summarize long successful output (command and PASS line are enough).
5. **Concise reporting:** do not restate plans or progress. The final PR report covers changes made, root causes, test results, performance evidence and remaining risks.
6. **Reuse context:** read the collaboration docs and the approved spec once at the start, then refer back to them instead of reloading them.
7. **Batch coherent edits:** once the root cause is known, make related changes together when safe instead of repeatedly editing the same function.
8. **Correctness first:** token efficiency never overrides required audits, tests, performance measurements, acceptance criteria or safety checks.
9. **No arbitrary token limits:** do not set fixed reasoning budgets that could stop you from solving complex physics, traffic, collision or world-generation problems.
10. **Report blockers:** if the spec is materially ambiguous or a required verification cannot be completed, say so in the PR description instead of guessing.

## Language
Code and PR text in English. Explanations to Martin (the owner) in Traditional Chinese.

## Report honestly
The PR description lists what was measured and what was NOT (device FPS, offline, real browser). Headless numbers are labelled headless. Do not claim a result you did not obtain.

## Review guidelines (for `@codex review`)
Treat as P1: syntax/runtime errors, broken save compatibility, per-frame allocations in hot paths, new network/CDN dependencies, edits to `sw.js` CACHE or to docs by a code PR, changes outside the task's scope.
