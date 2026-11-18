"""把上傳的車模型 (.blend / .fbx) 轉成遊戲用的 GLB：
- 車頭朝 glTF +Z、地面 y = 0、軸距中點在原點，左側為 +X (與 Kenney 車、物理輪胎一致)
- 四顆輪子拆成 wheel_fl / wheel_fr / wheel_rl / wheel_rr 節點，原點在輪心
- 減面、縮小貼圖、輸出 WebP 貼圖
用法: python3 -I convert_car.py '<json 設定>'
"""
import bpy, bmesh, sys, json, os, math
from mathutils import Vector, Matrix

cfg = json.loads(sys.argv[-1])
src = cfg['src']
bpy.ops.wm.read_factory_settings(use_empty=True)
if src.endswith('.blend'):
    bpy.ops.wm.open_mainfile(filepath=src)
else:
    bpy.ops.import_scene.fbx(filepath=src)

def tri_count(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)

def matches(name, pats):
    return any(name == p or (p.endswith('*') and name.startswith(p[:-1])) or (p.startswith('~') and p[1:].lower() in name.lower()) for p in pats)

# 1) 套用修改器 (鏡像、骨架)、解除父子關係並套用變換，讓頂點變成世界座標
for o in list(bpy.data.objects):
    if o.type in ('LIGHT', 'CAMERA'):
        bpy.data.objects.remove(o, do_unlink=True)
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
bpy.ops.object.select_all(action='DESELECT')
for o in meshes:
    o.hide_set(False); o.hide_viewport = False; o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
bpy.ops.object.convert(target='MESH')
bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
for o in list(bpy.data.objects):
    if o.type != 'MESH':
        bpy.data.objects.remove(o, do_unlink=True)
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
for o in meshes:
    o.data = o.data.copy() if o.data.users > 1 else o.data
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# 2) 刪掉不要的物件 (地板、背景、展示球、燈光、引擎…)
meshes_all = [o for o in bpy.data.objects if o.type == 'MESH']
for o in list(meshes_all):
    if matches(o.name, cfg.get('drop', [])):
        bpy.data.objects.remove(o, do_unlink=True)
    elif len(o.data.polygons) == 0:
        bpy.data.objects.remove(o, do_unlink=True)

meshes = [o for o in bpy.data.objects if o.type == 'MESH']

# 3) 把指定材質的面 (輪胎、鋼圈、碟盤) 從車身拆出來
wheel_objs = [o for o in meshes if matches(o.name, cfg.get('wheel_objs', []))]
if cfg.get('wheel_mats'):
    for o in list(meshes):
        if o in wheel_objs:
            continue
        idx = [i for i, m in enumerate(o.data.materials) if m and matches(m.name, cfg['wheel_mats'])]
        if not idx:
            continue
        if all(p.material_index in idx for p in o.data.polygons):
            wheel_objs.append(o); continue
        bpy.ops.object.select_all(action='DESELECT')
        o.select_set(True); bpy.context.view_layer.objects.active = o
        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(o.data)
        for f in bm.faces:
            f.select = f.material_index in idx
        bmesh.update_edit_mesh(o.data)
        bpy.ops.mesh.separate(type='SELECTED')
        bpy.ops.object.mode_set(mode='OBJECT')
        new = [x for x in bpy.context.selected_objects if x != o]
        wheel_objs += new
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
body_objs = [o for o in meshes if o not in wheel_objs]

def bbox(objs):
    mn = Vector((1e9, 1e9, 1e9)); mx = Vector((-1e9, -1e9, -1e9))
    for o in objs:
        for v in o.data.vertices:
            c = o.matrix_world @ v.co
            mn = Vector(map(min, mn, c)); mx = Vector(map(max, mx, c))
    return mn, mx

# 4) 方向：先把車身長軸轉到 Y，車頭轉到 -Y (= glTF +Z)
mn, mx = bbox(body_objs)
ctr = (mn + mx) / 2
front = cfg.get('front')
if not front:
    # 用尾燈 (紅色燈罩) 判斷車尾
    long_axis = 1 if (mx.y - mn.y) > (mx.x - mn.x) else 0
    acc, n = 0.0, 0
    for o in body_objs:
        for p in o.data.polygons:
            m = o.data.materials[p.material_index] if o.data.materials else None
            if m and 'red' in m.name.lower():
                acc += (o.matrix_world @ p.center)[long_axis] - ctr[long_axis]; n += 1
    rear_sign = 1 if acc > 0 else -1
    front = ('-' if rear_sign > 0 else '+') + 'XY'[long_axis]
    print('[auto] tail lights at', 'XY'[long_axis], rear_sign, '-> front', front)
