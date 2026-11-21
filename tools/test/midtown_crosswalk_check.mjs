// T-009 regression test: extracts and executes the REAL buildMidtownCrosswalks()
// from index.html with vendored Three.js r160. Structural/VM checks only;
// real Chromium draw-call and physics benchmarks belong to Claude (§6).
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const root = new URL('../../', import.meta.url);
const htmlPath = process.argv[2] ? new URL(process.argv[2], `file://${process.cwd()}/`) : new URL('index.html', root);
const html = fs.readFileSync(htmlPath, 'utf8');
const threeSrc = fs.readFileSync(new URL('libs/three/build/three.module.js', root), 'utf8');
const THREE = await import('data:text/javascript;base64,' + Buffer.from(threeSrc).toString('base64'));

function between(src, start, end) {
    const a = src.indexOf(start);
    assert.ok(a >= 0, `Missing marker: ${start}`);
    const b = src.indexOf(end, a);
    assert.ok(b > a, `Missing end marker: ${end}`);
    return src.slice(a, b);
}

// 1. Verify production wiring in index.html (builder exists, called once at startup, exposed via WORLD).
assert.ok(html.includes('function buildMidtownCrosswalks()'), 'Missing production buildMidtownCrosswalks()');
assert.match(html, /midtownCrosswalks:\s*null/, 'WORLD.midtownCrosswalks slot missing');
const startup = between(html, '        // ==================== 12. 啟動場景', '        setupControlsAndEvents();');
const buildWorldIdx = startup.indexOf('buildRealisticWorld();');
const buildCrossIdx = startup.indexOf('buildMidtownCrosswalks();');
const detailLayerIdx = startup.indexOf('if (o.isInstancedMesh) o.layers.set(DETAIL_LAYER)');
assert.ok(buildWorldIdx >= 0 && buildCrossIdx > buildWorldIdx && buildCrossIdx < detailLayerIdx,
    'buildMidtownCrosswalks() must run after buildRealisticWorld() and before DETAIL_LAYER traversal');
assert.equal((startup.match(/buildMidtownCrosswalks\(\)/g) || []).length, 1, 'Expected exactly one startup call');

const roadNetSrc = between(html, '        const ROAD_NET = {', '        // 沿 CatmullRom');
const builderSrc = between(html, '        function buildMidtownCrosswalks()', '        // ==================== 城市細節');

// Static check: no physics, timers, storage, textures, or remote URLs in builder.
for (const bad of ['CANNON', 'physicsWorld', 'addBody', 'addShape', 'requestAnimationFrame', 'setInterval',
    'setTimeout', 'localStorage', 'vh_save', 'fetch(', 'http://', 'https://', 'TextureLoader']) {
    assert.ok(!builderSrc.includes(bad), `buildMidtownCrosswalks() must not reference ${bad}`);
}

function runProductionBuilder() {
    const scene = new THREE.Scene();
    const world = { midtownCrosswalks: null };
    const seededBodies = [{ id: 'ground', shapes: [{ type: 'plane' }] }, { id: 'bldg', shapes: [{ type: 'box' }, { type: 'box' }] }];
    const physicsWorld = {
        bodies: seededBodies,
        addBody() { throw new Error('Forbidden physicsWorld.addBody() call'); },
    };
    const cannonSpy = new Proxy({}, { get(_, prop) { throw new Error(`Forbidden CANNON.${String(prop)} access`); } });
    // Deterministic PRNG seeded with 5019 to verify determinism (builder should not depend on randomness).
    let s = 5019;
    const seededMath = Object.create(Math);
    seededMath.random = () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; };

    const ctx = vm.createContext({ THREE, Math: seededMath, console, scene, WORLD: world, physicsWorld, CANNON: cannonSpy });
    vm.runInContext(roadNetSrc + '\n' + builderSrc + '\nthis.ROAD_NET = ROAD_NET;', ctx);
    ctx.ROAD_NET.routes = [
        { name: 'R0', pts: [{ x: 0, y: 0.06, z: -400 }, { x: 0, y: 0.06, z: -320 }] },
        { name: 'R1', pts: [{ x: -120, y: 0.06, z: -400 }, { x: -120, y: 0.06, z: -320 }] },
    ];

    const bodiesBefore = physicsWorld.bodies.length;
    const shapesBefore = physicsWorld.bodies.reduce((n, b) => n + b.shapes.length, 0);
    const roadSnapBefore = JSON.stringify({
        avenuesX: ctx.ROAD_NET.avenuesX, crossZ: ctx.ROAD_NET.crossZ,
        avenueHalf: ctx.ROAD_NET.avenueHalf, crossHalf: ctx.ROAD_NET.crossHalf,
        roundabouts: ctx.ROAD_NET.roundabouts, routes: ctx.ROAD_NET.routes,
    });

    const mesh = ctx.buildMidtownCrosswalks();

    const bodiesAfter = physicsWorld.bodies.length;
    const shapesAfter = physicsWorld.bodies.reduce((n, b) => n + b.shapes.length, 0);
    const roadSnapAfter = JSON.stringify({
        avenuesX: ctx.ROAD_NET.avenuesX, crossZ: ctx.ROAD_NET.crossZ,
        avenueHalf: ctx.ROAD_NET.avenueHalf, crossHalf: ctx.ROAD_NET.crossHalf,
        roundabouts: ctx.ROAD_NET.roundabouts, routes: ctx.ROAD_NET.routes,
    });

    return { mesh, scene, world, ctx, bodiesBefore, bodiesAfter, shapesBefore, shapesAfter, roadSnapBefore, roadSnapAfter };
}

