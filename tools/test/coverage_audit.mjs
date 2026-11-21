// Run against a commit or the worktree. --details prints every interval and every
// 10x10 center (consecutive x positions on one z row are compressed, step = 2).
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { collisionHarness, html, root, THREE } from './collision_harness.mjs';

const ref = process.argv.indexOf('--base');
const source = ref < 0 ? html : execFileSync('git', ['show', process.argv[ref + 1] + ':index.html'],
    { cwd: root, encoding: 'utf8', maxBuffer: 4e6 });
const details = process.argv.includes('--details');
const names = ['Suburb Main', 'Maple Ave', 'Hillcrest Loop', 'Valley Loop'];
const round = n => Math.round(n * 10) / 10;
const hits = (x,z,half,b,gap=0) => Math.abs(x-b.x)<half+b.w/2+gap && Math.abs(z-b.z)<half+b.d/2+gap;
const points = [[98,22],[110,20],[242,0],[-60,0],[-120,-540],[-1060,-238],[104.8,-100],[-605,555],[220,340],[-420,-200],[-240,-60],[236,-40],[-120,60],[-120,-660],[-480,-240],[-900,-245],[60,720]];
const reserved = [[-60,0,100,200],[-420,-55,40,410],[0,675,22,110],[-115,600,110,22],[-295,-720,110,22],...points.map(([x,z])=>[x,z,24,24])].map(([x,z,w,d])=>({x,z,w,d}));

