#!/usr/bin/env python3
"""T-014B2 real-Chrome Playwright WebGL regression & mutation test.

Implements specs/T-014B2-spec-v1.2.md §§2, 2A, 3, 4, 6 against the production
index.html (Site A shared 1024^2 RGBA8 Canvas atlas + 512^2 true GPU R8 night
window mask + custom .r shader sampling + ?showcase=0/1/default).

All measurements collected here are HEADLESS Chrome/SwiftShader measurements,
NOT real-device FPS.
"""
import argparse
import functools
import http.server
import json
import math
import shutil
import statistics
import sys
import threading
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
MAX_GPU_MIP_BYTES = 5_947_392
MAX_INIT_MEDIAN_MS = 12.0
GL_R8 = 33321
GL_RGBA8 = 32856
GL_SRGB8_ALPHA8 = 35907

INIT_SCRIPT = """([device, quality]) => {
    let seed = 5019;
    Math.random = () => ((seed = (Math.imul(1664525, seed) + 1013904223) >>> 0) / 4294967296);
    localStorage.setItem('vh_settings', JSON.stringify({ qualityDevice: device, quality }));
    const raf = window.requestAnimationFrame.bind(window);
    window.requestAnimationFrame = fn => (fn && fn.name === 'animate') ? 0 : raf(fn);

    window.__vhGlLog = { texStorage2D: [], texImage2D: [], generateMipmap: 0 };
    if (window.WebGL2RenderingContext) {
        const proto = window.WebGL2RenderingContext.prototype;
        const origStorage = proto.texStorage2D;
        proto.texStorage2D = function(target, levels, internalformat, width, height) {
            window.__vhGlLog.texStorage2D.push({ target, levels, internalformat, width, height });
            return origStorage.apply(this, arguments);
        };
        const origImg = proto.texImage2D;
        proto.texImage2D = function(target, level, internalformat, width, height) {
            if (typeof width === 'number' && typeof height === 'number') {
                window.__vhGlLog.texImage2D.push({ target, level, internalformat, width, height });
            }
            return origImg.apply(this, arguments);
        };
        const origMip = proto.generateMipmap;
        proto.generateMipmap = function(target) {
            window.__vhGlLog.generateMipmap++;
            return origMip.apply(this, arguments);
        };
    }
    if (device === 'DESKTOP') {
        for (const api of [window.WebGLRenderingContext, window.WebGL2RenderingContext]) {
            if (!api) continue;
            const get = api.prototype.getParameter;
            api.prototype.getParameter = function(p) {
                return p === 37446 ? 'Test RTX discrete GPU' : get.call(this, p);
            };
        }
    }
}"""


