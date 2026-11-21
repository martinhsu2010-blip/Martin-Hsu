// T-008 regression test: extracts and executes the REAL production renderDrivingHUD()
// and ZONE_ARRIVAL / updateZoneArrival() helper from index.html inside a controlled
// Node vm harness (DOM, fake clock, state, spies). No browser layout or device FPS claims.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const root = new URL('../../', import.meta.url);
const htmlPath = process.argv[2] ? new URL(process.argv[2], `file://${process.cwd()}/`) : new URL('index.html', root);
const html = fs.readFileSync(htmlPath, 'utf8');

function between(source, start, end) {
    const a = source.indexOf(start);
    assert.ok(a >= 0, `Missing marker: ${start}`);
    const b = source.indexOf(end, a);
    assert.ok(b > a, `Missing end marker: ${end}`);
    return source.slice(a, b);
}

// 1. Verify exact i18n key and existing 11 zone keys in STRINGS.
const tableMatch = html.match(/\/\/ I18N_TABLE_START\s*const STRINGS = ([\s\S]*?);\s*\/\/ I18N_TABLE_END/);
assert.ok(tableMatch, 'Missing STRINGS table');
const STRINGS = JSON.parse(tableMatch[1]);
assert.equal(STRINGS.en.zone_arrival_label, 'NOW ENTERING', 'STRINGS.en.zone_arrival_label mismatch');
assert.equal(STRINGS['zh-TW'].zone_arrival_label, '正在進入', 'STRINGS["zh-TW"].zone_arrival_label mismatch');

const ZONE_KEYS = [
    'midtown', 'ring_expressway', 'mount_chiliad', 'suburbs', 'old_town',
    'downtown_cbd', 'vice_circle', 'starlight_marina', 'santa_cruz_boardwalk',
    'ocean_drive', 'stunt_airport',
];
for (const key of ZONE_KEYS) {
    assert.ok(STRINGS.en[key] && STRINGS['zh-TW'][key], `Missing existing zone key: ${key}`);
}

// 2. Verify DOM structure in real index.html (#zone-arrival inside #game-hud, non-interactive, initially hidden).
const gameHud = between(html, '<div id="game-hud"', '<dialog id="quick-actions"');
assert.equal((html.match(/id="zone-arrival"/g) || []).length, 1, 'Expected exactly one #zone-arrival');
assert.equal((html.match(/id="zone-arrival-caption"/g) || []).length, 1, 'Expected exactly one #zone-arrival-caption');
assert.equal((html.match(/id="zone-arrival-name"/g) || []).length, 1, 'Expected exactly one #zone-arrival-name');
assert.ok(gameHud.includes('id="zone-arrival"'), '#zone-arrival must live inside #game-hud');

const zoneBlockMatch = gameHud.match(/<div id="zone-arrival"[^>]*>[\s\S]*?<\/div>\s*<!-- 右上/);
assert.ok(zoneBlockMatch, 'Missing #zone-arrival markup block');
const zoneBlock = zoneBlockMatch[0];
assert.match(zoneBlock, /<div id="zone-arrival"[^>]*class="[^"]*\bhidden\b[^"]*"/, '#zone-arrival must start hidden');
assert.match(zoneBlock, /<div id="zone-arrival"[^>]*class="[^"]*\bpointer-events-none\b[^"]*"/, '#zone-arrival must be pointer-events-none');
assert.match(zoneBlock, /role="status"/, '#zone-arrival must have role="status"');
assert.match(zoneBlock, /aria-live="polite"/, '#zone-arrival must have aria-live="polite"');
assert.doesNotMatch(zoneBlock, /<(?:button|a|input|select|textarea)\b/i, '#zone-arrival must be non-interactive');

// 3. Extract real production renderDrivingHUD() and updateZoneArrival() helper from index.html.
const hudSlice = between(html, '        function renderDrivingHUD()', '        // ==================== 賺錢玩法：');
assert.ok(hudSlice.includes('function renderDrivingHUD()'), 'Missing renderDrivingHUD()');
assert.ok(hudSlice.includes('function updateZoneArrival('), 'Missing updateZoneArrival() helper');

