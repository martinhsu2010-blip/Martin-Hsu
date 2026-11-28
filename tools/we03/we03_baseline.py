#!/usr/bin/env python3
"""T-018A1 / WE-03A browser baseline (Claude-owned measurement tool; NOT run in CI).

Headless Chrome + SwiftShader, same method as the WE-01 B8 appendix (D-057/D-060). Every number written
here is class MEASURED_HEADLESS: CPU submission time of the game's own `animate()` step in software GL.
It is NOT device FPS and NOT VRAM. It never edits a game file: the page is served read-only and the game
loop is reached through an init script that captures `animate` as window.__animate.

Phases (resumable; each result is written to --out as soon as it exists):
  presets   runtime values of every preset that can be reached (static source inventory is in calibration)
  render    4 presets x 6 locations x {12:00,23:00} fresh sessions, 20 warm-up + 120 recorded frames
  repeat    second independent session for B3 and CBD x day/night x 4 presets (16 sessions)
  physics   4 presets x 5 pairs of two fresh BASE sessions (900 warm-up + 360 recorded step(1/60,1/60,3))
  speed     achieved top speed on a test straight (a lower bound, never the game's absolute limit)
  terrain   terrainHeight at every WE-01 common-L0 cell centre (input to the synthetic fixture planner)
  stall     per-frame program/texture counters for the scenes whose recorded frames contained multi-second stalls
Usage: python3 tools/we03/we03_baseline.py --phase render --out specs/we03/baseline_metrics.json
"""
import argparse, functools, hashlib, http.server, importlib.util, json, os, statistics, subprocess, sys, threading, time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCHEMA = "we03-baseline-v1"
ENGINEERING_BASE = "e8d5250fce0ea5f07f68840481cb95d2eca803fb"
AUDIT_BASE = "84319439243b51aa8d119e33eb62a0637feea887"
PRESETS = ["PHONE_LOW", "PHONE_MED", "TABLET_MED", "DESKTOP_HIGH"]
ALL_PRESETS = ["PHONE_LOW", "PHONE_MED", "TABLET_LOW", "TABLET_MED", "TABLET_HIGH", "DESKTOP_MED", "DESKTOP_HIGH",
               "DESKTOP_ULTRA", "IGPU_LOW", "IGPU_MED", "IGPU_HIGH"]
LOCS = [("B1", 240, 1080), ("B2", -700, 945), ("B3", -490, -710), ("SiteA", -501, -790), ("CBD", -60, 0), ("Suburbs", -1060, -238)]
TIMES = [("12:00", 12.0), ("23:00", 23.0)]
REPEAT_LOCS = ("B3", "CBD")
SPEED_START, SPEED_HEADING, SPEED_SECONDS = (0, -880), 0.0, 45       # avenue x=0, ROAD_NET.avenueZ=892: ~1.7 km straight toward +z
WARM, FRAMES, PHYS_WARM, PHYS_REC, PHYS_PAIRS = 20, 120, 900, 360, 5
VIEWPORT = [800, 450]
GAME_FILES = ["index.html", "sw.js", "manifest.webmanifest", "manifest.zh-TW.webmanifest"]
SENSITIVE = ("index.html", "sw.js", "manifest.webmanifest", "manifest.zh-TW.webmanifest", "assets", "specs/we02", "specs/we01")


def sh(*a):
    return subprocess.run(a, cwd=REPO, capture_output=True, text=True).stdout.strip()


def load_harness():
    """Reuse the repo's browser harness (seeded Math.random, saved quality settings, DESKTOP GPU spoof) but keep
    the game loop callable: the stock init script discards `animate`, this one stores it. index.html is unchanged."""
    p = REPO / "tools/test/t014b2_site_a_facade_check.py"
    spec = importlib.util.spec_from_file_location("vh_harness", p)
    m = importlib.util.module_from_spec(spec); sys.modules["vh_harness"] = m; spec.loader.exec_module(m)
    old = "window.requestAnimationFrame = fn => (fn && fn.name === 'animate') ? 0 : raf(fn);"
    new = "window.requestAnimationFrame = fn => { if (fn && fn.name === 'animate') { window.__animate = fn; return 0; } return raf(fn); };"
    assert old in m.INIT_SCRIPT, "harness init script changed; update we03_baseline.py"
    m.INIT_SCRIPT = m.INIT_SCRIPT.replace(old, new)
    return m


