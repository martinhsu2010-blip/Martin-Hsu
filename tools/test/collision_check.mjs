// Node/Cannon component checks; no browser, renderer, offline or device-FPS claim.
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { collisionHarness, html, root, THREE, CANNON } from './collision_harness.mjs';
const base = execFileSync('git', ['show', 'dab2ba607ac77e706e82a947c3ce171ef5c45311:index.html'], { cwd: root, encoding: 'utf8', maxBuffer: 4e6 });
function distance(a, b) { return Math.hypot(a.x - b.x, a.z - b.z); }
function center(body, i = 0) { return body.pointToWorldFrame(body.shapeOffsets[i]); }
function clippedTrunkBounds(tree) {
    const geo = tree.trunkMesh.geometry, a = geo.attributes.position, index = geo.index;
    const count = tree.trunk.vertices || index.count, top = Math.min(6, tree.trunk.height);
    const box = new THREE.Box3();
    for (let i = 0; i < count; i += 3) {
        const tri = [0,1,2].map(k => new THREE.Vector3().fromBufferAttribute(a, index ? index.getX(i + k) : i + k));
        for (let j = 0; j < 3; j++) {
            const p = tri[j], q = tri[(j + 1) % 3];
            if (p.y <= top) box.expandByPoint(p);
            if ((p.y < top) !== (q.y < top)) box.expandByPoint(p.clone().lerp(q, (top - p.y) / (q.y - p.y)));
        }
    }
    return box;
}
const report = { alignment: [], populations: [], impacts: [], activation: {}, limits: 'Headless components; actual source geometry, placements and Cannon, no full city/browser/device claim' };
for (const preset of ['PHONE_LOW', 'DESKTOP_HIGH']) {
    const h = await collisionHarness(html, preset), old = await collisionHarness(base, preset);
    assert.ok(h.WORLD.suburbHouses.length >= old.WORLD.suburbHouses.length * 1.4);
    assert.equal(h.TREES.list.length, old.TREES.list.length);
    assert.equal(h.houseBodies.length, Math.ceil(h.WORLD.suburbHouses.length / 16));
    assert.ok(h.houseBodies.every(b => b.shapes.length <= 16 && b.world === h.physicsWorld));
    const span = bodies => Math.max(...bodies.map(b => { b.updateAABB(); return distance(b.aabb.lowerBound, b.aabb.upperBound); }));
    let houseCenter = 0, houseBoundary = 0, treeCenter = 0, treeBoundary = 0;
    for (let i = 0; i < h.WORLD.suburbHouses.length; i++) {
        const house = h.WORLD.suburbHouses[i];
        const { body, index, walls, instance } = house.collider;
        const m = new THREE.Matrix4(); walls.getMatrixAt(instance, m);
        const bm = new THREE.Matrix4(); house.baseMesh.getMatrixAt(house.baseInstance, bm);
        // Measure actual rendered foundation and shell bounds, independently of parcel dimensions.
        walls.geometry.computeBoundingBox(); house.baseMesh.geometry.computeBoundingBox();
        const top = walls.geometry.boundingBox.max.y;
        const bottom = new THREE.Vector3(0, -.5, 0).applyMatrix4(bm).y;
        const visual = new THREE.Vector3(0, top, 0).applyMatrix4(m), physical = center(body, index);
        visual.y = (visual.y + bottom) / 2;
        houseCenter = Math.max(houseCenter, visual.distanceTo(physical));
        const q = body.quaternion.mult(body.shapeOrientations[index]), half = body.shapes[index].halfExtents;
        for (const x of [-1,1]) for (const z of [-1,1]) {
            const v = new THREE.Vector3(x * .5, 0, z * .5).applyMatrix4(bm); v.y = visual.y;
            const p = q.vmult(new CANNON.Vec3(x * half.x, 0, z * half.z)); p.vadd(physical, p);
            houseBoundary = Math.max(houseBoundary, distance(v, p));
        }
        assert.ok(Math.abs(physical.y - half.y - bottom) < .001, 'foundation bottom fully solid');
    }
    for (let i = 0; i < h.TREES.list.length; i++) {
        const t = h.TREES.list[i], prev = old.TREES.list[i], entry = h.TREE_COLLIDERS.entries[i];
        for (const k of ['rot','scale','type']) assert.equal(t[k], prev[k]);
        for (const k of ['x','y','z']) assert.equal(t[k], prev[k]);
        const bounds = clippedTrunkBounds(t), m = new THREE.Matrix4(); t.trunkMesh.getMatrixAt(t.trunkInstance, m);
        const physical = entry.body.position, visual = bounds.getCenter(new THREE.Vector3()).applyMatrix4(m);
        treeCenter = Math.max(treeCenter, visual.distanceTo(physical));
        const local = entry.body.shapes[0].halfExtents, c = new THREE.Vector3().copy(physical).applyMatrix4(m.clone().invert());
        const error = Math.max(Math.abs(c.x - local.x / t.scale - bounds.min.x), Math.abs(c.x + local.x / t.scale - bounds.max.x),
            Math.abs(c.z - local.z / t.scale - bounds.min.z), Math.abs(c.z + local.z / t.scale - bounds.max.z)) * t.scale;
        treeBoundary = Math.max(treeBoundary, error);
        assert.ok(local.x / t.scale >= .35 - 1e-8 && local.x / t.scale <= .65 + 1e-8);
        assert.ok(local.z / t.scale >= .35 - 1e-8 && local.z / t.scale <= .65 + 1e-8);
    }
    assert.ok(houseCenter <= .35 && treeCenter <= .35 && houseBoundary <= .5 && treeBoundary <= .5);
    report.alignment.push({ preset, houses: h.WORLD.suburbHouses.length, houseBodies: h.houseBodies.length, trees: h.TREES.list.length,
        houseCenter, houseBoundary, treeCenter, treeBoundary,
        roadAdjusted: h.TREES.list.filter(t => t.roadAdjustedFrom).map(t => ({ type:t.type, before:t.roadAdjustedFrom, after:{x:t.x,y:t.y,z:t.z} })),
        maxCompoundHorizontalSpan: { before: span(old.houseBodies), after: span(h.houseBodies) } });
    // Audit actual road surfaces, not onCurvedRoad(), which also marks the entire mountain
    // and the roundabout island as unavailable BUILDING plots rather than drivable lanes.
    function inLane(x, z, y) {
        const r = h.ROAD_NET;
        if (Math.abs(y) < 2 && !r.roundabouts.some(rb => Math.hypot(x-rb.x,z-rb.z) < rb.rIn)) {
            if (r.avenuesX.some(ax => !(ax < -340 && z > r.hillAveZ) && Math.abs(x-ax) < r.avenueHalf && Math.abs(z) < r.avenueZ)) return true;
            if (r.crossZ.some(cz => Math.abs(z-cz) < r.crossHalf && x > (cz >= 360 ? -340 : -620) && x < 225)) return true;
            if (r.ribbons.some(road => h.nearestOnPolyline(x,z,road.pts).d < road.half)) return true;
        }
        for (const road of r.terrainRoads) {
            const hit = h.roadHeightOn(road,x,z);
            if (hit.d < road.half && Math.abs(hit.h-y) < 2) return true;
        }
        return false;
    }
    let minArrivalClearance = Infinity, roadIntrusions = 0;
    const protectedPoints = [...h.arrivals, ...h.depots, ...h.WORLD.vehicles.filter(v => !v.isAI && !v.isPolice).map(v => v.chassisBody.position)];
    for (const e of h.TREE_COLLIDERS.entries) {
        const half = e.body.shapes[0].halfExtents;
        for (const x of [-1,0,1]) for (const z of [-1,0,1]) {
            const point = new THREE.Vector3(x*half.x,0,z*half.z).applyQuaternion(e.body.quaternion).add(e.body.position);
            if (inLane(point.x,point.z,e.tree.y)) roadIntrusions++;
        }
        for (const point of protectedPoints) minArrivalClearance = Math.min(minArrivalClearance,
            distance(e.body.position,point) - Math.hypot(half.x,half.z));
        for (const ramp of h.ramps) {
            const dx=e.body.position.x-ramp.x,dz=e.body.position.z-ramp.z, heading=ramp.rotY+Math.PI;
            const along=dx*Math.sin(heading)+dz*Math.cos(heading), lateral=Math.abs(dx*Math.cos(heading)-dz*Math.sin(heading));
            if (along > -ramp.len-6 && along < 55) assert.ok(lateral > 5+Math.hypot(half.x,half.z), 'trunk in stunt corridor');
        }
    }
    assert.equal(roadIntrusions,0); assert.ok(minArrivalClearance >= 3);
    // Houses keep exact footprints; check all oriented wall corners against real lanes.
    let houseRoadIntrusions = 0;
    for (const house of h.WORLD.suburbHouses) {
        const {body,index}=house.collider, half=body.shapes[index].halfExtents, q=body.shapeOrientations[index], p=center(body,index);
        for(const x of [-1,0,1])for(const z of [-1,0,1]) {
            const v=q.vmult(new CANNON.Vec3(x*half.x,0,z*half.z));v.vadd(p,v);
            if(inLane(v.x,v.z,house.y)) houseRoadIntrusions++;
        }
    }
    assert.equal(houseRoadIntrusions,0);
    report.alignment[report.alignment.length-1].protected = { roadIntrusions, houseRoadIntrusions, minArrivalClearance };
    // Ten evenly sampled generated trunk locations, four headings; solid regardless of graphics quality.
    for (let i = 0; i < 10; i++) {
        const e = h.TREE_COLLIDERS.entries[Math.floor(i * h.TREE_COLLIDERS.entries.length / 10)], p = e.body.position;
        const row = { preset, index: i, x: p.x, z: p.z, counts: [] };
        for (let heading = 0; heading < 4; heading++) {
            h.selectObserver(p.x + 5, p.z + 5, p.y);
            h.camera.rotation.y = heading * Math.PI / 2;
            for (const candidate of h.TREE_COLLIDERS.entries) {
                if (distance(candidate.body.position, h.PLAYER.body.position) <= 140 && !h.treeOccupied(candidate)) assert.ok(candidate.active);
            }
            row.counts.push(h.TREE_COLLIDERS.active.length);
        }
        report.populations.push(row);
    }
}
console.log('PASS: Option B density; unchanged tree placements; rendered foundation/shell alignment; <=16 shapes/body; uncapped near-tree coverage at 10 locations x 4 headings');

