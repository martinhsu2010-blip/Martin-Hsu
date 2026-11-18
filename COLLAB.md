# COLLAB v3 — ChatGPT × Codex × Claude protocol (VICE HORIZON VI)

v3 adopted 2026-11-18 (D-011). Martin relays between the AIs. **This GitHub repo is the single source of truth.** No AI can see another's private chat; only what is written in the repo or on GitHub is shared.

## Roles
- **ChatGPT (designer/analyst)**: feature design, economy balance, bug analysis, task specs, design review. Writes specs, not code.
- **Codex (implementer)**: implements ONE approved task from its spec, runs checks, pushes a `codex/T-xxx-name` branch and opens a Pull Request. Never touches `main`, `sw.js` CACHE or the docs. Rules in `AGENTS.md`.
- **Claude (reviewer, integrator, releaser, brainstorm partner)**: fetches each PR from GitHub, reviews, runs the game in a headless browser, comments, merges, resolves conflicts, bumps `CACHE`, releases, updates TASKS/DECISIONS/LOG/HANDOFF. Small defects Claude fixes itself and says so; larger ones go back to Codex.
- **Martin**: requirements, priorities, final acceptance. Starts Codex tasks and tells Claude when a PR is ready. Only Martin/Claude merge; nobody merges from inside Codex.

## Files (repo root is the only official location; ignore any old `records/` path)
`COLLAB.md` this protocol · `AGENTS.md` rules for Codex · `HANDOFF.md` how the project works · `TASKS.md` board · `DECISIONS.md` register · `LOG.md` releases · `tools/` scripts · `.github/` CI + PR template.
Re-read at the start of each session: `https://martinhsu2010-blip.github.io/Martin-Hsu/<FILE>` (Pages refreshes ~2 min after a push; Claude reads GitHub directly).

## Feature flow
1. **Idea** → `Inbox` (anyone; Claude's brainstorm ideas go here as `proposed`).
2. **Spec** (ChatGPT) → Martin approves → decision `agreed`, task moves to `Ready for Codex`.
3. **Implement**: Martin starts a Codex task: "Implement T-xxx per TASKS.md and DECISIONS D-xxx; follow AGENTS.md." Codex opens a PR from `codex/T-xxx-name` using the PR template.
4. **Review**: Martin tells Claude "PR #n ready". Claude fetches the branch, reviews (correctness, regressions, mobile performance, save compatibility, scope, licenses), runs the game test, and posts a GitHub review with a verdict: `approved` / `changes-requested` (numbered) / `rejected` (reason).
5. **Fix loop**: on `changes-requested`, Claude's PR comment may mention `@codex` to start the fix task (max 2 rounds, then Martin decides). If Codex cannot be triggered from the comment, Martin starts it.
6. **Integrate**: on `approved`, Claude merges (squash), resolves conflicts, bumps `CACHE`, verifies live, appends decision events with the commit SHA, updates TASKS/LOG/HANDOFF.
7. **Accept**: Martin plays the release; task is `Done` only with evidence in `Verification`.

Rules: **one active code PR at a time** (the game is one 8,300-line file). The branch must start from the latest `main`; the author rebases when `main` moves.

## Tasks (`TASKS.md`)
Sections: `Inbox · Ready for ChatGPT · Ready for Codex · In review · Doing (Claude) · Blocked · Done`.
Fields: `ID, Title, Owner (exactly ONE), Reviewer, Priority P0/P1/P2, Depends on, Base commit, Branch/PR, Acceptance, Verification, Output`.
Typical feature = A (spec, Owner ChatGPT) → B (code, Owner Codex, depends on A) → review/release (Claude).
`Verification` levels: `designed` / `code-reviewed` / `measured (where)`. Phone 30 FPS and desktop 60 FPS are targets until measured on a real device; headless numbers are labelled headless.

## Decisions (`DECISIONS.md`)
Write when Martin confirms (or says "同步"). Statuses `proposed → agreed → implemented (commit SHA) | dropped`. Append-only: one header line per decision, one event line per change, never edit old events; a replaced decision stays and the new one says `supersedes D-0xx`.

## Handoff block (paste between AIs / into Codex)
```
HANDOFF -> <ChatGPT|Codex|Claude>
Task: T-xxx   Base commit: <sha>   Read: AGENTS.md, DECISIONS D-xxx, TASKS T-xxx
Context: <3 lines>   Deliverable: <exact output>   Acceptance: <list>
```

## Release and CI (`.github/workflows/`)
- Any change to a file listed in `sw.js` `PRECACHE` (index.html, models, libs, fonts, css, icons, manifest) needs a new `CACHE` value. On a PR this is only a warning; on `main` it fails. Claude bumps it when integrating.
- Docs-only changes (`*.md`, `tools/`, `.github/`) are not a game release.
- `tools/test/syntax_check.py` runs on every push/PR (script syntax + PRECACHE files exist).
- `main` is protected on GitHub (D-013): changes only arrive through a Pull Request (no approvals needed, but admins are not exempt); force pushes and deletion are blocked. Claude's own releases and doc updates also go branch → PR → merge.
- AI-triggered automation beyond the `@codex` mention is out of scope for now.

## Setup text for ChatGPT's project instructions (Martin pastes)
```
Project VICE HORIZON VI. Source of truth: https://github.com/martinhsu2010-blip/Martin-Hsu (Pages: https://martinhsu2010-blip.github.io/Martin-Hsu/).
Follow COLLAB.md (v3). Files are at the repo ROOT. You are the designer/analyst: write specs, balance numbers, bug analyses and design reviews as TASKS.md-ready text; do not write code for the game (Codex implements, Claude reviews). Re-read COLLAB.md, TASKS.md, DECISIONS.md before each task. Answer Martin in Traditional Chinese; Gemini prompts in English. End handoffs with the HANDOFF -> block.
```
Codex reads `AGENTS.md` automatically; in the Codex environment connect only this repo, base branch `main`.
