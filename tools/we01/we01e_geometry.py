#!/usr/bin/env python3
"""Claude-owned read-only extractor for the T-016E map geometry sidecar.

Reads the two formal WE-01 runtime dumps and writes map_geometry.json: existing
road segments, Site A footprints, beach and water polygons. No analysis.
Usage: python3 -B tools/we01/we01e_geometry.py PHONE_LOW.json DESKTOP_HIGH.json OUT.json
"""
import hashlib, json, sys

BASE = "84319439243b51aa8d119e33eb62a0637feea887"
FP = {"PHONE_LOW": "e473d222db998487e5fcfb187349e5006e6f619c1d15cca6bae1a2ee380352aa",
      "DESKTOP_HIGH": "52653bc578411a9eda9b314581bb16f45f3cb4eb1be623f9d39dc21ade365482"}


def pick(d):
    w = d["world"]
    segs = [{"id": s["id"], "elevation_type": s["elevation_type"], "centerline": s["centerline"],
             "carriageway_width_m": s["carriageway_width_m"], "sidewalk_left_m": s["sidewalk_left_m"],
             "sidewalk_right_m": s["sidewalk_right_m"]} for s in d["roads"]["segments"]]
    site = [{"id": f["id"], "polygon": f["polygon"], "protected": f["protected"]}
            for f in d["footprints"] if f["category"] == "SITE_A"]
    return {"roads": sorted(segs, key=lambda s: s["id"]), "site_a": sorted(site, key=lambda s: s["id"]),
            "beach_regions": w["beach_regions"], "water_regions": w["water_regions"]}


def main(argv):
    if len(argv) != 4:
        sys.exit(__doc__)
    picked = {}
    for path in argv[1:3]:
        d = json.load(open(path))
        m = d["metadata"]
        if m["base_sha"] != BASE or m["static_fingerprint"] != FP.get(m["preset"]):
            sys.exit(f"{path}: BASE or static fingerprint mismatch")
        picked[m["preset"]] = pick(d)
    if set(picked) != set(FP):
        sys.exit("need one PHONE_LOW and one DESKTOP_HIGH dump")
    if picked["PHONE_LOW"] != picked["DESKTOP_HIGH"]:
        sys.exit("geometry differs between presets; sidecar is only valid for identical geometry")
    out = {"schema_version": 1, "kind": "we01e_map_geometry", "base_sha": BASE,
           "coordinate_unit": "m", "axes": "x right, z down (world x/z)",
           "phone_low_static_fingerprint": FP["PHONE_LOW"],
           "desktop_high_static_fingerprint": FP["DESKTOP_HIGH"],
           "geometry_identical_across_presets": True, **picked["PHONE_LOW"]}
    text = json.dumps(out, sort_keys=True, indent=1) + "\n"
    open(argv[3], "w").write(text)
    print(argv[3], hashlib.sha256(text.encode()).hexdigest(), len(text), "bytes")


if __name__ == "__main__":
    main(sys.argv)