const helperSrc = hudSlice.slice(hudSlice.indexOf('const ZONE_ARRIVAL'));
for (const forbidden of ['showBanner', 'localStorage', 'sessionStorage', 'indexedDB', 'cookie', 'saveGame', 'saveSettings', 'startMission', 'teleportTo', 'setInterval', 'requestAnimationFrame', 'fetch(', 'THREE', 'CANNON', 'waypoint']) {
    assert.ok(!helperSrc.includes(forbidden), `Zone arrival helper must not reference forbidden API/system: ${forbidden}`);
}

// 4. Controlled DOM / Fake Clock / State VM harness running REAL production code.
class StubElement {
    constructor(id, initClasses = []) {
        this.id = id;
        this._text = '';
        this.textWrites = 0;
        this.style = {};
        const set = new Set(initClasses);
        this.classList = {
            add: (...xs) => xs.forEach(v => set.add(v)),
            remove: (...xs) => xs.forEach(v => set.delete(v)),
            contains: v => set.has(v),
            toggle: (v, f) => { const on = f === undefined ? !set.has(v) : Boolean(f); if (on) set.add(v); else set.delete(v); return on; },
        };
    }
    get textContent() { return this._text; }
    set textContent(v) { this._text = String(v); this.textWrites++; }
}

const elements = new Map();
const getEl = id => {
    if (!elements.has(id)) {
        elements.set(id, new StubElement(id, id === 'zone-arrival' ? ['hidden'] : []));
    }
    return elements.get(id);
};

// Fake deterministic clock.
let nowMs = 0;
let nextTimerId = 1;
let timersCreated = 0;
let timersCleared = 0;
let maxConcurrentTimers = 0;
const activeTimers = new Map();

function fakeSetTimeout(fn, delay) {
    const id = nextTimerId++;
    timersCreated++;
    activeTimers.set(id, { fn, due: nowMs + Number(delay) });
    if (activeTimers.size > maxConcurrentTimers) maxConcurrentTimers = activeTimers.size;
    return id;
}
function fakeClearTimeout(id) {
    if (activeTimers.delete(id)) timersCleared++;
}
function advanceClock(ms) {
    const target = nowMs + ms;
    while (true) {
        let nextId = null, nextDue = Infinity;
        for (const [id, entry] of activeTimers.entries()) {
            if (entry.due <= target && entry.due < nextDue) {
                nextDue = entry.due;
                nextId = id;
            }
        }
        if (nextId === null) break;
        const entry = activeTimers.get(nextId);
        activeTimers.delete(nextId);
        nowMs = entry.due;
        entry.fn();
    }
    nowMs = target;
}

const sideEffects = [];
const spy = name => (...args) => { sideEffects.push(`${name}(${args.length})`); throw new Error(`Forbidden call: ${name}`); };

let lang = 'en';
let pos = { x: -200, y: 0, z: 0 }; // Downtown CBD
let speed = 0;
const state = {
    mode: 'FOOT',
    nearestVehicle: null,
    currentVehicle: null,
    waypoint: null,
};

const context = vm.createContext({
    document: { getElementById: getEl },
    Math,
    Number,
    String,
    console,
    setTimeout: fakeSetTimeout,
    clearTimeout: fakeClearTimeout,
    setInterval: spy('setInterval'),
    requestAnimationFrame: spy('requestAnimationFrame'),
    fetch: spy('fetch'),
    showBanner: spy('showBanner'),
    saveGame: spy('saveGame'),
    saveSettings: spy('saveSettings'),
    startMission: spy('startMission'),
    teleportTo: spy('teleportTo'),
    localStorage: { getItem: spy('localStorage.getItem'), setItem: spy('localStorage.setItem') },
    sessionStorage: { getItem: spy('sessionStorage.getItem'), setItem: spy('sessionStorage.setItem') },
    tr: key => {
        const val = STRINGS[lang][key];
        assert.ok(val !== undefined, `Missing i18n key in ${lang}: ${key}`);
        return val;
    },
    getActivePosition: () => pos,
    getActiveSpeed: () => speed,
    nearestOnPolyline: () => ({ d: 9999 }),
    WORLD: { vehicles: [] },
    STATE: state,
    ROAD_NET: {
        hill: { x0: -910, x1: -330, z0: 310, z1: 810 },
        suburb: { x0: -1600, x1: -650, z0: -1020, z1: 270 },
        roundabouts: [{ x: -240, z: 0 }],
        ring: { pts: [{ x: 0, z: 0 }], half: 6 },
        spurs: [],
    },
});

