# CLAUDE.md — working notes for Claude (reviewer / integrator / releaser)

Roles and pipeline are in `COLLAB.md` (v3.3); this file only covers how Claude works efficiently. It never changes a role, a test requirement or an approved spec.

## Token efficiency (never at the cost of review quality)
1. **Review the diff, not the file.** Fetch the PR diff (`gh api repos/.../pulls/N/files`) and read changed hunks with their surroundings; locate anything else with `grep -n` and read small ranges of `index.html`. Use `HANDOFF.md` as the code map.
2. **Spend verification where the risk is.** Physics, traffic, collisions, world generation, saves, offline and draw calls get independent checks (run the tests, measure, look at screenshots); mechanical parts of a PR rely on CI plus a diff read. Never accept a number that decides acceptance (draw calls, counts, pass-through) only because the PR says so.
3. **Reuse, don't rediscover.** Keep probe scripts and the headless browser setup in one scratch script per task and reuse it across profiles instead of rewriting it; take only the screenshots that answer a question (one view per profile, same camera pose as the base build).
4. **Batch docs.** One docs PR per event (TASKS + LOG + DECISIONS + HANDOFF together), edited with a small script or targeted replace instead of re-reading whole docs already in context; commit, push, open the PR, check CI and merge in as few commands as practical.
5. **Short replies to Martin.** Traditional Chinese, conclusion first, what he must do next, no recap of steps. Longer detail goes in the PR/doc, not the chat.
6. **No fixed budgets.** If a review needs a deep dive (it found the T-004E z-fighting and the T-004C collider offsets that way), do it. Efficiency never overrides a required audit, test or acceptance check.

## Known environment facts (saves re-discovery)
- GraphQL is blocked: use `gh api` REST for PRs, merges and check-runs (`gh pr checks` fails).
- Local `main` may diverge: branch with `git checkout -B <branch> origin/main`; never `pull --ff-only`.
- Headless Chrome reports a SwiftShader GPU (classed `IGPU`): spoof `WEBGL_debug_renderer_info` (37446/7937) to reach DESKTOP/HIGH.
- `PHONE_LOW` skips `loadPolyHavenModels()` (no facade kit, `__phDone` never fires): use TABLET/MED or spoofed DESKTOP/HIGH to judge facades.
- Claude in Chrome is not reachable from the phone app: give Martin manual steps instead.
- Release = bump `CACHE` in `sw.js` (Claude only); Codex never edits it or the docs.
