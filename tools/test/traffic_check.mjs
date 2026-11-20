// Run: node tools/test/traffic_check.mjs
// Source/component regressions, not browser startup, rendered-model or real-device certification.
import assert from 'node:assert/strict';
import vm from 'node:vm';
import { harness, html, presets, kenney, CANNON, THREE } from './traffic_harness.mjs';
const expected = { PHONE_LOW: 22, PHONE_MED: 30, TABLET_LOW: 28, TABLET_MED: 32, TABLET_HIGH: 46,
    DESKTOP_MED: 40, DESKTOP_HIGH: 52, DESKTOP_ULTRA: 68, IGPU_LOW: 20, IGPU_MED: 34, IGPU_HIGH: 44 };
assert.deepEqual(presets(html), expected);
const types = ['sedan', 'suv', 'hatchback-sports', 'taxi', 'van', 'sedan-sports', 'suv-luxury', 'truck', 'delivery', 'garbage-truck', 'ambulance'];
assert.deepEqual(kenney.scenes.map(s => s.name).sort(), [...types].sort());
function distance(a, b) { return Math.hypot(a.x - b.x, a.z - b.z); }
function noFerrari(h, loaded = true) {
    for (const v of h.ordinary()) {
        assert.equal(v.modelKey, 'kenney'); assert.ok(types.includes(v.kenneyType));
        assert.equal(!!v.customApplied, loaded); assert.ok(!v.modelTemplate);
        if (loaded) assert.ok(v.carModel && !v.fallbackVisualGroup.visible && v.wheelClones.length === 4);
        else assert.ok(v.fallbackVisualGroup.visible);
        const oldModel = v.carModel;
        v.applyFerrariModel(new THREE.Group()); v.setDetail(true); v.setDetail(false);
        assert.equal(v.carModel, oldModel); assert.ok(!v.modelTemplate);
    }
}
let fresh = 0, recycled = 0, movedTotal = 0;
for (const [preset, count] of Object.entries(expected)) {
    for (let seed = 1; seed <= 5; seed++) {
        const h = await harness(html, preset, seed), cars = h.ordinary();
        assert.equal(cars.length, count); noFerrari(h); fresh++;
        assert.deepEqual(Array.from(h.KENNEY_TYPES, t => [t[0], t[1]]), types.map((t, i) => [t, [6,4,3,3,3,2,2,2,2,1,1][i]]));
        assert.deepEqual(Array.from(h.WORLD.vehicles.filter(v => !v.isAI && !v.isPolice), v => [v.name, v.modelKey]),
            [['Ferrari GT', null], ['Apex 4x4', null], ['VCPD Shelby GT500', 'fordcop']]);
        const parkedNearSpawn = h.WORLD.vehicles.filter(v => !v.isAI && !v.isPolice &&
            distance(v.chassisBody.position, h.PLAYER.body.position) <= 60);
        assert.deepEqual(Array.from(parkedNearSpawn, v => [v.name, v.color, v.modelKey]),
            [['Ferrari GT', 0xdc2626, null]]);
        assert.equal(h.WORLD.policeUnits.length, 2);
        assert.ok(h.WORLD.policeUnits.every(v => v.modelKey === 'fordcop' && !v.chassisGroup.visible));
        for (const v of cars) {
            for (const other of h.WORLD.vehicles) {
                if (other === v || !other.chassisGroup.visible) continue;
                assert.ok(distance(v.chassisBody.position, other.chassisBody.position) >= (other === h.WORLD.vehicles[0] ? 25 : 20) - 1e-8, `${preset} initial overlap`);
            }
            assert.ok(distance(v.chassisBody.position, h.PLAYER.body.position) >= 25);
        }
        // Intercept actual placements to check every insertion, not only the final snapshot.
        let moved = 0;
        const place = h.Vehicle.prototype.placeOnRoute;
        h.Vehicle.prototype.placeOnRoute = function (...args) {
            const before = this.chassisBody.position.clone();
            assert.ok(distance(before, h.PLAYER.body.position) > 120);
            assert.equal(h.trafficVisible(before.x, before.y, before.z), false);
            place.apply(this, args);
            const p = this.chassisBody.position;
            assert.ok(distance(p, h.PLAYER.body.position) >= 30);
            assert.equal(h.trafficVisible(p.x, p.y, p.z), false);
            for (const other of h.WORLD.vehicles) if (other !== this && other.chassisGroup.visible) {
                assert.ok(distance(p, other.chassisBody.position) >= 30 - 1e-8, `${preset} insertion overlap`);
            }
            moved++;
        };
        const identities = [...h.WORLD.vehicles], callbacks = cars.map(v => v.vehicle.preStepCallback);
        // Five independent seeded reloads, each recycled at five locations/headings for 60 seconds.
        for (let view = 0; view < 5; view++) {
            h.movePlayer(-240 + view * 65, -240 + view * 120, view * Math.PI / 2);
            for (let i = 0; i < 50; i++) h.recycleTraffic(1.2);
        }
        assert.ok(moved > 0, `${preset} never recycled`);
        assert.deepEqual([...h.WORLD.vehicles], identities);
        for (let i = 0; i < cars.length; i++) assert.equal(cars[i].vehicle.preStepCallback, callbacks[i]);
        noFerrari(h); recycled++; movedTotal += moved;
    }
}
console.log(`PASS: exact 11 pools; ${fresh} fresh + ${recycled} recycled component loads (5+5 per preset), ${movedTotal} safe insertions, 0 AI Ferrari; parked cars and Ford police preserved`);

