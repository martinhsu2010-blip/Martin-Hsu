# Decision register (append-only; rules in COLLAB.md)

Format: a header line per decision, then one event line per status change, newest last. Latest event = current state. Never edit or delete old events. Keep secrets and personal info out (public repo).
Event format: `D-NNN | date | proposed/agreed/implemented/dropped | note or commit SHA`

## D-001 Single-file `index.html` PWA on GitHub Pages, all assets vendored locally (offline play, no build step)
D-001 | 2026-11 | implemented | in repo from first deploy

## D-002 Cars load from GLB via a `CAR_MODELS` registry; physics wheels laid out from the model's wheel nodes
D-002 | 2026-11-18 | implemented | commit 2dfdf7d

## D-003 Ford Shelby GT500 is the police car; Porsche 911 ($25,000) and Lexus LC 500 ($18,000) are bought with in-game cash
D-003 | 2026-11-18 | agreed | by Martin
D-003 | 2026-11-18 | implemented | commit 2dfdf7d

## D-004 Income from delivery jobs (random destination, no physical cargo) and daily stunt jumps
D-004 | 2026-11-18 | agreed | by Martin
D-004 | 2026-11-18 | implemented | commit 2dfdf7d

## D-005 NPC traffic uses low-poly Kenney cars, ~50% higher density, distance recycling and far-physics freezing
D-005 | 2026-11-18 | agreed | by Martin
D-005 | 2026-11-18 | implemented | commit 2dfdf7d

## D-006 Progress (cash, owned cars, jumps) saved in localStorage `vh_save`
D-006 | 2026-11-18 | implemented | commit 2dfdf7d

## D-007 Claude/ChatGPT collaborate through repo files; only the builder pushes `main`
D-007 | 2026-11-18 | agreed | by Martin
D-007 | 2026-11-18 | implemented | COLLAB v2 adopted, docs in repo

## D-008 Build ChatGPT's proposed "Dual AI Studio" (own server + API keys)
D-008 | 2026-11-18 | proposed | Claude advises against for now (cost, needs always-on PC, API Claude loses sandbox tools); revisit after v2 runs a few weeks

## D-009 Docs-only changes do not need a game version bump; any change to a file in `sw.js` PRECACHE does; enforced by CI
D-009 | 2026-11-18 | agreed | by Martin via ChatGPT review
D-009 | 2026-11-18 | implemented | .github/workflows/pwa-cache-check.yml

## D-010 Division of labour: ChatGPT (GPT-6 Astra) writes code as diffs; Claude reviews, brainstorms, tests, and releases (supersedes the builder/designer split in D-007)
D-010 | 2026-11-18 | agreed | by Martin
D-010 | 2026-11-18 | implemented | COLLAB.md roles and feature flow updated

## D-011 COLLAB v3: ChatGPT designs/specs, Codex implements via GitHub PRs, Claude reviews/integrates/releases (supersedes D-010)
D-011 | 2026-11-18 | agreed | by Martin
D-011 | 2026-11-18 | implemented | COLLAB v3, AGENTS.md, PR template, CI updated
D-010 | 2026-11-18 | dropped | superseded by D-011

## D-012 Only one active code PR at a time; Codex never merges, never edits sw.js CACHE or docs; Claude bumps CACHE at integration
D-012 | 2026-11-18 | agreed | by Martin
D-012 | 2026-11-18 | implemented | AGENTS.md and CI (PR = warning, main = failure)

## D-013 Protect `main` on GitHub (require PR, no force push)
D-013 | 2026-11-18 | agreed | by Martin
D-013 | 2026-11-18 | implemented | GitHub classic rule on main: PR required (0 approvals), applies to admins, no force push, no deletion

## D-014 Economy Balance Specification v1.0 approved for T-001B
D-014 | 2026-11-18 | agreed | Martin approved T-001A Economy Balance Specification v1.0, covering purchase-time targets, delivery rewards/time limits, stunt and mission payouts, reward cooldowns, and save compatibility. Implementation assigned to Codex as T-001B; full specification in TASKS.md.
D-014 | 2026-11-18 | implemented | PR #3, commit 0412cbd (game vh-2026-11-18-13); Martin final gameplay acceptance pending.

## D-015 Immersive UX overhaul scope (T-003)
D-015 | 2026-11-19 | proposed | ChatGPT proposed an immersive UX overhaul (lower/closer camera, minimap-driven Game Hub, racing-style pedals, localization), split into T-003B..E. Claude reviewed feasibility (see TASKS T-003A).
D-015 | 2026-11-19 | agreed | Martin: language is switchable via a UI setting (not English-only); pedal changes are look/layout only with unchanged input behavior; target devices Samsung S26 Ultra and Samsung Tab S11. Full spec still needs Martin approval before any implementation.

