// VICE HORIZON VI Service Worker：快取優先，第一次載入後可離線遊玩
// 更新遊戲時，把 CACHE 的版本號改掉，玩家下次開啟就會下載新版本
const CACHE = 'vh-2026-11-22-09';
const PRECACHE = [
  "./",
  "./css/app.css",
  "./fonts/orbitron-latin-600-normal.woff2",
  "./fonts/orbitron-latin-800-normal.woff2",
  "./fonts/orbitron-latin-900-normal.woff2",
  "./fonts/rajdhani-latin-600-normal.woff2",
  "./fonts/rajdhani-latin-700-normal.woff2",
  "./icons/apple-touch-icon.png",
  "./icons/icon-192.png",
  "./icons/icon-512.png",
  "./icons/icon-maskable-512.png",
  "./index.html",
  "./libs/cannon-es/cannon-es.js",
  "./libs/draco/draco_decoder.js",
  "./libs/draco/draco_decoder.wasm",
  "./libs/draco/draco_wasm_wrapper.js",
  "./libs/meshoptimizer/meshopt_simplifier.js",
  "./libs/three/build/three.module.js",
  "./libs/three/examples/jsm/geometries/RoundedBoxGeometry.js",
  "./libs/three/examples/jsm/loaders/DRACOLoader.js",
  "./libs/three/examples/jsm/loaders/GLTFLoader.js",
  "./libs/three/examples/jsm/math/SimplexNoise.js",
  "./libs/three/examples/jsm/objects/Sky.js",
  "./libs/three/examples/jsm/objects/Water.js",
  "./libs/three/examples/jsm/postprocessing/EffectComposer.js",
  "./libs/three/examples/jsm/postprocessing/MaskPass.js",
  "./libs/three/examples/jsm/postprocessing/OutputPass.js",
  "./libs/three/examples/jsm/postprocessing/Pass.js",
  "./libs/three/examples/jsm/postprocessing/RenderPass.js",
  "./libs/three/examples/jsm/postprocessing/SMAAPass.js",
  "./libs/three/examples/jsm/postprocessing/SSAOPass.js",
  "./libs/three/examples/jsm/postprocessing/ShaderPass.js",
  "./libs/three/examples/jsm/postprocessing/UnrealBloomPass.js",
  "./libs/three/examples/jsm/shaders/CopyShader.js",
  "./libs/three/examples/jsm/shaders/FXAAShader.js",
  "./libs/three/examples/jsm/shaders/LuminosityHighPassShader.js",
  "./libs/three/examples/jsm/shaders/OutputShader.js",
  "./libs/three/examples/jsm/shaders/SMAAShader.js",
  "./libs/three/examples/jsm/shaders/SSAOShader.js",
  "./libs/three/examples/jsm/utils/BufferGeometryUtils.js",
  "./libs/three/examples/jsm/utils/SkeletonUtils.js",
  "./manifest.webmanifest",
  "./manifest.zh-TW.webmanifest",
  "./models/Michelle.glb",
  "./models/Soldier.glb",
  "./models/Xbot.glb",
  "./models/cars/fordgt500cop.glb",
  "./models/cars/kenney_traffic.glb",
  "./models/cars/lexuslc500.glb",
  "./models/cars/porsche911.glb",
  "./models/ferrari.glb",
  "./models/polyhaven/Models/gltf/1k/barrel_03/barrel_03_1k.gltf",
  "./models/polyhaven/Models/gltf/1k/covered_car/covered_car_1k.gltf",
  "./models/polyhaven/Models/gltf/1k/modular_urban_apartments_facade/modular_urban_apartments_facade_1k.gltf",
  "./models/polyhaven/Models/gltf/1k/painted_wooden_bench/painted_wooden_bench_1k.gltf",
  "./models/polyhaven/Models/gltf/1k/street_lamp_01/street_lamp_01_1k.gltf",
  "./models/polyhaven/Models/gltf/1k/water_manhole_cover/water_manhole_cover_1k.gltf",
  "./models/polyhaven/Models/gltf/4k/barrel_03/barrel_03.bin",
  "./models/polyhaven/Models/gltf/4k/painted_wooden_bench/painted_wooden_bench.bin",
  "./models/polyhaven/Models/gltf/4k/water_manhole_cover/water_manhole_cover.bin",
  "./models/polyhaven/Models/gltf/8k/covered_car/covered_car.bin",
  "./models/polyhaven/Models/gltf/8k/modular_urban_apartments_facade/modular_urban_apartments_facade.bin",
  "./models/polyhaven/Models/gltf/8k/street_lamp_01/street_lamp_01.bin",
  "./models/polyhaven/Models/jpg/1k/barrel_03/barrel_03_arm_1k.jpg",
  "./models/polyhaven/Models/jpg/1k/barrel_03/barrel_03_diff_1k.jpg",
  "./models/polyhaven/Models/jpg/1k/barrel_03/barrel_03_nor_gl_1k.jpg",
  "./models/polyhaven/Models/jpg/1k/covered_car/covered_car_arm_1k.jpg",
  "./models/polyhaven/Models/jpg/1k/covered_car/covered_car_diff_1k.jpg",
  "./models/polyhaven/Models/jpg/1k/covered_car/covered_car_nor_gl_1k.jpg",
  "./models/polyhaven/Models/jpg/1k/modular_urban_apartments_facade/modular_urban_apartments_facade_objects_arm_1k.jpg",
  "./models/polyhaven/Models/jpg/1k/modular_urban_apartments_facade/modular_urban_apartments_facade_objects_diff_1k.jpg",
  "./models/polyhaven/Models/jpg/1k/modular_urban_apartments_facade/modular_urban_apartments_facade_objects_nor_gl_1k.jpg",
  "./models/polyhaven/Models/jpg/1k/modular_urban_apartments_facade/modular_urban_apartments_facade_plaster_arm_1k.jpg",
  "./models/polyhaven/Models/jpg/1k/modular_urban_apartments_facade/modular_urban_apartments_facade_plaster_diff_1k.jpg",
  "./models/polyhaven/Models/jpg/1k/modular_urban_apartments_facade/modular_urban_apartments_facade_plaster_nor_gl_1k.jpg",
  "./models/polyhaven/Models/jpg/1k/modular_urban_apartments_facade/modular_urban_apartments_facade_trim_01_arm_1k.jpg",
  "./models/polyhaven/Models/jpg/1k/modular_urban_apartments_facade/modular_urban_apartments_facade_trim_01_diff_1k.jpg",
  "./models/polyhaven/Models/jpg/1k/modular_urban_apartments_facade/modular_urban_apartments_facade_trim_01_nor_gl_1k.jpg",
  "./models/polyhaven/Models/jpg/1k/modular_urban_apartments_facade/modular_urban_apartments_facade_trim_02_arm_1k.jpg",
  "./models/polyhaven/Models/jpg/1k/modular_urban_apartments_facade/modular_urban_apartments_facade_trim_02_diff_1k.jpg",
  "./models/polyhaven/Models/jpg/1k/modular_urban_apartments_facade/modular_urban_apartments_facade_trim_02_nor_gl_1k.jpg",
  "./models/polyhaven/Models/jpg/1k/painted_wooden_bench/painted_wooden_bench_arm_1k.jpg",
  "./models/polyhaven/Models/jpg/1k/painted_wooden_bench/painted_wooden_bench_diff_1k.jpg",
  "./models/polyhaven/Models/jpg/1k/painted_wooden_bench/painted_wooden_bench_nor_gl_1k.jpg",
  "./models/polyhaven/Models/jpg/1k/street_lamp_01/street_lamp_01_arm_1k.jpg",
  "./models/polyhaven/Models/jpg/1k/street_lamp_01/street_lamp_01_diff_1k.jpg",
  "./models/polyhaven/Models/jpg/1k/street_lamp_01/street_lamp_01_nor_gl_1k.jpg",
  "./models/polyhaven/Models/jpg/1k/water_manhole_cover/water_manhole_cover_arm_1k.jpg",
  "./models/polyhaven/Models/jpg/1k/water_manhole_cover/water_manhole_cover_diff_1k.jpg",
  "./models/polyhaven/Models/jpg/1k/water_manhole_cover/water_manhole_cover_nor_gl_1k.jpg",
  "./textures/polyhaven/aerial_grass_rock/aerial_grass_rock_diff_1k.jpg",
  "./textures/polyhaven/aerial_grass_rock/aerial_grass_rock_nor_gl_1k.jpg",
  "./textures/polyhaven/asphalt_02/asphalt_02_nor_gl_1k.jpg",
  "./textures/polyhaven/asphalt_02/asphalt_02_rough_1k.jpg",
  "./textures/polyhaven/concrete_wall_008/concrete_wall_008_diff_1k.jpg",
  "./textures/polyhaven/concrete_wall_008/concrete_wall_008_nor_gl_1k.jpg",
  "./textures/polyhaven/red_brick_03/red_brick_03_diff_1k.jpg",
  "./textures/polyhaven/red_brick_03/red_brick_03_nor_gl_1k.jpg",
  "./textures/polyhaven/rock_face/rock_face_diff_1k.jpg",
  "./textures/polyhaven/rock_face/rock_face_nor_gl_1k.jpg",
  "./textures/polyhaven/snow_02/snow_02_diff_1k.jpg",
  "./textures/polyhaven/snow_02/snow_02_nor_gl_1k.jpg",
  "./textures/waternormals.jpg"
];

self.addEventListener('install', event => {
    event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(PRECACHE)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
            .then(() => self.clients.claim())
    );
});

self.addEventListener('fetch', event => {
    if (event.request.method !== 'GET') return;
    event.respondWith(
        caches.match(event.request, { ignoreSearch: true }).then(hit => hit || fetch(event.request).then(res => {
            if (res && res.ok && new URL(event.request.url).origin === self.location.origin) {
                const copy = res.clone();
                caches.open(CACHE).then(cache => cache.put(event.request, copy));
            }
            return res;
        }))
    );
});
