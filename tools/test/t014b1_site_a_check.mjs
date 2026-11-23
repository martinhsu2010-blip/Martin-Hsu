// T-014B1 regression & mutation test (specs/T-014B1-spec-v1.2.md §6).
// Executes the REAL production buildShowcaseSiteA(), setShowcaseSiteAVisible(),
// batchStaticMeshes(), FAST_TRAVEL, wmSelect(), fastTravelTo(), setupWorldMap(),
// and teleportTo() extracted from index.html inside collisionHarness (Three.js r160 + cannon-es).
// Headless/VM structural & behavior checks only; real WebGL draw calls and device FPS
// are measured separately in real Chromium / on-device.
import assert from 'node:assert/strict';
import vm from 'node:vm';
import { collisionHarness, html, section, THREE, CANNON } from './collision_harness.mjs';

const SITE_A_CENTER = { x: -501, z: -790 };
const EXPECTED_A_POLY = [[-539, -777], [-517, -777], [-517, -763], [-526, -763], [-526, -770], [-539, -770]];
const EXPECTED_NAMES = {
    en: 'Showcase Site A (No Collision)',
    'zh-TW': '展示區 A（無碰撞）'
};
const EXPECTED_WARNS = {
    en: 'Showcase street (no collision, pass-through walls)',
    'zh-TW': '展示街（未設碰撞，可能穿牆）'
};

function triCount(geo) {
    return geo.index ? geo.index.count / 3 : geo.attributes.position.count / 3;
}

function meshBounds(mesh) {
    mesh.geometry.computeBoundingBox();
    return mesh.geometry.boundingBox;
}

function pointInTri2D(px, pz, ax, az, bx, bz, cx, cz) {
    const s = (ax - cx) * (pz - cz) - (az - cz) * (px - cx);
    const t = (bx - ax) * (pz - az) - (bz - az) * (px - ax);
    if ((s < 0) !== (t < 0) && s !== 0 && t !== 0) return false;
    const d = (cx - bx) * (pz - bz) - (cz - bz) * (px - bx);
    return d === 0 || (d < 0) === (s + t <= 0);
}

function geometryCoversXZ(geo, px, pz) {
    const pos = geo.attributes.position;
    const idx = geo.index;
    const count = idx ? idx.count : pos.count;
    for (let i = 0; i < count; i += 3) {
        const i0 = idx ? idx.getX(i) : i;
        const i1 = idx ? idx.getX(i + 1) : i + 1;
        const i2 = idx ? idx.getX(i + 2) : i + 2;
        if (pointInTri2D(px, pz, pos.getX(i0), pos.getZ(i0), pos.getX(i1), pos.getZ(i1), pos.getX(i2), pos.getZ(i2))) {
            return true;
        }
    }
    return false;
}

function aabbGap(a, b) {
    const dx = Math.max(0, a.minX - b.maxX, b.minX - a.maxX);
    const dz = Math.max(0, a.minZ - b.maxZ, b.minZ - a.maxZ);
    return Math.hypot(dx, dz);
}

function checkUnitOutwardNormals(mesh, label) {
    const pos = mesh.geometry.attributes.position;
    const norm = mesh.geometry.attributes.normal;
    assert.ok(pos && norm && pos.count === norm.count && pos.count >= 9, `${label}: missing position/normal`);
    let hasPosX = false, hasNegX = false, hasPosZ = false, hasNegZ = false, hasPosY = false;
    for (let i = 0; i < pos.count; i += 3) {
        const ax = pos.getX(i), ay = pos.getY(i), az = pos.getZ(i);
        const bx = pos.getX(i + 1), by = pos.getY(i + 1), bz = pos.getZ(i + 1);
        const cx = pos.getX(i + 2), cy = pos.getY(i + 2), cz = pos.getZ(i + 2);
        const ex1 = bx - ax, ey1 = by - ay, ez1 = bz - az;
        const ex2 = cx - ax, ey2 = cy - ay, ez2 = cz - az;
        const fx = ey1 * ez2 - ez1 * ey2;
        const fy = ez1 * ex2 - ex1 * ez2;
        const fz = ex1 * ey2 - ey1 * ex2;
        for (let k = 0; k < 3; k++) {
            const nx = norm.getX(i + k), ny = norm.getY(i + k), nz = norm.getZ(i + k);
            const len = Math.hypot(nx, ny, nz);
            assert.ok(Number.isFinite(len) && Math.abs(len - 1) < 1e-3, `${label}: non-unit normal`);
            if (nx > 0.7) hasPosX = true;
            if (nx < -0.7) hasNegX = true;
            if (nz > 0.7) hasPosZ = true;
            if (nz < -0.7) hasNegZ = true;
            if (ny > 0.9) hasPosY = true;
        }
        const avgNx = norm.getX(i) + norm.getX(i + 1) + norm.getX(i + 2);
        const avgNy = norm.getY(i) + norm.getY(i + 1) + norm.getY(i + 2);
        const avgNz = norm.getZ(i) + norm.getZ(i + 1) + norm.getZ(i + 2);
        assert.ok(fx * avgNx + fy * avgNy + fz * avgNz > -1e-6, `${label}: inverted triangle winding`);
    }
    assert.ok(hasPosX && hasNegX && hasPosZ && hasNegZ && hasPosY, `${label}: missing one of 4 sides or roof`);
}

function physicsFingerprint(world) {
    return world.bodies.map(b => ({
        mass: b.mass,
        x: Math.round(b.position.x * 1e3),
        y: Math.round(b.position.y * 1e3),
        z: Math.round(b.position.z * 1e3),
        shapes: b.shapes.map(s => ({
            type: s.type,
            he: s.halfExtents ? [s.halfExtents.x, s.halfExtents.y, s.halfExtents.z] : null,
            r: s.radius ?? null
        }))
    }));
}

function roadNetFingerprint(rn) {
    return JSON.stringify({
        avenuesX: rn.avenuesX,
        crossZ: rn.crossZ,
        roundabouts: rn.roundabouts,
        ribbons: rn.ribbons.length,
        terrainRoads: rn.terrainRoads.length
    });
}

