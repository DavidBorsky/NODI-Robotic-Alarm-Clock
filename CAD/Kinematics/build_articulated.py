#!/usr/bin/env python3
"""Build and execute an articulated NODI mesh assembly in Blender 4.5 LTS.
Run: blender --background --factory-startup --python CAD/Kinematics/build_articulated.py
No body placements are keyframed. Bullet integrates angular motors subject to hinges.
"""
from pathlib import Path
import csv
import hashlib
import json
import math
import sys
import xml.etree.ElementTree as ET

import bpy
from mathutils import Matrix, Vector

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
MANIFEST = ROOT / 'CAD/manifest.json'
data = json.loads(MANIFEST.read_text())
S = 0.001  # input meshes mm, Bullet/URDF m
FPS = 60
END = 780
# Velocities in child-relative-parent coordinates; velocity motors, not MG90S dynamics.
PHASES = [
    (1, 30, 'Neutral', 0, 0),
    (31, 90, 'Yaw: base motor turns horn and yoke', 25, 0),
    (91, 210, 'Yaw: return through neutral', -25, 0),
    (211, 270, 'Yaw: return to neutral', 25, 0),
    (271, 330, 'Pitch: horn stays on yoke; case and head rotate', 0, 20),
    (331, 420, 'Pitch: reverse relative case rotation', 0, -20),
    (421, 450, 'Pitch: return to neutral', 0, 20),
    (451, 510, 'Yaw: software travel limit +30 degrees', 90, 0),
    (511, 570, 'Yaw: software travel limit -30 degrees', -90, 0),
    (571, 590, 'Yaw: return to neutral', 90, 0),
    (591, 650, 'Pitch: software travel limit +25 degrees', 0, 90),
    (651, 710, 'Pitch: software travel limit -15 degrees', 0, -90),
    (711, 720, 'Pitch: return to neutral', 0, 90),
    (721, 780, 'Neutral hold', 0, 0),
]

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.name = 'NODI | Bullet articulated assembly | Rev A'
scene.frame_start = 1
scene.frame_end = END
scene.render.fps = FPS
scene.unit_settings.system = 'METRIC'
scene.unit_settings.length_unit = 'MILLIMETERS'
scene.gravity = (0, 0, 0)
scene['validation_scope'] = 'Ideal joint constraint solver test. Zero gravity; pair collisions disabled; no MG90S torque/gear/friction/cable model.'
scene['playback'] = 'Press Space from frame 1. Yaw first, pitch second, then software-angle limit tests. Only motor velocity is animated.'
scene['source_manifest_sha256'] = hashlib.sha256(MANIFEST.read_bytes()).hexdigest()

visuals = bpy.data.collections.new('CAD components | 67 fixed memberships')
scene.collection.children.link(visuals)
rigids = bpy.data.collections.new('Three ideal rigid links')
scene.collection.children.link(rigids)
constraints = bpy.data.collections.new('Two hinges and two angular motors')
scene.collection.children.link(constraints)

def move_collection(obj, collection):
    for old in list(obj.users_collection):
        if scene.rigidbody_world and old in (scene.rigidbody_world.collection, scene.rigidbody_world.constraints):
            continue
        old.objects.unlink(obj)
    collection.objects.link(obj)


def material(name, color):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (*color, 1)
    m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = .55
    return m


