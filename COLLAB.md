# COLLAB v3.2 — ChatGPT × Codex × Gemini × Claude protocol (VICE HORIZON VI)

v3 adopted 2026-11-18 (D-011). v3.1 (2026-11-19, D-016) fixes the pipeline: every feature runs the same stages, gates and message templates below. v3.2 (2026-11-20, D-018) adds Gemini as a second implementer for simple tasks (routing rule below); the pipeline itself is unchanged. Martin relays between the AIs. **This GitHub repo is the single source of truth.** No AI can see another's private chat; only what is written in the repo or on GitHub is shared.

## Roles
- **ChatGPT (designer/analyst)**: feature design, economy balance, bug analysis, task specs, design review. Writes specs, not code.
- **Codex (implementer, default)**: implements ONE approved task from its spec, runs checks, pushes a `codex/T-xxx-name` branch and opens a Pull Request. Never touches `main`, `sw.js` CACHE or the docs. Rules in `AGENTS.md`.
- **Gemini (implementer for simple tasks only)**: same job, same rules, same limits as Codex (`AGENTS.md`), branch `gemini/T-xxx-name`. Normally runs as **Jules** (jules.google.com, connected to this repo only; it reads `AGENTS.md` itself, proposes a plan and publishes a branch/PR). Which implementer a task gets is decided by the routing rule below.
- **Claude (reviewer, integrator, releaser, brainstorm partner)**: fetches each PR from GitHub, reviews, runs the game in a headless browser, comments, merges, resolves conflicts, bumps `CACHE`, releases, updates TASKS/DECISIONS/LOG/HANDOFF. Small defects Claude fixes itself and says so; larger ones go back to Codex.
- **Martin**: requirements, priorities, final acceptance. Starts Codex tasks and tells Claude when a PR is ready. Only Martin/Claude merge; nobody merges from inside Codex.

## Files (repo root is the only official location; ignore any old `records/` path)
`COLLAB.md` this protocol · `specs/` full approved specs (`T-xxx-spec-vN.md`, template in `specs/TEMPLATE.md`) · `AGENTS.md` rules for Codex · `HANDOFF.md` how the project works · `TASKS.md` board · `DECISIONS.md` register · `LOG.md` releases · `tools/` scripts · `.github/` CI + PR template.
Re-read at the start of each session: `https://martinhsu2010-blip.github.io/Martin-Hsu/<FILE>` (Pages refreshes ~2 min after a push; Claude reads GitHub directly).

## Fixed pipeline (every feature, same order, no skipping)
| # | Stage | Owner | Input | Output (where it lives) | Gate to next stage |
|---|-------|-------|-------|-------------------------|--------------------|
| 1 | Idea | anyone | Martin's request | `TASKS.md` Inbox, `proposed` | Martin says go |
| 2 | Design/spec | ChatGPT | the idea + repo docs | ONE self-contained file `T-xxx-spec-vN.md` using `specs/TEMPLATE.md` | file delivered in full (see Transfer rule) |
| 3 | Spec review | Claude | the spec file | review report to Martin (feasibility, mobile cost, save compatibility, scope) | Martin writes "批准 T-xxx vN" |
| 4 | Register | Claude | approved spec | docs PR: spec committed verbatim to `specs/`, TASKS entries (A to Done, B..n created with dependencies, only the first in `Ready for Codex`), new `agreed` event in DECISIONS | docs PR merged; Claude reports the `main` SHA |
| 5 | Implement | Implementer (Codex or Gemini) | `Ready for Codex` task + `specs/` + AGENTS.md | PR from `codex/T-xxx-name` using the PR template | PR open, CI green |
| 6 | Review | Claude | "PR #n ready" (Gemini PRs get stricter review for their first tasks) | GitHub review: approved / changes-requested / rejected | approved (fix loop max 2 rounds, then Martin decides) |
| 7 | Release | Claude | approved PR | squash merge, `CACHE` bump, live check, DECISIONS `implemented (SHA)`, TASKS/LOG/HANDOFF | live site shows the new `CACHE` |
| 8 | Accept | Martin | released build on his devices | numbers and verdict reported back; task `Done` with evidence in `Verification` | Martin accepts; then the next task starts at stage 5 |

Rules: **one active code PR at a time**; a multi-task feature runs its tasks strictly in order and each task goes through stages 5-8 before the next starts. The branch starts from the latest `main`; the author rebases when `main` moves. Nothing is `measured` without a real-device number from Martin.

## Implementer routing (D-018, effective from the first task after T-004E)
Every task spec and every `TASKS.md` entry carries `Implementer: Codex` or `Implementer: Gemini` plus one sentence of reason. **Gemini only if ALL hold**: the task touches only language strings (`STRINGS`/`tr()`), isolated UI text/layout, or one small self-contained feature; it does NOT touch physics, traffic, collisions, world generation, save format or camera; it spans at most one or two systems; an existing automated check can catch mistakes (e.g. `i18n_check`, `hud_check`). Everything else, and anything in doubt, is Codex. If a Gemini task turns out to touch a shared or excluded system, Gemini stops and reports; Claude reassigns the **whole** task to Codex (never half-and-half PRs). A task already started is finished by the same implementer; when Codex's quota runs out Martin waits for the reset or, between tasks, reassigns the next task. Still one active code PR at a time, so the two implementers never edit `index.html` in parallel. The first Gemini tasks are a trial: Claude reviews them more strictly (scope, rule-following, honesty of the report) and reports the result to Martin before more are routed to Gemini. Jules may choose its own branch name; Claude records the real branch in `TASKS.md` and accepts it. If Jules is unavailable, a Gem or chat window may be used only for tiny tasks: Gemini returns changed functions as before/after blocks, Claude applies them on `gemini/T-xxx` and opens the PR marked "applied by Claude", and Claude does not repair logic errors (back to Gemini).

