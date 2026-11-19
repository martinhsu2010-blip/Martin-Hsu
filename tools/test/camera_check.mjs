// Camera-only regression checks using the actual update function and vendored Three.js.
// No browser, renderer, physics simulation or device-performance claims.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import { execFileSync } from 'node:child_process';
const root = new URL('../../', import.meta.url);
const threeSource = fs.readFileSync(new URL('libs/three/build/three.module.js', root), 'utf8');
const THREE = await import('data:text/javascript;base64,' + Buffer.from(threeSource).toString('base64'));
const html = fs.readFileSync(new URL('index.html', root), 'utf8');
function harness(source) {
    const configStart = source.indexOf('        const CAMERA_CONFIG =');
    const config = configStart < 0 ? '' : source.slice(configStart, source.indexOf('        const camera =', configStart));
    const start = source.indexOf('        function getActivePosition()');
    const end = source.indexOf('        // ==================== 賺錢玩法', start);
    const car = {
        chassisGroup: new THREE.Group(), getForwardHeading: () => car.heading,
        getSpeedMPS: () => car.speed, heading: 0, speed: 0,
        flameGroup: { visible: false }, currentGear: 1, rpm: 850, nitro: 100
    };
    car.chassisGroup.position.set(0, 1, 0);
    const element = { style: {}, textContent: '' };
    const context = vm.createContext({
        THREE, Math, console, tr:key=>key, localStorage: { getItem: () => null, setItem() {} },
        document: { getElementById: () => element },
        STATE: { mode: 'FOOT', cameraMode: 0, time: 0, currentVehicle: null },
        PLAYER: { group: new THREE.Group(), body: { velocity: { x: 0, z: 0 } }, heading: 0 },
        WORLD: { vehicles: [], cameraBlockers: [] },
        ROAD_NET: { hill: {}, suburb: {}, ring: {}, spurs: [], roundabouts: [{ x: 1000, z: 1000 }] },
        nearestOnPolyline: () => ({ d: Infinity }),
        camera: new THREE.PerspectiveCamera(config ? 60 : 62, 16/9, 0.5, 2600),
        gradePass: null, shadowCamSize: 100, sunVector: new THREE.Vector3(1, 1, 0),
        sunLight: { shadow: { mapSize: { x: 1024 } }, target: new THREE.Object3D(), position: new THREE.Vector3() }
    });
    vm.runInContext(config + source.slice(start, end) + '\nthis.CAM = CAM; this.CONFIG = typeof CAMERA_CONFIG === "undefined" ? null : CAMERA_CONFIG;', context);
    context.PLAYER.group.position.set(0, 1, 0);
    context.car = car;
    context.step = (n = 1, dt = 1/60) => {
        for (let i = 0; i < n; i++) { context.STATE.time += dt; context.updateCameraAndLights(dt); }
    };
    context.drive = (mode = 0) => {
        context.STATE.mode = 'CAR'; context.STATE.currentVehicle = car; context.STATE.cameraMode = mode;
    };
    return context;
}
function close(actual, expected, epsilon = 0.001) {
    assert.ok(Math.abs(actual - expected) <= epsilon, `${actual} != ${expected} (+/- ${epsilon})`);
}
function summary(h) {
    h.step(300);
    const foot = { distance: h.camera.position.distanceTo(h.CAM.target), pitch: THREE.MathUtils.radToDeg(h.CAM.pitch) };
    h.drive(); h.step(300);
    const near = { distance: h.camera.position.distanceTo(h.CAM.target), pitch: THREE.MathUtils.radToDeg(h.CAM.pitch), fov: h.camera.fov };
    h.STATE.cameraMode = 1; h.step(300);
    const far = { distance: h.camera.position.distanceTo(h.CAM.target), pitch: THREE.MathUtils.radToDeg(h.CAM.pitch) };
    h.car.speed = 100; h.step(300); const speedFov = h.camera.fov;
    h.car.flameGroup.visible = true; h.step(300);
    return { foot, near, far, speedFov, nitroFov: h.camera.fov };
}
const after = summary(harness(html));
close(after.foot.distance, 4.2); close(after.foot.pitch, 12);
close(after.near.distance, 7.2); close(after.near.pitch, 10);
close(after.far.distance, 10.5); close(after.far.pitch, 14);
close(after.near.fov, 60, 0.051); close(after.speedFov, 68, 0.051); close(after.nitroFov, 72, 0.051);
console.log('PASS: foot/near/far defaults and 60/68/72 FOV limits');

const h = harness(html); h.drive(); h.step(300);
h.CAM.yaw = 1; h.CAM.pitch = 0.5; h.CAM.lastInput = h.STATE.time;
h.step(39, 0.05); close(h.CAM.yaw, 1); close(h.CAM.pitch, 0.5);
h.step(2, 0.05); assert.ok(h.CAM.yaw < 1 && h.CAM.yaw > 0.7);
h.CAM.pointers.set(1, {}); const held = h.CAM.yaw; h.step(120); close(h.CAM.yaw, held);
h.CAM.pointers.clear(); h.step(300); close(h.CAM.yaw, 0);
h.CAM.zoom = 0.55; h.step(300); close(h.camera.position.distanceTo(h.CAM.target), 7.2 * 0.55);
h.CAM.zoom = 2.2; h.step(300); close(h.camera.position.distanceTo(h.CAM.target), 7.2 * 2.2);
h.STATE.mode = 'FOOT'; h.step(300); close(h.CAM.pitch, THREE.MathUtils.degToRad(12));
h.CAM.pitch = 0.4; h.CAM.yaw = 0.8; h.step(300); close(h.CAM.pitch, 0.4); close(h.CAM.yaw, 0.8);
console.log('PASS: recenter delay, held gestures, manual foot orbit, zoom, enter/exit presets');

