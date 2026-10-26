#!/usr/bin/env python3
"""Annotate actual recorded-transform renders and assemble a compact GIF.
Requires Pillow; run after render_solver_motion.py. No CAD or pose changes.
"""
from pathlib import Path
import csv
import hashlib
import json
import os
import tempfile
from PIL import Image, ImageDraw, ImageFont
HERE = Path(__file__).resolve().parent
FRAMES = Path(tempfile.gettempdir()) / 'nodi-bullet-frames'
rows = {int(r['frame']): r for r in csv.DictReader((HERE / 'solver_motion.csv').open())}
projections = json.loads((FRAMES / 'projections.json').read_text())
font_root = Path('/usr/share/fonts/truetype/dejavu')
def font(size, bold=False):
    candidates = [font_root / ('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf'), Path('/System/Library/Fonts/Supplemental') / ('Arial Bold.ttf' if bold else 'Arial.ttf'), Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts' / ('arialbd.ttf' if bold else 'arial.ttf')]
    for candidate in candidates:
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default(size=size)

def compose(item):
    frame = item['frame']
    row = rows[frame]
    source = Image.open(FRAMES / f'frame_{frame:04d}.png').convert('RGB').resize((960, 720), Image.Resampling.LANCZOS)
    image = Image.new('RGB', (1320, 880), '#f4f7fa')
    image.paste(source, (0, 95))
    d = ImageDraw.Draw(image)
    d.rectangle((0, 0, 1320, 94), fill='#142b3a')
    d.text((30, 16), 'NODI  /  ARTICULATED MECHANISM', font=font(27, True), fill='white')
    motion = 'NEUTRAL HOLD' if frame < 31 else 'YAW: horn and yoke turn' if frame < 271 else 'PITCH: case and head turn'
    d.text((30, 54), motion, font=font(22), fill='#c6dde9')
    d.text((960, 14), 'BULLET SOLVER OUTPUT', font=font(19, True), fill='#82d0ec')
    d.text((960, 47), f"Yaw {float(row['yaw_deg']):+6.2f}°   Pitch {float(row['pitch_deg']):+6.2f}°", font=font(20), fill='white')
    d.rectangle((960, 95, 1320, 814), fill='#f4f7fa')
    labels = [
        ('tilt_servo', 180, 'PITCH SERVO CASE', 'Fixed to moving head', 'Blue for identification', '#167fae'),
        ('tilt_horn', 330, 'PITCH OUTPUT HORN', 'Fixed to the orange yoke', 'Held while case rotates', '#bf613d'),
        ('pan_horn', 500, 'YAW OUTPUT HORN', 'Drives the complete yoke', 'Spline grip is assumed', '#bf613d'),
        ('pan_servo', 650, 'YAW SERVO CASE', 'Fixed to the grounded base', 'Receives the reaction torque', '#234d61'),
    ]
    for ident, y, title, line1, line2, color in labels:
        px, py = item['targets'][ident]
        py += 95
        xend = 985
        d.line([(px, py), (945, py), (970, y + 15), (xend, y + 15)], fill=color, width=2)
        d.ellipse((px-5, py-5, px+5, py+5), fill=color, outline='white', width=2)
        d.rounded_rectangle((985, y-7, 1303, y+91), radius=8, fill='white', outline='#dce3e9', width=1)
        d.text((999, y+5), title, font=font(18, True), fill=color)
        d.text((999, y+34), line1, font=font(16), fill='#213848')
        d.text((999, y+57), line2, font=font(16), fill='#536a79')
    d.rectangle((0, 815, 1320, 880), fill='white')
    d.text((24, 827), 'Cutaway: shell and deck hidden; yoke translucent. Brass passive pivot supports the opposite side.', font=font(18), fill='#203847')
    d.text((24, 853), 'Actual hinge/motor solver run  •  ideal rigid couplings  •  no physical build, spline/contact or cable validation', font=font(16), fill='#6b7984')
    return image

frames = [compose(item) for item in projections]
assert frames
# A common palette reduces flicker and image size, while preserving the CAD colors.
palette = frames[len(frames)//2].quantize(colors=128)
indexed = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
indexed[0].save(HERE / 'mechanism_motion.gif', save_all=True, append_images=indexed[1:], duration=100, loop=0, optimize=True)
still = min(projections, key=lambda x: abs(x['frame'] - 330))
compose(still).save(HERE / 'mechanism_cutaway.png', optimize=True)
provenance = {
    'source': 'Recorded matrices from actual Blender/Bullet hinge and angular motor run',
    'solver_transforms_sha256': hashlib.sha256((HERE / 'solver_transforms.json').read_bytes()).hexdigest(),
    'solver_frames_displayed': [item['frame'] for item in projections],
    'frame_duration_ms': 100, 'still_solver_frame': still['frame'],
    'visualization': 'Base cup, deck and head shell omitted; yoke translucent with 0.01mm render-only outward offset to avoid coincident contact faces; pitch servo case blue. No source CAD or solver geometry altered.',
    'scope': 'Visualization of an ideal constrained solver result; not physical motion, torque coupling or cable validation.',
}
(HERE / 'render_provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
print(f'Created {len(frames)} labeled solver frames; still from solver frame {still["frame"]}')
