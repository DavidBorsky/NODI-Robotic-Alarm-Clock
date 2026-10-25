"""Render the exported CAD meshes in Blender; no generated concept geometry.
Usage: blender -b --python tools/render_cad.py -- hero
Run after CAD generation. Source coordinates mm; display graphics are illustrative.
"""
import bpy, json, math, sys
from pathlib import Path
from mathutils import Vector, Matrix
ROOT=Path(__file__).resolve().parents[1]
MODE=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'hero'
MANIFEST=ROOT/'CAD/manifest.json'
data=json.loads(MANIFEST.read_text())
entries=data['instances']
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
scene.render.engine='CYCLES'; scene.cycles.device='CPU'; scene.cycles.samples=24
scene.cycles.use_denoising=True
scene.render.resolution_x=1400; scene.render.resolution_y=1050
if MODE!='hero':
    scene.cycles.samples=12;scene.render.resolution_x=1000;scene.render.resolution_y=750
scene.render.resolution_percentage=100
scene.world.color=(.2,.2,.2)
world=scene.world; world.use_nodes=True
world.node_tree.nodes['Background'].inputs[0].default_value=(.72,.8,.85,1)
world.node_tree.nodes['Background'].inputs[1].default_value=.35
scene.view_settings.view_transform='AgX'
scene.render.image_settings.file_format='PNG'
S=.01
objs=[]
def material(name,color,metal=0,rough=.35):
    mat=bpy.data.materials.new(name); mat.diffuse_color=(*color[:3],1); mat.use_nodes=True
    bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color[:3],1)
    bs.inputs['Roughness'].default_value=rough;bs.inputs['Metallic'].default_value=metal
    return mat
for e in entries:
    path=ROOT/e['stl']
    bpy.ops.wm.stl_import(filepath=str(path),global_scale=S)
    o=bpy.context.object;o.name=e['id'];objs.append(o)
    col=e.get('color',[.65,.72,.72]);o.data.materials.append(material(o.name,col,.7 if e.get('material','').lower() in ['steel','brass','aluminum'] else 0))
    for p in o.data.polygons:p.use_smooth=False
    if MODE=='exploded':o.location+=Vector(e.get('explode',[0,0,0]))*S
    if MODE in ['sleepy','awake','cheerful']:
        pitch={'sleepy':18,'awake':0,'cheerful':-12}[MODE];yaw={'sleepy':-15,'awake':15,'cheerful':-20}[MODE]
        pivot=Vector((0,0,88*S));rot=Matrix.Rotation(math.radians(pitch),4,'X')
        if e.get('group')=='pitch':o.matrix_world=Matrix.Translation(pivot)@rot@Matrix.Translation(-pivot)@o.matrix_world
        if e.get('group') in ['pitch','yaw']:o.matrix_world=Matrix.Rotation(math.radians(yaw),4,'Z')@o.matrix_world
if MODE=='cutaway':
    for o in objs:
        if o.name in ['base_cup','base_deck','front_bezel','head_shell']:o.hide_render=True
# Display emissive artwork added only on top of the CAD display glass. No geometry is hidden.
# Coordinates may be read from manifest to follow display placement.
if MODE!='exploded':
    screen=next(e for e in entries if e['id']=='oled_active');bb=screen['bbox_mm'];disp=data.get('display_artwork',{'center':[(bb['min'][0]+bb['max'][0])/2,bb['min'][1]-.015,(bb['min'][2]+bb['max'][2])/2],'width':29.42,'height':14.7})
    cen=Vector(disp['center'])*S
    tex=ROOT/'Images/display_pixels.png'
    if tex.exists():
        bpy.ops.mesh.primitive_plane_add(size=1,location=cen,rotation=(math.pi/2,0,0))
        o=bpy.context.object;o.name='Illustrative OLED pixels';o.scale=(disp['width']*S,disp['height']*S,1)
        mat=bpy.data.materials.new('128x64 OLED graphic');mat.use_nodes=True;nodes=mat.node_tree.nodes;bs=nodes.get('Principled BSDF')
        img=nodes.new('ShaderNodeTexImage');img.image=bpy.data.images.load(str(tex));img.interpolation='Closest'
        mat.node_tree.links.new(img.outputs['Color'],bs.inputs['Base Color']);mat.node_tree.links.new(img.outputs['Color'],bs.inputs['Emission Color']);bs.inputs['Emission Strength'].default_value=1.8
        bs.inputs['Roughness'].default_value=.28;o.data.materials.append(mat)
        if MODE in ['sleepy','awake','cheerful']:
            bpy.context.view_layer.update()
            pivot=Vector((0,0,88*S));p=math.radians({'sleepy':18,'awake':0,'cheerful':-12}[MODE]);y=math.radians({'sleepy':-15,'awake':15,'cheerful':-20}[MODE]);o.matrix_world=Matrix.Rotation(y,4,'Z')@Matrix.Translation(pivot)@Matrix.Rotation(p,4,'X')@Matrix.Translation(-pivot)@o.matrix_world
# Ground, studio camera and area lighting.
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.04))
bpy.context.object.data.materials.append(material('Backdrop',(.82,.85,.83),0,.7))
def light(name,loc,power,size):
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,.7))-o.location).to_track_quat('-Z','Y').to_euler()
light('Key',(-3,-4,6),450,4);light('Fill',(4,-1,3),230,3);light('Rim',(0,4,4),350,3)
def camera(loc,target,scale):
    d=bpy.data.cameras.new('Camera');o=bpy.data.objects.new('Camera',d);scene.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=scale;scene.camera=o
if MODE=='exploded':camera((3.5,-5,3.4),(0,0,1.05),3.4)
elif MODE=='front':camera((0,-6,1.0),(0,0,.65),1.85)
elif MODE=='side':camera((6,0,1.0),(0,0,.65),1.85)
elif MODE=='top':camera((0,0,6),(0,0,.6),1.8)
else:camera((2.9,-4.7,2.65),(0,0,.65),2.35)
scene.render.filepath=str(ROOT/f'Images/nodi_{MODE}.png')
if MODE=='hero':
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'CAD/nodi_render_scene.blend'))
bpy.ops.render.render(write_still=True)
