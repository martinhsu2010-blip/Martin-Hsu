// T-014B3 regression, golden-hash, layout->geometry->UV->mask alignment, LOD/layer-31 & mutation test.
// Runs fast (<10s) directly against production code extracted from index.html (Three.js r160).
// Verifies BOTH golden SHA-256 hashes (R8 mask in Node + Chrome, 1024x1024 RGBA atlas in headless Chrome).
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import fs from 'node:fs';
import http from 'node:http';
import vm from 'node:vm';
import { spawn } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import * as THREE from '../../libs/three/build/three.module.js';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const HTML_PATH = path.join(ROOT, 'index.html');
const html = fs.readFileSync(HTML_PATH, 'utf8');

const GOLDEN_ATLAS_SHA256 = '61304bdf8a180a6e6ad2973a494d7841d591827fbe60b49b82bd94204024f7d9';
const GOLDEN_MASK_SHA256 = '920923f2d6351b6eb062357e43620a70db622c656186b9883a0cafe003f057ea';

function section(src, startMarker, endMarker) {
    const s = src.indexOf(startMarker);
    assert.ok(s >= 0, `Missing start marker: ${startMarker}`);
    const e = src.indexOf(endMarker, s);
    assert.ok(e > s, `Missing end marker: ${endMarker}`);
    return src.slice(s, e);
}

function sha256Hex(buf) {
    return crypto.createHash('sha256').update(buf).digest('hex');
}

function triCount(geo) {
    return geo.index ? geo.index.count / 3 : geo.attributes.position.count / 3;
}

function expectRed(name, fn) {
    let failed = false;
    try {
        fn();
    } catch (_) {
        failed = true;
    }
    assert.ok(failed, `MUTATION MUST TURN RED but stayed GREEN: ${name}`);
    console.log(`  [MUTATION RED] ${name}`);
}

// Minimal 2D canvas stub for Node structural/mask/layout runs (real RGBA pixels verified in headless Chrome below)
function makeCanvasStub() {
    const ctx = {
        fillStyle: '#000',
        fillRect() {},
        save() {},
        restore() {},
        translate() {},
        createLinearGradient() { return { addColorStop() {} }; }
    };
    return {
        width: 0, height: 0,
        getContext: () => ctx
    };
}

// Extract real production sections from index.html
const b1Src = section(html, '        // T-014B1: visual-only Site A', '        // T-014B1_END');
const b2b3Src = section(html, '        // T-014B2/B3: Site A shared facade layout', '        // ---------- 物理碰撞體線框除錯');

function createShowcaseContext(overrideB2B3 = b2b3Src) {
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(60, 16 / 9, 0.2, 2000);
    camera.layers.enable(1); // DETAIL_LAYER = 1, matching production
    camera.position.set(98, 2, 22);
    const mirrorCamera = new THREE.PerspectiveCamera(); // Water.js default: layer 0 only
    const ctxObj = {
        THREE,
        scene,
        camera,
        mirrorCamera,
        WORLD: { showcaseSiteA: null },
        STATE: { night: 0, quality: 'LOW' },
        performance: globalThis.performance,
        document: { createElement: () => makeCanvasStub() },
        terrainHeight: () => 2.5,
        showcaseFacadeAnisotropy: () => 2,
        Math, Number, Object, Array, Map, Set, Uint8Array, Float32Array, Boolean, Error, console
    };
    vm.createContext(ctxObj);
    vm.runInContext(
        b1Src + '\n' + overrideB2B3 + '\n' +
        'this.buildShowcaseSiteA = buildShowcaseSiteA;\n' +
        'this.setShowcaseSiteAVisible = setShowcaseSiteAVisible;\n' +
        'this.buildShowcaseFacadeLayout = buildShowcaseFacadeLayout;\n' +
        'this.buildShowcaseFacadeMaps = buildShowcaseFacadeMaps;\n' +
        'this.buildShowcaseSiteANear = buildShowcaseSiteANear;\n' +
        'this.updateShowcaseSiteALOD = updateShowcaseSiteALOD;\n' +
        'this.applyShowcaseFacades = applyShowcaseFacades;\n' +
        'this.SHOWCASE_FACADE_SEED = SHOWCASE_FACADE_SEED;\n' +
        'this.SHOWCASE_GEOM = SHOWCASE_GEOM;',
        ctxObj
    );
    return ctxObj;
}

// =========================================================================
// Validators (reused for production PASS and negative mutation RED)
// =========================================================================

function assertMaskGoldenHash(maskData) {
    assert.equal(maskData.byteLength, 512 * 512, `R8 mask byteLength ${maskData.byteLength} != 262144`);
    const hash = sha256Hex(maskData);
    assert.equal(hash, GOLDEN_MASK_SHA256, `R8 mask SHA-256 mismatch: ${hash} != ${GOLDEN_MASK_SHA256}`);
    return hash;
}

