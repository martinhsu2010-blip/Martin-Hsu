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
