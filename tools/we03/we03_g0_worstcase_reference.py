#!/usr/bin/env python3
"""Claude G0 reference calculation for WE-03 v1.0 review (analytic, NOT a renderer measurement).
Method (so T-018A1 can reproduce it exactly): 57 WE-02 plan parcels (phase<=2) at their bounds centres;
viewpoints on a 20 m grid x[-1100,600), z[-1000,1400); a building counts at LOD0/LOD1/LOD2 when the centre
distance is <= the preset radius; triangles = draft caps per prototype. Mode 'omni' counts every direction
(upper bound on resident geometry); mode 'cone' keeps only buildings inside a horizontal view cone
(best heading per viewpoint, 15 deg steps). No fog, occlusion, shadow pass, or building height."""
import json, math, sys
plan = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "specs/we02/district_plan.json"))
TRI = {"R01": (12000, 3000, 300), "R02": (20000, 5000, 600), "R05": (5000, 1200, 150), "R08": (8000, 2000, 240)}
PRESETS = {"PHONE_LOW": (100, 250, 650), "TABLET_MED": (140, 350, 850), "DESKTOP_HIGH": (200, 500, 1200)}
ps = [p for p in plan["parcels"] if p["phase"] <= 2]
pts = [((p["bounds_internal"][0] + p["bounds_internal"][2]) / 2, (p["bounds_internal"][1] + p["bounds_internal"][3]) / 2, p["prototype_id"]) for p in ps]
def tri(gx, gz, r, half=None, heading=0.0):
    t = 0
    for x, z, pr in pts:
        d = math.hypot(x - gx, z - gz)
        if d > r[2]: continue
        if half is not None and d > 1e-9:
            a = math.atan2(z - gz, x - gx)
            if abs((a - heading + math.pi) % (2 * math.pi) - math.pi) > half: continue
        t += TRI[pr][0 if d <= r[0] else 1 if d <= r[1] else 2]
    return t
for name, r in PRESETS.items():
    om = max((tri(gx, gz, r), gx, gz) for gx in range(-1100, 600, 20) for gz in range(-1000, 1400, 20))
    half = math.radians(96) / 2
    co = max((tri(gx, gz, r, half, math.radians(h)), gx, gz, h) for gx in range(-1100, 600, 20) for gz in range(-1000, 1400, 20) for h in range(0, 360, 15))
    print(f"{name}: omni {om[0]} at ({om[1]},{om[2]}); 96deg cone {co[0]} at ({co[1]},{co[2]}) heading {co[3]}")
