// Headless traffic component harness: actual game routes, vehicle/controller and Cannon world.
// No renderer, city colliders, NPCs, textures or browser. Never interpret its timing as device FPS.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
export const root = new URL('../../', import.meta.url);
export const html = fs.readFileSync(new URL('index.html', root), 'utf8');
async function vendored(path) {
    return import('data:text/javascript;base64,' + fs.readFileSync(new URL(path, root)).toString('base64'));
}
export const THREE = await vendored('libs/three/build/three.module.js');
export const CANNON = await vendored('libs/cannon-es/cannon-es.js');
function section(source, start, end) {
    const a = source.indexOf(start), b = source.indexOf(end, a);
    assert.ok(a >= 0 && b > a, `Missing source boundary: ${start}`);
    return source.slice(a, b);
}
// Geometry/transform-only reader for the vendored, uncompressed Kenney GLB. The real
// applyCustomModel consumes these nodes, so chassis and wheel bounds use the asset's vertices.
// Deliberately excludes material rendering, images, animation, networking and GLTFLoader testing.
function kenneyBounds() {
    const data = fs.readFileSync(new URL('models/cars/kenney_traffic.glb', root));
    const jsonLength = data.readUInt32LE(12), gltf = JSON.parse(data.subarray(20, 20 + jsonLength));
    assert.ok(!gltf.extensionsRequired?.length && !gltf.skins?.length);
    const binaryStart = 20 + jsonLength + 8;
    const meshes = gltf.meshes.map(mesh => {
        const group = new THREE.Group();
        for (const primitive of mesh.primitives) {
            const a = gltf.accessors[primitive.attributes.POSITION], view = gltf.bufferViews[a.bufferView];
            assert.equal(a.componentType, 5126); assert.equal(a.type, 'VEC3'); assert.ok(!a.sparse);
            const start = binaryStart + (view.byteOffset || 0) + (a.byteOffset || 0);
            const positions = new Float32Array(a.count * 3);
            for (let i = 0; i < a.count; i++) for (let j = 0; j < 3; j++) {
                positions[i * 3 + j] = data.readFloatLE(start + i * (view.byteStride || 12) + j * 4);
            }
            const geometry = new THREE.BufferGeometry();
            geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
            const material = new THREE.MeshBasicMaterial();
            material.name = gltf.materials[primitive.material]?.name || '';
            group.add(new THREE.Mesh(geometry, material));
        }
        return group;
    });
    function node(index) {
        const def = gltf.nodes[index], group = new THREE.Group();
        group.name = def.name || '';
        if (def.matrix) new THREE.Matrix4().fromArray(def.matrix).decompose(group.position, group.quaternion, group.scale);
        if (def.translation) group.position.fromArray(def.translation);
        if (def.rotation) group.quaternion.fromArray(def.rotation);
        if (def.scale) group.scale.fromArray(def.scale);
        if (def.mesh !== undefined) group.add(meshes[def.mesh].clone(true));
        for (const child of def.children || []) group.add(node(child));
        return group;
    }
    const scenes = gltf.scenes.map(s => {
        const group = new THREE.Group(); group.name = s.name;
        for (const index of s.nodes) group.add(node(index));
        return group;
    });
    return { scenes, scene: scenes[gltf.scene || 0] };
}
export const kenney = kenneyBounds();
export function presets(source) {
    const result = {};
    for (const m of source.matchAll(/(PHONE_LOW|PHONE_MED|TABLET_LOW|TABLET_MED|TABLET_HIGH|DESKTOP_MED|DESKTOP_HIGH|DESKTOP_ULTRA|IGPU_LOW|IGPU_MED|IGPU_HIGH):\s*\{[^\n]*traffic:\s*(\d+)/g)) result[m[1]] = +m[2];
    assert.equal(Object.keys(result).length, 11);
    return result;
}
export async function harness(source = html, preset = 'DESKTOP_HIGH', seed = 1, failAssets = false) {
    let randomState = seed >>> 0;
    const math = Object.create(Math);
    math.random = () => ((randomState = (Math.imul(randomState, 1664525) + 1013904223) >>> 0) / 4294967296);
    const assetCalls = [], warnings = [];
    const h = vm.createContext({
        THREE, CANNON, Math: math, console: { ...console, warn: (...args) => warnings.push(args) },
        tr: key => key, DENSITY: { traffic: presets(source)[preset] },
        STATE: { mode: 'FOOT', time: 0, currentVehicle: null, wantedStars: 0 },
        WORLD: { vehicles: [], policeUnits: [] },
        PLAYER: { body: new CANNON.Body({ mass: 0, position: new CANNON.Vec3(98, 1, 22) }), group: new THREE.Group() },
        camera: new THREE.PerspectiveCamera(60, 16 / 9, 0.5, 2600), scene: new THREE.Scene(),
        getPaintFlakeTexture: () => null, toDetailLayer() {},
        gltfLoader: { load(url, success, progress, failure) {
            assetCalls.push(url);
            if (url.endsWith('kenney_traffic.glb')) {
                queueMicrotask(() => failAssets ? failure() : success(kenney));
            }
            // Parked Ferrari / Ford visuals are intentionally not loaded in this component test.
        } }
    });
    const physics = section(source, '        const physicsWorld =', '        // ==================== 4. THREE.JS');
    const roads = section(source, '        const ROAD_NET =', '        // ---------- 道路視覺');
    const vehicles = section(source, '        const CAR_STANCE =', '        // 用 meshoptimizer');
    const manager = section(source, '        const TRAFFIC =', '        // Cache DOM/context');
    vm.runInContext(physics + roads + vehicles + manager + `
        this.physicsWorld = physicsWorld; this.ROAD_NET = ROAD_NET; this.TRAFFIC = TRAFFIC;
        this.Vehicle = RealisticRaycastVehicle; this.KENNEY_TYPES = KENNEY_TYPES;
        this.getActivePosition = () => STATE.mode === 'CAR' && STATE.currentVehicle ? STATE.currentVehicle.chassisGroup.position : PLAYER.group.position;
    `, h);
    // Only visual construction is stubbed; real Cannon wheels, collision listeners, controllers,
    // applyCustomModel, Ferrari guards, spawning, recycling and activation remain executable.
    h.Vehicle.prototype.setupLivery = function () {};
    h.Vehicle.prototype.buildFallbackCarMesh = function () {
        for (let i = 0; i < 4; i++) this.wheelMeshes.push(new THREE.Group());
    };
    h.Vehicle.prototype.buildRearLights = function () {};
    h.Vehicle.prototype.buildBodyKit = function () {};
    h.Vehicle.prototype.applyDamage = function () {}; // no rendering of damage in this harness
    h.movePlayer = (x, z, heading = 0, y = 1) => {
        h.PLAYER.body.position.set(x, y, z); h.PLAYER.group.position.copy(h.PLAYER.body.position);
        h.camera.position.set(x - Math.sin(heading) * 7.2, y + 2, z - Math.cos(heading) * 7.2);
        h.camera.lookAt(x + Math.sin(heading) * 30, y, z + Math.cos(heading) * 30);
        h.camera.updateMatrixWorld(true);
    };
    h.movePlayer(98, 22);
    h.spawnVehicles();
    for (let i = 0; i < 5; i++) await Promise.resolve();
    for (const v of h.WORLD.vehicles) {
        v.chassisGroup.position.copy(v.chassisBody.position);
        v.chassisGroup.quaternion.copy(v.chassisBody.quaternion);
    }
    h.ordinary = () => h.WORLD.vehicles.filter(v => v.isAI && !v.isPolice);
    h.freeze = () => {
        if (h.updateTrafficPhysics) h.updateTrafficPhysics();
        else for (const v of h.ordinary()) v.update(0); // baseline's actual camera-distance freeze path
    };
    h.tick = (dt = 1 / 60) => {
        h.STATE.time += dt;
        if (h.updateTrafficPhysics) h.updateTrafficPhysics();
        h.physicsWorld.step(1 / 60, dt, 3);
        for (const v of h.ordinary()) v.update(dt);
        h.recycleTraffic(dt);
    };
    h.assetCalls = assetCalls; h.warnings = warnings;
    return h;
}
