# T-018A1 findings, limits and open items (hand-written, WE-03A) - revision 1.1

Author: Claude. Status: ChatGPT read-only review of revision 0 returned REVISE (R01-R06); revision 1 answered it; the re-review returned REVISE with four minor corrections (R1-F01..F04), answered in revision 1.1 (section 1b). Submitted for re-review. Martin has not accepted. A1 approves no budget and does not authorize A2 or any later subtask. No game file, `sw.js`, CACHE, `vh_save`, or WE-01/WE-02 artifact or verdict was changed.

Source classes: MEASURED_HEADLESS, ANALYTIC_ESTIMATE, PROPOSED_LIMIT, PENDING_DEVICE, SOURCE_CONFIRMED, INCONCLUSIVE. Headless numbers are CPU submission time of `animate()` under SwiftShader; they are not device FPS and not VRAM.

**Two statuses are kept apart.** Artifact validation (the independent check) is PASS: structure, provenance, labels, re-derived analytics, 33/33 negative controls red. Measurement validity is INCONCLUSIVE for: physics self-control on all four presets, frame time as a hard gate, B3 density testing, and the headless stall in TABLET_MED/CBD. PASS on the first does not upgrade the second.

## 1. Corrections made for the review (R01-R06)

| id | what changed | where |
|---|---|---|
| R01 | Each pair now uses two fresh Chrome sessions (one per side), order alternating, both sides' bodies, shapes, readiness (`__phDone`) and load time recorded. The first run (two pages reused for five pairs) is kept unchanged as `physics_pairs_v1_reused_pages`. | `we03_baseline.py`, `baseline_metrics.json` |
| R02 | New validators: physics methodology and status-from-band, reset inventory completeness, beach/nesting/fallback classification, independent shadow estimate and replay P95, benefit by radius, strict budget label classes, exact budget preset set. 18 new negative controls (33 total), including the physics step protocol (900 warm-up + 360 recorded, `physicsWorld.step(1/60,1/60,3)`) and a sha256 pin proving the retained revision-0 evidence is identical to PR #132. | `we03_calibration_check.py` |
| R03 | Triangle metric reconciled: single-pass cone/omni columns exclude the shadow pass; `cone96_peak_viewpoint_plus_shadow_estimate` and `p95_incl_shadow` add it and are the only analytic values comparable with measured all-pass triangles. Limitations recorded (no fog, occlusion, height). | `calibration_data.json`, `calibration_report.md` |
| R04 | Fallback objects classified GLOBAL_STRESS_ONLY; B3 density test marked INCONCLUSIVE; scope exception left PENDING_MARTIN_APPROVAL. WE-01 land constraints were not relaxed. | `fixture_plan.json` |
| R05 | PHONE_MED budget row added. The draft has no PHONE_MED row, so every value is the midpoint of the draft PHONE_LOW and TABLET_MED rows, labelled PROPOSED_LIMIT and INTERPOLATED; nothing is approved. | `proposed_budgets.json` |
| R06 | Collision-body saving recomputed by radius (140/180/217/260/350 m) with the peak-grid maximum and the replay-path P95 reported separately. | `calibration_data.json` benefit |

## 1b. Re-review corrections (R1-F01..F04)

- **R1-F01:** the check now validates `warmup_steps`, `recorded_steps` and `step` against the approved protocol, and compares the retained revision-0 physics evidence with a pinned sha256 of the PR #132 data (verified identical to `c1c57c1`), not only its presence.
- **R1-F02:** the field is renamed `cone96_peak_viewpoint_plus_shadow_estimate` (budget key `analytic_cone96_peak_plus_shadow_triangles`). It is the shadow extra evaluated at the cone96 peak viewpoint, not a global maximum of the sum. Wording that called analytic counts an upper bound was removed for the sampled centre-point model; only the omnidirectional column keeps the name `omni_resident_upper_bound` because A1-C1 requires that label, and it too is a sampled 20 m viewpoint model, not a strict bound.
- **R1-F03:** section 6 is rewritten (A2 diagnostics only; ownership of LOD validation, radius selection and shader prewarming moved).
- **R1-F04:** section 3 now says the Ch03_Body link attribution is strongly supported by the CDP evidence but the deferred-link mechanism is not directly proven.

