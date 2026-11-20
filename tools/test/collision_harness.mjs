// Headless collision harness: real procedural placements/instance geometry and Cannon shapes.
// Canvas paint and rendering are omitted. No browser, full-scene or device-performance claim.
import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import { harness as trafficHarness, html, root, THREE, CANNON } from './traffic_harness.mjs';
export { html, root, THREE, CANNON };
export function section(source, start, end) {
    const a = source.indexOf(start), b = source.indexOf(end, a);
    assert.ok(a >= 0 && b > a, `Missing source boundary: ${start}`);
    return source.slice(a, b);
}
const threeURL = 'data:text/javascript;base64,' + fs.readFileSync(new URL('libs/three/build/three.module.js', root)).toString('base64');
const utils = fs.readFileSync(new URL('libs/three/examples/jsm/utils/BufferGeometryUtils.js', root), 'utf8').replace("from 'three'", `from '${threeURL}'`);
export const { mergeGeometries } = await import('data:text/javascript;base64,' + Buffer.from(utils).toString('base64'));
export async function collisionHarness(source = html, preset = 'PHONE_LOW') {
    const h = await trafficHarness(source, preset);
    h.PROFILE = preset.startsWith('DESKTOP') ? 'DESKTOP' : 'MOBILE'; h.DETAIL_LAYER = 1;
    h.mergeGeometries = mergeGeometries;
    const noop = () => {};
    const ctx = new Proxy({}, { get: (obj, key) => obj[key] ?? noop, set: (obj, key, val) => { obj[key] = val; return true; } });
    h.document = { createElement: () => ({ getContext: () => ctx }) };
    h.showBanner = noop; h.closeModals = noop; h.STUNT = { active: null };
    h.console = { log: noop, warn: noop };
    vm.runInContext(section(source, '        function addStaticBoxCollider(', '        // ---------- 平滑坡道') +
        section(source, '        const TREES =', '        // ==================== 環狀高架') +
        section(source, '        function buildPalmAssets()', '        // ---------- Poly Haven') +
        section(source, '        function addPocketPark(', '        // ---------- 程式產生的寫實棕櫚樹') +
        section(source, '        function cityDistrict(', '        // 玻璃帷幕牆貼圖') +
        section(source, '        function createCapsuleBody(', '        class RealisticCharacter') +
        section(source, '        function teleportTo(', '        function getActivePosition()') +
        section(source, '        const PHYS_DEBUG =', '        // ==================== 12.') +
        `this.TREES = TREES; this.PHYS_DEBUG = PHYS_DEBUG;
        this.TREE_COLLIDERS = typeof TREE_COLLIDERS === 'undefined' ? null : TREE_COLLIDERS;
        this.PLAYER.body = createCapsuleBody(75, .42, 1.8, 98, 1.1, 22, true);
        this.up = new CANNON.Vec3(0, 1, 0);
        `, h);
    // Execute all original tree-placement loops in their original order. Omit only unrelated visuals.
    const roundabout = section(source, '                for (let k = 0; k < 4; k++) {\n                    const a = k * Math.PI / 2 + 0.6;', '            // 地形 (');
    vm.runInContext('ROAD_NET.roundabouts.forEach(rb => {\n' + roundabout, h);
    const hill = section(source, '            const pineLimit =', '            dmy.scale.setScalar(1);\n            const rockGeo');
    vm.runInContext('{ const hl = ROAD_NET.hill, hr = ROAD_NET.hillRoad, dmy = new THREE.Object3D();' + hill + '}', h);
    const beforeHouses = h.physicsWorld.bodies.length;
    h.buildSuburbs();
    h.houseBodies = h.physicsWorld.bodies.slice(beforeHouses);
    h.city = [];
    let city = section(source, '            blockX.forEach((bx, ix) => {', '                        const bGroup = new THREE.Group();');
    const bx = source.match(/const blockX = ([^;]+);/)[0], bz = source.match(/const blockZ = ([^;]+);/)[0];
    vm.runInContext('{ const cityParcels = []; ' + bx + bz + city + 'this.city.push({x:px,z:pz,w,d,h,district});\n} }); }); }', h);
    const infillTrees = h.TREES.list.slice();
    h.buildTestCityInfill = (...args) => {
        const allTrees = h.TREES.list; h.TREES.list = infillTrees;
        try { return h.buildCityInfill(...args); } finally { h.TREES.list = allTrees; }
    };
    vm.runInContext('{ const dummy = new THREE.Object3D();' + section(source, '            const palmMatrices = [];', '            const lampMatrices = [];') + '}', h);
    vm.runInContext(section(source, '            [-240, -120, 0].forEach((ax, ai) => {', '            WORLD.lampPositions ='), h);
    h.buildTrees();
    if (h.initTreeColliders) h.initTreeColliders();
    vm.runInContext(section(source, '        const FAST_TRAVEL =', '        const WMAP =') +
        section(source, '        const DELIVERY =', '        function buildDeliveryDepots()') +
        section(source, '        function snapToRoad(', '        function districtName(') +
        '{' + section(source, '            const rampList = [', '            const rampMat =') + 'this.ramps = rampList;}' +
        'this.arrivals = FAST_TRAVEL; this.depots = DELIVERY.depots.map(d => snapToRoad(d.x, d.z));', h);
    h.scene.updateMatrixWorld(true);
    h.selectObserver = (x, z, y = h.terrainHeight(x, z) + 1.1) => {
        h.STATE.mode = 'FOOT'; h.STATE.currentVehicle = null;
        h.movePlayer(x, z, 0, y);
        h.PLAYER.body.aabbNeedsUpdate = true;
        h.refreshTreeColliders?.(0, true);
    };
    return h;
}