function blockerAt(h, distance) {
    const target = h.CAM.target;
    const direction = new THREE.Vector3(0, Math.sin(h.CAM.pitch), -Math.cos(h.CAM.pitch));
    const wall = new THREE.Mesh(new THREE.PlaneGeometry(100, 100), new THREE.MeshBasicMaterial({ side: THREE.DoubleSide }));
    wall.position.copy(target).addScaledVector(direction, distance);
    wall.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), direction);
    wall.updateMatrixWorld(true); h.WORLD.cameraBlockers = [wall];
    return wall;
}
const collision = harness(html); collision.drive(); collision.step(300);
const wall = blockerAt(collision, 3); collision.step();
close(collision.CAM.distance, 2.4); close(collision.camera.position.distanceTo(collision.CAM.target), 2.4);
collision.step(120); close(collision.CAM.distance, 2.4);
collision.WORLD.cameraBlockers = []; collision.step();
assert.ok(collision.CAM.distance > 2.4 && collision.CAM.distance < 3);
let previous = collision.CAM.distance;
for (let i = 0; i < 180; i++) { collision.step(); assert.ok(collision.CAM.distance >= previous); previous = collision.CAM.distance; }
close(collision.CAM.distance, 7.2, 0.001);
blockerAt(collision, 0.8); collision.step(); close(collision.CAM.distance, 0.2);
// Sharp orbit turns must resolve collisions on the actual final camera segment.
collision.CAM.yaw = Math.PI/2; collision.CAM.lastInput = collision.STATE.time;
collision.step(); assert.ok(Number.isFinite(collision.camera.position.length()));
console.log('PASS: immediate pull-in, steady wall contact, monotonic recovery and close blockers');

for (const dt of [1/30, 1/60, 1/120]) {
    const c = harness(html); c.drive(); c.step(300);
    blockerAt(c, 3); c.step(); c.WORLD.cameraBlockers = [];
    c.step(Math.round(1/dt), dt);
    close(c.CAM.distance, 7.2 - 4.8 * Math.exp(-4), 0.000001);
}
console.log('PASS: identical one-second collision recovery at 30/60/120 Hz');

// Tilted blockers represent the existing terrain/ramps/decks, using real mesh raycasts.
for (const pitch of [-0.1, 0.2, 0.7]) {
    const c = harness(html); c.drive(); c.step(300);
    c.CAM.pitch = pitch; c.CAM.lastInput = c.STATE.time;
    blockerAt(c, 2); c.step();
    assert.ok(c.camera.position.distanceTo(c.CAM.target) <= 1.401);
}
console.log('PASS: sloped/deck obstruction rays with manual pitch');

// Keep the car in view when a close wall pulls the camera ahead of the lagging anchor.
const moving = harness(html); moving.drive(); moving.step(300);
moving.car.chassisGroup.position.z += 8;
const closeWall = new THREE.Mesh(new THREE.PlaneGeometry(100, 100), new THREE.MeshBasicMaterial({ side: THREE.DoubleSide }));
closeWall.position.set(0, 2.1, 7); closeWall.updateMatrixWorld(true);
moving.WORLD.cameraBlockers = [closeWall]; moving.step();
const viewDirection = new THREE.Vector3(); moving.camera.getWorldDirection(viewDirection);
const subjectDirection = new THREE.Vector3().subVectors(moving.CAM.target, moving.camera.position).normalize();
close(viewDirection.dot(subjectDirection), 1);

const transition = harness(html); transition.drive(3); transition.step(300);
const birdPosition = transition.camera.position.clone(); transition.STATE.cameraMode = 0; transition.step();
assert.ok(transition.camera.position.distanceTo(birdPosition) < 8);
transition.step(300); close(transition.camera.position.distanceTo(transition.CAM.target), 7.2);
transition.car.chassisGroup.position.set(1000, 20, 1000); transition.step();
assert.ok(transition.camera.position.distanceTo(transition.CAM.target) < 8);
console.log('PASS: close-wall subject visibility, bird-to-chase easing and teleport anchor reset');

const baselineRef = process.argv[2];
if (baselineRef) {
    const beforeHtml = execFileSync('git', ['show', `${baselineRef}:index.html`], { cwd: root, maxBuffer: 2e6 }).toString();
    console.log('BEFORE/AFTER:', JSON.stringify({ before: summary(harness(beforeHtml)), after }));
    for (const mode of [2, 3]) {
        const before = harness(beforeHtml), current = harness(html);
        before.drive(mode); current.drive(mode);
        // Identical starting optics/anchor to compare the preserved fixed-camera path.
        before.step(300); current.step(300);
        for (let i = 0; i < 90; i++) {
            for (const c of [before, current]) {
                c.car.heading = Math.sin(i/10); c.car.speed = i;
                c.car.chassisGroup.position.set(i/4, 1 + Math.sin(i/20), i/8);
                c.car.flameGroup.visible = i > 60; c.step();
            }
            close(current.camera.position.distanceTo(before.camera.position), 0, 1e-9);
            close(current.camera.quaternion.angleTo(before.camera.quaternion), 0, 1e-6);
            close(current.camera.fov, before.camera.fov, 0.051);
        }
    }
    console.log('PASS: hood/bird position, orientation and FOV match baseline while moving/turning/nitro');
}
console.log('RESULT: PASS (Node camera regression checks; not browser/device testing)');