## 2. Results and what they mean

1. **Physics self-control (R01, fresh sessions): INCONCLUSIVE on all four presets.** Ratio ranges: PHONE_LOW 0.887-1.124, PHONE_MED 1.014-1.167, TABLET_MED 0.869-1.091, DESKTOP_HIGH 0.865-1.047 against the band 0.909-1.100. Bodies and shapes were identical on both sides of every pair. In the first (reused-page) run PHONE_MED and DESKTOP_HIGH looked STABLE; that was an artifact of reusing two pages and is now withdrawn as evidence. No physics-timing regression claim can be made from headless data. A2 should compare deterministic counts (bodies, shapes, contacts per step) rather than step time.
2. **Triangles (R03).** Analytic cone96 peak viewpoint plus shadow estimate (shadow extra evaluated at the cone96 peak viewpoint; not a global maximum of the sum) versus the provisional triangle budget: PHONE_LOW 138,000 vs 120,000; PHONE_MED 175,000 vs 160,000 (interpolated); TABLET_MED 167,000 vs 200,000; DESKTOP_HIGH 250,000 vs 350,000. Replay P95 including shadow: 133,000 / 189,000 / 193,000 / 246,700. PHONE_LOW and PHONE_MED exceed their provisional budget on the analytic estimate. These are sampled centre-point estimates without fog (LOD2 transmittance at the far edge is only 0.22-0.35), occlusion or camera height, not strict bounds, so they are **not a demonstrated P95 failure and not a validation**; it shows possible budget pressure to be measured later on the real LOD implementation (owned by C4/F2, not A2). Status: INCONCLUSIVE.
3. **B3 (R04).** Of the three extra buildings A1-C9 asks for in B3, two (R01 and R05) fit on free WE-01 land; the R08 extra (38 x 24 m) does not and sits in B1. Across the 63 synthetic buildings, 16 sit outside their intended region and are GLOBAL_STRESS_ONLY, 6 are B3_DENSITY and 41 are REGION_DENSITY. B3 is saturated, and B3-specific density testing with the full three extras is INCONCLUSIVE. This differs from the approved C9 text, so it needs Martin's decision (section 5).
4. **Streaming benefit (R06).** Geometry and shared-atlas savings are about 0 under four shared prototypes (honest analytic finding). The collision-body saving depends on the radius and on the metric. For 57 buildings, 1 body per building: peak-grid saving 68.4 / 66.7 / 56.1 / 56.1 / 56.1 % at 140 / 180 / 217 / 260 / 350 m; replay-path P95 saving 77.2 / 71.9 / 66.7 / 56.1 / 56.1 %. The earlier "about 56 %" is the peak-grid value at 217 m, not a replay P95. All ANALYTIC_ESTIMATE.
5. **Speed ceilings and hysteresis.** Code-derived ceilings 81.94 / 113.08 / 121.28 / 167.36 m/s (base, nitro, max upgrade, both; ANALYTIC_ESTIMATE, force limits only). Measured peaks stay below them. At those speeds one 250 ms update moves more than the PHONE_LOW LOD0 hysteresis band of 20 m, so a skip is possible; correctness belongs to C4.
6. **Frame time is not a hard gate.** Repeat P50 ratio range 0.694-1.190. Draw calls and triangles were identical in every repeat and are the deterministic metrics.
7. **Stalls recorded, not deleted.** TABLET_MED/CBD shows 12.8 s and 28.6 s frames; DESKTOP_HIGH/Suburbs shows one 6.1 s frame.
8. **PHONE_LOW resource estimates vary** between scenes (texture 33.4-49.4 MiB) while the other presets are constant. Likely asynchronous load; still unverified.

## 3. Stall attribution (MEASURED_HEADLESS, `stall_probe`)

The first counter-only probe (kept as `stall_probe_v1_counters`) saw a 25 s frame at probe frame 114 with no new program, texture or geometry, so it did not support the first-use compile hypothesis. The rerun adds new program names and a CDP sampling profile:

