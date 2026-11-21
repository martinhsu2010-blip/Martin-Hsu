// T-007 regression test: exercises the real WORLD "Next Stop" HTML, i18n table,
// and setupExplorePicks() handler extracted from index.html.
// No browser layout or real-device FPS claims.
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

// 1. Verify exact 7 new bilingual keys and 4 reused destination keys in STRINGS.
const i18nScript = html.match(/<script>\s*\/\/ I18N_TABLE_START([\s\S]*?)<\/script>/);
assert.ok(i18nScript, 'Missing I18N script block');
const tableMatch = html.match(/\/\/ I18N_TABLE_START\s*const STRINGS = ([\s\S]*?);\s*\/\/ I18N_TABLE_END/);
assert.ok(tableMatch, 'Missing STRINGS table');
const STRINGS = JSON.parse(tableMatch[1]);

const EXPECTED_NEW_KEYS = {
    explore_picks_heading: ['🧭 Next Stop', '🧭 下一站靈感'],
    explore_picks_note: ['Just an idea; no waypoint or mission is started.', '純探索建議；不會設定導航或開始任務。'],
    explore_picks_next: ['Next idea', '換個地點'],
    explore_tip_ocean: ['Cruise along the palm-lined coast at dusk.', '沿著棕櫚樹林立的海岸大道欣賞黃昏。'],
    explore_tip_marina: ['Visit the marina for a relaxed waterfront drive.', '前往遊艇碼頭，沿著水岸輕鬆兜風。'],
    explore_tip_chiliad: ['Follow the winding mountain road toward the summit.', '沿著蜿蜒山路往山頂前進。'],
    explore_tip_ring: ['Try one complete lap of the elevated ring road.', '試著沿高架環線完整兜風一圈。'],
};
for (const [key, [enVal, zhVal]] of Object.entries(EXPECTED_NEW_KEYS)) {
    assert.equal(STRINGS.en[key], enVal, `STRINGS.en.${key} mismatch`);
    assert.equal(STRINGS['zh-TW'][key], zhVal, `STRINGS['zh-TW'].${key} mismatch`);
}

const EXPECTED_CARDS = [
    { index: 0, titleKey: 'ocean_drive', tipKey: 'explore_tip_ocean', step: '1 / 4' },
    { index: 1, titleKey: 'starlight_marina', tipKey: 'explore_tip_marina', step: '2 / 4' },
    { index: 2, titleKey: 'mount_chiliad_summit', tipKey: 'explore_tip_chiliad', step: '3 / 4' },
    { index: 3, titleKey: 'ring_expressway', tipKey: 'explore_tip_ring', step: '4 / 4' },
];
for (const card of EXPECTED_CARDS) {
    assert.ok(STRINGS.en[card.titleKey] && STRINGS['zh-TW'][card.titleKey], `Missing reused key: ${card.titleKey}`);
}

// 2. Verify real HTML structure inside #hub-world and unchanged 5 Hub tabs.
const navMatch = html.match(/<nav id="quick-actions-list"[\s\S]*?<\/nav>/);
assert.ok(navMatch, 'Missing #quick-actions-list nav');
const tabMatches = [...navMatch[0].matchAll(/role="tab"/g)];
assert.equal(tabMatches.length, 5, 'Game Hub must keep exactly 5 tabs');

const worldSection = between(html, '<section id="hub-world"', '</section>');
assert.ok(worldSection.includes('id="explore-picks"'), '#explore-picks must live inside #hub-world');
assert.ok(worldSection.includes('id="pill-sky"') && worldSection.includes('id="pill-cop-chase"'), 'Existing WORLD buttons must remain');
assert.ok(worldSection.includes('id="desktop-hints"'), '#desktop-hints must remain inside #hub-world');

const exploreSection = between(worldSection, '<div id="explore-picks"', '<!-- 電腦版鍵盤滑鼠提示 -->');
assert.equal((exploreSection.match(/id="explore-picks"/g) || []).length, 1, 'Expected exactly one #explore-picks');
assert.equal((exploreSection.match(/id="explore-next"/g) || []).length, 1, 'Expected exactly one #explore-next');
assert.match(exploreSection, /<button[^>]*id="explore-next"[^>]*type="button"/, '#explore-next must be a native type="button"');
assert.match(exploreSection, /aria-live="polite"/, '#explore-picks must expose an aria-live="polite" region');

