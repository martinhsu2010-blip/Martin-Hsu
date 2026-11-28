// Deterministic rendered-callback fixture. Only the clocks, game systems and GPU are simulated.
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {execFileSync} from 'node:child_process';
import {performance} from 'node:perf_hooks';
import {html,root,section} from './collision_harness.mjs';

const BASE='a08531a4e72887c02b6f3977a13428d77930aedc';
const before=execFileSync('git',['show',BASE+':index.html'],{cwd:root,encoding:'utf8',maxBuffer:4e6});
const begin='        // === WE03A2-DIAG BEGIN ===', end='        // === WE03A2-DIAG END ===';
const block=section(html,begin,end);
const core=s=>section(s,'        function createFpsReadout()', '        let lastFrameAt');
const loop=s=>section(s,'        let lastFrameAt','\n        requestAnimationFrame(animate);');
const U='UNAVAILABLE', noop=()=>{};
const originalLoop=loop(before);
const cleanLoop=loop(block).replaceAll(/^            if \(recordFps\) recordFps\.(begin|beforeStep|afterStep|beforeRender)\([^;]*;\n/gm,'')
    .replace("if (recordFps) recordFps.interrupt('pause'); ",'');
assert.equal(cleanLoop,originalLoop,'pacing, physics, rendering and quality control order');
const outside=html.slice(0,html.indexOf(begin))+html.slice(html.indexOf(end)+end.length);
assert.equal(outside.replace(/^.*recordFps\.interrupt\("teleport"\);\n/m,'').trimEnd(),
    (before.slice(0,before.indexOf('        function createFpsReadout()'))+'\n'+before.slice(before.indexOf('    </script>',before.indexOf('        window.__VH = { TREE_COLLIDERS')))).trimEnd());
assert.doesNotMatch(core(block),/\b(?:fetch|setInterval|setTimeout|localStorage|InstancedMesh|WebGLRenderer|chunkRegistry)\b|renderer\.compile\(/);
function fixture(source=block,query='?fps=1',profile='PHONE',cache=['vh-test'],controlled=true) {
    let clock=0, allocated=0, steps=1, output, listener, renders=0, keysRead=0;
    const state={quality:'LOW',resScale:1,fpsCap:0,usePostFX:true,time:0,timeOfDay:12,
        perfCheck:{done:true},resCheck:{elapsed:0,frames:0,good:0}};
    const pos={x:-60,z:0};
    const info={autoReset:true,render:{calls:0,triangles:0},memory:{geometries:8,textures:10},programs:[],
        reset(){this.render.calls=0; this.render.triangles=0;}};
    function pass(n) {
        if(info.autoReset)info.reset();
        info.render.calls+=n;info.render.triangles+=n*8;
    }
    const costs=[1,2,3,4];
    const h={URLSearchParams,structuredClone,PROFILE:profile,STATE:state,location:{search:query},
        performance:{now:()=>clock},window:{caches:true},caches:{keys:async()=>{keysRead++;return cache;}},
        document:{hidden:false,createElement:()=>({style:{}}),body:{appendChild:o=>{output=o;}},
            addEventListener:(name,fn)=>{assert.equal(name,'visibilitychange');listener=fn;}},
        navigator:{serviceWorker:{controller:controlled?{}:null}},renderer:{info,getPixelRatio:()=>h.dpr,render:()=>{renders++;pass(3);clock+=costs[3];}},
        composer:{render:()=>{renders++;pass(3);pass(2);clock+=costs[3];}},scene:{},camera:{},
        WORLD:{vehicles:[]},PLAYER:{updatePlayer:()=>{clock+=costs[2];}},TREES:{uTime:{}},QUALITY_CONFIG:{},
        getActivePosition:()=>pos,requestAnimationFrame:noop,innerWidth:844,innerHeight:390,dpr:1,
        physicsWorld:{contacts:[1,2,3],bodies:[{shapes:[0]},{shapes:[1,2]}],stepnumber:40,
            step(){this.stepnumber+=steps;clock+=costs[1];}},
        updateTrafficPhysics:()=>{clock+=costs[0];},FIXED_TIME_STEP:1/60,lastTime:0};
    for(const m of originalLoop.matchAll(/\b((?:update|draw|recycle|refresh)[A-Z]\w*)\(/g)) h[m[1]]??=noop;
    for(const Type of [Float32Array,Float64Array,Uint32Array]) h[Type.name]=class extends Type {
        constructor(...args){super(...args); if(typeof args[0]==='number')allocated+=this.byteLength;}
    };
    vm.createContext(h);
    vm.runInContext(core(source)+loop(source)+'\nthis.rec=recordFps;this.draw=animate;',h);
    return {h,state,info,pos,costs,frame:t=>{clock=t;h.draw(t);},steps:n=>{steps=n;},
        get output(){return output;},get renders(){return renders;},get bytes(){return allocated;},
        keys:()=>keysRead,visible:(flag,t)=>{clock=t;h.document.hidden=!flag;listener();},
        snapshot:()=>h.rec.api.snapshot(),freeze:()=>{h.rec.interrupt('teleport');return h.rec.api.snapshot().frozenSegments.at(-1);}};
}
function runList(intervals,s=block) {
    const f=fixture(s); let now=10; f.frame(now);
    for(const delta of intervals)f.frame(now+=delta);
    return f.freeze();
}
const intervals=[16,20,30,33,33,40,50,51,100,120];
const rank=(xs,p)=>xs.length?xs.slice().sort((a,b)=>a-b)[Math.ceil(xs.length*p)-1]:U;
function percentiles(s) {
    for(const xs of [[],[42],[19,19,19],intervals,[120,30,16,100,50,33]]) {
        const got=runList(xs,s);
        for(const p of [50,95,99])assert.equal(got['frameP'+p],rank(xs,p/100),'nearest rank');
    }
}
function thresholds(s) {
    const got=runList(intervals,s);
    assert.deepEqual([got.over50,got.over100,got.over50Ratio,got.over100Ratio],[3,1,.3,.1],'strict thresholds');
}
function stall(s) {
    const got=runList([14,3100],s);
    assert.equal(got.sampleCount,2,'stall retained');
    assert.equal(got.longestFrame,3100,'unclamped interval');
    assert.equal(got.foregroundStallCount,1);
}
function cap(s) {
    const f=fixture(s);f.state.fpsCap=30;
    for(const t of [34,38,43,50,67])f.frame(t);
    assert.equal(f.renders,2); assert.equal(f.snapshot().sampleCount,1,'rendered callbacks only');
}
function phases(s) {
    const f=fixture(s); f.frame(1);f.frame(59991);f.pos.x=3;f.state.timeOfDay=13;f.frame(60201);
    const first=f.snapshot();
    assert.equal(first.phase,'WARM_UP','cold isolated');
    assert.equal(first.sampleCount,0);
    assert.deepEqual([first.coldSnapshot.durationMs,first.coldSnapshot.sampleCount],[60200,2]);
    assert.deepEqual([first.coldSnapshot.startTimeOfDay,first.coldSnapshot.endTimeOfDay,first.coldSnapshot.startX,first.coldSnapshot.endX],[12,13,-60,3]);
    assert.equal(first.coldLongFrameEvents.at(-1).interval,210);
    for(let i=1;i<=12;i++)f.frame(60201+60000*i);
    const after=f.snapshot(); assert.equal(after.phase,'MEASURE_12');
    assert.deepEqual(after.coldSnapshot,first.coldSnapshot);
    assert.equal(after.frozenSegments.length,8); assert.equal(after.removedSegments,5);
}
function off(s) {
    const f=fixture(s,'');
    assert.equal(f.h.rec,null,'default off');
    assert.equal(f.output,undefined);assert.equal(f.bytes,0);assert.ok(f.info.autoReset);
    assert.equal(f.keys(),0);f.frame(60);assert.equal(f.renders,1);
}
function counters(s) {
    const f=fixture(s);f.frame(1);f.steps(0);f.frame(1045);
    const d=f.snapshot();
    assert.deepEqual([d.bodies,d.shapes,d.contacts,d.substeps,d.contactsUpdated],[2,3,3,0,false],'Cannon counters');
    assert.equal(d.drawCalls,5,'all render passes');
    assert.equal(d.triangles,40);f.state.usePostFX=false;f.frame(1090);
    assert.equal(f.snapshot().drawCalls,3);
}
function attrib(s) {
    const f=fixture(s); f.frame(10);
    f.costs.splice(0,4,4,6,8,110); f.info.programs.push({name:'Ch03_Body'}); f.info.memory.textures++;
    f.frame(30);const early=f.snapshot().coldLongFrameEvents.at(-1);
    assert.equal(early.interval,null);assert.equal(early.frameSequence,2);assert.equal(early.programName,'Ch03_Body');
    f.costs.fill(1);f.frame(140);const e=f.snapshot().coldLongFrameEvents.at(-1);
    assert.deepEqual([e.interval,e.preCpuMs,e.physicsStepMs,e.updateCpuMs,e.renderSubmissionMs,e.unattributedMs],
        [110,4,6,8,110,-18],'preceding CPU and signed residual');
    assert.deepEqual([e.programDelta,e.textureDelta,e.geometryDelta],[1,1,0]);
}
function overflow(s) {
    const f=fixture(s); f.frame(1);
    for(let i=1;i<=16400;i++)f.frame(1+i*2);
    const d=f.freeze();assert.equal(d.overflow,16,'valid window overflow');
    assert.equal(d.segmentStatus,'INCOMPLETE');assert.equal(d.sampleCount,16400);
    assert.ok(f.bytes<1024*1024-32768,'reserved headroom for rings and 8 summaries');
    const g=fixture(s); g.frame(0);
    for(let i=1;i<=16384;i++)g.frame(i);
    g.frame(80000);assert.equal(g.snapshot().coldSnapshot.overflow,0,'expired slots are not overflow');
}
function viewport(s) {
    const f=fixture(s);f.frame(1);f.h.innerWidth--;f.frame(40);
    assert.equal(f.snapshot().phase,'WARM_UP','viewport interruption');
}
function availability(s) {
    const f=fixture(s);f.frame(1);assert.equal(f.snapshot().gpuTime,U,'GPU unavailable');assert.equal(f.snapshot().gcTime,U);
}
function resets(s) {assert.equal(fixture(s).info.autoReset,false,'diagnostic autoReset');}
for(const check of [percentiles,thresholds,stall,cap,phases,off,counters,attrib,overflow,viewport,availability,resets])check(block);
const f=fixture();f.frame(1); f.frame(1201);
f.visible(false,1220);f.frame(3000);f.visible(true,6400);f.frame(6500);
assert.equal(f.snapshot().hiddenDurationMs,5180);assert.equal(f.snapshot().sampleCount,0);
for(const [obj,key,val] of [[f.h,'dpr',2],[f.state,'quality','MED'],[f.state,'fpsCap',60],
    [f.state,'resScale',.7],[f.h,'innerHeight',420],[f.state,'usePostFX',false]]) {
    const old=f.snapshot().segmentId;obj[key]=val;f.frame(7000+old*200);
    assert.equal(f.snapshot().segmentId,old+1);
}
f.state.pauseRender=true;f.frame(20000);f.state.pauseRender=false;f.frame(25000);
assert.equal(f.snapshot().sampleCount,0);assert.equal(f.snapshot().phase,'WARM_UP');
const dirty=f.snapshot();dirty.frozenSegments.length=0;assert.ok(f.snapshot().frozenSegments.length);
const g=fixture();g.frame(0);g.frame(1300);
for(let i=1;i<50;i++)g.frame(1300+110*i);
assert.equal(g.snapshot().coldLongFrameEvents.length,32);
assert.ok(g.snapshot().coldEventsOverwritten>0);assert.equal(g.freeze().longestFrameEvent.interval,1300);
for(const [keys,controlled,expected] of [[[],true,U],[['vh-A','vh-B'],true,U],[['vh-A'],false,U],[['other','vh-A'],true,'vh-A']]) {
    const f=fixture(block,'?fps=1','PHONE',keys,controlled); await Promise.resolve();await Promise.resolve();
    assert.equal(f.snapshot().cache,expected);assert.equal(f.keys(),1);
}
const presets=Array.from(new Set([...html.matchAll(/(PHONE_LOW|PHONE_MED|TABLET_LOW|TABLET_MED|TABLET_HIGH|DESKTOP_MED|DESKTOP_HIGH|DESKTOP_ULTRA|IGPU_LOW|IGPU_MED|IGPU_HIGH):/g)].map(m=>m[1])));
assert.equal(presets.length,11);
for(const preset of presets) {
    const [profile,quality]=preset.split('_'),f=fixture(block,'?fps=1',profile);
    f.state.quality=quality;f.frame(30);
    assert.equal(f.snapshot().preset,preset);
}
const negative=[
    [percentiles,'Math.ceil(n*p)','Math.floor(n*p)',/nearest rank/],
    [thresholds,'interval>50','interval>=50',/strict thresholds/],
    [stall,'if (interval<=0)','if (interval<=0 || interval>2000)',/stall retained/],
    [stall,'const interval=now-previous','const interval=Math.min(100,now-previous)',/unclamped interval/],
    [cap,'if (elapsed < interval - 1) return;', 'if (elapsed < interval - 1) {recordFps(now);return;}',/rendered callbacks only/],
    [phases,"phase='WARM_UP'; measure=0","phase='COLD'; measure=0",/cold isolated/],
    [off,"get('fps')==='1'","get('fps')!=='0'",/default off/],
    [counters,'physics.shapes=physicsWorld.bodies.reduce((sum,b)=>sum+b.shapes.length,0)','physics.shapes=0',/Cannon counters/],
    [counters,'resources.drawCalls=info.render?.calls??U','resources.drawCalls=0',/all render passes/],
    [availability,'gpuTime:U','gpuTime:0',/GPU unavailable/],
    [overflow,'{overflow++; used--;}','{used--;}',/valid window overflow/],
    [attrib,'advance(now);','cpu.physicsStepMs=t2-t1; advance(now);',/preceding CPU/],
    [resets,'info.autoReset=false','info.autoReset=true',/diagnostic autoReset/],
    [viewport,'signature.viewportWidth!==innerWidth','false',/viewport interruption/]
];
for(const [i,[check,a,b,reason]] of negative.entries()) {
    assert.ok(block.includes(a));assert.throws(()=>check(block.replace(a,b)),e=>e.code==='ERR_ASSERTION' && reason.test(e.message));
    console.log('NC'+String(i+1).padStart(2,'0'),'rejected:',reason.source);
}
// Preserve the original completed-bin FPS readout; an empty bin after a stall counts as zero.
const binsFixture=fixture();
for(let second=0;second<61;second++) {
    const n=second===0?1:second%3+5;
    for(let i=0;i<n;i++)binsFixture.frame(second*1000+i*1000/n);
}
binsFixture.frame(61000);
assert.equal(binsFixture.snapshot().rollingAverageFps,6);
assert.match(binsFixture.output.textContent,/60s 6\.0 Low FPS 5/);
assert.equal(binsFixture.snapshot().lowest1sFps,5);
binsFixture.frame(65001);assert.equal(binsFixture.snapshot().lowest1sFps,0);

const bench=fixture(),t=performance.now();
bench.h.performance.now=()=>performance.now();
for(let i=0;i<10000;i++)bench.frame(i*4);
console.log('Headless test harness, 10,000 simulated callbacks, mean ms including fixture and statistics:',((performance.now()-t)/10000).toFixed(4));
const timing=bench.snapshot();
assert.ok(timing.samplingMeanMs>0 && timing.sortedSamples>0);
console.log('Headless diagnostic self-time ms/frame',timing.samplingMeanMs.toFixed(4),
    '1 Hz update ms',timing.statsUpdateMs.toFixed(4),'sorted samples',timing.sortedSamples);
console.log('RESULT: PASS (synthetic rendered intervals, negative controls, 11 presets; device evidence pending)');
