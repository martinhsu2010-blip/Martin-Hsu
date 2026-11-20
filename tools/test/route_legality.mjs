// Run before editing routes. --all prints every failing sample; default prints the first per route.
import assert from 'node:assert/strict';
import { harness, html, THREE } from './traffic_harness.mjs';

const h = await harness(html, 'DESKTOP_ULTRA');
const cars=h.ordinary();
assert.equal(new Set(cars.map(c=>c.kenneyType)).size,h.KENNEY_TYPES.length);
let width=0, length=0;
for (const car of cars) {
    const bounds=new THREE.Box3().setFromObject(car.carModel);
    const size=bounds.getSize(new THREE.Vector3());
    const he=car.chassisBody.shapes[0].halfExtents;
    width=Math.max(width,he.x,size.x/2); length=Math.max(length,he.z,size.z/2);
}
console.log('Kenney half footprint',width,length);
assert.ok(width + 1 <= 2.01 && length + 1 <= 4.02);
const surface=h.trafficSurfaceIndex(h.ROAD_NET);
let total=0;
for (const [rid,route] of h.ROAD_NET.routes.entries()) {
    const kind=rid===5 || rid===6 ? 'ring' : rid>=9 ? 'suburb' : 'city';
    let count=0, height=0;
    for (const [i,p] of route.entries()) {
        const y=p.y ?? h.terrainHeight(p.x,p.z);
        const legal=h.trafficSampleLegal(surface,kind,p,width+1,length+1,y);
        if (legal && p.trafficLegal) continue;
        if (surface(kind,p.x,p.z,y,Infinity) && !surface(kind,p.x,p.z,y,0.25)) height++;
        if (!count || process.argv.includes('--all')) console.log('R'+rid,i,'xyz',p.x.toFixed(2),y.toFixed(2),p.z.toFixed(2));
        count++;
    }
    console.log('R'+rid,route.length,'samples;',count,'violations;',height,'center height mismatches');
    total+=count;
}
console.log('Total violations',total);
process.exitCode=Number(total!==0);