const run1 = runProductionBuilder();
const { mesh, scene, world, ctx } = run1;

// R2: One InstancedMesh, count 32, material & shadow constraints, single scene mesh, idempotent rebuild.
assert.ok(mesh && mesh.isInstancedMesh && mesh instanceof THREE.InstancedMesh, 'Expected a THREE.InstancedMesh');
assert.equal(world.midtownCrosswalks, mesh, 'WORLD.midtownCrosswalks must reference the created InstancedMesh');
assert.equal(mesh.count, 32, `Expected 32 stripe instances, got ${mesh.count}`);
const drawMeshes = [];
scene.traverse(o => { if (o.isMesh) drawMeshes.push(o); });
assert.equal(drawMeshes.length, 1, `Expected exactly 1 draw-submitting mesh in scene, got ${drawMeshes.length}`);
assert.equal(drawMeshes[0], mesh, 'Only draw mesh in scene must be WORLD.midtownCrosswalks');

assert.equal(mesh.castShadow, false, 'Crosswalks must have castShadow=false');
assert.equal(mesh.frustumCulled, true, 'Crosswalks must retain frustumCulled=true');
assert.ok(mesh.boundingSphere && Number.isFinite(mesh.boundingSphere.radius) && mesh.boundingSphere.radius > 50,
    'InstancedMesh must compute a valid boundingSphere covering all stripes');
const remoteDist = mesh.boundingSphere.center.distanceTo(new THREE.Vector3(110, 0, 650));
assert.ok(remoteDist > mesh.boundingSphere.radius + 500, 'Remote control scene (110,650) must be well outside boundingSphere');

assert.ok(mesh.material && !Array.isArray(mesh.material), 'Expected single shared material');
assert.equal(mesh.material.transparent, false, 'Crosswalk material must be opaque (transparent=false)');
assert.ok(mesh.material.roughness >= 0.85, `Expected roughness >= 0.85, got ${mesh.material.roughness}`);
assert.equal(mesh.material.metalness, 0, `Expected metalness === 0, got ${mesh.material.metalness}`);
assert.equal(mesh.material.map, null, 'Crosswalk material must not attach external texture map');
assert.equal(mesh.material.emissive.getHex(), 0, 'Crosswalk material must be non-emissive');

// Idempotency: second call must not add another mesh to scene.
const second = ctx.buildMidtownCrosswalks();
assert.equal(second, mesh, 'Second buildMidtownCrosswalks() call must return existing mesh');
assert.equal(scene.children.length, 1, 'Second call must not duplicate scene children');

// R1: Geometry dimensions, instance matrix orientation, exact 32 coordinates at (-120,-360) and (0,-360).
const params = mesh.geometry.parameters;
assert.ok(params && Math.abs(params.width - 1.6) <= 0.005 && Math.abs(params.height - 2.8) <= 0.005,
    `Expected PlaneGeometry(1.6, 2.8), got ${JSON.stringify(params)}`);

