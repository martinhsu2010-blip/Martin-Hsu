// node tools/test/route_legality.mjs [--base <main SHA>] [--all]
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { harness, html, root, THREE } from './traffic_harness.mjs';

const candidate = await harness(html, 'DESKTOP_ULTRA');
const baseArg = process.argv.indexOf('--base');
const source = baseArg < 0 ? html : execFileSync('git', ['show', process.argv[baseArg + 1] + ':index.html'],
    { cwd: root, encoding: 'utf8', maxBuffer: 4 * 1024 * 1024 });
const h = baseArg < 0 ? candidate : await harness(source, 'DESKTOP_ULTRA');
const cars = h.ordinary();
assert.equal(new Set(cars.map(c => c.kenneyType)).size, h.KENNEY_TYPES.length);

let width = 0, length = 0;
for (const car of cars) {
    const bounds = new THREE.Box3().setFromObject(car.carModel);
    const he = car.chassisBody.shapes[0].halfExtents;
    width = Math.max(width, he.x, -bounds.min.x, bounds.max.x);
    length = Math.max(length, he.z, -bounds.min.z, bounds.max.z);
}
console.log('Largest Kenney origin-relative half extents', width, length);
assert.ok(width + 1 <= 2.01 && length + 1 <= 4.07, 'asset outgrew cached clearance envelope');
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
    let count = 0, heights = 0;
    for (const [i, p] of route.entries()) {
        const ground = h.terrainHeight(p.x, p.z), y = p.y ?? ground;
        const wrongHeight = (kind === 'suburb' && Math.abs(y - ground) > 0.25) ||
            (surface(kind, p.x, p.z, y, Infinity) && !surface(kind, p.x, p.z, y, 0.25));
        const legal = !wrongHeight && candidate.trafficSampleLegal(surface, kind, p, width + 1, length + 1, y);
        if (legal && (baseArg >= 0 || p.trafficLegal)) continue;
        if (wrongHeight) heights++;
        if (!count || process.argv.includes('--all')) {
            console.log('R' + rid, i, 'xyz', p.x.toFixed(2), y.toFixed(2), p.z.toFixed(2), wrongHeight ? 'height' : 'footprint');
        }
        count++;
    }
    console.log('R' + rid, route.length, 'samples;', count, 'violations;', heights, 'center height mismatches');
    total += count;
    samples += route.length;
}
console.log('Total violations', total, 'of', samples, 'samples');
process.exitCode = Number(total !== 0);
