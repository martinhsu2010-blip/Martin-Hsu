## Task
Task ID: T-xxx   (one PR = one task; branch name `codex/T-xxx-short-name` or `gemini/T-xxx-short-name`; implementer: Codex | Gemini)
Base commit (main SHA this branch started from):

## What changed and why
<!-- 3-6 lines. Link the DECISIONS entry (D-xxx) this implements. -->

## Verification (be honest: say what was NOT checked)
- [ ] `python3 tools/test/syntax_check.py` passes
- [ ] Ran / read the affected code paths (describe)
- Not verified: <!-- e.g. real-phone FPS, offline mode, existing save files -->

## Risk checklist
- [ ] Did not touch `sw.js` CACHE (the maintainer bumps it)
- [ ] No new binary assets (models/textures); asset needs are listed below instead
- [ ] Existing `vh_save` saves still load
- [ ] Mobile performance impact noted (draw calls / physics cost / memory)
- [ ] Only files needed for this task were changed

## Notes for the reviewer (Claude)
