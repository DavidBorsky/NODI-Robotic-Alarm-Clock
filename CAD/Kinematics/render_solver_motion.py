#!/usr/bin/env python3
"""Render recorded Bullet transforms, never hand-assigned angular poses.
Run with Blender after build_articulated.py. Optional -- --single for one frame.
Temporary PNG frames are written outside the repository to /tmp/nodi-bullet-frames.
Use compose_solver_motion.py with ordinary Python/Pillow for annotated GIF/PNG.
"""
from pathlib import Path
import json
import sys
import tempfile
import bpy
from mathutils import Matrix, Vector
from bpy_extras.object_utils import world_to_camera_view
HERE = Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(HERE / 'NODI_Articulated_RevA.blend'))
scene = bpy.context.scene
scene.rigidbody_world.enabled = False
for obj in scene.objects:
    if obj.rigid_body_constraint:
        obj.hide_render = True
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 8
scene.cycles.use_denoising = True
scene.render.resolution_x = 960
scene.render.resolution_y = 720
scene.render.resolution_percentage = 85
scene.render.image_settings.file_format = 'PNG'
for ob in scene.objects:
    if ob.type == 'LIGHT':
        ob.data.energy = 0
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.91, .95, 1, 1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value = .4
scene.view_settings.view_transform = 'Standard'
# Open the base, deck and head shell. The moving bezel remains visible.
for ident in ('base_cup', 'base_deck', 'head_shell', 'snooze_cap'):
    bpy.data.objects['PART__' + ident].hide_render = True
for ident in ('front_bezel', 'oled_pcb', 'oled_panel', 'oled_active'):
    bpy.data.objects['PART__' + ident].hide_render = False
for mat in bpy.data.materials:
    mat.use_nodes = True
    mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = mat.diffuse_color
    mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = .45
# Contrast the moving pitch servo case against the yaw motor fixed to base.
mat = bpy.data.objects['PART__tilt_servo'].active_material
mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.03, .32, .62, 1)
# Ghost only the yoke to expose its horn behind the upright. Source mesh is unchanged.
# Render-only 0.01 mm outward offset avoids coincident horn/plate surface artifacts.
yoke_obj = bpy.data.objects['PART__yoke']
display_offset = yoke_obj.modifiers.new('Display offset for coincident contact faces only', 'DISPLACE')
display_offset.strength = .00001
display_offset.mid_level = 0
bpy.data.objects['PART__yoke'].visible_shadow = False
yoke_mat = bpy.data.objects['PART__yoke'].active_material
nodes = yoke_mat.node_tree.nodes
links = yoke_mat.node_tree.links
transparent = nodes.new('ShaderNodeBsdfTransparent')
mix = nodes.new('ShaderNodeMixShader')
mix.inputs[0].default_value = .12
links.new(transparent.outputs[0], mix.inputs[1])
links.new(nodes['Principled BSDF'].outputs[0], mix.inputs[2])
links.new(mix.outputs[0], nodes['Material Output'].inputs['Surface'])
for location, power, size in (((.1, -.15, .3), .6, .15), ((-.2, -.08, .16), .3, .2), ((.0, .2, .2), .4, .12)):
    light = bpy.data.lights.new('Studio light', 'AREA')
    light.energy = power
    light.shape = 'DISK'
    light.size = size
    ob = bpy.data.objects.new(light.name, light)
    scene.collection.objects.link(ob)
    ob.location = location
    ob.rotation_euler = (Vector((0, 0, .06)) - ob.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera.location = (.225, -.22, .16)
scene.camera.rotation_euler = (Vector((0, 0, .057)) - scene.camera.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera.data.ortho_scale = .178
frames = Path(tempfile.gettempdir()) / 'nodi-bullet-frames'
frames.mkdir(exist_ok=True)
all_transforms = json.loads((HERE / 'solver_transforms.json').read_text())
# 10 fps samples from the yaw-then-pitch demonstration, plus separately labeled
# enforced-limit examples. Frame IDs are the original solver IDs.
selected = list(range(1, 451, 6))
if '--single' in sys.argv:
    selected = [330]
projections = []
for frame in selected:
    entry = all_transforms[frame - 1]
    for group, name in (('fixed', 'LINK_BASE_grounded'), ('yaw', 'LINK_YOKE_rotates_about_Z'), ('pitch', 'LINK_HEAD_rotates_about_local_X')):
        bpy.data.objects[name].matrix_world = Matrix(entry['transforms_m'][group])
    bpy.context.view_layer.update()
    scene.render.filepath = str(frames / f'frame_{frame:04d}.png')
    if '--resume' not in sys.argv or not Path(scene.render.filepath).is_file():
        bpy.ops.render.render(write_still=True)
    annotation = {'frame': frame, 'targets': {}}
    for ident in ('pan_servo', 'tilt_servo', 'tilt_horn', 'pitch_sleeve', 'pan_horn'):
        ob = bpy.data.objects['PART__' + ident]
        bounds = [ob.matrix_world @ Vector(v) for v in ob.bound_box]
        mid = sum(bounds, Vector()) / 8
        p = world_to_camera_view(scene, scene.camera, mid)
        annotation['targets'][ident] = [p.x * 960, (1 - p.y) * 720]
    projections.append(annotation)
(frames / 'projections.json').write_text(json.dumps(projections))
print('Recorded-transform frames saved in', frames)