D-015 | 2026-11-19 | agreed | Martin approved the complete T-003A Immersive Gameplay UX Specification v1.1 (`specs/T-003A-spec-v1.1.md`, archived verbatim in PR #8, commit ea43ece). Basis: Martin's chat messages of 2026-11-19 (05:45, 05:54 "批准") and his 05:59 request to register it after PR #8. Claude could not compare the file with ChatGPT's original chat text; the archived file is the approved version. Tasks T-003B..E run sequentially, one PR at a time; only T-003B is Ready for Codex.

## D-016 Fixed collaboration pipeline (COLLAB v3.1)
D-016 | 2026-11-19 | agreed | Martin asked for a fixed, repeatable process. COLLAB v3.1 defines 8 stages with gates, a Transfer rule (a handoff must carry its full body; Claude never invents spec content; approval is only Martin's own words), full specs stored verbatim in `specs/`, and standard message templates. Supersedes the free-form handoff block of v3.

## D-017 Living City 2.0 (T-004A v1.1) approved; suburbs use Option B
D-017 | 2026-11-19 | agreed | Martin approved the complete T-004A Living City 2.0 Specification v1.1 (`specs/T-004A-spec-v1.1.md`, archived verbatim in PR #23, commit a53d0ba) and selected suburban style Option B — Mixed American Small Town. Basis: Martin's chat message of 2026-11-19 17:28 ("正式批准 T-004A Living City 2.0 Specification v1.1。郊區建築採用 Option B"). All numbers in the spec (traffic pool table, Option B type shares and caps, collider tolerances, activation radii, FPS targets) are binding; changes need a new spec version approved by Martin. Claude could not compare the file with ChatGPT's original attachment; the archived file is the approved version. Tasks T-004B → C → D → E run sequentially, one code PR at a time, each released and Martin-accepted before the next; only T-004B is Ready for Codex.
D-017 | 2026-11-20 | implemented | T-004B (89f1a18, vh-2026-11-19-18), T-004C (06e0514, vh-2026-11-19-19), T-004D (17c16b3, vh-2026-11-20-01) and T-004E (dd4918d, vh-2026-11-20-02) released and Martin-accepted. Known deviation: desktop Old Town infill is +2.3% (89 vs 87 buildings) against the spec's +35% target because no legal 10x10 slot remains at the required clearances; Martin accepted it. Raising it later needs a new task/spec version.

## D-018 Second implementer: Gemini (Jules) for simple tasks
D-018 | 2026-11-20 | proposed | Martin asked whether Gemini could take part and how to cope with Codex's 5-hour usage limit. Claude advised splitting work by whole task, not mid-task; Martin proposed routing simple tasks (language strings, low-difficulty coding) to Gemini and the rest to Codex.
D-018 | 2026-11-20 | agreed | Martin ("可以，等到T-004E發布完、你驗收通過之後下一個任務再啟用新分工，不過你要注意也要讓gpt知道這個改動", 2026-11-20 05:50) approved the routing rule in COLLAB v3.2: Gemini (normally via Jules, repo-scoped GitHub app) takes only tasks that meet every criterion in "Implementer routing"; Codex takes everything else; ChatGPT marks `Implementer:` in each spec; one active code PR at a time; first Gemini tasks are a stricter-review trial. Effective from the first task after T-004E (accepted 2026-11-20). Martin has a working Jules account. Claude wrote a notice for ChatGPT (Martin relays it); ChatGPT must re-read COLLAB v3.2 before the next spec.
D-018 | 2026-11-20 | dropped | Suspended. Google announced (2026-10-29) that Jules is read-only after 2026-11-11 and shuts down 2026-12-31; no other Gemini agent that can open PRs on this repo exists on Martin's phone/tablet workflow (Antigravity is a desktop app; its cloud execution is not available). Martin chose to keep the original setup: Codex implements all code tasks. COLLAB v3.3 keeps the routing text, marked suspended, for a possible restart; reopen with a new decision.

## D-019 World coherence cleanup (T-005)
D-019 | 2026-11-20 | agreed | Martin ("批准", 2026-11-20 14:06) approved `specs/T-005-spec-v1.md`. Changes to D-017 numbers: ordinary traffic table raised per T-005 Part 2 (a preset may keep its old count if the performance guard trips); suburban caps (210 phone / 390 desktop) unchanged unless a later audit proposes a new cap for Martin; city infill soft gap rules may be relaxed per Part 4 (hard rules unchanged). The parked Muscle 69 is removed from the spawn area; the garage option stays. Split into T-005A (Parts 1-2) then T-005B (Parts 3-4). Spec causes marked "hypothesis" are unconfirmed until each task's audit.

## D-020 Reactivate the second implementer via Antigravity Remote Agents
D-020 | 2026-11-20 | agreed | supersedes the suspension recorded in D-018 (dropped). Martin ("決定正式重啟並採用 Antigravity Remote Agents", 2026-11-20 15:55) confirmed on his phone that his personal Google AI Pro account has Remote Agents (cloud sandbox opened at antigravity.google.com, GitHub repo attached, no computer needed). Claude checked Google's docs: available to AI Pro/Ultra personal accounts, rolling out gradually, not on free/Plus/Workspace; default permission preset runs commands without approval, so `main` protection (D-013) is the backstop. COLLAB v3.4: Gemini takes only whole low-risk tasks (UI strings/translations, wording polish, static HUD/menu CSS, no-logic doc fixes) on branch `gemini/<task-id>` with a minimal `index.html` diff; never physics, collisions, vehicle handling, traffic/police AI, world generation, draw calls/rendering performance or save format. Codex and Antigravity share ONE code-PR lock; no mid-task handoff. First Gemini tasks are a trial with stricter review. Unverified: that Antigravity opens PRs with the requested branch name and reads AGENTS.md (the trial checks both).
D-019 | 2026-11-20 | implemented | T-005A (Parts 1-2) released as vh-2026-11-20-03, commit d57d0db (PR #43); T-005B (Parts 3-4) still queued, starts after Martin accepts T-005A.
D-019 | 2026-11-21 | amended | Martin ("批准", 2026-11-21 09:02, after Claude's review) approved `specs/T-005-spec-v2.1.md` (ChatGPT; stored verbatim). It replaces Part 4 only; Parts 1-3 are verbatim v1. Martin rejected the c8e395f city shortfall (HARD_EMPTY 145 phone / 171 desktop centers, CAN_ADD 0): residual lots become visible pocket parks (1 shared batch, +0 body/shape), coverage shells get 4 heights and 5 colours per district from seed 5019 (+0 draw), colliders grouped per 120x120 cell with a +35% paired headless physics limit, and a `?fps=1` diagnostic readout is added for Martin's device acceptance (>= 30 FPS average per district). T-005B continues in PR #47.
D-019 | 2026-11-21 | implemented | T-005B (suburb frontage Part 3 + city Part 4 per v2.1) released as vh-2026-11-21-01, commit be87c2f (PR #47); awaiting Martin's device acceptance. Claude-verified: physics step ratio 1.13/1.06 (limit 1.35), draw calls within budgets, verge +0.04 over terrain, parks cover all 145/171 residual centers, `?fps=1` readout works with auto-quality off only while active.
D-019 | 2026-11-21 | done | Martin accepted T-005B (vh-2026-11-21-01) on his devices ("通過", no FPS numbers reported). T-005 is complete; the code-PR lock is free.

## D-021 COLLAB v3.5: staged authorization for Gemini
D-021 | 2026-11-21 | agreed | supersedes the implementer-routing scope of D-020 (D-020 history unchanged). Martin ("批准", 2026-11-21 15:21, after Claude's review of ChatGPT's COLLAB-v3.5-DRAFT-2.md) approved COLLAB v3.5: Gemini starts at Stage 1 (strings/static CSS) and is promoted only by Martin's explicit approval, Stage 2 (whole non-critical features, first one is a trial) and Stage 3 (Codex-equivalent, needs regression tests and Claude's independent T-005B-style physics/draw-call measurements); Stage 2 to 3 needs two consecutive different-category tasks (no exception). Kept: one shared code-PR lock, one implementer per whole task, D-013 main protection (Claude re-checks it on every Gemini PR and records the result), Claude-only `sw.js`/docs/`.github/`. New tests are wired into `pwa-cache-check.yml` by Claude at release. Board column renamed `Ready for Implementer`. `AGENTS.md` synced in the same PR. Registered text: `COLLAB.md` is draft 2 verbatim except the status banner. Note: a few transitional lines in v3.5 (e.g. §0, §5.1, §6, §8, §11 say "not effective until approved") are now stale; ChatGPT's project setting text (§11) should be updated by Martin.

## D-022 T-006 approved as Gemini's Stage 1 trial
D-022 | 2026-11-21 | agreed | Martin ("批准", 2026-11-21 15:32, after Claude's review) approved `specs/T-006-spec-v1.md` (ChatGPT; stored verbatim): zh-TW `shared_space` "Space" -> "空白鍵", one-line diff in index.html, implementer Gemini (Antigravity), branch `gemini/T-006`. First Stage 1 evidence under D-021; passing it does not promote Gemini to Stage 2 (needs Martin's separate explicit approval). Claude re-checks main protection (D-013) on the PR.
D-022 | 2026-11-21 | implemented | T-006 (PR #53 by Gemini/Antigravity) released as vh-2026-11-21-02, commit ffbe3f4. Strict +1/-1 diff, all nine AGENTS checks reported honestly, Claude's independent checks and D-013 protection re-check passed. First Stage 1 evidence; no promotion (needs Martin's separate explicit approval).
D-022 | 2026-11-21 | done | Martin accepted T-006 (vh-2026-11-21-02) on his devices ("通過"). Gemini remains Stage 1; no promotion requested. Code-PR lock free.

## D-023 Gemini promoted to Stage 2
D-023 | 2026-11-21 | agreed | Martin ("升2", 2026-11-21 16:09, replying to Claude's request for the COLLAB v3.5 §7.4 promotion sentence; his own words, accepted as the explicit promotion) promoted Gemini from Stage 1 to Stage 2 on evidence PR #53 (T-006, accepted). Scope per COLLAB v3.5 §4.2 / AGENTS.md: whole non-critical features, no save-schema/physics/collisions/vehicle/world/traffic/police/render-perf; each task needs an approved spec; the first Stage 2 task is a trial. Stage 3 needs a separate promotion and the §4.3 test gate.

## D-024 T-007 approved as Gemini's first Stage 2 trial
D-024 | 2026-11-21 | agreed | Martin ("批准", 2026-11-21 16:36, after Claude's review) approved `specs/T-007-spec-v1.md` (ChatGPT; stored verbatim): WORLD-tab "Next Stop" card, four fixed bilingual destination suggestions, in-memory only, no save/physics/render changes. Implementer Gemini (Antigravity), branch `gemini/T-007`; mandatory Stage 2 trial under COLLAB v3.5 §4.2 with a failing-capable regression test; Claude re-checks D-013 and wires CI. Passing it is the first of the two distinct-category Stage 2 evidences needed before any Stage 3 request.
D-024 | 2026-11-21 | implemented | T-007 (PR #59 by Gemini/Antigravity) released as vh-2026-11-21-03, commit 670acbc. Claude verdict: Stage 2 trial 通過. New test `explore_picks_check.mjs` wired into CI (workflow step ran and passed). Awaiting Martin's device acceptance; Stage 3 needs a second distinct-category Stage 2 task plus Martin's explicit promotion.
D-024 | 2026-11-21 | done | Martin accepted T-007 (vh-2026-11-21-03) on his devices ("通過t-007"). First of two distinct-category Stage 2 evidences recorded; Martin's request to go to Stage 3 now was declined under COLLAB v3.5 §4.2 (2 tasks required, no exception); second task (T-008) to be specified. Code-PR lock free.

## D-025 T-008 approved as Gemini's second Stage 2 task
D-025 | 2026-11-21 | agreed | Martin ("批准", 2026-11-21 17:58, after Claude's review) approved `specs/T-008-spec-v1.md` (ChatGPT; stored verbatim): Zone Arrival HUD, a passive 2,500 ms localized district-entry notice driven by the existing `renderDrivingHUD()` zone logic, no save/physics/render changes. Category: general HUD behavior (distinct from T-007). Implementer Gemini, branch `gemini/T-008`. If it passes with Claude's verdict and Martin's device acceptance it is the second distinct-category Stage 2 evidence; Stage 3 still needs Martin's separate explicit approval and the COLLAB v3.5 §4.3 gate.
D-025 | 2026-11-21 | implemented | T-008 (PR #63 by Gemini/Antigravity) released as vh-2026-11-21-04, commit 0803a21. Claude verdict: Stage 2 task 2 通過; `zone_arrival_check.mjs` wired into CI (step ran and passed). Awaiting Martin's device acceptance. If accepted, Gemini has two distinct-category Stage 2 evidences; Stage 3 still needs Martin's separate explicit promotion and the COLLAB v3.5 §4.3 gate.
D-025 | 2026-11-21 | done | Martin accepted T-008 (vh-2026-11-21-04) on his devices ("通過"). Gemini now has two distinct-category, Martin-accepted Stage 2 evidences (T-007 PR #59, T-008 PR #63) with zero recorded violations; COLLAB v3.5 §4.2 promotion condition is met on evidence. No promotion recorded: it needs Martin's explicit message. Code-PR lock free.

## D-026 Gemini promoted to Stage 3
D-026 | 2026-11-21 | agreed | Martin ("批准 Gemini 升至階段 3，依 COLLAB v3.5，證據 PR #59、#63", 2026-11-21 18:53) promoted Gemini from Stage 2 to Stage 3 on evidence T-007 (PR #59) and T-008 (PR #63): two distinct-category Stage 2 tasks, each reviewed, released and device-accepted, with zero recorded violations. Scope per COLLAB v3.5 §4.3: Codex-equivalent tasks, but each task needs a Martin-approved spec, per-risk regression tests, quantified acceptance values and Claude's independent paired measurements; the first high-risk task needs a separate test-completeness assessment. Rollback conditions in §4.3 apply.

## D-027 COLLAB v3.6: task routing and phased small tasks
D-027 | 2026-11-21 | agreed | supersedes the routing table of COLLAB v3.5 §5 (D-021 stage system and all gates unchanged). Martin ("批准", 2026-11-21 19:04, on Claude's COLLAB-v3.6-DRAFT.md delivered in the same conversation; he chose not to have ChatGPT cross-review it) approved: §5.1 routing (large-volume low-risk testable work -> Gemini; small high-risk judgment work -> Codex by default, Gemini only at Stage 3 with the full §4.3 gate; risk overrides volume; large and high-risk work is split), §5.2 phased small tasks with suggested size limits (about 600 logic lines, or 800 data lines / 150 i18n keys, per PR; each phase has its own regression test; no parallel phases), stale v3.5 transitional wording removed, ChatGPT project text updated. Open questions in §10 (size limits, objective risk/volume criteria) to be revisited after a few tasks.

## D-028 T-009 approved as Gemini's first Stage 3 task
D-028 | 2026-11-21 | agreed | Martin ("批准", 2026-11-21 19:57, replying to Claude's request for "批准 T-009 v1.1" after Claude's review; accepted under the same practice as D-022/D-024/D-025) approved `specs/T-009-spec-v1.1.md` (ChatGPT; stored verbatim): Midtown crosswalk pilot, 32 static stripes in one InstancedMesh at intersections (-240,-360) and (0,-360). v1 was revised to v1.1 after Claude's review found the in-loop physics measurement infeasible in headless (about 1 step/s) and noisy (baseline-vs-baseline spread up to about 20%); v1.1 uses in-page synchronous stepping, 5-pair calibration and a 5-to-9 pair verdict. Gate: Claude's pre-start audit must complete before Gemini starts (v3.6 §4.3). Known notes: effective cap is min(1.10, calibration median + 0.10); draw-call samples use in-page renderer.render frames (same method both versions).

## D-029 T-009 spec v1.2 approved (physics gate revised)
D-029 | 2026-11-21 | agreed | Martin ("批准", 2026-11-21 21:28, after Claude's review; same practice as D-028) approved `specs/T-009-spec-v1.2.md` (ChatGPT; stored verbatim), which changes only §6.2 of v1.1 (D-028 otherwise stands). Reason: Claude's pre-start calibration (PHONE_LOW, near scene, baseline vs baseline, 5 pairs: ratios 0.748/0.634/1.015/0.779/1.146, median 0.779) showed headless step-time noise of about +-30%, which made v1.1's cap min(1.10, calibration median+0.10) (= 0.879 here) fail identical code about half the time. v1.2: fixed PR/baseline median cap <= 1.25 (5 pairs, extend to 9), calibration is validity-only (median within [0.75, 1.33], else MEASUREMENT BLOCKER), alternating A/B order, bodies/shapes delta = 0 remains the primary hard gate. Old A09 "<=1.10" and v1 prompt wording are superseded by the v1.2 §6.2 precedence rule.

## D-030 T-009 spec v1.3 approved (second intersection moved to (-120,-360))
D-030 | 2026-11-21 | agreed | Martin ("批准", 2026-11-21 23:26, after Claude's review; same practice as D-028/D-029) approved `specs/T-009-spec-v1.3.md` (ChatGPT; stored verbatim). Change from v1.2: second crosswalk intersection (-240,-360) -> (-120,-360) in §3.1, R1, §6.1.5 (near scene teleportTo(-120,-408,0)), A03 and the English prompt; §6.2 is byte-identical to v1.2 (Claude verified by diff). Reason: Claude's pre-start scene check found Vice Broadway (RIBBON_DEFS, half 9) cuts diagonally through (-240,-360) at the same y=0.085 as the stripes (z-fighting, stripes across a diagonal carriageway); (0,-360) and (-120,-360) are flat standard junctions (screenshots checked). Pre-start calibration (baseline vs baseline, 5 alternating pairs, medians in [0.75,1.33]): PHONE_LOW near 1.149 / ctrl 1.042, TABLET_MED near 1.039 / ctrl 0.821, DESKTOP_HIGH near 0.905 / ctrl 0.998; bodies/shapes identical across pairs. Calibration scenes (0,-408) and (110,650) are unaffected by the move. Gemini's prompt must reference spec v1.3 at `specs/T-009-spec-v1.3.md`.
D-030 | 2026-11-22 | implemented | T-009 (PR #71 by Gemini/Antigravity) released as vh-2026-11-22-05, commit b729942. Claude verdict: Stage 3 trial PASS. New test `midtown_crosswalk_check.mjs` wired into CI (workflow step ran and passed). Independent checks: 13 AGENTS commands PASS; 11 mutations turn the test red; physics (in-page step, 5 alternating pairs, cap 1.25) medians 1.186/1.051 PHONE_LOW, 1.023/1.045 TABLET_MED, 0.966/1.047 DESKTOP_HIGH, bodies/shapes +0 in every pair; draw calls near +1 (all presets), control +0. D-013 re-check 2026-11-22 02:54 CST: PR required true, enforce_admins true, force pushes false, deletions false, rulesets 0. Disclosures: draw-call counting used no-op GL draw calls on software GPU and excludes postFX passes; spec R5 (real-browser check) was done by Claude, not committed in the test; headless numbers are not device measurements. Awaiting Martin's device acceptance (A12).
D-030 | 2026-11-22 | accepted | Martin accepted T-009 on his devices ("通過", 2026-11-22 08:36). He did not report `?fps=1` averages for S26 Ultra and Tab S11, so the >=30 FPS part of A12 is recorded as unmeasured, not passed. Gemini Stage 3 first task complete; no rollback.

## D-031 T-010 spec v1.1 approved (Midtown coverage facade pilot, Codex)
D-031 | 2026-11-22 | agreed | Martin ("批准", 2026-11-22 08:57, after Claude's G0 review; same practice as D-028..D-030) approved `specs/T-010-spec-v1.1.md` (ChatGPT; stored verbatim). Implementer: Codex (HIGH risk, SMALL volume, routing per COLLAB v3.6 §5.1). v1 was revised after Claude's review found: coverage windows sit at b.w/2+0.06 (not +0.09) with width scale b.w/5; tablet preset must be 800x1280 TABLET (844x390 is classed PHONE); new meshes must register in FACADE.chunks; fixed near camera (-232,5,-292) -> (-268,7,-310); R5 is Claude-run; tests must read the live WORLD.cityInfill. G0 result: each profile has 16+ coverage buildings in the bbox (PHONE/TABLET list vs DESKTOP list differ), east faces visible, no occlusion by Vice Broadway. Limits: physics median <= 1.25 (5 alternating pairs, extend to 9), bodies/shapes delta 0; near draw calls +2/+3/+4, control +0. New-scene baseline calibration (near (-232,5,-292) view and control (110,650)) is run by Claude while Codex implements; an invalid calibration is reported before Codex's PR is reviewed.

## D-032 T-010 released (Midtown coverage facade pilot, Codex)
D-032 | 2026-11-22 | implemented | PR #75 squash-merged as ae3951a, CACHE vh-2026-11-22-06, midtown_facade_pilot_check wired into CI. Claude review PASS: 16/16 injected mutations caught, baseline fails; bodies/shapes delta 0; physics median ratio PHONE 0.988 (5 pairs, calibration 0.943), TABLET 1.069 (5 pairs), DESKTOP physics not paired (test shows world unchanged); draw calls near +2 / control +0 on PHONE, TABLET, DESKTOP (TABLET 3 and DESKTOP 2 pairs, not 5; counts identical every pair; postFX excluded, LOD forced). Day/night screenshots clean. D-013 checked 2026-11-22T02:04Z via API. Pending Martin's device acceptance (`?fps=1` >=30; unreported = unmeasured).
