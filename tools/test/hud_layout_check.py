"""Run with a local game server: python3 tools/test/hud_layout_check.py http://127.0.0.1:8765.
Requires Playwright + Chromium. Optional CHROMIUM_BIN points to a system browser.
Screenshots go to a temporary directory. This verifies browser layout, not real-device FPS.
"""
import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path
from playwright.async_api import async_playwright

VIEWPORTS = [(1280, 800), (1024, 768), (960, 540), (915, 412), (844, 390), (800, 360), (667, 375), (568, 320), (640, 480), (540, 768), (412, 915)]
SEED = {"cash": 12345, "owned": ["lexuslc500"], "jumps": {"0": 50}, "deliveries": 7,
        "upgrade": 3, "collectedCrates": [0], "rewardCooldowns": {}}

async def layout(page, width, height):
    return await page.evaluate("""({width,height}) => {
        function box(id) {
            const e=document.getElementById(id), r=e.getBoundingClientRect();
            return {id,x:r.x,y:r.y,w:r.width,h:r.height,right:r.right,bottom:r.bottom};
        }
        const overlap=(a,b)=>Math.min(a.right,b.right)-Math.max(a.x,b.x)>1 && Math.min(a.bottom,b.bottom)-Math.max(a.y,b.y)>1;
        const buttons=['radar-container','btn-steer-left','btn-steer-right','btn-horn','btn-car-action','btn-drive-gas','btn-drive-brake','btn-drive-nitro','btn-drive-drift'].map(box);
        const regions=['radar-container','status-card','pursuit-hud-panel','mission-panel','center-banner','steering-controls','action-controls'].map(box);
        const errors=[];
        for(const b of buttons) {
            if(b.w<43.9 || b.h<43.9) errors.push('small touch target: '+b.id);
            if(b.x<0 || b.y<0 || b.right>width+1 || b.bottom>height+1) errors.push('outside viewport: '+b.id);
        }
        for(let i=0;i<buttons.length;i++)for(let j=i+1;j<buttons.length;j++)if(overlap(buttons[i],buttons[j]))errors.push('overlapping buttons: '+buttons[i].id+'/'+buttons[j].id);
        for(let i=0;i<regions.length;i++)for(let j=i+1;j<regions.length;j++)if(overlap(regions[i],regions[j]))errors.push('overlapping HUD: '+regions[i].id+'/'+regions[j].id);
        if(document.documentElement.scrollWidth>width)errors.push('horizontal scrolling');
        const left=box('steering-controls'),right=box('action-controls');
        const corridor=(right.x-left.right)/width;
        if(width>=800 && width>height && corridor<.55)errors.push('central corridor below 55%');
        const radar=box('radar-container'),gas=box('btn-drive-gas'),brake=box('btn-drive-brake');
        if(width>=960 && height>=560 && width>height) {
            if(radar.w<112 || radar.w>128)errors.push('tablet radar size');
            if(gas.w!==64 || gas.h!==118 || brake.w!==64 || brake.h!==100)errors.push('tablet pedal dimensions');
        }
        const canvas=document.getElementById('radar-canvas');
        if(canvas.width!==140 || canvas.height!==140)errors.push('radar backing size changed');
        return {errors,corridor,buttons,regions};
    }""", {"width": width, "height": height})

