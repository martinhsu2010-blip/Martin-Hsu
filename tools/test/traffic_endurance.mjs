// Cars-only component simulation, observer visits spawn, coast, elevated ring and suburb, no player inputs.
// Real controllers, Cannon, activation and recycle gates. No renderer or device FPS.
import assert from 'node:assert/strict';
import vm from 'node:vm';
import { harness, html, presets } from './traffic_harness.mjs';

for (const preset of process.argv.slice(2).length ? process.argv.slice(2) : Object.keys(presets(html))) {
    const h = await harness(html, preset);
    // Execute the game's own terrain triangulation and ring collision builder.
    // Rendering, spur ramps, props, traffic lights and parked vehicles are excluded.
    const part = (from, to) => {
        const a = html.indexOf(from), b = html.indexOf(to, a);
        assert.ok(a >= 0 && b > a);
        return html.slice(a, b);
    };
    vm.runInContext(part('const makeTerrain = (rg, es)', '                const geo = new THREE.BufferGeometry();') +
        part('const body = new CANNON.Body({ mass: 0, material: MAT_GROUND });\n                body.addShape(new CANNON.Trimesh', '                return mesh;') +
        '}; makeTerrain(ROAD_NET.terrainRegions[1], ' + (preset.startsWith('DESKTOP') ? 8 : 10) + ');' +
        '{' + part('const bodies = [];\n            let cur = null, curCount = 0;', '            segColliders(rp,') +
        'segColliders(ROAD_NET.ring.pts, ROAD_NET.ring.half, true, true, true, null, null); bodies.forEach(b=>physicsWorld.addBody(b));}', h);
    h.STATE.mode='SPECTATOR';
    for (const v of h.WORLD.vehicles.filter(v=>!v.isAI)) {
        v.setVisibility(false);
        if (v.vehicle.world) v.vehicle.removeFromWorld(h.physicsWorld);
    }
    const views = [[98,22,0], [230,480,0], [110,-380,Math.PI], [-1200,-247,Math.PI/2]];
    let peak=0, peakSpeed=0;
    for (let i=0; i<36000; i++) {
        if (i % 9000 === 0) {
            const [x,z,yaw] = views[i / 9000];
            h.movePlayer(x,z,yaw,h.terrainHeight(x,z)+1);
        }
        h.tick();
        if ((i+1)%60 === 0) {
            peak=Math.max(peak,h.trafficDiagnostics().offRoute);
            for (const car of h.ordinary()) peakSpeed=Math.max(peakSpeed, car.getSpeedMPS());
        }
    }
    const off=h.ordinary().filter(v=>h.nearestOnPolyline(v.chassisBody.position.x,v.chassisBody.position.z,
        [...h.ROAD_NET.routes[v.routeId],h.ROAD_NET.routes[v.routeId][0]]).d>8);
    const diagnostics=h.trafficDiagnostics();
    console.log(preset,JSON.stringify({seconds:h.STATE.time,peak,peakSpeed,offRoute:diagnostics.offRoute,
        outside:off.map(v=>({route:v.routeId,x:v.chassisBody.position.x,z:v.chassisBody.position.z}))}));
    assert.ok(peakSpeed > 3); assert.equal(off.length,0); assert.equal(diagnostics.offRoute,0);
}
