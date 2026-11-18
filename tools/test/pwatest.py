import asyncio, json
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--use-angle=swiftshader','--enable-unsafe-swiftshader'])
        ctx = await b.new_context(viewport={'width':960,'height':540})
        external = []
        async def route(r):
            if r.request.url.startswith('http://localhost:8777'): await r.continue_()
            else:
                external.append(r.request.url[:100]); await r.abort()
        await ctx.route('**/*', route)
        page = await ctx.new_page()
        logs = []
        page.on('console', lambda m: logs.append(f'[{m.type}] {m.text}'[:200]) if m.type in ('error','warning') and 'GL Driver' not in m.text else None)
        page.on('pageerror', lambda e: logs.append('[PAGEERROR] ' + str(e)[:300]))
        await page.goto('http://localhost:8777/vice-horizon-pwa/index.html', wait_until='load')
        await page.wait_for_timeout(45000)
        st = await page.evaluate("""(()=>{const V=__VH; return {ferrari: !!V.STATE.ferrariTemplate, playerMixer: !!V.PLAYER.mixer, npcMixers: V.WORLD.pedestrians.filter(n=>n.mixer).length, brickMap: !!(V.WORLD.wallMaterials[0].map && V.WORLD.wallMaterials[0].map.image && V.WORLD.wallMaterials[0].map.image.src && V.WORLD.wallMaterials[0].map.image.src.includes('polyhaven')), sw: !!navigator.serviceWorker.controller, swReg: null, font: document.fonts.check('900 12px Orbitron'), ph: !!window.__phDone, lod: !!V.STATE.ferrariLOD, twOK: getComputedStyle(document.getElementById('pill-quality')).borderRadius}})()""")
        reg = await page.evaluate("navigator.serviceWorker.getRegistration().then(r => r ? (r.active ? 'active' : 'installing') : 'none')")
        st['swReg'] = reg
        await page.screenshot(path='/home/claude/game/pwa_shot.png', timeout=120000)
        print(json.dumps(st)); print('external requests blocked:', external[:10]); print('\n'.join(logs[-15:]))
        await b.close()
asyncio.run(main())