const expectedCoords = [];
for (const [ax, cz] of [[-120, -360], [0, -360]]) {
    for (const dz of [-14.0, 14.0]) {
        for (let i = 0; i < 8; i++) expectedCoords.push({ ax, cz, x: ax + (i - 3.5) * 2.6, y: 0.085, z: cz + dz });
    }
}
const matched = new Set();
const mat4 = new THREE.Matrix4();
const pos = new THREE.Vector3(), quat = new THREE.Quaternion(), scale = new THREE.Vector3();
const upCheck = new THREE.Vector3(), xAxis = new THREE.Vector3(), yAxis = new THREE.Vector3();

for (let i = 0; i < mesh.count; i++) {
    mesh.getMatrixAt(i, mat4);
    mat4.decompose(pos, quat, scale);
    assert.ok(Math.abs(scale.x - 1) <= 0.005 && Math.abs(scale.y - 1) <= 0.005 && Math.abs(scale.z - 1) <= 0.005,
        `Instance ${i} scale must be (1,1,1)`);
    upCheck.set(0, 0, 1).applyQuaternion(quat);
    assert.ok(Math.abs(upCheck.x) <= 0.005 && Math.abs(upCheck.y - 1) <= 0.005 && Math.abs(upCheck.z) <= 0.005,
        `Instance ${i} plane normal must face +Y, got (${upCheck.x.toFixed(3)},${upCheck.y.toFixed(3)},${upCheck.z.toFixed(3)})`);
    xAxis.set(1, 0, 0).applyQuaternion(quat);
    yAxis.set(0, 1, 0).applyQuaternion(quat);
    assert.ok(Math.abs(Math.abs(xAxis.x) - 1) <= 0.005 && Math.abs(Math.abs(yAxis.z) - 1) <= 0.005,
        `Instance ${i} must align 1.6m along X and 2.8m along Z`);
    assert.ok(pos.y > 0.06 && pos.y <= 0.12 && Math.abs(pos.y - 0.085) <= 0.005,
        `Instance ${i} y must be 0.085m (<=0.12m), got ${pos.y}`);
    assert.ok(Math.abs(pos.x - (-240)) > 20, `Instance ${i} must NOT be placed at deprecated (-240,-360)`);

    const matchIdx = expectedCoords.findIndex((e, idx) =>
        !matched.has(idx) && Math.abs(pos.x - e.x) <= 0.005 && Math.abs(pos.z - e.z) <= 0.005);
    assert.ok(matchIdx >= 0, `Instance ${i} at (${pos.x.toFixed(3)}, ${pos.y.toFixed(3)}, ${pos.z.toFixed(3)}) does not match any §3.1 target`);
    const exp = expectedCoords[matchIdx];
    assert.ok(Math.abs(pos.x - exp.ax) + 0.8 <= ctx.ROAD_NET.avenueHalf + 0.005, `Instance ${i} exceeds avenueHalf`);
    assert.ok(Math.abs(pos.z - exp.cz) - 1.4 > 11.2, `Instance ${i} overlaps intersection pad (cz +/- 11.2m)`);
    matched.add(matchIdx);
}
assert.equal(matched.size, 32, 'All 32 expected stripe coordinates must be matched 1-to-1');

// R3: Physics bodies/shapes delta === 0 and ROAD_NET / routes unchanged.
assert.equal(run1.bodiesAfter - run1.bodiesBefore, 0, 'Must add 0 Cannon bodies');
assert.equal(run1.shapesAfter - run1.shapesBefore, 0, 'Must add 0 Cannon shapes');
assert.equal(run1.roadSnapAfter, run1.roadSnapBefore, 'ROAD_NET and routes must remain unchanged');

// R4: Determinism across two independent runs with seed 5019.
const run2 = runProductionBuilder();
assert.deepEqual([...run1.mesh.instanceMatrix.array], [...run2.mesh.instanceMatrix.array], 'Matrices must be deterministic');
assert.equal(run1.mesh.material.color.getHex(), run2.mesh.material.color.getHex(), 'Material color must be deterministic');
assert.equal(run1.mesh.material.roughness, run2.mesh.material.roughness, 'Material roughness must be deterministic');

console.log('PASS: R1 positions/orientation/dimensions — 32 stripes at (-120,-360) and (0,-360), z +/-14m, y=0.085m, inside avenueHalf & outside pads');
console.log('PASS: R2 single InstancedMesh (count=32), opaque matte white, castShadow=false, valid boundingSphere, idempotent');
console.log('PASS: R3 +0 physics bodies/shapes, ROAD_NET & routes unchanged; R4 deterministic across runs');
console.log('RESULT: PASS (VM/Three.js production builder regression check; Chromium draw calls, physics timing & device checks remain separate)');