async def main():
    url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8765"
    output = Path(tempfile.mkdtemp(prefix="vh-hud-layout-"))
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path=os.getenv("CHROMIUM_BIN"), args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        context = await browser.new_context(viewport={"width": 1280, "height": 800}, has_touch=True, is_mobile=True)
        await context.add_init_script("localStorage.setItem('vh_save', " + json.dumps(json.dumps(SEED)) + ");")
        page = await context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        await page.goto(url, wait_until="domcontentloaded", timeout=120000)
        await page.wait_for_function("window.__VH && __VH.PLAYER.group", timeout=120000)
        await page.evaluate("""() => {
            __VH.STATE.pauseRender=true;
            document.getElementById('touch-controls').classList.remove('hidden');
            __VH.toggleEnterExitCar();
            __VH.updateCameraAndLights(1/60);
        }""")
        # UI only: hold the simulation still so matrix screenshots and measurements are deterministic.
        assert not await page.locator("#hud-stars").is_visible()
        for width, height in VIEWPORTS:
            await page.set_viewport_size({"width": width, "height": height})
            for language in ["zh-TW", "en"]:
                await page.evaluate("""language => {
                    const en=language==='en';
                    document.getElementById('btn-drive-gas').querySelector('.vh-lbl').textContent=en?'GAS':'油門';
                    document.getElementById('btn-drive-brake').querySelector('.vh-lbl').textContent=en?'BRAKE':'煞車';
                    document.getElementById('btn-car-action-label').textContent=en?'Enter / exit vehicle':'上車／下車／召喚車輛';
                    document.getElementById('mission-panel').classList.remove('hidden');
                    document.getElementById('mission-title').textContent=en?'Airport stunt challenge':'機場飛躍挑戰';
                    document.getElementById('mission-progress').textContent='1.2 km • $2,150';
                    document.getElementById('mission-timer').textContent='3:42';
                    document.getElementById('wanted-badge').classList.remove('hidden');
                    document.getElementById('pursuit-hud-panel').classList.remove('hidden');
                    document.getElementById('pursuit-status-label').textContent=en?'Escaping pursuit (105 m)':'正在擺脫警方追捕';
                    document.getElementById('banner-title').textContent=en?'Delivery complete':'配送完成';
                    document.getElementById('banner-sub').textContent=en?'+$1,720 early bonus':'+$1,720 提早送達獎勵';
                }""", language)
                result = await layout(page, width, height)
                assert not result["errors"], (width, height, language, result)
                await page.screenshot(path=str(output / f"hud-{width}x{height}-{language}.png"))
                print(json.dumps({"viewport": [width, height], "labels": language, "corridor": result["corridor"], "result": "PASS"}), flush=True)
            await page.locator("#radar-container").click()
            assert await page.locator("#quick-actions").is_visible()
            for id_ in ["pill-quality", "pill-mission", "pill-garage", "pill-cop-chase", "pill-radio", "pill-cam", "pill-sky", "pill-settings", "quick-actions-map"]:
                button = page.locator("#" + id_)
                await button.scroll_into_view_if_needed()
                box = await button.bounding_box()
                assert box and box["width"] >= 44 and box["height"] >= 44, id_
            await page.locator("#quick-actions-close").click()
            assert not await page.locator("#quick-actions").is_visible()

        for button, modal in [("pill-mission", "missions-modal"), ("pill-garage", "garage-modal"), ("pill-settings", "settings-modal"), ("quick-actions-map", "world-map")]:
            await page.locator("#radar-container").click()
            await page.locator("#" + button).click()
            assert await page.locator("#" + modal).is_visible()
            assert not await page.locator("#quick-actions").is_visible()
            close = {"missions-modal": "close-missions-btn", "garage-modal": "close-garage-btn", "settings-modal": "close-settings-btn", "world-map": "wm-close"}[modal]
            await page.locator("#" + close).click()

        # Synthetic pointer events test wiring, not a physical multitouch device.
        await page.locator("#btn-drive-gas").dispatch_event("pointerdown", {"pointerId": 1, "pointerType": "touch"})
        await page.locator("#btn-steer-left").dispatch_event("pointerdown", {"pointerId": 2, "pointerType": "touch"})
        assert await page.evaluate("__VH.INPUT.forward && __VH.INPUT.left")
        await page.set_viewport_size({"width": 800, "height": 360})
        assert await page.evaluate("!__VH.INPUT.forward && !__VH.INPUT.left")
        assert await page.evaluate("__VH.SAVE.cash === 12345 && __VH.SAVE.owned.includes('lexuslc500') && __VH.SAVE.deliveries === 7")
        assert not errors, errors
        print("RESULT: PASS (browser layout and synthetic input; no real-device performance measurement)")
        print("Screenshots:", output)
        await browser.close()

asyncio.run(main())
