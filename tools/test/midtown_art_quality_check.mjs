// Exercise the production city initialisation sequence, including its art-stage call.
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {collisionHarness, html, root, section, THREE} from './collision_harness.mjs';

const base=execFileSync('git',['show','42a94d686c4cd399fe63ad41c76f59e8778c97e3:index.html'],
    {cwd:root,encoding:'utf8',maxBuffer:4e6});
const hash=v=>createHash('sha256').update(JSON.stringify(v)).digest('hex');
const dims=b=>[b.x,b.z,b.w,b.d,b.h,b.coverage];
const near=(a,b)=>Math.abs(a-b)<.00006;
const matrix=(m,i)=>{const t=new THREE.Matrix4(); m.getMatrixAt(i,t); return t;};
function boxes(m) {
    m.geometry.computeBoundingBox();
    return Array.from({length:m.count},(_,i)=>m.geometry.boundingBox.clone()
        .applyMatrix4(matrix(m,i).premultiply(m.matrixWorld)));
}
const overlap=(a,b,axis)=>Math.min(a.max[axis],b.max[axis])-Math.max(a.min[axis],b.min[axis])>.00006;
const projects=(a,b)=>overlap(a,b,'y') && overlap(a,b,'z');
function batch(m) {
    const mat=m.material;
    return [m.count,m.matrixWorld.elements,Array.from(m.instanceMatrix.array),m.instanceColor && Array.from(m.instanceColor.array),
        mat.type,mat.color.getHex(),mat.roughness,mat.metalness,mat.opacity,mat.emissive.getHex(),!!mat.map,
        m.castShadow,m.receiveShadow,m.visible,m.geometry.parameters];
}
async function world(source,preset) {
    const h=await collisionHarness(source,preset);
    h.PROFILE=preset.split('_')[0];
    Object.assign(h.WORLD,{buildings:[],roofs:[],cameraBlockers:[]});
    Object.assign(h,{cityParcels:h.city,wallMaterials:[new THREE.MeshStandardMaterial(),new THREE.MeshStandardMaterial()],
        windowData:[],nightWindowData:[],VH_I18N:{language:'en',saved:{owned:['starter'],cash:4321,deliveries:3}},
        localStorage:{setItem(k,v){h.payload=[k,JSON.parse(v)];}}});
    Object.assign(h.STATE,{cash:4321,upgradeLevel:2});
    vm.runInContext(section(source,'        const SAVE =','        function saveGame()'),h);
    // Capture the real painted swatch (headless Canvas sink).
    const create=h.document.createElement;
    h.document.createElement=type=>{
        const canvas=create(type), ctx=canvas.getContext('2d'), pixels=[];
        canvas.getContext=()=>new Proxy(ctx,{get(t,k){
            if(k==='fillRect') return (x,y,w,d)=>pixels.push([x,y,w,d,t.fillStyle]);
            return t[k];
        }});
        canvas.pixels=pixels;
        return canvas;
    };
    const stage=section(source,'            buildCityInfill(cityParcels,','            const winGeo =');
    vm.runInContext(stage.replace('buildCityInfill(','buildTestCityInfill('),h);
    h.scene.updateMatrixWorld(true);
    vm.runInContext('persistSave()',h);
    return h;
}
function protectedState(h) {
    const w=h.WORLD;
    return hash([
        [w.midtownFacadePilot,w.midtownStreetscapePilot].map(p=>[p.selected.map(dims),p.meshes.map(batch)]),
        h.windowData,h.nightWindowData,[...w.coverageWindows],w.cityInfillMeshes.map(batch),
        h.city,w.buildings,w.roofs,w.cityInfill.map(b=>[dims(b),b.instance]),
        h.ROAD_NET,w.vehicles.map(v=>[v.name,v.isAI,v.routeId,v.routeIdx,v.chassisBody.position]),h.payload,
        h.physicsWorld.bodies.map(b=>[b.mass,b.position,b.quaternion,b.shapeOffsets,b.shapeOrientations,
            b.shapes.map(s=>[s.type,s.halfExtents,s.radius,s.vertices,s.faces])])
    ]);
}
function verify(h,ref) {
    const w=h.WORLD, art=w.midtownArtPilot;
    assert.ok(art,'missing production art stage');
    assert.ok(art.selected.length===2 && art.selected.every((b,i)=>b===w.midtownStreetscapePilot.selected[i]),'selection/order');
    assert.equal(protectedState(h),protectedState(ref),'protected baseline state');
    const {meshes,selected}=art;
    assert.equal(meshes.length,2);
    assert.equal(h.scene.children.length-ref.scene.children.length,2);
    assert.equal(h.FACADE.chunks.length-ref.FACADE.chunks.length,2);
    assert.equal(new Set(meshes.map(m=>m.material)).size,2);
    for(const m of meshes) {
        const mat=m.material;
        assert.ok(m.isInstancedMesh && m.parent===h.scene && !m.castShadow,'batch/scene/shadow');
        assert.ok(mat.isMeshStandardMaterial && mat.roughness>=.78 && mat.metalness<=.05 &&
            !mat.emissive.getHex() && mat.opacity===1 && !mat.transparent,'opaque matte material');
        const chunks=h.FACADE.chunks.filter(c=>c.mesh===m);
        assert.equal(chunks.length,1);
        m.computeBoundingSphere();
        const {center,radius}=m.boundingSphere;
        assert.ok(near(chunks[0].x,center.x) && near(chunks[0].z,center.z) && near(chunks[0].r,radius));
    }
    const wall=meshes.find(m=>m.material.map), stone=wall?.material, tex=stone?.map;
    assert.ok(tex?.isCanvasTexture && tex.image.width<=256 && tex.image.height<=256);
    assert.equal(meshes.flatMap(m=>Object.values(m.material).filter(v=>v?.isTexture)).length,1);
    assert.ok(tex.wrapS===THREE.RepeatWrapping && tex.wrapT===THREE.RepeatWrapping);
    const pixels=tex.image.pixels;
    assert.equal(new Set(pixels.map(([x,y])=>x+','+y)).size,tex.image.width*tex.image.height);
    const tones=pixels.map(p=>Number(p[4].match(/\d+/)[0]));
    assert.ok(Math.max(...tones)-Math.min(...tones)<=12 && new Set(tones).size>=3,'subtle canvas grain');
    const shader={vertexShader:THREE.ShaderLib.standard.vertexShader};
    stone.onBeforeCompile(shader);
    assert.match(shader.vertexShader,/instanceMatrix\s*\*\s*vec4\(position/,'metric grain coordinates');
    assert.match(shader.vertexShader,/vMapUv\s*=.*stonePos.z.*stonePos.y/);
    const panes=[], glass=new THREE.Box3(new THREE.Vector3(-1.1,-1.2,0),new THREE.Vector3(1.1,1.2,0));
    for(const i of w.coverageWindows) {
        const m=h.windowData[i].matrix;
        if(m.elements[8]>.99) panes.push(glass.clone().applyMatrix4(m));
    }
    const prior=[...w.midtownFacadePilot.meshes,...w.midtownStreetscapePilot.meshes].flatMap(boxes);
    const accents=meshes.find(m=>m!==wall);
    const all=meshes.flatMap(m=>boxes(m).map((p,i)=>{
        const color=new THREE.Color(); m.getColorAt(i,color);
        return {p,m,color:color.getHex()};
    }));
    let checked=0;
    for(const [i,b] of selected.entries()) {
        const east=b.x+b.w/2, left=b.z-b.d/2, right=b.z+b.d/2;
        const parts=all.filter(({p})=>p.min.z>=left-.00006 && p.max.z<=right+.00006);
        checked+=parts.length;
        const old=prior.filter(p=>p.max.x>=east-.001 && p.min.x<=east+.25);
        const windows=panes.filter(p=>near(p.min.x,east+.06) && near((p.min.z+p.max.z)/2,b.z));
        assert.ok(windows.length>=2);
        let area=0,ground=0,spandrels=0;
        const sides=new Set(), palette=i?[0x818775,0x4d584d,0x626a5c]:[0xa99b83,0x5e564d,0x827665];
        for(const {p,m,color} of parts) {
            assert.ok(p.min.x>east && p.max.x<=east+.25006 && p.min.y>=0 && p.max.y<b.h-.5,'facade bounds');
            assert.ok(p.max.y<=2.95006 || p.min.y>=3.24994,'cornice clearance');
            assert.ok(windows.every(q=>!projects(p,q)),'glass clearance');
            assert.ok(old.every(q=>!projects(p,q) || p.max.x<q.min.x-.00006),'old detail clearance');
            const width=p.max.z-p.min.z,height=p.max.y-p.min.y;
            if(m===wall) {
                assert.ok(p.max.x<east+.06 && p.max.x-p.min.x<=.04006 && p.min.y>=3.25);
                assert.equal(color,palette[0]); area+=width*height;
            } else if(p.max.y<=2.95) {
                assert.equal(color,palette[1]); ground+=width*height;
            } else {
                assert.equal(color,palette[2]);
                if(width<1 && height>.5 && p.max.x>east+.16) sides.add(Math.sign((p.min.z+p.max.z)/2-b.z));
                if(width>b.d*.45 && height>.2 && p.max.x>east+.085 && p.max.x<east+.16) spandrels++;
            }
        }
        assert.ok(area>b.d*(b.h-3.8)*.43 && ground>2 && sides.size===2 && spandrels>=2,'architectural coverage/depth');
    }
    assert.equal(checked,all.length,'geometry escaped selected buildings');
    return {counts:[wall.count,accents.count],fingerprint:hash([meshes.map(batch),pixels])};
}
function lifecycle(h) {
    const art=h.WORLD.midtownArtPilot, refs=art.meshes.map(m=>[m,m.material,m.instanceMatrix,m.material.map]);
    const scene=h.scene.children.slice();
    h.STUNT.jumps=[];
    Object.assign(h,{WMAP:{},AUDIO:{stations:['OFF'],stationIndex:0},pursuitTextKey:'',pursuitTextValue:0});
    Object.assign(h.VH_I18N,{setLanguage:()=>true,name:s=>s});
    h.document.querySelectorAll=()=>[]; h.document.getElementById=()=>({});
    for(const n of ['refreshGarageLabels','refreshGpuLabel','updateSkyLabel','qualityLabel','renderDrivingHUD',
        'refreshMissionLabels','setPursuitText','renderBannerText']) h[n]=()=>{};
    vm.runInContext(section(html,'        function changeLanguage(', '        const HUB_PANELS'),h);
    h.teleportTo(110,650,0); h.changeLanguage('zh-TW'); h.changeLanguage('en');
    assert.ok(scene.length===h.scene.children.length && scene.every((m,i)=>m===h.scene.children[i]));
    assert.ok(h.WORLD.midtownArtPilot===art && refs.every(([m,mat,arr,map],i)=>
        art.meshes[i]===m && m.material===mat && m.instanceMatrix===arr && mat.map===map));
}
for(const preset of ['PHONE_LOW','TABLET_MED','DESKTOP_HIGH']) {
    const ref=await world(base,preset), h=await world(html,preset), result=verify(h,ref);
    assert.deepEqual(verify(await world(html,preset),ref),result,'repeat build determinism');
    lifecycle(h);
    console.log(preset,'wall/relief',result.counts.join('/'),'bodies/shapes delta 0/0');
    if(preset==='PHONE_LOW' && process.argv.includes('--mutations')) {
        assert.throws(()=>verify(ref,ref),/missing production art stage/);
        console.log('Baseline rejected: missing production art stage');
        for(const [from,to,reason] of [
            ['const selected = WORLD.midtownStreetscapePilot.selected;', 'const selected = WORLD.midtownStreetscapePilot.selected.slice().reverse();',/selection\/order/],
            ['mid-depth/2,mid+depth/2,','panes[0].lo+1,panes[0].lo+1.6,',/glass clearance/],
            ['mesh.castShadow=false;\n                mesh.receiveShadow=true;\n                mesh.computeBoundingSphere();\n                scene.add(mesh);\n                const {center,radius}=mesh.boundingSphere;',
             'mesh.castShadow=true; mesh.computeBoundingSphere(); scene.add(mesh); const {center,radius}=mesh.boundingSphere;',/batch\/scene\/shadow/]
        ]) {
            const changed=html.replace(from,to);
            assert.notEqual(changed,html);
            const mutated=await world(changed,preset);
            assert.throws(()=>verify(mutated,ref),reason);
            console.log('Mutation rejected:',reason.source);
        }
    }
}
console.log('RESULT: PASS (T-013 R1-R5)');