const failed = await harness(html, 'DESKTOP_ULTRA', 1, true);
noFerrari(failed, false); assert.ok(failed.warnings.length > 0);
const h = await harness(), car = h.ordinary()[0];
for (const model of [undefined, 'porsche911', 'fordcop']) {
    const v = new h.Vehicle({ isAI: true, model });
    assert.equal(v.modelKey, 'kenney'); v.applyFerrariModel(new THREE.Group()); assert.ok(!v.modelTemplate);
    v.vehicle.removeFromWorld(h.physicsWorld);
}
const missing = new h.Vehicle({ isAI: true, kenneyType: 'absent-subtype' });
missing.applyCustomModel(kenney); assert.ok(!missing.customApplied && missing.fallbackVisualGroup.visible);
missing.vehicle.removeFromWorld(h.physicsWorld);
console.log('PASS: rejected/missing assets retain geometric fallback; missing or incorrect ordinary-AI model config cannot select Ferrari');

// Hold one car on a flat street and move only the player. Activation runs BEFORE stepping.
car.chassisBody.position.set(0, 1, 0); h.resetTrafficBody(car);
const callback = car.vehicle.preStepCallback;
for (let i = 0; i < 100; i++) {
    h.movePlayer(250, 0); h.STATE.time += 3; h.updateTrafficPhysics();
    assert.ok(car.frozen && !h.physicsWorld.bodies.includes(car.chassisBody));
    assert.ok(!h.physicsWorld.hasEventListener('preStep', callback));
    car.chassisBody.velocity.set(60, -80, 25); car.chassisBody.angularVelocity.set(40, 40, 40);
    car.chassisBody.force.set(500, 500, 500); car.chassisBody.torque.set(500, 500, 500);
    car.vehicle.wheelInfos[0].engineForce = -9999; car.vehicle.wheelInfos[0].brake = 200;
    car.vehicle.wheelInfos[0].raycastResult.hasHit = true;
    h.movePlayer(161, 0); h.updateTrafficPhysics(); assert.ok(car.frozen);
    h.movePlayer(159, 0); h.updateTrafficPhysics(); assert.ok(!car.frozen);
    assert.equal(car.vehicle.preStepCallback, callback);
    assert.equal(h.physicsWorld._listeners.preStep.filter(f => f === callback).length, 1);
    for (const v of [car.chassisBody.velocity, car.chassisBody.angularVelocity, car.chassisBody.force, car.chassisBody.torque]) assert.ok(v.isZero());
    assert.deepEqual(car.chassisBody.previousPosition, car.chassisBody.position);
    assert.deepEqual(car.chassisBody.interpolatedPosition, car.chassisBody.position);
    assert.deepEqual(car.chassisBody.previousQuaternion, car.chassisBody.quaternion);
    assert.ok(!car.chassisBody.aabbNeedsUpdate && h.physicsWorld.broadphase.dirty);
    assert.equal(car.vehicle.wheelInfos[0].engineForce, 0); assert.equal(car.vehicle.wheelInfos[0].brake, 0);
    assert.equal(car.vehicle.wheelInfos[0].raycastResult.hasHit, false);
    h.movePlayer(199, 0); h.updateTrafficPhysics(); assert.ok(!car.frozen); // hysteresis
}
// A 90 m/s approach crosses the wake boundary well before the mandatory 100-unit region.
for (let x = 250; x >= 0; x -= 1.5) {
    h.movePlayer(x, 0); h.updateTrafficPhysics();
    if (x <= 100) assert.ok(!car.frozen && car.vehicle.world === h.physicsWorld);
}
// Teleport: deliberately stale visual anchor; manager must use the physical player body.
h.movePlayer(250, 0); h.STATE.time += 3; h.updateTrafficPhysics(); assert.ok(car.frozen);
h.PLAYER.body.position.set(10, 1, 0); h.updateTrafficPhysics(); assert.ok(!car.frozen);
// Entering a formerly frozen traffic car must also restore its wheels/body.
h.movePlayer(250, 0); h.STATE.time += 3; h.updateTrafficPhysics(); assert.ok(car.frozen);
car.isAI = false; h.STATE.currentVehicle = car; h.STATE.mode = 'CAR'; h.updateTrafficPhysics();
assert.ok(!car.frozen && car.vehicle.world === h.physicsWorld);
car.isAI = true; h.STATE.currentVehicle = null; h.STATE.mode = 'FOOT';
console.log('PASS: 100 freeze/wake cycles keep one callback; hysteresis, 90 m/s approach, teleport, captured car, force/wheel/AABB/interpolation reset');
// Review fix: an on-screen car beyond 200 units keeps driving; a frozen car that comes on screen wakes.
h.movePlayer(0, -300, 0); h.STATE.time += 3; h.updateTrafficPhysics(); assert.ok(!car.frozen, 'visible car at 300 units must stay active');
h.movePlayer(0, -300, Math.PI); h.updateTrafficPhysics(); assert.ok(!car.frozen, 'freeze waits for the hide grace period');
h.STATE.time += 3; h.updateTrafficPhysics(); assert.ok(car.frozen, 'off-screen car beyond 200 units freezes after the grace period');
h.movePlayer(0, -300, 0); h.updateTrafficPhysics(); assert.ok(!car.frozen && car.vehicle.world === h.physicsWorld, 'frozen car wakes when it comes on screen');
console.log('PASS: on-screen traffic stays active beyond 200 units; off-screen cars freeze after a 2 s grace and wake when seen');