// Observe the production first-row parcel decisions without changing RNG or placement.
function observeParcels(s) {
    const a=s.indexOf('function buildSuburbParcels'), b=s.indexOf('function buildSuburbMeshes',a);
    let part=s.slice(a,b);
    const slot="(WORLD.frontAudit ??= new Map())";
    const rules=[['if ((ti >= 5','type'],['if (x - ex <','boundary'],['if (nearestTerrainRoadDist','junction'],
        ['if ((ti === 2','type'],['if (!safe ||','slope'],['if (Math.hypot(x + 1060','protected'],['if (TREES.list.some','tree']];
    for(const [anchor,reason] of rules){
        const start=part.indexOf(anchor), end=part.indexOf('return;',start);
        assert.ok(start>=0 && end>start,anchor);
        const label=reason==='slope'?"(!safe ? 'junction' : 'slope')":JSON.stringify(reason);
        part=part.slice(0,end)+"{ observe("+label+"); return; }"+part.slice(end+7);
    }
    part=part.replace('SUBURB_TYPES.forEach((type, ti) => {', `SUBURB_TYPES.forEach((type, ti) => {
      const observe = reason => { if (setback === 28) return; const map=${slot};
      const key=zone+'/'+i+'/'+side; if(!map.has(key))map.set(key,new Set()); map.get(key).add(reason); };`);
    part=part.replace('candidates[ti].push(', "observe('eligible'); candidates[ti].push(");
    if(part.includes('const candidate ='))part=part.replace('candidates[ti].push(candidate);',
        "if(candidate.row===1)(WORLD.auditFrontCandidates ??= []).push(candidate); candidates[ti].push(candidate);");
    return s.slice(0,a)+part+s.slice(b);
}
function frontage(h,zone,side) {
    const road=h.ROAD_NET.suburbRoads[zone], pts=road.pts, runs=[];
    let run, legal=0, maxLegal=0, limit=0;
    for(let i=0;i<pts.length-1;i++){
        const p=pts[i], q=pts[i+1], ds=q.s-p.s, n=Math.max(1,Math.ceil(ds));
        const k=Math.max(4,Math.min(4+5*Math.floor((pts.length-9)/5),4+5*Math.round((i-4)/5)));
        const reasons=h.WORLD.frontAudit.get(zone+'/'+k+'/'+side)??new Set();
        for(let j=0;j<n;j++){
            const t=(j+.5)/n, st=p.s+j*ds/n;
            const x=p.x+t*(q.x-p.x)-side*(p.tz+t*(q.tz-p.tz))*road.half;
            const z=p.z+t*(q.z-p.z)+side*(p.tx+t*(q.tx-p.tx))*road.half;
            const covered=h.WORLD.suburbHouses.some(b=>{
                const dx=x-b.x,dz=z-b.z;
                if(Math.abs(dx)>24||Math.abs(dz)>24)return false;
                const u=Math.max(0,Math.abs(dx*b.c-dz*b.s)-(b.hx-.5));
                const v=Math.max(0,Math.abs(dx*b.s+dz*b.c)-(b.hz-.5));
                return u*u+v*v<=196;
            });
            if(covered){run=null;legal=0;continue;}
            if(!run){run={from:st,to:st,reasons:new Set()};runs.push(run);}
            run.to=st+ds/n;
            if(reasons.has('eligible')){
                const behind=h.WORLD.suburbHouses.some(b=> b.zone===zone && b.k===k+zone*7 && side*((b.z-p.z)*p.tx-(b.x-p.x)*p.tz)>road.half+20);
                run.reasons.add(behind?'second row selected':'quota/cap');
                legal+=ds/n; limit+=ds/n; maxLegal=Math.max(maxLegal,legal);
            }else{
                for(const reason of reasons)if(reason!=='type')run.reasons.add(reason);
                legal=0;
            }
        }
    }
    if(h.WORLD.auditFrontCandidates)assert.ok(maxLegal<=45,names[zone]+' frontage');
    const counts=runs.map(r=>r.to-r.from);
    if(details) for(const r of runs)console.log('RUN',names[zone],side,round(r.from),round(r.to),[...r.reasons].join('/'));
    console.log('FRONT',names[zone],side,'runs',runs.length,'total',round(counts.reduce((a,b)=>a+b,0)),'max',round(Math.max(0,...counts)),'eligibleTotal',round(limit),'eligibleMax',round(maxLegal));
}
function city(h) {
    const n=h.ROAD_NET, old=h.city.map(b=>({...b,w:b.w+4,d:b.d+4})), added=h.WORLD.cityInfill;
    const roadGap=(p,axis,half)=>Math.min(...axis.map(v=>Math.abs(p-v)))-half-5;
    const trees=h.TREES.list.map(t=>({x:t.x,z:t.z,w:4*t.scale,d:4*t.scale}));
    const keys=(b,size)=>size===120?Math.floor((b.x+240)/120)+'/'+Math.floor((b.z+360)/120):Math.floor((b.x+400)/240)+'/'+Math.floor((b.z+720)/240);
    const cells=[120,240].map(s=>new Set(old.map(b=>keys(b,s))));
    const offsets=new Set([-36,-32,-30,-24,-18,-12,-6,0,6,12,18,24,30,32,36]);
    const counts={CBD:{},MID:{},OLD:{}};
    const exactRoad=h.cityRoadEnvelope?.();
    const remaining={CBD:0,MID:0,OLD:0}, buildable={CBD:0,MID:0,OLD:0};
    for(let ix=0;ix<5;ix++)for(let bz=-660;bz<=660;bz+=120){
        const left=n.avenuesX[ix],right=n.avenuesX[ix+1],bx=(left+right)/2, district=h.cityDistrict(bx,bz);
        if((bx===-60&&Math.abs(bz)===60)||(bx<=-180&&bz>=300)||(bx===-510&&bz>-300))continue;
        const near=b=>b.x>=left-45&&b.x<=right+45&&Math.abs(b.z-bz)<=110;
        const original=old.filter(near),fill=added.filter(near),trunks=trees.filter(near);
        for(let z=bz-60;z<=bz+60;z+=2){
            let row;
            for(let x=left;x<=right;x+=2){
                const guard=Math.min(roadGap(x,n.avenuesX,n.avenueHalf),roadGap(z,n.crossZ,n.crossHalf));
                if(guard<3||reserved.some(b=>hits(x,z,5,b,3))||trunks.some(b=>hits(x,z,5,b,3)))continue;
                if(original.some(b=>hits(x,z,5,b))||fill.some(b=>hits(x,z,5,b)))continue;
                if(h.rectHitsElevated(x,z,10,10,3)||h.rectHitsCurvedRoad(x,z,10,10,3.5))continue;
                let reason=[...original,...fill].some(b=>hits(x,z,5,b,4))?'facade gap':guard<10?'street strip':
                    cells.some((set,i)=>!set.has(keys({x,z},[120,240][i])))?'facade cell':
                    !offsets.has(x-bx)||!offsets.has(z-bz)?'unsampled grid':'placement target';
                if(exactRoad){
                    if(exactRoad(x,z,5))reason='continuous road clearance';
                    else {
                        remaining[district]++;
                        const hasSpace=(px,pz,size)=>Math.min(roadGap(px,n.avenuesX,n.avenueHalf),roadGap(pz,n.crossZ,n.crossHalf))+5>=size/2+3 &&
                            !reserved.some(b=>hits(px,pz,size/2,b,3)) && !trunks.some(b=>hits(px,pz,size/2,b,3)) &&
                            !original.some(b=>hits(px,pz,size/2,b,3)) && !fill.some(b=>hits(px,pz,size/2,b,3)) &&
                            !exactRoad(px,pz,size/2);
                        let fit=false;
                        for(const size of [10,8])for(let dx=1-size/2-5;dx<size/2+5&&!fit;dx++)
                            for(let dz=1-size/2-5;dz<size/2+5&&!fit;dz++)fit=hasSpace(x+dx,z+dz,size);
                        if(fit)buildable[district]++;
                        reason=fit?'buildable':'clearance prevents another shell';
                    }
                }
                counts[district][reason]=(counts[district][reason]||0)+1;
                if(details){
                    if(row&&row.end===x-2&&row.reason===reason)row.end=x;
                    else {if(row)console.log('LOT',district,bx,bz,z,row.start,row.end,row.reason);row={start:x,end:x,reason};}
                }
            }
            if(row)console.log('LOT',district,bx,bz,z,row.start,row.end,row.reason);
        }
    }
    if(exactRoad){
        console.log('HARD_EMPTY',JSON.stringify(remaining),'CAN_ADD',JSON.stringify(buildable));
        assert.ok(Object.values(buildable).every(n=>n===0),'legal shell fits a remaining hard-clear rectangle');
    }
    console.log('CITY',JSON.stringify(counts),'placed',JSON.stringify(Object.fromEntries(Object.keys(counts).map(d=>[d,h.city.filter(b=>b.district===d).length+added.filter(b=>b.district===d).length]))));
}
// Sample inside every lawn triangle against makeTerrain's indexed ground faces.
function checkVergeHeight(h, mesh, grid) {
    const {x0,z0,x1,z1}=h.ROAD_NET.suburb;
    const pos=mesh.geometry.attributes.position, idx=mesh.geometry.index;
    const cache=new Map();
    function height(i,j) {
        const key=i+','+j;
        if (!cache.has(key)) cache.set(key,Math.fround(h.terrainHeight(x0+i*grid,z0+j*grid)));
        return cache.get(key);
    }
    let min=Infinity,max=-Infinity;
    for (let k=0;k<idx.count;k+=3) {
        const a=idx.getX(k), b=idx.getX(k+1), c=idx.getX(k+2);
        const mean=get=>(get(a)+get(b)+get(c))/3;
        const gx=(mean(v=>pos.getX(v))-x0)/grid, gz=(mean(v=>pos.getZ(v))-z0)/grid;
        const i=Math.floor(gx), j=Math.floor(gz), u=gx-i, v=gz-j;
        const A=height(i,j), B=height(i+1,j), C=height(i,j+1), D=height(i+1,j+1);
        let ground=0;
        if (i>=0 && j>=0 && i<Math.round((x1-x0)/grid) && j<Math.round((z1-z0)/grid) && Math.max(A,B,C,D)>=.08)
            ground=u+v<=1 ? (1-u-v)*A+u*B+v*C : (1-v)*B+(1-u)*C+(u+v-1)*D;
        const gap=mean(v=>pos.getY(v))-ground;
        min=Math.min(min,gap); max=Math.max(max,gap);
    }
    console.log('VERGE',idx.count/3,'triangle centers; clearance (m)',min,max);
    assert.ok(min>=.039 && max<=.041,'verge must follow the rendered ground');
}

