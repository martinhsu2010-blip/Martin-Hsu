import os, re, shutil, json, hashlib, subprocess, zipfile
SRC = '/home/claude/game/vh_j.html'
NM = '/home/claude/pwabuild/node_modules'
OUT = '/home/claude/pwabuild/out/vice-horizon-pwa'
ASSETS = '/home/claude/pwabuild/assets'
VERSION = 'vh-2026-11-18-12'
if os.path.exists(OUT): shutil.rmtree(OUT)
os.makedirs(OUT)
src = open(SRC).read()

# ---------- 1. JS libs: three core + crawled addon deps ----------
def copy(rel_src, rel_dst):
    dst = os.path.join(OUT, rel_dst); os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.copy(rel_src, dst)
copy(f'{NM}/three/build/three.module.js', 'libs/three/build/three.module.js')
copy(f'{NM}/cannon-es/dist/cannon-es.js', 'libs/cannon-es/cannon-es.js')
jsm = f'{NM}/three/examples/jsm'
todo = re.findall(r"from 'three/addons/([^']+)'", src)
seen = set()
while todo:
    rel = os.path.normpath(todo.pop())
    if rel in seen: continue
    seen.add(rel)
    path = os.path.join(jsm, rel)
    code = open(path).read()
    copy(path, f'libs/three/examples/jsm/{rel}')
    for imp in re.findall(r"(?:from|import)\s+['\"](\.{1,2}/[^'\"]+)['\"]", code):
        todo.append(os.path.normpath(os.path.join(os.path.dirname(rel), imp)))
for f in ['draco_decoder.js', 'draco_decoder.wasm', 'draco_wasm_wrapper.js']:
    copy(f'{jsm}/libs/draco/gltf/{f}', f'libs/draco/{f}')
print('addon files:', len(seen))

# ---------- 2. assets ----------
for f in ['Soldier.glb', 'Xbot.glb', 'Michelle.glb', 'ferrari.glb']:
    copy(f'{ASSETS}/{f}', f'models/{f}')
copy(f'{ASSETS}/waternormals.jpg', 'textures/waternormals.jpg')
# 新車款：Porsche / Lexus / Ford 警車 (玩家提供) + Kenney Car Kit 交通車 (CC0)
for f in sorted(os.listdir(f'{ASSETS}/cars')):
    copy(f'{ASSETS}/cars/{f}', f'models/cars/{f}')
for root, _, files in os.walk(f'{ASSETS}/ph'):
    for f in files:
        rel = os.path.relpath(os.path.join(root, f), f'{ASSETS}/ph')
        copy(os.path.join(root, f), f'textures/polyhaven/{rel}')

