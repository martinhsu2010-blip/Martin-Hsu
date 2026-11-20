// Run: node tools/test/traffic_audit.mjs [baseline-commit]
// Reproducible HEADLESS COMPONENT comparison, not a full-city/browser/device benchmark.
// Counts are source-generated placements + 60 s of recycle-manager calls while stationary.
// "Visible" means a radius-4 sphere intersects a 60-degree, 16:9 frustum within 200 units;
// no buildings/occlusion, no rendered screenshots and no driving simulation for these counts.
// Timing uses real Cannon.step and actual Kenney wheel/chassis bounds on the game's flat box
// ground. Cars are braked, all bodies start at y=1; city/decks/NPCs/props/rendering are absent.
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { performance } from 'node:perf_hooks';
import { harness, html, root, THREE, presets } from './traffic_harness.mjs';
const baselineCommit = process.argv[2] || '5dd882ac9c1cf66ed910c600f6f619f4dfa2a5a7';
const baseline = execFileSync('git', ['show', `${baselineCommit}:index.html`], { cwd: root, encoding: 'utf8', maxBuffer: 4 * 1024 * 1024 });
const viewpoints = [
    ['Spawn street', 98, 22, 0], ['Downtown south', -120, -240, 90],
    ['Downtown west', -420, 0, 180], ['Roundabout', -240, 0, 270],
    ['North avenue', 110, 600, 0], ['South avenue', -240, -720, 90],
    ['West highway', -680, -240, 0], ['Hill approach', -350, 360, 270],
    ['Suburb entry', -1000, -240, 270], ['Suburb loop', -1300, -420, 0]
];
function counts(h) {
    const pos = h.PLAYER.body.position;
    const frustum = new THREE.Frustum().setFromProjectionMatrix(new THREE.Matrix4().multiplyMatrices(h.camera.projectionMatrix, h.camera.matrixWorldInverse));
    const sphere = new THREE.Sphere(new THREE.Vector3(), 4);
    let nearby = 0, visible = 0, active = 0;
    for (const car of h.ordinary()) {
        if (!car.frozen) active++;
        const p = car.chassisBody.position;
        if (Math.hypot(p.x - pos.x, p.z - pos.z) > 200) continue;
        nearby++;
        if (car.chassisGroup.visible && frustum.intersectsSphere(sphere.set(p, 4))) visible++;
    }
    return { nearby, visible, active };
}
// --guard compares all quality presets against the same main commit. One loaded
// GLB primitive is one opaque color-pass submission (shadows/postFX are excluded).
const guard = process.argv.includes('--guard');
const selected = guard ? Object.keys(presets(html)) : ['PHONE_LOW', 'TABLET_MED', 'DESKTOP_HIGH'];
function structuralCalls(h) {
    let calls = 0;
    for (const v of h.ordinary()) {
        const p = v.chassisBody.position;
        if (!h.trafficVisible(p.x,p.y,p.z)) continue;
        for (const group of [v.carModel, ...v.wheelClones]) {
            group.traverseVisible(obj => { if (obj.isMesh) calls++; });
        }
    }
    return calls;
}
const records = [];
for (const preset of selected) {
    for (const [label, x, z, degrees] of viewpoints) {
        const record = { preset, view: label, x, z, heading: degrees };
        for (const [version, source] of [['baseline', baseline], ['candidate', html]]) {
            const fresh = { nearby: 0, visible: 0, active: 0 }, recycled = { ...fresh };
            const seeds = guard ? 1 : 5;
            for (let seed = 1; seed <= seeds; seed++) {
                const h = await harness(source, preset, seed);
                h.movePlayer(x, z, degrees * Math.PI / 180, h.terrainHeight(x, z) + 1);
                h.freeze();
                const initial = counts(h);
                if (guard) record[version + "FreshCalls"] = structuralCalls(h);
                for (const key in fresh) fresh[key] += initial[key] / seeds;
                for (let i = 0; i < 50; i++) { h.recycleTraffic(1.2); h.freeze(); }
                const final = counts(h);
                if (guard) record[version + "RecycledCalls"] = structuralCalls(h);
                for (const key in recycled) recycled[key] += final[key] / seeds;
                assert.ok(h.ordinary().every(v => v.modelKey === 'kenney' && !v.modelTemplate));
            }
            for (const obj of [fresh, recycled]) for (const key in obj) obj[key] = +obj[key].toFixed(2);
            record[version] = { fresh, recycled };
        }
        records.push(record);
    }
    console.error(`Counts completed: ${preset}`);
}
function quantile(values, fraction) { return values[Math.floor((values.length - 1) * fraction)]; }
const timings = [];
for (const preset of selected) {
    for (const [version, source] of [['baseline', baseline], ['candidate', html]]) {
        const samples = [], populations = [];
        for (let round = 0; round < 3; round++) {
            const h = await harness(source, preset, 1 + round);
            h.movePlayer(-240, 0, 0);
            for (let i = 0; i < 50; i++) { h.recycleTraffic(1.2); h.freeze(); }
            // Fixed flat-road workload: retain the manager's real active population; no later recycling.
            h.freeze();
            populations.push(h.ordinary().filter(v => !v.frozen).length);
            for (const v of h.WORLD.vehicles) {
                v.chassisBody.position.y = 1;
                v.chassisBody.velocity.setZero(); v.chassisBody.angularVelocity.setZero();
                v.chassisBody.aabbNeedsUpdate = true;
                for (let i = 0; i < 4; i++) { v.vehicle.applyEngineForce(0, i); v.vehicle.setBrake(35, i); }
            }
            h.physicsWorld.broadphase.dirty = true;
            for (let i = 0; i < 600; i++) h.physicsWorld.step(1 / 60);
            for (let i = 0; i < 1200; i++) {
                const start = performance.now(); h.physicsWorld.step(1 / 60);
                samples.push(performance.now() - start);
            }
        }
        samples.sort((a, b) => a - b);
        timings.push({ preset, version, activeOrdinary: populations, samples: samples.length,
            medianMs: +quantile(samples, .5).toFixed(4), p95Ms: +quantile(samples, .95).toFixed(4) });
    }
}
console.log(JSON.stringify({ baselineCommit, environment: { node: process.version, platform: process.platform, architecture: process.arch },
    limits: 'HEADLESS traffic component only. Spatial/frustum counts without occlusion or motion. Flat-ground physics without city/decks/NPCs/props. No browser startup/offline/device/FPS claim.',
    method: { countSeeds: guard ? [1] : [1,2,3,4,5], recycleCalls: 50, recycleDt: 1.2, nearbyRadius: 200, fov: 60, aspect: '16:9',
        physicsRounds: 3, warmupStepsPerRound: 600, sampleStepsPerRound: 1200, physicsDt: 1 / 60 },
    viewpoints: records, physicsWorldStep: timings }, null, 2));