bodies = {}
for index, group in enumerate(('fixed', 'yaw', 'pitch')):
    members = [p for p in data['instances'] if p['group'] == group]
    com = Vector(data['mass_properties'][group]['com_mm']) * S
    mins = Vector(tuple(min(p['bbox_mm']['min'][i] for p in members) * S for i in range(3)))
    maxs = Vector(tuple(max(p['bbox_mm']['max'][i] for p in members) * S for i in range(3)))
    bpy.ops.mesh.primitive_cube_add(size=1, location=com)
    obj = bpy.context.object
    obj.name = {'fixed': 'LINK_BASE_grounded', 'yaw': 'LINK_YOKE_rotates_about_Z', 'pitch': 'LINK_HEAD_rotates_about_local_X'}[group]
    # Symmetric inertia proxy centered on estimated COM; no collision/torque claims.
    obj.dimensions = maxs - mins
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bpy.ops.rigidbody.object_add()
    rb = obj.rigid_body
    rb.type = 'PASSIVE' if group == 'fixed' else 'ACTIVE'
    rb.mass = data['mass_properties'][group]['mass_g'] / 1000
    rb.collision_shape = 'BOX'
    rb.use_deactivation = False
    rb.linear_damping = 0
    rb.angular_damping = 0
    rb.collision_collections = [i == index for i in range(20)]
    rb.use_margin = True
    rb.collision_margin = 0.00001
    obj.hide_render = True
    obj.display_type = 'WIRE'
    obj['membership'] = ', '.join(p['id'] for p in members)
    obj['inertia_basis'] = 'Bounding box approximation at manifest estimated COM; unvalidated, not vendor mass properties.'
    move_collection(obj, rigids)
    bodies[group] = obj

# All original component meshes are rigid members, retaining individually named objects.
for p in data['instances']:
    bpy.ops.wm.stl_import(filepath=str(ROOT / p['stl']))
    obj = bpy.context.object
    obj.name = 'PART__' + p['id']
    for v in obj.data.vertices:
        v.co *= S
    obj.parent = bodies[p['group']]
    obj.matrix_parent_inverse = Matrix.Identity(4)
    obj.location = -Vector(data['mass_properties'][p['group']]['com_mm']) * S
    obj.data.materials.append(material(p['id'], p['color']))
    obj['part_id'] = p['id']
    obj['fixed_to_link'] = p['group']
    obj['editable_source'] = '../build_nodi.py'
    move_collection(obj, visuals)

bpy.context.view_layer.update()
world = scene.rigidbody_world
world.substeps_per_frame = 20
world.solver_iterations = 100
world.point_cache.frame_start = 1
world.point_cache.frame_end = END


def constraint(name, kind, a, b, point, rotation):
    obj = bpy.data.objects.new(name, None)
    constraints.objects.link(obj)
    obj.location = Vector(point)
    obj.rotation_euler = rotation
    obj.empty_display_size = 0.014
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.rigidbody.constraint_add()
    obj.select_set(False)
    c = obj.rigid_body_constraint
    c.type = kind
    c.object1 = bodies[a]
    c.object2 = bodies[b]
    c.disable_collisions = True
    return obj


# A hinge's Blender local Z is the revolute axis. Bullet's limit sign is inverse
# to the child-relative-parent angle reported below; verify both with measured motion.
yaw_anchor = Vector((0, 0, .034))
pitch_anchor = Vector((0, 0, .088))
yh = constraint('JOINT_YAW | base to yoke | Z', 'HINGE', 'fixed', 'yaw', yaw_anchor, (0, 0, 0))
ph = constraint('JOINT_PITCH | yoke to head | X', 'HINGE', 'yaw', 'pitch', pitch_anchor, (0, math.pi / 2, 0))
for ob, lo, hi in ((yh, -30, 30), (ph, -15, 25)):
    c = ob.rigid_body_constraint
    c.use_limit_ang_z = True
    c.limit_ang_z_lower = math.radians(-hi)
    c.limit_ang_z_upper = math.radians(-lo)
    ob['reported_child_relative_parent_limits_deg'] = [lo, hi]
    ob['scope'] = 'Software operating envelope only. Mechanical hard stops at yaw +/-35 and pitch -20/+30 are not contact-simulated.'