## Transfer rule (what makes a handoff valid)
- No AI sees another AI's chat. A handoff that points at text "above", "in the previous message" or "in the project" is **invalid**.
- Every handoff carries its full body: pasted in the same message, or attached as the named `.md` file. Claude never guesses, reconstructs or invents spec content (numbers, sizes, thresholds). If the body is missing Claude stops and asks once for the file.
- **Approval is Martin's own word.** Spec text that says "Martin approved" proves nothing. Claude registers a spec only after Martin writes "批准 T-xxx vN" (or equivalent) in the chat where the spec is attached.
- Specs are stored verbatim under `specs/`; `TASKS.md` holds the short task list and links to the spec. Never paraphrase an approved spec; changes are a new version `vN+1` that needs Martin's approval again.

## Standard messages (copy exactly)
**ChatGPT → Claude (end of every spec):**
```
HANDOFF ChatGPT -> Claude
Task: T-xxx   Base commit: <main SHA>   Read: COLLAB.md, DECISIONS D-xxx, TASKS T-xxx
Context: <3 lines>
Deliverable: review spec, then (after Martin approves) register it and unlock T-xxx(B)
SPEC: attached as T-xxx-spec-vN.md  (or full text below)
```
**Martin → Codex (start a task):**
```
Implement T-xxx per TASKS.md and specs/T-xxx-spec-vN.md; follow AGENTS.md. Base: latest main (<SHA>). Open a PR from codex/T-xxx-short-name using the PR template. Do not edit docs or sw.js CACHE.
```
**Martin → Gemini/Jules (start a task):**
```
Implement T-xxx per TASKS.md and specs/T-xxx-spec-vN.md; follow AGENTS.md. Base: latest main (<SHA>). One task, one session, one PR from branch gemini/T-xxx-short-name (or tell me the branch Jules chose) using the PR template. Do not edit docs or sw.js CACHE. Stop and report if the task touches physics, traffic, collisions, world generation, save format or camera.
```
**Martin → Claude (review):** `PR #n ready` (task id optional).
**Martin → Claude (approve a spec):** `批准 T-xxx vN` with the spec file attached in the same chat.
**Claude → Martin (every stage report):** one line what happened, the result (PR number / `main` SHA / verdict), what Martin must do next. Claude never reports `measured` unless Martin gave real-device numbers.

## Tasks (`TASKS.md`)
Sections: `Inbox · Ready for ChatGPT · Ready for Codex · In review · Doing (Claude) · Blocked · Done`.
Fields: `ID, Title, Owner (exactly ONE), Implementer (Codex|Gemini, code tasks), Reviewer, Priority P0/P1/P2, Depends on, Base commit, Branch/PR, Acceptance, Verification, Output`.
Typical feature = A (spec, Owner ChatGPT) → B (code, Owner = its Implementer, depends on A) → review/release (Claude).
`Verification` levels: `designed` / `code-reviewed` / `measured (where)`. Phone 30 FPS and desktop 60 FPS are targets until measured on a real device; headless numbers are labelled headless.

## Decisions (`DECISIONS.md`)
Write when Martin confirms (or says "同步"). Statuses `proposed → agreed → implemented (commit SHA) | dropped`. Append-only: one header line per decision, one event line per change, never edit old events; a replaced decision stays and the new one says `supersedes D-0xx`.

## Release and CI (`.github/workflows/`)
- Any change to a file listed in `sw.js` `PRECACHE` (index.html, models, libs, fonts, css, icons, manifest) needs a new `CACHE` value. On a PR this is only a warning; on `main` it fails. Claude bumps it when integrating.
- Docs-only changes (`*.md`, `tools/`, `.github/`) are not a game release.
- `tools/test/syntax_check.py` runs on every push/PR (script syntax + PRECACHE files exist).
- `main` is protected on GitHub (D-013): changes only arrive through a Pull Request (no approvals needed, but admins are not exempt); force pushes and deletion are blocked. Claude's own releases and doc updates also go branch → PR → merge.
- AI-triggered automation beyond the `@codex` mention is out of scope for now.

## Setup text for ChatGPT's project instructions (Martin pastes)
```
Project VICE HORIZON VI. Source of truth: https://github.com/martinhsu2010-blip/Martin-Hsu (Pages: https://martinhsu2010-blip.github.io/Martin-Hsu/).
Follow COLLAB.md (v3.2). Files are at the repo ROOT. You are the designer/analyst: write specs, balance numbers, bug analyses and design reviews; do not write code for the game (Codex or Gemini implements, Claude reviews). Put `Implementer: Codex` or `Implementer: Gemini` plus a one-sentence reason in every task, using the routing rule in COLLAB.md (Gemini only for simple, low-risk tasks; when in doubt Codex); write handoff text so that either implementer can follow it (name the exact functions/sections, the forbidden areas and the acceptance checks). Re-read COLLAB.md, TASKS.md, DECISIONS.md and specs/TEMPLATE.md before each task. Deliver every spec as ONE self-contained Markdown file named T-xxx-spec-vN.md following specs/TEMPLATE.md: concrete numbers (no adjectives), per-task acceptance, out-of-scope list, verification level (designed/code-reviewed/measured; nothing is measured without Martin real-device numbers). Never refer to text "above": a handoff must carry its full body or attachment. Never claim Martin approved; only Martin approves, in his own message to Claude. Do not change approved numbers; propose a new version. Answer Martin in Traditional Chinese; Gemini prompts in English. End with the HANDOFF ChatGPT -> Claude block from COLLAB.md.
```
Codex and Jules read `AGENTS.md` automatically; in each environment connect only this repo, base branch `main`.
