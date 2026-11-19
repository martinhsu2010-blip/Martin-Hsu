// Headless geometry audit. Draw submissions are a structural upper bound, not renderer/device timing.
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { collisionHarness, html, root, THREE } from './collision_harness.mjs';
const base = execFileSync('git',['show','dab2ba607ac77e706e82a947c3ce171ef5c45311:index.html'],{cwd:root,encoding:'utf8',maxBuffer:4e6});
const types=['bungalow','detached','duplex','townhouse','walkup','store','workshop'], shares=[30,20,15,12,10,8,5];
// Independent polygon/segment distances, rather than invoking the production SAT predicate.
const cross=(a,b,c)=>(b.x-a.x)*(c.z-a.z)-(b.z-a.z)*(c.x-a.x);
function pointSegment(p,a,b){const dx=b.x-a.x,dz=b.z-a.z,l=dx*dx+dz*dz;const t=l?Math.max(0,Math.min(1,((p.x-a.x)*dx+(p.z-a.z)*dz)/l)):0;return Math.hypot(p.x-a.x-t*dx,p.z-a.z-t*dz);}
function inside(p,poly){return poly.every((a,i)=>cross(a,poly[(i+1)%poly.length],p)>=-1e-7)||poly.every((a,i)=>cross(a,poly[(i+1)%poly.length],p)<=1e-7);}
function pointPoly(p,poly){return inside(p,poly)?0:Math.min(...poly.map((a,i)=>pointSegment(p,a,poly[(i+1)%poly.length])));}
function segDist(a,b,c,d){if(cross(a,b,c)*cross(a,b,d)<0&&cross(c,d,a)*cross(c,d,b)<0)return 0;return Math.min(pointSegment(a,c,d),pointSegment(b,c,d),pointSegment(c,a,b),pointSegment(d,a,b));}
function polyDist(a,b){if(inside(a[0],b)||inside(b[0],a))return 0;return Math.min(...a.flatMap((p,i)=>b.map((q,j)=>segDist(p,a[(i+1)%a.length],q,b[(j+1)%b.length]))));}
function corners(h){return [[-1,-1],[1,-1],[1,1],[-1,1]].map(([x,z])=>({x:h.x+h.c*h.hx*x+h.s*h.hz*z,z:h.z-h.s*h.hx*x+h.c*h.hz*z}));}
function bodyCorners(body,index){const p=body.pointToWorldFrame(body.shapeOffsets[index]),q=body.quaternion.mult(body.shapeOrientations[index]),e=body.shapes[index].halfExtents;return [[-1,-1],[1,-1],[1,1],[-1,1]].map(([x,z])=>{const v=q.vmult({x:x*e.x,y:0,z:z*e.z});return {x:p.x+v.x,z:p.z+v.z};});}
const report=[];
for(const preset of ['PHONE_LOW','DESKTOP_HIGH']){
    const h=await collisionHarness(html,preset),old=await collisionHarness(base,preset),houses=h.WORLD.suburbHouses,polys=houses.map(corners);
    const cap=preset==='PHONE_LOW'?210:390;
    assert.equal(houses.length,cap);assert.ok(houses.length/old.WORLD.suburbHouses.length>=1.4);
    const counts=types.map(t=>houses.filter(h=>h.type===t).length);
    counts.forEach((n,i)=>assert.ok(Math.abs(n-cap*shares[i]/100)<1,`${types[i]} integer quota`));
    assert.ok(counts.slice(0,5).reduce((a,b)=>a+b,0)/cap>=.75);
    assert.equal(JSON.stringify(h.city),JSON.stringify(old.city),'city placements unchanged');
    assert.equal(JSON.stringify(h.TREES.list.map(({x,y,z,rot,scale,type})=>({x,y,z,rot,scale,type}))),JSON.stringify(old.TREES.list.map(({x,y,z,rot,scale,type})=>({x,y,z,rot,scale,type}))),'all trees unchanged');
    let minGap=Infinity,minTrunkGap=Infinity,minRoadGap=Infinity,minProtectedGap=Infinity,maxTerrainRange=0;
    const points=[...h.arrivals,...h.depots,...h.WORLD.vehicles.slice(0,4).map(v=>v.chassisBody.position)];
    for(let i=0;i<houses.length;i++){
        const house=houses[i],poly=polys[i];
        for(let j=0;j<i;j++)minGap=Math.min(minGap,polyDist(poly,polys[j]));
        for(const e of h.TREE_COLLIDERS.entries)minTrunkGap=Math.min(minTrunkGap,polyDist(poly,bodyCorners(e.body,0)));
        for(const p of points)minProtectedGap=Math.min(minProtectedGap,pointPoly(p,poly));
        for(const road of h.ROAD_NET.terrainRoads){
            for(let n=1;n<road.pts.length;n++){
                const a=road.pts[n-1],b=road.pts[n];
                if(Math.min(a.x,b.x)>house.x+30||Math.max(a.x,b.x)<house.x-30||Math.min(a.z,b.z)>house.z+30||Math.max(a.z,b.z)<house.z-30)continue;
                const gap=Math.min(...poly.map((p,j)=>segDist(p,poly[(j+1)%4],a,b)))-road.half;
                minRoadGap=Math.min(minRoadGap,gap);
            }
        }
        for(const ramp of h.ramps){
            const heading=ramp.rotY+Math.PI,c=Math.cos(heading),s=Math.sin(heading);
            const corridor=[[-8,-ramp.len-6],[8,-ramp.len-6],[8,55],[-8,55]].map(([x,z])=>({x:ramp.x+c*x+s*z,z:ramp.z-s*x+c*z}));
            assert.ok(polyDist(poly,corridor)>=3,'ramp takeoff/landing clearance');
        }
        const ys=poly.map(p=>h.terrainHeight(p.x,p.z));
        maxTerrainRange=Math.max(maxTerrainRange,Math.max(...ys)-Math.min(...ys));
        assert.ok(Math.max(...ys)-Math.min(...ys)<=3.5);
        assert.ok(h.nearestTerrainRoadDist(house.x,house.z)>=8.5);
        assert.ok(!h.rectHitsElevated(house.x,house.z,2*(Math.abs(house.c)*house.hx+Math.abs(house.s)*house.hz),2*(Math.abs(house.s)*house.hx+Math.abs(house.c)*house.hz),4));
        if(house.ti>=5)assert.ok(house.zone<2&&house.terrainRange<=1.5,'commercial on flat main roads');
        if(house.ti===4)assert.ok(house.terrainRange<=1.5,'flat walk-up parcel');
        if(house.ti===0)assert.ok(house.zone>=2,'bungalows on minor loops');
        assert.ok(Number.isFinite(house.x)&&Number.isFinite(house.z),'world-map compatible');
    }
    assert.ok(minGap>=3-1e-6,`structure gap ${minGap}`);assert.ok(minTrunkGap>0,`trunk gap ${minTrunkGap}`);
    assert.ok(minRoadGap>=3-1e-6,`road gap ${minRoadGap}`);assert.ok(minProtectedGap>=3,`protected gap ${minProtectedGap}`);
    const meshes=h.WORLD.suburbMeshes;
    assert.ok(meshes.every(m=>m.isInstancedMesh&&!Array.isArray(m.material)));
    const opaque=new Set(meshes.filter(m=>m.geometry.attributes.color||m===houses[0].baseMesh).map(m=>m.material));
    const roofs=new Set(meshes.filter(m=>!m.geometry.attributes.color&&m!==houses[0].baseMesh).map(m=>m.material));
    assert.ok(opaque.size<=6&&roofs.size<=2);
    // Each single-material InstancedMesh issues <=1 opaque draw (geometry groups ignored).
    const addedOpaqueDraws=meshes.length-3;
    assert.ok(addedOpaqueDraws<= (preset==='PHONE_LOW'?20:30));
    const baselineZones=[0,0,0,0];for(const house of old.WORLD.suburbHouses){const distances=old.ROAD_NET.suburbRoads.map(r=>old.nearestOnPolyline(house.x,house.z,r.pts).d);baselineZones[distances.indexOf(Math.min(...distances))]++;}
    report.push({preset,...h.WORLD.suburbStats,ratio:houses.length/old.WORLD.suburbHouses.length,baselineZones,
        minGap,minTrunkGap,minRoadGap,minProtectedGap,maxTerrainRange,houseBodies:h.houseBodies.length,maxShapes:Math.max(...h.houseBodies.map(b=>b.shapes.length)),
        opaqueMaterials:opaque.size,roofMaterials:roofs.size,opaqueDrawUpperBound:meshes.length,baselineOpaqueDraws:3,addedOpaqueDraws,
        addedWithOneShadowPass:addedOpaqueDraws*2});
}
console.log('REPORT '+JSON.stringify(report));
console.log('RESULT: PASS (headless placements/geometry; draw-call structural upper bound, not a WebGL measurement)');
