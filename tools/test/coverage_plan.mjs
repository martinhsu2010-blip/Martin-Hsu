// Offline planner for the two static city layouts. Run from the repo root:
// node tools/test/coverage_plan.mjs > /tmp/city-layout.js
// The planner runs inside the same block context and hard-rule checks as the game.
import { collisionHarness, html } from './collision_harness.mjs';

function planBlock() {
    const land = [];
    for (let z=bz-60;z<=bz+60;z+=2) for (let x=left;x<=right;x+=2) {
        if (!hard(x,z,8)) continue;
        const roadGap=Math.min(x-left-net.avenueHalf,right-x-net.avenueHalf,60-Math.abs(z-bz)-net.crossHalf);
        land.push({x,z,roadGap,ten:hard(x,z,10)});
    }
    // Keep each previous pass. A smaller footprint or a narrower tree-free
    // sidewalk may only fill space left by the preceding relaxation.
    // Each available 10x10 rectangle is a goal; adjacent centers can describe
    // the same empty lot. Prefer goals with the fewest possible placements.
    const goals=land.filter(p=>p.ten && occupied.every(b=>clear(p.x,p.z,10,10,b,0)));
    const stride=right-left+1;
    const key=(x,z)=>(z-bz+60)*stride+x-left;
    const grid=new Map(goals.map(g=>[key(g.x,g.z),g]));
    for (const site of land) {
        site.covers=[];
        // At 2-unit grid resolution both shell sizes intersect centers
        // at offsets -8..8 on each axis (touching only is still empty).
        for(let dz=-8;dz<=8;dz+=2) for(let dx=-8;dx<=8;dx+=2) {
            if(site.x+dx<left || site.x+dx>right) continue;
            const g=grid.get(key(site.x+dx,site.z+dz));
            if(g)site.covers.push(g);
        }
    }
    const record=stats[district], movable=new Set();
    record.passes ??= [0,0,0]; record.emptyAfter ??= [0,0,0];
    for (const [step,sizes,strip] of [[0,[10],10],[1,[8],10],[2,[10,8],3]]) {
        for (const size of sizes) {
            for(const g of goals)g.options=[];
            const candidates=land.filter(s=>(size===8 || s.ten) && s.roadGap>=size/2+strip &&
                occupied.every(b=>clear(s.x,s.z,size,size,b,3)));
            for(const s of candidates) {
                s.blocked=false;
                for(const g of s.covers)if(!g.covered)g.options.push(s);
            }
            const pending=goals.filter(g=>!g.covered && g.options.length).sort((a,b)=>a.options.length-b.options.length);
            for (const g of pending) {
                if(g.covered)continue;
                let best,score=0;
                for(const s of g.options) {
                    if(s.blocked)continue;
                    let gain=0;
                    for(const target of s.covers)if(!target.covered)gain+=1/target.options.length;
                    if(gain>score){best=s;score=gain;}
                }
                if(!best)continue;
                const parcel={x:best.x,z:best.z,w:size,d:size,h:height,district,infill:true,coverage:true};
                added.push(parcel); occupied.push(parcel); movable.add(parcel); record.passes[step]++;
                for(const target of best.covers)target.covered=true;
                for(const s of candidates)if(!clear(s.x,s.z,size,size,parcel,3))s.blocked=true;
            }
        }
        record.emptyAfter[step]+=goals.filter(g=>!g.covered).length;
    }
    // A grid centered on even coordinates misses lots with only one unit
    // of latitude. Repair residual holes at half-grid offsets, moving only a
    // newly placed shell and only when the total number of holes goes down.
    function coveredBy(x,z,size) {
        const result=[], reach=5+size/2;
        for(let gz=Math.ceil((z-reach+.01)/2)*2;gz<z+reach;gz+=2)
            for(let gx=Math.ceil((x-reach+.01)/2)*2;gx<x+reach;gx+=2) {
                if(gx<left || gx>right)continue;
                const g=grid.get(key(gx,gz)); if(g)result.push(g);
            }
        return result;
    }
    for(const g of goals)g.count=0;
    for(const b of movable) for(const g of coveredBy(b.x,b.z,b.w))g.count++;
    let improved;
    do {
        improved=false;
        for (const g of goals) {
            if(g.count)continue;
            let choice, bestGain=0;
            const near=occupied.filter(b=>Math.abs(b.x-g.x)<b.w/2+18 && Math.abs(b.z-g.z)<b.d/2+18);
            for (const size of [10,8]) for(let z=g.z-8;z<=g.z+8;z++) for(let x=g.x-8;x<=g.x+8;x++) {
                let move=null, blocked=false;
                for(const b of near)if(!clear(x,z,size,size,b,3)) {
                    if(move || !movable.has(b)){blocked=true;break;}
                    move=b;
                }
                if(blocked || !hard(x,z,size))continue;
                const cover=coveredBy(x,z,size);
                const lost=move ? coveredBy(move.x,move.z,move.w) : [];
                const gain=cover.filter(v=>!v.count).length-lost.filter(v=>v.count===1&&!cover.includes(v)).length;
                if(gain>bestGain){choice={x,z,size,move,cover,lost};bestGain=gain;}
            }
            if (!choice)continue;
            const {x,z,size,move,cover,lost}=choice;
            const parcel=move ?? {h:height,district,infill:true,coverage:true};
            if(!move){added.push(parcel);occupied.push(parcel);movable.add(parcel);record.passes[2]++;}
            Object.assign(parcel,{x,z,w:size,d:size});
            for(const v of lost)v.count--;
            for(const v of cover)v.count++;
            improved=true;
        }
    } while(improved);
    record.emptyAfter[2]+=goals.filter(g=>!g.count).length-goals.filter(g=>!g.covered).length;
}

const fn = planBlock.toString();
const injected = fn.slice(fn.indexOf('{')+1, fn.lastIndexOf('}'));
const source = html.replace(/ +\/\/ BEGIN compiled city lots[\s\S]*?\/\/ END compiled city lots/, () => injected);
if (source === html) throw new Error('Missing city lot planner boundary');
console.log('        const CITY_COVERAGE_LOTS = {');
for (const [profile,preset] of [['mobile','PHONE_LOW'],['desktop','DESKTOP_HIGH']]) {
    const h=await collisionHarness(source,preset);
    const lots=h.cityInfillParcels(h.city).filter(b=>b.coverage);
    console.error(preset,JSON.stringify(h.WORLD.cityInfillStats));
    const blocks=new Map();
    for (const b of lots) {
        const ix=h.ROAD_NET.avenuesX.findIndex((x,i,xs)=>x<b.x && xs[i+1]>b.x);
        const bz=Math.floor(b.z/120)*120+60;
        const key=ix+'/'+bz;
        if(!blocks.has(key))blocks.set(key,[]);
        blocks.get(key).push([b.x,b.z,b.w]);
    }
    console.log('            '+profile+': {');
    for(const [key,rows] of blocks) console.log('                '+JSON.stringify(key)+': '+JSON.stringify(rows)+',');
    console.log('            },');
}
console.log('        };');
