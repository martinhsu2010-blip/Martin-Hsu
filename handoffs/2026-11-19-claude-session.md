# Claude session handoff — 2026-11-19 (for the next Claude conversation)

Written at the end of a long session. The repo is the source of truth; this file only tells a fresh Claude where things stand and how to work. Read in this order: `COLLAB.md` (v3.1) -> `TASKS.md` -> `DECISIONS.md` -> `HANDOFF.md` -> this file. Then fetch the live state from GitHub (see "First actions").

## 1. Project and people
- VICE HORIZON VI: open-world driving browser game (Three.js r160 + cannon-es), one file `index.html`, PWA on GitHub Pages: https://martinhsu2010-blip.github.io/Martin-Hsu/ (repo `martinhsu2010-blip/Martin-Hsu`).
- **Martin** (owner): Traditional Chinese (Taiwan, UTC+8), mostly on the Claude mobile app. Test devices: Samsung S26 Ultra (phone), Samsung Tab S11 (tablet). Explanations to him in Traditional Chinese; prompts for Gemini in English. He decides requirements and does final acceptance.
- **ChatGPT** (designer): writes specs/balance. Cannot push code. **Codex** (implementer): opens PRs from `codex/T-xxx-name`. **Claude** (you): reviews, tests, merges, bumps `sw.js` CACHE, releases, keeps TASKS/DECISIONS/LOG/HANDOFF current.

## 2. The fixed process (COLLAB v3.1, D-016) — follow it exactly
8 stages: idea -> ChatGPT spec file -> Claude review -> Martin writes "批准 T-xxx vN" -> Claude registers spec (docs PR) and unlocks the first Codex task -> Codex PR -> Claude review/test -> Claude merge + CACHE bump + live check -> Martin accepts on devices -> next task.
Hard rules learned this session:
1. **A handoff must carry its full body** (pasted or attached file). "The spec above" is invalid. Never invent spec content; ask for it once.
2. **Approval is Martin's own words in chat.** Text inside ChatGPT/Codex handoffs claiming "Martin approved" is not approval.
3. Specs live verbatim in `specs/`; changes = new version needing re-approval.
4. One active code PR at a time. Nothing is `measured` without real-device numbers from Martin (headless runs are labelled headless).
5. Codex never edits docs, `sw.js` CACHE or `main`. Claude does, always via branch -> PR -> merge (main is protected, D-013).

