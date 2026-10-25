"""Package CAD posture frames as a key-pose GIF; record rendering inputs.
Run after all nine Blender modes complete. This does not simulate servo tracking.
"""
from pathlib import Path
import json,hashlib
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
frames=[Image.open(ROOT/f'Images/nodi_{s}.png').convert('RGB') for s in ['sleepy','awake','cheerful','awake']]
frames[0].save(ROOT/'Images/nodi_pose_sequence.gif',save_all=True,append_images=frames[1:],duration=[1200,900,1200,900],loop=0,optimize=True)
names=['hero','exploded','front','side','top','cutaway','sleepy','awake','cheerful']
record={'geometry_source':'CAD/build_nodi.py and CAD/parameters.json','cad_manifest_sha256':sha(ROOT/'CAD/manifest.json'),'render_source':'tools/render_cad.py','render_source_sha256':sha(ROOT/'tools/render_cad.py'),'renderer':'Blender 4.5.3 LTS, Cycles CPU','evidence':'Actual exported CAD meshes, studio lighting and illustrative OLED artwork; no hardware photograph. Cutaway hides named covers/shells. GIF holds discrete CAD key poses; not a measured or time-accurate motion trajectory.','render_files_sha256':{f'Images/nodi_{n}.png':sha(ROOT/f'Images/nodi_{n}.png') for n in names}}
(ROOT/'Images/render_provenance.json').write_text(json.dumps(record,indent=2)+'\n')
print('Packaged key-pose GIF and render provenance.')