CHROME_ARGS = ["--no-sandbox", "--disable-dev-shm-usage", "--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"]


def launch(pw):
    """One fresh Chrome per measured session: a long SwiftShader run can take the GPU process down and make later page loads hang."""
    return pw.chromium.launch(channel="chrome", headless=True, args=CHROME_ARGS)


def serve(root):
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a, **k):
            pass
    H = functools.partial(Quiet, directory=str(root))
    s = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{s.server_address[1]}"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# ---------------------------------------------------------------- in-page programs
STATIC_JS = r"""() => {
  const V = window.__VH, {scene, renderer, physicsWorld, WORLD} = V;
  const geoms = new Set(), mats = new Set(), texs = new Set();
  let meshes = 0, inst = 0, instTotal = 0, lights = 0, skinned = 0;
  scene.traverse(o => { if (o.isLight) lights++; if (!o.isMesh && !o.isLine && !o.isPoints) return; meshes++;
    if (o.isSkinnedMesh) skinned++;
    if (o.isInstancedMesh) { inst++; instTotal += o.count; }
    if (o.geometry) geoms.add(o.geometry);
    (Array.isArray(o.material) ? o.material : [o.material]).forEach(m => m && mats.add(m)); });
  let gbytes = 0;   // de-duplicated: each geometry object counted once; attributes/indices as stored
  geoms.forEach(g => { for (const k in g.attributes) { const a = g.attributes[k]; const arr = a.isInterleavedBufferAttribute ? a.data.array : a.array; gbytes += arr.byteLength; } if (g.index) gbytes += g.index.array.byteLength; });
  const keys = ['map','normalMap','roughnessMap','metalnessMap','emissiveMap','aoMap','alphaMap','bumpMap','envMap','lightMap'];
  mats.forEach(m => keys.forEach(k => { if (m[k]) texs.add(m[k]); }));
  [scene.background, scene.environment].forEach(x => { if (x && x.isTexture) texs.add(x); });
  let tbytes = 0, unsized = 0;   // estimate: w*h*4 bytes (RGBA8 assumed, compressed formats not modelled) x faces x 4/3 if mipmapped
  texs.forEach(tx => { const im = tx.image; let w = 0, h = 0, faces = 1;
    if (Array.isArray(im)) { faces = im.length; const f = im[0]; w = f && (f.width || (f.image && f.image.width)) || 0; h = f && (f.height || (f.image && f.image.height)) || 0; }
    else if (im) { w = im.width || 0; h = im.height || 0; }
    if (!w || !h) unsized++;
    tbytes += w * h * 4 * faces * (tx.generateMipmaps ? 4 / 3 : 1); });
  let shapes = 0, stat = 0, dyn = 0, sleeping = 0;
  physicsWorld.bodies.forEach(b => { shapes += b.shapes.length; if (b.mass === 0) stat++; else dyn++; if (b.sleepState === 2) sleeping++; });
  const wl = {}; for (const k in WORLD) { const v = WORLD[k]; if (Array.isArray(v)) wl[k] = v.length; }
  const gl = renderer.getContext(), ext = gl.getExtension('WEBGL_debug_renderer_info');
  const cap = renderer.capabilities, st = V.STATE;
  return { meshes, instancedMeshes: inst, instancedInstances: instTotal, skinnedMeshes: skinned, lights,
    geometries_unique: geoms.size, materials_unique: mats.size, textures_unique: texs.size, textures_without_size: unsized,
    renderer_geometries: renderer.info.memory.geometries, renderer_textures: renderer.info.memory.textures,
    programs: (renderer.info.programs || []).length,
    geometry_buffer_bytes_estimate: gbytes, texture_bytes_estimate: Math.round(tbytes),
    texture_estimate_note: 'RGBA8 w*h*4*faces*(4/3 if generateMipmaps); no compression/format model; headless estimate, not VRAM',
    bodies: physicsWorld.bodies.length, shapes, bodies_static: stat, bodies_dynamic: dyn, bodies_sleeping: sleeping,
    world_array_lengths: wl, trees: V.TREES.list.length,
    capability: { gpu_unmasked: ext ? gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) : null, gl_renderer: gl.getParameter(gl.RENDERER), gl_version: gl.getParameter(gl.VERSION),
      maxTextures: cap.maxTextures, maxTextureSize: cap.maxTextureSize, maxAttributes: cap.maxAttributes, precision: cap.precision, isWebGL2: cap.isWebGL2 },
    settings: { quality: st.quality, fpsCap: st.fpsCap, usePostFX: st.usePostFX, resScale: st.resScale, pixelRatio: renderer.getPixelRatio(),
      shadowEnabled: renderer.shadowMap.enabled, shadowMapSize: (() => { const l = scene.children.find(c => c.isDirectionalLight && c.shadow); return l ? l.shadow.mapSize.x : null; })(),
      fogDensity: scene.fog ? scene.fog.density : null, cameraFar: V.camera.far, cameraFov: V.camera.fov, cameraAspect: V.camera.aspect } };
}"""

