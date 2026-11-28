# T-018A2 - Device Frame-Time Diagnostics (spec v1.1, entry point)

Supersedes `specs/T-018A2-spec-v1.0.md` as the text Codex implements (D-070). Scope, risk (HIGH/SMALL), implementer (Codex), `index.html` ceiling (<= 250 added+changed lines), file allowlist and test ceiling (<= 700 lines combined) are exactly as approved in D-069; nothing is widened.

Precedence (highest first):
1. `specs/T-018A2-g0-followup-v1.1.md` conditions **A2-C14..C17**.
2. `specs/T-018A2-g0-review-v1.0.md` conditions A2-C1..C13 (where v1.1 is silent or less strict).
3. `specs/T-018A2-draft-v1.1-chatgpt.md` (verbatim ChatGPT v1.1; its status lines "PR #136 OPEN", "not approved" and its sections 17, 19, 25, 32 describing pending decisions are superseded by D-068/D-069/D-070).
4. `specs/WE-03-budget-governance-v1.0.md`, `specs/WE-03-series-spec-v1.0.md`, D-065.
Older drafts (`T-018A2-draft-v1.0-chatgpt.md`) are history only.

Summary of the added conditions:
- A2-C14: B4 is measured and reported in A2 but does not block A2 acceptance; it blocks streaming implementation and F2.
- A2-C15: snapshot records start/end `timeOfDay` and player x/z per segment; device results are grouped by observed day/night with drift flagged; no game time control is added; `teleportTo()` triggers a segment interruption only when the diag object exists.
- A2-C16: Codex proves the 4-line HUD fits in a phone-landscape Playwright screenshot (viewport recorded) with all B4 fields and preset/fpsCap/CACHE/release, without covering driving view or touch controls; otherwise STOP.
- A2-C17: resource-delta events are logged at the frame that produced them (with that frame's CPU) and completed with the next interval; mean sampling self-time is in the snapshot; the 10,000-call batch runs only in the test harness; test line count estimate reported at about 500 lines, STOP if above 700.

Registration unchanged: base `origin/main` is confirmed at Codex start; one active code PR; T-018B and later, budget values, streaming and WE-04..WE-09 not authorized.