rotz = {'-Y': 0, '+Y': math.pi, '+X': -math.pi / 2, '-X': math.pi / 2}[front]
R = Matrix.Rotation(rotz, 4, 'Z') @ Matrix.Translation(-ctr)
for o in meshes:
    o.matrix_world = R @ o.matrix_world
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# 5) 縮放到真實車長
mn, mx = bbox(body_objs + wheel_objs)
s = cfg['length'] / (mx.y - mn.y)
for o in meshes:
    o.matrix_world = Matrix.Scale(s, 4) @ o.matrix_world
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
print('[scale]', round(s, 4), 'dims', tuple(round(v * s, 2) for v in (mx - mn)))

# 6) 輪子：拆成零件，依前後左右分四組
bpy.ops.object.select_all(action='DESELECT')
for o in wheel_objs:
    o.select_set(True)
bpy.context.view_layer.objects.active = wheel_objs[0]
if len(wheel_objs) > 1:
    bpy.ops.object.join()
W = bpy.context.view_layer.objects.active
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.separate(type='LOOSE'); bpy.ops.object.mode_set(mode='OBJECT')
parts = list(bpy.context.selected_objects)
groups = {'fl': [], 'fr': [], 'rl': [], 'rr': []}
max_wheel = cfg.get('max_wheel', 0.95)
for p in parts:
    a, b = bbox([p])
    c = (a + b) / 2
    if max(b - a) > max_wheel or abs(c.x) < 0.25:
        bpy.data.objects.remove(p, do_unlink=True)  # 跑到原點的多餘輪子
        continue
    key = ('f' if c.y < 0 else 'r') + ('l' if c.x > 0 else 'r')
    groups[key].append(p)
wheels = {}
for key, objs in groups.items():
    assert objs, 'missing wheel ' + key
    big = max(objs, key=lambda o: (lambda a, b: (b - a).z)(*bbox([o])))  # 最大的零件 = 輪胎
    a, b = bbox([big])
    center, radius = (a + b) / 2, (b.z - a.z) / 2
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    if len(objs) > 1:
        bpy.ops.object.join()
    w = bpy.context.view_layer.objects.active
    w.name = 'wheel_' + key
    # 原檔前輪可能是打方向的：用俯視投影的主成分找輪軸，轉回正前方
    pts = [w.matrix_world @ v.co for v in w.data.vertices]
    mx_ = sum(p.x for p in pts) / len(pts); my_ = sum(p.y for p in pts) / len(pts)
    sxx = sum((p.x - mx_) ** 2 for p in pts); syy = sum((p.y - my_) ** 2 for p in pts); sxy = sum((p.x - mx_) * (p.y - my_) for p in pts)
    ang = 0.5 * math.atan2(2 * sxy, sxx - syy)  # 長軸 (滾動方向) 角度
    steer = ang - math.pi / 2 if ang > 0 else ang + math.pi / 2  # 滾動方向應該沿 Y
    if abs(math.degrees(steer)) > 4 and abs(math.degrees(steer)) < 40:
        piv = Matrix.Translation(center) @ Matrix.Rotation(-steer, 4, 'Z') @ Matrix.Translation(-center)
        w.matrix_world = piv @ w.matrix_world
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        print('[steer fix]', key, round(math.degrees(steer), 1), 'deg')
        a, b = bbox([w]); center = Vector(((a.x + b.x) / 2, (a.y + b.y) / 2, center.z))
    wheels[key] = (w, center, radius)

# 7) 平移：地面 z=0、左右置中、軸距中點 y=0
r = sum(v[2] for v in wheels.values()) / 4
cz = sum(v[1].z for v in wheels.values()) / 4
cx = sum(v[1].x for v in wheels.values()) / 4
fy = (wheels['fl'][1].y + wheels['fr'][1].y) / 2
ry = (wheels['rl'][1].y + wheels['rr'][1].y) / 2
T = Matrix.Translation(Vector((-cx, -(fy + ry) / 2, -(cz - r))))
for o in [o for o in bpy.data.objects if o.type == 'MESH']:
    o.matrix_world = T @ o.matrix_world
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
info = {'radius': round(r, 3), 'wheels': {}}
for key, (w, c, rad) in wheels.items():
    c2 = T @ c
    bpy.context.scene.cursor.location = c2
    bpy.ops.object.select_all(action='DESELECT'); w.select_set(True); bpy.context.view_layer.objects.active = w
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    info['wheels'][key] = [round(c2.x, 3), round(c2.z, 3), round(-c2.y, 3)]  # glTF 座標 (x, y, z)