FRAME_JS = r"""({x, z, hour, frames, warm}) => {
  const V = window.__VH, S = V.STATE, r = V.renderer;
  S.dayCycle = false; S.fpsCap = 0; S.qualityManual = true; if (S.perfCheck) S.perfCheck.done = true;
  S.pauseRender = false; S.timeOfDay = hour; V.applySkyParams(V.skyAtHour(hour), true);
  V.teleportTo(x, z, 0);
  let now = (window.__now || 1000); const anim = window.__animate;
  r.info.autoReset = false;
  let cur = null;
  const origRender = r.render.bind(r), origShadow = r.shadowMap.render.bind(r.shadowMap);
  const snap = () => ({c: r.info.render.calls, t: r.info.render.triangles});
  r.render = function(sc, cam) { const a = snap(), t0 = performance.now(); const o = origRender(sc, cam); const b = snap(); cur && cur.push(['render', b.c - a.c, b.t - a.t, performance.now() - t0]); return o; };
  r.shadowMap.render = function(...args) { const a = snap(), t0 = performance.now(); const o = origShadow(...args); const b = snap(); cur && cur.push(['shadow', b.c - a.c, b.t - a.t, performance.now() - t0]); return o; };
  for (let i = 0; i < warm; i++) { r.info.reset(); anim(now += 1000 / 60); }
  const cam0 = V.camera.position.toArray(), pl0 = V.PLAYER.body.position.toArray();
  const ms = [], calls = [], tris = [], shT = [], shC = [], mainT = [], nrender = [];
  for (let i = 0; i < frames; i++) {
    now += 1000 / 60; r.info.reset(); cur = []; const t0 = performance.now(); anim(now); const dt = performance.now() - t0;
    const p = cur; cur = null; ms.push(dt); calls.push(r.info.render.calls); tris.push(r.info.render.triangles);
    let st = 0, sc = 0, mt = 0, nr = 0; p.forEach(q => { if (q[0] === 'shadow') { sc += q[1]; st += q[2]; } else { nr++; mt += q[2]; } });
    shC.push(sc); shT.push(st); mainT.push(mt); nrender.push(nr);
  }
  r.render = origRender; r.shadowMap.render = origShadow; window.__now = now;
  const cam1 = V.camera.position.toArray(), pl1 = V.PLAYER.body.position.toArray();
  const inB = V.WORLD.buildings.some(b => pl1[0] >= b.minX && pl1[0] <= b.maxX && pl1[2] >= b.minZ && pl1[2] <= b.maxZ);
  return { frame_ms: ms, draw_calls: calls, triangles: tris, shadow_triangles: shT, shadow_calls: shC, render_pass_triangles: mainT, render_passes: nrender,
    camera_start: cam0, camera_end: cam1, player_start: pl0, player_end: pl1, ground: V.__th(x, z), inside_building: inB, mode: S.mode, hour: S.timeOfDay };
}"""

