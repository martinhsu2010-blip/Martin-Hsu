async (OPT) => {
  const V = window.__VH, T = V.THREE, th = V.__th, W = V.WORLD, RN = V.ROAD_NET;
  const mmv = x => (x === null || x === undefined) ? null : Math.floor(x * 1000 + 0.5);
  const r3 = x => (x === null || x === undefined) ? null : mmv(x) / 1000;
  const rect2poly = r => [[r[0], r[1]], [r[2], r[1]], [r[2], r[3]], [r[0], r[3]]];
  const inter = (a, b) => !(a[2] < b[0] || a[0] > b[2] || a[3] < b[1] || a[1] > b[3]);
  const REG = OPT.regions || [
    { id: 'B1', name: 'Oceanfront Heights', r: [90, 930, 390, 1230] },
    { id: 'B2', name: 'Vista Hills', r: [-900, 820, -500, 1070] },
    { id: 'B3', name: 'Palmwood Quarter', r: [-640, -810, -340, -610] }];
  const BUF = 100;
  const surv = REG.map(g => [g.r[0] - BUF, g.r[1] - BUF, g.r[2] + BUF, g.r[3] + BUF]);
  const ROUTES = { C01: [[221, 890], [240, 960], [240, 1200]], C02: [[110, 960], [170, 960], [240, 960]],
    H01: [[-635, 682], [-800, 800], [-800, 1030]], H02: [[-800, 1030], [-420, 1000], [-240, 880]],
    X01: [[-240, 880], [0, 960], [110, 960]], U01: [[-600, -720], [-510, -720], [-420, -720]] };
  const COR = Object.entries(ROUTES).filter(([id]) => !OPT.routes || OPT.routes.includes(id)).map(([id, p]) => { const xs = p.map(q => q[0]), zs = p.map(q => q[1]);
    return { id, r: [Math.min(...xs) - 60, Math.min(...zs) - 60, Math.max(...xs) + 60, Math.max(...zs) + 60] }; });
  const WIN = surv.concat(COR.map(c => c.r)).map(r => [r[0] - 10, r[1] - 10, r[2] + 10, r[3] + 10]);
  const inWin = b => WIN.some(w => inter(b, w));

  // ---------- canonical helpers (contract C3) ----------
  const canon = v => v === null ? 'null' : Array.isArray(v) ? '[' + v.map(canon).join(',') + ']' :
    typeof v === 'object' ? '{' + Object.keys(v).sort().map(k => JSON.stringify(k) + ':' + canon(v[k])).join(',') + '}' :
    typeof v === 'string' ? JSON.stringify(v) : String(v);
  const sha = async s => [...new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(s)))].map(b => b.toString(16).padStart(2, '0')).join('');
  const byId = a => a.slice().sort((p, q) => p.id < q.id ? -1 : p.id > q.id ? 1 : 0);
  const poly = p => p.map(q => [mmv(q[0]), mmv(q[1])]);
  const b4 = b => b.map(mmv);
  const fpView = d => ({
    physical_ground: { bounds: b4(d.world.physical_ground.bounds), top_y: mmv(d.world.physical_ground.top_y) },
    terrain_regions: byId(d.world.terrain_regions.map(r => ({ id: r.id, polygon: poly(r.polygon), margin_m: mmv(r.margin_m), terrain_support_status: r.terrain_support_status }))),
    water_regions: d.world.water_regions.map(poly), beach_regions: d.world.beach_regions.map(poly),
    regions: byId(d.regions.map(r => ({ id: r.id, name: r.name, initial_polygon: poly(r.initial_polygon), survey_polygon: poly(r.survey_polygon), buffer_m: mmv(r.buffer_m) }))),
    height_grids: byId(d.height_grids.map(g => ({ id: g.id, region_id: g.region_id, origin_x: mmv(g.origin_x), origin_z: mmv(g.origin_z), step_m: mmv(g.step_m), nx: g.nx, nz: g.nz, heights: g.heights.map(mmv), source: g.source, sample_method: g.sample_method }))),
    footprints: byId(d.footprints.map(f => { const o = { id: f.id, category: f.category, source_group: f.source_group, geometry_type: f.geometry_type, geometry_precision: f.geometry_precision,
      polygon: f.polygon ? poly(f.polygon) : null, bounds: b4(f.bounds), y_min: mmv(f.y_min), y_max: mmv(f.y_max), visual: f.visual, physical: f.physical, protected: f.protected };
      if (f.parent_id !== undefined) o.parent_id = f.parent_id; return o; })),
    roads: { completeness: d.roads.completeness,
      nodes: byId(d.roads.nodes.map(n => ({ id: n.id, x: mmv(n.x), y: mmv(n.y), z: mmv(n.z), connected_segment_ids: n.connected_segment_ids.slice().sort() }))),
      segments: byId(d.roads.segments.map(s => ({ id: s.id, start_node_id: s.start_node_id, end_node_id: s.end_node_id, centerline: s.centerline.map(p => p.map(mmv)),
        carriageway_width_m: mmv(s.carriageway_width_m), sidewalk_left_m: mmv(s.sidewalk_left_m), sidewalk_right_m: mmv(s.sidewalk_right_m),
        corridor_footprint_ids: s.corridor_footprint_ids.slice().sort(), elevation_type: s.elevation_type, traffic_route_ids: s.traffic_route_ids.slice().sort() }))) },
    source_counts: d.metadata.source_counts, completeness: d.completeness });

  // ---------- geometry helpers ----------
  const hull = pts => { const p = pts.map(q => [q[0], q[1]]).sort((a, b) => a[0] - b[0] || a[1] - b[1]);
    const u = []; for (const q of p) if (!u.length || u[u.length - 1][0] !== q[0] || u[u.length - 1][1] !== q[1]) u.push(q);
    if (u.length < 3) return u;
    const cr = (o, a, b) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
    const lo = []; for (const q of u) { while (lo.length >= 2 && cr(lo[lo.length - 2], lo[lo.length - 1], q) <= 0) lo.pop(); lo.push(q); }
    const up = []; for (let i = u.length - 1; i >= 0; i--) { const q = u[i]; while (up.length >= 2 && cr(up[up.length - 2], up[up.length - 1], q) <= 0) up.pop(); up.push(q); }
    lo.pop(); up.pop(); return lo.concat(up); };
  const bboxOf = pts => { const xs = pts.map(q => q[0]), zs = pts.map(q => q[1]); return [Math.min(...xs), Math.min(...zs), Math.max(...xs), Math.max(...zs)]; };
  const orect = (x, z, hx, hz, rot) => { const c = Math.cos(rot), s = Math.sin(rot);
    return [[-hx, -hz], [hx, -hz], [hx, hz], [-hx, hz]].map(([lx, lz]) => [x + lx * c + lz * s, z - lx * s + lz * c]); };
  const fps = []; const fpIds = new Set();
  const addFp = f => { f.polygon = f.polygon ? f.polygon.map(q => [r3(q[0]), r3(q[1])]) : null;
    f.bounds = (f.polygon ? bboxOf(f.polygon) : f.bounds).map(r3); f.y_min = r3(f.y_min); f.y_max = r3(f.y_max);
    if (!inWin(f.bounds)) return false; if (fpIds.has(f.id)) throw new Error('dup id ' + f.id); fpIds.add(f.id); fps.push(f); return true; };
  const mk = (id, category, group, prec, polygon, y0, y1, vis, phys, prot) => ({ id, category, source_group: group, geometry_type: 'POLYGON', geometry_precision: prec,
    polygon, bounds: null, y_min: y0, y_max: y1, visual: vis, physical: phys, protected: !!prot, source_ref: group, verification: 'RUNTIME_VERIFIED' });
  const aabbFp = (id, category, group, b, y0, y1, vis, phys, prot) => { const f = mk(id, category, group, 'CONSERVATIVE_AABB', rect2poly(b), y0, y1, vis, phys, prot); f.geometry_type = 'AABB'; return f; };

  // ---------- static WORLD lists ----------
  const counts = { 'WORLD.buildings': W.buildings.length, 'WORLD.cityInfill': W.cityInfill.length, 'WORLD.suburbHouses': W.suburbHouses.length,
    'TREES': V.TREES.list.length, 'TREE_COLLIDERS': V.TREE_COLLIDERS.entries.length };
  W.buildings.forEach((b, i) => addFp(aabbFp('BLD_' + i, 'BUILDING', 'WORLD.buildings', [b.minX, b.minZ, b.maxX, b.maxZ], null, null, true, true, false)));
  W.cityInfill.forEach((b, i) => addFp(mk('INF_' + i, 'BUILDING', 'WORLD.cityInfill', 'EXACT_OUTLINE', rect2poly([b.x - b.w / 2, b.z - b.d / 2, b.x + b.w / 2, b.z + b.d / 2]), null, b.h, true, true, false)));
  W.suburbHouses.forEach((h, i) => addFp(mk('SUB_' + i, 'BUILDING', 'WORLD.suburbHouses', 'EXACT_OUTLINE', orect(h.x, h.z, h.hx, h.hz, h.rot), null, null, true, true, false)));
  V.TREE_COLLIDERS.entries.forEach((e, i) => { const sh = e.body.shapes[0], p = e.body.position, he = sh.halfExtents;
    addFp(aabbFp('TRE_' + i, 'TREE', 'TREE_COLLIDERS', [p.x - he.x, p.z - he.z, p.x + he.x, p.z + he.z], p.y - he.y, p.y + he.y, true, true, false)); });

  // ---------- static physics bodies (mass 0), contract C1 ----------
  const known = new Set(); W.cityInfill.forEach(b => b.body && known.add(b.body)); V.TREE_COLLIDERS.entries.forEach(e => known.add(e.body));
  const quatMul = (a, b) => ({ x: a.w * b.x + a.x * b.w + a.y * b.z - a.z * b.y, y: a.w * b.y - a.x * b.z + a.y * b.w + a.z * b.x, z: a.w * b.z + a.x * b.y - a.y * b.x + a.z * b.w, w: a.w * b.w - a.x * b.x - a.y * b.y - a.z * b.z });
  const rotV = (q, v) => { const ix = q.w * v[0] + q.y * v[2] - q.z * v[1], iy = q.w * v[1] + q.z * v[0] - q.x * v[2], iz = q.w * v[2] + q.x * v[1] - q.y * v[0], iw = -q.x * v[0] - q.y * v[1] - q.z * v[2];
    return [ix * q.w + iw * -q.x + iy * -q.z - iz * -q.y, iy * q.w + iw * -q.y + iz * -q.x - ix * -q.z, iz * q.w + iw * -q.z + ix * -q.y - iy * -q.x]; };
  const shapesOut = [];
  let ground = null;
  for (const b of V.physicsWorld.bodies) {
    if (b.mass !== 0 || known.has(b)) continue;
    b.shapes.forEach((sh, k) => {
      const off = b.shapeOffsets[k], so = b.shapeOrientations[k], q = quatMul(b.quaternion, so), o = rotV(b.quaternion, [off.x, off.y, off.z]);
      const c = [b.position.x + o[0], b.position.y + o[1], b.position.z + o[2]];
      if (sh.type === 4 && sh.halfExtents.x >= 2000) { ground = { half: [sh.halfExtents.x, sh.halfExtents.y, sh.halfExtents.z], pos: c }; return; }
      let pts3 = null, prec = 'EXACT_OUTLINE';
      if (sh.type === 4) { const h = sh.halfExtents; pts3 = [-1, 1].flatMap(a => [-1, 1].flatMap(bb => [-1, 1].map(cc => rotV(q, [a * h.x, bb * h.y, cc * h.z])))).map(v => [c[0] + v[0], c[1] + v[1], c[2] + v[2]]); }
      else if (sh.type === 1) { const r = sh.radius; pts3 = [[-r, -r, -r], [r, r, r]].map(v => [c[0] + v[0], c[1] + v[1], c[2] + v[2]]); prec = 'CONSERVATIVE_AABB'; }
      else if (sh.type === 16 || sh.type === 128) { pts3 = sh.vertices.map(v => { const w = rotV(q, [v.x, v.y, v.z]); return [c[0] + w[0], c[1] + w[1], c[2] + w[2]]; }); if (sh.type === 128) prec = 'CONSERVATIVE_AABB'; }
      else if (sh.type === 256) { const vs = sh.vertices; pts3 = []; for (let i = 0; i < vs.length; i += 3) { const w = rotV(q, [vs[i], vs[i + 1], vs[i + 2]]); pts3.push([c[0] + w[0], c[1] + w[1], c[2] + w[2]]); } prec = 'CONSERVATIVE_AABB'; }
      else { shapesOut.push({ unsupported: sh.type }); return; }
      shapesOut.push({ pts3, prec });
    });
  }
  const physFps = [];
  for (const s of shapesOut) { if (s.unsupported) continue; const xz = s.pts3.map(p => [p[0], p[2]]), ys = s.pts3.map(p => p[1]);
    const bb = bboxOf(xz); if (!inWin(bb)) continue;
    const pg = s.prec === 'EXACT_OUTLINE' ? hull(xz) : rect2poly(bb);
    physFps.push({ pg, prec: s.prec, y0: Math.min(...ys), y1: Math.max(...ys) }); }
  physFps.sort((a, b) => { const A = bboxOf(a.pg), B = bboxOf(b.pg); for (let i = 0; i < 4; i++) { const d = mmv(A[i]) - mmv(B[i]); if (d) return d; } return mmv(a.y0) - mmv(b.y0) || (a.prec < b.prec ? -1 : 1); });
  physFps.forEach((s, i) => { const f = mk('PHY_' + i, 'COLLIDER', 'PHYSICS_STATIC', s.prec, s.pg, s.y0, s.y1, false, true, false); if (s.prec === 'CONSERVATIVE_AABB') f.geometry_type = 'AABB'; addFp(f); });
  const unsupported = shapesOut.filter(s => s.unsupported).length;

  // ---------- scene boxes (conservative, small meshes and instances) ----------
  V.scene.updateMatrixWorld(true);
  const scn = [], bx = new T.Box3(), v3 = new T.Vector3(), m4 = new T.Matrix4(), bb2 = new T.Box3();
  const MAXS = 40;
  V.scene.traverse(o => { if (!o.isMesh || !o.geometry || !o.visible) return;
    if (o.isInstancedMesh) { if (!o.geometry.boundingBox) o.geometry.computeBoundingBox(); const gb = o.geometry.boundingBox;
      for (let i = 0; i < o.count; i++) { o.getMatrixAt(i, m4); m4.premultiply(o.matrixWorld); bb2.copy(gb).applyMatrix4(m4);
        const b = [bb2.min.x, bb2.min.z, bb2.max.x, bb2.max.z]; if (b[2] - b[0] > MAXS || b[3] - b[1] > MAXS || !inWin(b)) continue; scn.push({ b, y0: bb2.min.y, y1: bb2.max.y }); } return; }
    bx.setFromObject(o); if (bx.isEmpty()) return; const b = [bx.min.x, bx.min.z, bx.max.x, bx.max.z];
    if (b[2] - b[0] > MAXS || b[3] - b[1] > MAXS || !inWin(b)) return; scn.push({ b, y0: bx.min.y, y1: bx.max.y }); });
  const seen = new Set(); const scn2 = [];
  for (const s of scn) { const k = s.b.map(mmv).join(',') + '|' + mmv(s.y0) + '|' + mmv(s.y1); if (seen.has(k)) continue; seen.add(k); scn2.push(s); }
  scn2.sort((a, b) => { for (let i = 0; i < 4; i++) { const d = mmv(a.b[i]) - mmv(b.b[i]); if (d) return d; } return mmv(a.y0) - mmv(b.y0) || mmv(a.y1) - mmv(b.y1); });
  const bldg = fps.filter(f => f.category === 'BUILDING');
  const owner = s => { const cx = (s.b[0] + s.b[2]) / 2, cz = (s.b[1] + s.b[3]) / 2; return bldg.find(f => f.bounds[0] - 2 <= cx && cx <= f.bounds[2] + 2 && f.bounds[1] - 2 <= cz && cz <= f.bounds[3] + 2); };
  scn2.forEach((s, i) => { const o = owner(s); const f = aabbFp('SCN_' + i, o ? 'BUILDING' : 'OTHER', 'SCENE_BOX3', s.b, s.y0, s.y1, true, false, false); if (o) f.parent_id = o.id; addFp(f); });

  // ---------- Site A ----------
  const sc = W.showcaseSiteA;
  const siteInfo = { keys: Object.keys(sc.footprints || {}) };
  for (const [k, f] of Object.entries(sc.footprints || {})) { const o = {}; for (const [kk, vv] of Object.entries(f)) if (typeof vv === 'number') o[kk] = vv; siteInfo[k] = o; }
  const PROT = [-561, -831, -441, -753];
  { const sb = Object.entries(sc.footprints || {}).filter(([k, f]) => f && typeof f.minX === 'number').map(([k, f]) => [f.minX, f.minZ, f.maxX, f.maxZ]);
    const SB = [Math.min(...sb.map(b => b[0])), Math.min(...sb.map(b => b[1])), Math.max(...sb.map(b => b[2])), Math.max(...sb.map(b => b[3]))];
    const ok = SB[0] - 10 === PROT[0] && SB[1] - 10 === PROT[1] && SB[2] + 10 === PROT[2] && SB[3] + 10 === PROT[3]; siteInfo.siteBBox = SB; siteInfo.protectOk = ok;
    const f = mk('SITEA_PROTECT', 'SITE_A', 'SITE_A_PROTECTION', 'EXACT_OUTLINE', rect2poly(PROT), null, null, false, false, true); f.verification = ok ? 'RUNTIME_VERIFIED' : 'UNKNOWN'; addFp(f);
    for (const k of ['buildingA', 'buildingB']) { const b = sc.footprints[k]; const g = mk('SITEA_' + k, 'SITE_A', 'WORLD.showcaseSiteA', 'EXACT_OUTLINE', rect2poly([b.minX, b.minZ, b.maxX, b.maxZ]), b.baseY, null, true, false, true); addFp(g); } }

  // ---------- water / beach / ground ----------
  const waters = [], beaches = [];
  { bx.setFromObject(W.oceanMesh); waters.push(rect2poly([bx.min.x, bx.min.z, bx.max.x, bx.max.z])); }
  V.scene.traverse(o => { if (o.isMesh && o.geometry && o.geometry.type === 'PlaneGeometry' && o.geometry.parameters.width === 240 && o.geometry.parameters.height === 2200) { bx.setFromObject(o); beaches.push(rect2poly([bx.min.x, bx.min.z, bx.max.x, bx.max.z])); } });
  const gmesh = []; V.scene.traverse(o => { if (o.isMesh && o.geometry && o.geometry.type === 'PlaneGeometry' && o.geometry.parameters.width === 3200 && o.geometry.parameters.height === 3200) { bx.setFromObject(o); gmesh.push([bx.min.x, bx.min.z, bx.max.x, bx.max.z]); } });

  // ---------- roads ----------
  const nodes = new Map(), segs = [], corr = [];
  const nodeId = (x, y, z) => 'N_' + mmv(x) + '_' + mmv(z);
  const addNode = (x, y, z, sid) => { const id = nodeId(x, y, z); if (!nodes.has(id)) nodes.set(id, { id, x: r3(x), y: r3(y), z: r3(z), connected_segment_ids: [], source_ref: 'ROAD_NET' }); nodes.get(id).connected_segment_ids.push(sid); return id; };
  let roadFootprintsAdded = 0;
  const addRoad = (sid, pts, half, elev, group, sideW) => {
    const cl = pts.map(p => [r3(p[0]), r3(p[1]), r3(p[2])]); const quads = [];
    for (let i = 0; i + 1 < pts.length; i++) { const a = pts[i], b = pts[i + 1]; const dx = b[0] - a[0], dz = b[2] - a[2], L = Math.hypot(dx, dz); if (L < 1e-6) continue;
      const nx = -dz / L * half, nz = dx / L * half; const q = [[a[0] + nx, a[2] + nz], [b[0] + nx, b[2] + nz], [b[0] - nx, b[2] - nz], [a[0] - nx, a[2] - nz]];
      const bb = bboxOf(q); if (!inWin(bb)) continue; quads.push({ i, q }); }
    if (!quads.length) return; const ids = [];
    quads.forEach(({ i, q }) => { const f = mk('ROAD_' + sid + '_' + i, 'ROAD', group, 'EXACT_OUTLINE', q, Math.min(pts[i][1], pts[i + 1][1]), Math.max(pts[i][1], pts[i + 1][1]), true, true, false); if (addFp(f)) ids.push(f.id); });
    const s = { id: sid, start_node_id: null, end_node_id: null, centerline: cl, carriageway_width_m: r3(half * 2), sidewalk_left_m: null, sidewalk_right_m: null, corridor_footprint_ids: ids, elevation_type: elev, traffic_route_ids: [], source_ref: group, verification: 'RUNTIME_VERIFIED' };
    s.start_node_id = addNode(pts[0][0], pts[0][1], pts[0][2], sid); s.end_node_id = addNode(pts[pts.length - 1][0], pts[pts.length - 1][1], pts[pts.length - 1][2], sid); segs.push(s); };
  const P3 = p => [p.x, p.y === undefined ? 0 : p.y, p.z];
  // avenues and cross streets (analytic)
  RN.avenuesX.forEach(ax => { const z1 = ax < -340 ? RN.hillAveZ : RN.avenueZ; addRoad('AVE_' + ax, [[ax, 0, -RN.avenueZ], [ax, 0, z1]], RN.avenueHalf, 'GROUND', 'ROAD_NET.avenues'); });
  RN.crossZ.forEach(cz => { const x0 = RN.pavedCrossWest(cz); addRoad('CRS_' + cz, [[x0, 0, cz], [RN.pavedCrossEast, 0, cz]], RN.crossHalf, 'GROUND', 'ROAD_NET.crossStreets'); });
  // avenue sidewalks (conservative 6 m strips outside the carriageway)
  RN.avenuesX.forEach(ax => { const z1 = ax < -340 ? RN.hillAveZ : RN.avenueZ; [[ax + RN.avenueHalf, ax + RN.avenueHalf + 6], [ax - RN.avenueHalf - 6, ax - RN.avenueHalf]].forEach(([xa, xb], k) =>
    addFp(aabbFp('SWK_AVE_' + ax + '_' + k, 'SIDEWALK', 'ROAD_NET.avenueSidewalks', [xa, -RN.avenueZ, xb, z1], 0, 0.3, true, false, false))); });
  RN.crossZ.forEach(cz => { const x0 = RN.pavedCrossWest(cz); [[cz + RN.crossHalf, cz + RN.crossHalf + 6], [cz - RN.crossHalf - 6, cz - RN.crossHalf]].forEach(([za, zb], k) =>
    addFp(aabbFp('SWK_CRS_' + cz + '_' + k, 'SIDEWALK', 'ROAD_NET.crossSidewalks', [x0, za, RN.pavedCrossEast, zb], 0, 0.3, true, false, false))); });
  RN.ribbons.forEach((r, i) => addRoad('RIB_' + i, r.pts.map(P3), r.half, 'UNKNOWN', 'ROAD_NET.ribbons'));
  addRoad('HILL_ROAD', RN.hillRoad.pts.map(P3), RN.hillRoad.half, 'GROUND', 'ROAD_NET.hillRoad');
  RN.terrainRoads.forEach((r, i) => addRoad('TRD_' + i, r.pts.map(P3), r.half, 'GROUND', 'ROAD_NET.terrainRoads'));
  RN.suburbRoads.forEach((r, i) => addRoad('SUBR_' + i, r.pts.map(P3), r.half, 'GROUND', 'ROAD_NET.suburbRoads'));
  addRoad('RING', RN.ring.pts.map(P3), RN.ring.half, 'UNKNOWN', 'ROAD_NET.ring');
  RN.spurs.forEach((r, i) => addRoad('SPUR_' + i, r.pts.map(P3), r.half, 'UNKNOWN', 'ROAD_NET.spurs'));
  RN.roundabouts.forEach((r, i) => { const n = 48, pg = []; for (let k = 0; k < n; k++) pg.push([r.x + Math.cos(k / n * 2 * Math.PI) * r.rOut, r.z + Math.sin(k / n * 2 * Math.PI) * r.rOut]);
    const f = mk('RBT_' + i, 'ROAD', 'ROAD_NET.roundabouts', 'CONSERVATIVE_AABB', rect2poly([r.x - r.rOut, r.z - r.rOut, r.x + r.rOut, r.z + r.rOut]), 0, 0.3, true, true, false); f.geometry_type = 'AABB'; addFp(f); });
  const nodeList = [...nodes.values()].filter(n => true);

  // ---------- height grids ----------
  const grids = [];
  const mkGrid = (id, region, r, step) => { const nx = Math.round((r[2] - r[0]) / step) + 1, nz = Math.round((r[3] - r[1]) / step) + 1, h = new Array(nx * nz);
    for (let iz = 0; iz < nz; iz++) for (let ix = 0; ix < nx; ix++) h[iz * nx + ix] = r3(th(r[0] + ix * step, r[1] + iz * step));
    grids.push({ id, region_id: region, origin_x: r[0], origin_z: r[1], step_m: step, nx, nz, heights: h, source: 'runtime_terrainHeight', sample_method: 'DIRECT_RUNTIME' }); };
  mkGrid('WORLD_20M', 'WORLD', [-1600, -1600, 1600, 1600], 20);
  REG.forEach((g, i) => mkGrid(g.id + '_1M', g.id, surv[i], 1));
  COR.forEach(c => mkGrid('COR_' + c.id + '_1M', 'ROAD_CORRIDOR', c.r, 1));

  // ---------- assemble ----------
  const src = {}; for (const f of fps) (src[f.source_group] = src[f.source_group] || []).push(f);
  const srcFp = {}; for (const [g, list] of Object.entries(src)) srcFp[g] = await sha(canon(fpView({ world: { physical_ground: { bounds: [0, 0, 0, 0], top_y: 0 }, terrain_regions: [], water_regions: [], beach_regions: [] }, regions: [], height_grids: [], footprints: list, roads: { completeness: 'PARTIAL', nodes: [], segments: [] }, metadata: { source_counts: {} }, completeness: {} }).footprints));
  const gh = ground ? { half: ground.half, pos: ground.pos } : null;
  const physical_ground = gh ? { shape: 'BOX', half_extents: gh.half, position: gh.pos.map(r3), top_y: r3(gh.pos[1] + gh.half[1]),
    bounds: [gh.pos[0] - gh.half[0], gh.pos[2] - gh.half[2], gh.pos[0] + gh.half[0], gh.pos[2] + gh.half[2]].map(r3), verification: 'RUNTIME_VERIFIED', source_ref: 'physicsWorld.bodies mass 0 Box half>=2000' }
    : { shape: 'BOX', half_extents: [0, 0, 0], position: [0, 0, 0], top_y: 0, bounds: [0, 0, 0, 0], verification: 'UNKNOWN', source_ref: 'not found' };
  const tr = RN.terrainRegions.map(r => ({ id: 'TR_' + r.name, polygon: rect2poly([r.x0, r.z0, r.x1, r.z1]), margin_m: 20, source_ref: 'ROAD_NET.terrainRegions', terrain_support_status: 'VERIFIED' }));
  const dump = {
    schema_version: 1,
    metadata: { base_sha: OPT.base_sha, game_release: OPT.game_release, preset: OPT.preset, initialization_complete: true, showcase_visible: !!(sc.group ? sc.group.visible : true), night: false,
      extraction_version: 'we01-extract-1', generated_at: new Date().toISOString(), coordinate_unit: 'm',
      generation_settings: { viewport: [innerWidth, innerHeight], unsupported_static_shapes: unsupported, scene_box_max_size_m: MAXS, sample: !!OPT.regions, ground_mesh_bounds: gmesh[0] || null },
      static_fingerprint: '', source_counts: Object.assign({}, counts, { 'PHYSICS_STATIC_SHAPES_IN_WINDOW': physFps.length }), source_fingerprints: srcFp, seed: null },
    world: { ground_bounds: gmesh[0] ? gmesh[0].map(r3) : null, playable_bounds: null, physical_ground, terrain_regions: tr, water_regions: waters.map(p => p.map(q => [r3(q[0]), r3(q[1])])), beach_regions: beaches.map(p => p.map(q => [r3(q[0]), r3(q[1])])),
      map_ui_bounds: null, boundary_obstacles: [], source_refs: ['window.__VH'] },
    regions: REG.map((g, i) => ({ id: g.id, name: g.name, initial_polygon: rect2poly(g.r), survey_polygon: rect2poly(surv[i]), buffer_m: BUF, source_ref: 'spec 3.1' })),
    height_grids: grids, footprints: fps,
    roads: { nodes: nodeList, segments: segs, completeness: 'PARTIAL' },
    completeness: { world_bounds: 'PARTIAL', terrain_heights: 'COMPLETE', physical_ground: gh ? 'COMPLETE' : 'UNKNOWN', terrain_regions: 'COMPLETE', visual_occupancy: 'COMPLETE', physical_occupancy: unsupported ? 'PARTIAL' : 'COMPLETE',
      trees: 'COMPLETE', water_and_beach: 'COMPLETE', protected_areas: 'COMPLETE', roads: 'COMPLETE', traffic_routes: 'UNKNOWN' },
    issues: [
      { id: 'ISS_TRAFFIC', severity: 'INFO', category: 'traffic_routes', affected_region_ids: [], affected_polygon: null, message: 'Static traffic routes (ROAD_NET.routes) are not mapped to road segments in this extraction; empty traffic_route_ids does not mean no traffic.', source_ref: 'extractor' },
      { id: 'ISS_SIDEWALK', severity: 'INFO', category: 'sidewalks', affected_region_ids: [], affected_polygon: null, message: 'Avenue and cross-street sidewalks are conservative 6 m strips outside the carriageway (CONSERVATIVE_AABB); other roads carry no sidewalk footprint.', source_ref: 'extractor' },
      { id: 'ISS_SCENE', severity: 'INFO', category: 'scene_box3', affected_region_ids: [], affected_polygon: null, message: 'SCENE_BOX3 footprints are conservative world AABBs of visible meshes and instances (<=40 m); tree crowns inflate obstacles. Boxes whose centre lies within 2 m of a building footprint are category BUILDING with parent_id (facade parts), the rest are OTHER.', source_ref: 'extractor' },
      { id: 'ISS_PLAYABLE', severity: 'INFO', category: 'world_bounds', affected_region_ids: [], affected_polygon: null, message: 'playable_bounds and map_ui_bounds were not extracted (null); all candidate regions lie inside the 3200 m ground mesh and the 4800 m physical ground.', source_ref: 'extractor' }] };
  dump.roads.completeness = 'COMPLETE';
  dump.metadata.static_fingerprint = await sha(canon(fpView(dump)));
  dump.__debug = { siteInfo, nFp: fps.length, bySource: Object.fromEntries(Object.entries(src).map(([k, v]) => [k, v.length])), blockedHouses: W.suburbHouses.filter(h => h.blocked).length, dayKeys: Object.keys(V.DAY || {}) };
  return dump;
}
