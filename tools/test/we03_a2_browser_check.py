"""A2 browser gates. Run at the requested PR commit. Artifacts go outside the checkout."""
import argparse
import functools
import json
import os
import shutil
import subprocess
import tempfile
import threading
from contextlib import contextmanager
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
BASE = "a08531a4e72887c02b6f3977a13428d77930aedc"
PHONE = "Mozilla/5.0 (Linux; Android 14; Mobile) AppleWebKit/537.36 Chrome/130.0 Mobile Safari/537.36"
VIEW = dict(width=844, height=390)
READY = "window.__VH && __VH.WORLD.vehicles.length && __VH.renderer"
SEED = """let seed=5019;
Math.random=()=>((seed=(Math.imul(seed,1664525)+1013904223)>>>0)/4294967296);
let gameSeed=5019;
window.gameRandom=()=>((gameSeed=(Math.imul(gameSeed,1664525)+1013904223)>>>0)/4294967296);
const raf=requestAnimationFrame.bind(window);
window.requestAnimationFrame=fn=>fn.name==='animate' ? (window.gameFrame=fn,0) : raf(fn);
"""


@contextmanager
def serve():
    base = subprocess.check_output(["git", "show", BASE + ":index.html"], cwd=ROOT)
    candidate = (ROOT / "index.html").read_bytes()

    class Handler(SimpleHTTPRequestHandler):
        def do_GET(self):
            path = urlsplit(self.path).path
            parts = path.split("/", 2)
            if len(parts) == 3 and parts[1] in ("base", "pr", "live"):
                self.path = "/" + parts[2]
                if parts[2] == "index.html":
                    data = base if parts[1] == "base" else candidate
                    if parts[1] != "live":
                        # Test-only clock entry and save fixture hook, available identically to both revisions.
                        data = data.replace(b"Math.random()", b"window.gameRandom()").replace(
                            b"window.__VH = { TREE_COLLIDERS", b"window.__VH = { persistSave, TREE_COLLIDERS")
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                    return
            super().do_GET()

        def log_message(self, *_):
            pass

    with ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Handler, directory=ROOT)) as server:
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            yield f"http://127.0.0.1:{server.server_port}"
        finally:
            server.shutdown()


def context(browser, live=False):
    return browser.new_context(viewport=VIEW, screen=VIEW, device_scale_factor=1, is_mobile=True,
                               has_touch=True, user_agent=PHONE, service_workers="allow" if live else "block")


def load(page, url):
    page.goto(url, wait_until="domcontentloaded", timeout=240000)
    page.wait_for_function(READY, timeout=240000)


def settings(ctx, save=None):
    ctx.add_init_script("""if (!localStorage.getItem('vh_settings'))
        localStorage.setItem('vh_settings',JSON.stringify({quality:'LOW',qualityDevice:'PHONE',fpsCap:30}));""")
    if save is not None:
        ctx.add_init_script("if (!localStorage.getItem('vh_save')) localStorage.setItem('vh_save',"
                            + json.dumps(json.dumps(save)) + ");")


def reference_save(browser, host):
    with context(browser) as ctx:
        settings(ctx)
        ctx.add_init_script(SEED)
        p = ctx.new_page()
        load(p, host + "/base/index.html")
        return p.evaluate("""() => {
            const {SAVE,STATE,persistSave}=__VH;
            const model=Object.keys(__VH.CAR_MODELS).find(key=>__VH.CAR_MODELS[key].price>0);
            if(!model) throw Error('owned vehicle fixture');
            Object.assign(SAVE,{owned:[model],jumps:{3:true},deliveries:7});
            STATE.cash=19327; STATE.upgradeLevel=2; persistSave();
            const data=JSON.parse(localStorage.getItem('vh_save'));
            if(data.cash!==19327 || data.upgrade!==2 || data.deliveries!==7) throw Error('base fixture');
            return data;
        }""")


# Count outside A2. In particular, direct and composer passes each contribute to these totals.
MEASURE = """post => {
    const {renderer:r,STATE:s,physicsWorld:w}=__VH;
    const time=performance.now()+100, counts=[];
    const meshes=[], materials=new Set(), textures=new Set();
    __VH.scene.traverse(obj=>{
        if(!obj.isMesh)return;
        meshes.push(obj);
        for(const mat of [].concat(obj.material)){
            materials.add(mat);
            for(const v of Object.values(mat)) if(v?.isTexture) textures.add(v);
        }
    });
    s.usePostFX=post;
    for(let i=0;i<30;i++) {
        r.info.autoReset=false;
        r.info.reset();
        gameFrame(time+40*i);
        counts.push({calls:r.info.render.calls,triangles:r.info.render.triangles,
            meshes:meshes.length,materials:materials.size,textures:textures.size,
            bodies:w.bodies.length,shapes:w.bodies.reduce((sum,b)=>sum+b.shapes.length,0),contacts:w.contacts.length});
    }
    return counts;
}"""