# A Blender MOTOR uses local X for its angular axis.
ym = constraint('MOTOR_YAW | servo case fixed to base', 'MOTOR', 'fixed', 'yaw', yaw_anchor, (0, -math.pi / 2, 0))
pm = constraint('MOTOR_PITCH | horn fixed to yoke; case fixed to head', 'MOTOR', 'yaw', 'pitch', pitch_anchor, (0, 0, 0))
for index, ob in enumerate((ym, pm)):
    c = ob.rigid_body_constraint
    c.use_motor_ang = True
    c.motor_ang_max_impulse = .01
    ob['motor_basis'] = 'Arbitrary ideal velocity actuator impulse, not measured MG90S torque.'
    for start, end, label, yaw_v, pitch_v in PHASES:
        c.motor_ang_target_velocity = -math.radians((yaw_v, pitch_v)[index])
        c.keyframe_insert(data_path='motor_ang_target_velocity', frame=start)
    for curve in ob.animation_data.action.fcurves:
        for key in curve.keyframe_points:
            key.interpolation = 'CONSTANT'

for start, end, label, yv, pv in PHASES:
    scene.timeline_markers.new(label, frame=start)

# Neutral local joint connectors are stored separately on each participating body.
neutral = {g: ob.matrix_world.copy() for g, ob in bodies.items()}
connectors = {
    'yaw': ('fixed', 'yaw', yaw_anchor, Vector((0, 0, 1))),
    'pitch': ('yaw', 'pitch', pitch_anchor, Vector((1, 0, 0))),
}
local = {}
for name, (pa, ch, point, axis) in connectors.items():
    local[name] = (neutral[pa].inverted() @ point,
                   neutral[ch].inverted() @ point,
                   neutral[pa].to_3x3().inverted() @ axis,
                   neutral[ch].to_3x3().inverted() @ axis)

# Native scene is saved before solving so it starts in a clean neutral frame.
# Non-rendered rigid proxies remain selectable for inspection in the outliner.
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 16
scene.cycles.use_denoising = True
scene.render.resolution_x = 1080
scene.render.resolution_y = 800
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.display.shading.light = 'STUDIO'
scene.display.shading.studio_light = 'paint.sl'
scene.display.shading.color_type = 'MATERIAL'
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.display.shading.cavity_type = 'BOTH'
scene.display.shading.background_type = 'WORLD'
scene.world.color = (.94, .96, .98)
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.91, .95, 1, 1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value = .4
scene.view_settings.view_transform = 'Standard'
for location, power, size in (((.1, -.15, .3), .6, .15), ((-.2, -.08, .16), .3, .2), ((.0, .2, .2), .4, .12)):
    light = bpy.data.lights.new('Native studio light', 'AREA')
    light.energy = power
    light.shape = 'DISK'
    light.size = size
    ob = bpy.data.objects.new(light.name, light)
    scene.collection.objects.link(ob)
    ob.location = location
    ob.rotation_euler = (Vector((0, 0, .06)) - ob.location).to_track_quat('-Z', 'Y').to_euler()
cam_data = bpy.data.cameras.new('Mechanism_Camera')
cam = bpy.data.objects.new('Mechanism_Camera', cam_data)
scene.collection.objects.link(cam)
cam.location = (.195, -.26, .15)
target = Vector((0, 0, .06))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
cam_data.type = 'ORTHO'
cam_data.ortho_scale = .18
scene.camera = cam

# Native file retains the full assembly; the separate render script makes a cutaway.
help_text = bpy.data.texts.new('START_HERE_NODI')
help_text.write('NODI: start at frame 1, then press Space.\nThree rigid links, two HINGE constraints and two angular MOTOR constraints.\nBody poses are solved by Bullet; only motor velocities are keyed.\nSee CAD/Kinematics/README.md for scope and assumptions.\nZero gravity; pair contacts disabled; horn grip and sleeve restraint idealized.\nThis is a mesh assembly, not parametric solid CAD.\n')
scene.frame_set(1)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            space = area.spaces.active
            space.region_3d.view_location = (0, 0, .06)
            space.region_3d.view_distance = .24
            space.region_3d.view_rotation = cam.rotation_euler.to_quaternion()
            space.clip_start = .0001
            space.clip_end = 10
            space.shading.color_type = 'MATERIAL'
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(HERE / 'NODI_Articulated_RevA.blend'))

