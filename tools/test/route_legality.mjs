// node tools/test/route_legality.mjs [--base <commit>] [--all] [--drive-r1]
import assert from 'node:assert/strict';
import vm from 'node:vm';
import { mergeGeometries, section } from './collision_harness.mjs';
import { execFileSync } from 'node:child_process';
import { harness, html, root, THREE } from './traffic_harness.mjs';

const candidate = await harness(html, 'DESKTOP_ULTRA');
const baseArg = process.argv.indexOf('--base');
const source = baseArg < 0 ? html : execFileSync('git', ['show', process.argv[baseArg + 1] + ':index.html'],
    { cwd: root, encoding: 'utf8', maxBuffer: 4 * 1024 * 1024 });
const h = baseArg < 0 ? candidate : await harness(source, 'DESKTOP_ULTRA');
// Run the game's complete ring/spur/pillar builder, including its real Cannon boxes.
h.mergeGeometries = mergeGeometries;
h.createHighwayTexture = () => null;
h.WORLD.roadMaterials = [];
h.WORLD.cameraBlockers = [];
const elevated = section(source, '        function extrudeStrip(', '        function buildRealisticWorld()');
const capture = 'bodies.forEach(b => physicsWorld.addBody(b));';
assert.ok(elevated.includes(capture));
vm.runInContext(elevated.replace(capture, capture + ' return { bodies, pillars: pil };'), h);
const { bodies, pillars } = h.buildElevatedRoads();
const clear = candidate.elevatedTrafficClearance(bodies, pillars);
// Keep the reported regression detectable after R1 no longer travels either stretch.
for (const z of [235.5, 244.5]) {
    for (const x of [-155, -320]) assert.equal(clear({ x, z, tx: -1, tz: 0 }), false);
}
assert.ok(clear({ x: -240, z: 235.5, tx: -1, tz: 0 }), 'open junction under the high deck');
const tallPillar = pillars.find(p => p.top > 8);
assert.ok(tallPillar);
assert.equal(clear({ x: tallPillar.x + 2, z: tallPillar.z, tx: 0, tz: 1 }), false,
    'the car envelope clips a pillar even though its center misses the column');
const cars = h.ordinary();
assert.equal(new Set(cars.map(c => c.kenneyType)).size, h.KENNEY_TYPES.length);

let width = 0, length = 0, height = 0;
for (const car of cars) {
    const bounds = new THREE.Box3().setFromObject(car.carModel);
    height = Math.max(height, bounds.max.y - bounds.min.y);
    const he = car.chassisBody.shapes[0].halfExtents;
    width = Math.max(width, he.x, -bounds.min.x, bounds.max.x);
    length = Math.max(length, he.z, -bounds.min.z, bounds.max.z);
}
console.log('Largest Kenney origin-relative half extents', width, length);
assert.ok(width + 1 <= 2.01 && length + 1 <= 4.07 && height + 1 <= 3.17, 'asset outgrew cached clearance envelope');
const net = h.ROAD_NET;
if (!net.pavedCrossWest) {
    assert.ok(source.includes('const westX = (z >= 360) ? -340 : -620;') && source.includes('const eastX = 225;'));
    net.pavedCrossWest = z => z >= 360 ? -340 : -620;
    net.pavedCrossEast = 225;
}
const surface = candidate.trafficSurfaceIndex(net);
let total = 0, samples = 0;
for (const [rid, route] of net.routes.entries()) {
    const kind = rid === 5 || rid === 6 ? 'ring' : rid >= 9 ? 'suburb' : 'city';
    let count = 0, heights = 0, structures = 0;
    for (const [i, p] of route.entries()) {
        const ground = h.terrainHeight(p.x, p.z), y = p.y ?? ground;
        const wrongHeight = (kind === 'suburb' && Math.abs(y - ground) > 0.25) ||
            (surface(kind, p.x, p.z, y, Infinity) && !surface(kind, p.x, p.z, y, 0.25));
        const blocked = kind === 'city' && !clear(p);
        const legal = !blocked && !wrongHeight && candidate.trafficSampleLegal(surface, kind, p, width + 1, length + 1, y);
        if (legal && (baseArg >= 0 || p.trafficLegal)) continue;
        if (wrongHeight) heights++;
        if (blocked) structures++;
        if (!count || process.argv.includes('--all')) {
            console.log('R' + rid, i, 'xyz', p.x.toFixed(2), y.toFixed(2), p.z.toFixed(2), blocked ? 'elevated structure' : wrongHeight ? 'height' : 'footprint');
        }
        count++;
    }
    console.log('R' + rid, route.length, 'samples;', count, 'violations;', heights, 'center height mismatches;', structures, 'structure overlaps');
    total += count;
    samples += route.length;
}
console.log('Total violations', total, 'of', samples, 'samples');
process.exitCode = Number(total !== 0);

if (process.argv.includes('--drive-r1')) {
    const route = net.routes[1], car = cars[0];
    for (const other of h.WORLD.vehicles) {
        if (other !== car && other.vehicle.world) other.vehicle.removeFromWorld(h.physicsWorld);
    }
    h.WORLD.vehicles.splice(0, h.WORLD.vehicles.length, car);
    h.STATE.mode = 'SPECTATOR';
    // Start on each approach to the detour; repeating along the full loop also
    // covers both of the former ramp crossings when running against --base.
    const starts = [];
    const nearest = h.nearestOnPolyline(-121.8, 235.5, route).i;
    starts.push(nearest, 454);
    for (let i = 0; i < route.length; i += 125) starts.push(i);
    let longestStall = 0;
    for (const idx of new Set(starts)) {
        car.placeOnRoute(1, idx);
        car.trafficRecovery = false;
        let stopped = 0, worst = 0, travel = 0;
        for (let frame = 0; frame < 1800; frame++) {
            const pos = car.chassisBody.position, x = pos.x, z = pos.z;
            if (frame % 30 === 0) h.movePlayer(x, z);
            h.STATE.time += 1 / 60;
            h.updateTrafficPhysics();
            h.physicsWorld.step(1 / 60);
            car.update(1 / 60);
            travel += Math.hypot(pos.x - x, pos.z - z);
            stopped = car.getSpeedMPS() < 0.5 ? stopped + 1 : 0;
            worst = Math.max(stopped, worst);
        }
        longestStall = Math.max(longestStall, worst / 60);
        console.log('R1 drive', idx, 'travel', travel.toFixed(1), 'm; longest stop', (worst / 60).toFixed(2),
            's; end x/z', car.chassisBody.position.x.toFixed(1), car.chassisBody.position.z.toFixed(1));
    }
    assert.ok(longestStall <= 3, 'R1 stopped for more than 3 s in a 30 s drive');
}