def comparison(browser, host, target, enabled, fixture, post):
    with context(browser) as ctx:
        settings(ctx, fixture)
        ctx.add_init_script(SEED)
        p = ctx.new_page()
        errors = []
        p.on("pageerror", lambda e: errors.append(str(e)))
        load(p, host + "/" + target + "/index.html" + ("?fps=1" if enabled else ""))
        p.wait_for_function("__VH.WORLD.vehicles.every(v=>v.customApplied || v.hasFerrariMesh)", timeout=240000)
        state = p.evaluate("""() => ({hud:!!document.querySelector('#fps-diagnostics'),
            api:!!__VH.diag, auto:__VH.renderer.info.autoReset,keys:Object.keys(localStorage).sort(),
            save:JSON.parse(localStorage.getItem('vh_save')),actual:__VH.SAVE})""")
        assert state["hud"] == enabled and state["api"] == (target == "pr" and enabled)
        # Before the independent harness touches autoReset.
        assert state["auto"] == (target == "base" or not enabled)
        assert state["save"] == fixture and state["actual"] == fixture, (target, state)
        rows = p.evaluate(MEASURE, post)
        assert all(r["calls"] > 0 and r["triangles"] > 0 for r in rows), rows
        if target == "pr" and enabled:
            snap = p.evaluate("__VH.diag.snapshot()")
            for field, key in [("drawCalls", "calls"), ("triangles", "triangles"), ("contacts", "contacts")]:
                assert snap[field] == rows[-1][key], (field, snap[field], rows[-1])
        p.reload(wait_until="domcontentloaded", timeout=240000)
        p.wait_for_function(READY, timeout=240000)
        result = p.evaluate("""() => [JSON.parse(localStorage.getItem('vh_save')),
            __VH.SAVE,Object.keys(localStorage).sort()]""")
        assert result == [fixture, fixture, state["keys"]] and not errors, (result, errors)
        return rows, state["keys"]


LAYOUT = """() => {
    const output=document.querySelector('#fps-diagnostics'), range=document.createRange();
    const rect=node=>{const r=node.getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height};};
    const box=rect(output), lines=output.textContent.split('\\n');
    let offset=0;
    const extents=lines.map(line=>{
        range.setStart(output.firstChild,offset);range.setEnd(output.firstChild,offset+line.length);
        offset+=line.length+1;return rect(range);
    });
    const buttons=[...document.querySelectorAll('#touch-controls button')].map(b=>({id:b.id,...rect(b)}))
        .filter(r=>r.w && r.h);
    return {mode:__VH.STATE.mode,w:innerWidth,h:innerHeight,lines,box,extents,buttons,
        canvas:rect(__VH.renderer.domElement),style:getComputedStyle(output).whiteSpace};
}"""


def overlaps(a, b):
    return (a["x"] < b["x"] + b["w"] and b["x"] < a["x"] + a["w"]
            and a["y"] < b["y"] + b["h"] and b["y"] < a["y"] + a["h"])


