// Run the full production city infill path twice: independent base and candidate worlds.
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import vm from 'node:vm';
import {collisionHarness, html, root, section, THREE} from './collision_harness.mjs';

const base = execFileSync('git',['show','e267e7231ca6271b1c24dbdf922cd4f1bb887678:index.html'],
    {cwd:root,encoding:'utf8',maxBuffer:4e6});
const digest = v => createHash('sha256').update(JSON.stringify(v)).digest('hex');
const eps = .00005;
const near = (a,b) => Math.abs(a-b)<eps;
const dims = b => [b.x,b.z,b.w,b.d,b.h,b.district,b.coverage];
const matrix = (m,i) => { const t = new THREE.Matrix4(); m.getMatrixAt(i,t); return t; };
function boxes(mesh) {
    mesh.geometry.computeBoundingBox();
    return Array.from({length:mesh.count},(_,i) =>
        mesh.geometry.boundingBox.clone().applyMatrix4(matrix(mesh,i).premultiply(mesh.matrixWorld)));
}
async function world(source,preset) {
    const h = await collisionHarness(source,preset);
    h.PROFILE = preset.split('_')[0];
    Object.assign(h.WORLD,{buildings:[],roofs:[],cameraBlockers:[]});
    const glass=[], night=[];
    h.buildTestCityInfill(h.city,[new THREE.MeshStandardMaterial(),new THREE.MeshStandardMaterial()],glass,night);
    h.scene.updateMatrixWorld(true);
    return {h,glass,night};
}
function protectedState({h,glass,night}) {
    const w=h.WORLD;
    return {
        bodies:h.physicsWorld.bodies.length, shapes:h.physicsWorld.bodies.reduce((n,b)=>n+b.shapes.length,0),
        physics:digest(h.physicsWorld.bodies.map(b=>[b.mass,b.position,b.quaternion,b.shapeOffsets,b.shapeOrientations,
            b.shapes.map(s=>[s.type,s.halfExtents,s.radius,s.vertices,s.faces])])),
        placements:digest([h.city,w.roofs,w.buildings,w.cityInfill.map(b=>[dims(b),matrix(b.mesh,b.instance).elements])]),
        roads:digest(h.ROAD_NET), vehicles:digest(w.vehicles.map(v=>[v.name,v.chassisBody.position])),
        windows:digest([glass,night]), facade:digest([w.midtownFacadePilot.selected.map(dims),
            w.midtownFacadePilot.meshes.map(m=>Array.from(m.instanceMatrix.array))])
    };
}
function checkGeometry({h,glass}, segments) {
    const w=h.WORLD, {selected,meshes}=w.midtownStreetscapePilot;
    const [trim,panels,paving] = meshes.map(boxes);
    const trimCount=trim.length, panelCount=panels.length, pavingCount=paving.length;
    function take(group,fn,reason) {
        const index=group.findIndex(fn);
        assert.ok(index>=0,reason);
        return group.splice(index,1)[0];
    }
    for (const b of selected) {
        const east=b.x+b.w/2, left=b.z-b.d/2, right=b.z+b.d/2;
        const onFace = p => p.min.x>=east-eps && p.max.x<=east+.25+eps && p.min.z>=left-eps && p.max.z<=right+eps;
        const storefront = p => onFace(p) && p.max.y<=2.95+eps && p.min.y>=-eps;
        const centered = p => near((p.min.z+p.max.z)/2,b.z);
        const door=take(panels,p=>storefront(p) && centered(p),'central east door');
        assert.ok(door.max.z-door.min.z>=1.4-eps && door.max.z-door.min.z<=1.8+eps &&
            door.max.y-door.min.y>=2.3-eps && door.max.y-door.min.y<=2.8+eps && near(door.min.y,.18));
        for (const side of [-1,1]) {
            const pane=take(panels,p=>storefront(p) && (side<0?p.max.z<door.min.z:p.min.z>door.max.z),'side window');
            assert.ok(pane.max.z-pane.min.z>=1.2-eps && pane.min.z>=left+.25-eps && pane.max.z<=right-.25+eps);
            const [a,c]=side<0?[pane.max.z,door.min.z]:[door.max.z,pane.min.z];
            const jamb=take(trim,p=>storefront(p) && near(p.min.z,a) && near(p.max.z,c) &&
                near(p.min.y,door.min.y) && near(p.max.y,door.max.y),'door jamb');
            assert.ok(c-a>=.15-eps && pane.max.x-door.max.x>=.06-eps && jamb.max.x-pane.max.x>=.06-eps);
            take(trim,p=>storefront(p) && near(p.min.z,pane.min.z) && near(p.max.z,pane.max.z) &&
                near(p.min.y,.18) && near(p.max.y,pane.min.y),'window plinth');
        }
        take(trim,p=>storefront(p) && centered(p) && near(p.min.y,door.max.y) && p.max.z>door.max.z,'header');
        take(trim,p=>storefront(p) && near(p.min.z,door.min.z) && near(p.max.z,door.max.z) &&
            near(p.max.y,.18) && near(p.max.x,east+.20),'threshold to apron');
        // Ignore other T-010 elevations behind this wall when checking the Y/Z projection.
        const existing=w.midtownFacadePilot.meshes.flatMap(boxes).filter(q=>q.min.x>=east-eps && q.max.x<=east+.25+eps);
        const glassBox=new THREE.Box3(new THREE.Vector3(-1.1,-1.2,0),new THREE.Vector3(1.1,1.2,0));
        for (const i of w.coverageWindows) {
            const m=glass[i].matrix, e=m.elements;
            if (near(e[12],east+.06) && near(e[14],b.z)) existing.push(glassBox.clone().applyMatrix4(m));
        }
        const unobstructed = p => existing.every(q =>
            Math.min(p.max.y,q.max.y)-Math.max(p.min.y,q.min.y)<=eps ||
            Math.min(p.max.z,q.max.z)-Math.max(p.min.z,q.min.z)<=eps);
        for (const side of [-1,1]) {
            const p=take(trim,p=>onFace(p) && p.min.y>=3.25-eps && p.max.y<=b.h-.25+eps &&
                p.max.y>b.h-1 && side*((p.min.z+p.max.z)/2-b.z)>b.d/2-1,'upper post');
            assert.ok(p.max.z-p.min.z>=.16-eps && p.max.z-p.min.z<=.28+eps &&
                p.max.x-east>=.1-eps && p.max.x-east<=.22+eps && unobstructed(p));
        }
        for (const y of [4.4,9,13.6].filter(y=>y<b.h-.5)) {
            const p=take(trim,p=>onFace(p) && near((p.min.y+p.max.y)/2,y) && centered(p),'floor band');
            assert.ok(p.max.y-p.min.y>=.10-eps && p.max.y-p.min.y<=.22+eps &&
                p.max.x-east<=.22+eps && p.max.z-p.min.z>b.d-2 && unobstructed(p));
        }
        for (const [sx,start,end] of segments) {
            const lo=Math.max(left,start), hi=Math.min(right,end);
            if (hi<=lo) continue;
            const inner=sx-2.5, outer=sx+2.5;
            const full=p=>near(p.min.z,lo) && near(p.max.z,hi);
            take(paving,p=>full(p) && near(p.min.x,east+.20) && near(p.max.x,inner) &&
                near(p.min.y,0) && near(p.max.y,.18),'continuous flush apron');
            const overlay=p=>p.min.x>=inner-eps && p.max.x<=outer+eps && p.min.z>=lo-eps &&
                p.max.z<=hi+eps && p.max.y>=.195-eps && p.max.y<=.215+eps;
            take(paving,p=>overlay(p) && full(p) && p.min.x>=outer-.3,'street curb');
            const seams=paving.filter(p=>overlay(p) && p.max.x-p.min.x>4 && p.max.z-p.min.z<.10)
                .sort((a,b)=>a.min.z-b.min.z);
            assert.ok(seams.length && seams[0].min.z-lo<3 && hi-seams.at(-1).max.z<3,'sidewalk seam coverage');
            seams.forEach((p,i)=>{
                if (i) assert.ok(p.min.z-seams[i-1].min.z>=2-eps && p.min.z-seams[i-1].min.z<=3+eps);
                paving.splice(paving.indexOf(p),1);
            });
        }
    }
    assert.equal(trim.length+panels.length+paving.length,0,'unexpected geometry outside contracts');
    return [trimCount,panelCount,pavingCount];
}
for (const preset of ['PHONE_LOW','TABLET_MED','DESKTOP_HIGH']) {
    const candidate=await world(html,preset), {h,glass}=candidate, w=h.WORLD;
    assert.ok(w.midtownStreetscapePilot,'missing production streetscape');
    const ref=await world(base,preset);
    assert.deepEqual(protectedState(candidate),protectedState(ref),'baseline world changed');
    const {selected,meshes}=w.midtownStreetscapePilot, old=w.midtownFacadePilot;
    assert.equal(selected.length,2);
    assert.ok(selected.every((b,i)=>b===old.selected[i] && b.coverage && w.cityInfill.includes(b)),'pilot target/order');
    assert.equal(meshes.length,3);
    assert.ok(new Set(meshes.map(m=>m.material)).size<=3);
    assert.equal(h.scene.children.length-ref.h.scene.children.length,3);
    assert.equal(h.FACADE.chunks.length-ref.h.FACADE.chunks.length,3);
    for (const m of meshes) {
        assert.ok(m.parent===h.scene && m.isInstancedMesh && !m.castShadow && !old.meshes.includes(m));
        const mat=m.material;
        assert.ok(mat.isMeshStandardMaterial && mat.roughness>=.72 && mat.metalness<=.08 && !mat.transparent &&
            mat.opacity===1 && !mat.emissive.getHex() && !Object.values(mat).some(v=>v?.isTexture));
        const entries=h.FACADE.chunks.filter(c=>c.mesh===m);
        assert.equal(entries.length,1);
        m.computeBoundingSphere();
        const {center,radius}=m.boundingSphere;
        assert.ok(near(entries[0].x,center.x) && near(entries[0].z,center.z) && near(entries[0].r,radius));
    }
    const segments=[];
    h.visitAvenueSidewalks(-240,(sx,a,b)=>{if (sx< -240) segments.push([sx,a,b]);});
    const adjacent=segments.filter(([,a,c])=>selected.some(b=>a<b.z+b.d/2 && c>b.z-b.d/2));
    assert.ok(adjacent.length && adjacent.every(([sx])=>near(sx,-254.5)));
    const counts=checkGeometry(candidate,adjacent);
    const travel=h.arrivals.find(t=>t.id==='MIDTOWN_W');
    console.log(preset,JSON.stringify({parcels:selected.map(dims),sidewalk:adjacent,counts,
        arrivalToEastWall:selected.map(b=>Math.hypot(travel.x-b.x-b.w/2,Math.max(0,Math.abs(travel.z-b.z)-b.d/2))),
        bodies:h.physicsWorld.bodies.length,shapes:protectedState(candidate).shapes}));

    // Exercise real event handlers; replace only UI/storage sinks missing from the component harness.
    h.STUNT.jumps=[];
    Object.assign(h,{WMAP:{},SAVE:{},AUDIO:{stations:['OFF'],stationIndex:0},pursuitTextKey:'',pursuitTextValue:0,
        VH_I18N:{setLanguage:()=>true,name:s=>s}});
    h.document.querySelectorAll=()=>[]; h.document.getElementById=()=>({});
    for (const n of ['persistSave','refreshGarageLabels','refreshGpuLabel','updateSkyLabel','qualityLabel',
        'renderDrivingHUD','refreshMissionLabels','setPursuitText','renderBannerText']) h[n]=()=>{};
    vm.runInContext(section(html,'        function changeLanguage(', '        const HUB_PANELS'),h);
    const scene=h.scene.children.slice(), arrays=meshes.map(m=>m.instanceMatrix);
    h.teleportTo(110,650,0); h.changeLanguage('zh-TW'); h.changeLanguage('en');
    assert.ok(h.scene.children.length===scene.length && scene.every((m,i)=>h.scene.children[i]===m));
    assert.ok(meshes.every((m,i)=>m.instanceMatrix===arrays[i]) && w.midtownStreetscapePilot.meshes===meshes);

    // The shipped buildings all exceed 14.1 m. Probe a shorter building and a clipped
    // sidewalk to expose missing height gates or use of hard-coded sidewalk extents.
    const first=selected[0], savedHeight=first.h;
    first.h=13.9;
    const visit=h.visitAvenueSidewalks;
    const clipped=[[adjacent[0][0],first.z-2,first.z+2]];
    h.visitAvenueSidewalks=(x,fn)=>{assert.equal(x,-240);clipped.forEach(s=>fn(...s));};
    h.buildMidtownStreetscape(new THREE.BoxGeometry(1,1,1),glass);
    checkGeometry(candidate,clipped);
    first.h=savedHeight; h.visitAvenueSidewalks=visit;
}
console.log('RESULT: PASS (R1–R5; real instance matrices, production sidewalk segments and baseline world)');
