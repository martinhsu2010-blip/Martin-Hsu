# Claude × ChatGPT collaboration protocol (VICE HORIZON VI)

Goal: two AI assistants work on the same game without overwriting each other. The owner (Martin) relays between them. **GitHub repo = single source of truth.**

## Roles
- **Claude (builder)**: edits `index.html`/assets, tests in a headless browser, bumps `sw.js` `CACHE`, commits and pushes to `main`. Only Claude (or the owner) pushes to `main`.
- **ChatGPT (planner/reviewer)**: reads the live repo, reviews code, designs features/balance, writes task specs and bug reports. It does not edit `index.html` directly; it submits changes as a task in `TASKS.md` or as a patch/diff the owner passes to Claude.
- **Owner**: decides priorities, plays the game, relays messages, approves releases.

## Files (read these first, every session)
1. `HANDOFF.md` — how the project works (architecture, systems, pitfalls).
2. `TASKS.md` — the task board. One task = one block with status.
3. `DECISIONS.md` — every decision, including ones discussed but **not yet coded**. This is how ChatGPT learns what was said in the Claude chat.
4. `LOG.md` — one line per shipped change: date, version, what, who.

## Workflow
1. Anyone proposes work by adding a task under **Inbox** in `TASKS.md` (ChatGPT: give the text to the owner or Claude to commit).
2. Owner moves a task to **Next**. Claude takes it, sets **Doing**, implements, tests, ships, sets **Done** with the version number and logs it in `LOG.md`.
3. At the end of every Claude session, Claude appends new decisions to `DECISIONS.md`; after every release it updates `LOG.md` and, if systems changed, `HANDOFF.md`.
4. Before starting any session, each AI re-reads these files from the live site (the repo is public):
   - https://martinhsu2010-blip.github.io/Martin-Hsu/HANDOFF.md
   - https://martinhsu2010-blip.github.io/Martin-Hsu/TASKS.md
   - https://martinhsu2010-blip.github.io/Martin-Hsu/DECISIONS.md
   - https://martinhsu2010-blip.github.io/Martin-Hsu/index.html (the game)
   (Allow ~2 min after a push for Pages to refresh.)

## Rules
- Never assume the other AI's state; re-read the files.
- One owner per task at a time (see `Owner:` field).
- Do not bump the game version or push unless you are the builder.
- Gemini prompts must be in English; explanations to the owner in Traditional Chinese.
- Mobile performance is a hard constraint; note the impact of any feature.

## Task template
```
### T-012 Short title
Status: Inbox | Next | Doing | Done
Owner: Claude | ChatGPT | Martin
Why: …
Acceptance: …
Notes / version shipped: …
```