copy(f'{NM}/meshoptimizer/meshopt_simplifier.js', 'libs/meshoptimizer/meshopt_simplifier.js')
# Poly Haven CC0 models (mirror their URL paths)
ph = json.load(open('/home/claude/fix1/ph_models.json'))
for name, d in ph.items():
    for url in [d['gltf']] + list(d['files'].values()):
        rel = url.split('/file/ph-assets/Models/')[1]
        dst = os.path.join(OUT, 'models/polyhaven/Models', rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if not os.path.exists(dst):
            subprocess.run(['curl', '-sS', '-f', '-o', dst, url], check=True)

# ---------- 3. fonts ----------
font_css = []
for fam, pkg, weights in [('Orbitron', 'orbitron', [600, 800, 900]), ('Rajdhani', 'rajdhani', [600, 700])]:
    for w in weights:
        fn = f'{pkg}-latin-{w}-normal.woff2'
        copy(f'{NM}/@fontsource/{pkg}/files/{fn}', f'fonts/{fn}')
        font_css.append(f"@font-face{{font-family:'{fam}';font-style:normal;font-weight:{w};font-display:swap;src:url('../fonts/{fn}') format('woff2');}}")

# ---------- 4. HTML rewrite ----------
html = src
rep = [
    ('https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js', './libs/three/build/three.module.js'),
    ('https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/', './libs/three/examples/jsm/'),
    ('https://cdn.jsdelivr.net/npm/cannon-es@0.20.0/+esm', './libs/cannon-es/cannon-es.js'),
    ('https://www.gstatic.com/draco/versioned/decoders/1.5.6/', './libs/draco/'),
    ('https://martinhsu2010-blip.github.io/Martin-Hsu/models/cars/', './models/cars/'),
    ('https://threejs.org/examples/models/gltf/', './models/'),
    ('https://raw.githubusercontent.com/mrdoob/three.js/master/examples/models/gltf/', './models/'),
    ('https://threejs.org/examples/textures/waternormals.jpg', './textures/waternormals.jpg'),
    ('https://dl.polyhaven.org/file/ph-assets/Textures/jpg/1k/', './textures/polyhaven/'),
    ('https://dl.polyhaven.org/file/ph-assets/Models/', './models/polyhaven/Models/'),
    ('https://cdn.jsdelivr.net/npm/meshoptimizer@1.3.0/meshopt_simplifier.js', './libs/meshoptimizer/meshopt_simplifier.js'),
]
for a, b in rep:
    assert a in html, a
    html = html.replace(a, b)
# Tailwind CDN + Google Fonts -> local CSS
html = re.sub(r'\s*<script src="https://cdn.tailwindcss.com"></script>', '', html)
html = re.sub(r'\s*<link href="https://fonts.googleapis.com/css2\?[^"]+" rel="stylesheet">', '', html)
pwa_head = '''
    <link rel="stylesheet" href="./css/app.css">
    <link rel="manifest" href="./manifest.webmanifest">
    <link rel="icon" type="image/png" sizes="192x192" href="./icons/icon-192.png">
    <link rel="apple-touch-icon" href="./icons/apple-touch-icon.png">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-title" content="Vice Horizon">'''
html = html.replace('<meta name="theme-color" content="#0f172a">', '<meta name="theme-color" content="#0f172a">' + pwa_head, 1)
# Noto Sans TC fallback to system CJK fonts (offline)
html = html.replace("font-family: 'Rajdhani', 'Noto Sans TC', sans-serif;", "font-family: 'Rajdhani', 'Noto Sans TC', 'PingFang TC', 'Microsoft JhengHei', sans-serif;")
html = html.replace("font-family: 'Orbitron', 'Noto Sans TC', sans-serif;", "font-family: 'Orbitron', 'Noto Sans TC', 'PingFang TC', 'Microsoft JhengHei', sans-serif;")

install_ui = '''
    <!-- ==================== PWA：安裝按鈕與 iPhone/iPad 提示 ==================== -->
    <button id="pwa-install-btn" type="button" class="hidden fixed z-50 left-1/2 -translate-x-1/2 bottom-24 px-5 py-3 rounded-2xl font-vice font-black text-sm bg-gradient-to-r from-rose-600 via-sky-600 to-emerald-500 text-white shadow-xl border-2 border-white/80">📲 安裝遊戲到主畫面</button>
    <div id="pwa-ios-hint" class="hidden fixed z-50 inset-x-3 bottom-24 hud-glass rounded-2xl p-3 text-sm text-white border border-sky-400/60 text-center">
        📲 要安裝成 App：點 Safari 下方的 <b>分享</b> 按鈕 → 選擇 <b>加入主畫面</b>
        <button id="pwa-ios-close" type="button" class="ml-2 px-2 py-0.5 rounded-lg bg-white/15">知道了</button>
    </div>
    <script>
    (function () {
        // 註冊 Service Worker：第一次開啟後，之後沒有網路也能玩
        if ('serviceWorker' in navigator) {
            // 自動更新：每次開啟都檢查新版本；新版本下載完、接管頁面時自動重新載入 (只在「更新」時，第一次安裝不會)
            var hadController = !!navigator.serviceWorker.controller;
            var reloaded = false;
            navigator.serviceWorker.addEventListener('controllerchange', function () {
                if (!hadController || reloaded) return;
                reloaded = true;
                var n = document.createElement('div');
                n.textContent = '已下載新版本，重新載入中…';
                n.style.cssText = 'position:fixed;left:50%;top:14px;transform:translateX(-50%);z-index:9999;padding:8px 16px;border-radius:999px;background:rgba(2,6,23,.92);color:#67e8f9;font:700 13px system-ui,sans-serif;border:1px solid rgba(34,211,238,.6)';
                document.body.appendChild(n);
                setTimeout(function () { location.reload(); }, 900);
            });
            window.addEventListener('load', function () {
                navigator.serviceWorker.register('./sw.js', { updateViaCache: 'none' }).then(function (reg) {
                    reg.update().catch(function () {});
                    document.addEventListener('visibilitychange', function () { if (document.visibilityState === 'visible') reg.update().catch(function () {}); });
                }).catch(function () {});
            });
        }
        var standalone = window.matchMedia('(display-mode: standalone)').matches || window.matchMedia('(display-mode: fullscreen)').matches || window.navigator.standalone === true;
        var deferred = null;
        var btn = document.getElementById('pwa-install-btn');
        window.addEventListener('beforeinstallprompt', function (e) {
            e.preventDefault();
            deferred = e;
            if (!standalone) btn.classList.remove('hidden');
        });
        btn.addEventListener('click', function () {
            if (!deferred) return;
            deferred.prompt();
            deferred.userChoice.finally(function () { deferred = null; btn.classList.add('hidden'); });
        });
        window.addEventListener('appinstalled', function () { btn.classList.add('hidden'); });
        // iPhone / iPad：Safari 沒有安裝按鈕，顯示一次「分享 → 加入主畫面」提示
        var ua = navigator.userAgent;
        var isIOS = /iPhone|iPad|iPod/.test(ua) || (/Macintosh/.test(ua) && navigator.maxTouchPoints > 1);
        var seen = false;
        try { seen = localStorage.getItem('vh_ios_hint') === '1'; } catch (e) {}
        if (isIOS && !standalone && !seen) {
            var hint = document.getElementById('pwa-ios-hint');
            hint.classList.remove('hidden');
            document.getElementById('pwa-ios-close').addEventListener('click', function () {
                hint.classList.add('hidden');
                try { localStorage.setItem('vh_ios_hint', '1'); } catch (e) {}
            });
        }
        // 從主畫面開啟時：嘗試鎖定橫向
        if (standalone && screen.orientation && screen.orientation.lock) {
            screen.orientation.lock('landscape').catch(function () {});
        }
        // 阻擋雙擊縮放與下拉重新整理
        var lastTouch = 0;
        document.addEventListener('touchend', function (e) {
            var now = Date.now();
            if (now - lastTouch < 300) e.preventDefault();
            lastTouch = now;
        }, { passive: false });
        document.addEventListener('gesturestart', function (e) { e.preventDefault(); });
    })();
    </script>
'''
html = html.replace('    <!-- 電腦版鍵盤滑鼠提示 -->', install_ui + '\n    <!-- 電腦版鍵盤滑鼠提示 -->', 1)
open(f'{OUT}/index.html', 'w').write(html)

# ---------- 5. Tailwind compile ----------
os.makedirs(f'{OUT}/css', exist_ok=True)
open('/home/claude/pwabuild/tw-in.css', 'w').write('@tailwind base;\n@tailwind components;\n@tailwind utilities;\n')
open('/home/claude/pwabuild/tailwind.config.js', 'w').write(f"module.exports = {{ content: ['{OUT}/index.html'], theme: {{ extend: {{}} }}, plugins: [] }};\n")
subprocess.run(['npx', 'tailwindcss', '-c', '/home/claude/pwabuild/tailwind.config.js', '-i', '/home/claude/pwabuild/tw-in.css', '-o', '/home/claude/pwabuild/tw-out.css', '--minify'], cwd='/home/claude/pwabuild', check=True, capture_output=True)
open(f'{OUT}/css/app.css', 'w').write('\n'.join(font_css) + '\n' + open('/home/claude/pwabuild/tw-out.css').read())

# ---------- 6. icons ----------
from PIL import Image, ImageDraw, ImageFont
def make_icon(size, maskable=False):
    img = Image.new('RGB', (size, size), (15, 23, 42))
    d = ImageDraw.Draw(img)
    for y in range(size):
        t = y / size
        r = int(244 * (1 - t) + 14 * t); g = int(63 * (1 - t) + 165 * t); b = int(94 * (1 - t) + 233 * t)
        d.line([(0, y), (size, y)], fill=(r, g, b))
    pad = int(size * (0.2 if maskable else 0.1))
    d.rounded_rectangle([pad, pad, size - pad, size - pad], radius=int(size * 0.12), fill=(15, 23, 42))
    # sun + road
    cx, cy = size // 2, int(size * 0.47)
    rad = int(size * 0.16)
    d.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], fill=(251, 191, 36))
    d.polygon([(cx - int(size * 0.05), size - pad), (cx + int(size * 0.05), size - pad), (cx + int(size * 0.015), cy + rad), (cx - int(size * 0.015), cy + rad)], fill=(56, 189, 248))
    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', int(size * 0.13))
    except Exception:
        font = ImageFont.load_default()
    d.text((cx, int(size * 0.72)), 'VICE', fill=(255, 255, 255), font=font, anchor='mm')
    return img