def hud(browser, host, out):
    with context(browser, live=True) as ctx:
        settings(ctx)
        p = ctx.new_page()
        errors = []
        p.on("pageerror", lambda e: errors.append(str(e)))
        load(p, host + "/live/index.html?fps=1")
        # First visit may not be controlled. Reload only after the real registration is ready.
        p.wait_for_function("!!navigator.serviceWorker.controller", timeout=300000)
        p.reload(wait_until="domcontentloaded", timeout=240000)
        p.wait_for_function(READY, timeout=240000)
        p.wait_for_function("__VH.diag.snapshot().cache !== 'UNAVAILABLE'", timeout=240000)
        p.evaluate("""() => { __VH.STATE.nearestVehicle=__VH.WORLD.vehicles[0];
            __VH.toggleEnterExitCar(); __VH.teleportTo(-60,0,0); }""")
        p.wait_for_function("""__VH.diag.snapshot().sampleCount>=3 &&
            __VH.diag.snapshot().frameP95!=='UNAVAILABLE' &&
            !document.querySelector('#fps-diagnostics').textContent.includes('—')""", timeout=240000)
        snap = p.evaluate("__VH.diag.snapshot()")
        data = p.evaluate(LAYOUT)
        # Save the evidence even when the following fit checks fail.
        p.screenshot(path=out / "phone-landscape-844x390.png", timeout=120000)
        (out / "phone-landscape-layout.json").write_text(json.dumps(dict(snapshot=snap, layout=data), indent=2))
        assert (data["w"], data["h"], data["mode"]) == (844, 390, "CAR")
        lines, box = data["lines"], data["box"]
        assert len(lines) == 4 and data["style"] == "pre"
        for row, labels in zip(lines, [
            ["#", " N ", "Avg ", "60s ", "Low FPS ", snap["preset"], " x", " cap "],
            ["P50/95/99 ", ">50/100 ", " max "], ["CPU95 P/U/R ", "B/S/C "],
            ["Draw/Tri/Prog ", "Hz N/A", "CACHE " + snap["cache"], "rel " + snap["release"]]
        ]):
            assert all(label in row for label in labels), (labels, row)
        assert box["x"] >= 0 and box["x"] + box["w"] <= data["w"]
        assert box["y"] + box["h"] <= data["h"] and box["y"] >= data["h"] * .84
        ys = [r["y"] for r in data["extents"]]
        assert len(set(ys)) == 4 and ys == sorted(ys)
        for r in data["extents"]:
            assert r["x"] >= box["x"] and r["x"] + r["w"] <= box["x"] + box["w"] + 1
        buttons = data["buttons"]
        assert {"btn-drive-gas", "btn-drive-brake", "btn-steer-left"} <= {b["id"] for b in buttons}
        assert not any(overlaps(box, b) for b in buttons), (box, buttons)
        assert not overlaps(box, dict(x=211, y=78, w=422, h=234)), "central driving view"
        assert not errors, errors
        ctx.set_offline(True)
        p.reload(wait_until="domcontentloaded", timeout=240000)
        p.wait_for_function(READY, timeout=240000)
        assert p.evaluate("!!navigator.serviceWorker.controller && !!__VH.diag")
        print("A2-C16 geometry PASS; independently inspect", out / "phone-landscape-844x390.png")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--artifacts", type=Path)
    ap.add_argument("--chromium", default=os.getenv("CHROME_BIN"))
    ap.add_argument("--hud-only", action="store_true")
    args = ap.parse_args()
    out = (args.artifacts or Path(tempfile.mkdtemp(prefix="we03-a2-"))).resolve()
    out.mkdir(exist_ok=True, parents=True)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    (out / "commit.txt").write_text(commit + "\n")
    print("Revision", commit, "baseline", BASE, "artifacts", out, flush=True)
    exe = args.chromium or shutil.which("google-chrome") or shutil.which("chromium")
    with serve() as host, sync_playwright() as pw, pw.chromium.launch(executable_path=exe, args=[
        "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--disable-dev-shm-usage"
    ]) as browser:
        hud(browser, host, out)
        if args.hud_only:
            return
        fixture = reference_save(browser, host)
        for post in (False, True):
            first, keys = comparison(browser, host, "base", False, fixture, post)
            repeat, _ = comparison(browser, host, "base", False, fixture, post)
            evidence = {"base-off": first, "base-off-repeat": repeat}
            deterministic = all(a["contacts"] == b["contacts"] for a, b in zip(first, repeat))
            fields = ["calls", "triangles", "bodies", "shapes", "meshes", "materials", "textures"] + (["contacts"] if deterministic else [])
            for target, enabled in [("base", True), ("pr", False), ("pr", True)]:
                rows, actual_keys = comparison(browser, host, target, enabled, fixture, post)
                evidence[f"{target}-{enabled}"] = rows
                assert actual_keys == keys
                for a, b in zip(first, rows):
                    for k in fields:
                        assert a[k] == b[k], (post, target, enabled, k, a, b)
            (out / f"external-post-{post}.json").write_text(json.dumps(evidence, indent=2))
            print("PostFX", post, "external counters verified; contacts", "PASS" if deterministic else "INCONCLUSIVE")
        print("RESULT: PASS (browser structural, save and HUD checks; device FPS pending)")


if __name__ == "__main__":
    main()
