# WE-01 dump schema v1 — field notes for the analyzer (Claude-owned fixtures)

Spec: `specs/WE-01-spec-v1.2.md` (§5 schema, conditions C1-C6). These notes describe what the **real** extractor (`tools/we01/`) emits; if they disagree with the spec text, tell Claude, do not guess.

## Files
- `sample_phone_low.json`, `sample_desktop_high.json`: real runtime data from BASE `84319439243b51aa8d119e33eb62a0637feea887` (`vh-2026-11-27-02`), but with **three small sample regions** (B1/B2/B3 ids, 40x40 m initial, +100 m survey buffer) and only corridor `U01`, so they stay ~1 MB. `metadata.generation_settings.sample = true`.
- `fingerprint_reference.py`: reference implementation of the C3 fingerprint (Python). Both samples verify with it (`python3 fingerprint_reference.py <dump.json>` prints `True`). The extractor computes the same value in JavaScript, so the contract is already proven JS = Python on full dumps.
- Full dumps (`world_phone_low.json`, `world_desktop_high.json`, ~4.4 / 5.4 MB each, three real regions B1/B2/B3) are produced by Claude and never committed.

## Do not hardcode
- Region ids, polygons, buffer, grid origins, corridor ids and sizes come **from the dump** (the sample uses other rectangles than the spec). Only the rules (buffer 100, step 1 m for B*/corridor grids, step 20 m for WORLD) are fixed.
- Validate grids against their own `origin/step/nx/nz` and against the region `survey_polygon` they belong to (`B*_1M` grids must cover it exactly; `COR_*` grids are free rectangles).

## Conventions
- Metres, at most 3 decimals. Bounds are arrays `[xmin, zmin, xmax, zmax]`. Polygons are `[[x,z],...]` without repeating the first point.
- `height_grids[].heights` is row-major `index = iz*nx + ix`, x = origin_x + ix*step, z = origin_z + iz*step. Heights come straight from runtime `terrainHeight` (`DIRECT_RUNTIME`).
- Footprint ids are ASCII and unique. `geometry_type` is `POLYGON` (outline) or `AABB` (rectangle polygon from a bounding box).
- Terrain regions (`TR_*`) carry `margin_m = 20` (terrain height is blended up to 20 m outside the region rectangle).
- Physical ground: Box half extents [2400, 0.5, 2400] at [0, -0.5, 0], top y = 0, bounds [-2400,-2400,2400,2400], `RUNTIME_VERIFIED`. Ground mesh bounds in `metadata.generation_settings.ground_mesh_bounds` (3200 m square).

## Source groups in `footprints[].source_group`
| group | category | precision | notes |
|---|---|---|---|
| `WORLD.buildings` | BUILDING | CONSERVATIVE_AABB | minX/maxX/minZ/maxZ |
| `WORLD.cityInfill` | BUILDING | EXACT_OUTLINE | x,z,w,d box; `y_max` = h |
| `WORLD.suburbHouses` | BUILDING | EXACT_OUTLINE | oriented rectangle (visual wall box); physics boxes are 0.3 m larger per side |
| `TREE_COLLIDERS` | TREE | CONSERVATIVE_AABB | trunk collider box (all trees, not only the active pool) |
| `PHYSICS_STATIC` | COLLIDER | EXACT_OUTLINE for boxes/convex, CONSERVATIVE_AABB for cylinders/spheres/trimesh | physicsWorld bodies with mass 0, per shape; duplicates of infill/tree bodies and the ground box removed; `visual=false`, `physical=true` |
| `SCENE_BOX3` | OTHER | CONSERVATIVE_AABB | visible meshes and instances up to 40 m wide; **inflates** obstacles (tree crowns, facade windows, lamps); `visual=true`, `physical=false` |
| `ROAD_NET.*` | ROAD | EXACT_OUTLINE per segment quad (roundabout: AABB) | carriageway only: avenues (half 12), cross streets (half 11), ribbons, hillRoad, terrainRoads, suburbRoads, ring, spurs |
| `ROAD_NET.avenueSidewalks` / `crossSidewalks` | SIDEWALK | CONSERVATIVE_AABB | 6 m strips outside the carriageway; other roads have no sidewalk footprint |
| `SITE_A_PROTECTION` | SITE_A | EXACT_OUTLINE | `protected=true`, X[-561,-441] Z[-831,-753]; equals the runtime Site A bounding box +10 m (`RUNTIME_VERIFIED`) |
| `WORLD.showcaseSiteA` | SITE_A | EXACT_OUTLINE | buildings A and B, `protected=true` |

Only objects intersecting a survey rectangle or a corridor rectangle (+10 m) are emitted; the cut-off is part of the fingerprint.

## Roads
`roads.segments` hold the centerlines (`[x,y,z]`), widths and corridor footprint ids; nodes are segment endpoints (id from mm coordinates, so crossing roads are not merged into junction nodes). `traffic_route_ids` is always empty and `completeness.traffic_routes = UNKNOWN` (static routes are not mapped yet); empty does not mean "no traffic". `elevation_type` is `UNKNOWN` for ribbons, ring and spurs.

## Completeness and issues
`world_bounds = PARTIAL` (`playable_bounds`, `map_ui_bounds` are null) and `traffic_routes = UNKNOWN`; everything the land analysis needs is `COMPLETE`. `issues[]` has four INFO items describing the conservative choices above (ISS_TRAFFIC, ISS_SIDEWALK, ISS_SCENE, ISS_PLAYABLE).

## Fingerprint contract (C3), summary
Input view = physical_ground bounds/top_y, terrain_regions, water/beach polygons, regions, height_grids, footprints (without `source_ref`/`verification`), roads (without `source_ref`/`verification`), `metadata.source_counts`, `completeness`. All metric numbers -> integer mm with `floor(x*1000+0.5)`; `nx`, `nz`, counts stay; lists with `id` sorted by id; canonical JSON `sort_keys=True, separators=(",", ":")`; SHA-256 hex of the UTF-8 bytes. `fingerprint_reference.py` is the exact definition; a change in any included value must change the fingerprint (test A17), a change in `generated_at`, `issues`, `source_ref` or `seed` must not.
