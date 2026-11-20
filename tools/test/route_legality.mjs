// Run before editing routes. --all prints every failing sample; default prints the first per route.
import assert from 'node:assert/strict';
import { harness, html, THREE } from './traffic_harness.mjs';

function trafficSurfaceIndex(net) {
    // Index the two triangles of each rendered road-strip segment in 32-unit cells.
    const cells = new Map();
    const cell = (x, z) => (Math.floor(x / 32) + 128) * 256 + Math.floor(z / 32) + 128;
    function triangle(kind, a, b, c) {
        const den = (b.z-c.z)*(a.x-c.x) + (c.x-b.x)*(a.z-c.z);
        if (!den) return;
        const t = {kind, a, b, c, den};
        for (let x = Math.floor(Math.min(a.x,b.x,c.x)/32); x <= Math.floor(Math.max(a.x,b.x,c.x)/32); x++)
            for (let z = Math.floor(Math.min(a.z,b.z,c.z)/32); z <= Math.floor(Math.max(a.z,b.z,c.z)/32); z++) {
                const key = cell(x*32,z*32);
                if (!cells.has(key)) cells.set(key, []);
                cells.get(key).push(t);
            }
    }
    function strip(road, kind, left = -road.half, right = road.half) {
        const edge = (p, side) => ({x:p.x - p.tz*side, z:p.z + p.tx*side, y:p.y || 0});
        const pts = road.pts;
        for (let i=0; i < pts.length - (road.closed ? 0 : 1); i++) {
            const p=pts[i], q=pts[(i+1)%pts.length];
            const a=edge(p,left), b=edge(p,right), c=edge(q,left), d=edge(q,right);
            triangle(kind,a,b,c); triangle(kind,b,d,c);
        }
    }
    for (const road of net.ribbons) strip(road,'city');
    strip(net.ring,'ring', -net.ring.half + 0.5, -0.3);
    strip(net.ring,'ring', 0.3, net.ring.half - 0.5);
    for (const road of net.suburbRoads) strip(road,'suburb');
    return function supported(kind,x,z,y,tolerance) {
        if (kind === 'city') {
            // The approach ramps physically occupy the surface of the -120 avenue.
            const az = Math.abs(z);
            if (Math.abs(x + 120) <= 9 && az >= 90 && az <= 142) {
                const t = (142 - az) / 52;
                return Math.abs(y - 7*t*t*(3-2*t)) <= tolerance;
            }
            const rb=net.roundabouts[0], r=Math.hypot(x-rb.x,z-rb.z);
            if (r < rb.rIn) return false;
            if (Math.abs(y) <= tolerance) {
                if (r <= rb.rOut) return true;
                if (z >= -net.avenueZ && net.avenuesX.some(v => Math.abs(v-x)<=net.avenueHalf && z <= (v < -340 ? net.hillAveZ : net.avenueZ))) return true;
                if (x<=225 && net.crossZ.some(v => Math.abs(v-z)<=net.crossHalf && x >= (v>=360 ? -340 : -620))) return true;
            }
        }
        const candidates=cells.get(cell(x,z));
        if (!candidates) return false;
        for (const t of candidates) {
            if (t.kind !== kind) continue;
            const {a,b,c,den}=t;
            const u=((b.z-c.z)*(x-c.x)+(c.x-b.x)*(z-c.z))/den;
            const v=((c.z-a.z)*(x-c.x)+(a.x-c.x)*(z-c.z))/den;
            if (u >= -1e-7 && v >= -1e-7 && u+v <= 1.0000001 &&
                Math.abs(y-(u*a.y+v*b.y+(1-u-v)*c.y))<=tolerance) return true;
        }
        return false;
    };
}
function trafficSampleLegal(surface,kind,p,width,length,y) {
    if (!surface(kind,p.x,p.z,y,0.25)) return false;
    for (const side of [-width,0,width]) {
        for (const end of [-length,-length/2,0,length/2,length]) {
            if (!surface(kind,p.x+p.tz*side+p.tx*end,p.z-p.tx*side+p.tz*end,y,0.65)) return false;
        }
    }
    return true;
}

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
const surface=trafficSurfaceIndex(h.ROAD_NET);
let total=0;
for (const [rid,route] of h.ROAD_NET.routes.entries()) {
    const kind=rid===5 || rid===6 ? 'ring' : rid===9 ? 'suburb' : 'city';
    let count=0, height=0;
    for (const [i,p] of route.entries()) {
        const y=p.y ?? h.terrainHeight(p.x,p.z);
        if (trafficSampleLegal(surface,kind,p,width+1,length+1,y)) continue;
        if (surface(kind,p.x,p.z,y,Infinity) && !surface(kind,p.x,p.z,y,0.25)) height++;
        if (!count || process.argv.includes('--all')) console.log('R'+rid,i,'xyz',p.x.toFixed(2),y.toFixed(2),p.z.toFixed(2));
        count++;
    }
    console.log('R'+rid,route.length,'samples;',count,'violations;',height,'center height mismatches');
    total+=count;
}
console.log('Total violations',total);
process.exitCode=Number(total!==0);
