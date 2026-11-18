# AGENTS.md — rules for Codex (and any coding agent) working on VICE HORIZON VI

Read `COLLAB.md` first; this file is the short version for the coding agent.

## Project
Open-world driving browser game: Three.js r160 + cannon-es 0.20, one file `index.html` (~8,300 lines, search for `// ====` banners), PWA served by GitHub Pages from `main`. Architecture and current systems: `HANDOFF.md`. Task you are working on: `TASKS.md`. Decisions you must respect: `DECISIONS.md`.

## Your job
Implement ONE approved task at a time exactly as specified in `TASKS.md` / the linked decision. Do not add unrequested features. If the spec is ambiguous or seems wrong, stop and say so in the PR description instead of guessing.

## Workflow rules
- Work on a branch named `codex/T-<id>-<short-name>` from the latest `main`. Never push to `main`. Never merge your own PR. Open a PR using the template and keep it small.
- One active code PR at a time. If another PR is open, wait.
- Do NOT edit `sw.js` `CACHE` or the docs (`TASKS.md`, `DECISIONS.md`, `LOG.md`, `HANDOFF.md`, `COLLAB.md`); the maintainer (Claude) does that when integrating.
- Do not add or change binary assets (models, textures, fonts, libs). List what you would need in the PR instead.
- Do not reformat or reorder unrelated code; the file is large and diffs must stay reviewable.

## Hard constraints (the reviewer checks these)
- Mobile performance first: no per-frame allocations in hot loops, keep draw calls low (use InstancedMesh / merged static meshes), keep physics cost low (cannon-es `step` is the main cost). Say how your change affects phones.
- Existing saves (`localStorage` key `vh_save`: cash, owned[], jumps{}, deliveries, upgrade) must keep loading. Add fields with defaults; never rename or remove.
- cannon-es notes: `wheelInfos[i].isInContact` is always false; use `raycastResult.hasHit`. The Box chassis does not collide with Trimesh terrain (handled by `supportOnTerrain()`).
- Keep the game working offline (everything is vendored; do not add CDN URLs).
- Window debug handle `window.__VH` may be extended for testing.

## Checks to run before opening the PR
```
python3 tools/test/syntax_check.py      # must print RESULT: PASS
```
If you can run a headless browser, also load `index.html` via a local static server and confirm there are no console errors on startup; otherwise say that you could not. The reviewer runs the real game test; do not claim performance numbers you did not measure.

## Language
Code and PR text in English. Explanations to Martin (the owner) in Traditional Chinese.

## Review guidelines (for `@codex review`)
Treat as P1: syntax/runtime errors, broken save compatibility, per-frame allocations in hot paths, new network/CDN dependencies, edits to `sw.js` CACHE or to docs by a code PR, changes outside the task's scope.