PHYS_JS = r"""({warm, rec, x, z}) => {
  const V = window.__VH; V.teleportTo(x, z, 0); const w = V.physicsWorld;
  for (let i = 0; i < warm; i++) w.step(1/60, 1/60, 3);
  const s = new Array(rec);
  for (let i = 0; i < rec; i++) { const t0 = performance.now(); w.step(1/60, 1/60, 3); s[i] = performance.now() - t0; }
  return { samples: s, bodies: w.bodies.length };
}"""

SPEED_JS = r"""({x, z, heading, seconds, upgrade, nitro, hz, model}) => {
  const V = window.__VH, S = V.STATE, I = V.INPUT, r = V.renderer;
  S.selectedModel = model || null; S.dayCycle = false; S.fpsCap = 0; S.upgradeLevel = upgrade; S.pauseRender = false; if (S.perfCheck) S.perfCheck.done = true;
  V.teleportTo(x, z, 0);
  if (S.mode !== 'CAR') V.toggleEnterExitCar();
  const car = S.currentVehicle, b = car.chassisBody;
  b.position.set(x, V.__th(x, z) + 1.2, z); b.velocity.set(0, 0, 0); b.angularVelocity.set(0, 0, 0);
  b.quaternion.setFromEuler(0, heading, 0); car.nitro = 100;
  I.forward = true; I.shift = !!nitro; I.left = I.right = I.backward = false;
  let now = (window.__now || 1000), peak = 0, peakT = 0, t = 0; const anim = window.__animate; const trace = [];
  const n = Math.round(seconds * hz);
  for (let i = 0; i < n; i++) { now += 1000 / hz; anim(now); t += 1 / hz; const v = Math.hypot(b.velocity.x, b.velocity.z); if (v > peak) { peak = v; peakT = t; } if (i % hz === 0) trace.push(+v.toFixed(2)); }
  I.forward = I.shift = false; window.__now = now;
  return { vehicle: car.name, vmax_kmh_source: car.vmax, upgrade, nitro: !!nitro, peak_mps: peak, peak_kmh: peak * 3.6, peak_at_s: peakT, per_second_mps: trace,
           end_position: [b.position.x, b.position.y, b.position.z], max_step_distance_m_at_peak: peak / hz };
}"""


STALL_JS = r"""({x, z, hour, frames}) => {
  const V = window.__VH, S = V.STATE, r = V.renderer; S.dayCycle = false; S.fpsCap = 0; S.qualityManual = true; if (S.perfCheck) S.perfCheck.done = true; S.pauseRender = false;
  S.timeOfDay = hour; V.applySkyParams(V.skyAtHour(hour), true); V.teleportTo(x, z, 0);
  let now = window.__now || 1000, last = [(r.info.programs || []).length, r.info.memory.textures, r.info.memory.geometries]; const out = [];
  for (let i = 0; i < frames; i++) {
    now += 1000 / 60; r.info.reset(); const t0 = performance.now(); window.__animate(now); const ms = performance.now() - t0;
    const cur = [(r.info.programs || []).length, r.info.memory.textures, r.info.memory.geometries];
    if (ms > 500 || cur.some((v, k) => v !== last[k])) out.push({frame: i, ms: Math.round(ms), d_programs: cur[0] - last[0], d_textures: cur[1] - last[1], d_geometries: cur[2] - last[2]});
    last = cur;
  }
  return out;
}"""
STALL_SCENES = [("TABLET_MED", "CBD", -60, 0, "12:00", 12.0), ("TABLET_MED", "CBD", -60, 0, "23:00", 23.0), ("DESKTOP_HIGH", "Suburbs", -1060, -238, "12:00", 12.0), ("PHONE_MED", "CBD", -60, 0, "23:00", 23.0)]

TERRAIN_JS = r"""(cells) => { const th = window.__VH.__th; return cells.map(c => +th(c[0], c[1]).toFixed(3)); }"""
L0_CSV = "tools/fixtures/we01/we01a_common_l0_cells.csv"


