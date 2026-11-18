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