function assertGroupArchitecture(ctx, sc) {
    // Original B1 group untouched: 6 children, all visible === true
    assert.equal(sc.group.name, 'showcase_site_a');
    assert.equal(sc.group.children.length, 6, `sc.group must keep exactly 6 children, got ${sc.group.children.length}`);
    for (const m of sc.group.children) {
        assert.equal(m.visible, true, `Original mesh ${m.name} must keep visible === true`);
        assert.equal(m.castShadow, false, `${m.name}: castShadow must be false`);
    }
    assert.equal(Object.keys(sc.meshes).length, 6, 'WORLD.showcaseSiteA.meshes must stay 6 entries');

    // Separate sibling Near group
    const near = sc.near;
    assert.ok(near && near.group, 'Missing sc.near.group');
    assert.equal(near.group.parent, ctx.scene, 'Near group must be a direct sibling child of scene');
    assert.notEqual(near.group, sc.group, 'Near group must be separate from sc.group');
    assert.equal(near.group.userData.noBatch, true, 'Near group missing userData.noBatch = true');
    const nearMeshes = near.group.children.filter(c => c.isMesh);
    assert.ok(nearMeshes.length >= 2 && nearMeshes.length <= 4, `Near mesh count ${nearMeshes.length} outside [2, 4]`);

    // <= 10 stored meshes, <= 5 existing materials reused, 0 new materials/textures/shadow casters
    const allStored = [...sc.group.children.filter(c => c.isMesh), ...nearMeshes];
    assert.ok(allStored.length <= 10, `Stored meshes ${allStored.length} > 10`);
    const origMatSet = new Set(sc.materials);
    assert.ok(origMatSet.size <= 5, `Base material count ${origMatSet.size} > 5`);
    for (const m of nearMeshes) {
        assert.equal(m.visible, true, `Near mesh ${m.name} must keep visible === true`);
        assert.equal(m.userData.noBatch, true, `Near mesh ${m.name} missing userData.noBatch = true`);
        assert.equal(m.castShadow, false, `Near mesh ${m.name} must have castShadow = false`);
        assert.equal(m.receiveShadow, true, `Near mesh ${m.name} must have receiveShadow = true`);
        assert.ok(origMatSet.has(m.material), `Near mesh ${m.name} introduced a new material`);
    }
    assert.equal(near.meshes.buildingAShell.material, sc.materials[0], 'A Near shell must reuse matShellA');
    assert.equal(near.meshes.buildingBShell.material, sc.materials[1], 'B Near shell must reuse matShellB');
    assert.equal(near.meshes.buildingARoof.material, sc.materials[2], 'A Near roof must reuse matRoofTrim');
    assert.equal(near.meshes.buildingBRoof.material, sc.materials[2], 'B Near roof must reuse matRoofTrim');
}

function assertTriangleBudgets(sc) {
    const farA = triCount(sc.meshes.buildingAShell.geometry) + triCount(sc.meshes.buildingARoof.geometry);
    const farB = triCount(sc.meshes.buildingBShell.geometry) + triCount(sc.meshes.buildingBRoof.geometry);
    const farStreet = triCount(sc.meshes.streetAsphalt.geometry) + triCount(sc.meshes.streetSidewalks.geometry);
    const farTotal = farA + farB + farStreet;
    assert.ok(farTotal <= 520, `Far total triangles ${farTotal} > 520`);

    const nearAShell = triCount(sc.near.meshes.buildingAShell.geometry);
    const nearARoof = triCount(sc.near.meshes.buildingARoof.geometry);
    const nearBShell = triCount(sc.near.meshes.buildingBShell.geometry);
    const nearBRoof = triCount(sc.near.meshes.buildingBRoof.geometry);
    const nearA = nearAShell + nearARoof;
    const nearB = nearBShell + nearBRoof;
    const nearTotal = nearA + nearB;
    assert.ok(nearA <= 6000, `Building A Near triangles ${nearA} > 6000`);
    assert.ok(nearB <= 8000, `Building B Near triangles ${nearB} > 8000`);
    assert.ok(nearTotal <= 14064, `Site A Near total triangles ${nearTotal} > 14064`);
    return { farA, farB, farStreet, farTotal, nearAShell, nearARoof, nearA, nearBShell, nearBRoof, nearB, nearTotal };
}

function checkUnitOutwardNormals(mesh, label) {
    const pos = mesh.geometry.attributes.position;
    const norm = mesh.geometry.attributes.normal;
    assert.ok(pos && norm && pos.count === norm.count && pos.count >= 9, `${label}: missing position/normal`);
    for (let i = 0; i < pos.count; i += 3) {
        const ax = pos.getX(i), ay = pos.getY(i), az = pos.getZ(i);
        const bx = pos.getX(i + 1), by = pos.getY(i + 1), bz = pos.getZ(i + 1);
        const cx = pos.getX(i + 2), cy = pos.getY(i + 2), cz = pos.getZ(i + 2);
        const ex1 = bx - ax, ey1 = by - ay, ez1 = bz - az;
        const ex2 = cx - ax, ey2 = cy - ay, ez2 = cz - az;
        const fx = ey1 * ez2 - ez1 * ey2, fy = ez1 * ex2 - ex1 * ez2, fz = ex1 * ey2 - ey1 * ex2;
        for (let k = 0; k < 3; k++) {
            const nx = norm.getX(i + k), ny = norm.getY(i + k), nz = norm.getZ(i + k);
            const len = Math.hypot(nx, ny, nz);
            assert.ok(Number.isFinite(len) && Math.abs(len - 1) < 1e-3, `${label}: non-unit normal at v=${i + k}`);
        }
        const avgNx = norm.getX(i) + norm.getX(i + 1) + norm.getX(i + 2);
        const avgNy = norm.getY(i) + norm.getY(i + 1) + norm.getY(i + 2);
        const avgNz = norm.getZ(i) + norm.getZ(i + 1) + norm.getZ(i + 2);
        assert.ok(fx * avgNx + fy * avgNy + fz * avgNz > -1e-6, `${label}: inverted winding at tri=${i / 3}`);
    }
}

