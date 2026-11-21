"""Compare fixed cameras and the changed render batches in real headless WebGL."""
import argparse
import base64
import functools
import http.server
import json
import shutil
import subprocess
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
VIEWS = {
    "Suburb-Main": (-1048, -242, -1118, -258),
    "Maple-Ave": (-915, -461, -974, -426),
    "Hillcrest": (-1210, 39, -1270, 31),
    "Valley": (-1210, -643, -1140, -646),
    "Ocean-Drive": (98, -173, 57, -180),
    "Midtown": (-240, -183, -319, -175),
    "Old-Town": (0, -540, -60, -535),
}
RENDER = """([label,x,z,tx,tz]) => {
    const {WORLD:w,renderer:r,scene,camera:c,__th:height,updateFacadeLOD}=window.__VH;
    c.position.set(x,height(x,z)+4,z); c.lookAt(tx,height(tx,tz)+3,tz);
    c.updateMatrixWorld(); updateFacadeLOD(true);
    r.render(scene,c);
    const image=r.domElement.toDataURL('image/png').split(',')[1];
    const focused = label==='city' ? [...w.cityInfillMeshes,...(w.cityCoverageFacades||[]),w.winInstanced] :
        [...w.suburbMeshes,...(w.suburbVerge?[w.suburbVerge]:[])];
    const keep=new Set(focused), hidden=[];
    scene.traverse(o=>{
        if(o.visible && (o.isMesh||o.isLine||o.isPoints||o.isSprite) && !keep.has(o)) {
            hidden.push(o); o.visible=false;
        }
    });
    r.render(scene,c);
    const calls=r.info.render.calls;
    hidden.forEach(o=>o.visible=true);
    return {image,calls};
}"""
INIT = """([device,quality]) => {
    localStorage.setItem('vh_settings', JSON.stringify({qualityDevice:device,quality}));
    const raf=window.requestAnimationFrame.bind(window);
    window.requestAnimationFrame=fn=>fn.name==='animate'?0:raf(fn);
    if(device==='DESKTOP'){
      for(const api of [window.WebGLRenderingContext,window.WebGL2RenderingContext]){
        const get=api.prototype.getParameter;
        api.prototype.getParameter=function(p){return p===37446?'Test RTX discrete GPU':get.call(this,p)};
      }
    }
}"""


def capture(browser, url, source, name, preset, output):
    device, quality = preset.split('_')
    mobile = device == 'PHONE'
    options = dict(viewport=dict(width=800, height=450), screen=dict(width=800, height=450),
                   device_scale_factor=1, is_mobile=mobile, has_touch=mobile,
                   service_workers='block')
    if mobile:
        options['user_agent'] = 'Mozilla/5.0 (Linux; Android 14; Mobile) AppleWebKit/537.36 Chrome/130.0 Mobile Safari/537.36'
    with browser.new_context(**options) as ctx:
        ctx.add_init_script(f'({INIT})({json.dumps([device, quality])})')
        ctx.route('**/index.html', lambda route: route.fulfill(body=source, content_type='text/html'))
        p = ctx.new_page()
        errors = []
        p.on('pageerror', lambda e: errors.append(str(e)))
        p.goto(url + '/index.html', wait_until='domcontentloaded', timeout=180000)
        p.wait_for_function('window.__VH && window.__VH.WORLD.cityInfill', timeout=180000)
        if not mobile:
            p.wait_for_function('window.__phDone', timeout=240000)
        settings = p.evaluate('''() => [__VH.STATE.quality,__VH.WORLD.suburbHouses.length]''')
        assert settings == [quality, 210 if mobile else 390], (preset, settings)
        result = {}
        for i, (view, pos) in enumerate(VIEWS.items()):
            data = p.evaluate(RENDER, ['suburb' if i < 4 else 'city', *pos])
            (output/f'{preset}-{view}-{name}.png').write_bytes(base64.b64decode(data['image']))
            result[view] = data['calls']
        assert not errors, errors
        return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('base')
    ap.add_argument('output', type=Path)
    ap.add_argument('preset', choices=['PHONE_LOW', 'DESKTOP_HIGH'])
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    before = subprocess.check_output(['git', 'show', f'{args.base}:index.html'], cwd=ROOT)
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
    with http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler) as server, sync_playwright() as pw:
        threading.Thread(target=server.serve_forever, daemon=True).start()
        url = f'http://127.0.0.1:{server.server_port}'
        chrome = shutil.which('google-chrome') or shutil.which('chromium')
        with pw.chromium.launch(executable_path=chrome, args=['--no-sandbox', '--disable-dev-shm-usage',
                                '--use-angle=swiftshader', '--enable-unsafe-swiftshader']) as browser:
            old = capture(browser,url,before,'base',args.preset,args.output)
            new = capture(browser,url,(ROOT/'index.html').read_bytes(),'candidate',args.preset,args.output)
        server.shutdown()
    delta = {k:new[k]-v for k,v in old.items()}
    result = dict(preset=args.preset, before=old, after=new, delta=delta)
    (args.output/'draws.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result),flush=True)
    for i,(k,d) in enumerate(delta.items()):
        limit = (4 if i<4 else 8) if args.preset=='PHONE_LOW' else (8 if i<4 else 16)
        assert d <= limit,(k,d,limit)


if __name__ == '__main__':
    main()

