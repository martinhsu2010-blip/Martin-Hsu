# T-003 Immersive UX overhaul — who does what (COLLAB v3)

Status: working instructions. The approved spec lives in TASKS.md (T-003A) once recorded. This file never overrides TASKS.md, DECISIONS.md or AGENTS.md.

## Fixed facts (Martin-approved, D-015)
- Targets: Samsung S26 Ultra (phone), Samsung Tab S11 (tablet), 30 FPS default target on both.
- Real-device FPS is NOT yet measured. Never write `measured` without a real-device number from Martin.
- Tablet landscape HUD must pass layouts 1280x800, 1024x768, 960x540 (plus compact phone layout).
- Minimap reuses the existing `radar-canvas`. No second 3D renderer.
- Pedals: look and position only. Input logic (`INPUT.forward/backward/left/right`) unchanged.
- Language is switchable (UI setting, saved in `vh_save` as a new backward-compatible field).
- Keep all gameplay, saves and offline/PWA behavior. No unrelated changes.
- Order is strict, one code PR at a time: T-003B camera -> T-003C HUD + minimap + pedal look -> T-003D Game Hub -> T-003E language system.

## Transfer rule (why the last handoffs failed)
A handoff that says "the spec above" is invalid: Claude and Codex cannot see other chats. Every handoff must carry its full text in the same message, or as an attached .md file. Claude does not write or guess numbers (camera values, sizes, thresholds); if the text is missing Claude stops and asks.

## 1. Instructions for Claude (reviewer / integrator / releaser)
1. Never implement features. Review, test, merge, bump `sw.js` CACHE, release, keep TASKS/DECISIONS/LOG/HANDOFF current.
2. When ChatGPT's spec arrives with full text: review against `index.html` (feasibility, mobile cost, save compatibility), report findings to Martin, and only after Martin says approved: record the full spec verbatim in TASKS.md (T-003A -> Done, `Verification: designed / Martin approved`), append a new `agreed` event to D-015 (never edit old events), create T-003B..E with dependencies, and set only T-003B to Ready for Codex. Docs-only PR, no CACHE bump, then report the new `main` SHA.
3. Reviewing a Codex PR: fetch via GitHub REST, read the full diff, run `python3 tools/test/syntax_check.py`, run headless checks where meaningful, check mobile cost and `vh_save` compatibility, post a review (approved / changes-requested / rejected). Small text fixes may be pushed by Claude; logic changes go back to Codex.
4. Release a game PR only when CI passes and the PR changes `sw.js` CACHE. Update LOG with version + SHA. Tell Martin what he must test by hand.
5. Be honest about verification: automated headless results are not real-device results.

## 2. Instructions for ChatGPT (designer / balance / Code Review)
1. Design and specify only. Do not write the implementation.
2. Deliver the T-003A spec as ONE self-contained Markdown file `T-003A-spec-v1.1.md` (or the full text in the message). Required sections, each with concrete numbers, not adjectives:
   - Camera: chase camera distance, height, pitch, FOV (idle and at speed), collision margin, smoothing, per-camera-mode behavior; one constants block; before/after values.
   - HUD: element list, position and size per layout; layouts 1280x800, 1024x768, 960x540, and phone compact; safe-area rules; what is hidden on low quality.
   - Minimap: reuse `radar-canvas`, size, update rate, low-quality behavior.
   - Pedals: look and position only; sizes, touch target minimums; confirm input unchanged.
   - Game Hub: which existing buttons it groups, navigation flow, how existing feature IDs and `closeModals` are preserved.
   - Language: string-table design, supported languages, settings UI, save field name, fallback rule, how dynamic strings are handled, CI check for leftover text.
   - Performance: 30 FPS method (device, quality preset, scene, duration, how measured), pass/fail thresholds, what Martin records.
   - Acceptance criteria per task T-003B..E, and an explicit "not in scope" list.
3. Hand off using the format below. Do not claim real-device results; mark everything `designed` until Martin reports measurements.
4. Do not change approved numbers later without Martin's confirmation; propose changes as a new version.

Handoff format (must include full text):
```
HANDOFF ChatGPT -> Claude
Task: T-003A
Base commit: <main SHA>
Read: COLLAB.md v3, AGENTS.md, DECISIONS D-011/D-012/D-015, TASKS T-003A
SPEC (full text follows, or attached as T-003A-spec-v1.1.md):
<entire spec>
```

## 3. Instructions for Codex (implementer)
1. Start only when TASKS.md marks a task Ready for Codex and Martin has started it. Work from the latest `main`; record the base SHA in the PR.
2. Branch `codex/T-003B-camera` (use the task id and short name). One task per PR. Never push to `main`.
3. Implement exactly the task's Acceptance list in TASKS.md. No unrelated edits, no refactors, no gameplay or economy changes (D-014 values stay).
4. Do not touch `sw.js` CACHE unless told; Claude bumps it at release. Do not change input logic, physics, saves (beyond the one new language field in T-003E), or PWA/offline behavior.
5. Mobile performance is a hard constraint: no extra renderers, no per-frame allocations in hot loops, keep the minimap on `radar-canvas`.
6. Before opening the PR run `python3 tools/test/syntax_check.py` and any headless checks you can; fill the PR template honestly. List what you did NOT verify (real devices, FPS on S26 Ultra / Tab S11).
7. Open the PR via GitHub (branch `codex/T-xxx-name`) so Claude can fetch the diff. If push returns 403, report it; do not work around it.
8. After Claude's review, address requested changes on the same branch.

## 4. Martin's steps
1. Ask ChatGPT for the spec file and attach/paste the full text to Claude. Say "approved" when satisfied.
2. After Claude reports the docs PR and `main` SHA, tell Codex to start T-003B.
3. When Claude says "PR #n ready for hand testing": test on S26 Ultra and Tab S11, report FPS and layout results back.
4. Final gameplay acceptance for each task is Martin's.