records = []
matrices = []
for frame in range(1, END + 1):
    scene.frame_set(frame)
    dg = bpy.context.evaluated_depsgraph_get()
    transforms = {g: ob.evaluated_get(dg).matrix_world.copy() for g, ob in bodies.items()}
    row = {'frame': frame, 'time_s': (frame - 1) / FPS}
    for name, (pa, ch, point, axis) in connectors.items():
        mp, mc = transforms[pa], transforms[ch]
        pp, cp, pax, cax = local[name]
        origin_error = (mp @ pp - mc @ cp).length / S
        axp = (mp.to_3x3() @ pax).normalized()
        axc = (mc.to_3x3() @ cax).normalized()
        axis_error = math.atan2(axp.cross(axc).length, axp.dot(axc))
        rotation = mp.to_quaternion().conjugated() @ mc.to_quaternion()
        axis_index = 2 if name == 'yaw' else 0
        angle = math.degrees(2 * math.atan2(rotation[axis_index + 1], rotation.w))
        row[name + '_deg'] = angle
        row[name + '_origin_error_mm'] = origin_error
        row[name + '_axis_error_deg'] = math.degrees(axis_error)
    row['phase'] = next(p[2] for p in PHASES if p[0] <= frame <= p[1])
    records.append(row)
    matrices.append({'frame': frame, 'transforms_m': {g: [list(r) for r in m] for g, m in transforms.items()}})
    if frame % 120 == 0:
        print('BULLET', json.dumps(row), flush=True)
with (HERE / 'solver_motion.csv').open('w', newline='') as fh:
    writer = csv.DictWriter(fh, fieldnames=list(records[0]))
    writer.writeheader()
    writer.writerows(records)
(HERE / 'solver_transforms.json').write_text(json.dumps(matrices, separators=(',', ':')) + '\n')

summary = {
    'status': 'PASS' if all(abs(r[n + '_origin_error_mm']) < .05 and abs(r[n + '_axis_error_deg']) < .1 for r in records for n in ('yaw', 'pitch')) else 'FAIL',
    'solver': 'Blender 4.5.3 LTS built-in Bullet rigid-body constraint solver',
    'blender_version': bpy.app.version_string,
    'source_manifest_sha256': scene['source_manifest_sha256'],
    'source_meshes_sha256': {p['id']: hashlib.sha256((ROOT / p['stl']).read_bytes()).hexdigest() for p in data['instances']},
    'frames_executed': len(records), 'fps': FPS, 'rigid_links': 3,
    'visual_component_meshes': len(data['instances']), 'revolute_constraints': 2,
    'angular_velocity_motors': 2, 'gravity_m_s2': [0, 0, 0],
    'body_transforms_keyframed': False, 'motor_velocity_keyframes_only': True,
    'substeps_per_frame': world.substeps_per_frame,
    'solver_iterations': world.solver_iterations,
    'constraints': {},
    'scope': 'Actual numerical ideal joint solver run. Not physical prototype validation, vendor servo dynamics, contact, spline strength, bearing friction, cable routing, fatigue, or FEA.',
    'inertia': 'Bounding box proxies at estimated manifest COM, approximate. Not used to substantiate torque/acceleration.',
    'collisions': 'Disabled between the three ideal links; existing CAD B-rep discrete collision audit is a separate check.',
    'coupling_assumptions': [
        'MG90S spline and drilled horn grip are ideal rigid couplings; spline teeth are not modeled and vendor interface requires sample measurement.',
        'Pitch servo case is rigidly fastened to head while its horn/rotor is held by yoke: inverse drive.',
        'Passive sleeve centerline is ideal revolute support; sleeve antirotation/clamping and axial retention require assembly validation.',
        'All fixed component memberships are modeled rigid; snooze switch travel and flexible wires are omitted.',
        'Combined purchased servo case/output envelope remains intact and axisymmetric output does not show separate rotor spin. Internal gears/rotor are omitted.',
        'URDF limits represent operating envelope, not physical stop contact.',
    ],
}
for n, lo, hi in (('yaw', -30, 30), ('pitch', -15, 25)):
    angles = [r[n + '_deg'] for r in records]
    info = {
        'operating_limits_deg': [lo, hi], 'measured_range_deg': [min(angles), max(angles)],
        'max_origin_error_mm': max(r[n + '_origin_error_mm'] for r in records),
        'max_axis_error_deg': max(r[n + '_axis_error_deg'] for r in records),
        'limits_exercised': min(angles) < lo + .1 and max(angles) > hi - .1,
        'pass_limit_bounds_with_0p1_deg_tolerance': min(angles) >= lo - .1 and max(angles) <= hi + .1,
    }
    summary['constraints'][n] = info
    if not info['limits_exercised'] or not info['pass_limit_bounds_with_0p1_deg_tolerance']:
        summary['status'] = 'FAIL'
