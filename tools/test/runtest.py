import asyncio, sys, json, time
from playwright.async_api import async_playwright
# usage: runtest.py URL outpng seconds [mobile] [script]
url, out, secs = sys.argv[1], sys.argv[2], float(sys.argv[3])
mobile = len(sys.argv) > 4 and sys.argv[4] == 'mobile'
script = sys.argv[5] if len(sys.argv) > 5 else None
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist','--autoplay-policy=no-user-gesture-required'])
        if mobile:
            ctx = await b.new_context(viewport={'width':915,'height':412}, device_scale_factor=2, is_mobile=True, has_touch=True,
                user_agent='Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Mobile Safari/537.36')
        else:
            ctx = await b.new_context(viewport={'width':960,'height':540})
        page = await ctx.new_page()
        logs = []
        page.on('console', lambda m: logs.append(f'[{m.type}] {m.text}'[:400]))
        page.on('pageerror', lambda e: logs.append(f'[PAGEERROR] {e}'[:600]))
        page.on('requestfailed', lambda r: logs.append(f'[REQFAIL] {r.url[:120]} {r.failure}'))
        await page.goto(url, wait_until='load', timeout=90000)
        await page.wait_for_timeout(int(secs*1000))
        if script:
            res = await page.evaluate(open(script).read())
            logs.append('[SCRIPT] ' + json.dumps(res)[:3000])
        print('\n'.join(logs[-80:]), flush=True)
        fps = await page.evaluate('''() => new Promise(r=>{let n=0;const t0=performance.now();function f(){n++; if(performance.now()-t0<3000) requestAnimationFrame(f); else r(n/3);} requestAnimationFrame(f);})''')
        print('[FPS approx]', round(fps,1), flush=True)
        try:
            await page.screenshot(path=out, timeout=120000)
        except Exception as e:
            print('[SHOTFAIL]', str(e)[:200])
        await b.close()
asyncio.run(main())
