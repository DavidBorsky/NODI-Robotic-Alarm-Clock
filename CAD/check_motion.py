#!/usr/bin/env python3
"""Independent one-degree motion sweeps and exact hard-stop contact checks.

Separated DOFs are sufficient for these checks: all pitch hardware rotates with
yaw; all fixed parts above the deck lie only in the pan stage. The complete
seven-pose multi-body audit remains in build_nodi.py.
"""
import json
import math
from pathlib import Path

from build_nodi import PARTS, HERE, pose

parts = {p["id"]: p for p in PARTS}


def measure(a, b, yaw=0, pitch=0):
    sa, sb = pose(parts[a], yaw, pitch), pose(parts[b], yaw, pitch)
    return dict(intersection_mm3=sa.intersect(sb).Volume(), distance_mm=sa.distance(sb))


rows = []
for yaw in range(-30, 31):
    for a, b in (("yoke", "base_deck"), ("yoke", "snooze_cap"),
                 ("pan_horn", "pan_servo"), ("yoke", "pan_servo")):
        rows.append(dict(a=a,b=b,yaw_deg=yaw,pitch_deg=0,**measure(a,b,yaw=yaw)))
for pitch in range(-15, 26):
    for a, b in (("head_shell", "yoke"), ("head_shell", "tilt_horn"),
                 ("head_shell", "base_deck"), ("tilt_servo", "yoke"),
                 ("tilt_servo", "tilt_horn"), ("front_bezel", "yoke")):
        rows.append(dict(a=a,b=b,yaw_deg=0,pitch_deg=pitch,**measure(a,b,pitch=pitch)))
hardstops = []
for yaw in (-35,35,-36,36):
    hardstops.append(dict(axis="yaw", angle_deg=yaw,**measure("yoke","base_deck",yaw=yaw)))
for pitch in (-20,30,-21,31):
    hardstops.append(dict(axis="pitch",angle_deg=pitch,**measure("head_shell","yoke",pitch=pitch)))

# Positive clearances only: bearing faces, horn splines, etc intentionally touch.
noncontact = [("yoke","snooze_cap"),("head_shell","yoke"),("head_shell","base_deck"),
              ("tilt_servo","yoke"),("front_bezel","yoke")]
minima = []
for a,b in noncontact:
    selected = [r for r in rows if r["a"]==a and r["b"]==b]
    worst = min(selected,key=lambda r:r["distance_mm"])
    minima.append(worst)
result = dict(units="mm", sweep_step_deg=1, exact_solid_pair_checks=len(rows),
    nonexcluded_intersections=[r for r in rows if r["intersection_mm3"]>0.01],
    minimum_clearances=minima, hardstop_checks=hardstops,
    pass_soft_limit_sweep=all(r["intersection_mm3"]<=0.01 for r in rows),
    pass_hardstops=all(r["intersection_mm3"]<=0.01 if r["angle_deg"] in (-35,35,-20,30)
                      else r["intersection_mm3"]>0.01 for r in hardstops),
    limitations="Discrete 1-degree B-rep sweeps; no cable solids, manufacturing variation or contact forces. At hard limit solids touch; one degree beyond demonstrates intended mechanical interference, not strength validation.")
(HERE / "motion_validation.json").write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps(result,indent=2))