function signedWallOffsetBuildingA(px, py, pz, layout) {
    const segs = py < layout.A.baseY + 9.6 - 1e-3 ? layout.A.segments : layout.A.upperSegments;
    let bestDist = Infinity, bestSigned = 0;
    for (const seg of segs) {
        const [x0, z0] = seg.worldStart, [x1, z1] = seg.worldEnd;
        const tx = (x1 - x0) / seg.length, tz = (z1 - z0) / seg.length;
        const t = Math.max(0, Math.min(seg.length, (px - x0) * tx + (pz - z0) * tz));
        const cx = x0 + tx * t, cz = z0 + tz * t;
        const d = Math.hypot(px - cx, pz - cz);
        if (d < bestDist) {
            bestDist = d;
            bestSigned = (px - cx) * seg.normal[0] + (pz - cz) * seg.normal[2];
        }
    }
    return bestSigned;
}

function signedWallOffsetBuildingB(px, py, pz, layout) {
    const r = py < layout.B.baseY + 20.8 - 1e-3 ? layout.B.baseRect : layout.B.upperRect;
    const cxArc = r.minX + r.arcR, czArc = r.maxZ - r.arcR;
    if (px < cxArc && pz > czArc) {
        return Math.hypot(px - cxArc, pz - czArc) - r.arcR;
    }
    const dWest = r.minX - px;
    const dEast = px - r.maxX;
    const dSouth = r.minZ - pz;
    const dNorth = pz - r.maxZ;
    return Math.max(dWest, dEast, dSouth, dNorth);
}

