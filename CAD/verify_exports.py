#!/usr/bin/env python3
"""Read committed assembly STEP files and every STL; record portable QA evidence."""
import hashlib
import itertools
import json
from pathlib import Path

import cadquery as cq
import trimesh

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
manifest_path = HERE / "manifest.json"
manifest = json.loads(manifest_path.read_text())
assemblies = []
for name in ("NODI_Assembly_RevA.step", "NODI_Exploded_RevA.step"):
    shape = cq.importers.importStep(str(HERE / "exports" / name)).val()
    assemblies.append(dict(file="CAD/exports/"+name, valid=shape.isValid(),
                           solid_count=len(shape.Solids()),
                           expected_solids=len(manifest["instances"])))
meshes = []
for path in sorted((HERE / "exports").rglob("*.stl")):
    mesh = trimesh.load_mesh(path, process=True)
    meshes.append(dict(file=str(path.relative_to(ROOT)),watertight=bool(mesh.is_watertight),
                       winding_consistent=bool(mesh.is_winding_consistent),
                       vertices=len(mesh.vertices),triangles=len(mesh.faces),
                       positive_volume=bool(mesh.volume>0)))
# Audit all neutral-pose bodies, including fastener heads. Only the explicitly
# mapped smooth-shank/thread-pilot pairs can have positive intersection volume.
thread_engagements = {}
for p in manifest["instances"]:
    ident = p["id"]
    for prefix,target in (("deck_screw_","base_cup"),("bezel_screw_","head_shell"),
                          ("oled_screw_","front_bezel"),("pan_mount_screw_","base_cup"),
                          ("tilt_mount_screw_","head_shell"),("pan_horn_screw_","pan_horn"),
                          ("tilt_horn_screw_","tilt_horn"),("rear_screw_","base_cup"),
                          ("power_screw_","base_cup"),("switch_screw_","base_cup"),
                          ("ballast_screw_","base_cup")):
        if ident.startswith(prefix):
            thread_engagements[tuple(sorted((ident,target)))] = "Nominal smooth shank in smaller thread pilot; thread geometry omitted."
for a,b in (("pitch_bolt","pitch_nut"),("pan_retaining_screw","pan_servo"),
            ("tilt_retaining_screw","tilt_servo")):
    thread_engagements[tuple(sorted((a,b)))] = "Nominal smooth shank in simplified nut/motor threaded bore; thread geometry omitted."
solids = {p["id"]:cq.importers.importStep(str(ROOT / p["step"])).val() for p in manifest["instances"]}
clashes,engagements = [],[]
for (a,sa),(b,sb) in itertools.combinations(solids.items(),2):
    ba,bb = sa.BoundingBox(),sb.BoundingBox()
    if (ba.xmax<=bb.xmin+1e-6 or bb.xmax<=ba.xmin+1e-6 or
        ba.ymax<=bb.ymin+1e-6 or bb.ymax<=ba.ymin+1e-6 or
        ba.zmax<=bb.zmin+1e-6 or bb.zmax<=ba.zmin+1e-6):
        continue
    volume = sa.intersect(sb).Volume()
    if volume>0.01:
        row = dict(a=a,b=b,intersection_mm3=volume)
        reason = thread_engagements.get(tuple(sorted((a,b))))
        if reason:
            engagements.append(dict(**row,exclusion=reason))
        else:
            clashes.append(row)
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
result = dict(manifest_sha256=sha(manifest_path),source_sha256=sha(HERE / "build_nodi.py"),
    parameters_sha256=sha(HERE / "parameters.json"), assemblies=assemblies,
    meshes=meshes, stl_file_count=len(meshes),
    neutral_audit_nonexcluded_intersections=clashes,
    neutral_audit_explicit_thread_engagements=engagements,
    pass_neutral_all_body_audit=not clashes,
    pass_assemblies=all(a["valid"] and a["solid_count"]==a["expected_solids"] for a in assemblies),
    pass_stl_readback=all(m["watertight"] and m["winding_consistent"] and m["positive_volume"] for m in meshes))
(HERE / "export_validation.json").write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps({k:v for k,v in result.items() if k not in ("meshes",)},indent=2))
assert result["pass_assemblies"] and result["pass_stl_readback"] and result["pass_neutral_all_body_audit"], "Export verification failed; inspect export_validation.json"