# ---------------------------------------------------------------- page helpers
TABLET_UA = "Mozilla/5.0 (Linux; Android 14; SM-X926B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
PHONE_UA = "Mozilla/5.0 (Linux; Android 14; Mobile) AppleWebKit/537.36 Chrome/130.0 Mobile Safari/537.36"


def open_game(H, browser, url, preset):
    """Like the repo harness, but TABLET presets get a 1280x800 `screen` (game detectDevice(): short screen side >= 600 -> TABLET) while the viewport stays 800x450.
    IGPU presets are reached natively (SwiftShader matches the game's integrated-GPU test); DESKTOP presets use the harness GPU-name spoof."""
    device, quality = preset.split("_")
    vp = {"width": 800, "height": 450}
    opts = dict(viewport=vp, screen=vp, device_scale_factor=1, service_workers="block")
    if device == "PHONE": opts.update(is_mobile=True, has_touch=True, user_agent=PHONE_UA)
    if device == "TABLET": opts.update(is_mobile=True, has_touch=True, user_agent=TABLET_UA, screen={"width": 1280, "height": 800})
    ctx = browser.new_context(**opts)
    ctx.add_init_script(f"({H.INIT_SCRIPT})({json.dumps([device, quality])})")
    page = ctx.new_page(); errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(url + "/index.html", wait_until="domcontentloaded", timeout=120000)
    page.wait_for_function("window.__VH && window.__VH.WORLD && window.__VH.WORLD.showcaseSiteA && window.__VH.WORLD.showcaseSiteA.atlas", timeout=120000)
    return ctx, page, errors


def open_page(H, browser, url, preset):
    t0 = time.time()
    for attempt in range(3):                         # a cold session occasionally misses the 120 s load window; retry on a fresh context
        try:
            ctx, page, errs = open_game(H, browser, url, preset)
            break
        except Exception as e:
            print("load retry", preset, attempt, str(e)[:80], flush=True)
            if attempt == 2:
                raise
    ph = None
    if preset != "PHONE_LOW":                       # PHONE_LOW never loads Poly Haven models (__phDone never fires)
        try:
            page.wait_for_function("window.__phDone === true", timeout=150000); ph = True
        except Exception:
            ph = False
    return ctx, page, errs, round((time.time() - t0) * 1000), ph