// Upside-down recovery must not bypass the 120-unit or visible-car protections.
const p = await harness(); const protectedCar = p.ordinary()[0];
p.movePlayer(0, 0); protectedCar.chassisBody.position.set(80, 1, 0);
protectedCar.chassisBody.quaternion.setFromAxisAngle(new CANNON.Vec3(0, 0, 1), Math.PI);
p.resetTrafficBody(protectedCar);
for (let i = 0; i < 7; i++) protectedCar.updateRouteAI(1, 0);
assert.ok(protectedCar.trafficRecovery); const protectedPosition = protectedCar.chassisBody.position.clone();
for (let i = 0; i < 20; i++) p.recycleTraffic(1.2);
assert.deepEqual(protectedCar.chassisBody.position, protectedPosition);
protectedCar.chassisBody.position.set(0, 1, 300); p.resetTrafficBody(protectedCar);
p.updateTrafficFrustum(); assert.ok(p.trafficVisible(0, 1, 300));
for (let i = 0; i < 20; i++) p.recycleTraffic(1.2);
assert.equal(protectedCar.chassisBody.position.z, 300);
console.log('PASS: nearby upside-down recovery and distant visible vehicles never teleport');

// Drift alone must persist for >2 s, even if the car freezes while displaced.
const drift = await harness(), displaced = drift.ordinary()[0];
displaced.chassisBody.position.set(700, 1, 700);
for (const now of [0, 1, 2]) {
    drift.STATE.time = now;
    drift.updateTrafficPhysics();
    assert.ok(!displaced.trafficRecovery);
}
drift.STATE.time = 2.25;
drift.updateTrafficPhysics();
assert.ok(displaced.frozen && displaced.trafficRecovery);
assert.equal(drift.trafficDiagnostics().offRoute, 1);
for (let i = 0; i < 100 && displaced.trafficRecovery; i++) drift.recycleTraffic(1.2);
assert.ok(!displaced.trafficRecovery);
assert.equal(drift.trafficDiagnostics().offRoute, 0);

