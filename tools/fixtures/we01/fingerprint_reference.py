import json, math, hashlib, sys
def mm(x): return None if x is None else math.floor(x*1000+0.5)
def poly(p): return [[mm(a), mm(b)] for a, b in p]
def by_id(a): return sorted(a, key=lambda o: o["id"])
def view(d):
    f = []
    for x in d["footprints"]:
        o = {k: x[k] for k in ("id","category","source_group","geometry_type","geometry_precision","visual","physical","protected")}
        o["polygon"] = poly(x["polygon"]) if x["polygon"] else None
        o["bounds"] = [mm(v) for v in x["bounds"]]; o["y_min"] = mm(x["y_min"]); o["y_max"] = mm(x["y_max"])
        if "parent_id" in x: o["parent_id"] = x["parent_id"]
        f.append(o)
    w = d["world"]; r = d["roads"]
    return {
      "physical_ground": {"bounds": [mm(v) for v in w["physical_ground"]["bounds"]], "top_y": mm(w["physical_ground"]["top_y"])},
      "terrain_regions": by_id([{"id": t["id"], "polygon": poly(t["polygon"]), "margin_m": mm(t["margin_m"]), "terrain_support_status": t["terrain_support_status"]} for t in w["terrain_regions"]]),
      "water_regions": [poly(p) for p in w["water_regions"]], "beach_regions": [poly(p) for p in w["beach_regions"]],
      "regions": by_id([{"id": g["id"], "name": g["name"], "initial_polygon": poly(g["initial_polygon"]), "survey_polygon": poly(g["survey_polygon"]), "buffer_m": mm(g["buffer_m"])} for g in d["regions"]]),
      "height_grids": by_id([{"id": g["id"], "region_id": g["region_id"], "origin_x": mm(g["origin_x"]), "origin_z": mm(g["origin_z"]), "step_m": mm(g["step_m"]), "nx": g["nx"], "nz": g["nz"], "heights": [mm(h) for h in g["heights"]], "source": g["source"], "sample_method": g["sample_method"]} for g in d["height_grids"]]),
      "footprints": by_id(f),
      "roads": {"completeness": r["completeness"],
        "nodes": by_id([{"id": n["id"], "x": mm(n["x"]), "y": mm(n["y"]), "z": mm(n["z"]), "connected_segment_ids": sorted(n["connected_segment_ids"])} for n in r["nodes"]]),
        "segments": by_id([{"id": s["id"], "start_node_id": s["start_node_id"], "end_node_id": s["end_node_id"], "centerline": [[mm(v) for v in p] for p in s["centerline"]], "carriageway_width_m": mm(s["carriageway_width_m"]), "sidewalk_left_m": mm(s["sidewalk_left_m"]), "sidewalk_right_m": mm(s["sidewalk_right_m"]), "corridor_footprint_ids": sorted(s["corridor_footprint_ids"]), "elevation_type": s["elevation_type"], "traffic_route_ids": sorted(s["traffic_route_ids"])} for s in r["segments"]])},
      "source_counts": d["metadata"]["source_counts"], "completeness": d["completeness"]}
def fingerprint(d):
    return hashlib.sha256(json.dumps(view(d), sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
if __name__ == "__main__":
    for p in sys.argv[1:]:
        d = json.load(open(p)); print(p.split("/")[-1], fingerprint(d) == d["metadata"]["static_fingerprint"], fingerprint(d)[:16])