function extractSaveBaseKeys(source) {
    const m = source.match(/const SAVE = \(\(\) => \{\s*const base = (\{[\s\S]*?\});/);
    assert.ok(m, 'Missing SAVE base definition');
    return Object.keys(vm.runInNewContext('(' + m[1] + ')')).sort();
}

function makeStubElement() {
    return {
        style: { setProperty() {} },
        classList: {
            _set: new Set(),
            add(c) { this._set.add(c); },
            remove(c) { this._set.delete(c); },
            contains(c) { return this._set.has(c); }
        },
        children: [],
        innerHTML: '',
        textContent: '',
        addEventListener(type, fn) { this[type] = fn; },
        appendChild(child) { this.children.push(child); }
    };
}

function expectRed(name, fn) {
    let failed = false;
    try {
        fn();
    } catch (err) {
        failed = true;
    }
    assert.ok(failed, `MUTATION MUST TURN RED but stayed GREEN: ${name}`);
    console.log(`  [MUTATION RED] ${name}`);
}

const builderSrc = section(html, '        // T-014B1: visual-only Site A', '        // T-014B1_END');
const batchSrc = section(html, '        function batchStaticMeshes()', '        // T-014B1: visual-only Site A');

function attachBuilder(h, src = builderSrc) {
    h.WORLD.showcaseSiteA = null;
    vm.runInContext(src + '\nthis.buildShowcaseSiteA = buildShowcaseSiteA; this.setShowcaseSiteAVisible = setShowcaseSiteAVisible;', h);
}

// =========================================================================
// Core validators (reused for production PASS and negative mutation RED)
// =========================================================================

function assertB1Site(h, sc) {
    assert.equal(sc.footprints.center.x, SITE_A_CENTER.x);
    assert.equal(sc.footprints.center.z, SITE_A_CENTER.z);
    const { buildingAShell, buildingARoof, buildingBShell, buildingBRoof, streetAsphalt, streetSidewalks } = sc.meshes;
    const aspBox = meshBounds(streetAsphalt);
    const swBox = meshBounds(streetSidewalks);
    const aBox = meshBounds(buildingAShell);
    const aRoofBox = meshBounds(buildingARoof);
    const bBox = meshBounds(buildingBShell);
    const bRoofBox = meshBounds(buildingBRoof);

    // Exact footprint extents (§2)
    assert.ok(Math.abs(aspBox.min.x - (-551)) < 1e-4 && Math.abs(aspBox.max.x - (-451)) < 1e-4, 'asphalt x != [-551,-451]');
    assert.ok(Math.abs(aspBox.min.z - (-795)) < 1e-4 && Math.abs(aspBox.max.z - (-785)) < 1e-4, 'asphalt z != [-795,-785]');
    assert.ok(Math.abs(swBox.min.x - (-551)) < 1e-4 && Math.abs(swBox.max.x - (-451)) < 1e-4, 'sidewalks x != [-551,-451]');
    assert.ok(Math.abs(swBox.min.z - (-799)) < 1e-4 && Math.abs(swBox.max.z - (-781)) < 1e-4, 'sidewalks z != [-799,-781]');
    assert.ok(Math.abs(aBox.min.x - (-539)) < 1e-4 && Math.abs(aBox.max.x - (-517)) < 1e-4, 'building A x != [-539,-517]');
    assert.ok(Math.abs(aBox.min.z - (-777)) < 1e-4 && Math.abs(aBox.max.z - (-763)) < 1e-4, 'building A z != [-777,-763]');
    assert.ok(aRoofBox.min.x >= -539 - 1e-4 && aRoofBox.max.x <= -517 + 1e-4 && aRoofBox.min.z >= -777 - 1e-4 && aRoofBox.max.z <= -763 + 1e-4, 'building A roof outside footprint');
    assert.ok(Math.abs(bBox.min.x - (-484)) < 1e-4 && Math.abs(bBox.max.x - (-461)) < 1e-4, 'building B x != [-484,-461]');
    assert.ok(Math.abs(bBox.min.z - (-821)) < 1e-4 && Math.abs(bBox.max.z - (-803)) < 1e-4, 'building B z != [-821,-803]');
    assert.ok(bRoofBox.min.x >= -484 - 1e-4 && bRoofBox.max.x <= -461 + 1e-4 && bRoofBox.min.z >= -821 - 1e-4 && bRoofBox.max.z <= -803 + 1e-4, 'building B roof outside footprint');

    // 4m clearances from sidewalks
    assert.ok(Math.abs((aBox.min.z - swBox.max.z) - 4) < 1e-4, 'Building A must sit 4m north of north sidewalk');
    assert.ok(Math.abs((swBox.min.z - bBox.max.z) - 4) < 1e-4, 'Building B must sit 4m south of south sidewalk');

    // Terrain height grounding checks on real production terrainHeight(x, z)
    const aspPos = streetAsphalt.geometry.attributes.position;
    for (let i = 0; i < aspPos.count; i++) {
        const x = aspPos.getX(i), y = aspPos.getY(i), z = aspPos.getZ(i);
        const expectedY = h.terrainHeight(x, z) + sc.footprints.asphalt.yOffset;
        assert.ok(sc.footprints.asphalt.yOffset >= 0.04 && sc.footprints.asphalt.yOffset <= 0.08, 'asphalt offset out of [0.04,0.08]');
        assert.ok(Math.abs(y - expectedY) < 1e-4, `asphalt y=${y} != terrainHeight(${x},${z})+offset=${expectedY}`);
    }
    const swPos = streetSidewalks.geometry.attributes.position;
    let swBaseMatches = 0, swTopMatches = 0;
    for (let i = 0; i < swPos.count; i++) {
        const x = swPos.getX(i), y = swPos.getY(i), z = swPos.getZ(i);
        const groundY = h.terrainHeight(x, z);
        const topY = groundY + sc.footprints.southSidewalk.topOffset;
        assert.ok(sc.footprints.southSidewalk.topOffset > sc.footprints.asphalt.yOffset && sc.footprints.southSidewalk.topOffset <= 0.35, 'sidewalk height invalid');
        if (Math.abs(y - groundY) < 1e-4) swBaseMatches++;
        else if (Math.abs(y - topY) < 1e-4) swTopMatches++;
        else assert.fail(`sidewalk vertex y=${y} neither groundY=${groundY} nor topY=${topY}`);
    }
    assert.ok(swBaseMatches > 0 && swTopMatches > 0, 'sidewalks missing base or top vertices');
    const expectedYA = Math.min(...EXPECTED_A_POLY.map(([x, z]) => h.terrainHeight(x, z)));
    const expectedYB = Math.min(...sc.footprints.buildingB.polygon.map(([x, z]) => h.terrainHeight(x, z)));
    assert.ok(Math.abs(aBox.min.y - expectedYA) < 1e-4, `Building A base y=${aBox.min.y} != terrainHeight=${expectedYA}`);
    assert.ok(Math.abs(bBox.min.y - expectedYB) < 1e-4, `Building B base y=${bBox.min.y} != terrainHeight=${expectedYB}`);

    // Non-overlap with ROAD_NET, existing city buildings, roofs, depots, trees
    const envelopes = [
        { name: 'street', minX: swBox.min.x, maxX: swBox.max.x, minZ: swBox.min.z, maxZ: swBox.max.z },
        { name: 'buildingA', minX: aBox.min.x, maxX: aBox.max.x, minZ: aBox.min.z, maxZ: aBox.max.z },
        { name: 'buildingB', minX: bBox.min.x, maxX: bBox.max.x, minZ: bBox.min.z, maxZ: bBox.max.z }
    ];
    for (const env of envelopes) {
        assert.ok(Number.isFinite(h.ROAD_NET.avenueHalf) && Number.isFinite(h.ROAD_NET.crossHalf), 'Missing ROAD_NET half widths');
        for (const ax of h.ROAD_NET.avenuesX) {
            const road = { minX: ax - h.ROAD_NET.avenueHalf, maxX: ax + h.ROAD_NET.avenueHalf, minZ: -1200, maxZ: 1200 };
            assert.ok(aabbGap(env, road) > 1, `${env.name} overlaps avenue x=${ax}`);
        }
        for (const cz of h.ROAD_NET.crossZ) {
            const road = { minX: -1200, maxX: 1200, minZ: cz - h.ROAD_NET.crossHalf, maxZ: cz + h.ROAD_NET.crossHalf };
            assert.ok(aabbGap(env, road) > 1, `${env.name} overlaps cross street z=${cz}`);
        }
        for (const rb of h.ROAD_NET.roundabouts) {
            const box = { minX: rb.x - rb.rOut, maxX: rb.x + rb.rOut, minZ: rb.z - rb.rOut, maxZ: rb.z + rb.rOut };
            assert.ok(aabbGap(env, box) > 1, `${env.name} overlaps roundabout (${rb.x},${rb.z})`);
        }
        for (const rib of h.ROAD_NET.ribbons) {
            for (const p of rib.pts) {
                const box = { minX: p.x - rib.half, maxX: p.x + rib.half, minZ: p.z - rib.half, maxZ: p.z + rib.half };
                assert.ok(aabbGap(env, box) > 1, `${env.name} overlaps ribbon ${rib.name}`);
            }
        }
        for (const b of [...h.city, ...h.WORLD.roofs]) {
            const box = { minX: b.x - b.w / 2, maxX: b.x + b.w / 2, minZ: b.z - b.d / 2, maxZ: b.z + b.d / 2 };
            assert.ok(aabbGap(env, box) > 1, `${env.name} overlaps existing city/roof at (${b.x},${b.z})`);
        }
        for (const d of h.depots) {
            const box = { minX: d.x - 4, maxX: d.x + 4, minZ: d.z - 4, maxZ: d.z + 4 };
            assert.ok(aabbGap(env, box) > 1, `${env.name} overlaps depot at (${d.x},${d.z})`);
        }
        for (const t of h.TREES.list) {
            const box = { minX: t.x - 1, maxX: t.x + 1, minZ: t.z - 1, maxZ: t.z + 1 };
            assert.ok(aabbGap(env, box) > 1, `${env.name} overlaps tree at (${t.x},${t.z})`);
        }
    }
}

function assertB1Shape(sc) {
    const { buildingAShell, buildingARoof, buildingBShell, buildingBRoof } = sc.meshes;
    assert.equal(JSON.stringify(sc.footprints.buildingA.polygon), JSON.stringify(EXPECTED_A_POLY), 'Building A L polygon mismatch');

    // Building A genuinely missing NW cutout quadrant (-539..-526, -770..-763)
    assert.equal(geometryCoversXZ(buildingAShell.geometry, -532.5, -766.5), false, 'Building A NW cutout must be empty (not a box)');
    assert.equal(geometryCoversXZ(buildingARoof.geometry, -532.5, -766.5), false, 'Building A roof must not cover NW cutout');
    // Both arms of L present
    assert.equal(geometryCoversXZ(buildingAShell.geometry, -532.5, -773.5), true, 'Building A west arm missing');
    assert.equal(geometryCoversXZ(buildingAShell.geometry, -521.5, -766.5), true, 'Building A north-east arm missing');

    // Building A upper street setback >= 1.2m (vertices above y=10.5 must be north of z = -777 + 1.2)
    const aPos = buildingAShell.geometry.attributes.position;
    let upperMinZ = Infinity, lowerMinZ = Infinity;
    for (let i = 0; i < aPos.count; i++) {
        const y = aPos.getY(i), z = aPos.getZ(i);
        if (y < sc.footprints.buildingA.baseY + 1.0) lowerMinZ = Math.min(lowerMinZ, z);
        if (y > sc.footprints.buildingA.baseY + 10.5) upperMinZ = Math.min(upperMinZ, z);
    }
    const actualSetback = upperMinZ - lowerMinZ;
    assert.ok(actualSetback >= 1.2 - 1e-4, `Building A street setback=${actualSetback.toFixed(2)}m < 1.2m`);
    const aMaxY = meshBounds(buildingAShell).max.y - sc.footprints.buildingA.baseY;
    assert.ok(aMaxY >= 15.5 && aMaxY <= 17.5, `Building A height ${aMaxY} outside expected 16-17m crown`);

    // Building B: true 10-segment quarter-circle arc at NW corner, center (-480,-807), r=4
    const bPos = buildingBShell.geometry.attributes.position;
    const arcPts = new Map();
    for (let i = 0; i < bPos.count; i++) {
        const x = bPos.getX(i), y = bPos.getY(i), z = bPos.getZ(i);
        if (Math.abs(y - sc.footprints.buildingB.baseY) > 1e-3) continue;
        if (x <= -480 + 1e-3 && z >= -807 - 1e-3) {
            const r = Math.hypot(x - (-480), z - (-807));
            if (Math.abs(r - 4.0) < 0.02) {
                const key = `${Math.round(x * 1e4)},${Math.round(z * 1e4)}`;
                arcPts.set(key, [x, z]);
            }
        }
    }
    assert.equal(arcPts.size, 11, `Building B must have 11 vertices (10 segments) on r=4 arc, got ${arcPts.size}`);
    // Verify the sharp corner (-484, -803) is truly cut away by the arc
    assert.equal(geometryCoversXZ(buildingBShell.geometry, -483.8, -803.2), false, 'Building B NW corner must be curved, not sharp');

    // Building B has distinct 2-level roof heights (main ~20-22m, upper ~23-25m)
    const bHeights = new Set();
    for (let i = 0; i < bPos.count; i++) {
        const y = Math.round((bPos.getY(i) - sc.footprints.buildingB.baseY) * 10) / 10;
        if (y > 1) bHeights.add(y);
    }
    const sortedBHeights = [...bHeights].sort((a, b) => a - b);
    assert.ok(sortedBHeights.length >= 2, `Building B needs >=2 roof levels, got ${sortedBHeights}`);
    assert.ok(sortedBHeights[0] >= 20 && sortedBHeights[0] <= 22, `Building B main level ${sortedBHeights[0]} outside 20-22m`);
    assert.ok(sortedBHeights.at(-1) >= 23 && sortedBHeights.at(-1) <= 25, `Building B upper level ${sortedBHeights.at(-1)} outside 23-25m`);

    // All 4 sides + roof + outward winding on both buildings
    checkUnitOutwardNormals(buildingAShell, 'buildingAShell');
    checkUnitOutwardNormals(buildingBShell, 'buildingBShell');
    assert.ok(triCount(buildingARoof.geometry) >= 24, 'Building A missing roof parapet/equipment');
    assert.ok(triCount(buildingBRoof.geometry) >= 48, 'Building B missing roof parapet/equipment');
}

function assertB1Budget(sc) {
    const { buildingAShell, buildingARoof, buildingBShell, buildingBRoof, streetAsphalt, streetSidewalks } = sc.meshes;
    const trisA = triCount(buildingAShell.geometry) + triCount(buildingARoof.geometry);
    const trisB = triCount(buildingBShell.geometry) + triCount(buildingBRoof.geometry);
    const trisStreet = triCount(streetAsphalt.geometry) + triCount(streetSidewalks.geometry);
    const trisTotal = trisA + trisB + trisStreet;
    assert.ok(trisA <= 400, `Building A triangles ${trisA} > 400`);
    assert.ok(trisB <= 900, `Building B triangles ${trisB} > 900`);
    assert.ok(trisA + trisB <= 1300, `A+B triangles ${trisA + trisB} > 1300`);
    assert.ok(trisStreet <= 120, `Street triangles ${trisStreet} > 120`);
    assert.ok(trisTotal <= 1420, `Total triangles ${trisTotal} > 1420`);

    const allMeshes = sc.group.children.filter(c => c.isMesh);
    const mats = new Set(allMeshes.map(m => m.material));
    assert.ok(mats.size <= 5, `Materials ${mats.size} > 5`);
    const texFields = ['map', 'emissiveMap', 'normalMap', 'roughnessMap', 'metalnessMap', 'aoMap', 'alphaMap', 'bumpMap'];
    for (const mat of mats) {
        for (const f of texFields) assert.equal(mat[f], null, `Material must not carry texture ${f}`);
    }
    for (const m of allMeshes) {
        assert.equal(m.castShadow, false, `${m.name}: castShadow must be false`);
    }
    return { trisA, trisB, trisStreet, trisTotal, matCount: mats.size, meshCount: allMeshes.length };
}

function visibleShowcaseMeshes(group) {
    if (!group.visible) return [];
    const list = [];
    group.traverse(o => { if (o.isMesh && o.visible) list.push(o); });
    return list;
}

function assertB1Render(h, sc) {
    const onMeshes = visibleShowcaseMeshes(sc.group);
    const buildingMeshes = onMeshes.filter(m => m.name.includes('building'));
    const streetMeshes = onMeshes.filter(m => m.name.includes('street'));
    assert.ok(buildingMeshes.length <= 4, `Building draw meshes ${buildingMeshes.length} > 4`);
    assert.ok(streetMeshes.length <= 2, `Street draw meshes ${streetMeshes.length} > 2`);
    assert.ok(onMeshes.length <= 6, `Total draw meshes ${onMeshes.length} > 6`);
    assert.equal(onMeshes.filter(m => m.castShadow).length, 0, 'Shadow-casting showcase meshes must be 0');

    const geoRefs = onMeshes.map(m => m.geometry);
    const matRefs = onMeshes.map(m => m.material);
    const sceneChildrenBefore = h.scene.children.length;

    // OFF -> 0 visible showcase meshes; other scene objects remain visible
    const nonShowcaseProbe = new THREE.Mesh(new THREE.BoxGeometry(1, 1, 1), new THREE.MeshStandardMaterial());
    h.scene.add(nonShowcaseProbe);
    h.setShowcaseSiteAVisible(false);
    assert.equal(visibleShowcaseMeshes(sc.group).length, 0, 'Showcase OFF must yield 0 visible meshes');
    assert.equal(nonShowcaseProbe.visible, true, 'Showcase OFF must not hide unrelated scene meshes');

    // ON -> exact same geometry & material references, no scene growth
    h.setShowcaseSiteAVisible(true);
    const backMeshes = visibleShowcaseMeshes(sc.group);
    assert.equal(backMeshes.length, onMeshes.length);
    for (let i = 0; i < onMeshes.length; i++) {
        assert.equal(backMeshes[i].geometry, geoRefs[i], 'Geometry recreated on ON/OFF');
        assert.equal(backMeshes[i].material, matRefs[i], 'Material recreated on ON/OFF');
    }
    h.scene.remove(nonShowcaseProbe);
    assert.equal(h.scene.children.length, sceneChildrenBefore, 'Scene child count drifted');

    // Verify batchStaticMeshes() still batches unrelated static meshes while leaving showcase meshes untouched
    const sharedMat = new THREE.MeshStandardMaterial({ color: 0x999999 });
    const s1 = new THREE.Mesh(new THREE.BoxGeometry(1, 1, 1), sharedMat);
    const s2 = new THREE.Mesh(new THREE.BoxGeometry(1, 1, 1), sharedMat);
    s2.position.set(5, 0, 0);
    h.scene.add(s1, s2);
    h.MISSION = { marker: new THREE.Object3D() };
    h.WORLD.pedestrians = [];
    vm.runInContext(batchSrc + '\nbatchStaticMeshes();', h);
    assert.equal(s1.parent, null, 'Global batchStaticMeshes must still merge unrelated static meshes');
    assert.equal(s2.parent, null, 'Global batchStaticMeshes must still merge unrelated static meshes');
    assert.equal(sc.group.children.length, onMeshes.length, 'batchStaticMeshes must not absorb showcase meshes');
    for (const m of onMeshes) assert.equal(m.parent, sc.group, 'Showcase mesh moved out of showcase group');
}

function assertB1Phys(before, h) {
    assert.deepEqual(physicsFingerprint(h.physicsWorld), before.physics, 'physicsWorld bodies/shapes changed');
    assert.equal(roadNetFingerprint(h.ROAD_NET), before.roadNet, 'ROAD_NET mutated');
    assert.equal(h.WORLD.buildings.length, before.buildings, 'WORLD.buildings changed');
    assert.equal(h.WORLD.roofs.length, before.roofs, 'WORLD.roofs changed');
    assert.equal(h.city.length, before.city, 'city parcels changed');
    assert.equal(h.TREES.list.length, before.trees, 'TREES.list changed');
    assert.equal(h.depots.length, before.depots, 'DELIVERY.depots changed');
    assert.deepEqual(extractSaveBaseKeys(html), ['collectedCrates', 'deliveries', 'jumps', 'owned', 'rewardCooldowns'], 'SAVE schema keys changed');
}

function setupTravelContext(h, overrideTravelSrc = null) {
    const nodes = new Map();
    const banners = [];
    Object.assign(h.document, {
        documentElement: {},
        addEventListener() {},
        createElement: makeStubElement,
        querySelector: () => null,
        querySelectorAll: () => [],
        getElementById(id) {
            if (!nodes.has(id)) nodes.set(id, makeStubElement());
            return nodes.get(id);
        }
    });
    Object.assign(h, {
        window: makeStubElement(),
        localStorage: { getItem: () => null },
        setTimeout: f => f(),
        drawWorldMap() {},
        districtName: () => 'VICE SUBURBS',
        WMAP: { open: false, scale: 0.35, sel: null, travelBlocked: false },
        MISSION: { active: null },
        SAVE: { owned: [], jumps: {}, deliveries: 0, collectedCrates: [], rewardCooldowns: {}, language: 'en' },
        showBanner(tFn, sFn) { banners.push({ title: typeof tFn === 'function' ? tFn() : tFn, sub: typeof sFn === 'function' ? sFn() : sFn }); }
    });
    const runtime = html.match(/<script>\s*\/\/ I18N_TABLE_START([\s\S]*?)<\/script>/)[1];
    if (!h.locale) vm.runInContext(runtime + '\nthis.locale = VH_I18N;', h);
    const travelCode = overrideTravelSrc || (
        section(html, '        function wmSelect(', '        // 導航點') +
        section(html, '        function setupWorldMap()', '        // ==================== 11.')
    );
    vm.runInContext(travelCode + '\nthis.FAST_TRAVEL_REF = FAST_TRAVEL;', h);
    return { nodes, banners };
}

function assertB1Travel(h, ctx) {
    const entries = h.arrivals;
    const siteEntries = entries.filter(t => t.id === 'SHOWCASE_SITE_A');
    assert.equal(siteEntries.length, 1, 'Expected exactly one SHOWCASE_SITE_A in FAST_TRAVEL');
    const site = siteEntries[0];
    assert.equal(entries.at(-1), site, 'SHOWCASE_SITE_A must be appended after MIDTOWN_W');
    assert.equal(site.x, -501);
    assert.equal(site.z, -790);
    assert.equal(site.h, 0);
    assert.ok(!('y' in site), 'SHOWCASE_SITE_A must rely on existing terrainHeight via teleportTo');

    // No extra Missions-modal button or return button added
    const missionsMarkup = section(html, 'id="missions-modal"', '<div role="tabpanel"');
    assert.ok(!missionsMarkup.includes('SHOWCASE_SITE_A'), 'Must not add Missions-modal button for Site A');
    assert.ok(!html.includes('showcase-return'), 'Must not add return button');

    const chips = h.document.getElementById('wm-chips').children;
    const car = h.WORLD.vehicles[0];
    const expectedGroundY = h.terrainHeight(-501, -790);

    for (const lang of ['en', 'zh-TW']) {
        h.locale.setLanguage(lang);
        assert.equal(site.name, EXPECTED_NAMES[lang], `${lang}: FAST_TRAVEL name mismatch`);
        chips.length = 0;
        h.setupWorldMap();
        const found = chips.filter(b => b.innerHTML.includes('data-map-location="SHOWCASE_SITE_A"'));
        assert.equal(found.length, 1, `${lang}: expected exactly one Site A world-map chip`);
        assert.ok(found[0].innerHTML.includes('>' + EXPECTED_NAMES[lang] + '<'), `${lang}: chip label mismatch`);

        // Select chip -> verify wm-sel-name & wm-sel-sub warning
        found[0].click();
        assert.equal(h.document.getElementById('wm-sel-name').textContent, EXPECTED_NAMES[lang], `${lang}: wm-sel-name mismatch`);
        assert.ok(h.document.getElementById('wm-sel-sub').textContent.includes(EXPECTED_WARNS[lang]), `${lang}: wm-sel-sub missing no-collision warning`);

        // (a) Active DELIVERY.job + Site A in CAR mode -> succeeds, preserves exact job identity/fields, clears STUNT.active & car motion
        h.STATE.mode = 'CAR';
        h.STATE.currentVehicle = car;
        car.chassisBody.position.set(80, 4, 90);
        car.chassisBody.velocity.set(18, 2, -14);
        car.chassisBody.angularVelocity.set(1, 2, 1);
        car.airTime = 1.4;
        car.airReady = true;
        car.rampAirborne = true;
        h.STUNT.active = { id: 'ramp_1', startX: 80 };
        const activeJob = { id: 'job_42', dest: { x: 100, z: 100, name: 'Test' }, progress: 0.5, startedAt: 12345 };
        vm.runInContext('DELIVERY', h).job = activeJob;
        const saveBefore = JSON.stringify(h.SAVE);
        const missionBefore = JSON.stringify(h.MISSION);
        ctx.banners.length = 0;

        found[0].click();
        h.document.getElementById('wm-travel').click();

        assert.equal(vm.runInContext('DELIVERY.job', h), activeJob, `${lang}: DELIVERY.job identity changed`);
        assert.deepEqual(vm.runInContext('DELIVERY.job', h), { id: 'job_42', dest: { x: 100, z: 100, name: 'Test' }, progress: 0.5, startedAt: 12345 }, `${lang}: DELIVERY.job fields mutated`);
        assert.equal(h.WMAP.travelBlocked, false, `${lang}: Site A must not set travelBlocked`);
        assert.deepEqual([car.chassisBody.position.x, car.chassisBody.position.z], [-501, -790], `${lang}: car did not teleport to Site A`);
        assert.ok(Math.abs(car.chassisBody.position.y - (expectedGroundY + 1.35)) < 1e-4, `${lang}: car y != terrainHeight + 1.35`);
        assert.equal(h.STUNT.active, null, `${lang}: STUNT.active not cleared on car teleport`);
        assert.equal(car.airTime, 0);
        assert.equal(car.airReady, false);
        assert.equal(car.rampAirborne, false);
        assert.deepEqual([car.chassisBody.velocity.x, car.chassisBody.velocity.y, car.chassisBody.velocity.z], [0, 0, 0]);
        assert.deepEqual([car.chassisBody.angularVelocity.x, car.chassisBody.angularVelocity.y, car.chassisBody.angularVelocity.z], [0, 0, 0]);
        assert.equal(JSON.stringify(h.SAVE), saveBefore, `${lang}: SAVE mutated on Site A travel`);
        assert.equal(JSON.stringify(h.MISSION), missionBefore, `${lang}: MISSION mutated on Site A travel`);
        assert.equal(ctx.banners.at(-1)?.sub, EXPECTED_NAMES[lang], `${lang}: banner subtitle mismatch`);

        // (b) Same active DELIVERY.job + ANY OTHER FAST_TRAVEL entry (OCEAN & MIDTOWN_W) -> BLOCKED, job intact
        for (const otherId of ['OCEAN', 'MIDTOWN_W']) {
            const otherChip = chips.find(b => b.innerHTML.includes(`data-map-location="${otherId}"`));
            assert.ok(otherChip, `Missing chip for ${otherId}`);
            car.chassisBody.position.set(42, 3, 42);
            otherChip.click();
            h.document.getElementById('wm-travel').click();
            assert.deepEqual([car.chassisBody.position.x, car.chassisBody.position.z], [42, 42], `${lang}: ${otherId} was NOT blocked during delivery`);
            assert.equal(vm.runInContext('DELIVERY.job', h), activeJob, `${lang}: job mutated on blocked ${otherId}`);
            assert.equal(h.WMAP.travelBlocked, true, `${lang}: travelBlocked not set for blocked ${otherId}`);
        }

        // (d) FOOT mode travel to Site A succeeds & stays FOOT mode (even with active job)
        h.STATE.mode = 'FOOT';
        h.STATE.currentVehicle = null;
        h.PLAYER.body.position.set(15, 2, 15);
        h.PLAYER.body.velocity.set(5, 0, 5);
        h.PLAYER.heading = 1.23;
        found[0].click();
        h.document.getElementById('wm-travel').click();
        assert.equal(h.STATE.mode, 'FOOT', `${lang}: FOOT mode changed`);
        assert.deepEqual([h.PLAYER.body.position.x, h.PLAYER.body.position.z], [-501, -790], `${lang}: foot did not teleport to Site A`);
        assert.ok(Math.abs(h.PLAYER.body.position.y - (expectedGroundY + 1.2)) < 1e-4, `${lang}: foot y != terrainHeight + 1.2`);
        assert.deepEqual([h.PLAYER.body.velocity.x, h.PLAYER.body.velocity.y, h.PLAYER.body.velocity.z], [0, 0, 0]);
        assert.equal(h.PLAYER.heading, 0);
        assert.equal(vm.runInContext('DELIVERY.job', h), activeJob);

        vm.runInContext('DELIVERY.job = null', h);
    }
}

function assertB1Repeat(h, sc) {
    const baseSceneLen = h.scene.children.length;
    const baseBodies = h.physicsWorld.bodies.length;
    const baseGeoUuids = Object.values(sc.meshes).map(m => m.geometry.uuid);
    const baseMatUuids = sc.materials.map(m => m.uuid);
    const site = h.arrivals.find(t => t.id === 'SHOWCASE_SITE_A');

    for (let r = 0; r < 3; r++) {
        h.fastTravelTo(site);
        h.fastTravelTo(site);
        h.locale.setLanguage(r % 2 === 0 ? 'zh-TW' : 'en');
        h.setShowcaseSiteAVisible(false);
        h.setShowcaseSiteAVisible(true);
        const again = h.buildShowcaseSiteA();
        assert.equal(again, sc, 'buildShowcaseSiteA must be idempotent');
    }
    assert.equal(h.scene.children.length, baseSceneLen, 'Scene children grew across repeats');
    assert.equal(sc.group.children.length, 6, 'Showcase group children grew across repeats');
    assert.equal(h.physicsWorld.bodies.length, baseBodies, 'Physics bodies grew across repeats');
    assert.deepEqual(Object.values(sc.meshes).map(m => m.geometry.uuid), baseGeoUuids, 'Geometries changed across repeats');
    assert.deepEqual(sc.materials.map(m => m.uuid), baseMatUuids, 'Materials changed across repeats');
}

function assertB1Compat(source = html) {
    // Startup wiring: buildShowcaseSiteA() called once, strictly after batchStaticMeshes()
    const startup = section(source, '        // ==================== 12. 啟動場景', '        setupControlsAndEvents();');
    const batchIdx = startup.indexOf('batchStaticMeshes();');
    const siteIdx = startup.indexOf('buildShowcaseSiteA();');
    assert.ok(batchIdx >= 0 && siteIdx > batchIdx, 'buildShowcaseSiteA() must run after batchStaticMeshes()');
    assert.equal((startup.match(/buildShowcaseSiteA\(\)/g) || []).length, 1, 'Expected exactly one startup buildShowcaseSiteA() call');
    // Test-only __VH exposure present
    assert.ok(source.includes('setShowcaseSiteAVisible'), 'Missing __VH setShowcaseSiteAVisible');
    // Existing FAST_TRAVEL intact
    const ft = vm.runInNewContext(section(source, '        const FAST_TRAVEL =', '        const WMAP =') + 'FAST_TRAVEL', { THREE, tr: k => k });
    assert.equal(ft.length, 12, 'Expected 10 original + MIDTOWN_W + SHOWCASE_SITE_A = 12 FAST_TRAVEL entries');
    assert.equal(ft[0].id, 'OCEAN');
    assert.equal(ft[10].id, 'MIDTOWN_W');
    assert.equal(ft[11].id, 'SHOWCASE_SITE_A');
    assert.deepEqual(extractSaveBaseKeys(source), ['collectedCrates', 'deliveries', 'jumps', 'owned', 'rewardCooldowns']);
}

// =========================================================================
// 1. Run full production verification on PHONE_LOW and DESKTOP_HIGH
// =========================================================================
console.log('=== T-014B1 Production Verification (Headless VM / Structural + Behavior) ===');
let lastHarness = null;
for (const preset of ['PHONE_LOW', 'DESKTOP_HIGH']) {
    const h = await collisionHarness(html, preset);
    Object.assign(h.WORLD, { buildings: [], roofs: [], cameraBlockers: [] });
    h.buildTestCityInfill(h.city, [new THREE.MeshStandardMaterial(), new THREE.MeshStandardMaterial()], [], []);
    const before = {
        physics: physicsFingerprint(h.physicsWorld),
        roadNet: roadNetFingerprint(h.ROAD_NET),
        buildings: h.WORLD.buildings.length,
        roofs: h.WORLD.roofs.length,
        city: h.city.length,
        trees: h.TREES.list.length,
        depots: h.depots.length
    };
    attachBuilder(h);
    const sc = h.buildShowcaseSiteA();
    assertB1Site(h, sc);
    assertB1Shape(sc);
    const budget = assertB1Budget(sc);
    assertB1Render(h, sc);
    assertB1Phys(before, h);
    const ctx = setupTravelContext(h);
    assertB1Travel(h, ctx);
    assertB1Repeat(h, sc);
    assertB1Compat(html);
    console.log(`PASS [${preset}]`, budget);
    lastHarness = h;
}

// =========================================================================
// 2. Deliberate negative mutations — EVERY §6 category MUST turn RED
// =========================================================================
console.log('=== T-014B1 Negative Mutation Verification (Every Mutation Must Turn RED) ===');

function withMutatedBuilder(mutBuilderSrc, fn) {
    const h = lastHarness;
    const prevSc = h.WORLD.showcaseSiteA;
    if (prevSc && prevSc.group.parent) prevSc.group.parent.remove(prevSc.group);
    const prevToggle = h.setShowcaseSiteAVisible;
    const prevBodies = h.physicsWorld.bodies.slice();
    const prevAvenues = h.ROAD_NET.avenuesX.slice();
    try {
        attachBuilder(h, mutBuilderSrc);
        fn(h);
    } finally {
        const cur = h.WORLD.showcaseSiteA;
        if (cur && cur !== prevSc && cur.group.parent) cur.group.parent.remove(cur.group);
        for (const c of h.scene.children.slice()) {
            if (c.name === 'showcase_site_a' && (!prevSc || c !== prevSc.group)) h.scene.remove(c);
        }
        while (h.physicsWorld.bodies.length > prevBodies.length) {
            h.physicsWorld.removeBody(h.physicsWorld.bodies[h.physicsWorld.bodies.length - 1]);
        }
        h.ROAD_NET.avenuesX.length = 0;
        h.ROAD_NET.avenuesX.push(...prevAvenues);
        attachBuilder(h, builderSrc);
        h.WORLD.showcaseSiteA = prevSc;
        if (prevSc && !prevSc.group.parent) h.scene.add(prevSc.group);
        h.setShowcaseSiteAVisible = prevToggle;
        vm.runInContext('DELIVERY.job = null', h);
    }
}

// B1-SITE mutations (including spec CHANGE 1 mandatory +0.5m y lift)
withMutatedBuilder(builderSrc.replace('[-539, -777], [-517, -777]', '[-539, -786], [-517, -786]'), h => {
    expectRed('B1-SITE: push Building A into street', () => assertB1Site(h, h.buildShowcaseSiteA()));
});
withMutatedBuilder(builderSrc.replace('[-551, -526, -501, -476, -451]', '[-605, -580, -555, -530, -505]'), h => {
    expectRed('B1-SITE: shift street onto x=-600 avenue', () => assertB1Site(h, h.buildShowcaseSiteA()));
});
{
    // Raise all added asphalt / sidewalk / building base y by +0.5m (spec §6 CHANGE 1)
    const liftedSrc = builderSrc
        .replace('const ASPHALT_Y_OFFSET = 0.05;', 'const ASPHALT_Y_OFFSET = 0.55;')
        .replace('const b00 = terrainHeight(x0, z0)', 'const b00 = terrainHeight(x0, z0) + 0.5')
        .replace('const yA = Math.min(', 'const yA = 0.5 + Math.min(')
        .replace('const yB = Math.min(', 'const yB = 0.5 + Math.min(');
    withMutatedBuilder(liftedSrc, h => {
        expectRed('B1-SITE: lift asphalt/sidewalk/building base y by +0.5m', () => assertB1Site(h, h.buildShowcaseSiteA()));
    });
}

// B1-SHAPE mutations
withMutatedBuilder(builderSrc.replace(
    'const aBasePts = [[-539, -777], [-517, -777], [-517, -763], [-526, -763], [-526, -770], [-539, -770]];',
    'const aBasePts = [[-539, -777], [-517, -777], [-517, -763], [-539, -763]];'
), h => {
    expectRed('B1-SHAPE: seal Building A L cutout into a plain box', () => assertB1Shape(h.buildShowcaseSiteA()));
});
withMutatedBuilder(builderSrc.replace('makeCurvedRect(-484, -461, -821, -803, 4.0, 10)', 'makeCurvedRect(-484, -461, -821, -803, 4.0, 1)'), h => {
    expectRed('B1-SHAPE: reduce Building B 10-seg arc to 1-seg chamfer', () => assertB1Shape(h.buildShowcaseSiteA()));
});
withMutatedBuilder(builderSrc.replace('[-538.4, -775.2], [-517.6, -775.2]', '[-538.4, -777.0], [-517.6, -777.0]'), h => {
    expectRed('B1-SHAPE: remove Building A street setback', () => assertB1Shape(h.buildShowcaseSiteA()));
});

// B1-BUDGET mutations
withMutatedBuilder(builderSrc.replace('mesh.castShadow = false;', 'mesh.castShadow = true;'), h => {
    expectRed('B1-BUDGET: enable castShadow=true on showcase mesh', () => assertB1Budget(h.buildShowcaseSiteA()));
});
withMutatedBuilder(builderSrc, h => {
    const sc = h.buildShowcaseSiteA();
    sc.materials[0].map = new THREE.DataTexture(new Uint8Array(4), 1, 1);
    expectRed('B1-BUDGET: attach DataTexture map to showcase material', () => assertB1Budget(sc));
});
withMutatedBuilder(builderSrc.replace('addCylinder(bRoofBuf, -465.5, -814.5, 1.4, yB + 23.8, yB + 24.9, 10);', 'addCylinder(bRoofBuf, -465.5, -814.5, 1.4, yB + 23.8, yB + 24.9, 300);'), h => {
    expectRed('B1-BUDGET: over-subdivide geometry beyond Building B 900-tri cap', () => assertB1Budget(h.buildShowcaseSiteA()));
});

// B1-RENDER mutations
withMutatedBuilder(builderSrc, h => {
    const sc = h.buildShowcaseSiteA();
    sc.group.add(new THREE.Mesh(new THREE.BoxGeometry(1, 1, 1), sc.materials[0]));
    expectRed('B1-RENDER: add extra unmerged mesh (7 > 6 draw calls)', () => assertB1Render(h, sc));
});
withMutatedBuilder(builderSrc, h => {
    const sc = h.buildShowcaseSiteA();
    h.setShowcaseSiteAVisible = () => true;
    expectRed('B1-RENDER: showcase remains visible when toggled OFF', () => assertB1Render(h, sc));
});

// B1-PHYS mutations
withMutatedBuilder(builderSrc, h => {
    const before = {
        physics: physicsFingerprint(h.physicsWorld),
        roadNet: roadNetFingerprint(h.ROAD_NET),
        buildings: h.WORLD.buildings.length,
        roofs: h.WORLD.roofs.length,
        city: h.city.length,
        trees: h.TREES.list.length,
        depots: h.depots.length
    };
    h.buildShowcaseSiteA();
    const extraBody = new CANNON.Body({ mass: 0 });
    extraBody.addShape(new CANNON.Box(new CANNON.Vec3(1, 1, 1)));
    h.physicsWorld.addBody(extraBody);
    expectRed('B1-PHYS: add one CANNON Box body', () => assertB1Phys(before, h));
});
withMutatedBuilder(builderSrc, h => {
    const before = {
        physics: physicsFingerprint(h.physicsWorld),
        roadNet: roadNetFingerprint(h.ROAD_NET),
        buildings: h.WORLD.buildings.length,
        roofs: h.WORLD.roofs.length,
        city: h.city.length,
        trees: h.TREES.list.length,
        depots: h.depots.length
    };
    h.buildShowcaseSiteA();
    h.ROAD_NET.avenuesX.push(-501);
    expectRed('B1-PHYS: mutate ROAD_NET.avenuesX', () => assertB1Phys(before, h));
});

// B1-TRAVEL mutations
const baseTravelSrc = section(html, '        function wmSelect(', '        // 導航點') +
    section(html, '        function setupWorldMap()', '        // ==================== 11.');
withMutatedBuilder(builderSrc, h => {
    const ctx = setupTravelContext(h, baseTravelSrc.replace("const bypassDelivery = !!(t && t.id === 'SHOWCASE_SITE_A');", 'const bypassDelivery = false;'));
    expectRed('B1-TRAVEL: block SHOWCASE_SITE_A during active DELIVERY.job', () => assertB1Travel(h, ctx));
});
withMutatedBuilder(builderSrc, h => {
    const ctx = setupTravelContext(h, baseTravelSrc.replace("const bypassDelivery = !!(t && t.id === 'SHOWCASE_SITE_A');", 'const bypassDelivery = true;'));
    expectRed('B1-TRAVEL: accidentally bypass DELIVERY.job guard for other destinations', () => assertB1Travel(h, ctx));
});
withMutatedBuilder(builderSrc, h => {
    const ctx = setupTravelContext(h, baseTravelSrc.replace('teleportTo(t.x, t.z, t.h || 0, y);', 'DELIVERY.job = null; teleportTo(t.x, t.z, t.h || 0, y);'));
    expectRed('B1-TRAVEL: clear DELIVERY.job during Site A fast travel', () => assertB1Travel(h, ctx));
});
withMutatedBuilder(builderSrc, h => {
    const ctx = setupTravelContext(h, baseTravelSrc.replace("sel.id === 'SHOWCASE_SITE_A' ? subBase + ' · ' + tr('showcase_site_a_warn') : subBase", 'subBase'));
    expectRed('B1-TRAVEL: omit no-collision warning from wm-sel-sub', () => assertB1Travel(h, ctx));
});
withMutatedBuilder(builderSrc, h => {
    const ctx = setupTravelContext(h, baseTravelSrc.replace('VH_I18N.name(t.name)', "'Site A'"));
    expectRed('B1-TRAVEL: shorten banner name instead of exact Showcase Site A (No Collision)', () => assertB1Travel(h, ctx));
});

// B1-REPEAT mutation
withMutatedBuilder(builderSrc.replace('if (WORLD.showcaseSiteA) return WORLD.showcaseSiteA;', ''), h => {
    const sc = h.buildShowcaseSiteA();
    setupTravelContext(h);
    expectRed('B1-REPEAT: non-idempotent builder duplicates showcase group on repeat call', () => assertB1Repeat(h, sc));
});

// B1-COMPAT mutation
{
    const badSaveHtml = html.replace('rewardCooldowns: {}', 'rewardCooldowns: {}, showcaseVisited: false');
    expectRed('B1-COMPAT: add new field to SAVE schema', () => assertB1Compat(badSaveHtml));
}

console.log('RESULT: PASS (B1-SITE/SHAPE/BUDGET/RENDER/PHYS/TRAVEL/REPEAT/COMPAT + 20 negative mutations RED)');