for(const preset of ['PHONE_LOW','DESKTOP_HIGH']){
    console.log('PRESET',preset);
    const h=await collisionHarness(observeParcels(source),preset);
    for(let zone=0;zone<4;zone++)for(const side of [-1,1])frontage(h,zone,side);
    if (h.WORLD.auditFrontCandidates) {
        const houses=h.WORLD.suburbHouses, prior=[];
        for(const b of houses){
            const road=h.ROAD_NET.suburbRoads[b.zone], p=road.pts[b.k-b.zone*7];
            const distance=Math.hypot(b.x-p.x,b.z-p.z)-road.half;
            if(b.row===1)assert.ok(Math.abs(distance-(b.hz-.5)-7)<1e-6);
            else {
                assert.ok(Math.abs(distance-28)<1e-6);
                const front=h.WORLD.auditFrontCandidates.filter(f=>f.zone===b.zone && f.side===b.side && f.k===b.k);
                assert.ok(front.every(f=>prior.some(o=>!h.suburbSeparated(f,o))),'open first row before a rear parcel');
            }
            prior.push(b);
        }
        assert.equal(houses.length,preset==='PHONE_LOW'?210:390);
        const verge=h.WORLD.suburbVerge, normals=verge.geometry.attributes.normal;
        assert.ok(verge.isMesh&&!Array.isArray(verge.material)&&!verge.castShadow);
        for(let i=0;i<normals.count;i++)assert.ok(normals.getY(i)>0,'lawn triangle faces down');
        if (ref<0) checkVergeHeight(h,verge,preset==='PHONE_LOW'?10:8);
        console.log('HOUSES',houses.length,'front',houses.filter(b=>b.row===1).length,'rear',houses.filter(b=>b.row===2).length);
    }
    if(process.argv.includes('--front'))continue;
    h.WORLD.roofs=[];h.WORLD.buildings=[];h.WORLD.cameraBlockers=[];
    h.buildTestCityInfill(h.city,[new THREE.MeshStandardMaterial(),new THREE.MeshStandardMaterial()],[],[]);
    city(h);
}