vm.runInContext(hudSlice, context);

const zoneEl = getEl('zone-arrival');
const captionEl = getEl('zone-arrival-caption');
const nameEl = getEl('zone-arrival-name');
const radarZoneEl = getEl('radar-zone');
const speedEl = getEl('hud-speed');
const gearEl = getEl('hud-gear');

// A3/A4: Initial HUD update at Downtown CBD (-200, 0, 0) must NOT show notice.
context.renderDrivingHUD();
assert.equal(radarZoneEl.textContent, 'Downtown CBD');
assert.equal(zoneEl.classList.contains('hidden'), true, 'Initial HUD update must not show #zone-arrival');
assert.equal(timersCreated, 0, 'Initial HUD update must not schedule timer');
assert.equal(speedEl.textContent, '0');
assert.equal(gearEl.textContent, STRINGS.en.label_foot);
assert.equal(state.mode, 'FOOT');

// A4/A5: Transition Downtown CBD -> Ocean Drive (130, 0, 0) shows notice immediately.
pos = { x: 130, y: 0, z: 0 };
context.renderDrivingHUD();
assert.equal(radarZoneEl.textContent, 'Ocean Drive');
assert.equal(zoneEl.classList.contains('hidden'), false, 'Zone change must reveal #zone-arrival');
assert.equal(captionEl.textContent, 'NOW ENTERING');
assert.equal(nameEl.textContent, 'Ocean Drive');
assert.equal(timersCreated, 1);
assert.equal(activeTimers.size, 1);

// A5: 300 unchanged frames in Ocean Drive must NOT add timers or rewrite DOM text.
const captionWritesBefore = captionEl.textWrites;
const nameWritesBefore = nameEl.textWrites;
for (let i = 0; i < 300; i++) context.renderDrivingHUD();
assert.equal(timersCreated, 1, '300 unchanged frames must not create extra timers');
assert.equal(activeTimers.size, 1);
assert.equal(captionEl.textWrites, captionWritesBefore, 'Unchanged frames must not rewrite caption DOM');
assert.equal(nameEl.textWrites, nameWritesBefore, 'Unchanged frames must not rewrite name DOM');

// A5: Exact 2499 ms visible / 2500 ms hidden boundary.
advanceClock(2499);
assert.equal(zoneEl.classList.contains('hidden'), false, 'Notice must remain visible at 2499 ms');
assert.equal(activeTimers.size, 1);
advanceClock(1);
assert.equal(zoneEl.classList.contains('hidden'), true, 'Notice must hide at exactly 2500 ms');
assert.equal(activeTimers.size, 0);
assert.equal(radarZoneEl.textContent, 'Ocean Drive');

// Unchanged frames while hidden + language switch while hidden must NOT re-show notice.
for (let i = 0; i < 300; i++) context.renderDrivingHUD();
assert.equal(zoneEl.classList.contains('hidden'), true);
assert.equal(timersCreated, 1);
lang = 'zh-TW';
context.renderDrivingHUD();
assert.equal(radarZoneEl.textContent, '海濱大道');
assert.equal(zoneEl.classList.contains('hidden'), true, 'Language switch must not re-show hidden notice');
assert.equal(timersCreated, 1);
lang = 'en';
context.renderDrivingHUD();
assert.equal(radarZoneEl.textContent, 'Ocean Drive');
assert.equal(zoneEl.classList.contains('hidden'), true);

// A4/A5/A7: Rapid B -> C transition (Suburbs -> Old Town) cancels stale timer and preserves car speed/gear.
pos = { x: -1060, y: 0, z: -238 }; // Suburbs
context.renderDrivingHUD();
assert.equal(radarZoneEl.textContent, 'Suburbs');
assert.equal(zoneEl.classList.contains('hidden'), false);
assert.equal(nameEl.textContent, 'Suburbs');
assert.equal(activeTimers.size, 1);
const timersAfterSuburbs = timersCreated;

