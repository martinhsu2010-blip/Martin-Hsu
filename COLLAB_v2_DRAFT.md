# COLLAB v2 (DRAFT — becomes COLLAB.md once Martin approves)

Response to ChatGPT's proposal. Positions: Q1 agree, Q2 agree, Q3 not now.

## Files (all at repo root — this is the only official location; any `records/` path in older instructions is obsolete)
`HANDOFF.md` how the project works · `TASKS.md` task board · `DECISIONS.md` decision register · `LOG.md` releases · `tools/` archived scripts

## 1. Decisions are written when Martin confirms, not at session end
- Statuses: `proposed` (discussed) → `agreed` (Martin confirmed, not coded) → `implemented` (in code, with commit SHA) or `dropped`.
- Never delete history. A replaced decision stays; the new one says `supersedes D-0xx`.
- Fallback trigger: Martin says "同步" and Claude writes everything pending.

## 2. Tasks: one current owner, two handoff lanes
`TASKS.md` sections: `Inbox` · `Ready for ChatGPT` · `Ready for Claude` · `Doing` · `Blocked` · `Done`.
Task fields: `ID, Title, Owner (exactly one), Priority P0/P1/P2, Depends on, Base commit, Acceptance, Verification, Output`.
- Work that needs both AIs is split into A (design/spec, ChatGPT) and B (implement, Claude, depends on A). Example: T-001A economy spec → T-001B implementation.
- `Verification` must say what was actually checked and what was not. Use three levels: `designed` (intended), `code-reviewed`, `measured` (with where: headless browser vs real device). Phone 30 FPS / desktop 60 FPS are targets until measured on a real device; Claude's headless numbers are `measured (headless, not a phone)`.

## 3. Handoff messages
When work moves to the other AI, the sender ends with a standard block Martin can paste:
```
HANDOFF -> <ChatGPT|Claude>
Task: T-xxx   Base commit: <sha>   Read: DECISIONS D-xxx, TASKS T-xxx
Context: <3 lines>   Deliverable: <exact output>   Acceptance: <list>
```
The receiver replies with the same shape (`HANDOFF ->` back), plus patch/diff/design text. Martin pastes it back; Claude commits it.

## 4. Code safety
- Only Claude (or Martin) writes to `main`. ChatGPT sends patches/diffs/reviews, never overwrites `index.html`.
- Large features go on a `feature/<name>` branch and merge after verification. (GitHub Pages serves `main` only, so branches are not live.)
- Every release records game version + commit SHA in `LOG.md`.
- Completion claims need evidence in `Verification`.

## 5. Q3 automation (GitHub Actions → AI)
Not now. An Action cannot reach either chat; it would need API keys, a hosted coordinator and cost, and an API-driven Claude loses the sandbox (headless testing, model conversion, deploy). Revisit when (a) v2 has run stably for a few weeks and (b) Martin is willing to pay for API usage.
Allowed now: plain CI checks with no AI, e.g. fail the push if `index.html` changed but `sw.js` `CACHE` did not, or if `TASKS.md` has a task with two owners.
