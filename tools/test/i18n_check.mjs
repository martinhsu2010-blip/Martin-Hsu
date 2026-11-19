// Exercise the actual locale runtime, save initialization and live-refresh functions.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const html=fs.readFileSync(new URL('../../index.html',import.meta.url),'utf8');
const runtime=html.match(/<script>\s*\/\/ I18N_TABLE_START([\s\S]*?)<\/script>/)[1];
const table=JSON.parse(html.match(/const STRINGS = ([\s\S]*?);\s*\/\/ I18N_TABLE_END/)[1]);
function between(start,end){const a=html.indexOf(start),b=html.indexOf(end,a);assert.ok(a>=0&&b>a);return html.slice(a,b);}
function harness(raw,{readError=false,writeError=false}={}){
    const elements=new Map(),stored=new Map();if(raw!==null)stored.set('vh_save',raw);
    const element=id=>{if(!elements.has(id))elements.set(id,{id,dataset:{},style:{},value:'',textContent:'',classList:{add(){},remove(){}},setAttribute(k,v){this[k]=v;},getAttribute(k){return this[k];}});return elements.get(id);};
    const staticLabel=element('static-label');staticLabel.dataset.i18n='missions';
    const aria=element('aria');aria['data-i18n-aria-label']='open_game_hub';
    const chip=element('map-chip');chip.dataset.mapLocation='OCEAN';
    const document={documentElement:{lang:''},getElementById:element,addEventListener(){},
        querySelector:s=>element(s),querySelectorAll:s=>s==='[data-i18n]'?[staticLabel]:s==='[data-i18n-aria-label]'?[aria]:s==='[data-map-location]'?[chip]:[]};
    const context=vm.createContext({document,console,Math,Number,Date,Map,JSON,
        localStorage:{getItem(k){if(readError)throw Error('unavailable');return stored.get(k)??null;},setItem(k,v){if(writeError)throw Error('quota');stored.set(k,v);}},
        setTimeout(){return 1;},clearTimeout(){},
        STATE:{cash:12345,upgradeLevel:3,mode:'FOOT',quality:'MED'},
        GPU_NAME:'GPU',PROFILE:'TABLET',
        WORLD:{vehicles:[{name:table['zh-TW'].sedan}]},STUNT:{jumps:[{name:table['zh-TW'].downtown_plaza_ramp}]},ROAD_NET:{ribbons:[],terrainRoads:[]},
        KENNEY_TYPES:[['sedan',6,table['zh-TW'].sedan]],
        DELIVERY:{job:null},MISSION:{active:false,mode:'DRIFT',score:300},WMAP:{open:false,sel:null},
        getActivePosition:()=>({x:0,z:0}),renderDrivingHUD(){},updateSkyLabel(){},drawWorldMap(){},wmSelect(){},
        AUDIO:{stations:['OFF'],stationIndex:0}
    });
    vm.runInContext(runtime+'\nthis.i18n=VH_I18N;'+between('        const SAVE =','        const STATE =')+'\nthis.save=SAVE;'+between('        let bannerText =','        function addCash(')+between('        let refreshGarageLabels =','        const HUB_PANELS ='),context);
    // A real location getter ensures chips and map selection re-read the active language.
    vm.runInContext("const FAST_TRAVEL=[{id:'OCEAN',get name(){return tr('ocean_drive');}}];",context);
    return {context,stored,element};
}
const seed={cash:12345,owned:['lexuslc500'],jumps:{DT:50},deliveries:7,upgrade:3,collectedCrates:[0],rewardCooldowns:{airborne:Date.now()+50000},customField:'preserve'};
for(const [raw,expected] of [[null,'en'],[JSON.stringify(seed),'zh-TW'],[JSON.stringify({...seed,language:'en'}),'en'],[JSON.stringify({...seed,language:'zh-TW'}),'zh-TW'],[JSON.stringify({...seed,language:'xx'}),'zh-TW'],['broken JSON','zh-TW'],['null','zh-TW'],['[]','zh-TW']]){
    const {context,stored}=harness(raw);assert.equal(context.i18n.language,expected);assert.equal(context.save.language,expected);
    assert.equal(stored.get('vh_save')??null,raw,'initial read must not overwrite the save');
}
assert.equal(harness(null,{readError:true}).context.i18n.language,'en');
const {context,stored,element}=harness(JSON.stringify(seed));
for(const language of ['en','zh-TW','en']){
    context.changeLanguage(language);
    assert.equal(context.i18n.language,language);assert.equal(context.document.documentElement.lang,language);
    assert.equal(element('language-select').value,language);
    assert.equal(element('static-label').textContent,table[language].missions);
    assert.equal(element('aria')['aria-label'],table[language].open_game_hub);
    assert.equal(element('map-chip').textContent,table[language].ocean_drive);
    assert.equal(context.WORLD.vehicles[0].name,table[language].sedan);
    assert.equal(context.STUNT.jumps[0].name,table[language].downtown_plaza_ramp);
    const saved=JSON.parse(stored.get('vh_save'));assert.deepEqual(saved,{...seed,language});
    assert.equal(harness(stored.get('vh_save')).context.i18n.language,language,'reload retains choice');
}
context.changeLanguage('bogus');assert.equal(context.i18n.language,'en');
assert.doesNotThrow(()=>harness(JSON.stringify(seed),{writeError:true}).context.changeLanguage('en'));
// Switching an active notification must not restart its lifetime or trigger gameplay.
vm.runInContext("showBanner(() => tr('delivery_complete') + '1200', () => tr('delivered_on_time'));",context);
context.changeLanguage('zh-TW');assert.equal(element('banner-title').textContent,table['zh-TW'].delivery_complete+'1200');
context.changeLanguage('en');assert.equal(element('banner-sub').textContent,table.en.delivered_on_time);
context.MISSION.active=true;context.changeLanguage('zh-TW');assert.equal(context.MISSION.score,300);
assert.ok(element('mission-progress').textContent.includes(table['zh-TW'].label_pts));
context.DELIVERY.job={left:-61,limit:90,reward:1000,dest:{x:0,z:0,name:table.en.ocean_drive}};
context.changeLanguage('en');assert.equal(context.DELIVERY.job.left,-61);assert.equal(context.DELIVERY.job.reward,1000);
assert.equal(element('mission-timer').textContent,'Late +1:01');assert.equal(element('mission-progress').textContent,table.en.enter_a_vehicle_to_unload);
context.changeLanguage('zh-TW');assert.equal(context.DELIVERY.job.dest.name,table['zh-TW'].ocean_drive);
assert.equal(element('mission-timer').textContent,table['zh-TW'].late+'1:01');
// Navigation notifications must outlive cleared gameplay references safely.
context.STATE.waypoint={x:0,z:0,name:table.en.ocean_drive};
context.clearWaypoint=()=>{context.STATE.waypoint=null;};
vm.runInContext(between('        function updateWaypoint()', '        function setupWorldMap()'),context);
context.updateWaypoint();assert.equal(context.STATE.waypoint,null);
context.changeLanguage('en');assert.equal(element('banner-sub').textContent,table.en.ocean_drive);
context.changeLanguage('zh-TW');assert.equal(element('banner-sub').textContent,table['zh-TW'].ocean_drive);
// Stable game IDs remain literals, regardless of language; enum values are not translated.
assert.match(html, /id: 'OCEAN', get name/);
assert.doesNotMatch(html, /(?:id|mode|archetype|type): tr\(/);
for(const lang of ['en','zh-TW'])for(const key of ['quality_LOW','quality_MED','quality_HIGH','quality_ULTRA','device_PHONE','device_TABLET','device_DESKTOP','device_IGPU'])assert.ok(table[lang][key]);
console.log('RESULT: PASS (new/old/invalid/blocked saves, persistence, live labels/aria/map/banner/mission/delivery; no browser/device claims)');