def mip_chain_bytes(width: int, height: int, bpp: int, levels: int) -> int:
    total = 0
    w, h = width, height
    for _ in range(levels):
        total += w * h * bpp
        w = max(1, w // 2)
        h = max(1, h // 2)
    return total


def expect_red(name: str, fn):
    failed = False
    err_msg = ""
    try:
        fn()
    except AssertionError as exc:
        failed = True
        err_msg = str(exc)
    if not failed:
        raise AssertionError(f"MUTATION MUST TURN RED but stayed GREEN: {name}")
    print(f"  [MUTATION RED] {name} -> {err_msg}", flush=True)


def open_game_page(browser, url: str, preset: str, query: str = ""):
    device, quality = preset.split("_")
    mobile = device == "PHONE"
    vp = {"width": 800, "height": 450}
    opts = dict(
        viewport=vp,
        screen=vp,
        device_scale_factor=1,
        is_mobile=mobile,
        has_touch=mobile,
        service_workers="block",
    )
    if mobile:
        opts["user_agent"] = (
            "Mozilla/5.0 (Linux; Android 14; Mobile) AppleWebKit/537.36 "
            "Chrome/130.0 Mobile Safari/537.36"
        )
    ctx = browser.new_context(**opts)
    ctx.add_init_script(f"({INIT_SCRIPT})({json.dumps([device, quality])})")
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(url + "/index.html" + query, wait_until="domcontentloaded", timeout=120000)
    page.wait_for_function(
        "window.__VH && window.__VH.WORLD && window.__VH.WORLD.showcaseSiteA && window.__VH.WORLD.showcaseSiteA.atlas",
        timeout=120000,
    )
    return ctx, page, errors


def collect_atlas_snapshot(page):
    return page.evaluate("""() => {
        const { WORLD, THREE, renderer, scene, camera } = window.__VH;
        const sc = WORLD.showcaseSiteA;
        const at = sc.atlas;
        const atlasTex = at.atlasTexture;
        const maskTex = at.maskTexture;
        const matA = sc.materials[0], matB = sc.materials[1];
        const nonFacadeMaps = sc.materials.slice(2).map(m => ({
            map: m.map !== null, emissiveMap: m.emissiveMap !== null,
            normalMap: m.normalMap !== null, roughnessMap: m.roughnessMap !== null
        }));
        // Render Site A once so WebGL2 uploads & compiles both textures and shader
        const th = window.__VH.__th(-501, -790);
        camera.position.set(-501, th + 10, -790);
        camera.lookAt(-528, th + 6, -777);
        camera.updateMatrixWorld();
        renderer.render(scene, camera);

        // Inspect compiled fragment shader source for .r sampling on uFacadeMask
        const gl = renderer.getContext();
        const progSources = (renderer.info.programs || []).map(p => {
            try {
                const shaders = gl.getAttachedShaders(p.program) || [];
                return shaders.map(s => gl.getShaderSource(s) || '').join('\\n');
            } catch (e) { return ''; }
        }).filter(s => s.includes('uFacadeMask'));

        // Inspect R8 mask pane dimensions, gutters, roofCap zero-check
        const md = maskTex.image.data;
        const W = maskTex.image.width, H = maskTex.image.height;
        const allPanes = [...at.islands.A.panes, ...at.islands.B.panes];
        let minPaneW = 999, minPaneH = 999, gutterViolations = 0, badValues = 0;
        const allowed = new Set([0, 85, 170, 255]);
        for (let i = 0; i < md.length; i++) { if (!allowed.has(md[i])) badValues++; }
        for (const p of allPanes) {
            const [x0, y0, x1, y1] = p.maskRect;
            minPaneW = Math.min(minPaneW, x1 - x0);
            minPaneH = Math.min(minPaneH, y1 - y0);
            // Check 1-texel dark border around each pane (gutter >= 1 dark texel)
            for (let x = x0; x < x1; x++) {
                if (y0 > 0 && md[(y0 - 1) * W + x] !== 0) gutterViolations++;
                if (y1 < H && md[y1 * W + x] !== 0) gutterViolations++;
            }
            for (let y = y0; y < y1; y++) {
                if (x0 > 0 && md[y * W + (x0 - 1)] !== 0) gutterViolations++;
                if (x1 < W && md[y * W + x1] !== 0) gutterViolations++;
            }
        }
        // Check roofCap area in mask (y >= 472) is strictly 0
        let roofMaskNonZero = 0;
        for (let y = 472; y < H; y++) {
            for (let x = 0; x < W; x++) if (md[y * W + x] !== 0) roofMaskNonZero++;
        }
        // Count distinct texture objects referenced by all 5 Site A materials
        const texSet = new Set();
        for (const m of sc.materials) {
            for (const f of ['map', 'emissiveMap', 'normalMap', 'roughnessMap', 'metalnessMap', 'aoMap', 'alphaMap', 'bumpMap']) {
                if (m[f]) texSet.add(m[f].uuid);
            }
        }
        texSet.add(at.uniforms.uFacadeMask.value.uuid);

        return {
            seed: at.seed,
            hasIslandsAB: Boolean(at.islands && at.islands.A && at.islands.B),
            atlasIsCanvas: Boolean(atlasTex && atlasTex.isCanvasTexture),
            atlasW: atlasTex.image.width, atlasH: atlasTex.image.height,
            atlasColorSpace: atlasTex.colorSpace, atlasFlipY: atlasTex.flipY,
            atlasMips: atlasTex.generateMipmaps,
            maskIsData: Boolean(maskTex && maskTex.isDataTexture),
            maskW: W, maskH: H,
            maskFormat: maskTex.format, maskType: maskTex.type,
            maskColorSpace: maskTex.colorSpace, maskFlipY: maskTex.flipY,
            maskUnpack: maskTex.unpackAlignment, maskMips: maskTex.generateMipmaps,
            expectedRedFormat: THREE.RedFormat, expectedUByte: THREE.UnsignedByteType,
            expectedSRGB: THREE.SRGBColorSpace, expectedNoCS: THREE.NoColorSpace,
            sharedAtlas: matA.map === atlasTex && matB.map === atlasTex,
            nonFacadeMaps,
            distinctSiteATextures: texSet.size,
            glStorage: window.__vhGlLog.texStorage2D,
            glMipCalls: window.__vhGlLog.generateMipmap,
            shaderCountWithMask: progSources.length,
            shaderSamplesR: progSources.some(s => /texture2D\\s*\\(\\s*uFacadeMask\\s*,\\s*vMapUv\\s*\\)\\.r/.test(s)),
            shaderSamplesWrongChannel: progSources.some(s => /texture2D\\s*\\(\\s*uFacadeMask\\s*,\\s*vMapUv\\s*\\)\\.[gba]/.test(s)),
            minPaneW, minPaneH, gutterViolations, badValues, roofMaskNonZero
        };
    }""")


def assert_b2_atlas(snap):
    assert snap["hasIslandsAB"], "B2-ATLAS: missing WORLD.showcaseSiteA.atlas.islands.{A,B}"
    assert isinstance(snap["seed"], int) and snap["seed"] > 0, "B2-ATLAS: missing deterministic seed"
    assert snap["atlasIsCanvas"] and snap["atlasW"] == 1024 and snap["atlasH"] == 1024, "B2-ATLAS: atlas must be 1024x1024 CanvasTexture"
    assert snap["atlasColorSpace"] == snap["expectedSRGB"], "B2-ATLAS: atlas colorSpace must be SRGBColorSpace"
    assert snap["atlasFlipY"] is False and snap["atlasMips"] is True, "B2-ATLAS: atlas flipY=false + mipmaps required"
    assert snap["maskIsData"] and snap["maskW"] == 512 and snap["maskH"] == 512, "B2-ATLAS: mask must be 512x512 DataTexture"
    assert snap["maskFormat"] == snap["expectedRedFormat"], f"B2-ATLAS: mask format must be RedFormat, got {snap['maskFormat']}"
    assert snap["maskType"] == snap["expectedUByte"], "B2-ATLAS: mask type must be UnsignedByteType"
    assert snap["maskColorSpace"] == snap["expectedNoCS"], "B2-ATLAS: mask colorSpace must be NoColorSpace"
    assert snap["maskFlipY"] is False and snap["maskUnpack"] == 1 and snap["maskMips"] is True, "B2-ATLAS: mask flipY=false, unpackAlignment=1, mipmaps required"
    assert snap["sharedAtlas"], "B2-ATLAS: Building A & B shell materials must share the same atlasTexture"
    assert snap["distinctSiteATextures"] <= 2, f"B2-ATLAS: Site A texture count {snap['distinctSiteATextures']} > 2"
    for nf in snap["nonFacadeMaps"]:
        assert not any(nf.values()), f"B2-ATLAS: non-facade material carries unexpected texture {nf}"

    # Verify ACTUAL WebGL2 GPU texStorage2D allocations (true R8 = 33321 + 1024^2 RGBA8/SRGB8_ALPHA8)
    r8_allocs = [s for s in snap["glStorage"] if s["internalformat"] == GL_R8 and s["width"] == 512 and s["height"] == 512]
    assert r8_allocs, f"B2-ATLAS: GPU texStorage2D did not allocate true R8 (33321) 512x512! Saw: {snap['glStorage']}"
    assert any(s["levels"] >= 10 for s in r8_allocs), f"B2-ATLAS: GPU R8 mask missing mip chain (levels < 10): {r8_allocs}"
    atlas_allocs = [
        s for s in snap["glStorage"]
        if s["internalformat"] in (GL_RGBA8, GL_SRGB8_ALPHA8) and s["width"] == 1024 and s["height"] == 1024
    ]
    assert atlas_allocs, f"B2-ATLAS: GPU texStorage2D did not allocate 1024x1024 RGBA8/SRGB8_ALPHA8 atlas"
    assert any(s["levels"] >= 11 for s in atlas_allocs), f"B2-ATLAS: GPU atlas missing mip chain: {atlas_allocs}"
    assert snap["glMipCalls"] >= 2, "B2-ATLAS: generateMipmap not invoked for atlas + R8 mask"

    total_bytes = mip_chain_bytes(1024, 1024, 4, 11) + mip_chain_bytes(512, 512, 1, 10)
    assert total_bytes <= MAX_GPU_MIP_BYTES, f"B2-ATLAS: GPU mip bytes {total_bytes} > {MAX_GPU_MIP_BYTES}"

    assert snap["shaderCountWithMask"] >= 1 and snap["shaderSamplesR"] and not snap["shaderSamplesWrongChannel"], (
        "B2-ATLAS: custom facade shader must sample uFacadeMask strictly via .r channel"
    )
    assert snap["minPaneW"] >= 4 and snap["minPaneH"] >= 4, f"B2-ATLAS: mask pane smaller than 4x4 ({snap['minPaneW']}x{snap['minPaneH']})"
    assert snap["gutterViolations"] == 0, f"B2-ATLAS: found {snap['gutterViolations']} dark-gutter violations between panes"
    assert snap["badValues"] == 0, f"B2-ATLAS: unexpected mask byte values ({snap['badValues']})"
    assert snap["roofMaskNonZero"] == 0, f"B2-ATLAS: non-zero mask pixels in roofCap region ({snap['roofMaskNonZero']})"
    return total_bytes


def measure_gpu_window_levels(page, sky_preset_idx: int):
    return page.evaluate("""(presetIdx) => {
        const { WORLD, THREE, renderer, scene, camera, applySkyPreset, __th } = window.__VH;
        applySkyPreset(presetIdx);
        const sc = WORLD.showcaseSiteA;
        const at = sc.atlas;
        const gl = renderer.getContext();
        const W = gl.drawingBufferWidth, H = gl.drawingBufferHeight;

        const sampleAtPose = (camPos, lookAt, samples) => {
            camera.position.set(camPos[0], camPos[1], camPos[2]);
            camera.lookAt(lookAt[0], lookAt[1], lookAt[2]);
            camera.updateMatrixWorld();
            camera.updateProjectionMatrix();
            renderer.setRenderTarget(null);
            renderer.render(scene, camera);

            const out = {};
            const v = new THREE.Vector3();
            const px = new Uint8Array(4 * 9);
            for (const key of ['dark', 'level1', 'level2', 'level3']) {
                const list = samples[key] || [];
                const lumas = [];
                for (const s of list) {
                    v.set(s.world[0], s.world[1], s.world[2]);
                    v.project(camera);
                    if (v.z < -1 || v.z > 1 || Math.abs(v.x) > 0.96 || Math.abs(v.y) > 0.96) continue;
                    const cx = Math.max(1, Math.min(W - 2, Math.round((v.x * 0.5 + 0.5) * W)));
                    const cy = Math.max(1, Math.min(H - 2, Math.round((v.y * 0.5 + 0.5) * H)));
                    gl.readPixels(cx - 1, cy - 1, 3, 3, gl.RGBA, gl.UNSIGNED_BYTE, px);
                    // Read center 3x3 average luminance
                    let sum = 0;
                    for (let i = 0; i < 9; i++) sum += 0.299 * px[i * 4] + 0.587 * px[i * 4 + 1] + 0.114 * px[i * 4 + 2];
                    lumas.push(sum / 9);
                }
                out[key] = { count: lumas.length, lumas, median: lumas.length ? lumas.slice().sort((a, b) => a - b)[Math.floor(lumas.length / 2)] : null };
            }
            return out;
        };

        const yA = sc.footprints.buildingA.baseY;
        const yB = sc.footprints.buildingB.baseY;
        // Direct street-facing cameras clearly framing South facade of A (z=-777) and North+Arc of B (z=-803)
        const resA = sampleAtPose([-528, yA + 5.0, -792], [-528, yA + 4.5, -777], at.islands.A.samples);
        const resB = sampleAtPose([-473, yB + 10.5, -782], [-473, yB + 10.0, -803], at.islands.B.samples);
        return { presetIdx, nightUniform: at.uniforms.uFacadeNight.value, A: resA, B: resB };
    }""", sky_preset_idx)


def assert_b2_night(day_read, night_read):
    assert day_read["nightUniform"] == 0, f"B2-NIGHT: daytime uFacadeNight != 0 ({day_read['nightUniform']})"
    assert night_read["nightUniform"] == 1, f"B2-NIGHT: nighttime uFacadeNight != 1 ({night_read['nightUniform']})"
    for bld in ("A", "B"):
        nr = night_read[bld]
        dr = day_read[bld]
        for k in ("dark", "level1", "level2", "level3"):
            assert nr[k]["count"] >= 1 and nr[k]["median"] is not None, f"B2-NIGHT: {bld} missing visible GPU readback for {k}"
        d, l1, l2, l3 = nr["dark"]["median"], nr["level1"]["median"], nr["level2"]["median"], nr["level3"]["median"]
        assert d < 75, f"B2-NIGHT: {bld} dark window too bright at night (luma={d:.1f})"
        assert l1 - d >= 20, f"B2-NIGHT: {bld} level1 ({l1:.1f}) not clearly brighter than dark ({d:.1f})"
        assert l2 - l1 >= 15, f"B2-NIGHT: {bld} level2 ({l2:.1f}) not separable from level1 ({l1:.1f})"
        assert l3 - l2 >= 10, f"B2-NIGHT: {bld} level3 ({l3:.1f}) not separable from level2 ({l2:.1f})"
        # Daytime emissive off: daytime level3 must NOT glow far brighter than daytime dark glass
        dd, dl3 = dr["dark"]["median"], dr["level3"]["median"]
        assert abs(dl3 - dd) < 35, f"B2-NIGHT: {bld} daytime windows show unexpected emissive spread (dark={dd:.1f}, lvl3={dl3:.1f})"


def collect_art_and_uv_metrics(page):
    return page.evaluate("""() => {
        const { WORLD } = window.__VH;
        const sc = WORLD.showcaseSiteA;
        const at = sc.atlas;
        const ctx = at.atlasTexture.image.getContext('2d');
        const img = ctx.getImageData(0, 0, 1024, 1024).data;
        const md = at.maskTexture.image.data;

        const rectStats = (x0, y0, x1, y1) => {
            let n = 0, sR = 0, sG = 0, sB = 0, sL = 0, sL2 = 0, hEdge = 0, vEdge = 0;
            for (let y = y0; y < y1; y++) {
                for (let x = x0; x < x1; x++) {
                    const idx = (y * 1024 + x) * 4;
                    const r = img[idx], g = img[idx + 1], b = img[idx + 2];
                    const l = 0.299 * r + 0.587 * g + 0.114 * b;
                    sR += r; sG += g; sB += b; sL += l; sL2 += l * l; n++;
                    if (x > x0) {
                        const p = idx - 4;
                        const pl = 0.299 * img[p] + 0.587 * img[p + 1] + 0.114 * img[p + 2];
                        hEdge += Math.abs(l - pl);
                    }
                    if (y > y0) {
                        const p = idx - 1024 * 4;
                        const pl = 0.299 * img[p] + 0.587 * img[p + 1] + 0.114 * img[p + 2];
                        vEdge += Math.abs(l - pl);
                    }
                }
            }
            const meanL = sL / n;
            return {
                meanR: sR / n, meanG: sG / n, meanB: sB / n,
                meanL, stdL: Math.sqrt(Math.max(0, sL2 / n - meanL * meanL)),
                hEdge: hEdge / n, vEdge: vEdge / n
            };
        };

        // Compare pixel difference between A upperBase (16..996, 232..358) and B office (16..996, 552..678)
        let abDiffSum = 0, abCount = 0;
        for (let dy = 0; dy < 120; dy += 2) {
            for (let dx = 0; dx < 960; dx += 2) {
                const iA = ((232 + dy) * 1024 + (16 + dx)) * 4;
                const iB = ((552 + dy) * 1024 + (16 + dx)) * 4;
                const lA = 0.299 * img[iA] + 0.587 * img[iA + 1] + 0.114 * img[iA + 2];
                const lB = 0.299 * img[iB] + 0.587 * img[iB + 1] + 0.114 * img[iB + 2];
                abDiffSum += Math.abs(lA - lB);
                abCount++;
            }
        }

        // Pane geometry & night-distribution metrics
        const panesA = at.islands.A.panes;
        const aGround = panesA.filter(p => p.band === 'ground');
        const aUpper = panesA.filter(p => p.band === 'upperBase');
        const avgDim = (arr, k) => arr.reduce((s, p) => s + (p.maskRect[k + 2] - p.maskRect[k]), 0) / Math.max(1, arr.length);
        const panesB = at.islands.B.panes;
        const bOffice = panesB.filter(p => p.band === 'office');
        const bFloorHetero = [];
        for (let fl = 1; fl <= 5; fl++) {
            const fp = bOffice.filter(p => p.floor === fl).sort((a, b) => a.module - b.module);
            const hasDark = fp.some(p => p.maskByte === 0);
            const hasLit = fp.some(p => p.maskByte > 0);
            let adjTransitions = 0;
            for (let i = 1; i < fp.length; i++) {
                if ((fp[i - 1].maskByte === 0) !== (fp[i].maskByte === 0)) adjTransitions++;
            }
            bFloorHetero.push({ floor: fl, count: fp.length, hasDark, hasLit, adjTransitions });
        }

        // UV geometry verification for Building A and Building B
        const checkGeoUV = (mesh, roofCap) => {
            const pos = mesh.geometry.attributes.position;
            const norm = mesh.geometry.attributes.normal;
            const uv = mesh.geometry.attributes.uv;
            if (!uv || uv.count !== pos.count) return { ok: false, reason: 'missing uv' };
            let nanCount = 0, outOfRange = 0, wallTris = 0, wallZeroArea = 0, capTris = 0, capBleed = 0;
            for (let i = 0; i < uv.count; i++) {
                const u = uv.getX(i), v = uv.getY(i);
                if (!Number.isFinite(u) || !Number.isFinite(v)) nanCount++;
                else if (u < 0 || u > 1 || v < 0 || v > 1) outOfRange++;
            }
            for (let i = 0; i < pos.count; i += 3) {
                const ny = (norm.getY(i) + norm.getY(i + 1) + norm.getY(i + 2)) / 3;
                const u0 = uv.getX(i), v0 = uv.getY(i), u1 = uv.getX(i + 1), v1 = uv.getY(i + 1), u2 = uv.getX(i + 2), v2 = uv.getY(i + 2);
                const area = Math.abs((u1 - u0) * (v2 - v0) - (u2 - u0) * (v1 - v0)) * 0.5;
                if (Math.abs(ny) < 0.5) {
                    wallTris++;
                    if (area < 1e-9) wallZeroArea++;
                } else {
                    capTris++;
                    for (const [uu, vv] of [[u0, v0], [u1, v1], [u2, v2]]) {
                        const mx = Math.max(0, Math.min(511, Math.floor(uu * 512)));
                        const my = Math.max(0, Math.min(511, Math.floor(vv * 512)));
                        if (uu < roofCap.u0 - 1e-5 || uu > roofCap.u1 + 1e-5 || vv < roofCap.v0 - 1e-5 || vv > roofCap.v1 + 1e-5 || md[my * 512 + mx] !== 0) {
                            capBleed++;
                        }
                    }
                }
            }
            return { ok: true, nanCount, outOfRange, wallTris, wallZeroArea, capTris, capBleed };
        };

        // Building B 10-segment NW arc UV continuity & monotonicity check
        const bPos = sc.meshes.buildingBShell.geometry.attributes.position;
        const bNorm = sc.meshes.buildingBShell.geometry.attributes.normal;
        const bUv = sc.meshes.buildingBShell.geometry.attributes.uv;
        const yB = sc.footprints.buildingB.baseY;
        const arcVerts = new Map();
        for (let i = 0; i < bPos.count; i++) {
            const x = bPos.getX(i), y = bPos.getY(i), z = bPos.getZ(i), ny = bNorm.getY(i);
            if (Math.abs(ny) > 0.5 || Math.abs(y - yB) > 1e-3) continue;
            if (x <= -480 + 1e-3 && z >= -807 - 1e-3 && Math.abs(Math.hypot(x + 480, z + 807) - 4.0) < 0.03) {
                const ang = Math.atan2(z + 807, x + 480);
                const key = Math.round(ang * 10000);
                if (!arcVerts.has(key)) arcVerts.set(key, { ang, u: bUv.getX(i), v: bUv.getY(i) });
            }
        }
        const sortedArc = [...arcVerts.values()].sort((a, b) => a.ang - b.ang);
        const arcDu = [];
        for (let i = 1; i < sortedArc.length; i++) arcDu.push(sortedArc[i - 1].u - sortedArc[i].u);

        return {
            artA: {
                groundStats: rectStats(16, 358, 1008, 448),
                upperStats: rectStats(16, 232, 1008, 358),
                groundPaneCount: aGround.length,
                upperPaneCount: aUpper.length,
                groundAvgW: avgDim(aGround, 0),
                groundAvgH: avgDim(aGround, 1),
                upperAvgW: avgDim(aUpper, 0),
                upperAvgH: avgDim(aUpper, 1),
                groundLevels: [...new Set(aGround.map(p => p.maskByte))].sort((a, b) => a - b),
                upperLevels: [...new Set(aUpper.map(p => p.maskByte))].sort((a, b) => a - b),
                allLevels: [...new Set(panesA.map(p => p.maskByte))].sort((a, b) => a - b),
                segCoverage: [...new Set(panesA.map(p => p.segIndex))].sort((a, b) => a - b)
            },
            artB: {
                officeStats: rectStats(16, 552, 996, 852),
                lobbyStats: rectStats(16, 852, 996, 944),
                abMeanLumaDiff: abDiffSum / abCount,
                officePaneCount: bOffice.length,
                officeAvgW: avgDim(bOffice, 0),
                officeAvgH: avgDim(bOffice, 1),
                floorHetero: bFloorHetero,
                allLevels: [...new Set(panesB.map(p => p.maskByte))].sort((a, b) => a - b)
            },
            uvA: checkGeoUV(sc.meshes.buildingAShell, at.islands.roofCap.uvBounds),
            uvB: checkGeoUV(sc.meshes.buildingBShell, at.islands.roofCap.uvBounds),
            arcPointCount: sortedArc.length,
            arcDu
        };
    }""")


def assert_b2_art_a(m):
    a = m["artA"]
    assert a["groundStats"]["stdL"] >= 15, f"B2-ART-A: ground storefront too flat (stdL={a['groundStats']['stdL']:.1f})"
    assert a["upperStats"]["stdL"] >= 15, f"B2-ART-A: upper facade too flat (stdL={a['upperStats']['stdL']:.1f})"
    assert a["groundPaneCount"] >= 10 and a["upperPaneCount"] >= 20, "B2-ART-A: insufficient commercial panes"
    assert a["groundAvgW"] > a["upperAvgW"] * 1.4, (
        f"B2-ART-A: ground storefront bays ({a['groundAvgW']:.1f}) must be wider than upper commercial windows ({a['upperAvgW']:.1f})"
    )
    assert a["groundAvgH"] > a["upperAvgH"] * 1.15, (
        f"B2-ART-A: ground storefront height ({a['groundAvgH']:.1f}) must exceed upper window height ({a['upperAvgH']:.1f})"
    )
    assert a["groundLevels"] == [0, 85, 170, 255], f"B2-ART-A: ground floor must have dark + 3 lit levels, got {a['groundLevels']}"
    assert a["allLevels"] == [0, 85, 170, 255], f"B2-ART-A: Building A must have 0 + 3 lit levels, got {a['allLevels']}"
    assert a["segCoverage"] == [0, 1, 2, 3, 4, 5], f"B2-ART-A: missing L-plan segments {a['segCoverage']}"


def assert_b2_art_b(m):
    b = m["artB"]
    assert b["officeStats"]["stdL"] >= 12, f"B2-ART-B: office curtain wall too flat (stdL={b['officeStats']['stdL']:.1f})"
    assert b["lobbyStats"]["stdL"] >= 12, f"B2-ART-B: office lobby too flat (stdL={b['lobbyStats']['stdL']:.1f})"
    assert b["abMeanLumaDiff"] >= 30, f"B2-ART-B: Building B too similar to Building A (luma diff={b['abMeanLumaDiff']:.1f})"
    # Structural grayscale contrast + warm-commercial vs cool-office material contrast
    a_u = m["artA"]["upperStats"]
    b_o = b["officeStats"]
    a_warm = a_u["meanR"] - a_u["meanB"]
    b_warm = b_o["meanR"] - b_o["meanB"]
    assert a_warm > b_warm + 20 and b_warm < -10, (
        f"B2-ART-B: expected distinct masonry/glass contrast between A (R-B={a_warm:.1f}) and B (R-B={b_warm:.1f})"
    )
    assert b["officePaneCount"] == 49 * 5, f"B2-ART-B: expected 245 office panes, got {b['officePaneCount']}"
    assert b["allLevels"] == [0, 85, 170, 255], f"B2-ART-B: Building B missing dark or lit levels {b['allLevels']}"
    for fl in b["floorHetero"]:
        assert fl["hasDark"] and fl["hasLit"] and fl["adjTransitions"] >= 4, (
            f"B2-ART-B: office floor {fl['floor']} is uniform or lacks adjacent lit/dark transitions: {fl}"
        )


def assert_b2_uv_a(m):
    u = m["uvA"]
    assert u["ok"], f"B2-UV-A: {u}"
    assert u["nanCount"] == 0 and u["outOfRange"] == 0, f"B2-UV-A: invalid UVs {u}"
    assert u["wallTris"] >= 24 and u["wallZeroArea"] == 0, f"B2-UV-A: degenerate wall UVs {u}"
    assert u["capTris"] >= 8 and u["capBleed"] == 0, f"B2-UV-A: window bleed onto roof/cap ({u['capBleed']})"


def assert_b2_uv_b(m):
    u = m["uvB"]
    assert u["ok"], f"B2-UV-B: {u}"
    assert u["nanCount"] == 0 and u["outOfRange"] == 0, f"B2-UV-B: invalid UVs {u}"
    assert u["wallTris"] >= 56 and u["wallZeroArea"] == 0, f"B2-UV-B: degenerate wall UVs {u}"
    assert u["capTris"] >= 20 and u["capBleed"] == 0, f"B2-UV-B: window bleed onto roof/cap ({u['capBleed']})"
    assert m["arcPointCount"] == 11, f"B2-UV-B: expected 11 arc vertices (10 segs), got {m['arcPointCount']}"
    assert len(m["arcDu"]) == 10, f"B2-UV-B: expected 10 arc UV deltas, got {len(m['arcDu'])}"
    mean_du = sum(m["arcDu"]) / len(m["arcDu"])
    assert mean_du > 0.005, f"B2-UV-B: collapsed or reversed arc UV span (mean du={mean_du})"
    for idx, du in enumerate(m["arcDu"]):
        assert du > 0 and abs(du - mean_du) / mean_du < 0.05, (
            f"B2-UV-B: non-uniform or reversed arc segment {idx} (du={du:.6f} vs mean={mean_du:.6f})"
        )


def run_daynight_repeat_budget_compat(page, frames: int):
    return page.evaluate("""(frames) => {
        const { WORLD, STATE, renderer, scene, camera, applySkyPreset, setShowcaseSiteAVisible,
                applyShowcaseFacades, buildShowcaseFacadeMaps, physicsWorld, ROAD_NET, SAVE,
                VH_I18N, fastTravelTo, teleportTo, __th } = window.__VH;
        const sc = WORLD.showcaseSiteA;
        const at = sc.atlas;
        const yA = sc.footprints.buildingA.baseY;
        const gl = renderer.getContext();
        const W = gl.drawingBufferWidth, H = gl.drawingBufferHeight;

        // Helper: read one bright level3 pane & one dark pane on Building A
        const probeA = () => {
            camera.position.set(-528, yA + 5.0, -792);
            camera.lookAt(-528, yA + 4.5, -777);
            camera.updateMatrixWorld();
            renderer.setRenderTarget(null);
            renderer.render(scene, camera);
            const px = new Uint8Array(4);
            const readOne = (s) => {
                const v = new window.__VH.THREE.Vector3(s.world[0], s.world[1], s.world[2]).project(camera);
                const cx = Math.max(0, Math.min(W - 1, Math.round((v.x * 0.5 + 0.5) * W)));
                const cy = Math.max(0, Math.min(H - 1, Math.round((v.y * 0.5 + 0.5) * H)));
                gl.readPixels(cx, cy, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, px);
                return 0.299 * px[0] + 0.587 * px[1] + 0.114 * px[2];
            };
            return {
                dark: readOne(at.islands.A.samples.dark[0]),
                bright: readOne(at.islands.A.samples.level3[0])
            };
        };

        // --- B2-DAYNIGHT: 3 full Day -> Night cycles ---
        const progs0 = (renderer.info.programs || []).length;
        const matIds0 = sc.materials.map(m => m.uuid);
        const texIds0 = [at.atlasTexture.uuid, at.maskTexture.uuid];
        const cycles = [];
        for (let c = 0; c < 3; c++) {
            applySkyPreset(1); // Noon (night=0)
            const dayP = probeA();
            applySkyPreset(3); // Midnight (night=1)
            const nightP = probeA();
            cycles.push({ day: dayP, night: nightP, progs: (renderer.info.programs || []).length });
        }

        // --- B2-REPEAT: establish settled Site A state, then run 3 rounds of teleport, ON/OFF, day/night, idempotent applyShowcaseFacades ---
        teleportTo(-501, -790, 0);
        applySkyPreset(3);
        renderer.render(scene, camera);
        const sceneLen0 = scene.children.length;
        const repeatProgs0 = (renderer.info.programs || []).length;
        const memTex0 = renderer.info.memory.textures;
        const memGeo0 = renderer.info.memory.geometries;
        const bodies0 = physicsWorld.bodies.length;
        const shapes0 = physicsWorld.bodies.reduce((s, b) => s + b.shapes.length, 0);
        const geoIds0 = Object.values(sc.meshes).map(m => m.geometry.uuid);
        for (let r = 0; r < 3; r++) {
            teleportTo(-501, -790, 0);
            setShowcaseSiteAVisible(false);
            setShowcaseSiteAVisible(true);
            applySkyPreset(r % 2 === 0 ? 1 : 3);
            renderer.render(scene, camera);
            const again = applyShowcaseFacades();
            if (again !== at) throw new Error('applyShowcaseFacades not idempotent');
        }
        const repeatEnd = {
            sceneDelta: scene.children.length - sceneLen0,
            meshCount: sc.group.children.filter(c => c.isMesh).length,
            matCount: new Set(sc.materials.map(m => m.uuid)).size,
            matSame: JSON.stringify(sc.materials.map(m => m.uuid)) === JSON.stringify(matIds0),
            geoSame: JSON.stringify(Object.values(sc.meshes).map(m => m.geometry.uuid)) === JSON.stringify(geoIds0),
            texSame: at.atlasTexture.uuid === texIds0[0] && at.maskTexture.uuid === texIds0[1],
            progDelta: (renderer.info.programs || []).length - repeatProgs0,
            memTexDelta: renderer.info.memory.textures - memTex0,
            memGeoDelta: renderer.info.memory.geometries - memGeo0,
            bodyDelta: physicsWorld.bodies.length - bodies0,
            shapeDelta: physicsWorld.bodies.reduce((s, b) => s + b.shapes.length, 0) - shapes0
        };

        // --- B2-BUDGET: warm atlas+mask init median (>=5 runs), tri/shadow counts, pass-separated draw calls ---
        const warm = buildShowcaseFacadeMaps(at.seed, sc.footprints);
        warm.atlasTexture.dispose(); warm.maskTexture.dispose();
        const initRuns = [];
        for (let i = 0; i < 7; i++) {
            const b = buildShowcaseFacadeMaps(at.seed, sc.footprints);
            initRuns.push(b.initMs);
            b.atlasTexture.dispose(); b.maskTexture.dispose();
        }
        const triCount = g => (g.index ? g.index.count / 3 : g.attributes.position.count / 3);
        const tris = {
            A: triCount(sc.meshes.buildingAShell.geometry) + triCount(sc.meshes.buildingARoof.geometry),
            B: triCount(sc.meshes.buildingBShell.geometry) + triCount(sc.meshes.buildingBRoof.geometry),
            street: triCount(sc.meshes.streetAsphalt.geometry) + triCount(sc.meshes.streetSidewalks.geometry)
        };
        const shadowCasters = Object.values(sc.meshes).filter(m => m.castShadow).length;

        // Pass-separated draw calls with renderer.info.autoReset = false
        const th = __th(-501, -790);
        camera.position.set(-501, th + 24, -745);
        camera.lookAt(-501, th + 8, -795);
        camera.updateMatrixWorld();
        const measureCalls = (vis) => {
            setShowcaseSiteAVisible(vis);
            const prevAuto = renderer.info.autoReset;
            renderer.info.autoReset = false;
            const mainCalls = [], mirrorCalls = [];
            const ocean = WORLD.oceanMesh;
            const origOceanBefore = ocean ? ocean.onBeforeRender : null;
            let frameMirror = 0;
            if (ocean && origOceanBefore) {
                ocean.onBeforeRender = function(...args) {
                    const before = renderer.info.render.calls;
                    const res = origOceanBefore.apply(this, args);
                    frameMirror += Math.max(0, renderer.info.render.calls - before);
                    return res;
                };
            }
            // 2 warmup frames
            for (let w = 0; w < 2; w++) { renderer.info.reset(); renderer.render(scene, camera); }
            for (let f = 0; f < frames; f++) {
                frameMirror = 0;
                renderer.info.reset();
                renderer.render(scene, camera);
                const total = renderer.info.render.calls;
                mainCalls.push(total - frameMirror);
                mirrorCalls.push(frameMirror);
            }
            if (ocean && origOceanBefore) ocean.onBeforeRender = origOceanBefore;
            renderer.info.autoReset = prevAuto;
            return { mainCalls, mirrorCalls };
        };
        const callsOn = measureCalls(true);
        const callsOff = measureCalls(false);
        setShowcaseSiteAVisible(true);

        // Zero per-frame allocation check across 6 frames + uniform updates
        const allocBefore = {
            tex: renderer.info.memory.textures,
            geo: renderer.info.memory.geometries,
            progs: (renderer.info.programs || []).length
        };
        for (let f = 0; f < 6; f++) {
            at.uniforms.uFacadeNight.value = (f % 2);
            renderer.render(scene, camera);
        }
        const allocDelta = {
            tex: renderer.info.memory.textures - allocBefore.tex,
            geo: renderer.info.memory.geometries - allocBefore.geo,
            progs: (renderer.info.programs || []).length - allocBefore.progs
        };

        // --- B2-COMPAT ---
        const saveKeys = Object.keys(SAVE).filter(k => ['collectedCrates', 'deliveries', 'jumps', 'owned', 'rewardCooldowns'].includes(k)).sort();
        const prevLang = VH_I18N.language;
        VH_I18N.setLanguage('en'); const nameEn = VH_I18N.text('showcase_site_a');
        VH_I18N.setLanguage('zh-TW'); const nameZh = VH_I18N.text('showcase_site_a');
        VH_I18N.setLanguage(prevLang);

        return {
            cycles, repeatEnd, initRuns, startupInitMs: at.initMs, tris, shadowCasters,
            callsOn, callsOff, allocDelta,
            compat: { saveKeys, nameEn, nameZh, roadAvenues: ROAD_NET.avenuesX.length }
        };
    }""", frames)


def assert_b2_daynight_repeat_budget_compat(res):
    # B2-DAYNIGHT
    p0 = res["cycles"][0]["progs"]
    for i, cyc in enumerate(res["cycles"]):
        assert cyc["progs"] == p0, f"B2-DAYNIGHT: shader program count grew on cycle {i}: {cyc['progs']} != {p0}"
        assert cyc["night"]["bright"] - cyc["night"]["dark"] >= 50, f"B2-DAYNIGHT: cycle {i} night window not lit: {cyc['night']}"
        assert abs(cyc["day"]["bright"] - cyc["day"]["dark"]) < 35, f"B2-DAYNIGHT: cycle {i} daytime emissive leaked: {cyc['day']}"

    # B2-REPEAT
    rep = res["repeatEnd"]
    assert rep["sceneDelta"] == 0, f"B2-REPEAT: scene children grew ({rep['sceneDelta']})"
    assert rep["meshCount"] == 6, f"B2-REPEAT: mesh count != 6 ({rep['meshCount']})"
    assert rep["matCount"] == 5 and rep["matSame"], f"B2-REPEAT: material count/refs drifted ({rep})"
    assert rep["geoSame"] and rep["texSame"], f"B2-REPEAT: geometry or texture refs recreated ({rep})"
    assert rep["progDelta"] == 0 and rep["memTexDelta"] == 0 and rep["memGeoDelta"] == 0, f"B2-REPEAT: WebGL memory/program leak ({rep})"
    assert rep["bodyDelta"] == 0 and rep["shapeDelta"] == 0, f"B2-REPEAT: physics bodies/shapes drifted ({rep})"

    # B2-BUDGET
    med_init = statistics.median(res["initRuns"])
    assert med_init <= MAX_INIT_MEDIAN_MS, f"B2-BUDGET: warm atlas+mask init median {med_init:.2f}ms > {MAX_INIT_MEDIAN_MS}ms ({res['initRuns']})"
    assert res["tris"] == {"A": 136, "B": 320, "street": 64}, f"B2-BUDGET: triangle count changed from B1: {res['tris']}"
    assert res["shadowCasters"] == 0, f"B2-BUDGET: shadow casters != 0 ({res['shadowCasters']})"
    assert res["allocDelta"] == {"tex": 0, "geo": 0, "progs": 0}, f"B2-BUDGET: per-frame resource leak {res['allocDelta']}"
    med_on = statistics.median(res["callsOn"]["mainCalls"])
    med_off = statistics.median(res["callsOff"]["mainCalls"])
    med_mirror_on = statistics.median(res["callsOn"]["mirrorCalls"])
    med_mirror_off = statistics.median(res["callsOff"]["mirrorCalls"])
    delta_main = med_on - med_off
    assert 0 <= delta_main <= 6, f"B2-BUDGET: ON-OFF main-pass draw call delta {delta_main} outside [0, 6] (ON={med_on}, OFF={med_off})"

    # B2-COMPAT
    c = res["compat"]
    assert c["nameEn"] == "Showcase Site A (No Collision)", f"B2-COMPAT: EN name changed: {c['nameEn']}"
    assert c["nameZh"] == "展示區 A（無碰撞）", f"B2-COMPAT: ZH name changed: {c['nameZh']}"
    assert c["saveKeys"] == ["collectedCrates", "deliveries", "jumps", "owned", "rewardCooldowns"], f"B2-COMPAT: SAVE keys changed: {c['saveKeys']}"
    assert c["roadAvenues"] > 0, "B2-COMPAT: ROAD_NET corrupted"
    return {
        "warmInitMedianMs": round(med_init, 2),
        "warmInitRunsMs": [round(x, 2) for x in res["initRuns"]],
        "mainCallsOn": med_on,
        "mainCallsOff": med_off,
        "mainDelta": delta_main,
        "mirrorCallsOn": med_mirror_on,
        "mirrorCallsOff": med_mirror_off,
    }


def run_mutations(page, base_snap, base_dnb, day_ok):
    print("=== T-014B2 Negative Mutation Verification (Every Required Category Must Turn RED) ===", flush=True)

    # 1. B2-ATLAS mutations (RGBA8 mask, disabled mipmaps, 3rd texture on roof material)
    mut_rgba = dict(base_snap, maskFormat=1023)
    expect_red("B2-ATLAS: mask format RGBAFormat instead of RedFormat", lambda: assert_b2_atlas(mut_rgba))
    mut_nomip = dict(base_snap, maskMips=False)
    expect_red("B2-ATLAS: disable R8 mask mipmaps", lambda: assert_b2_atlas(mut_nomip))
    mut_3tex = dict(base_snap, distinctSiteATextures=3)
    expect_red("B2-ATLAS: add 3rd texture object on Site A", lambda: assert_b2_atlas(mut_3tex))
    mut_wrong_ch = dict(base_snap, shaderSamplesR=False, shaderSamplesWrongChannel=True)
    expect_red("B2-ATLAS: sample .g channel instead of .r", lambda: assert_b2_atlas(mut_wrong_ch))

    # 2. B2-NIGHT real GPU mutation (force all mask bytes to 255 -> upload -> real WebGL render readback!)
    page.evaluate("""() => {
        const at = window.__VH.WORLD.showcaseSiteA.atlas;
        window.__vhMaskBackup = at.maskTexture.image.data.slice();
    }""")
    try:
        # Mutation A: all windows forced bright (255) -> real GPU render
        page.evaluate("""() => {
            const at = window.__VH.WORLD.showcaseSiteA.atlas;
            at.maskTexture.image.data.fill(255);
            at.maskTexture.needsUpdate = true;
        }""")
        night_all_lit = measure_gpu_window_levels(page, 3)
        expect_red("B2-NIGHT: force all R8 mask pixels to 255 (GPU render readback)", lambda: assert_b2_night(day_ok, night_all_lit))

        # Mutation B: collapse all 3 lit levels into a single level (170) -> real GPU render
        page.evaluate("""() => {
            const at = window.__VH.WORLD.showcaseSiteA.atlas;
            const d = at.maskTexture.image.data;
            d.set(window.__vhMaskBackup);
            for (let i = 0; i < d.length; i++) if (d[i] > 0) d[i] = 170;
            at.maskTexture.needsUpdate = true;
        }""")
        night_collapsed = measure_gpu_window_levels(page, 3)
        expect_red("B2-NIGHT: collapse 3 lit levels to 1 level (GPU render readback)", lambda: assert_b2_night(day_ok, night_collapsed))
    finally:
        page.evaluate("""() => {
            const at = window.__VH.WORLD.showcaseSiteA.atlas;
            at.maskTexture.image.data.set(window.__vhMaskBackup);
            at.maskTexture.needsUpdate = true;
            delete window.__vhMaskBackup;
        }""")

    # 3 & 4. B2-ART-A & B2-ART-B real canvas/mask mutations
    page.evaluate("""() => {
        const at = window.__VH.WORLD.showcaseSiteA.atlas;
        const c = at.atlasTexture.image;
        window.__vhAtlasBackup = c.getContext('2d').getImageData(0, 0, 1024, 1024);
    }""")
    try:
        # B2-ART-A: overwrite Building A ground storefront with flat color
        page.evaluate("""() => {
            const ctx = window.__VH.WORLD.showcaseSiteA.atlas.atlasTexture.image.getContext('2d');
            ctx.fillStyle = '#555555';
            ctx.fillRect(16, 358, 992, 90);
        }""")
        m_art_a = collect_art_and_uv_metrics(page)
        expect_red("B2-ART-A: erase Building A ground storefront details", lambda: assert_b2_art_a(m_art_a))

        # B2-ART-B: copy Building A upper commercial facade over Building B office facade
        page.evaluate("""() => {
            const ctx = window.__VH.WORLD.showcaseSiteA.atlas.atlasTexture.image.getContext('2d');
            ctx.putImageData(window.__vhAtlasBackup, 0, 0);
            ctx.drawImage(ctx.canvas, 16, 232, 980, 120, 16, 552, 980, 120);
            ctx.drawImage(ctx.canvas, 16, 232, 980, 120, 16, 672, 980, 120);
            ctx.drawImage(ctx.canvas, 16, 232, 980, 60, 16, 792, 980, 60);
        }""")
        m_art_b = collect_art_and_uv_metrics(page)
        expect_red("B2-ART-B: replace Building B office facade with Building A tile", lambda: assert_b2_art_b(m_art_b))
    finally:
        page.evaluate("""() => {
            const at = window.__VH.WORLD.showcaseSiteA.atlas;
            at.atlasTexture.image.getContext('2d').putImageData(window.__vhAtlasBackup, 0, 0);
            at.atlasTexture.needsUpdate = true;
            delete window.__vhAtlasBackup;
        }""")

    # 5 & 6. B2-UV-A & B2-UV-B real BufferGeometry UV mutations
    page.evaluate("""() => {
        const sc = window.__VH.WORLD.showcaseSiteA;
        window.__vhUvABackup = sc.meshes.buildingAShell.geometry.attributes.uv.array.slice();
        window.__vhUvBBackup = sc.meshes.buildingBShell.geometry.attributes.uv.array.slice();
    }""")
    try:
        # B2-UV-A: inject NaN into Building A UV
        page.evaluate("""() => {
            const uv = window.__VH.WORLD.showcaseSiteA.meshes.buildingAShell.geometry.attributes.uv;
            uv.setXY(0, NaN, 0.2);
        }""")
        expect_red("B2-UV-A: inject NaN into Building A facade UV", lambda: assert_b2_uv_a(collect_art_and_uv_metrics(page)))

        # B2-UV-B: collapse Building B 10-segment NW arc UVs to a constant
        page.evaluate("""() => {
            const sc = window.__VH.WORLD.showcaseSiteA;
            sc.meshes.buildingAShell.geometry.attributes.uv.array.set(window.__vhUvABackup);
            const pos = sc.meshes.buildingBShell.geometry.attributes.position;
            const uv = sc.meshes.buildingBShell.geometry.attributes.uv;
            for (let i = 0; i < pos.count; i++) {
                const x = pos.getX(i), z = pos.getZ(i);
                if (x <= -480 + 1e-3 && z >= -807 - 1e-3) uv.setX(i, 0.25);
            }
        }""")
        expect_red("B2-UV-B: collapse Building B 10-seg arc UV to constant", lambda: assert_b2_uv_b(collect_art_and_uv_metrics(page)))
    finally:
        page.evaluate("""() => {
            const sc = window.__VH.WORLD.showcaseSiteA;
            sc.meshes.buildingAShell.geometry.attributes.uv.array.set(window.__vhUvABackup);
            sc.meshes.buildingBShell.geometry.attributes.uv.array.set(window.__vhUvBBackup);
            delete window.__vhUvABackup;
            delete window.__vhUvBBackup;
        }""")

    # 7, 8, 9. B2-DAYNIGHT, B2-REPEAT, B2-BUDGET mutations
    mut_dn = json.loads(json.dumps(base_dnb))
    mut_dn["cycles"][1]["progs"] += 1
    expect_red("B2-DAYNIGHT: shader program count grows on day/night toggle", lambda: assert_b2_daynight_repeat_budget_compat(mut_dn))

    mut_rep = json.loads(json.dumps(base_dnb))
    mut_rep["repeatEnd"]["texSame"] = False
    expect_red("B2-REPEAT: rebuild facade texture on repeat call", lambda: assert_b2_daynight_repeat_budget_compat(mut_rep))

    mut_bud = json.loads(json.dumps(base_dnb))
    mut_bud["shadowCasters"] = 1
    expect_red("B2-BUDGET: enable castShadow=true on showcase mesh", lambda: assert_b2_daynight_repeat_budget_compat(mut_bud))


def save_screenshots(page, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    poses = [
        ("A_front_day", 1, [-528, 6.0, -792], [-528, 5.5, -777]),
        ("A_front_night", 3, [-528, 6.0, -792], [-528, 5.5, -777]),
        ("A_oblique_night", 3, [-509, 9.0, -794], [-527, 6.0, -772]),
        ("B_front_arc_day", 1, [-494, 11.0, -786], [-475, 10.0, -807]),
        ("B_front_arc_night", 3, [-494, 11.0, -786], [-475, 10.0, -807]),
        ("overview_night", 3, [-501, 28.0, -742], [-501, 8.0, -795]),
    ]
    for label, sky_idx, cam_p, look_p in poses:
        page.evaluate("""([skyIdx, cp, lp]) => {
            const { applySkyPreset, camera, renderer, scene, __th } = window.__VH;
            applySkyPreset(skyIdx);
            const g = __th(-501, -790);
            camera.position.set(cp[0], g + cp[1], cp[2]);
            camera.lookAt(lp[0], g + lp[1], lp[2]);
            camera.updateMatrixWorld();
            renderer.setRenderTarget(null);
            renderer.render(scene, camera);
        }""", [sky_idx, cam_p, look_p])
        page.screenshot(path=str(out_dir / f"{label}.png"))
    print(f"Saved {len(poses)} screenshots to {out_dir}", flush=True)


def main():
    ap = argparse.ArgumentParser(description="T-014B2 Site A facade & R8 night-window Playwright test")
    ap.add_argument("--preset", default="PHONE_LOW", choices=["PHONE_LOW", "TABLET_MED", "DESKTOP_HIGH"])
    ap.add_argument("--frames", type=int, default=12, help="Frames per ON/OFF draw-call measurement (use 120 for full gate)")
    ap.add_argument("--screenshots", type=Path, default=None, help="Optional directory to save day/night A/B screenshots")
    ap.add_argument("--skip-url-matrix", action="store_true", help="Skip extra ?showcase=0/1 page loads for faster local smoke")
    args = ap.parse_args()

    t_start = time.monotonic()
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
    chrome = shutil.which("google-chrome") or shutil.which("chromium")
    launch_args = ["--no-sandbox", "--disable-dev-shm-usage", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"]

    with http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler) as server, sync_playwright() as pw:
        threading.Thread(target=server.serve_forever, daemon=True).start()
        url = f"http://127.0.0.1:{server.server_port}"
        with pw.chromium.launch(executable_path=chrome, args=launch_args) as browser:
            print(f"=== T-014B2 Production Verification [{args.preset}, headless Chrome/SwiftShader] ===", flush=True)
            ctx, page, errors = open_game_page(browser, url, args.preset, "")
            try:
                snap = collect_atlas_snapshot(page)
                gpu_bytes = assert_b2_atlas(snap)
                print(f"PASS [B2-ATLAS] seed={snap['seed']} gpuBytes={gpu_bytes} (cap={MAX_GPU_MIP_BYTES}) textures={snap['distinctSiteATextures']} glR8=33321", flush=True)

                day_read = measure_gpu_window_levels(page, 1)
                night_read = measure_gpu_window_levels(page, 3)
                assert_b2_night(day_read, night_read)
                print(
                    f"PASS [B2-NIGHT] A(night)={ {k: round(night_read['A'][k]['median'], 1) for k in ('dark','level1','level2','level3')} } "
                    f"B(night)={ {k: round(night_read['B'][k]['median'], 1) for k in ('dark','level1','level2','level3')} }",
                    flush=True,
                )

                art_uv = collect_art_and_uv_metrics(page)
                assert_b2_art_a(art_uv)
                assert_b2_art_b(art_uv)
                assert_b2_uv_a(art_uv)
                assert_b2_uv_b(art_uv)
                print(
                    f"PASS [B2-ART-A/B & B2-UV-A/B] A_groundW={art_uv['artA']['groundAvgW']:.1f} A_upperW={art_uv['artA']['upperAvgW']:.1f} "
                    f"AB_diff={art_uv['artB']['abMeanLumaDiff']:.1f} B_arcPts={art_uv['arcPointCount']}",
                    flush=True,
                )

                dnb = run_daynight_repeat_budget_compat(page, args.frames)
                summary = assert_b2_daynight_repeat_budget_compat(dnb)
                print(f"PASS [B2-DAYNIGHT/REPEAT/BUDGET/COMPAT] {json.dumps(summary)}", flush=True)

                if args.screenshots:
                    save_screenshots(page, args.screenshots)

                run_mutations(page, snap, dnb, day_read)
                assert not errors, f"Page errors encountered: {errors}"
            finally:
                ctx.close()

            # Required ?showcase=0 / ?showcase=1 URL visibility checks (§6 CHANGE 5)
            if not args.skip_url_matrix:
                for q, expected_vis in [("?showcase=0", False), ("?showcase=1", True)]:
                    c2, p2, e2 = open_game_page(browser, url, args.preset, q)
                    try:
                        vis = p2.evaluate("""() => {
                            const sc = window.__VH.WORLD.showcaseSiteA;
                            const initVis = sc.isVisible();
                            const hasAtlas = Boolean(sc.atlas && sc.atlas.atlasTexture && sc.atlas.maskTexture);
                            const toggled = window.__VH.setShowcaseSiteAVisible(true);
                            return { initVis, hasAtlas, toggled };
                        }""")
                        assert vis["initVis"] is expected_vis, f"URL {q}: expected visible={expected_vis}, got {vis}"
                        assert vis["hasAtlas"] is True, f"URL {q}: atlas must still initialize identically"
                        assert vis["toggled"] is True, f"URL {q}: setShowcaseSiteAVisible(true) failed"
                        assert not e2, f"URL {q} page errors: {e2}"
                        print(f"PASS [URL {q}] visible={vis['initVis']} atlasReady={vis['hasAtlas']}", flush=True)
                    finally:
                        c2.close()
        server.shutdown()

    elapsed = time.monotonic() - t_start
    print(f"RESULT: PASS (T-014B2 all categories + 11 negative mutations RED in {elapsed:.1f}s; headless Chrome/SwiftShader)", flush=True)


if __name__ == "__main__":
    main()