const cardMatches = [...exploreSection.matchAll(/<article\b([^>]*)>([\s\S]*?)<\/article>/g)];
assert.equal(cardMatches.length, 4, 'Expected exactly 4 destination cards in #explore-picks');
const parsedCards = cardMatches.map(m => {
    const attrs = m[1];
    const body = m[2];
    const idxMatch = attrs.match(/data-explore-card="(\d+)"/);
    assert.ok(idxMatch, 'Card missing data-explore-card attribute');
    const classMatch = attrs.match(/class="([^"]*)"/);
    const classes = classMatch ? classMatch[1].split(/\s+/).filter(Boolean) : [];
    const ariaHidden = (attrs.match(/aria-hidden="([^"]*)"/) || [])[1] || null;
    const hasHiddenAttr = /(?:^|\s)hidden(?:\s|=|$)/.test(attrs);
    const i18nKeys = [...body.matchAll(/data-i18n="([^"]+)"/g)].map(k => k[1]);
    return { index: Number(idxMatch[1]), classes, ariaHidden, hasHiddenAttr, i18nKeys, body };
});

for (let i = 0; i < EXPECTED_CARDS.length; i++) {
    const exp = EXPECTED_CARDS[i];
    const got = parsedCards[i];
    assert.equal(got.index, exp.index, `Card ${i} index mismatch`);
    assert.ok(got.i18nKeys.includes(exp.titleKey), `Card ${i} must reuse ${exp.titleKey}`);
    assert.ok(got.i18nKeys.includes(exp.tipKey), `Card ${i} must use ${exp.tipKey}`);
    assert.ok(got.body.includes(exp.step), `Card ${i} must display ${exp.step}`);
    if (i === 0) {
        assert.ok(!got.classes.includes('hidden') && !got.hasHiddenAttr && got.ariaHidden === 'false', 'Card 0 must be initially visible');
    } else {
        assert.ok(got.classes.includes('hidden') && got.hasHiddenAttr && got.ariaHidden === 'true', `Card ${i} must be initially hidden`);
    }
}

// 3. Static side-effect audit on real setupExplorePicks() source in index.html.
const setupExploreSrc = between(html, '        function setupExplorePicks()', '        // ---------- 靜態物件合併');
assert.ok(setupExploreSrc.includes('function setupExplorePicks()'), 'Missing named setupExplorePicks() function');
for (const forbidden of ['localStorage', 'sessionStorage', 'indexedDB', 'cookie', 'requestAnimationFrame', 'setInterval', 'setTimeout', 'fetch(', 'THREE', 'CANNON', 'saveGame', 'saveSettings', 'startMission', 'teleportTo', 'waypoint']) {
    assert.ok(!setupExploreSrc.includes(forbidden), `setupExplorePicks() must not touch forbidden API/system: ${forbidden}`);
}

// 4. DOM/VM harness driving the REAL setupControlsAndEvents() + setupExplorePicks() + Hub + VH_I18N from index.html.
class StubElement {
    constructor(id, { classes = [], attrs = {}, hidden = false, text = '' } = {}) {
        this.id = id;
        this.open = false;
        this.hidden = hidden;
        this.textContent = text;
        this.value = '';
        this.style = {};
        this.dataset = {};
        this.listeners = {};
        this.attrs = { ...attrs };
        this.children = [];
        const classSet = new Set(classes);
        this.classList = {
            add: (...xs) => xs.forEach(v => classSet.add(v)),
            remove: (...xs) => xs.forEach(v => classSet.delete(v)),
            contains: v => classSet.has(v),
            toggle: (v, force) => {
                const on = force === undefined ? !classSet.has(v) : Boolean(force);
                if (on) classSet.add(v); else classSet.delete(v);
                return on;
            },
        };
    }
    setAttribute(name, value) { this.attrs[name] = String(value); this[name] = String(value); }
    getAttribute(name) { return name in this.attrs ? this.attrs[name] : null; }
    appendChild(child) { this.children.push(child); return child; }
    focus() { this.focused = true; }
    showModal() { this.open = true; }
    close() { this.open = false; this.emit('close'); }
    addEventListener(type, fn) { (this.listeners[type] ??= []).push(fn); }
    emit(type, event = {}) {
        event.preventDefault ??= () => {};
        event.stopPropagation ??= () => {};
        event.target ??= this;
        for (const fn of this.listeners[type] || []) fn(event);
    }
    click() { this.emit('click'); }
    querySelectorAll(selector) {
        if (selector === '[data-explore-card]') return this.children.filter(c => c.getAttribute('data-explore-card') !== null);
        return [];
    }
}

