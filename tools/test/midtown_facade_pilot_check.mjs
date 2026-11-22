// Component test: the normal city builder calls the pilot after placements, styling and glazing.
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {collisionHarness, html, section, THREE} from './collision_harness.mjs';

const EPS = .00005;
const near = (a,b) => Math.abs(a-b) < EPS;
const fields = b => [b.x,b.z,b.w,b.d,b.h,b.styleHash];
function instanceMatrix(mesh, i) {
    const m = new THREE.Matrix4();
    mesh.getMatrixAt(i,m);
    return m;
}
function snapshot(h, glass, night) {
    const world = h.WORLD;
    return JSON.stringify({
        bodies: h.physicsWorld.bodies.map(b => [b.id,b.position,b.quaternion,b.shapeOffsets,b.shapeOrientations,
            b.shapes.map(s => [s.id,s.type,s.halfExtents,s.radius,s.vertices,s.faces])]),
        roadNet: h.ROAD_NET, routes: h.ROAD_NET.routes, vehicles: world.vehicles.map(v => v.chassisBody.id),
        buildings: world.buildings, roofs: world.roofs, trees: h.TREES.list.map(t => [t.type,t.x,t.y,t.z,t.scale,t.rot,t.tint]),
        parcels: world.cityInfill.map(b => [fields(b),instanceMatrix(b.mesh,b.instance).elements,b.mesh.matrix.elements]),
        stats: world.cityInfillStats, glass, night, save: h.SAVE
    });
}
function expectedSelection(infill) {
    const candidates = Array.from(infill).filter(b => b.coverage === true && b.district === 'MID' &&
        -420 < b.x && b.x < -240 && -360 < b.z && b.z < -240);
    const key = b => [Math.abs(b.x+240), Math.abs(b.z+300), b.x,b.z,b.w,b.d];
    return candidates.sort((a,b) => {
        const left = key(a), right = key(b);
        const first = left.findIndex((n,i) => n !== right[i]);
        return first === -1 ? 0 : left[first]-right[first];
    }).slice(0,6);
}
function verifyGeometry(h, glass, selected, meshes, additions) {
    assert.ok(meshes.length > 0 && meshes.length <= 2);
    assert.equal(new Set(meshes.map(m => m.material)).size <= 2,true);
    assert.ok(additions.length === meshes.length && additions.every(m => meshes.includes(m)),
        'all and only pilot meshes attached');
    const boxes = [];
    h.scene.updateMatrixWorld(true);
    for (const m of meshes) {
        assert.ok(m.isInstancedMesh && m.parent === h.scene && m.visible && !m.castShadow);
        assert.ok(m.material.isMeshStandardMaterial && !m.material.transparent && m.material.opacity === 1 &&
            m.material.roughness >= .8 && m.material.metalness === 0 && !m.material.emissive.getHex());
        assert.ok(!Object.values(m.material).some(x => x?.isTexture));
        const chunks = h.FACADE.chunks.filter(c => c.mesh === m);
        assert.equal(chunks.length,1);
        m.computeBoundingSphere();
        const {center,radius} = m.boundingSphere;
        assert.ok(near(chunks[0].x,center.x) && near(chunks[0].z,center.z) && near(chunks[0].r,radius));
        m.geometry.computeBoundingBox();
        for (let i=0;i<m.count;i++) {
            boxes.push(m.geometry.boundingBox.clone().applyMatrix4(instanceMatrix(m,i).premultiply(m.matrixWorld)));
        }
    }
    function take(predicate, label) {
        const i = boxes.findIndex(predicate);
        assert.ok(i >= 0,label);
        boxes.splice(i,1);
    }
    for (const b of selected) {
        const east = b.x+b.w/2;
        take(({min,max}) => min.x >= east-EPS && max.x <= east+.20+EPS &&
            near((min.y+max.y)/2,b.h-.22) && near(max.y-min.y,.22) &&
            near(min.z,b.z-b.d/2) && near(max.z,b.z+b.d/2),'missing east roofline');
        const panes = Array.from(h.WORLD.coverageWindows,i => glass[i].matrix.elements)
            .filter(e => near(e[12],east+.06) && near(e[14],b.z) && e[8] > .99)
            .sort((a,c) => a[13]-c[13]).slice(0,2);
        assert.equal(panes.length,Math.min(2,Math.floor((b.h-6)/4.6)));
        for (const [floor,e] of panes.entries()) {
            const y=e[13], halfWidth=1.1*Math.hypot(e[0],e[1],e[2]);
            assert.ok(near(y,6.2+floor*4.6) && near(halfWidth,1.1*b.w/5));
            const left=e[14]-halfWidth, right=e[14]+halfWidth, bottom=y-1.2, top=y+1.2;
            const outside = ({min,max}) => min.x >= e[12]+.07-EPS && max.x <= east+.25+EPS &&
                max.x > min.x && max.y < b.h;
            for (const side of ['left','right']) {
                take(box => outside(box) && near(box.min.y,bottom) && near(box.max.y,top) &&
                    near(box.max.z-box.min.z,.12) && (side==='left' ? near(box.max.z,left) : near(box.min.z,right)),
                    'window side rail '+side);
            }
            for (const edge of ['bottom','top']) {
                take(box => outside(box) && near(box.min.z,left-.12) && near(box.max.z,right+.12) &&
                    near(box.max.y-box.min.y,.12) && (edge==='bottom' ? near(box.max.y,bottom) : near(box.min.y,top)),
                    'horizontal rail '+edge);
            }
            take(box => outside(box) && box.max.x-box.min.x <= .18+EPS && near(box.max.y,bottom-.12) &&
                box.min.y < box.max.y && box.min.z < left && box.max.z > right,'projecting sill');
        }
    }
    assert.equal(boxes.length,0,'unmatched decorations');
}
for (const preset of ['PHONE_LOW','TABLET_MED','DESKTOP_HIGH']) {
    const h = await collisionHarness(html,preset);
    h.PROFILE = preset.split('_')[0];
    Object.assign(h.WORLD,{buildings:[],roofs:[],cameraBlockers:[]});
    const glass=[], night=[];
    const start = html.indexOf('        const SAVE ='), end = html.indexOf('        function cooldownLeft',start);
    h.VH_I18N = {saved:{cash:50},language:'en'};
    vm.runInContext(html.slice(start,end)+'this.SAVE = SAVE;',h);
    const build = h.buildMidtownFacadePilot;
    assert.equal(typeof build,'function','missing production pilot');
    let selectedRows, calls=0;
    h.buildMidtownFacadePilot = unit => {
        calls++;
        const before = snapshot(h,glass,night);
        const objects = new Set();
        h.scene.traverse(o => objects.add(o));
        const expected = expectedSelection(h.WORLD.cityInfill);
        assert.equal(expected.length,6);
        const random = h.Math.random;
        h.Math.random = () => assert.fail('pilot used RNG');
        try { build(unit); } finally { h.Math.random = random; }
        assert.equal(snapshot(h,glass,night) === before,true,'protected world, save or glazing changed');
        const {selected,meshes} = h.WORLD.midtownFacadePilot;
        assert.equal(selected.length,6);
        selected.forEach((b,i) => assert.equal(b === expected[i],true,'selection or ordering changed'));
        const added=[];
        h.scene.traverse(o => { if (!objects.has(o)) added.push(o); });
        verifyGeometry(h,glass,selected,meshes,added);
        selectedRows = Array.from(selected,fields);
    };
    h.buildTestCityInfill(h.city,[new THREE.MeshStandardMaterial(),new THREE.MeshStandardMaterial()],glass,night);
    assert.equal(calls,1,'pilot must run once in world initialization');
    console.log(preset,'east (+X) [x,z,w,d,h,styleHash]',JSON.stringify(selectedRows));

    // Exercise the production lifecycle handlers. Only their unrelated HUD and storage sinks are stubbed.
    h.STUNT.jumps = [];
    Object.assign(h,{WMAP:{}, AUDIO:{stations:['OFF'],stationIndex:0}, pursuitTextKey:'', pursuitTextValue:0});
    h.document.querySelectorAll = () => [];
    h.document.getElementById = () => ({});
    Object.assign(h.VH_I18N,{setLanguage:() => true,name:s => s});
    for (const name of ['persistSave','refreshGarageLabels','refreshGpuLabel','updateSkyLabel','qualityLabel',
        'renderDrivingHUD','refreshMissionLabels','setPursuitText','renderBannerText']) h[name] = () => {};
    vm.runInContext(section(html,'        function changeLanguage(', '        const HUB_PANELS'),h);
    const meshesBefore = h.scene.children.slice();
    h.teleportTo(110,650,0);
    h.changeLanguage('zh-TW');
    h.changeLanguage('en');
    assert.equal(calls,1,'teleport/language rebuilt facade');
    assert.ok(h.scene.children.length === meshesBefore.length && meshesBefore.every((m,i) => m === h.scene.children[i]));

    // Replay with the same placed parcels in reverse traversal order. Probe each open
    // boundary separately: widening the far edge can otherwise leave the top six intact.
    const live = h.WORLD.cityInfill;
    const sample = h.WORLD.midtownFacadePilot.selected[0];
    const unit = new THREE.BoxGeometry(1,1,1);
    h.WORLD.cityInfill = Array.from(live).reverse();
    build(unit);
    assert.deepEqual(Array.from(h.WORLD.midtownFacadePilot.selected,fields),selectedRows);
    for (const override of [{x:-420},{x:-240},{z:-360},{z:-240},{coverage:false},{district:'CBD'}]) {
        h.WORLD.cityInfill = [{...sample,...override}];
        build(unit);
        assert.equal(h.WORLD.midtownFacadePilot.selected.length,0,'ineligible '+JSON.stringify(override));
    }
}
console.log('RESULT: PASS (live placement, east glazing, batches, LOD and protected world state)');
