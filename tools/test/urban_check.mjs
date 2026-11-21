// Production placement/mesh/Cannon audit. Structural draw counts; no browser/device claim.
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {performance} from 'node:perf_hooks';
import {collisionHarness,html,root,THREE,CANNON} from './collision_harness.mjs';
const base=execFileSync('git',['show','0cc9aff09338ade85fd78826470053d3e5d68208:index.html'],{cwd:root,encoding:'utf8',maxBuffer:4e6});
const gap=(a,b)=>Math.hypot(Math.max(0,Math.abs(a.x-b.x)-(a.w+b.w)/2),Math.max(0,Math.abs(a.z-b.z)-(a.d+b.d)/2));
const report=[];
for(const preset of ['PHONE_LOW','DESKTOP_HIGH']){
 const h=await collisionHarness(html,preset),old=await collisionHarness(base,preset);
 assert.equal(JSON.stringify(h.city),JSON.stringify(old.city),'original city shells unchanged');
 assert.equal(JSON.stringify(h.TREES.list.map(t=>[t.x,t.y,t.z,t.type,t.scale])),JSON.stringify(old.TREES.list.map(t=>[t.x,t.y,t.z,t.type,t.scale])));
 const original=h.city.map(b=>h.addStaticBoxCollider(b.x,b.h/2,b.z,b.w/2+.7,b.h/2,b.d/2+.7));
 h.WORLD.buildings=[];h.WORLD.roofs=[];h.WORLD.cameraBlockers=[];
 const windows=[],night=[];h.buildTestCityInfill(h.city,[new THREE.MeshStandardMaterial(),new THREE.MeshStandardMaterial()],windows,night);
 old.WORLD.buildings=[]; old.WORLD.roofs=[]; old.WORLD.cameraBlockers=[];
 old.buildTestCityInfill(old.city,[new THREE.MeshStandardMaterial(),new THREE.MeshStandardMaterial()],[],[]);
 const added=h.WORLD.cityInfill, bodies=[...new Set(added.map(b=>b.body))];
 const shapeKey=b=>[b.x,b.z,b.w,b.d,b.h,b.district].join('/');
 assert.deepEqual(Array.from(added.filter(b=>!b.coverage),shapeKey),Array.from(old.WORLD.cityInfill,shapeKey));
 const oldCounts=Object.fromEntries(Object.entries(old.WORLD.cityInfillStats).map(([d,s])=>[d,s.after]));
 assert.equal(h.WORLD.buildings.length,added.length);assert.equal(h.WORLD.roofs.length,added.length);
 let minBuilding=Infinity,minRoad=Infinity,minPoint=Infinity,minTree=Infinity,maxAlignment=0;
 for(const [i,b] of added.entries()){
  assert.ok(b.h>={CBD:8,MID:12,OLD:7}[b.district]&&b.h<={CBD:30,MID:32,OLD:20}[b.district]);
  assert.ok(!h.rectHitsElevated(b.x,b.z,b.w,b.d,3)&&!h.rectHitsCurvedRoad(b.x,b.z,b.w,b.d,3.5));
  for(const o of [...h.city.map(o=>({...o,w:o.w+4,d:o.d+4})),...added.slice(0,i)])minBuilding=Math.min(minBuilding,gap({...b,w:b.w+1,d:b.d+1},{...o,w:o.w+1,d:o.d+1}));
  for(const x of h.ROAD_NET.avenuesX)minRoad=Math.min(minRoad,Math.abs(b.x-x)-b.w/2-h.ROAD_NET.avenueHalf);
  for(const z of h.ROAD_NET.crossZ)minRoad=Math.min(minRoad,Math.abs(b.z-z)-b.d/2-h.ROAD_NET.crossHalf);
  for(const p of [...h.arrivals,...h.depots,...h.WORLD.vehicles.filter(v => !v.isAI && !v.isPolice).map(v=>v.chassisBody.position)])minPoint=Math.min(minPoint,gap(b,{...p,w:0,d:0}));
  for(const e of h.TREE_COLLIDERS.entries){const p=e.body.position,a=e.body.aabb;minTree=Math.min(minTree,gap(b,{x:p.x,z:p.z,w:a.upperBound.x-a.lowerBound.x,d:a.upperBound.z-a.lowerBound.z}));}
  for(const r of h.ramps){const theta=r.rotY+Math.PI,dx=b.x-r.x,dz=b.z-r.z,along=dx*Math.sin(theta)+dz*Math.cos(theta),side=Math.abs(dx*Math.cos(theta)-dz*Math.sin(theta));if(along> -r.len-12&&along<61)assert.ok(side>Math.hypot(b.w,b.d)/2+8,'stunt corridor');}
  const matrix=new THREE.Matrix4();b.mesh.getMatrixAt(b.instance,matrix);const box=new THREE.Box3(new THREE.Vector3(-.5,-.5,-.5),new THREE.Vector3(.5,.5,.5)).applyMatrix4(matrix);const j=b.shapeIndex??0, lo=new CANNON.Vec3(),hi=new CANNON.Vec3();
  b.body.shapes[j].calculateWorldAABB(b.body.pointToWorldFrame(b.body.shapeOffsets[j]),b.body.quaternion.mult(b.body.shapeOrientations[j]),lo,hi);
  maxAlignment=Math.max(maxAlignment,box.min.distanceTo(lo),box.max.distanceTo(hi));
  assert.ok(b.body.shapes.length<=16);
  assert.ok(b.body.world===h.physicsWorld&&b.body.mass===0&&h.WORLD.cameraBlockers.includes(b.mesh));
 }
 assert.ok(minBuilding>=2&&minRoad>=3&&minPoint>=3&&minTree>=3,JSON.stringify({minBuilding,minRoad,minPoint,minTree}));assert.ok(maxAlignment<=.35);
 const small=b=>`${Math.floor((b.x+240)/120)}_${Math.floor((b.z+360)/120)}`,big=b=>`${Math.floor((b.x+400)/240)}_${Math.floor((b.z+720)/240)}`;
 for(const key of [small,big]){const keys=new Set(h.city.map(key));assert.ok(added.filter(b=>!b.coverage).every(b=>keys.has(key(b))),'no added facade batch/LOD cell');}
 assert.ok(h.WORLD.cityInfillMeshes.length<=3&&h.WORLD.cityInfillMeshes.every(m=>m.isInstancedMesh&&!Array.isArray(m.material)));
 // Matched headless workloads: same stationary cars, baseline city boxes and pooled trunks.
 h.selectObserver(-60,-180);h.freeze();
 for(const car of h.WORLD.vehicles){car.chassisBody.velocity.setZero();car.chassisBody.angularVelocity.setZero();for(let w=0;w<4;w++){car.vehicle.applyEngineForce(0,w);car.vehicle.setBrake(35,w);}}
 const timing={};
 for(const version of ['before','after']){
  if(version==='before')for(const b of bodies)h.physicsWorld.removeBody(b);else for(const b of bodies)h.physicsWorld.addBody(b);
  h.physicsWorld.broadphase.dirty=true;for(let i=0;i<600;i++)h.physicsWorld.step(1/60);
  const times=[];for(let i=0;i<1800;i++){const t=performance.now();h.physicsWorld.step(1/60);times.push(performance.now()-t);}times.sort((a,b)=>a-b);timing[version]={medianMs:times[900],p95Ms:times[1710]};
 }
 const facadeDraws=h.WORLD.cityCoverageFacades.length;
 assert.ok(h.WORLD.cityCoverageFacades.every(mesh=>mesh.isInstancedMesh&&!mesh.castShadow&&h.FACADE.chunks.some(c=>c.mesh===mesh)));
 const shellDelta=h.WORLD.cityInfillMeshes.length-old.WORLD.cityInfillMeshes.length;
 assert.ok(facadeDraws+2*shellDelta<=(preset==='PHONE_LOW'?8:16));
 report.push({preset,oldCounts,coverageOpaqueDrawDelta:facadeDraws+shellDelta,coverageDrawDeltaWithShadows:facadeDraws+2*shellDelta,counts:h.WORLD.cityInfillStats,minBuilding,minRoad,minPoint,minTree,maxAlignment,addedBodies:bodies.length,baselineBodies:original.length,addedOpaqueDraws:h.WORLD.cityInfillMeshes.length,addedWithOneShadowPass:2*h.WORLD.cityInfillMeshes.length,extraFacadeCells:0,windowInstances:windows.length,headlessStep:timing});
}
console.log('REPORT '+JSON.stringify(report));console.log('RESULT: PASS (headless components; structural draw count; no device FPS claim)');
