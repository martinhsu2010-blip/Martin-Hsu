# Decisions (append-only; newest at the bottom)

Claude updates this at the end of every working session, including decisions that were discussed but **not yet implemented**. Keep it free of secrets and personal info (the repo is public).
Format: `D-NNN | date | status (agreed/implemented/dropped) | decision | why`

D-001 | 2026-11 | implemented | Game is a single-file `index.html` PWA on GitHub Pages, all assets vendored locally | offline play, easy hosting, no build step
D-002 | 2026-11 | implemented | New cars are loaded from GLB files via a `CAR_MODELS` registry; physics wheels are laid out from the model's wheel nodes | lets any converted model drop in
D-003 | 2026-11 | implemented | Ford Shelby GT500 is the police car; Porsche 911 ($25,000) and Lexus LC 500 ($18,000) must be bought with in-game cash | owner request
D-004 | 2026-11 | implemented | Income comes from delivery jobs (random destination, no physical cargo) and daily stunt jumps | owner request
D-005 | 2026-11 | implemented | NPC traffic uses low-poly Kenney cars, density ~50% higher, with distance-based recycling and physics freezing | performance on phones
D-006 | 2026-11 | implemented | Progress (cash, owned cars, jumps) is saved in localStorage `vh_save` | no backend needed
D-007 | 2026-11-18 | agreed | Claude↔ChatGPT collaboration runs through the public repo files (HANDOFF/TASKS/DECISIONS/LOG); only the builder pushes to `main` | cheap, works from phone, no API keys
D-008 | 2026-11-18 | open | Whether to build ChatGPT's proposed "Dual AI Studio" (own server + API keys) | pending owner decision; see COLLAB.md
