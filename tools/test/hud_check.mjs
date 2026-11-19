// Structural and event/radar checks against actual source. No browser layout or FPS claims.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import { execFileSync } from 'node:child_process';
const root = new URL('../../', import.meta.url);
const html = fs.readFileSync(new URL('index.html', root), 'utf8');
const baselineRef = process.argv[2] || 'd96335833dba1207ab693a70dd0d77c91d477019';
const before = execFileSync('git', ['show', `${baselineRef}:index.html`], {cwd:root,maxBuffer:2e6}).toString();
const ids = [...html.matchAll(/\bid="([^"]+)"/g)].map(m=>m[1]);
assert.equal(ids.length, new Set(ids).size, 'Duplicate DOM IDs');
for (const id of [...before.matchAll(/\bid="([^"]+)"/g)].map(m=>m[1])) assert.ok(ids.includes(id), `Removed ID: ${id}`);
assert.match(html, /id="radar-canvas" width="140" height="140"/);
const dialog = html.slice(html.indexOf('<dialog id="quick-actions"'),html.indexOf('</dialog>'));
for (const name of ['quality','mission','garage','cop-chase','radio','cam','sky','settings']) assert.ok(dialog.includes(`id="pill-${name}"`));
assert.ok(dialog.includes('id="hud-crates"') && dialog.includes('id="desktop-hints"'));
function between(source, start, end) { const a=source.indexOf(start); assert.ok(a>=0,start);const b=source.indexOf(end,a);assert.ok(b>a,end);return source.slice(a,b); }
for (const [start,end] of [
    ['        const CAMERA_CONFIG =','        const camera ='],
    ['        function getActivePosition()', '        // ==================== 賺錢玩法'],
    ['        function fastTravelTo(', '        function setWaypoint('],
    ['        const SAVE =','        const STATE =']
]) assert.equal(between(html,start,end),between(before,start,end),`Out-of-scope change: ${start}`);
assert.equal((html.match(/new THREE.WebGLRenderer/g)||[]).length,(before.match(/new THREE.WebGLRenderer/g)||[]).length);
assert.ok(!between(html,'        function drawRadar(now','        // ==================== 世界地圖').includes('...ROAD_NET'));
console.log('PASS: preserved IDs, single 140x140 radar, all eight actions, unchanged camera/save/fast-travel paths');

class Element {
    constructor(id) {
        this.id=id; this.open=false; this.listeners={}; this.style={}; this.value=''; this.dataset={};
        const values=new Set(['missions-modal','garage-modal','settings-modal','world-map'].includes(id)?['hidden']:[]);
        this.classList={add:(...x)=>x.forEach(v=>values.add(v)),remove:(...x)=>x.forEach(v=>values.delete(v)),contains:x=>values.has(x),toggle:(x,on)=>{if(on??!values.has(x))values.add(x);else values.delete(x);}};
    }
    setAttribute(name,value){this[name]=value;}
    focus(){this.focused=true;}
    click(){this.emit('click');}
    addEventListener(type,fn){(this.listeners[type]??=[]).push(fn);}
    emit(type,event={}){event.preventDefault??=()=>{};event.stopPropagation??=()=>{};event.target??=this;for(const fn of this.listeners[type]||[])fn(event);}
    showModal(){this.open=true;} close(){this.open=false;this.emit('close');}
    getBoundingClientRect(){return {left:0,top:0,width:120,height:120};}
    closest(selector){return selector==='button'?this:null;}
}
function documentStub(){
    const elements=new Map(); const doc=new Element('document');doc.hidden=false;
    doc.getElementById=id=>{if(!elements.has(id))elements.set(id,new Element(id));return elements.get(id);};
    doc.querySelectorAll=selector=>selector==='#touch-controls .active-press'?[...elements.values()].filter(e=>e.classList.contains('active-press')):[];
    return doc;
}
function radarHarness(source){
    const document=documentStub(), trace=[];
    const ctx=new Proxy({}, {get:(t,p)=>p in t?t[p]:(...args)=>trace.push([p,...args]),set:(t,p,v)=>{t[p]=v;trace.push([p,v]);return true;}});
    document.getElementById('radar-canvas').getContext=()=>ctx;
    const road={half:6,pts:[{x:0,z:0},{x:1,z:1},{x:2,z:2},{x:3,z:3}]};
    const context=vm.createContext({document,performance:{now:()=>0},Math,Number,
        getActivePosition:()=>({x:0,z:0}),getActiveHeading:()=>0,
        ROAD_NET:{hill:{cx:0,cz:0,rx:200,rz:200},suburb:{x0:-100,x1:-50,z0:0,z1:100},avenuesX:[-400,110],avenueZ:900,hillAveZ:300,crossZ:[0,400],crossX0:-600,crossX1:250,ribbons:[road],terrainRoads:[road],ring:road,spurs:[road],roundabouts:[{x:0,z:0,rOut:10,rIn:8}]},
        STATE:{quality:'MED',time:0,currentVehicle:null,waypoint:{x:1000,z:0}},
        WORLD:{vehicles:[{chassisGroup:{visible:true},chassisBody:{position:{x:5,z:5}},isPolice:true}]},
        MISSION:{active:true,currentCP:0,checkpoints:[{x:10,z:20}]},
        DELIVERY:{depots:[{x:5,z:5}],job:{dest:{x:0,z:1000}}},STUNT:{jumps:[{id:0,x:20,z:20}]},SAVE:{jumps:{}}
    });
    const extraStart=source.includes('        function drawRadarDot(')?'        function drawRadarDot(':'        function drawRadarExtras(';
    const radarStart=source.includes('        const RADAR =')?'        const RADAR =':'        function drawRadar()';
    vm.runInContext(between(source,extraStart,'        function drawMapExtras(')+between(source,radarStart,'        // ==================== 世界地圖')+'\nthis.radar = typeof RADAR === "undefined" ? null : RADAR;',context);
    return {context,trace,document};
}
const original=radarHarness(before), current=radarHarness(html);
original.context.drawRadar(); current.context.drawRadar(0);
assert.deepEqual(current.trace,original.trace,'Road and waypoint/police/mission/delivery/stunt rendering changed');
console.log('PASS: identical radar draw-command trace with all marker types');
for(const fps of [30,60,120])for(const [quality,expected] of [['MED',100],['LOW',80]]){
    const {context,trace}=radarHarness(html);context.STATE.quality=quality;
    for(let n=0;n<fps*10;n++)context.drawRadar(n*1000/fps);
    const draws=trace.filter(x=>x[0]==='clearRect').length;
    assert.ok(Math.abs(draws-expected)<=1,`${fps} Hz ${quality}: ${draws}`);
}
for(const hiddenCase of ['document','observer','dialog','missions-modal','garage-modal','settings-modal','world-map']){
    const {context,trace,document}=radarHarness(html);
    if(hiddenCase==='document')document.hidden=true;
    else if(hiddenCase==='observer')context.radar.visible=false;
    else if(hiddenCase==='dialog')context.radar.actions.open=true;
    else document.getElementById(hiddenCase).classList.remove('hidden');
    for(let t=0;t<1000;t+=16)context.drawRadar(t);
    assert.equal(trace.length,0,hiddenCase);
    document.hidden=false;context.radar.visible=true;context.radar.actions.open=false;
    for(const e of context.radar.overlays)e.classList.add('hidden');
    context.drawRadar(1000);assert.equal(trace.filter(x=>x[0]==='clearRect').length,1);
}
console.log('PASS: 10 Hz normal / 8 Hz LOW at 30/60/120 render Hz; hidden/menu suppression and resume');

const document=documentStub(), window=new Element('window');const INPUT={};
const timers=new Map(),frames=[];let timerId=0,mapDraws=0;
const context=vm.createContext({document,window,INPUT,console,parseInt,parseFloat,
    canvas:document.getElementById('game-canvas'),CAM:{pointers:new Map(),sens:1,invertY:false},RADAR:{lastDraw:0},
    STATE:{upgradeLevel:1,cash:3500,fpsCap:30},SAVE:{owned:[]},GPU_NAME:'test',PROFILE:'TABLET',
    camera:{updateProjectionMatrix(){}},applyResolution(){},
    WMAP:{open:false,pointers:new Map()},
    clearInterval(id){timers.delete(id);},setInterval(fn){const id=++timerId;timers.set(id,fn);return id;},
    requestAnimationFrame(fn){frames.push(fn);},getActivePosition:()=>({x:10,z:20}),
    wmSelect(){mapDraws++;},drawWorldMap(){mapDraws++;},
    toggleEnterExitCar(){},addCash(){},AUDIO:{playSFX(){},toggleStation(){}},
});
vm.runInContext(between(html,'        const HUB_PANELS =','        function startMission(')+between(html,'        function openWorldMap()','        // 快速穿梭')+between(html,'        function setupControlsAndEvents()','        // ---------- 靜態物件合併'),context);
context.setupControlsAndEvents();
const gas=document.getElementById('btn-drive-gas'), steer=document.getElementById('btn-steer-left');
for(const [id,key] of [['btn-drive-gas','forward'],['btn-drive-brake','backward'],['btn-steer-left','left'],['btn-steer-right','right'],['btn-drive-nitro','shift'],['btn-drive-drift','space']]){
    const e=document.getElementById(id); e.emit('touchstart');assert.equal(INPUT[key],true);e.emit('touchend');assert.equal(INPUT[key],false);
    e.emit('pointerdown');e.emit('pointercancel');assert.equal(INPUT[key],false);
}
gas.emit('touchstart');steer.emit('touchstart');assert.ok(INPUT.forward&&INPUT.left);
steer.emit('touchend');assert.ok(INPUT.forward&&!INPUT.left);gas.emit('touchend');
for(const event of ['resize','orientationchange','blur']){
    gas.emit('touchstart');steer.emit('touchstart');window.emit(event);
    assert.ok(!INPUT.forward&&!INPUT.left&&!gas.classList.contains('active-press'));
}
gas.emit('touchstart');document.hidden=true;document.emit('visibilitychange');assert.equal(INPUT.forward,false);
document.hidden=false;
gas.emit('touchstart');document.getElementById('radar-container').emit('click');assert.equal(INPUT.forward,false);
assert.equal(document.getElementById('quick-actions').open,true);
document.getElementById('pill-mission').emit('click');assert.equal(document.getElementById('quick-actions').open,true);
assert.equal(document.getElementById('missions-modal').classList.contains('hidden'),false);
document.getElementById('radar-container').emit('click');document.getElementById('quick-actions-map').emit('click');
assert.equal(document.getElementById('world-map').classList.contains('hidden'),false);
console.log('PASS: unchanged binary bindings, simultaneous steering/gas, cancellation/lifecycle cleanup, actions and map entry');
// Switching tabs cancels map work, clears held inputs and retains exactly one active panel.
for (const [tab,panel] of [['pill-mission','missions-modal'],['pill-garage','garage-modal'],['hub-world-tab','hub-world'],['pill-settings','settings-modal']]) {
    gas.emit('touchstart');document.getElementById(tab).click();
    assert.equal(INPUT.forward,false);assert.equal(timers.size,0);assert.equal(context.WMAP.open,false);
    const draws=mapDraws;while(frames.length)frames.shift()();assert.equal(mapDraws,draws,'queued map draw after tab switch');
    for(const id of ['world-map','missions-modal','garage-modal','hub-world','settings-modal'])assert.equal(document.getElementById(id).classList.contains('hidden'),id!==panel);
    assert.equal(document.getElementById(tab)['aria-selected'],'true');
}
for(let i=0;i<3;i++)document.getElementById('quick-actions-map').click();
assert.equal(timers.size,1,'only one map timer');
context.WMAP.pointers.set(7,{});document.getElementById('pill-settings').click();assert.equal(context.WMAP.pointers.size,0);
document.getElementById('quick-actions-list').emit('keydown',{target:document.getElementById('pill-settings'),key:'ArrowRight'});
assert.equal(context.WMAP.open,true);assert.equal(document.getElementById('quick-actions-map').focused,true);
document.getElementById('quick-actions').emit('cancel');
assert.equal(document.getElementById('quick-actions').open,false);assert.equal(timers.size,0);
assert.equal(document.getElementById('radar-container').focused,true);
for(const close of ['quick-actions-close','close-missions-btn','close-garage-btn','close-settings-btn']) {
    document.getElementById('radar-container').click();document.getElementById(close).click();
    assert.equal(timers.size,0);assert.equal(context.WMAP.open,false);
}
// Exercise the actual delivery guard, including a job started during the fade.
let teleports=0;const delayed=[];
context.DELIVERY={job:{}};context.showBanner=()=>{};context.setTimeout=fn=>delayed.push(fn);context.teleportTo=()=>teleports++;
vm.runInContext(between(html,'        function fastTravelTo(','        function setWaypoint('),context);
context.fastTravelTo({x:0,z:0});assert.equal(delayed.length,0);
context.DELIVERY.job=null;context.fastTravelTo({x:0,z:0});context.DELIVERY.job={};delayed.shift()();assert.equal(teleports,0);
assert.match(dialog,/data-mode="STUNT"/);
assert.equal((dialog.match(/data-mode=/g)||[]).length,4);
console.log('PASS: five Hub tabs, map timer lifecycle, queued draw guard, focus/close flow, delivery fast-travel guards, existing STUNT');
console.log('RESULT: PASS (Node structural/event checks; browser layout and device testing still required)');
