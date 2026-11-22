// Exercise the two production listeners, real placed parcels and both teleport branches.
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import vm from 'node:vm';
import {collisionHarness, html, root, section, THREE, CANNON} from './collision_harness.mjs';

const baseline = execFileSync('git',['show','3541e6271dbe2542ecf240a2bf5a4003bbe282fe:index.html'],
    {cwd:root,encoding:'utf8',maxBuffer:4e6});
const travelSource = page => section(page,'        const FAST_TRAVEL =','        const WMAP =');
const old = vm.runInNewContext(travelSource(baseline)+'FAST_TRAVEL',{THREE,tr:k=>k});
const signature = t => [t.id,t.icon,t.x,t.z,t.h,t.y?.toString()];
const key = 'midtown_west', id = 'MIDTOWN_W', icon = '🏢';
const names = {en:'Midtown West','zh-TW':'中城西側'};
const table = JSON.parse(html.match(/const STRINGS = ([\s\S]*?);\s*\/\/ I18N_TABLE_END/)[1]);
for (const [lang,name] of Object.entries(names)) assert.equal(table[lang][key],name,lang+' translation');
const missions = section(html,'id="missions-modal"','<div role="tabpanel"');
const buttons = [...missions.matchAll(/<button\b([^>]*\bdata-tp="([^"]+)"[^>]*)>([\s\S]*?)<\/button>/g)];
const matches = buttons.filter(([,attrs,value]) => value === id && /class="[^"]*\btp-btn\b/.test(attrs));
assert.equal(matches.length,1,'one Missions button');
const label = matches[0][3].match(/<span data-i18n="midtown_west">Midtown West<\/span>/);
assert.ok(label && matches[0][3].replace(label[0],'').trim() === icon,'persistent Missions icon and bound label');

function element() {
    return {style:{setProperty(){}},classList:{add(){},remove(){}},children:[],
        addEventListener(type,fn){this[type]=fn;},appendChild(child){this.children.push(child);}};
}
for (const preset of ['PHONE_LOW','DESKTOP_HIGH']) {
    const h = await collisionHarness(html,preset);
    Object.assign(h.WORLD,{buildings:[],roofs:[],cameraBlockers:[]});
    h.buildTestCityInfill(h.city,[new THREE.MeshStandardMaterial(),new THREE.MeshStandardMaterial()],[],[]);
    const entries = h.arrivals, target = entries.find(t=>t.id===id);
    assert.equal(entries.filter(t=>t.id===id).length,1);
    assert.equal(entries.at(-1),target);
    assert.deepEqual(Array.from(entries.slice(0,-1),signature),Array.from(old,signature),'original destinations');
    assert.equal(target.icon,icon);
    assert.ok(!('y' in target));
    const {x,z,h:heading} = target;
    const parcels = [...h.city,...h.WORLD.roofs];
    assert.ok(h.city.length && h.WORLD.cityInfill.length && h.WORLD.roofs.length);
    const gap = Math.min(...parcels.map(b => Math.hypot(Math.max(Math.abs(b.x-x)-b.w/2,0),
        Math.max(Math.abs(b.z-z)-b.d/2,0))));
    assert.ok(gap > 0,'arrival inside a placed building');
    assert.ok(Math.abs(x+240)<=10 && Math.abs(z+300)<=15 && Math.abs(heading+Math.PI/2)<1e-6);
    assert.ok(h.ROAD_NET.avenuesX.includes(-240) && Math.abs(x+240)<h.ROAD_NET.avenueHalf);
    const snap = h.snapToRoad(x,z), displacement = Math.hypot(x-snap.x,z-snap.z);
    assert.ok(snap.name === h.tr('avenue') && displacement<=6);

    const nodes = new Map(), btn = element(), boundLabel = {dataset:{i18n:key}};
    btn.getAttribute = attr => attr==='data-tp' ? matches[0][2] : null;
    Object.assign(h.document,{documentElement:{},addEventListener(){},createElement:element,
        querySelector:()=>null,querySelectorAll:s=>s==='.tp-btn'?[btn]:s==='[data-i18n]'?[boundLabel]:[],
        getElementById(n){if(!nodes.has(n)) nodes.set(n,element());return nodes.get(n);}});
    Object.assign(h,{window:element(),localStorage:{getItem:()=>null},setTimeout:f=>f(),drawWorldMap(){},
        districtName:()=>'',WMAP:{scale:.35}});
    const runtime = html.match(/<script>\s*\/\/ I18N_TABLE_START([\s\S]*?)<\/script>/)[1];
    vm.runInContext(runtime+'\nthis.locale=VH_I18N;'+
        section(html,'        function wmSelect(','        // 導航點')+
        section(html,'        function setupWorldMap()', '        // ==================== 11.')+
        section(html,"            document.querySelectorAll('.tp-btn')","            document.getElementById('cancel-mission-btn')"),h);
    const car = h.WORLD.vehicles[0];
    for (const [lang,name] of Object.entries(names)) {
        h.locale.setLanguage(lang);
        assert.equal(boundLabel.textContent,name);
        assert.equal(target.name,name);
        const chips = h.document.getElementById('wm-chips').children;
        chips.length=0;
        h.setupWorldMap();
        const found = chips.filter(b=>b.innerHTML.includes('data-map-location="'+id+'"'));
        assert.equal(found.length,1);
        assert.ok(found[0].innerHTML.includes(icon) && found[0].innerHTML.includes('>'+name+'<'));
        const mapTravel = () => {found[0].click();h.document.getElementById('wm-travel').click();};
        for (const travel of [mapTravel,()=>btn.click()]) for (const mode of ['FOOT','CAR']) {
            h.STATE.mode=mode; h.STATE.currentVehicle=mode==='CAR'?car:null;
            const body = mode==='CAR'?car.chassisBody:h.PLAYER.body;
            body.position.set(50,3,50);
            const job = {};
            vm.runInContext('DELIVERY',h).job=job;
            travel();
            assert.deepEqual([body.position.x,body.position.z],[50,50],'delivery block');
            assert.equal(vm.runInContext('DELIVERY.job',h),job);
            vm.runInContext('DELIVERY.job=null',h);
            travel();
            const forward = car.chassisBody.quaternion.vmult(new CANNON.Vec3(0,0,1));
            const actual = mode==='CAR'?Math.atan2(forward.x,forward.z):h.PLAYER.heading;
            assert.deepEqual([body.position.x,body.position.z],[x,z]);
            assert.ok(Math.abs(actual-heading)<1e-6,'runtime west heading');
        }
    }
    h.STATE.mode='FOOT'; h.STATE.currentVehicle=null;
    h.fastTravelTo(entries[0]);
    assert.deepEqual([h.PLAYER.body.position.x,h.PLAYER.body.position.z],[old[0].x,old[0].z]);
    console.log(preset,{x,z,heading,snapDisplacement:displacement,nearestBuildingMeters:gap,placed:parcels.length});
}
console.log('RESULT: PASS (both menus, locales, foot/car landings, delivery guard and original destinations)');
