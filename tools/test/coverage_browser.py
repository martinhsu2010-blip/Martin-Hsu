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
    const aerial=label.startsWith('Park');
    c.position.set(x,height(x,z)+(aerial?55:4),z); c.lookAt(tx,height(tx,tz)+(aerial?0:3),tz);
    c.updateMatrixWorld(); updateFacadeLOD(true);
    r.render(scene,c);
    const image=r.domElement.toDataURL('image/png').split(',')[1];
    const calls=r.info.render.calls;
    return {image,calls};
}"""
INIT = """([device,quality]) => {
    let seed=5019;
    Math.random=()=>((seed=(Math.imul(1664525,seed)+1013904223)>>>0)/4294967296);
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
        views=dict(VIEWS)
        old_target=(-458,-696) if mobile else (-562,-656)
        for label,(x,z) in [('CBD',(82,168)),('Midtown',(-356,-194)),('Old',old_target),('Near',(83,168))]:
            views['Park-'+label]=(x+9,z+9,x,z)
        p.evaluate('''() => {__VH.STATE.timeOfDay=12; __VH.applySkyParams(__VH.skyAtHour(12));}''')
        for i, (view, pos) in enumerate(views.items()):
            data = p.evaluate(RENDER, [view, *pos])
            (output/f'{preset}-{view}-{name}.png').write_bytes(base64.b64decode(data['image']))
            result[view] = data['calls']
        assert not errors, errors
        return result


def diagnostic(browser, url, candidate, device, quality, output):
    counts=[]
    for enabled in [False,True]:
        tablet=device=='TABLET'
        with browser.new_context(viewport={'width':1024 if tablet else 800,'height':680 if tablet else 450},
                is_mobile=True,has_touch=True,user_agent='Mozilla/5.0 (Linux; Android) Mobile Chrome',
                service_workers='block') as ctx:
            ctx.add_init_script(f'({INIT})({json.dumps([device,quality])})')
            # Expose the production callbacks only in this test document.
            source=candidate.replace(b'window.__VH = { TREE_COLLIDERS',b'window.__VH = { animate, recordFps, TREE_COLLIDERS')
            ctx.route('**/index.html*',lambda route:route.fulfill(body=source,content_type='text/html'))
            p=ctx.new_page()
            p.goto(url+'/index.html'+('?fps=1' if enabled else ''),wait_until='domcontentloaded')
            p.wait_for_function('window.__VH && __VH.WORLD.cityInfill',timeout=180000)
            state=p.evaluate('''enabled=>{
                const {STATE:s,animate,recordFps,renderer,scene,camera}=__VH;
                const output=document.querySelector('#fps-diagnostics');
                const save=localStorage.getItem('vh_save');
                if (!!output!==enabled || !!recordFps!==enabled) throw Error('FPS gate');
                if(enabled){
                    const raw=[];
                    for(let t=0;t<61;t++){
                        const n=t===0?1:(t%3+5);
                        raw.push(n);
                        for(let i=0;i<n;i++)recordFps(t*1000+i*1000/n);
                    }
                    recordFps(61000);
                    const bins=raw.slice(-60), avg=(bins.reduce((a,b)=>a+b)/60).toFixed(1);
                    if(!output.textContent.includes(avg)||!output.textContent.includes('FPS 5'))throw Error(output.textContent);
                    document.dispatchEvent(new Event('visibilitychange'));
                    if(!output.textContent.includes('—'))throw Error('stale FPS');
                }
                renderer.render(scene,camera); const calls=renderer.info.render.calls;
                const q=s.quality,scale=s.resScale;
                s.perfCheck.done=true; s.resCheck={elapsed:2,frames:1,lastNow:1,good:0};
                animate(63000);
                if(enabled ? s.resScale!==scale : s.resScale>=scale)throw Error('resolution guard');
                if(enabled){
                    s.qualityManual=false; s.perfCheck={elapsed:100,frames:1,lastNow:1,done:false};
                    animate(65000);
                    if(s.quality!==q)throw Error('auto quality');
                    document.getElementById('pill-quality').click();
                    recordFps(66500);
                    if(!output.textContent.includes(s.quality))throw Error('preset refresh');
                }
                if(localStorage.getItem('vh_save')!==save)throw Error('save changed');
                return {calls,active:enabled,text:output?.textContent,scale:s.resScale,quality:s.quality};
            }''',enabled)
            counts.append(state)
            p.screenshot(path=str(output/f'{device}-fps-{enabled}.png'))
    print('DIAGNOSTIC',device,json.dumps(counts),flush=True)
    assert counts[0]['calls']==counts[1]['calls']


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
            previous=subprocess.check_output(['git','show','c8e395f:index.html'],cwd=ROOT)
            candidate=(ROOT/'index.html').read_bytes()
            uniform=candidate.replace(b'styleCoverage(parcels);',b'/* comparison: legacy uniform shell heights */')
            old = capture(browser,url,before,'base',args.preset,args.output)
            reviewed = capture(browser,url,previous,'reviewed',args.preset,args.output)
            uniform_calls = capture(browser,url,uniform,'uniform',args.preset,args.output)
            new = capture(browser,url,(ROOT/'index.html').read_bytes(),'candidate',args.preset,args.output)
            if args.preset=='PHONE_LOW':
                for device,quality in [('PHONE','LOW'),('TABLET','MED')]:
                    diagnostic(browser,url,candidate,device,quality,args.output)
        server.shutdown()
    delta = {k:new[k]-v for k,v in old.items()}
    result = dict(preset=args.preset, before=old, reviewed=reviewed, uniform=uniform_calls, after=new, delta=delta)
    (args.output/'draws.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result),flush=True)
    for i,(k,d) in enumerate(delta.items()):
        limit = (4 if i<4 else 8) if args.preset=='PHONE_LOW' else (8 if i<4 else 16)
        assert d <= limit,(k,d,limit)
        if i>=4:
            assert new[k]-reviewed[k]<=1,(k,new[k],reviewed[k])
            assert new[k]==uniform_calls[k],(k,new[k],uniform_calls[k])


if __name__ == '__main__':
    main()