function assertLayoutGeometryUVMaskAlignment(sc, maskData) {
    const layout = sc.atlas.layout;
    assert.ok(layout && layout.A && layout.B, 'Missing shared layout on sc.atlas.layout');
    const aOps = new Map(layout.A.openings.map(o => [o.id, o]));
    const bOps = new Map([...layout.B.openings, ...layout.B.crownOpenings].map(o => [o.id, o]));
    const wq = sc.near.windowQuads;
    assert.equal(wq.length, aOps.size + bOps.size, `windowQuads count ${wq.length} != total layout openings ${aOps.size + bOps.size}`);

    const aGeo = sc.near.meshes.buildingAShell.geometry;
    const bGeo = sc.near.meshes.buildingBShell.geometry;
    checkUnitOutwardNormals(sc.near.meshes.buildingAShell, 'A Near shell');
    checkUnitOutwardNormals(sc.near.meshes.buildingARoof, 'A Near roof');
    checkUnitOutwardNormals(sc.near.meshes.buildingBShell, 'B Near shell');
    checkUnitOutwardNormals(sc.near.meshes.buildingBRoof, 'B Near roof');

    const aWinTris = new Set();
    const bWinTris = new Set();
    let minRecess = Infinity, maxRecess = -Infinity;

    for (const entry of wq) {
        const isA = entry.building === 'A';
        const op = isA ? aOps.get(entry.id) : bOps.get(entry.id);
        assert.ok(op, `Unknown opening id ${entry.id}`);
        assert.ok(entry.triCount >= 2, `Opening ${entry.id} has < 2 triangles`);
        const geo = isA ? aGeo : bGeo;
        const pos = geo.attributes.position;
        const uv = geo.attributes.uv;
        const triSet = isA ? aWinTris : bWinTris;

        let uMin = Infinity, uMax = -Infinity, vMin = Infinity, vMax = -Infinity;
        for (let t = 0; t < entry.triCount; t++) {
            const ti = entry.triStart + t;
            triSet.add(ti);
            for (let k = 0; k < 3; k++) {
                const vi = ti * 3 + k;
                const u = uv.getX(vi), v = uv.getY(vi);
                assert.ok(Number.isFinite(u) && Number.isFinite(v), `Non-finite UV on ${entry.id}`);
                uMin = Math.min(uMin, u); uMax = Math.max(uMax, u);
                vMin = Math.min(vMin, v); vMax = Math.max(vMax, v);
                const px = pos.getX(vi), py = pos.getY(vi), pz = pos.getZ(vi);
                const signedOff = isA
                    ? signedWallOffsetBuildingA(px, (op.y0 + op.y1) * 0.5, pz, layout)
                    : signedWallOffsetBuildingB(px, (op.y0 + op.y1) * 0.5, pz, layout);
                const rec = -signedOff;
                assert.ok(Math.abs(rec - op.recess) < 0.015, `${entry.id}: recess ${rec.toFixed(4)} != expected ${op.recess}`);
                assert.ok(rec >= 0.15 - 1e-4 && rec <= 0.25 + 1e-4, `${entry.id}: recess ${rec.toFixed(4)} out of [0.15, 0.25]m`);
                minRecess = Math.min(minRecess, rec);
                maxRecess = Math.max(maxRecess, rec);
            }
        }
        // Geometry UV rect matches layout opening UV rect
        assert.ok(Math.abs(uMin - op.uvRect.u0) < 1e-4, `${entry.id}: geo uMin ${uMin} != layout ${op.uvRect.u0}`);
        assert.ok(Math.abs(uMax - op.uvRect.u1) < 1e-4, `${entry.id}: geo uMax ${uMax} != layout ${op.uvRect.u1}`);
        assert.ok(Math.abs(vMin - op.uvRect.v0) < 1e-4, `${entry.id}: geo vMin ${vMin} != layout ${op.uvRect.v0}`);
        assert.ok(Math.abs(vMax - op.uvRect.v1) < 1e-4, `${entry.id}: geo vMax ${vMax} != layout ${op.uvRect.v1}`);

        // Layout maskRect lies strictly inside geometry UV rect & every texel in maskRect equals op.maskByte
        const [mx0, my0, mx1, my1] = op.maskRect;
        assert.ok(mx0 / 512 >= uMin - 1e-5 && mx1 / 512 <= uMax + 1e-5, `${entry.id}: maskRect X outside geo UV`);
        assert.ok(my0 / 512 >= vMin - 1e-5 && my1 / 512 <= vMax + 1e-5, `${entry.id}: maskRect Y outside geo UV`);
        const midX = Math.floor((mx0 + mx1) * 0.5), midY = Math.floor((my0 + my1) * 0.5);
        assert.equal(maskData[midY * 512 + midX], op.maskByte, `${entry.id}: mask texel at (${midX},${midY}) != ${op.maskByte}`);
    }

    // Verify projecting frames in [0.08, 0.12] m AND zero night-mask bleed on all non-window triangles
    const checkShellExtras = (geo, winTris, isA, label) => {
        const pos = geo.attributes.position;
        const uv = geo.attributes.uv;
        const totalTris = pos.count / 3;
        let maxProj = -Infinity;
        let bleedTris = 0;
        for (let ti = 0; ti < totalTris; ti++) {
            if (winTris.has(ti)) continue;
            let cu = 0, cv = 0, cy = 0;
            for (let k = 0; k < 3; k++) {
                const vi = ti * 3 + k;
                const u = uv.getX(vi), v = uv.getY(vi);
                assert.ok(Number.isFinite(u) && Number.isFinite(v) && u >= -1e-5 && u <= 1 + 1e-5 && v >= -1e-5 && v <= 1 + 1e-5, `${label}: invalid UV on tri ${ti}`);
                cu += u; cv += v; cy += pos.getY(vi);
            }
            const avgY = cy / 3;
            const isPenthouse = isA && avgY > layout.A.baseY + 14.2 + 1e-3;
            if (!isPenthouse) {
                const tierY = isA
                    ? (avgY <= layout.A.baseY + 9.6 + 1e-4 ? layout.A.baseY + 4.0 : layout.A.baseY + 12.0)
                    : (avgY <= layout.B.baseY + 20.8 + 1e-4 ? layout.B.baseY + 10.0 : layout.B.baseY + 22.0);
                for (let k = 0; k < 3; k++) {
                    const vi = ti * 3 + k;
                    const off = isA
                        ? signedWallOffsetBuildingA(pos.getX(vi), tierY, pos.getZ(vi), layout)
                        : signedWallOffsetBuildingB(pos.getX(vi), tierY, pos.getZ(vi), layout);
                    if (off > maxProj) maxProj = off;
                }
                const mx = Math.max(0, Math.min(511, Math.floor((cu / 3) * 512)));
                const my = Math.max(0, Math.min(511, Math.floor((cv / 3) * 512)));
                if (maskData[my * 512 + mx] !== 0) bleedTris++;
            }
        }
        assert.ok(maxProj >= 0.08 - 1e-4 && maxProj <= 0.12 + 1e-4, `${label}: max frame projection ${maxProj.toFixed(4)}m outside [0.08, 0.12]m`);
        assert.equal(bleedTris, 0, `${label}: ${bleedTris} non-window triangles sample non-zero night mask`);
        return maxProj;
    };
    const projA = checkShellExtras(aGeo, aWinTris, true, 'Building A Near');
    const projB = checkShellExtras(bGeo, bWinTris, false, 'Building B Near');
    return { openingsChecked: wq.length, minRecess, maxRecess, projA, projB };
}

function renderedSiteAMeshesForCamera(sc, cam) {
    const out = [];
    for (const grp of [sc.group, sc.near.group]) {
        if (!grp.visible) continue;
        for (const m of grp.children) {
            if (m.isMesh && m.visible && m.layers.test(cam.layers)) out.push(m);
        }
    }
    return out;
}

