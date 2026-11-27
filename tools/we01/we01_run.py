"""WE-01 runtime dump extractor (Claude-owned; not part of the game or of Gemini's allowlist).

Usage (from the repo root, with Chrome + Playwright installed):
  python3 tools/we01/we01_run.py full   OUTDIR   # PHONE_LOW and DESKTOP_HIGH, two independent loads each, fingerprint check
  python3 tools/we01/we01_run.py sample|b3mid|roads OUTDIR   # trimmed schema-valid sample dumps (sample: 3 small regions + U01; b3mid: B3 mid-size land; roads: six corridors, 25 m band)
Reads the game from the working tree; writes JSON dumps only. See tools/fixtures/we01/SCHEMA_NOTES.md.
"""
import sys, json, time, hashlib, importlib.util, functools, http.server, threading
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
BASE_SHA = "84319439243b51aa8d119e33eb62a0637feea887"; REL = "vh-2026-11-27-02"
JS = (Path(__file__).with_name("we01_extract.js")).read_text()
spec = importlib.util.spec_from_file_location("t", ROOT / "tools/test/t014b2_site_a_facade_check.py")
t = importlib.util.module_from_spec(spec); sys.modules["t"] = t; spec.loader.exec_module(t)
MINI = {"regions": [{"id": "B1", "name": "SAMPLE Oceanfront Heights", "r": [350, 1000, 390, 1040]},
                    {"id": "B2", "name": "SAMPLE Vista Hills", "r": [-640, 830, -600, 870]},
                    {"id": "B3", "name": "SAMPLE Palmwood Quarter", "r": [-580, -790, -540, -750]}], "routes": ["U01"]}

TINY = [{"id": "B1", "name": "SAMPLE Oceanfront Heights", "r": [350, 1000, 390, 1040]},
        {"id": "B2", "name": "SAMPLE Vista Hills", "r": [-640, 830, -600, 870]}]
MODES = {"sample": MINI,
         # B3 mid-size fragmented land (x -540..-240, z -860..-710, 20 m buffer) + U01 corridor (WE-01B fixtures)
         "b3mid": {"regions": TINY + [{"id": "B3", "name": "SAMPLE Palmwood Quarter (mid)", "r": [-540, -860, -240, -710]}], "routes": ["U01"], "buf": 20, "corBand": 25},
         # all six candidate road corridors with a 25 m band (WE-01C fixtures)
         "roads": {"regions": TINY + [{"id": "B3", "name": "SAMPLE Palmwood Quarter", "r": [-580, -790, -540, -750]}], "routes": ["C01", "C02", "H01", "H02", "X01", "U01"], "buf": 20, "corBand": 25}}

def serve():
    H = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT)); H.log_message = lambda *a, **k: None
    s = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H); threading.Thread(target=s.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{s.server_address[1]}"

def run(browser, url, preset, name, outdir, extra=None):
    ctx, page, errs = t.open_game_page(browser, url, preset)
    if preset.endswith("HIGH"):
        try: page.wait_for_function("window.__phDone === true", timeout=60000)
        except Exception: pass
    d = page.evaluate(JS, dict({"preset": preset, "base_sha": BASE_SHA, "game_release": REL}, **(extra or {})))
    d.pop("__debug", None); p = Path(outdir) / name
    p.write_text(json.dumps(d, separators=(",", ":")), encoding="utf-8"); ctx.close()
    print(name, preset, p.stat().st_size // 1024, "KB", "static_fingerprint", d["metadata"]["static_fingerprint"], "sha256", hashlib.sha256(p.read_bytes()).hexdigest(), "errs", errs[:2])
    return d

if __name__ == "__main__":
    mode, outdir = sys.argv[1], sys.argv[2]; Path(outdir).mkdir(parents=True, exist_ok=True); url = serve(); ok = True
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome", headless=True, args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
        for preset in ("PHONE_LOW", "DESKTOP_HIGH"):
            if mode in MODES:
                run(b, url, preset, f"{mode}_{preset.lower()}.json" if mode != "sample" else f"sample_{preset.lower()}.json", outdir, MODES[mode])
            else:
                a = run(b, url, preset, f"world_{preset.lower()}_A.json", outdir); c = run(b, url, preset, f"world_{preset.lower()}_B.json", outdir)
                same = a["metadata"]["static_fingerprint"] == c["metadata"]["static_fingerprint"]; ok &= same; print(preset, "A==B static fingerprint:", same)
        b.close()
    sys.exit(0 if ok else 1)
