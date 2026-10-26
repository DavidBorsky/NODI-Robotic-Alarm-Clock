#!/usr/bin/env python3
"""Independently audit URDF tree and compare FK with recorded Bullet transforms.
Uses only Python standard library; no Blender or CadQuery dependency.
"""
from pathlib import Path
import csv
import hashlib
import json
import math
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
manifest_path = HERE.parent / 'manifest.json'
manifest = json.loads(manifest_path.read_text())
validation = json.loads((HERE / 'solver_validation.json').read_text())
robot = ET.parse(HERE / 'NODI_Articulated_RevA.urdf').getroot()
links = {x.attrib['name']: x for x in robot.findall('link')}
joints = robot.findall('joint')
parents = {x.find('child').attrib['link']: x.find('parent').attrib['link'] for x in joints}
assert len(links) == 70 and len(joints) == 69
assert len(parents) == 69, 'Each nonroot link must have exactly one parent'
assert set(links) - set(parents) == {'base_link'}
assert sum(j.attrib['type'] == 'revolute' for j in joints) == 2
assert sum(j.attrib['type'] == 'fixed' for j in joints) == 67
assert validation['status'] == 'PASS'
assert hashlib.sha256(manifest_path.read_bytes()).hexdigest() == validation['source_manifest_sha256']
for j in joints:
    assert j.find('parent').attrib['link'] in links
    assert j.find('child').attrib['link'] in links
    node = j.find('child').attrib['link']
    seen = set()
    while node in parents:
        assert node not in seen, 'Cycle in URDF'
        seen.add(node)
        node = parents[node]
    assert node == 'base_link'
for p in manifest['instances']:
    assert hashlib.sha256((HERE.parent.parent / p['stl']).read_bytes()).hexdigest() == validation['source_meshes_sha256'][p['id']]
for mesh in robot.findall('.//mesh'):
    assert (HERE / mesh.attrib['filename']).is_file(), mesh.attrib['filename']
    assert [float(v) for v in mesh.attrib['scale'].split()] == [.001, .001, .001]


def eye():
    return [[float(i == j) for j in range(4)] for i in range(4)]


def mm(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def translate(xyz):
    m = eye()
    for i, v in enumerate(xyz):
        m[i][3] = v
    return m


def rotate(axis, angle):
    m = eye()
    i, j = ((1, 2) if axis == [1., 0., 0.] else (0, 1))
    c, s = math.cos(angle), math.sin(angle)
    m[i][i], m[j][j], m[i][j], m[j][i] = c, c, -s, s
    return m


angles = {int(r['frame']): r for r in csv.DictReader((HERE / 'solver_motion.csv').open())}
transforms = json.loads((HERE / 'solver_transforms.json').read_text())
max_origin_error_mm = 0.
max_rotation_entry_error = 0.
checks = 0
# Every original mesh origin at every solver frame is compared, not just end poses.
for entry in transforms:
    frame = entry['frame']
    world = {'base_link': eye()}
    todo = list(joints)
    while todo:
        ready = [j for j in todo if j.find('parent').attrib['link'] in world]
        assert ready
        for joint in ready:
            parent = joint.find('parent').attrib['link']
            child = joint.find('child').attrib['link']
            origin = joint.find('origin')
            xyz = [float(v) for v in origin.attrib['xyz'].split()]
            assert origin.attrib['rpy'] == '0 0 0'
            local = translate(xyz)
            if joint.attrib['type'] == 'revolute':
                n = 'yaw' if joint.attrib['name'].startswith('yaw') else 'pitch'
                axis = [float(v) for v in joint.find('axis').attrib['xyz'].split()]
                local = mm(local, rotate(axis, math.radians(float(angles[frame][n + '_deg']))))
            world[child] = mm(world[parent], local)
            todo.remove(joint)
    for p in manifest['instances']:
        com = [v * -.001 for v in manifest['mass_properties'][p['group']]['com_mm']]
        bullet = mm(entry['transforms_m'][p['group']], translate(com))
        fk = world[p['id']]
        origin_error = math.sqrt(sum((bullet[i][3] - fk[i][3]) ** 2 for i in range(3))) * 1000
        rotation_error = max(abs(bullet[i][j] - fk[i][j]) for i in range(3) for j in range(3))
        max_origin_error_mm = max(max_origin_error_mm, origin_error)
        max_rotation_entry_error = max(max_rotation_entry_error, rotation_error)
        checks += 1
assert max_origin_error_mm < .05
assert max_rotation_entry_error < .00001
result = {
    'status': 'PASS', 'method': 'Independent stdlib URDF tree/FK compared with recorded Bullet world matrices',
    'links': len(links), 'revolute_joints': 2, 'fixed_joints': 67,
    'mesh_paths_present': 67, 'frames_checked': len(transforms), 'component_transform_checks': checks,
    'max_mesh_origin_difference_mm': max_origin_error_mm,
    'max_rotation_matrix_entry_difference': max_rotation_entry_error,
    'source_manifest_digest_matches': True,
    'scope': 'Consistency between explicit joint graph and actual solver run; does not validate physical fixed joints, spline or vendor interfaces.',
}
(HERE / 'urdf_validation.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
