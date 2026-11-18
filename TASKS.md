# Task board (rules: COLLAB.md v3). One Owner per task. One active code PR at a time.

## Ready for ChatGPT
(none)

## Ready for Codex
### T-001B Economy implementation
Owner: Codex
Reviewer: Claude
Priority: P1
Depends on: T-001A
Base commit: Latest `main` after approved documentation is merged
Branch/PR: `codex/T-001B-economy` / pending
Output: Minimal implementation PR following the complete approved T-001A specification above.

Acceptance:

1. Apply all approved reward and time formulas.
2. Preserve existing car prices, six depots and game features.
3. Implement ramp, airtime, mission and police reward cooldowns.
4. Prevent duplicate rewards and fast-travel delivery shortcuts.
5. Preserve all existing save fields and owned cars.
6. Persist new crate and cooldown information safely.
7. Pass `python3 tools/test/syntax_check.py`.
8. Report actual automated/headless checks without claiming unperformed real-device testing.
9. Claude reviews correctness, regressions, mobile effects, and save compatibility.
10. Martin performs final gameplay acceptance.

Verification: Implementation not started; pending Codex PR and Claude review.

**Reviewer notes (Claude, after reading the current code; these clarify how the approved spec meets the existing game and change NO approved value. Codex follows them unless Martin objects):**

1. *An airtime reward already exists* (`this.airTime * 500`, no cap, min 0.65 s, 10 s guard after a ramp). Replace it with the approved formula. Do not add a second payout path.
2. *Crates already exist* (15, HUD `n/15`) and pay $1,000 per pickup, reset every session. Change to $400, once per save via `collectedCrates`. In an old save the field is missing, so all 15 can be collected once more; this is accepted by the spec (old collections are not reconstructed).
3. *Existing payouts to replace:* police escape currently pays $2,000 (spec: $600, 600 s cooldown); arrest fine is already −$300 (keep); missions pay through `finishMission(reward)`, so the three mission types need an id each. If the game has a mission type the spec does not list, leave its payout unchanged and say so in the PR.
4. *Cooldowns must survive a reload.* `STATE.time` restarts at 0 on load, so store cooldown expiry as wall-clock time (`Date.now()`) in `rewardCooldowns`; the UI shows the remaining seconds. Treat a missing or non-numeric value as "no cooldown".
5. *Starting cash is already $3,500* (new saves only); do not touch existing saves' cash.
6. Spec arithmetic was checked: the delivery table and both progression scenarios add up. Half-dollar cases (for example 365 → $370) round up, as in `Math.round`.

## In review
(none)

## Doing (Claude)
(none)

## Blocked
### T-002 Verify licenses of the Porsche / Lexus / Ford Sketchfab models
Owner: Martin
Priority: P2
Why: archives had no license text; needed before any public sharing.

## Inbox
(none)

## Done
- T-000 Collaboration docs created and migrated to COLLAB v2 (2026-11-18)

### T-001A Economy balance spec
Owner: ChatGPT
Reviewer: Claude
Priority: P1
Depends on: —
Base commit: `265b61289f7ce9edb8c105bb8fc1939365289aa8`
Branch/PR: Not applicable to design
Verification: `designed` — source code reviewed, Martin approved 2026-11-18. No human playtest or performance measurement completed.
Output: Approved Economy Balance Specification v1.0, reproduced below.

**Approved specification**

**A. Starting economy and progression**

- Starting cash: $3,500.
- Lexus LC 500: $18,000.
- Porsche 911: $25,000.
- Default Ferrari remains free.
- Engine upgrades remain $1,000 per level.
- First Lexus purchase target: 20–35 minutes of mixed gameplay.
- Porsche purchase target: 55–90 minutes cumulative gameplay, assuming Lexus was bought first.

**B. Delivery jobs**

Keep all six depots, existing pickup and delivery conditions, and destination range of 320–1,500 metres.

- BaseReward = roundTo10(350 + Distance × 1.2)
- TimeLimit = round(75 + Distance / 9) seconds
- Early delivery (remaining time >35% of initial limit): 1.20× base
- On-time delivery: 1.00× base
- Late delivery: 0.50× base
- Round final payment to nearest $10.
- No automatic expiration for late deliveries.
- Disable fast travel during an active delivery.
- Distance refers to straight-line distance; no route-finding algorithm is required in this release.

| Distance | Base | Limit | Early | Late |
|---|---:|---:|---:|---:|
| 320 m | $730 | 111 s | $880 | $370 |
| 900 m | $1,430 | 175 s | $1,720 | $720 |
| 1,500 m | $2,150 | 242 s | $2,580 | $1,080 |

**C. Stunt jumps**

- First successful completion of each unique ramp: $900.
- Seven unique ramps; total initial-completion reward: $6,300.
- Repeat reward = min(450, 180 + 10 × round(Distance / 20)).
- Same ramp: maximum one repeat payout every 120 seconds.
- Repeat ramps and generic airtime rewards share a 90-second global payout cooldown.
- First-time ramp completion is exempt from repeat-reward cooldown restrictions.
- One jump must not pay both ramp and generic airtime rewards.

**D. Generic airtime rewards**

- Reward = min(400, round(AirTime × 150)).
- Minimum qualifying airtime: 0.65 seconds.
- Require genuine airborne and landing detection using `raycastResult.hasHit`.
- Maximum payout: $400 per landing.
- Shared 90-second global cooldown with repeat ramp rewards.
- Do not use cannon-es `isInContact`.

**E. Other income sources**

| Source | Approved payment |
|---|---:|
| Collectible crate | $400 |
| Race mission | $1,400 |
| Drift mission | $1,200 |
| Airport stunt mission | $1,600 |
| Successful police escape | $600 |
| Arrest fine | -$300 |

- Fifteen collectible crates, collectible once per save.
- Each mission type has its own 300-second payout cooldown.
- Police escape payout cooldown: 600 seconds.
- Replaying a mission during cooldown remains allowed without an additional payout.
- Cooldown information must be understandable in the UI.
- Cooldowns must remain effective after reloading the game.

**F. Save compatibility**

Preserve `localStorage` key `vh_save` and all existing fields: `cash`, `owned`, `jumps`, `deliveries`, `upgrade`.

Add compatible fields with safe defaults:

- `collectedCrates`
- `rewardCooldowns`

Do not reset current cash, owned cars, jump progress, deliveries or upgrades. Older saves lack crate history; initialize new tracking safely without claiming old collections can be reconstructed.

**G. Progression reference scenarios (design estimates)**

First purchase:

- 7 normal 900 m deliveries: $10,010
- 3 first-time ramps: $2,700
- 2 crates: $800
- 1 race: $1,400
- Total earned: $14,910
- Starting cash + earnings: $18,410
- Lexus purchase leaves $410.

Second purchase after Lexus:

- 12 normal 900 m deliveries: $17,160
- 4 first-time ramps: $3,600
- Airport stunt: $1,600
- Drift mission: $1,200
- 2 crates: $800
- Police escape: $600
- Total earned: $24,960
- With $410 balance: $25,370
- Porsche purchase leaves $370.

These are planning calculations, not measured gameplay results.