function assertLayerInvariants(ctx, sc) {
    const DETAIL_LAYER = 1;
    const INACTIVE_LAYER = 31;
    // Camera layer masks: main = {0,1}, mirror = {0}, both exclude layer 31
    assert.equal(ctx.camera.layers.mask, (1 << 0) | (1 << DETAIL_LAYER), 'Main camera must enable layers 0 and 1 only');
    assert.equal(ctx.mirrorCamera.layers.mask, (1 << 0), 'Mirror camera must enable layer 0 only');

    const allSiteAMeshes = [...sc.group.children, ...sc.near.group.children];
    for (const m of allSiteAMeshes) {
        assert.equal(m.visible, true, `Mesh ${m.name} must keep visible === true (use layer 31, not .visible)`);
        assert.equal((m.layers.mask & (1 << DETAIL_LAYER)), 0, `Mesh ${m.name} must NEVER use DETAIL_LAYER (1)`);
    }

    const checkPair = (label, farS, farR, nearS, nearR, expected) => {
        const activeLayer = (1 << 0) >>> 0, inactiveLayer = (1 << INACTIVE_LAYER) >>> 0;
        if (expected === 'near') {
            assert.equal(nearS.layers.mask, activeLayer, `${label} Near shell not on layer 0`);
            assert.equal(nearR.layers.mask, activeLayer, `${label} Near roof not on layer 0`);
            assert.equal(farS.layers.mask, inactiveLayer, `${label} Far shell not on layer 31`);
            assert.equal(farR.layers.mask, inactiveLayer, `${label} Far roof not on layer 31`);
        } else {
            assert.equal(farS.layers.mask, activeLayer, `${label} Far shell not on layer 0`);
            assert.equal(farR.layers.mask, activeLayer, `${label} Far roof not on layer 0`);
            assert.equal(nearS.layers.mask, inactiveLayer, `${label} Near shell not on layer 31`);
            assert.equal(nearR.layers.mask, inactiveLayer, `${label} Near roof not on layer 31`);
        }
    };
    checkPair('A', sc.meshes.buildingAShell, sc.meshes.buildingARoof, sc.near.meshes.buildingAShell, sc.near.meshes.buildingARoof, sc.lod.A);
    checkPair('B', sc.meshes.buildingBShell, sc.meshes.buildingBRoof, sc.near.meshes.buildingBShell, sc.near.meshes.buildingBRoof, sc.lod.B);

    // Street meshes always on layer 0
    assert.equal(sc.meshes.streetAsphalt.layers.mask, 1, 'streetAsphalt must stay on layer 0');
    assert.equal(sc.meshes.streetSidewalks.layers.mask, 1, 'streetSidewalks must stay on layer 0');

    // Main camera and mirror camera draw the exact same active Site A meshes (6 when visible, 0 when hidden)
    const mainDrawn = renderedSiteAMeshesForCamera(sc, ctx.camera);
    const mirrorDrawn = renderedSiteAMeshesForCamera(sc, ctx.mirrorCamera);
    const expectedCount = sc.isVisible() ? 6 : 0;
    assert.equal(mainDrawn.length, expectedCount, `Main camera Site A drawn count ${mainDrawn.length} != ${expectedCount}`);
    assert.equal(mirrorDrawn.length, expectedCount, `Mirror camera Site A drawn count ${mirrorDrawn.length} != ${expectedCount}`);
    assert.deepEqual(mainDrawn.map(m => m.name).sort(), mirrorDrawn.map(m => m.name).sort(), 'Mirror pass must match main-camera LOD state');
}

function assertLODAndVisibilityBehavior(ctx, sc) {
    // 1. Spawn (98, 2, 22) -> both Far
    ctx.camera.position.set(98, 2, 22);
    ctx.updateShowcaseSiteALOD(true);
    assert.equal(sc.lod.A, 'far'); assert.equal(sc.lod.B, 'far');
    assertLayerInvariants(ctx, sc);

    // 2. Hysteresis on Building A (AABB x:[-539,-517], z:[-777,-763]):
    // Move to z = -777 - 42 = -819, x = -528 (42m south of A, inside (35,50)) -> stays Far!
    ctx.camera.position.set(-528, 8, -819);
    ctx.updateShowcaseSiteALOD(false);
    assert.equal(sc.lod.A, 'far', 'A must stay Far when approaching at 42m (>35m)');

    // Move to z = -777 - 35 = -812 (exact 35m; test high Y=120 to prove horizontal AABB distance!)
    ctx.camera.position.set(-528, 120, -812);
    ctx.updateShowcaseSiteALOD(false);
    assert.equal(sc.lod.A, 'near', 'A must enter Near at horizontal dist <= 35m regardless of Y');
    assertLayerInvariants(ctx, sc);

    // Retreat to 42m -> stays Near (hysteresis)!
    ctx.camera.position.set(-528, 8, -819);
    ctx.updateShowcaseSiteALOD(false);
    assert.equal(sc.lod.A, 'near', 'A must stay Near inside hysteresis band (42m < 50m)');

    // Retreat to 49.9m -> stays Near!
    ctx.camera.position.set(-528, 8, -826.9);
    ctx.updateShowcaseSiteALOD(false);
    assert.equal(sc.lod.A, 'near', 'A must stay Near at 49.9m');

    // Retreat to 50.0m -> switches to Far!
    ctx.camera.position.set(-528, 8, -827.0);
    ctx.updateShowcaseSiteALOD(false);
    assert.equal(sc.lod.A, 'far', 'A must enter Far at >= 50m');
    assertLayerInvariants(ctx, sc);

    // 3. Mixed state: A Near (20m), B Far (60m)
    ctx.camera.position.set(-528, 10, -743); // dist to A = 20m, dist to B = hypot(44, 60) = 74.4m
    ctx.updateShowcaseSiteALOD(true);
    assert.equal(sc.lod.A, 'near', 'Mixed state: A should be Near');
    assert.equal(sc.lod.B, 'far', 'Mixed state: B should be Far');
    assertLayerInvariants(ctx, sc);

    // 4. First-frame direct reset after teleport (no stale Near carried into (35,50) band!)
    ctx.camera.position.set(-528, 8, -792); // 15m from A -> Near
    ctx.updateShowcaseSiteALOD(false);
    assert.equal(sc.lod.A, 'near');
    ctx.camera.position.set(-528, 8, -819); // teleport directly to 42m
    sc.resetLOD();
    assert.equal(sc.lod.A, 'far', 'First-frame reset after teleport to 42m must compute Far directly, not keep stale Near');
    assertLayerInvariants(ctx, sc);

    // 5. Showcase OFF (?showcase=0 / setVisible(false)): both groups hidden, 0 meshes rendered, LOD skipped
    const sceneLenBefore = ctx.scene.children.length;
    assert.equal(ctx.setShowcaseSiteAVisible(false), false);
    assert.equal(sc.isVisible(), false);
    assert.equal(sc.group.visible, false);
    assert.equal(sc.near.group.visible, false);
    assertLayerInvariants(ctx, sc);

    const updatesBefore = sc.lod.updates, skipsBefore = sc.lod.skippedWhileHidden;
    ctx.camera.position.set(-528, 8, -792); // 15m from A while hidden
    ctx.updateShowcaseSiteALOD(false);
    assert.equal(sc.lod.updates, updatesBefore, 'LOD updates must be skipped while hidden');
    assert.equal(sc.lod.skippedWhileHidden, skipsBefore + 1, 'skippedWhileHidden counter did not increment');
    assert.equal(sc.lod.A, 'far', 'LOD state must not mutate while hidden');

    // Turn back ON -> immediate direct computation at 15m -> Near
    assert.equal(ctx.setShowcaseSiteAVisible(true), true);
    assert.equal(sc.isVisible(), true);
    assert.equal(sc.lod.A, 'near', 'Turning showcase ON must compute LOD directly on first frame');
    assertLayerInvariants(ctx, sc);
    assert.equal(ctx.scene.children.length, sceneLenBefore, 'scene.children count drifted after ON/OFF');

    // Idempotence check
    assert.equal(ctx.applyShowcaseFacades(), sc.atlas, 'applyShowcaseFacades must be idempotent');
    assert.equal(ctx.buildShowcaseSiteANear(), sc.near, 'buildShowcaseSiteANear must be idempotent');
    assert.equal(ctx.scene.children.length, sceneLenBefore, 'scene.children grew on repeat calls');
}