advanceClock(1500); // 1000 ms left on Suburbs timer
state.mode = 'CAR';
state.currentVehicle = { currentGear: 3, rpm: 4200, nitro: 80 };
speed = 20; // 72 km/h
pos = { x: 0, y: 0, z: -500 }; // Old Town
context.renderDrivingHUD();
assert.equal(radarZoneEl.textContent, 'Old Town');
assert.equal(speedEl.textContent, '72');
assert.equal(gearEl.textContent, 'G3');
assert.equal(zoneEl.classList.contains('hidden'), false);
assert.equal(nameEl.textContent, 'Old Town');
assert.equal(timersCreated, timersAfterSuburbs + 1);
assert.equal(timersCleared, 1, 'Rapid B->C transition must cancel stale B timer');
assert.equal(activeTimers.size, 1, 'Only one active hide timer may exist');
assert.equal(maxConcurrentTimers, 1, 'Never more than one active timer concurrently');

// Advance past when Suburbs timer would have fired (t + 1000 ms): Old Town must STILL be visible.
advanceClock(1000);
assert.equal(zoneEl.classList.contains('hidden'), false, 'Stale Suburbs timer must not hide Old Town early');
advanceClock(1499); // 2499 ms since entering Old Town
assert.equal(zoneEl.classList.contains('hidden'), false, 'Old Town notice must stay visible at 2499 ms');
advanceClock(1); // 2500 ms since entering Old Town
assert.equal(zoneEl.classList.contains('hidden'), true, 'Old Town notice must hide at 2500 ms');
assert.equal(activeTimers.size, 0);

// A6: Language switch en -> zh-TW -> en while visible updates wording without restarting timer.
pos = { x: 130, y: 0, z: 0 }; // Ocean Drive
context.renderDrivingHUD();
assert.equal(zoneEl.classList.contains('hidden'), false);
assert.equal(captionEl.textContent, 'NOW ENTERING');
assert.equal(nameEl.textContent, 'Ocean Drive');
const timersBeforeLangSwitch = timersCreated;

advanceClock(1000);
lang = 'zh-TW';
context.renderDrivingHUD();
assert.equal(zoneEl.classList.contains('hidden'), false);
assert.equal(captionEl.textContent, '正在進入');
assert.equal(nameEl.textContent, '海濱大道');
assert.equal(radarZoneEl.textContent, '海濱大道');
assert.equal(timersCreated, timersBeforeLangSwitch, 'Language switch must not create a new timer');

advanceClock(500);
lang = 'en';
context.renderDrivingHUD();
assert.equal(captionEl.textContent, 'NOW ENTERING');
assert.equal(nameEl.textContent, 'Ocean Drive');
assert.equal(timersCreated, timersBeforeLangSwitch, 'Switching back to en must not create a new timer');

advanceClock(999); // 2499 ms from original Ocean Drive entry
assert.equal(zoneEl.classList.contains('hidden'), false, 'Notice must remain visible until original 2500 ms expires');
advanceClock(1); // 2500 ms from original Ocean Drive entry
assert.equal(zoneEl.classList.contains('hidden'), true, 'Notice must hide at original 2500 ms deadline');
assert.equal(activeTimers.size, 0);

assert.equal(sideEffects.length, 0, `Unexpected forbidden side effects: ${sideEffects.join(', ')}`);

console.log('PASS: #zone-arrival markup, zone_arrival_label i18n, and real renderDrivingHUD() extracted from index.html');
console.log('PASS: initial suppression, coordinate transitions (Downtown CBD -> Ocean Drive -> Suburbs -> Old Town), 300 unchanged frames (0 extra timers/DOM writes)');
console.log('PASS: exact 2499 ms visible / 2500 ms hidden, rapid B->C cancels stale timer (max 1 active), live en <-> zh-TW without timer reset, unchanged speed/gear/#radar-zone');
console.log('RESULT: PASS (Node vm regression check on real production renderDrivingHUD(); browser layout and real-device checks remain separate)');
