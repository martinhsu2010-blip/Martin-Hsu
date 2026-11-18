# COLLAB v2 — Claude × ChatGPT protocol (VICE HORIZON VI)

Adopted 2026-11-18 (agreed by Martin, reviewed by ChatGPT). The owner (Martin) relays between the AIs. **This GitHub repo is the single source of truth.** Neither AI can see the other's private chat; only what is written here is shared.

## Roles (updated 2026-11-18, D-010: ChatGPT writes the code, Claude reviews)
- **ChatGPT (author)**: designs and writes the code for features and fixes (GPT-6 Astra). Delivers a unified diff against a stated base commit plus a short design note. Does not overwrite `index.html` directly.
- **Claude (reviewer, tester, release gate, brainstorm partner)**: reviews every diff, applies it in the sandbox, runs the game in a headless browser, checks performance impact, sends back findings, and only then commits, bumps `CACHE`, pushes `main` and releases. Also proposes ideas and critiques designs. Claude fixes small defects found in review itself (and says so); anything larger goes back to ChatGPT.
- **Martin**: final decisions, acceptance, priorities, and relaying between the two chats.
- Why Claude still pushes: ChatGPT cannot push to GitHub or run the game; Claude has the sandbox and the deploy path.

## Feature flow
1. Idea → `Inbox` (either AI can propose; Claude's brainstorm notes go here as `proposed`).
2. Martin approves → ChatGPT designs and writes the diff (`Ready for ChatGPT` → output).
3. Martin pastes the HANDOFF block + diff to Claude → `Ready for Claude`: review.
4. Claude replies with a verdict: `approved` / `changes-requested` (numbered findings) / `rejected` (reason). Reviews check: correctness, regressions in existing systems, mobile performance (draw calls, physics cost, memory), save-file compatibility, security, asset licenses.
5. On `approved`: Claude applies, tests, releases, logs version + commit SHA. On `changes-requested`: Martin returns the findings to ChatGPT, loop to step 2.
6. A task is `Done` only with evidence in `Verification`.

## Files (repo root is the only official location; ignore any old `records/` path)
`HANDOFF.md` how the project works · `TASKS.md` task board · `DECISIONS.md` decision register · `LOG.md` releases · `tools/` archived scripts. Both AIs re-read the relevant files at the start of every session:
`https://martinhsu2010-blip.github.io/Martin-Hsu/<FILE>` (Pages refreshes ~2 min after a push).

## Decisions (`DECISIONS.md`)
- Write a decision when Martin confirms it (or says "同步"), not at session end.
- Statuses: `proposed` → `agreed` (confirmed, not coded) → `implemented` (in code, with commit SHA) or `dropped`.
- **Append-only history.** Each decision has a header line plus one event line per status change: `D-012 | 2026-12-01 | agreed | by Martin`, later `D-012 | 2026-12-05 | implemented | commit abc1234`. Never edit or delete old event lines; the latest event is the current state. A replaced decision stays and the new one says `supersedes D-0xx`.

## Tasks (`TASKS.md`)
- Sections: `Inbox · Ready for ChatGPT · Ready for Claude · Doing · Blocked · Done`.
- Fields: `ID, Title, Owner (exactly ONE), Reviewer, Priority P0/P1/P2, Depends on, Base commit, Acceptance, Verification, Output`.
- Normal feature task: Owner ChatGPT (design + diff), then Owner Claude (review/test/release). Add a `Reviewer:` line. Work can still be split A (design/spec) and B (diff) when large.
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