// Headless Chrome check for BOTH golden SHA-256 hashes (1024^2 RGBA canvas + 512^2 R8 mask)
async function verifyGoldenHashesInChrome(overrideB2B3 = b2b3Src) {
    const chrome = fs.existsSync('/usr/bin/google-chrome') ? '/usr/bin/google-chrome'
        : (fs.existsSync('/usr/bin/chromium') ? '/usr/bin/chromium' : null);
    if (!chrome) return { skipped: true };

    const page = `<!doctype html><html><body><script>
        const THREE = {
            CanvasTexture: function(img){ this.image = img; },
            DataTexture: function(data, w, h){ this.image = { data, width: w, height: h }; },
            SRGBColorSpace: 1, NoColorSpace: 0, LinearMipmapLinearFilter: 1, LinearFilter: 1,
            ClampToEdgeWrapping: 1, RedFormat: 1, UnsignedByteType: 1
        };
        const WORLD = { showcaseSiteA: null }, STATE = { night: 0 };
        ${overrideB2B3}
        (async () => {
            const built = buildShowcaseFacadeMaps(SHOWCASE_FACADE_SEED, null);
            const rgba = built.canvas.getContext('2d').getImageData(0, 0, 1024, 1024).data;
            const toHex = buf => Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, '0')).join('');
            const atlasHash = toHex(await crypto.subtle.digest('SHA-256', rgba));
            const maskHash = toHex(await crypto.subtle.digest('SHA-256', built.maskData));
            document.title = JSON.stringify({ atlasHash, maskHash, rgbaBytes: rgba.byteLength, maskBytes: built.maskData.byteLength });
        })();
    </script></body></html>`;

    const srv = http.createServer((req, res) => { res.writeHead(200, { 'Content-Type': 'text/html' }); res.end(page); });
    await new Promise(r => srv.listen(0, '127.0.0.1', r));
    const port = srv.address().port;
    const proc = spawn(chrome, ['--headless=new', '--no-sandbox', '--disable-gpu', '--dump-dom', `http://127.0.0.1:${port}/`], { stdio: ['ignore', 'pipe', 'pipe'] });
    let out = '';
    proc.stdout.on('data', d => out += d);
    await new Promise(r => proc.on('close', r));
    srv.close();
    const m = out.match(/<title>(.*?)<\/title>/);
    assert.ok(m, `Chrome failed to produce title payload: ${out.slice(0, 300)}`);
    return JSON.parse(m[1]);
}

function assertGoldenChromeHashes(res) {
    assert.equal(res.rgbaBytes, 1024 * 1024 * 4, `Atlas RGBA byteLength ${res.rgbaBytes} != 4194304`);
    assert.equal(res.maskBytes, 512 * 512, `Mask byteLength ${res.maskBytes} != 262144`);
    assert.equal(res.atlasHash, GOLDEN_ATLAS_SHA256, `Atlas SHA-256 mismatch: ${res.atlasHash} != ${GOLDEN_ATLAS_SHA256}`);
    assert.equal(res.maskHash, GOLDEN_MASK_SHA256, `Mask SHA-256 mismatch: ${res.maskHash} != ${GOLDEN_MASK_SHA256}`);
}