function bootSession(storageBacking) {
    const elements = new Map();
    const getOrCreate = id => {
        if (!elements.has(id)) {
            const initHidden = ['missions-modal', 'garage-modal', 'settings-modal', 'world-map', 'hub-world'].includes(id);
            elements.set(id, new StubElement(id, { classes: initHidden ? ['hidden'] : [] }));
        }
        return elements.get(id);
    };

    // Populate #explore-picks and its 4 cards + i18n spans directly from parsed index.html.
    const rootEl = getOrCreate('explore-picks');
    const headingSpan = new StubElement('explore-heading-span');
    headingSpan.dataset.i18n = 'explore_picks_heading';
    const noteSpan = new StubElement('explore-note-span');
    noteSpan.dataset.i18n = 'explore_picks_note';
    const nextBtn = getOrCreate('explore-next');
    const nextSpan = new StubElement('explore-next-span');
    nextSpan.dataset.i18n = 'explore_picks_next';
    const i18nSpans = [headingSpan, noteSpan, nextSpan];

    const cardEls = parsedCards.map(c => {
        const el = new StubElement(`explore-card-${c.index}`, {
            classes: c.classes,
            attrs: { 'data-explore-card': String(c.index), 'aria-hidden': c.ariaHidden || 'false' },
            hidden: c.hasHiddenAttr,
        });
        el.titleSpan = new StubElement(`card-${c.index}-title`);
        el.titleSpan.dataset.i18n = c.i18nKeys[0];
        el.descSpan = new StubElement(`card-${c.index}-desc`);
        el.descSpan.dataset.i18n = c.i18nKeys[1];
        i18nSpans.push(el.titleSpan, el.descSpan);
        rootEl.appendChild(el);
        return el;
    });

    const doc = new StubElement('document');
    doc.hidden = false;
    doc.documentElement = { lang: 'en' };
    doc.body = new StubElement('body');
    doc.getElementById = getOrCreate;
    doc.querySelector = s => getOrCreate(s);
    doc.querySelectorAll = s => {
        if (s === '[data-i18n]') return i18nSpans;
        if (s === '#explore-picks [data-explore-card]') return cardEls;
        return [];
    };

    const sideEffects = [];
    let failOnForbidden = false;
    const recordSideEffect = name => {
        sideEffects.push(name);
        if (failOnForbidden) throw new Error(`Forbidden side effect during explore interaction: ${name}`);
    };

    const windowObj = new StubElement('window');
    windowObj.innerWidth = 1280;
    windowObj.innerHeight = 800;

    const stateObj = {
        upgradeLevel: 1,
        cash: 3500,
        fpsCap: 30,
        waypoint: null,
        quality: 'MED',
        mode: 'FOOT',
    };
    const stateProxy = new Proxy(stateObj, {
        set(target, prop, value) {
            if (failOnForbidden && prop === 'waypoint') recordSideEffect('STATE.waypoint');
            target[prop] = value;
            return true;
        },
    });

    const localStorageStub = {
        getItem(k) { return storageBacking.get(k) ?? null; },
        setItem(k, v) { recordSideEffect(`localStorage.setItem(${k})`); storageBacking.set(k, String(v)); },
        removeItem(k) { recordSideEffect(`localStorage.removeItem(${k})`); storageBacking.delete(k); },
    };
    const sessionStorageStub = {
        getItem() { return null; },
        setItem(k) { recordSideEffect(`sessionStorage.setItem(${k})`); },
    };

    const context = vm.createContext({
        document: doc,
        window: windowObj,
        console,
        Math,
        Number,
        String,
        Date,
        Map,
        JSON,
        parseInt,
        parseFloat,
        localStorage: localStorageStub,
        sessionStorage: sessionStorageStub,
        INPUT: {},
        canvas: getOrCreate('game-canvas'),
        CAM: { pointers: new Map(), sens: 1, invertY: false },
        RADAR: { lastDraw: 0 },
        STATE: stateProxy,
        SAVE: { owned: [] },
        GPU_NAME: 'test',
        PROFILE: 'TABLET',
        camera: { aspect: 1, updateProjectionMatrix() {} },
        applyResolution() {},
        refreshGpuLabel() {},
        WMAP: { open: false, pointers: new Map() },
        clearInterval() {},
        setInterval() { recordSideEffect('setInterval'); return 1; },
        setTimeout() { recordSideEffect('setTimeout'); return 1; },
        requestAnimationFrame() { recordSideEffect('requestAnimationFrame'); },
        fetch() { recordSideEffect('fetch'); },
        getActivePosition: () => ({ x: 10, z: 20 }),
        wmSelect() { recordSideEffect('wmSelect'); },
        drawWorldMap() {},
        startMission() { recordSideEffect('startMission'); },
        teleportTo() { recordSideEffect('teleportTo'); },
        saveGame() { recordSideEffect('saveGame'); },
        saveSettings() { recordSideEffect('saveSettings'); },
        toggleEnterExitCar() {},
        addCash() {},
        AUDIO: { playSFX() {}, toggleStation() {} },
    });

    // Execute real I18N runtime, Hub panel/tab control, and setupControlsAndEvents + setupExplorePicks from index.html.
    vm.runInContext(
        i18nScript[1]
        + '\nthis.VH_I18N = VH_I18N;'
        + between(html, '        const HUB_PANELS =', '        function startMission(')
        + between(html, '        function openWorldMap()', '        // 快速穿梭')
        + between(html, '        function setupControlsAndEvents()', '        // ---------- 靜態物件合併'),
        context
    );

    context.setupControlsAndEvents();
    context.VH_I18N.apply();

    const visibleIndices = () => cardEls
        .filter(c => !c.classList.contains('hidden') && !c.hidden && c.getAttribute('aria-hidden') === 'false')
        .map(c => Number(c.getAttribute('data-explore-card')));

    const assertActiveIndex = expected => {
        assert.deepEqual(visibleIndices(), [expected], `Expected only card ${expected} visible`);
        assert.equal(rootEl.dataset.exploreIndex, String(expected), `root dataset.exploreIndex mismatch`);
        for (const c of cardEls) {
            const idx = Number(c.getAttribute('data-explore-card'));
            const active = idx === expected;
            assert.equal(c.classList.contains('hidden'), !active, `Card ${idx} hidden class mismatch`);
            assert.equal(c.hidden, !active, `Card ${idx} hidden property mismatch`);
            assert.equal(c.getAttribute('aria-hidden'), active ? 'false' : 'true', `Card ${idx} aria-hidden mismatch`);
        }
    };

    return {
        context,
        doc,
        rootEl,
        nextBtn,
        cardEls,
        headingSpan,
        noteSpan,
        nextSpan,
        sideEffects,
        setFailOnForbidden: v => { failOnForbidden = v; },
        assertActiveIndex,
    };
}