const h = await collisionHarness();
// Isolate activation fixtures without changing any production geometry/rules.
for (const car of h.WORLD.vehicles) { car.setVisibility(false); if (car.chassisBody.world) car.vehicle.removeFromWorld(h.physicsWorld); }
const e = h.TREE_COLLIDERS.entries.find(e => e.tree.type === 'broad'); const p = e.body.position;
h.selectObserver(p.x + 1000, p.z); assert.equal(e.active, false);
const updates = h.TREE_COLLIDERS.updates;
h.movePlayer(p.x + 10, p.z, 0, p.y); h.PLAYER.body.aabbNeedsUpdate = true;
for (let i = 0; i < 29; i++) h.refreshTreeColliders(1 / 60);
assert.equal(h.TREE_COLLIDERS.updates, updates); h.refreshTreeColliders(.02); assert.ok(e.active);
h.selectObserver(p.x + 170, p.z); assert.ok(e.active);
h.selectObserver(p.x + 181, p.z); assert.ok(!e.active);
// Exact teleport function, and occupied chassis with deliberately stale AABB.
const vehicle = h.WORLD.vehicles[0]; vehicle.setVisibility(true); vehicle.vehicle.addToWorld(h.physicsWorld);
h.STATE.mode = 'CAR'; h.STATE.currentVehicle = vehicle;
vehicle.chassisBody.position.set(p.x + 1000, p.y, p.z); vehicle.chassisBody.updateAABB();
h.teleportTo(p.x, p.z, 0, p.y + .45); assert.ok(!e.active, 'must defer occupied tree, even after a direct position write');
assert.ok(h.TREE_COLLIDERS.deferred > 0);
h.teleportTo(p.x + 10, p.z, 0, p.y + .45); assert.ok(e.active, 'teleport activates before stepping');
// Active traffic contact keeps the tree registered after the observer leaves.
vehicle.isAI = true; vehicle.chassisBody.position.set(p.x + 1, p.y, p.z); vehicle.chassisBody.aabbNeedsUpdate = true;
h.selectObserver(p.x + 1000, p.z); assert.ok(e.active);
vehicle.vehicle.removeFromWorld(h.physicsWorld); vehicle.frozen = true;
h.refreshTreeColliders(0, true); assert.ok(!e.active, 'frozen traffic must not retain distant tree bodies');
// Debug includes inactive bodies and tracks registration without rebuilding geometry.
h.setPhysicsDebug(true); const geometries = h.PHYS_DEBUG.items.map(it => it.mesh.geometry);
h.updatePhysicsDebug();
const item = h.PHYS_DEBUG.items.find(it => it.body === e.body); assert.ok(item && !item.mesh.visible);
vehicle.setVisibility(false); h.selectObserver(p.x + 10, p.z, p.y); h.updatePhysicsDebug();
assert.ok(item.mesh.visible); assert.ok(item.mesh.position.distanceTo(e.body.position) < 1e-8);
assert.deepEqual(h.PHYS_DEBUG.items.map(it => it.mesh.geometry), geometries);
report.activation = { allocated: h.TREE_COLLIDERS.entries.length, active: h.TREE_COLLIDERS.active.length, deferred: h.TREE_COLLIDERS.deferred };
const allocatedBodies = CANNON.Body.idCounter, allocatedShapes = CANNON.Shape.idCounter;
for (let i=0;i<100;i++) h.refreshTreeColliders(.5);
assert.equal(CANNON.Body.idCounter,allocatedBodies); assert.equal(CANNON.Shape.idCounter,allocatedShapes);
console.log('PASS: 0.5 s cadence, 140/180 hysteresis, immediate teleport, occupied-body deferral, active-AI retention/frozen exclusion, dynamic PHYS_DEBUG registration');