- TABLET_MED/CBD 12:00: a 31.8 s frame at frame 100 coincides with one new program, `Ch03_Body` (MeshPhysicalMaterial); the profile's dominant self time is `getProgramInfoLog` (35.5 s).
- TABLET_MED/CBD 23:00: the stall is at frame 114 with no new program in that frame; the dominant self time is `uniformMatrix4fv` (29.5 s), the first call that has to wait for a deferred program link. The program was created at frame 100 (+1 program, 40 ms), so this fits a deferred link.
- DESKTOP_HIGH/Suburbs and PHONE_MED/CBD showed no stall in this rerun, so the 6.1 s Suburbs frame is not reproduced and stays unexplained.

Conclusion: the multi-second TABLET_MED/CBD stall is strongly supported by the CDP evidence as the first-use link of the `Ch03_Body` shader program under software GL. The deferred-link mechanism that explains the 14-frame offset between creation and stall (12:00 versus 23:00 runs) is consistent with the profile but not directly proven, so the attribution is qualified, not confirmed. Whether a real GPU shows any stall is PENDING_DEVICE; no GC or GPU-timer attribution is available headless and none is claimed.

## 4. Tool sizes (A1-C4 ceilings 600 / 500 / 400 lines)

`we03_baseline.py` 456, `we03_calibration.py` 499, `we03_calibration_check.py` **446**. The check exceeds its 400-line ceiling by 46 lines because R02 and R1-F01 asked for more validators and controls; two helper functions in the generator were compacted to stay at 499. This needs Martin's decision (section 5).

## 5. Decisions needed from Martin (not taken by Claude)

1. B3 scope exception: accept GLOBAL_STRESS_ONLY for the one 60-set extra that fell back to B1 (and the 15 other fallbacks in the 120 set) and B3 density as INCONCLUSIVE, or require a different B3 source without relaxing WE-01 land constraints.
2. Check ceiling: raise `we03_calibration_check.py` from 400 to 450 lines (ChatGPT recommends 450 if no important validation is deleted), or have Claude cut 46 lines of validators or controls.

## 6. Diagnostics for A2 (if A2 is later registered and approved; diagnostics only, 250-line ceiling)

A2 is a diagnostics tool and does not change production behaviour. Within that boundary it must provide:

1. Frame intervals and longest-frame evidence with feasible attribution (program creation, texture upload, physics step, draw); GC and GPU timers marked unavailable where the browser does not expose them.
2. Cold-frame evidence preserved separately from warmed frames. Shader prewarming is part of the test procedure only (a separate warmed series), never a new production behaviour, and the cold series is not deleted.
3. Deterministic physics counts (bodies, shapes, contacts) next to step-time, because step-time ratios were INCONCLUSIVE.

Owned elsewhere, not by A2: validating actual LOD triangle counts against the analytic estimates (C4/F2); choosing the active collision radius and its safety (D/E1); prototype resource residency (C1); real hysteresis correctness (C4); collision readiness (D); predictive scheduling (E1).

## 7. Commands run

```
python3 tools/we03/we03_baseline.py --phase physics --presets <preset>   # fresh sessions, resumable; run per preset
python3 tools/we03/we03_baseline.py --phase stall                        # counters, program names, CDP sampling profile
python3 tools/we03/we03_calibration.py
python3 tools/we03/we03_calibration_check.py                             # CI uses --skip-git
```

Earlier phases (presets, render, repeat, speed, terrain) are unchanged from revision 0.

## 8. Tool-hash history note

The first three speed runs used an earlier revision of `we03_baseline.py` (PHONE_LOW only, before the nitro and ceiling fixes). `baseline_metrics.json` lists every tool hash; those PHONE_LOW speed values were re-verified against the ceiling check and are unaffected. The physics and stall phases of this revision ran with the revision-1 tool hash.

## 9. Review limits

Static re-review by ChatGPT will not re-run the browser. The independent check re-derives analytics from `index.html`, WE-02 and WE-01 inputs, but the headless measurements themselves are not independently reproducible bit-for-bit (2 vCPU shared host).
