# T-018A1 findings, limits and open items (hand-written, WE-03A)

Author: Claude. Status: submitted for ChatGPT read-only review; Martin has not accepted. A1 approves no budget and does not authorize A2 or any later subtask. No game file, `sw.js`, CACHE, `vh_save`, or WE-01/WE-02 artifact or verdict was changed.

Source classes used throughout: MEASURED_HEADLESS, ANALYTIC_ESTIMATE, PROPOSED_LIMIT, PENDING_DEVICE, SOURCE_CONFIRMED, INCONCLUSIVE. Headless numbers are CPU submission time of `animate()` under SwiftShader; they are not device FPS and not VRAM.

## 1. Results summary

- Baseline: 48/48 combinations (4 presets x 6 locations x 12:00/23:00, 20 warm-up + 120 recorded frames), 16/16 repeat sessions, physics self-control 5 alternating pairs per preset. Draw calls and triangles were identical in every repeat.
- Calibration: triangle model over 57 WE-02 parcels, chunk contract at 64/128/256 m, synthetic fixture plans (40/57/60/120 sites), speed ceilings, streaming-benefit analysis, device protocol, labelled proposed budgets (all PROPOSED_LIMIT or PENDING_DEVICE, none approved).
- Independent check `we03_calibration_check.py`: all gates PASS, 15/15 negative controls red, changed-file allowlist (21 paths) clean.

## 2. Findings and limitations

1. **B3 saturation.** B3 has no free rectangle in the WE-01 common-L0 cells for the synthetic 60/120 sets. Those buildings fall back to regions B1/B2 and carry an `intended_region` field. B3-specific density claims must not be drawn from the 60/120 sets.
2. **Tablet harness fix.** TABLET presets were first measured as iGPU because headless Chrome had no tablet-class screen. `open_game()` now sets a 1280x800 screen and an Android UA, and the check compares measured runtime values against the source tables (one negative control covers this). PHONE_LOW never fires `__phDone`, so facade-kit scenes there are not comparable to the other presets.
3. **Speed ceilings and hysteresis.** Code-derived ceilings: 81.94 m/s base, 113.08 with nitro, 121.28 max upgrade, 167.36 max upgrade plus nitro (ANALYTIC_ESTIMATE, force limits only). Measured peaks stay below them (checked, with a negative control). At those speeds one 250 ms update moves 20-30+ m, which exceeds the PHONE_LOW LOD0 hysteresis band of 20 m: a skip risk that A2 must diagnose, not assume away.
4. **Streaming benefit gate is structurally degenerate.** With four shared prototypes, resident geometry and atlas do not depend on building count, so geometry/texture saving from streaming is about 0 under the same LOD strategy. Collision bodies are the only large saving (about 56% under the 1-body-per-building assumption, ANALYTIC_ESTIMATE). A percentage gate on geometry or texture cannot be passed or failed meaningfully.
5. **Physics self-control.** PHONE_LOW (0.895..1.054) and TABLET_MED (0.937..1.351) are INCONCLUSIVE; PHONE_MED and DESKTOP_HIGH are STABLE. No physics regression claim can be made on those two presets from headless data.
6. **Frame time is not a hard gate.** Repeat P50 ratio range is 0.694..1.190; usable as a hard gate: False. Draw calls and triangle counts are the deterministic comparison metrics.
7. **Stalls are recorded, not deleted.** TABLET_MED/CBD shows 12.8 s and 28.6 s frames at 12:00 and 23:00 and DESKTOP_HIGH/Suburbs/12:00 shows a 6.1 s frame. They stay in `baseline_metrics.json`, which is why the P99 and max columns for those rows are huge.
8. **PHONE_LOW resource estimates vary** between scenes (texture 33.4-49.4 MiB) while other presets are constant. Likely asynchronous load timing, not verified.

## 3. Stall diagnosis (`stall_probe` in baseline_metrics.json, MEASURED_HEADLESS)

A per-frame counter run (`--phase stall`) re-ran four scenes with program, texture and geometry deltas.

- Frame 0 of every session is a 2-3 s first-render burst (57-66 programs, 54-112 textures, 91-172 geometries). That is normal first-use compile and upload under SwiftShader and sits inside warm-up.
- TABLET_MED/CBD: a small step at probe frame 100 (+1 program, +5 textures, 40-59 ms) and then a **25-27 s frame at probe frame 114 with zero new programs, textures or geometries**, reproduced at both 12:00 and 23:00.
- DESKTOP_HIGH/Suburbs and PHONE_MED/CBD did not stall in the probe, so the 6.1 s Suburbs frame was not reproduced.

Conclusion: the first-use shader/texture compile hypothesis explains frame 0 but **does not explain the 25 s stall**. Its cause is UNEXPLAINED (candidates not tested: a periodic game task, GC, a SwiftShader pass for that view). It is deterministic only for TABLET_MED/CBD. Status INCONCLUSIVE; A2 must diagnose it before any frame-time claim for that scene.

## 4. Open items and risks

- No device measurement exists. Every FPS, VRAM and thermal budget stays PENDING_DEVICE until Martin runs the device protocol on the S26 Ultra and Tab S11.
- Proposed budgets are PROPOSED_LIMIT and unapproved; Martin must confirm revised budgets after review.
- Fixture sets use synthetic sites at WE-01 common-L0 free cells, not final world content.

## 5. Diagnostics A2 must include (if A2 is later registered and approved)

1. Per-frame stall attribution (programs, textures, geometries, physics step, GC) for TABLET_MED/CBD.
2. Hysteresis check at the measured speed range against 250 ms update steps and the PHONE_LOW 20 m band.
3. Separate geometry/texture resident-set reporting per prototype so the benefit gate is meaningful.
4. Physics self-control rerun with more pairs for PHONE_LOW and TABLET_MED.
5. B3 placement with a larger free-cell source or an explicit exclusion.

## 6. Commands run

```
python3 tools/we03/we03_baseline.py --phase all   # presets, render, repeat, physics, speed, terrain, stall (resumable)
python3 tools/we03/we03_calibration.py
python3 tools/we03/we03_calibration_check.py      # CI uses --skip-git
```

## 7. Tool-hash history note

The first three speed runs used an earlier revision of `we03_baseline.py` (PHONE_LOW only, before the nitro and ceiling fixes). The environment history in `baseline_metrics.json` lists every tool hash; the PHONE_LOW speed values were re-verified against the ceiling check and are unaffected.