// Use independent real Cannon scenes per impact: production chassis/wheels and exact obstacle
// shape/transform. Actual terrain-height Trimesh patches and supportOnTerrain are used on slopes; unrelated city geometry is absent.
const terrainCache = new Map();
export function impact(h, obstacle, speed, heading, slope = 0, walker = false, omitCollider = false) {
    const world = new CANNON.World({ gravity: new CANNON.Vec3(0, -9.82, 0) });
    world.broadphase = new CANNON.SAPBroadphase(world);
    world.defaultContactMaterial.friction = .4; world.defaultContactMaterial.restitution = .15;
    for (const material of h.physicsWorld.contactmaterials) world.addContactMaterial(material);
    const origin = center(obstacle.body, obstacle.index || 0), q = obstacle.body.quaternion.mult(obstacle.body.shapeOrientations[obstacle.index || 0]);
    const shape = obstacle.body.shapes[obstacle.index || 0];
    const fixed = new CANNON.Body({ mass: 0, material: obstacle.body.material, shape, position: origin.clone(), quaternion: q.clone() }); if (!omitCollider) world.addBody(fixed);
    const direction = new CANNON.Vec3(Math.sin(heading), 0, Math.cos(heading));
    const inv = q.inverse(), local = inv.vmult(direction), half = shape.halfExtents;
    const radius = Math.abs(local.x) * half.x + Math.abs(local.z) * half.z;
    const start = radius + 6, baseY = obstacle.groundY ?? origin.y - half.y;
    const terrain = h.inTerrainRegion(origin.x, origin.z, 5);
    let groundShape, groundPosition;
    if (terrain) {
        if (!terrainCache.has(shape)) {
            const vertices = [], indices = [], n = 32, step = 2;
            for (let iz = 0; iz <= n; iz++) for (let ix = 0; ix <= n; ix++) {
                const x = (ix - n / 2) * step, z = (iz - n / 2) * step;
                vertices.push(x, h.terrainHeight(origin.x + x, origin.z + z), z);
            }
            for (let iz = 0; iz < n; iz++) for (let ix = 0; ix < n; ix++) {
                const a = iz * (n + 1) + ix, b = a + 1, c = a + n + 1, d = c + 1;
                indices.push(a, c, b, b, c, d);
            }
            terrainCache.set(shape, new CANNON.Trimesh(vertices, indices));
        }
        groundShape = terrainCache.get(shape); groundPosition = new CANNON.Vec3(origin.x, 0, origin.z);
    } else {
        groundShape = new CANNON.Box(new CANNON.Vec3(60, .5, 60));
        groundPosition = new CANNON.Vec3(origin.x, baseY - .5, origin.z);
    }
    world.addBody(new CANNON.Body({ mass: 0, material: obstacle.body.material, shape: groundShape, position: groundPosition }));
    const car = h.WORLD.vehicles[0]; let body;
    if (walker) body = h.createCapsuleBody(75, .42, 1.8, 0, 0, 0, true);
    else { body = car.chassisBody; if (car.vehicle.world) car.vehicle.removeFromWorld(car.vehicle.world); }
    const startX = origin.x - direction.x * start, startZ = origin.z - direction.z * start;
    body.position.set(startX, (terrain ? h.terrainHeight(startX, startZ) : baseY) + .8, startZ);
    body.quaternion.setFromAxisAngle(new CANNON.Vec3(0,1,0), heading); body.velocity.setZero(); body.angularVelocity.setZero();
    body.force.setZero(); body.torque.setZero(); body.aabbNeedsUpdate = true; body.wakeUp();
    if (walker) world.addBody(body); else { car.vehicle.addToWorld(world); for (let i = 0; i < 4; i++) { car.vehicle.applyEngineForce(0, i); car.vehicle.setBrake(0, i); } }
    body.velocity.set(direction.x * speed / 3.6, 0, direction.z * speed / 3.6);
    let contacts = 0, passed = false, maxSpeed = body.velocity.length(), previousAlong = -start, coreCrossing = null, firstImpactKmh = null;
    const collide = event => { if (event.body === fixed) { if (!contacts) firstImpactKmh = body.velocity.length() * 3.6; contacts++; } }; body.addEventListener('collide', collide);
    const steps = Math.ceil((2 * start / Math.max(1, speed / 3.6) + 1) * 60);
    for (let i = 0; i < steps; i++) {
        if (walker) { body.velocity.x = direction.x * speed / 3.6; body.velocity.z = direction.z * speed / 3.6; }
        world.step(1 / 60);
        if (!walker) car.supportOnTerrain();
        const delta = body.position.vsub(origin), along = delta.dot(direction);
        // A head-on car reaching the far side without a collision is a tunnel; deflection after
        // a real contact is allowed. Track full passage along the original impact corridor.
        const lateral = Math.abs(delta.x * direction.z - delta.z * direction.x);
        const width = Math.abs(local.z) * half.x + Math.abs(local.x) * half.z;
        if (previousAlong < 0 && along >= 0 && lateral < width && body.position.y > origin.y - half.y && body.position.y < origin.y + half.y) {
            coreCrossing = { along, lateral, y: body.position.y, obstacleY: origin.y };
        }
        if (coreCrossing && along > radius + (walker ? .42 : 2.28)) passed = true;
        previousAlong = along;
        maxSpeed = Math.max(maxSpeed, body.velocity.length());
        assert.ok(Number.isFinite(body.position.y));
    }
    body.removeEventListener('collide', collide);
    if (walker) world.removeBody(body); else car.vehicle.removeFromWorld(world);
    return { contacts, passed, coreCrossing, firstImpactKmh, maxSpeed, finalY: body.position.y, along: body.position.vsub(origin).dot(direction), lateral: Math.abs((body.position.x-origin.x)*direction.z-(body.position.z-origin.z)*direction.x) };
}
const sim = await collisionHarness();
const trunks = [];
for (const type of ['palm','pine','broad']) {
    const matching = sim.TREE_COLLIDERS.entries.filter(e => e.tree.type === type);
    for (let i = 0; i < 4; i++) trunks.push(matching[Math.floor(i * matching.length / 4)]);
}
const houses = sim.WORLD.suburbHouses;
// Two walls per new type, each approached from its downhill side at an actual sloped parcel.
const wallSamples = [];
for (const type of ['bungalow','detached','duplex','townhouse','walkup','store','workshop']) {
    const ranked = houses.filter(h => h.type === type).map(house => {
        const {body,index} = house.collider, half = body.shapes[index].halfExtents;
        let best = null;
        for (let face=0;face<4;face++) {
            const heading = house.rot + face * Math.PI/2;
            const r = face%2 ? half.x : half.z;
            const ground = sim.terrainHeight(house.x-Math.sin(heading)*r, house.z-Math.cos(heading)*r);
            const exposed = house.y-ground;
            if (!best || exposed > best.exposed) best = { house, heading, exposed };
        }
        return best;
    }).sort((a,b) => b.exposed-a.exposed);
    assert.ok(ranked.length>=2 && ranked[1].exposed > .2, `${type}: two downhill foundation fixtures`);
    wallSamples.push(...ranked.slice(0,2));
}
const absent = impact(sim, { body:trunks[0].body, groundY:trunks[0].tree.y }, 60, trunks[0].tree.rot, 0, false, true);
assert.ok(absent.passed && absent.contacts === 0, 'negative control must detect the original pass-through');
for (const speed of [20,60,120,180]) {
    let trunkContacts = 0, wallContacts = 0, tunnels = 0; const impactSpeeds = [];
    for (let i = 0; i < trunks.length; i++) {
        const e = trunks[i], result = impact(sim, { body: e.body, groundY: e.tree.y }, speed, e.tree.rot);
        trunkContacts += result.contacts > 0; tunnels += result.passed; impactSpeeds.push(result.firstImpactKmh);
        assert.ok(result.contacts > 0 && !result.passed, `trunk ${i} @ ${speed}: ${JSON.stringify(result)}`);
    }
    for (let i = 0; i < wallSamples.length; i++) {
        const { house, heading, exposed } = wallSamples[i];
        const result = impact(sim, { ...house.collider, groundY: house.y }, speed, heading);
        wallContacts += result.contacts > 0; tunnels += result.passed; impactSpeeds.push(result.firstImpactKmh);
        assert.ok(result.contacts > 0 && !result.passed, `${house.type} downhill ${exposed} @ ${speed}: ${JSON.stringify(result)}`);
    }
    report.impacts.push({ speedKmh: speed, trunks: trunks.length, trunkContacts, walls: wallSamples.length, wallContacts, downhillFoundations: wallSamples.map(s => ({type:s.house.type, exposed:s.exposed})), tunnels, firstImpactKmh: [Math.min(...impactSpeeds), Math.max(...impactSpeeds)] });
}
for (const e of [trunks[0], trunks[4], trunks[8]]) { const r = impact(sim, { body: e.body, groundY: e.tree.y }, 6, e.tree.rot, 0, true); assert.ok(r.contacts > 0 && !r.passed, JSON.stringify(r)); }
for (const { house, heading } of wallSamples.filter((_,i)=>i%2===0)) { const r = impact(sim, { ...house.collider, groundY: house.y }, 6, heading, 0, true); assert.ok(r.contacts > 0 && !r.passed, JSON.stringify(r)); }
console.log('PASS: real 1/60 Cannon impacts, 12 trunks (all 3 types), 14 downhill foundations (all 7 types) at 20/60/120 km/h; 180 km/h separate; walking capsule contact');
// City additions use the same real-car impact fixture as trees and foundations.
report.cityImpacts=[];
for(const preset of ['PHONE_LOW','DESKTOP_HIGH']) {
    const citySim = preset==='PHONE_LOW' ? sim : await collisionHarness(html,preset);
    citySim.WORLD.buildings=[];citySim.WORLD.roofs=[];citySim.WORLD.cameraBlockers=[];
    citySim.buildTestCityInfill(citySim.city,[new THREE.MeshStandardMaterial(),new THREE.MeshStandardMaterial()],[],[]);
    for(const speed of [20,60,120]){
        let contacts=0;
        for(const b of citySim.WORLD.cityInfill) for(const heading of [0,Math.PI/2]) {
            const result=impact(citySim,{body:b.body,groundY:0},speed,heading);
            assert.ok(result.contacts>0&&!result.passed,JSON.stringify({district:b.district,speed,result}));contacts++;
        }
        report.cityImpacts.push({preset,speed,contacts,buildings:citySim.WORLD.cityInfill.length,tunnels:0});
    }
}
console.log('REPORT ' + JSON.stringify(report));
console.log('RESULT: PASS (headless geometry/physics components, not full-game browser or device testing)');