def pct(a, q):
    s = sorted(a); k = max(0, min(len(s) - 1, int(-(-q * len(s) // 100)) - 1))   # nearest-rank
    return s[k]


def stats(a):
    return {"n": len(a), "min": round(min(a), 4), "p50": round(pct(a, 50), 4), "p95": round(pct(a, 95), 4), "p99": round(pct(a, 99), 4),
            "max": round(max(a), 4), "mean": round(statistics.fmean(a), 4), "n_over_50": sum(1 for v in a if v > 50), "n_over_100": sum(1 for v in a if v > 100)}


def one_session(H, pw, url, preset, loc, x, z, tname, hour, tag):
    browser = launch(pw)
    ctx, page, errs, load_ms, ph = open_page(H, browser, url, preset)
    try:
        default_cap = page.evaluate("() => window.__VH.STATE.fpsCap")      # before FRAME_JS lifts the cap: identifies the real PHONE/TABLET (30) vs DESKTOP/IGPU (60) profile
        r = page.evaluate(FRAME_JS, {"x": x, "z": z, "hour": hour, "frames": FRAMES, "warm": WARM})
        res = page.evaluate(STATIC_JS)
        errors = [str(e)[:200] for e in errs[:5]]
    finally:
        ctx.close(); browser.close()
    rec = {"measurement_class": "MEASURED_HEADLESS", "preset": preset, "location": loc, "x": x, "z": z, "time": tname, "hour": hour,
           "session_tag": tag, "default_fps_cap": default_cap, "warmup_frames": WARM, "recorded_frames": len(r["frame_ms"]), "dt": "1/60", "load_wall_ms": load_ms, "ph_done": ph, "page_errors": errors,
           "frame_ms_definition": "CPU time of one animate() call incl. renderer submission; software GL; not device frame time",
           "stats": {"frame_ms": stats(r["frame_ms"]), "draw_calls": stats(r["draw_calls"]), "triangles": stats(r["triangles"]),
                     "shadow_triangles": stats(r["shadow_triangles"]), "render_pass_triangles": stats(r["render_pass_triangles"])},
           "samples": {k: r[k] for k in ("frame_ms", "draw_calls", "triangles", "shadow_triangles", "shadow_calls", "render_pass_triangles", "render_passes")},
           "fixed_view": {k: r[k] for k in ("camera_start", "camera_end", "player_start", "player_end", "ground", "inside_building", "mode", "hour")},
           "resources": res}
    return rec


def phase_render(H, pw, url, out, preset_list, repeat):
    key = "repeats" if repeat else "combinations"
    for preset in preset_list:
        for loc, x, z in LOCS:
            if repeat and loc not in REPEAT_LOCS:
                continue
            for tname, hour in TIMES:
                k = f"{preset}/{loc}/{tname}"
                if k in out.setdefault(key, {}):
                    continue
                t0 = time.time()
                out[key][k] = one_session(H, pw, url, preset, loc, x, z, tname, hour, "repeat" if repeat else "primary")
                s = out[key][k]["stats"]
                print(f"{key[:4]} {k} ms_p50={s['frame_ms']['p50']} dc={s['draw_calls']['p50']} tri={s['triangles']['p50']} ph={out[key][k]['ph_done']} ({time.time()-t0:.0f}s)", flush=True)
                save(out, out["_path"])


def phase_physics(H, pw, url, out, preset_list):
    for preset in preset_list:
        if preset in out.setdefault("physics_pairs", {}) and len(out["physics_pairs"][preset]["pairs"]) >= PHYS_PAIRS:
            continue
        browser = launch(pw)
        ca, pa, _, _, pha = open_page(H, browser, url, preset)
        cb, pb, _, _, phb = open_page(H, browser, url, preset)
        pairs = []
        try:
            for i in range(PHYS_PAIRS):
                order = [("A", pa), ("B", pb)] if i % 2 == 0 else [("B", pb), ("A", pa)]
                rec = {}
                for nm, pg in order:
                    rec[nm] = pg.evaluate(PHYS_JS, {"warm": PHYS_WARM, "rec": PHYS_REC, "x": -60, "z": 0})
                ma, mb = statistics.median(rec["A"]["samples"]), statistics.median(rec["B"]["samples"])
                pairs.append({"order": [o[0] for o in order], "median_ms_A": round(ma, 5), "median_ms_B": round(mb, 5), "ratio_B_over_A": round(mb / ma, 5),
                              "bodies": rec["A"]["bodies"], "samples_ms_A": [round(v, 5) for v in rec["A"]["samples"]], "samples_ms_B": [round(v, 5) for v in rec["B"]["samples"]]})
                print("pair", preset, i, pairs[-1]["median_ms_A"], pairs[-1]["median_ms_B"], pairs[-1]["ratio_B_over_A"], flush=True)
        finally:
            ca.close(); cb.close(); browser.close()
        out["physics_pairs"][preset] = {"measurement_class": "MEASURED_HEADLESS", "warmup_steps": PHYS_WARM, "recorded_steps": PHYS_REC, "step": "physicsWorld.step(1/60,1/60,3)",
                                        "control_band": [round(1 / 1.10, 5), 1.10], "ph_done": [pha, phb], "pairs": pairs}
        save(out, out["_path"])


def phase_presets(H, pw, url, out):
    """Runtime values (read right after load, before any measurement code runs) for all 11 presets; the check compares them with the QUALITY_CONFIG source."""
    for preset in ALL_PRESETS:
        if preset in out.setdefault("preset_runtime", {}):
            continue
        browser = launch(pw)
        ctx, page, errs, load_ms, ph = open_page(H, browser, url, preset)
        try:
            res = page.evaluate(STATIC_JS)
        finally:
            ctx.close(); browser.close()
        out["preset_runtime"][preset] = {"measurement_class": "MEASURED_HEADLESS", "settings": res["settings"], "capability": res["capability"], "load_wall_ms": load_ms, "ph_done": ph,
                                         "bodies": res["bodies"], "shapes": res["shapes"], "materials": res["materials_unique"]}
        print("preset", preset, res["settings"], flush=True)
        save(out, out["_path"])


def phase_speed(H, pw, url, out):
    sp = out.setdefault("speed", {"measurement_class": "MEASURED_HEADLESS", "runs": [],
                                  "note": "peak speed reached on one test straight in the headless sim; a LOWER BOUND on the game's limit, never the limit itself",
                                  "track": {"start": list(SPEED_START), "heading_rad": SPEED_HEADING, "seconds": SPEED_SECONDS, "description": "avenue x=0 heading +z (ROAD_NET.avenuesX[4])"}})
    for model in (None, "porsche911"):
        for upgrade, nitro in ((1, False), (1, True), (5, True)):
            if any(r["model"] == model and r["upgrade"] == upgrade and r["nitro"] == nitro for r in sp["runs"]):
                continue
            browser = launch(pw)                                                         # fresh Chrome and page per run: no car carried over
            ctx, page, errs, load_ms, ph = open_page(H, browser, url, "PHONE_LOW")
            try:
                r = page.evaluate(SPEED_JS, {"x": SPEED_START[0], "z": SPEED_START[1], "heading": SPEED_HEADING, "seconds": SPEED_SECONDS, "upgrade": upgrade, "nitro": nitro, "hz": 60, "model": model})
            finally:
                ctx.close(); browser.close()
            r["model"] = model
            sp["runs"].append(r); print("speed", model, upgrade, nitro, round(r["peak_mps"], 1), "m/s", r["vehicle"], flush=True)
            save(out, out["_path"])


def phase_stall(H, pw, url, out):
    """Re-run the scenes whose recorded frames contained multi-second stalls with per-frame program/texture/geometry counters (diagnosis only, never a gate)."""
    st = out.setdefault("stall_probe", {"measurement_class": "MEASURED_HEADLESS", "note": "frame index counts from the first frame after load (warm-up included); a stall with new programs/textures is a first-use shader compile or upload, not steady-state cost", "runs": {}})
    for preset, loc, x, z, tname, hour in STALL_SCENES:
        k = f"{preset}/{loc}/{tname}"
        if k in st["runs"]:
            continue
        browser = launch(pw); ctx, page, errs, load_ms, ph = open_page(H, browser, url, preset)
        try:
            st["runs"][k] = page.evaluate(STALL_JS, {"x": x, "z": z, "hour": hour, "frames": WARM + FRAMES})
        finally:
            ctx.close(); browser.close()
        print("stall", k, st["runs"][k][-3:], flush=True); save(out, out["_path"])


def phase_terrain(H, pw, url, out):
    """terrainHeight() at the centre of every WE-01 common-L0 cell (5 m grid): lets the fixture planner reject unstandable synthetic sites."""
    if "terrain_l0" in out:
        return
    rows = [l.strip().split(",") for l in (REPO / L0_CSV).read_text().splitlines()[1:] if l.strip()]
    cells = [[float(r[1]), float(r[2])] for r in rows]
    browser = launch(pw)
    ctx, page, errs, load_ms, ph = open_page(H, browser, url, "PHONE_LOW")
    try:
        h = page.evaluate(TERRAIN_JS, cells)
    finally:
        ctx.close(); browser.close()
    out["terrain_l0"] = {"measurement_class": "MEASURED_HEADLESS", "source": L0_CSV, "source_sha256": sha256(REPO / L0_CSV), "n": len(h),
                         "regions": [r[0] for r in rows], "x": [c[0] for c in cells], "z": [c[1] for c in cells], "height_m": h,
                         "note": "game terrainHeight(x,z) at cell centres; geometry is identical across presets (WE-01 map_geometry)"}
    print("terrain cells", len(h), min(h), max(h), flush=True); save(out, out["_path"])


# ---------------------------------------------------------------- orchestration
def protected_files():
    """Files A1 must leave byte-identical: game files, manifests, WE-01 final and WE-02 accepted artifacts."""
    out = sh("git", "ls-tree", "-r", "--name-only", ENGINEERING_BASE, "--", "specs/we01-final", "specs/we02", *GAME_FILES)
    return sorted(out.splitlines())


def environment(browser, url):
    return {"engineering_base": ENGINEERING_BASE, "audit_base": AUDIT_BASE, "head": sh("git", "rev-parse", "HEAD"),
            "index_html_blob": sh("git", "hash-object", "index.html"), "index_html_sha256": sha256(REPO / "index.html"),
            "index_html_blob_at_engineering_base": sh("git", "rev-parse", f"{ENGINEERING_BASE}:index.html"),
            "index_html_blob_at_audit_base": sh("git", "rev-parse", f"{AUDIT_BASE}:index.html"),
            "cache": next((l.split("'")[1] for l in (REPO / "sw.js").read_text().splitlines() if l.strip().startswith("const CACHE")), None),
            "browser": browser.version, "playwright": sh(sys.executable, "-c", "import importlib.metadata as m;print(m.version('playwright'))"),
            "python": sys.version.split()[0], "viewport": VIEWPORT, "headless": True, "gl": "swiftshader", "os": " ".join(os.uname()[:3]), "cpus": os.cpu_count(),
            "protected_blobs_at_engineering_base": {f: sh("git", "rev-parse", f"{ENGINEERING_BASE}:{f}") for f in protected_files()},
            "tool_sha256": sha256(__file__), "harness_sha256": sha256(REPO / "tools/test/t014b2_site_a_facade_check.py"),
            "method": {"warmup_frames": WARM, "recorded_frames": FRAMES, "dt": "1/60", "dayCycle": False, "fpsCap": 0, "viewport": VIEWPORT,
                       "gpu_spoof": "DESKTOP profile: UNMASKED_RENDERER_WEBGL (37446) returns 'Test RTX discrete GPU' via the shared harness init script",
                       "physics": f"{PHYS_WARM} warm-up + {PHYS_REC} recorded physicsWorld.step(1/60,1/60,3), position (-60,0)"},
            "game_file_diff_vs_engineering_base": sh("git", "diff", "--stat", ENGINEERING_BASE, "--", *GAME_FILES)}


def save(out, path):
    d = {k: v for k, v in out.items() if k != "_path"}
    tmp = str(path) + ".tmp"
    Path(tmp).write_text(json.dumps(d, separators=(",", ":")))
    os.replace(tmp, path)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--phase", choices=["presets", "render", "repeat", "physics", "speed", "terrain", "stall", "all"], required=True)
    ap.add_argument("--out", default=str(REPO / "specs/we03/baseline_metrics.json"))
    ap.add_argument("--presets", default=",".join(PRESETS))
    args = ap.parse_args()
    from playwright.sync_api import sync_playwright
    if sh("git", "diff", "--stat", ENGINEERING_BASE, "--", *GAME_FILES):
        sys.exit("game files differ from the engineering base: refusing to measure")
    outp = Path(args.out)
    out = json.loads(outp.read_text()) if outp.exists() else {"schema": SCHEMA}
    out["_path"] = outp
    H = load_harness(); url = serve(REPO)
    wanted = [p for p in args.presets.split(",") if p]
    with sync_playwright() as p:
        tmp = launch(p); env = environment(tmp, url); tmp.close()
        out.setdefault("environment_history", [])
        if not out["environment_history"] or out["environment_history"][-1].get("tool_sha256") != env["tool_sha256"] or out["environment_history"][-1]["head"] != env["head"]:
            out["environment_history"].append(dict(env, phase=args.phase, started=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())))
        out["environment"] = env
        ph = args.phase
        if ph in ("presets", "all"): phase_presets(H, p, url, out)
        if ph in ("render", "all"): phase_render(H, p, url, out, wanted, False)
        if ph in ("repeat", "all"): phase_render(H, p, url, out, wanted, True)
        if ph in ("physics", "all"): phase_physics(H, p, url, out, wanted)
        if ph in ("speed", "all"): phase_speed(H, p, url, out)
        if ph in ("terrain", "all"): phase_terrain(H, p, url, out)
        if ph in ("stall", "all"): phase_stall(H, p, url, out)
        save(out, outp)
    print("done", args.phase, outp)


if __name__ == "__main__":
    main()
