# tools/ — archived helper scripts (not needed to run the game)

These were used from Claude's sandbox. Paths inside them are sandbox paths and will need adjusting.
- `car-pipeline/convert_car.py` — Blender (bpy) pipeline: raw Sketchfab model → game-ready GLB (front axis, wheel nodes, material overrides, decimation). Run with `python3 -I`.
- `pwa-build/build.py` — rewrites CDN URLs to local paths and packages the PWA into the layout of this repo.
- `test/runtest.py`, `test/pwatest.py` — headless-browser smoke test and offline PWA test.

Note: the large `round*.py` patch scripts are NOT archived. They only replayed edits onto older single-file builds that are not in this repo. From now on `index.html` here is the canonical source and is edited directly.