// =========================================================================
// 1. Production Verification
// =========================================================================
console.log('=== T-014B3 Production Verification (Layout, Golden Hashes, Near Geometry, Layer-31 LOD) ===');
const ctx = createShowcaseContext();
const sc = ctx.buildShowcaseSiteA();
ctx.applyShowcaseFacades();

// Verify R8 mask golden hash in Node
const maskHashNode = assertMaskGoldenHash(sc.atlas.maskTexture.image.data);
console.log(`PASS [MASK-HASH] sha256=${maskHashNode}`);

// Verify BOTH golden hashes (1024x1024 RGBA atlas + 512x512 R8 mask) in headless Chrome
const chromeRes = await verifyGoldenHashesInChrome();
if (chromeRes.skipped) {
    console.log('SKIP [CHROME-ATLAS-HASH] No chrome/chromium binary found');
} else {
    assertGoldenChromeHashes(chromeRes);
    console.log(`PASS [CHROME-GOLDEN-HASHES] atlas=${chromeRes.atlasHash} mask=${chromeRes.maskHash}`);
}

// Verify group architecture, triangle budgets, geometry->UV->mask alignment, LOD & layers
assertGroupArchitecture(ctx, sc);
const tris = assertTriangleBudgets(sc);
console.log(`PASS [TRIS & BUDGET]`, {
    ...tris,
    nearBufferBytes: sc.near.stats.bufferBytes,
    nearInitMs: Number(sc.near.stats.initMs.toFixed(2))
});

const align = assertLayoutGeometryUVMaskAlignment(sc, sc.atlas.maskTexture.image.data);
console.log(`PASS [LAYOUT->GEO->UV->MASK]`, {
    openingsChecked: align.openingsChecked,
    recessRangeM: [Number(align.minRecess.toFixed(3)), Number(align.maxRecess.toFixed(3))],
    maxProjA: Number(align.projA.toFixed(3)),
    maxProjB: Number(align.projB.toFixed(3))
});

assertLODAndVisibilityBehavior(ctx, sc);
console.log('PASS [LOD & LAYER-31 & SHOWCASE-OFF]');

// Verify index.html wiring
assert.ok(html.includes('updateShowcaseSiteALOD(false);'), 'Missing animate() call to updateShowcaseSiteALOD(false)');
assert.ok(html.includes('WORLD.showcaseSiteA.resetLOD()'), 'Missing teleportTo() call to WORLD.showcaseSiteA.resetLOD()');
console.log('PASS [WIRING]');

// =========================================================================
// 2. Negative Mutation Verification (EVERY mutation MUST turn RED)
// =========================================================================
console.log('=== T-014B3 Negative Mutation Verification (Every Mutation Must Turn RED) ===');

// M1: Flip 1 byte in R8 mask -> golden mask hash RED
{
    const badMask = sc.atlas.maskTexture.image.data.slice();
    badMask[100] ^= 1;
    expectRed('M1: flip 1 byte in R8 mask (golden mask SHA-256)', () => assertMaskGoldenHash(badMask));
}

// M2: Alter 1 pixel in atlas -> golden Chrome atlas hash RED
if (!chromeRes.skipped) {
    const badAtlasSrc = b2b3Src.replace("r('#d6c6af', 16, 16, 992, 432);", "r('#d6c6ae', 16, 16, 992, 432);");
    const badChromeRes = await verifyGoldenHashesInChrome(badAtlasSrc);
    expectRed('M2: alter 1 RGB value in atlas (golden Chrome atlas SHA-256)', () => assertGoldenChromeHashes(badChromeRes));
}

// M3: Drift 1 opening's geometry UV -> layout->geo->UV alignment RED
{
    const uvAttr = sc.near.meshes.buildingAShell.geometry.attributes.uv;
    const origU = uvAttr.getX(sc.near.windowQuads[0].triStart * 3);
    uvAttr.setX(sc.near.windowQuads[0].triStart * 3, origU + 0.02);
    expectRed('M3: drift recessed glazing vertex UV by +0.02', () => assertLayoutGeometryUVMaskAlignment(sc, sc.atlas.maskTexture.image.data));
    uvAttr.setX(sc.near.windowQuads[0].triStart * 3, origU);
}

// M4: Break mask texel alignment for a lit opening -> RED
{
    const badMask = sc.atlas.maskTexture.image.data.slice();
    const litOp = sc.atlas.layout.A.openings.find(o => o.maskByte > 0);
    const [mx0, my0, mx1, my1] = litOp.maskRect;
    badMask[Math.floor((my0 + my1) * 0.5) * 512 + Math.floor((mx0 + mx1) * 0.5)] = 0;
    expectRed('M4: zero out R8 mask texel at lit opening center', () => assertLayoutGeometryUVMaskAlignment(sc, badMask));
}

// M5: Recess depth out of [0.15, 0.25]m -> RED
{
    const badCtx = createShowcaseContext(b2b3Src.replace('recessA: 0.20,', 'recessA: 0.05,'));
    const badSc = badCtx.buildShowcaseSiteA();
    badCtx.applyShowcaseFacades();
    expectRed('M5: recess depth 0.05m outside [0.15, 0.25]m', () => assertLayoutGeometryUVMaskAlignment(badSc, badSc.atlas.maskTexture.image.data));
}