os.makedirs(f'{OUT}/icons', exist_ok=True)
make_icon(192).save(f'{OUT}/icons/icon-192.png')
make_icon(512).save(f'{OUT}/icons/icon-512.png')
make_icon(512, True).save(f'{OUT}/icons/icon-maskable-512.png')
make_icon(180).save(f'{OUT}/icons/apple-touch-icon.png')

# ---------- 7. manifest ----------
manifest = {
    'name': 'VICE HORIZON VI', 'short_name': 'Vice Horizon', 'description': '開放世界駕駛遊戲 (Three.js + cannon-es)',
    'start_url': './index.html', 'scope': './', 'display': 'fullscreen', 'display_override': ['fullscreen', 'standalone'],
    'orientation': 'landscape', 'background_color': '#0f172a', 'theme_color': '#0f172a',
    'icons': [
        {'src': 'icons/icon-192.png', 'sizes': '192x192', 'type': 'image/png'},
        {'src': 'icons/icon-512.png', 'sizes': '512x512', 'type': 'image/png'},
        {'src': 'icons/icon-maskable-512.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'maskable'}
    ]
}
json.dump(manifest, open(f'{OUT}/manifest.webmanifest', 'w'), ensure_ascii=False, indent=2)

# ---------- 8. service worker (precache every file) ----------
files = []
for root, _, fs in os.walk(OUT):
    for f in fs:
        rel = os.path.relpath(os.path.join(root, f), OUT).replace(os.sep, '/')
        if rel != 'sw.js': files.append('./' + rel)
files.sort()
sw = f'''// VICE HORIZON VI Service Worker：快取優先，第一次載入後可離線遊玩
// 更新遊戲時，把 CACHE 的版本號改掉，玩家下次開啟就會下載新版本
const CACHE = '{VERSION}';
const PRECACHE = {json.dumps(['./'] + files, indent=2)};

self.addEventListener('install', event => {{
    event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(PRECACHE)).then(() => self.skipWaiting()));
}});

self.addEventListener('activate', event => {{
    event.waitUntil(
        caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
            .then(() => self.clients.claim())
    );
}});

self.addEventListener('fetch', event => {{
    if (event.request.method !== 'GET') return;
    event.respondWith(
        caches.match(event.request, {{ ignoreSearch: true }}).then(hit => hit || fetch(event.request).then(res => {{
            if (res && res.ok && new URL(event.request.url).origin === self.location.origin) {{
                const copy = res.clone();
                caches.open(CACHE).then(cache => cache.put(event.request, copy));
            }}
            return res;
        }}))
    );
}});
'''
open(f'{OUT}/sw.js', 'w').write(sw)

# ---------- 9. credits ----------
open(f'{OUT}/CREDITS.txt', 'w').write('''VICE HORIZON VI — 第三方資源
- three.js r160 (MIT) — https://threejs.org
- cannon-es 0.20.0 (MIT) — https://github.com/pmndrs/cannon-es
- 3D 模型 Soldier.glb、Xbot.glb、Michelle.glb、ferrari.glb 與 waternormals.jpg 取自 three.js 官方範例 (examples/models, examples/textures)，版權與授權依原作者，請保留此說明
- 牆面 / 柏油貼圖：Poly Haven (CC0) — red_brick_03、concrete_wall_008、asphalt_02 — https://polyhaven.com\n- 3D 模型：Poly Haven (CC0) — street_lamp_01、painted_wooden_bench、covered_car、barrel_03、water_manhole_cover、modular_urban_apartments_facade；地形貼圖 aerial_grass_rock、rock_face、snow_02\n- 交通車：Kenney Car Kit 3.1 (CC0) — https://kenney.nl\n- Porsche 911 Carrera 4S、Lexus LC 500 Convertible、Ford Shelby GT500 Patrol 車模型由玩家提供 (Sketchfab 下載)，版權與授權依原作者\n- meshoptimizer (MIT) — https://github.com/zeux/meshoptimizer
- 字型：Orbitron、Rajdhani (SIL Open Font License) — Fontsource
''')
size = sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(OUT) for f in fs)
print('files:', len(files) + 1, 'total MB:', round(size / 1e6, 1))