# 8) 減面
body_objs = [o for o in bpy.data.objects if o.type == 'MESH' and not o.name.startswith('wheel_')]
def decimate(objs, target):
    tot = sum(tri_count(o) for o in objs)
    small = sum(tri_count(o) for o in objs if tri_count(o) < 1200)
    big = tot - small
    if tot <= target or big == 0:
        return tot
    ratio = max(0.06, min(1.0, (target - small) / big))
    for o in objs:
        if tri_count(o) < 1200:
            continue
        rr = ratio * cfg.get('ratio_boost', {}).get(next((k for k in cfg.get('ratio_boost', {}) if k.lower() in o.name.lower()), ''), 1.0)
        m = o.modifiers.new('dec', 'DECIMATE'); m.ratio = min(1.0, rr); m.use_collapse_triangulate = True
        bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
        bpy.ops.object.modifier_apply(modifier='dec')
    return sum(tri_count(o) for o in objs)
info['bodyTris'] = decimate(body_objs, cfg.get('body_tris', 60000))
info['wheelTris'] = sum(decimate([w], cfg.get('wheel_tris', 3000)) for w, _, _ in wheels.values())

# 車身合併成一個物件 (材質分開成 primitive)
bpy.ops.object.select_all(action='DESELECT')
for o in body_objs:
    o.select_set(True)
bpy.context.view_layer.objects.active = body_objs[0]
bpy.ops.object.join()
bpy.context.view_layer.objects.active.name = 'body'

# 9a) 材質整理：非玻璃材質一律不透明 (FBX 匯入會把貼圖 alpha 接到透明度，車門會變半透明)、金屬度歸零
GLASS = ('glass', 'wind', 'window')
for m in bpy.data.materials:
    ov = cfg.get('mat_override', {}).get(m.name)
    if ov:
        m.use_nodes = True
        nt = m.node_tree
        for n in list(nt.nodes):
            nt.nodes.remove(n)
        out = nt.nodes.new('ShaderNodeOutputMaterial')
        bs = nt.nodes.new('ShaderNodeBsdfPrincipled')
        nt.links.new(bs.outputs[0], out.inputs[0])
        bs.inputs['Base Color'].default_value = (*ov[:3], 1)
        bs.inputs['Metallic'].default_value = ov[3]
        bs.inputs['Roughness'].default_value = ov[4]
        bs.inputs['Alpha'].default_value = ov[5] if len(ov) > 5 else 1.0
        continue
    if not m.use_nodes:
        continue
    nt = m.node_tree
    bs = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if not bs:
        continue
    if not any(k in m.name.lower() for k in GLASS):
        for l in list(bs.inputs['Alpha'].links):
            nt.links.remove(l)
        bs.inputs['Alpha'].default_value = 1.0
    if not bs.inputs['Metallic'].links:
        bs.inputs['Metallic'].default_value = 0.0

# 9) 補上原檔沒接的貼圖 (Porsche)
tex_dir = cfg.get('tex_dir')
for mname, links in cfg.get('tex_links', {}).items():
    m = bpy.data.materials.get(mname)
    if not m:
        continue
    m.use_nodes = True
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    for sock, fname in links.items():
        img = bpy.data.images.load(os.path.join(tex_dir, fname))
        tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = img
        if sock == 'Normal':
            img.colorspace_settings.name = 'Non-Color'
            nm = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(tn.outputs[0], nm.inputs['Color']); nt.links.new(nm.outputs[0], bsdf.inputs['Normal'])
        elif sock == 'Emission':
            nt.links.new(tn.outputs[0], bsdf.inputs['Emission Color']); bsdf.inputs['Emission Strength'].default_value = 1.0
        else:
            nt.links.new(tn.outputs[0], bsdf.inputs[sock])
            if sock == 'Base Color' and tn.outputs.get('Alpha') and cfg.get('alpha_from_tex', {}).get(mname):
                nt.links.new(tn.outputs['Alpha'], bsdf.inputs['Alpha'])

# 10) 縮小貼圖
max_tex = cfg.get('max_tex', 1024)
for img in bpy.data.images:
    if not img.has_data:
        try: img.reload()
        except Exception: pass
    if img.size[0] == 0:
        continue
    lim = max_tex // 2 if ('_n' in img.name.lower() or 'normal' in img.name.lower()) else max_tex
    w, h = img.size
    if max(w, h) > lim:
        k = lim / max(w, h)
        img.scale(max(1, int(w * k)), max(1, int(h * k)))

bpy.ops.export_scene.gltf(filepath=cfg['out'], export_format='GLB', export_image_format='WEBP', export_image_quality=82,
                          export_yup=True, export_apply=True, export_animations=False, export_skins=False, export_morph=False,
                          export_cameras=False, export_lights=False)
info['size_kb'] = os.path.getsize(cfg['out']) // 1024
print('[INFO]', json.dumps(info))