// Deny even an otherwise-clear slot when its init-time legality flag is false.
for (const route of drift.ROAD_NET.routes) for (const q of route) q.trafficLegal = false;
assert.equal(drift.findInitialTrafficSlot(0, 0), false);
displaced.chassisBody.position.set(700, 1, 700);
displaced.trafficRecovery = true;
for (let i = 0; i < 10; i++) drift.recycleTraffic(1.2);
assert.equal(displaced.chassisBody.position.x, 700);
console.log('PASS: sustained off-route detection, gated recovery, illegal initial and recycle slot rejection');

// Exercise the real enter/exit and garage selection handlers with audio/UI stubs.
const game = await harness();
Object.assign(game, { syncControlUI() {}, AUDIO: { playSFX() {} }, showBanner() {}, refreshGarageLabels() {} });
const slice = (from, to) => html.slice(html.indexOf(from), html.indexOf(to, html.indexOf(from)));
const select = { getAttribute: key => key === 'data-car' ? 'MUSCLE' : null,
    addEventListener(_, fn) { this.click = fn; } };
game.document = { querySelectorAll: () => [select] };
assert.match(html, /<button data-car="MUSCLE"/);
vm.runInContext(slice("document.querySelectorAll('.car-archetype-btn').forEach(btn", '\n            });') + '\n            });', game, {timeout:1000});
vm.runInContext(slice('function toggleEnterExitCar()', '        let refreshGarageLabels'), game);
game.STATE.nearestVehicle = game.WORLD.vehicles[0];
game.toggleEnterExitCar();
assert.equal(game.STATE.currentVehicle.name, 'Ferrari GT');
game.toggleEnterExitCar();
select.click();
game.STATE.nearestVehicle = null;
game.toggleEnterExitCar();
assert.equal(game.STATE.currentVehicle.archetype, 'MUSCLE');
console.log('PASS: Ferrari GT enter/exit and garage Muscle summon');

// Real Cannon contact after thaw: a box launched into a stationary traffic chassis must collide.
const c = await harness(), target = c.ordinary()[0];
for (const v of c.WORLD.vehicles) if (v !== target && v.vehicle.world) v.vehicle.removeFromWorld(c.physicsWorld);
target.chassisBody.position.set(0, 0.8, 0); target.chassisBody.quaternion.set(0, 0, 0, 1); c.resetTrafficBody(target);
c.movePlayer(250, 0); c.updateTrafficPhysics(); c.movePlayer(10, 0); c.updateTrafficPhysics();
const striker = new CANNON.Body({ mass: 1200, shape: new CANNON.Box(new CANNON.Vec3(1, .4, 2)), position: new CANNON.Vec3(0, .8, -7) });
striker.velocity.set(0, 0, 20); c.physicsWorld.addBody(striker);
let contacts = 0;
striker.addEventListener('collide', event => { if (event.body === target.chassisBody) contacts++; });
for (let i = 0; i < 90; i++) c.physicsWorld.step(1 / 60);
assert.ok(contacts > 0, 'reactivated chassis must not be a ghost');
for (const n of Object.values(target.chassisBody.position)) assert.ok(Number.isFinite(n));
assert.ok(target.chassisBody.velocity.length() < 50, 'no explosive stale-impulse launch');
console.log('PASS: reactivated traffic chassis generates real Cannon contacts with finite bounded motion');
const animation = html.slice(html.indexOf('function animate('));
assert.ok(animation.indexOf('updateTrafficPhysics();') < animation.indexOf('physicsWorld.step('));
console.log('RESULT: PASS (headless source/components; full-city browser, offline and device checks remain separate)');