const storageBacking = new Map();
const session1 = bootSession(storageBacking);

// Initial state: index 0 visible, no unauthorized storage writes.
session1.assertActiveIndex(0);
assert.equal(storageBacking.size, 0, 'Initial load must not write storage');

// Strict side-effect guard during Next Stop interactions.
session1.setFailOnForbidden(true);

// Cycle 0 -> 1 -> 2 -> 3 -> 0 via real click handler.
for (const expected of [1, 2, 3, 0]) {
    session1.nextBtn.click();
    session1.assertActiveIndex(expected);
}

// Re-invoking setupExplorePicks() must not double-bind the click handler.
session1.context.setupExplorePicks();
session1.nextBtn.click();
session1.assertActiveIndex(1);

// Advance to index 2, switch Hub tabs & close/reopen Hub -> index 2 preserved.
session1.nextBtn.click();
session1.assertActiveIndex(2);
session1.doc.getElementById('hub-world-tab').click();
session1.doc.getElementById('pill-settings').click();
session1.context.closeModals();
session1.doc.getElementById('hub-world-tab').click();
session1.assertActiveIndex(2);

// Language switch en -> zh-TW -> en at index 2 updates text immediately without changing index.
session1.context.VH_I18N.setLanguage('zh-TW');
session1.assertActiveIndex(2);
assert.equal(session1.headingSpan.textContent, STRINGS['zh-TW'].explore_picks_heading);
assert.equal(session1.noteSpan.textContent, STRINGS['zh-TW'].explore_picks_note);
assert.equal(session1.nextSpan.textContent, STRINGS['zh-TW'].explore_picks_next);
assert.equal(session1.cardEls[2].titleSpan.textContent, STRINGS['zh-TW'].mount_chiliad_summit);
assert.equal(session1.cardEls[2].descSpan.textContent, STRINGS['zh-TW'].explore_tip_chiliad);

session1.context.VH_I18N.setLanguage('en');
session1.assertActiveIndex(2);
assert.equal(session1.headingSpan.textContent, STRINGS.en.explore_picks_heading);
assert.equal(session1.noteSpan.textContent, STRINGS.en.explore_picks_note);
assert.equal(session1.nextSpan.textContent, STRINGS.en.explore_picks_next);
assert.equal(session1.cardEls[2].titleSpan.textContent, STRINGS.en.mount_chiliad_summit);
assert.equal(session1.cardEls[2].descSpan.textContent, STRINGS.en.explore_tip_chiliad);

assert.equal(session1.sideEffects.length, 0, `Unexpected side effects: ${session1.sideEffects.join(', ')}`);
assert.equal(storageBacking.size, 0, 'Explore picks must not write any storage');

// Simulated full page reload resets selection to index 0.
const session2 = bootSession(storageBacking);
session2.assertActiveIndex(0);
assert.equal(storageBacking.size, 0, 'Reload must not write any storage');

console.log('PASS: 4 cards & #explore-next in #hub-world, exact 7 new + 4 reused i18n keys, 5 Hub tabs preserved');
console.log('PASS: real setupExplorePicks() cycles 0->1->2->3->0, guards double-bind, preserves across Hub tabs/close, resets on reload');
console.log('PASS: en <-> zh-TW updates text at index 2 without changing selection; zero storage/navigation/timer side effects');
console.log('RESULT: PASS (Node DOM/VM regression checks on real index.html; browser layout and real-device checks remain separate)');