// M6: Frame projection out of [0.08, 0.12]m -> RED
{
    const badCtx = createShowcaseContext(b2b3Src.replace('frameProjA: 0.10,', 'frameProjA: 0.25,'));
    const badSc = badCtx.buildShowcaseSiteA();
    badCtx.applyShowcaseFacades();
    expectRed('M6: frame projection 0.25m outside [0.08, 0.12]m', () => assertLayoutGeometryUVMaskAlignment(badSc, badSc.atlas.maskTexture.image.data));
}

// M7: Night glow bleed onto non-window frame triangle -> RED
{
    const uvAttr = sc.near.meshes.buildingAShell.geometry.attributes.uv;
    const winSet = new Set();
    for (const q of sc.near.windowQuads) if (q.building === 'A') for (let k = 0; k < q.triCount; k++) winSet.add(q.triStart + k);
    let nonWinTri = 0;
    while (winSet.has(nonWinTri)) nonWinTri++;
    const litOp = sc.atlas.layout.A.openings.find(o => o.maskByte > 0);
    const saved = [0, 1, 2].map(k => [uvAttr.getX(nonWinTri * 3 + k), uvAttr.getY(nonWinTri * 3 + k)]);
    for (let k = 0; k < 3; k++) uvAttr.setXY(nonWinTri * 3 + k, litOp.u, litOp.v);
    expectRed('M7: point non-window frame triangle UV into lit R8 mask texel', () => assertLayoutGeometryUVMaskAlignment(sc, sc.atlas.maskTexture.image.data));
    for (let k = 0; k < 3; k++) uvAttr.setXY(nonWinTri * 3 + k, saved[k][0], saved[k][1]);
}

// M8: Use DETAIL_LAYER (1) instead of layer 31 -> RED
{
    const prevMask = sc.meshes.buildingAShell.layers.mask;
    sc.meshes.buildingAShell.layers.set(1);
    expectRed('M8: contaminate inactive mesh with DETAIL_LAYER (1)', () => assertLayerInvariants(ctx, sc));
    sc.meshes.buildingAShell.layers.mask = prevMask;
}

// M9: Suppress Far via .visible = false instead of layer 31 -> RED
{
    sc.meshes.buildingAShell.visible = false;
    expectRed('M9: suppress Far mesh via .visible = false instead of layer 31', () => assertLayerInvariants(ctx, sc));
    sc.meshes.buildingAShell.visible = true;
}

// M10: Both Near and Far active simultaneously on layer 0 -> RED
{
    const prevFar = sc.meshes.buildingAShell.layers.mask, prevNear = sc.near.meshes.buildingAShell.layers.mask;
    sc.meshes.buildingAShell.layers.set(0);
    sc.near.meshes.buildingAShell.layers.set(0);
    expectRed('M10: render both Near and Far simultaneously on layer 0', () => assertLayerInvariants(ctx, sc));
    sc.meshes.buildingAShell.layers.mask = prevFar;
    sc.near.meshes.buildingAShell.layers.mask = prevNear;
}

// M11: Broken hysteresis (switch at 42m) -> RED
{
    const badCtx = createShowcaseContext(b2b3Src.replace('const SHOWCASE_LOD_FAR_DIST = 50;', 'const SHOWCASE_LOD_FAR_DIST = 40;'));
    const badSc = badCtx.buildShowcaseSiteA();
    badCtx.applyShowcaseFacades();
    expectRed('M11: broken hysteresis threshold (Far at 40m instead of 50m)', () => assertLODAndVisibilityBehavior(badCtx, badSc));
}

// M12: Skip first-frame reset on teleport -> RED
{
    const badCtx = createShowcaseContext(b2b3Src.replace('sc.resetLOD = () => {', 'sc.resetLOD = () => { return;'));
    const badSc = badCtx.buildShowcaseSiteA();
    badCtx.applyShowcaseFacades();
    expectRed('M12: stale Near state carried over after teleport into (35,50) band', () => assertLODAndVisibilityBehavior(badCtx, badSc));
}

// M13: Showcase OFF leaks Near group visible -> RED
{
    const badCtx = createShowcaseContext(b2b3Src.replace('nearGroup.visible = vis;', 'nearGroup.visible = true;'));
    const badSc = badCtx.buildShowcaseSiteA();
    badCtx.applyShowcaseFacades();
    expectRed('M13: showcase OFF leaves Near group visible', () => assertLODAndVisibilityBehavior(badCtx, badSc));
}

// M14: New material on Near mesh -> RED
{
    const origMat = sc.near.meshes.buildingAShell.material;
    sc.near.meshes.buildingAShell.material = new THREE.MeshStandardMaterial();
    expectRed('M14: introduce new material on Near mesh', () => assertGroupArchitecture(ctx, sc));
    sc.near.meshes.buildingAShell.material = origMat;
}

// M15: Triangle budget exceeded on Building A Near -> RED
{
    const origGeo = sc.near.meshes.buildingAShell.geometry;
    const bloated = new THREE.BufferGeometry();
    bloated.setAttribute('position', new THREE.Float32BufferAttribute(new Float32Array(6100 * 9), 3));
    sc.near.meshes.buildingAShell.geometry = bloated;
    expectRed('M15: Building A Near exceeds 6000-triangle budget', () => assertTriangleBudgets(sc));
    sc.near.meshes.buildingAShell.geometry = origGeo;
    bloated.dispose();
}

console.log(`RESULT: PASS (T-014B3 layout, golden hashes, Near geometry, layer-31 LOD + ${chromeRes.skipped ? 14 : 15} negative mutations RED)`);