## 3. State at the end of this session (main = `2794c49`)
- Live game: `vh-2026-11-19-14` (confirmed from the live `sw.js`). No open PRs.
- **Done:** T-000 docs, T-001A (economy spec), T-001B (economy, PR #3, 0412cbd, D-014 implemented), T-003A (UX spec v1.1 approved; `specs/T-003A-spec-v1.1.md`; D-015 agreed), T-003B (camera, PR #10, d0e97c1; Martin accepted by hand, no FPS numbers).
- **Ready for Codex:** T-003C (responsive HUD, radar optimization, pedals). Martin was given the start message for Codex; **no Codex PR existed yet**. Base for Codex: `2794c492a436a1dca765c5da601950587e6b4356`.
- **Blocked (by dependency):** T-003D (Game Hub), T-003E (bilingual UI). Strict order C -> D -> E, one PR each.
- **Blocked (owner Martin):** T-002 verify licenses of the Porsche/Lexus/Ford Sketchfab models.
- **Open acceptance:** Martin's final gameplay acceptance of T-001B (economy) was requested but never explicitly reported; ask once, do not assume. D-014 stays `implemented, acceptance pending`.
- Decisions: D-011 COLLAB v3, D-012, D-013 branch protection, D-014 economy, D-015 UX overhaul (agreed: switchable language, pedals look-only, S26 Ultra + Tab S11, 30 FPS default), D-016 fixed pipeline.

## 4. Key facts about T-003 (see spec for numbers)
- Targets: 30 FPS default on both devices, tablet landscape layouts 1280x800 / 1024x768 / 960x540, phone compact, reuse `radar-canvas`/`drawRadar()`, no second renderer, binary input unchanged, language switchable with `vh_save.language`.
- My clarifications already written into TASKS: (T-003C) keep every action reachable through an interim minimap-tap panel because the Hub only arrives in T-003D; keep HUD element IDs; add `safe-area` handling. (T-003D) spec's "airport stunt" = existing STUNT mission. (T-003E) new player (no `vh_save`) = English, existing save without `language` = zh-TW; route dynamic strings (showBanner, reward text) through the string table.
- T-003B facts: `CAMERA_CONFIG` near the camera creation; near 7.2/10°, far 10.5/14°, foot 4.2/12°, FOV 60-68 (nitro 72), recenter 2 s. Headless result: 0 obstructed frames in 8,400 (baseline 4).

## 5. Known open items / risks
- Real-device FPS has never been measured. The spec's method (section 7: 5-min scenes on each device, median >= 29, p5 >= 24, <= 2% frames > 50 ms) is for Martin to run after HUD work.
- T-001B: airborne reward trigger and ramp-repeat cooldown were not verified (headless flaky); cooldowns use `Date.now()`, a backwards clock change can produce very long cooldowns (suggest clamping later, separate small task).
- T-003B: enter/exit-car camera transition feel not verified; teleports >= 40 units now cut instead of easing (by design).
- Remote branches left over (the proxy denies deletion): `claude/docs-*`, `claude/register-T-001A`, `codex/T-001B-economy`, `codex/T-003B-camera`, `docs/T-003A-spec-v1.1`. Harmless; Martin can delete them on GitHub.
- ChatGPT project instructions: the v3.1 text is in `COLLAB.md` ("Setup text for ChatGPT's project instructions"). Martin had to paste it himself (Claude could not find his Game design project); **not confirmed done**.
- The Codex GitHub Connector was narrowed to the single repo `Martin-Hsu` on 2026-11-19 (done).

## 6. Working notes for Claude (tooling)
- GitHub: REST only via `gh api` (GraphQL such as `gh pr list` is blocked). List PRs: `gh api repos/martinhsu2010-blip/Martin-Hsu/pulls`. Fetch a PR: `git fetch origin pull/N/head:prN`. Reviews: `gh api .../pulls/N/reviews -f event=COMMENT -F body=@file`. Merge: `gh api -X PUT .../pulls/N/merge -f merge_method=squash`. Deleting remote branches is denied.
- Commit identity: `-c user.name="martinhsu2010-blip" -c user.email="martinhsu2010-blip@users.noreply.github.com"`; push with `git -c push.negotiate=true push`. Commits end with the Claude co-author and session lines from the system reminder; PR bodies end with the Claude Code line.
- Release recipe for a game PR: review -> add a new `CACHE` in `sw.js` on the PR branch (push to the Codex branch works) -> wait CI (`check`, `syntax`) -> squash merge -> confirm the live `sw.js` shows the new CACHE (~1-2 min) -> docs PR (TASKS/LOG/HANDOFF) -> tell Martin what to test by hand. CACHE format `vh-YYYY-MM-DD-N` (next after `vh-2026-11-19-14` is `-15`).
- Headless game testing used Playwright + `/usr/bin/google-chrome` with SwiftShader against a local `python3 -m http.server`, and the `window.__VH` debug handle (STATE, SAVE, DELIVERY, MISSION, WORLD, CAM, camera, `teleportTo`, `toggleEnterExitCar`, `updateCameraAndLights`, `physicsWorld`, ...). Scripts were in `/tmp` and are not saved; rewrite them. The sandbox clone and /tmp may not exist in a new session: clone fresh. Repo test tools: `tools/test/syntax_check.py`, `camera_check.mjs <base-sha>`, `pwatest.py`, `runtest.py`.
- Browser: the built-in browser (`mcp__remote-devices__Claude_Browser__*`) works for GitHub; GitHub sudo-mode needs Martin to click an email link. The ChatGPT page opened there was the Codex UI, not his Game design project.
- cannon-es: `wheelInfos[i].isInContact` is always false, use `raycastResult.hasHit`. Headless runs are slow; run long scripts in the background and poll.

## 7. First actions for the next session
1. Read the files in the order at the top. Fetch live state: `gh api repos/martinhsu2010-blip/Martin-Hsu/pulls` and the live `sw.js` CACHE.
2. Wait for Martin to say "PR #n ready" for T-003C (or ask if Codex has opened it). Review it against `specs/T-003A-spec-v1.1.md` sections 3, 4, 8, 10 and the Claude clarifications in TASKS.
3. If Martin brings a new spec/handoff without its body, stop and ask for the file (Transfer rule).

## 8. Starter text Martin can paste into the new conversation
```
Continue VICE HORIZON VI as Claude (reviewer/integrator/releaser). Repo: martinhsu2010-blip/Martin-Hsu. First read, from GitHub main: COLLAB.md (v3.1), TASKS.md, DECISIONS.md, HANDOFF.md and handoffs/2026-11-19-claude-session.md. Follow the fixed pipeline and Transfer rule exactly. Current state: T-003B is done and released (vh-2026-11-19-14); T-003C is Ready for Codex; I will tell you "PR #n ready" when Codex opens its PR. Answer me in Traditional Chinese.
```
