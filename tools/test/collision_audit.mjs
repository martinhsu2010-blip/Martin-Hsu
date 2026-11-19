// Run: node tools/test/collision_audit.mjs [baseline-commit]
// HEADLESS COMPONENT timing: actual vehicles, all suburban compound bodies and active trunks,
// on the original flat ground. No city/deck/terrain colliders, NPCs, props, renderer or FPS claim.
import { execFileSync } from 'node:child_process';
import { performance } from 'node:perf_hooks';
import { collisionHarness, html, root } from './collision_harness.mjs';
const commit = process.argv[2] || 'e9c8229b218946954e8d6d3a80dab096379fab76';
const base = execFileSync('git', ['show', `${commit}:index.html`], { cwd: root, encoding: 'utf8', maxBuffer: 4e6 });
const results = [];
for (const preset of ['PHONE_LOW', 'TABLET_MED', 'DESKTOP_HIGH']) {
    for (const [name, x, z] of [['Spawn', 98, 22], ['Suburb road', -1100, -260], ['Hill road', -600, 390]]) {
        for (const [version, source] of [['before', base], ['after', html]]) {
            const h = await collisionHarness(source, preset), values = [], refresh = [];
            h.selectObserver(x, z); h.freeze(); h.refreshTreeColliders?.(0, true);
            // Match the prior traffic benchmark's stationary flat-ground workload. All vehicle
            // chassis start at y=1 with brakes; no controller/recycling changes during sampling.
            for (const car of h.WORLD.vehicles) {
                car.chassisBody.position.y = 1; car.chassisBody.aabbNeedsUpdate = true;
                car.chassisBody.velocity.setZero(); car.chassisBody.angularVelocity.setZero();
                for (let i = 0; i < 4; i++) { car.vehicle.applyEngineForce(0, i); car.vehicle.setBrake(35, i); }
            }
            h.physicsWorld.broadphase.dirty = true;
            for (let i = 0; i < 600; i++) h.physicsWorld.step(1 / 60);
            for (let i = 0; i < 1800; i++) {
                const start = performance.now(); h.physicsWorld.step(1 / 60); values.push(performance.now() - start);
            }
            const activeTrees = h.TREE_COLLIDERS?.active.length || 0;
            if (h.refreshTreeColliders) for (let i = 0; i < 100; i++) {
                const start = performance.now(); h.refreshTreeColliders(.5); refresh.push(performance.now() - start);
            }
            values.sort((a,b) => a-b); refresh.sort((a,b) => a-b);
            const q = (v, f) => v.length ? +v[Math.floor((v.length - 1) * f)].toFixed(4) : null;
            results.push({ preset, view: name, x, z, version, houseBodies: h.houseBodies.length, activeTrees,
                totalTrees: h.TREES.list.length, activeVehicles: h.WORLD.vehicles.filter(v => v.chassisBody.world === h.physicsWorld).length,
                medianStepMs: q(values,.5), p95StepMs: q(values,.95), medianRefreshMs: q(refresh,.5), p95RefreshMs: q(refresh,.95) });
        }
    }
    console.error(`Completed: ${preset}`);
}
console.log(JSON.stringify({ base: commit, environment: { node: process.version, platform: process.platform, arch: process.arch },
    method: { warmupSteps: 600, timedSteps: 1800, dt: 1/60, refreshSamples: 100 },
    limits: 'HEADLESS COMPONENT timing on flat ground; no full-city, terrain, browser, rendering or device-FPS measurement', results }, null, 2));
