# COLLAB v2 — Claude × ChatGPT protocol (VICE HORIZON VI)

Adopted 2026-11-18 (agreed by Martin, reviewed by ChatGPT). The owner (Martin) relays between the AIs. **This GitHub repo is the single source of truth.** Neither AI can see the other's private chat; only what is written here is shared.

## Roles
- **Claude (builder)**: implements, tests, bumps `sw.js` `CACHE`, commits, pushes `main`, releases. Only Claude or Martin writes to `main`.
- **ChatGPT (designer/reviewer)**: system design, code review, bug analysis, performance plans, task specs. Sends patches/diffs/designs, never overwrites `index.html`.
- **Martin**: final decisions, acceptance, priorities.

## Files (repo root is the only official location; ignore any old `records/` path)
`HANDOFF.md` how the project works · `TASKS.md` task board · `DECISIONS.md` decision register · `LOG.md` releases · `tools/` archived scripts. Both AIs re-read the relevant files at the start of every session:
`https://martinhsu2010-blip.github.io/Martin-Hsu/<FILE>` (Pages refreshes ~2 min after a push).

## Decisions (`DECISIONS.md`)
- Write a decision when Martin confirms it (or says "同步"), not at session end.
- Statuses: `proposed` → `agreed` (confirmed, not coded) → `implemented` (in code, with commit SHA) or `dropped`.
- **Append-only history.** Each decision has a header line plus one event line per status change: `D-012 | 2026-12-01 | agreed | by Martin`, later `D-012 | 2026-12-05 | implemented | commit abc1234`. Never edit or delete old event lines; the latest event is the current state. A replaced decision stays and the new one says `supersedes D-0xx`.

## Tasks (`TASKS.md`)
- Sections: `Inbox · Ready for ChatGPT · Ready for Claude · Doing · Blocked · Done`.
- Fields: `ID, Title, Owner (exactly ONE), Priority P0/P1/P2, Depends on, Base commit, Acceptance, Verification, Output`.
- Work needing both AIs is split: A = design/spec (ChatGPT), B = implementation (Claude, `Depends on` A).
- `Verification` states what was actually checked, using levels `designed` / `code-reviewed` / `measured (where)`. Phone 30 FPS and desktop 60 FPS are targets until measured on a real device; headless-browser numbers are labelled as such.

## Handoff message (paste between AIs)
```
HANDOFF -> <ChatGPT|Claude>
Task: T-xxx   Base commit: <sha>   Read: DECISIONS D-xxx, TASKS T-xxx
Context: <3 lines>   Deliverable: <exact output>   Acceptance: <list>
```
Moving a task = write the decision, set the single Owner, place it in the other AI's `Ready for` lane, commit, then give Martin the block above. The receiver answers in the same shape.

## Code safety
- Big features on `feature/<name>` branches, merged to `main` after verification (Pages serves `main` only).
- Every release records game version + commit SHA in `LOG.md`.
- "Done" needs evidence in `Verification`, not just a claim.

## Release and CI
- Any change to a cached game file (everything listed in `sw.js` `PRECACHE`, including `index.html`, models, libs, fonts, css, icons, manifest) requires a new `CACHE` value in `sw.js`.
- Docs-only changes (`*.md`, `tools/`, `.github/`) do not need a bump and are not a game release.
- `.github/workflows/pwa-cache-check.yml` enforces this and fails the push otherwise.

## Automation
GitHub Actions that call AIs are out of scope for now (needs API keys, cost, a coordinator; an API Claude loses the sandbox tools). Revisit after v2 has run stably for a few weeks.

## Text for ChatGPT's project instructions (Martin pastes into the ChatGPT project)
```
Project: VICE HORIZON VI. Source of truth: https://github.com/martinhsu2010-blip/Martin-Hsu (Pages: https://martinhsu2010-blip.github.io/Martin-Hsu/).
Follow COLLAB.md. Files are at the repo ROOT (not records/): HANDOFF.md, TASKS.md, DECISIONS.md, LOG.md.
Before any task, re-read COLLAB.md, TASKS.md, DECISIONS.md. You are the designer/reviewer: send patches/diffs/specs, never overwrite index.html. Answer Martin in Traditional Chinese; Gemini prompts in English.
End handoffs with the HANDOFF -> block from COLLAB.md.
```