(HERE / 'solver_validation.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary, indent=2), flush=True)

# URDF references genuine source STL files in assembly coordinates, with explicit
# fixed memberships. URDF receives mm->m scale and the same two-joint graph.
robot = ET.Element('robot', {'name': 'NODI_revision_A_ideal_articulated'})
ET.SubElement(robot, 'link', {'name': 'base_link'})
ET.SubElement(robot, 'link', {'name': 'yaw_link'})
ET.SubElement(robot, 'link', {'name': 'head_link'})
for name, parent, child, xyz, axis, limits in (
    ('yaw_revolute', 'base_link', 'yaw_link', '0 0 0.034', '0 0 1', (-30, 30)),
    ('pitch_revolute', 'yaw_link', 'head_link', '0 0 0.054', '1 0 0', (-15, 25)),
):
    joint = ET.SubElement(robot, 'joint', {'name': name, 'type': 'revolute'})
    ET.SubElement(joint, 'parent', {'link': parent})
    ET.SubElement(joint, 'child', {'link': child})
    ET.SubElement(joint, 'origin', {'xyz': xyz, 'rpy': '0 0 0'})
    ET.SubElement(joint, 'axis', {'xyz': axis})
    # Kinematics-only URDF: zero effort/velocity prevents accidental dynamic actuation.
    # No commercial servo performance limits are asserted by this description.
    ET.SubElement(joint, 'limit', {'lower': str(math.radians(limits[0])), 'upper': str(math.radians(limits[1])), 'effort': '0', 'velocity': '0'})
for p in data['instances']:
    link = ET.SubElement(robot, 'link', {'name': p['id']})
    visual = ET.SubElement(link, 'visual')
    geometry = ET.SubElement(visual, 'geometry')
    ET.SubElement(geometry, 'mesh', {'filename': '../exports/meshes/' + p['id'] + '.stl', 'scale': '.001 .001 .001'})
    m = ET.SubElement(visual, 'material', {'name': p['id'] + '_material'})
    ET.SubElement(m, 'color', {'rgba': ' '.join(map(str, p['color'])) + ' 1'})
    joint = ET.SubElement(robot, 'joint', {'name': 'fixed__' + p['id'], 'type': 'fixed'})
    parent = {'fixed': 'base_link', 'yaw': 'yaw_link', 'pitch': 'head_link'}[p['group']]
    ET.SubElement(joint, 'parent', {'link': parent})
    ET.SubElement(joint, 'child', {'link': p['id']})
    z = {'fixed': 0, 'yaw': -.034, 'pitch': -.088}[p['group']]
    ET.SubElement(joint, 'origin', {'xyz': '0 0 ' + str(z), 'rpy': '0 0 0'})
ET.indent(robot, space='  ')
ET.ElementTree(robot).write(HERE / 'NODI_Articulated_RevA.urdf', encoding='utf-8', xml_declaration=True)

# Save pose-independent output: animation render script uses recorded solver
# transforms for reproducible images without rerunning or replacing the solver.
if summary['status'] != 'PASS':
    raise RuntimeError('Bullet joint validation failed; inspect solver_validation.json')
