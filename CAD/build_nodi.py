#!/usr/bin/env python3
"""NODI revision A: executable CadQuery B-rep source; millimetres throughout.

Coordinates: X right, Y rear, Z up. Shapes are authored in assembly coordinates.
The inverse tilt arrangement fixes the horn to the yoke and rotates the servo case
with the head. Commercial parts are interface envelopes, not vendor CAD.
"""
from pathlib import Path
import argparse
import itertools
import json
import math
import time

import cadquery as cq

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
P = json.loads((HERE / "parameters.json").read_text())
OUT = HERE / "exports"
for folder in [OUT / "STEP", OUT / "STL", OUT / "meshes"]:
    folder.mkdir(parents=True, exist_ok=True)


def box(w, d, h, c):
    return cq.Workplane("XY").box(w, d, h).translate(c).val()


def cyl(r, h, start, axis=(0, 0, 1)):
    return cq.Solid.makeCylinder(r, h, cq.Vector(*start), cq.Vector(*axis))


def rounded_box(w, d, h, c, r, vertical="Z"):
    return cq.Workplane(obj=box(w, d, h, c)).edges("|" + vertical).fillet(r).val()


def fuse(*shapes):
    out = shapes[0]
    for sh in shapes[1:]:
        out = out.fuse(sh)
    return out.clean()


def cut(shape, *tools):
    for tool in tools:
        shape = shape.cut(tool)
    return shape.clean()


def hole_x(shape, diameter, y, z, xmin=-70, length=140):
    return cut(shape, cyl(diameter / 2, length, (xmin, y, z), (1, 0, 0)))


def hole_y(shape, diameter, x, z, ymin=-60, length=120):
    return cut(shape, cyl(diameter / 2, length, (x, ymin, z), (0, 1, 0)))


def screw(axis, start, length, diameter, head_diameter=None, head_h=1.6):
    # Smooth nominal shank and cylindrical head: threads deliberately omitted.
    head_diameter = head_diameter or diameter * 1.8
    a = cq.Vector(*axis)
    hstart = cq.Vector(*start) - a.multiply(head_h)
    return fuse(cyl(diameter / 2, length, start, axis),
                cyl(head_diameter / 2, head_h, hstart.toTuple(), axis))


def ring(od, ident, h, start, axis=(0, 0, 1)):
    return cut(cyl(od / 2, h, start, axis), cyl(ident / 2, h, start, axis))


PARTS = []
COLORS = {"ivory": [0.91, 0.89, 0.82], "orange": [0.91, 0.40, 0.20],
          "dark": [0.075, 0.10, 0.13], "metal": [0.55, 0.59, 0.63],
          "brass": [0.70, 0.51, 0.18], "green": [0.04, 0.35, 0.22],
          "cyan": [0.24, 0.81, 0.91], "white": [0.91, 0.94, 0.95]}


def add(ident, number, name, shape, group="fixed", color="metal", material="Steel",
        density=7.85, mass=None, printable=False, explode=(0, 0, 0), notes=""):
    entry = dict(id=ident, part_number=number, name=name, shape=shape, group=group,
                 color=COLORS.get(color, color) if isinstance(color, str) else color, material=material,
                 density_g_cm3=density, mass_override_g=mass, printable=printable,
                 explode=list(explode), notes=notes)
    PARTS.append(entry)
    return shape


def custom(ident, number, name, shape, group="fixed", color="ivory", explode=(0, 0, 0)):
    return add(ident, number, name, shape, group, color, "PETG", P["petg_density_g_cm3"],
               printable=True, explode=explode)


# Base cup: 2.4 mm walls, floor and a screwed removable deck.
bw, bd, bh, wall = [P[k] for k in ("base_width_mm", "base_depth_mm", "base_height_mm", "wall_mm")]
base = rounded_box(bw, bd, 29.6, (0, 0, 14.8), 10)
inside = rounded_box(bw - 2 * wall, bd - 2 * wall, 31,
                     (0, 0, 17.9), 7.6)
base = cut(base, inside)
base_bolts = [(x, y) for x in (-51, 51) for y in (-41, 41)]
for x, y in base_bolts:
    base = fuse(base, cyl(4, 27.2, (x, y, 2.4)))
    base = cut(base, cyl(1.35, 20, (x, y, 10)))
# Slotted servo tabs: body rests at flange plane Z24, no unsupported motor mass.
for x in (-8.2, 19.2):
    base = fuse(base, box(4, 12.2, 21.6, (x, 0, 13.2)))
    base = cut(base, cyl(0.9, 14, (x, 0, 12)))
# Electronic carrier mounts. All bosses originate from the printed floor.
rear_holes = [(x, y) for x in (-36, 36) for y in (19.5, 38.5)]
power_holes = [(x, y) for x in (-50, -19) for y in (-12, 12)]
switch_holes = [(-9.5, -36), (9.5, -36)]
for x, y in rear_holes:
    base = fuse(base, cyl(3, 4.6, (x, y, 2.4)))
    base = cut(base, cyl(1.35, 7, (x, y, 1)))
for x, y in power_holes:
    base = fuse(base, cyl(3, 2.6, (x, y, 2.4)))
    base = cut(base, cyl(1.35, 6.4, (x, y, 0.6)))
for x, y in switch_holes:
    base = fuse(base, cyl(3, 20.5, (x, y, 2.4)))
    base = cut(base, cyl(1.35, 12, (x, y, 12)))
# Retained low ballast: floor-connected bosses support the steel bar atZ8.4.
for x in (-10, 18):
    base = fuse(base, cyl(3, 6, (x, -19, 2.4)))
    base = cut(base, cyl(1.35, 6.2, (x, -19, 2.4)))
for y in (24, 32):
    base = cut(base, cyl(1.25, 5, (45, y, -1)))
# Captive USB cable entry and acoustic apertures.
base = hole_y(base, 7.2, 34, 12, ymin=45, length=12)
for x in (28, 32, 36):
    base = hole_y(base, 2.2, x, 13, ymin=-55, length=10)
custom("base_cup", "NODI-P01", "Base cup and integral mounting bosses", base)

lid = rounded_box(120, 100, 2.4, (0, 0, 30.8), 10)
lid = cut(lid, cyl(P["lid_bearing_bore_mm"] / 2, 6, (0, 0, 28)),
          cyl(3.8, 6, (0, -36, 28)), cyl(5, 6, (0, 34, 28)))
for x, y in base_bolts:
    lid = cut(lid, cyl(1.65, 5, (x, y, 28)), cyl(3.1, 1.4, (x, y, 30.6)))
# Yaw stops touch the rotating pin at +/-35 degrees. Both have radius2.
delta_yaw = math.degrees(2 * math.asin(4 / (2 * 55)))
for a in (-35 - delta_yaw, 35 + delta_yaw):
    rad = math.radians(a)
    lid = fuse(lid, cyl(2, 6, (55 * math.cos(rad), 55 * math.sin(rad), 32)))
custom("base_deck", "NODI-P02", "Removable base deck with yaw stops", lid, explode=(0, 0, 25))
add("thrust_washer", "NODI-C01", "PTFE annular thrust washer", ring(40, 25, 2, (0, 0, 32)),
    material="PTFE", density=2.2, color="white", explode=(0, 0, 42))

# One-piece U-yoke, including supported pilot journal and stop features.
gap, arm_t, arm_d, zaxis = [P[k] for k in ("yoke_gap_mm", "yoke_thickness_mm", "yoke_arm_depth_mm", "pitch_axis_height_mm")]
yoke_width = gap + 2 * arm_t
yoke = rounded_box(yoke_width, 40, 4, (0, 0, 36), 3)
yoke = fuse(yoke, ring(24, 20.4, 5, (0, 0, 29)))
for x in (-gap / 2 - arm_t / 2, gap / 2 + arm_t / 2):
    yoke = fuse(yoke, box(arm_t, arm_d, zaxis - 38, (x, 0, (zaxis + 38) / 2)),
                cyl(14, arm_t, (x - arm_t / 2, 0, zaxis), (1, 0, 0)))
yoke = cut(yoke, cyl(4.5, 8, (0, 0, 32)))
for x in (-7, 7):
    yoke = cut(yoke, cyl(1.1, 8, (x, 0, 32)))
yoke = hole_x(yoke, 4.2, 0, 88, xmin=-50, length=8)
yoke = hole_x(yoke, 6, 0, 88, xmin=42, length=8)
for y in (-7, 7):
    yoke = hole_x(yoke, 2.2, y, 88, xmin=42, length=8)
yoke = fuse(yoke, box(10, 4, 4, (50, 0, 36)), cyl(2, 4, (55, 0, 34)))
yoke = cut(yoke, ring(28, 19, 1.4, (-45.4, 0, 88), (1, 0, 0)))
delta_pitch = math.degrees(2 * math.asin(3 / (2 * 12)))
pitch_stop_centres = []
for a in (-20 - delta_pitch, 30 + delta_pitch):
    rad = math.radians(a)
    y, z = -12 * math.sin(rad), 88 + 12 * math.cos(rad)
    pitch_stop_centres.append([y, z])
    yoke = fuse(yoke, cyl(1.5, 1.5, (-45.5, y, z), (1, 0, 0)))
custom("yoke", "NODI-P03", "One-piece pan and tilt yoke", yoke, "yaw", "orange", (0, 0, 62))

# Head rear shell, detachable bezel, servo posts and passive pivot boss.
head_outer = rounded_box(86, 45.6, 60, (0, 1.2, 88), 6, "Y")
head_inner = rounded_box(81.2, 47, 55.2, (0, -1.9, 88), 3.6, "Y")
head = cut(head_outer, head_inner)
# The open front is -21.6; rear internal surface is +21.6.
bezel_holes = [(x, z) for x in (-36, 36) for z in (64, 112)]
for x, z in bezel_holes:
    head = fuse(head, cyl(4.5, 8, (x, -21.6, z), (0, 1, 0)))
    head = hole_y(head, 1.8, x, z, ymin=-22, length=8)
head = fuse(head, cyl(5, 9, (-43, 0, 88), (1, 0, 0)))
head = hole_x(head, 4.2, 0, 88, xmin=-46, length=14)
# Internal servo flange supports, tabs sit against plane X35.4.
for y in (-8.2, 19.2):
    head = fuse(head, box(5.2, 4, 24, (38, y, 88)))
    head = hole_x(head, 1.8, y, 88, xmin=34, length=10)
# Right wall clearance for rotating servo output/horn and bottom cable slot.
head = hole_x(head, 21, 0, 88, xmin=40, length=6)
head = cut(head, cyl(4, 7, (0, 15, 55)))
head = fuse(head, cyl(1.5, 2.4, (-44.4, 0, 100), (1, 0, 0)))
for x in (-15, -5, 5, 15):
    head = cut(head, box(4, 6, 1.8, (x, 23, 65)))
head = cut(head, box(3, 0.8, 14, (34.5, 21.8, 88)))
custom("head_shell", "NODI-P04", "Head shell with servo cradle and passive pivot", head,
       "pitch", "ivory", (0, 0, 100))
bezel = rounded_box(86, 2.4, 60, (0, -22.8, 88), 6, "Y")
bezel = cut(bezel, rounded_box(36, 8, 24, (0, -22.8, 90), 2, "Y"))
for x, z in bezel_holes:
    bezel = hole_y(bezel, 2.2, x, z, ymin=-26, length=7)
for x in (-15.25, 15.25):
    for z in (76, 104):
        bezel = fuse(bezel, cyl(2.5, 2.7, (x, -21.6, z), (0, 1, 0)))
        bezel = hole_y(bezel, 1.8, x, z, ymin=-23, length=7)
custom("front_bezel", "NODI-P05", "Front bezel and OLED mounting spacers", bezel,
       "pitch", "dark", (0, -50, 100))

# Commercial motors: dimensioned body, flange, tower/output and actual clearance bores.
def servo_vertical():
    body = box(22.8, 12.2, 22.5, (5.5, 0, 15.15))
    flange = box(32.4, 12.2, 2.0, (5.5, 0, 25))
    for x in (-8.2, 19.2):
        flange = cut(flange, cyl(1.1, 4, (x, 0, 23)))
    return cut(fuse(body, flange, cyl(5.7, 3, (0, 0, 26.4)), cyl(2.4, 3, (0, 0, 29.4))), cyl(0.9, 7, (0, 0, 26.4)))


pan_servo = servo_vertical()
add("pan_servo", "NODI-C02", "TowerPro MG90S yaw servo envelope", pan_servo,
    color="dark", material="MG90S assembly", density=None, mass=13.4,
    notes="Manufacturer envelope22.8x12.2x28.5mm; flange/horn pattern is a design interface assumption requiring incoming sample check.")
# Rotate the same motor so its output points +X; translate output tip toX41.8,Z88.
tilt_servo = pan_servo.rotate((0, 0, 0), (0, 1, 0), 90).rotate((0, 0, 0), (1, 0, 0), 90)
# Rotation maps original(X,Y,Z) -> (Z,X,Y), so axis+Z -> +X and longbodyX -> +Y.
tilt_servo = tilt_servo.translate((9.4, 0, 88))
add("tilt_servo", "NODI-C02", "TowerPro MG90S pitch servo envelope", tilt_servo,
    "pitch", "dark", "MG90S assembly", None, 13.4, explode=(30, 0, 100),
    notes="Servo case is fixed to head; output horn is fixed to yoke. Neutral shafttipX41.8.")
# Horns are purchased drilled discs, not assumed exact stock TowerPro geometry.
pan_horn = fuse(ring(19, 3, 1.6, (0, 0, 32.4)), ring(7, 4.8, 2, (0, 0, 30.4)))
for x in (-7, 7):
    pan_horn = cut(pan_horn, cyl(0.9, 4, (x, 0, 31)))
add("pan_horn", "NODI-C03", "19mm servo disc horn, match-drilled", pan_horn,
    "yaw", "white", "Nylon", 1.14, mass=1.5, explode=(0, 0, 48))
tilt_horn = fuse(ring(19, 3, 2.2, (41.8, 0, 88), (1, 0, 0)), ring(7, 4.8, 2, (39.8, 0, 88), (1, 0, 0)))
for y in (-7, 7):
    tilt_horn = hole_x(tilt_horn, 1.8, y, 88, xmin=40, length=6)
add("tilt_horn", "NODI-C03", "19mm servo disc horn, match-drilled", tilt_horn,
    "yaw", "white", "Nylon", 1.14, mass=1.5, explode=(25, 0, 62))

# Vendor horn retaining screws have clearance through both yoke access bores.
add("pan_retaining_screw", "NODI-F09", "Vendor M2.2 x6 servo horn retaining screw", screw((0, 0, -1), (0, 0, 34), 6, 2.2, 4.2, 1.5), "yaw", explode=(0, 0, 65))
add("tilt_retaining_screw", "NODI-F09", "Vendor M2.2 x6 servo horn retaining screw", screw((-1, 0, 0), (44, 0, 88), 6, 2.2, 4.2, 1.5), "yaw", explode=(35, 0, 62))

# Left passive pivot: sleeve is clamped, PETG boss turns on OD4 and PTFE thrust washer.
add("pitch_sleeve", "NODI-C04", "Brass pivot sleeve OD4 ID3.2 x14.2", ring(4, 3.2, 14.2, (-48, 0, 88), (1, 0, 0)),
    "yaw", "brass", "Brass", 8.5, explode=(-22, 0, 62))
add("pitch_washer", "NODI-C05", "PTFE pivot washer OD8 ID4.3 x1", ring(8, 4.3, 1, (-44, 0, 88), (1, 0, 0)),
    "yaw", "white", "PTFE", 2.2, explode=(-20, 0, 62))
add("pitch_bolt", "NODI-F01", "M3 x20 passive pivot screw", screw((1, 0, 0), (-48, 0, 88), 20, 3, 5.5, 2),
    "yaw", explode=(-36, 0, 62))
add("pitch_nut", "NODI-F02", "M3 DIN985 nylon locking nut envelope", ring(5.5, 2.6, 4, (-33.8, 0, 88), (1, 0, 0)),
    "yaw", explode=(-12, 0, 62))

# OLED PCB drilled to the published Adafruit938 mounting pattern, panel and active screen.
oled = box(35.6, 1.6, 33, (0, -18.1, 90))
for x in (-15.25, 15.25):
    for z in (76, 104):
        oled = hole_y(oled, 2.5, x, z, ymin=-20, length=4)
add("oled_pcb", "NODI-C06", "Adafruit938 OLED PCB envelope", oled, "pitch", "green", "FR4 module", None, 5,
    explode=(0, -30, 100))
add("oled_panel", "NODI-C06", "OLED glass and driver panel envelope", box(34.5, 4.1, 23, (0, -20.95, 90)),
    "pitch", "dark", "OLED module", None, 4, explode=(0, -36, 100))
add("oled_active", "VISUAL", "OLED active display surface", box(29.42, 0.03, 14.7, (0, -23.015, 90)),
    "pitch", [0.025, 0.06, 0.07], "Display surface", None, 0,
    notes="29.42x14.7mm active area; renderer may overlay time/eyes within this area.")

# Base electronics on two removable flat carriers, print flat.
rear = box(80, 27, 2, (0, 29, 8))
for x, y in rear_holes:
    rear = cut(rear, cyl(1.6, 5, (x, y, 6)), cyl(2.9, 1.2, (x, y, 7.8)))
custom("rear_carrier", "NODI-P06", "Rear electronics carrier80x27", rear, explode=(0, 20, 20))
power = box(35, 28, 2, (-34.5, 0, 6))
for x, y in power_holes:
    power = cut(power, cyl(1.6, 5, (x, y, 4)), cyl(2.9, 1.2, (x, y, 5.8)))
custom("power_carrier", "NODI-P07", "Power electronics carrier35x28", power, explode=(-18, 0, 20))
add("pico", "NODI-C07", "Raspberry Pi Pico board envelope", box(51, 21, 3.8, (-12, 29, 10.9)),
    color="green", material="Pico assembly", density=None, mass=3)
add("rtc", "NODI-C08", "Adafruit3013 DS3231 RTC envelope", box(23, 17.6, 7.2, (27, 29, 12.6)),
    color="green", material="RTC assembly", density=None, mass=5)
add("power_perfboard", "NODI-C09", "Power and buffer perfboard envelope", box(31, 24, 1.6, (-34.5, 0, 7.8)),
    color="green", material="Populated circuit", density=None, mass=6)
add("capacitor", "NODI-C10", "1000uF capacitor envelope OD10x16", cyl(5, 16, (-42, 0, 8.6)),
    color="dark", material="Capacitor assembly", density=None, mass=2.5)
add("buffer_ic", "NODI-C11", "74AHCT125 DIP14 envelope", box(6.5, 19.3, 4, (-26.5, 0, 10.6)),
    color="dark", material="IC assembly", density=None, mass=1)
# Rear carrier includes reserved lead holes, but boards are bonded on nylon pads for POC.
switch_carrier = box(26, 20, 1.6, (0, -36, 23.7))
for x, y in switch_holes:
    switch_carrier = cut(switch_carrier, cyl(1.6, 4, (x, y, 22)))
custom("switch_carrier", "NODI-P08", "Snooze switch carrier", switch_carrier, explode=(0, -20, 20))
add("snooze_switch", "NODI-C12", "12mm tactile snooze switch envelope", fuse(box(12, 12, 3.5, (0, -36, 26.25)), cyl(1.75, 2.5, (0, -36, 28))),
    color="dark", material="Switch assembly", density=None, mass=1.5)
cap = fuse(cyl(8, 3.5, (0, -36, 32.8)), cyl(3.5, 2.3, (0, -36, 30.5)))
custom("snooze_cap", "NODI-P09", "Snooze button cap", cap, color="orange", explode=(0, -20, 40))
add("piezo", "NODI-C13", "Murata PKM13 piezo buzzer envelope", cyl(6.3, 6.9, (32, -28, 2.4)),
    color="dark", material="Piezo assembly", density=None, mass=2)
# Elastomer feet have pressure sensitive adhesive backs.
for i, (x, y) in enumerate(itertools.product((-45, 45), (-44, 44)), 1):
    add(f"foot_{i}", "NODI-C14", "Self adhesive silicone foot12x3", cyl(6, 3, (x, y, -3)),
        color="dark", material="Silicone", density=1.15, explode=(0, 0, -12))

# Machined low-carbon-steel ballast is cut from12.5mm plate and drilled, not printed.
ballast = box(40, 18, 12.5, (4, -19, 14.65))
for x in (-10, 18):
    ballast = cut(ballast, cyl(1.7, 16, (x, -19, 7)))
add("ballast", "NODI-P10", "Retained steel ballast40x18x12.5", ballast,
    color="metal", material="Low carbon steel", density=7.85, explode=(0, -20, 15))
for i, x in enumerate((-10, 18), 1):
    add(f"ballast_screw_{i}", "NODI-F10", "M3 x18 ballast screw", screw((0, 0, -1), (x, -19, 20.9), 18, 3, 5.4, 1.2))

# Complete major fasteners. Threads omitted; no false modeled interference fit.
for i, (x, y) in enumerate(base_bolts, 1):
    # Recessed heads are in the deck counterbores.
    add(f"deck_screw_{i}", "NODI-F03", "M3 x10 deck screw", screw((0, 0, -1), (x, y, 30.6), 10, 3, 5.6, 1.2),
        explode=(0, 0, 30))
for i, (x, z) in enumerate(bezel_holes, 1):
    add(f"bezel_screw_{i}", "NODI-F04", "M2 x8 bezel screw", screw((0, 1, 0), (x, -24, z), 8, 2, 3.6, 1.2),
        "pitch", explode=(0, -60, 100))
for i, (x, z) in enumerate(itertools.product((-15.25, 15.25), (76, 104)), 1):
    add(f"oled_screw_{i}", "NODI-F05", "M2 x5 OLED screw", screw((0, -1, 0), (x, -17.3, z), 5, 2, 3.4, 1.2),
        "pitch", explode=(0, -25, 100))
for i, x in enumerate((-8.2, 19.2), 1):
    add(f"pan_mount_screw_{i}", "NODI-F06", "M2 x8 servo mounting screw", screw((0, 0, -1), (x, 0, 26), 8, 2, 3.4, 1.2))
for i, y in enumerate((-8.2, 19.2), 1):
    add(f"tilt_mount_screw_{i}", "NODI-F06", "M2 x8 servo mounting screw", screw((1, 0, 0), (33.4, y, 88), 8, 2, 3.4, 1.2),
        "pitch", explode=(25, 0, 100))
for i, x in enumerate((-7, 7), 1):
    add(f"pan_horn_screw_{i}", "NODI-F07", "M2 x6 horn screw", screw((0, 0, -1), (x, 0, 38), 6, 2, 3.4, 1.2),
        "yaw", explode=(0, 0, 68))
for i, y in enumerate((-7, 7), 1):
    add(f"tilt_horn_screw_{i}", "NODI-F07", "M2 x6 horn screw", screw((-1, 0, 0), (48, y, 88), 6, 2, 3.4, 1.2),
        "yaw", explode=(35, 0, 62))
for prefix, holes, z in (("rear", rear_holes, 7.8), ("power", power_holes, 5.8), ("switch", switch_holes, 24.5)):
    for i, (x, y) in enumerate(holes, 1):
        add(f"{prefix}_screw_{i}", "NODI-F11" if prefix == "power" else "NODI-F08", "M3 x5 power carrier screw" if prefix == "power" else "M3 x6 carrier screw", screw((0, 0, -1), (x, y, z), 5 if prefix == "power" else 6, 3, 5.4, 1.2))


def manifest():
    entries = []
    for part in PARTS:
        sh = part["shape"]
        bb = sh.BoundingBox()
        com = sh.Center()
        volume = sh.Volume()
        mass = part["mass_override_g"]
        if mass is None:
            mass = volume / 1000 * part["density_g_cm3"]
        row = {k: v for k, v in part.items() if k not in ("shape", "mass_override_g")}
        row.update(volume_mm3=volume, mass_g=mass, com_mm=[com.x, com.y, com.z],
                   bbox_mm={"min": [bb.xmin, bb.ymin, bb.zmin], "max": [bb.xmax, bb.ymax, bb.zmax]},
                   stl=f"CAD/exports/meshes/{part['id']}.stl",
                   step=f"CAD/exports/STEP/{part['id']}.step",
                   solid_count=len(sh.Solids()), valid=sh.isValid(),
                   mass_basis="vendor/engineering estimate" if part["mass_override_g"] is not None else "CAD solid volume x material density (100% solid upper bound)")
        entries.append(row)
    data = dict(revision=P["revision"], units="mm", coordinates="X right; Y rear; Z up; face points-Y",
                instances=entries, mechanism=dict(pitch_axis_mm=[0, 0, 88], yaw_axis_mm=[0, 0, 0],
                    pitch_limits_deg=P["pitch_limits_deg"], yaw_limits_deg=P["yaw_limits_deg"],
                    pitch_hard_limits_deg=P["pitch_hard_limits_deg"], yaw_hard_limits_deg=P["yaw_hard_limits_deg"]),
                drawing_dimensions=dict(yoke_width_mm=yoke_width,yoke_gap_mm=gap,yoke_thickness_mm=arm_t,
                    pan_plate_depth_mm=40,pan_plate_z_mm=[34,38],arm_depth_mm=arm_d,
                    pitch_axis_z_mm=88,upper_pad_radius_mm=14,left_bore_mm=4.2,right_access_bore_mm=6,
                    horn_holes_mm=2.2,horn_hole_y_mm=[-7,7],pan_horn_hole_x_mm=[-7,7],
                    pilot_od_mm=24,pilot_id_mm=20.4,pilot_z_mm=[29,34],central_access_mm=9,
                    pitch_stop_pin_diameter_mm=3,pitch_stop_centres_yz_mm=pitch_stop_centres,
                    pitch_stop_recess_od_mm=28,pitch_stop_recess_id_mm=19,pitch_stop_recess_depth_mm=1.4,
                    pitch_stop_recess_x_mm=[-45.4,-44],pitch_stop_pin_x_mm=[-45.5,-44],pitch_stop_lug_x_mm=[-44.4,-42],
                    yaw_stop_lug_center_mm=[55,0,36],yaw_stop_lug_diameter_mm=4,
                    yaw_stop_bridge_bounds_mm=[[45,-2,34],[55,2,38]]))
    for group in ("fixed", "yaw", "pitch"):
        members = [row for row in entries if row["group"] == group]
        total = sum(row["mass_g"] for row in members)
        data.setdefault("mass_properties", {})[group] = dict(mass_g=total,
            com_mm=[sum(row["mass_g"] * row["com_mm"][j] for row in members) / total for j in range(3)])
    data["mass_properties"]["total_mass_g"] = sum(row["mass_g"] for row in entries)
    (HERE / "manifest.json").write_text(json.dumps(data, indent=2) + "\n")
    return data


def export_all():
    assy = cq.Assembly(name="NODI_revision_A")
    for part in PARTS:
        sh = part["shape"]
        ident = part["id"]
        cq.exporters.export(sh, str(OUT / "STEP" / f"{ident}.step"))
        cq.exporters.export(sh, str(OUT / "meshes" / f"{ident}.stl"),
            tolerance=P["export_tolerance_mm"], angularTolerance=P["export_angular_tolerance_rad"])
        if part["printable"]:
            # Printable files use a local, minimum-Z-at-zero coordinate system.
            bb = sh.BoundingBox()
            local = sh.translate((-sh.Center().x, -sh.Center().y, -bb.zmin))
            cq.exporters.export(local, str(OUT / "STL" / f"{part['part_number']}_{ident}.stl"),
                tolerance=P["export_tolerance_mm"], angularTolerance=P["export_angular_tolerance_rad"])
        assy.add(sh, name=ident, color=cq.Color(*part["color"]))
    assy.save(str(OUT / "NODI_Assembly_RevA.step"))
    exploded = cq.Assembly(name="NODI_exploded_revision_A")
    for part in PARTS:
        exploded.add(part["shape"].translate(part["explode"]), name=part["id"], color=cq.Color(*part["color"]))
    exploded.save(str(OUT / "NODI_Exploded_RevA.step"))


def pose(part, yaw, pitch):
    sh = part["shape"]
    if part["group"] == "pitch":
        sh = sh.rotate((0, 0, 88), (1, 0, 88), pitch)
    if part["group"] in ("pitch", "yaw"):
        sh = sh.rotate((0, 0, 0), (0, 0, 1), yaw)
    return sh


def validate(run_sweep=True):
    records = []
    # Read back every STEP export and compare body volume (translation invariant).
    for part in PARTS:
        reread = cq.importers.importStep(str(OUT / "STEP" / f"{part['id']}.step")).val()
        original = part["shape"]
        records.append(dict(id=part["id"], valid=original.isValid(), solids=len(original.Solids()),
            step_valid=reread.isValid(), volume_mm3=original.Volume(),
            step_volume_relative_error=abs(reread.Volume() - original.Volume()) / max(original.Volume(), 1e-9)))
    # Threads intentionally not represented: screw/pilot-hole engagements are listed separately.
    # Mesh and exact solid collision checks distinguish structure from purchased envelopes.
    structural_ids = {"base_cup", "base_deck", "thrust_washer", "yoke", "head_shell", "front_bezel",
                      "pan_servo", "tilt_servo", "pan_horn", "tilt_horn", "pitch_sleeve", "pitch_washer",
                      "oled_pcb", "oled_panel", "snooze_cap", "snooze_switch", "rear_carrier", "power_carrier",
                      "switch_carrier", "pico", "rtc", "power_perfboard", "capacitor", "buffer_ic", "piezo", "ballast"}
    candidates = [p for p in PARTS if p["id"] in structural_ids]
    # Fixed integral support features intentionally touch hardware faces (zero volume), not interpenetrate.
    exclusions = {}
    samples = [(-30,-15),(-30,25),(0,-15),(0,0),(0,25),(30,-15),(30,25)] if run_sweep else [(0,0)]
    clashes = []
    excluded_clashes = []
    # Only moving/fixed and pitch/yaw pairs need repeat sweeps; fixed internal checks once.
    for yaw, pitch in samples:
        transformed = {p["id"]: pose(p, yaw, pitch) for p in candidates}
        for a, b in itertools.combinations(candidates, 2):
            if (yaw, pitch) != (0,0) and a["group"] == b["group"]:
                continue
            sha, shb = transformed[a["id"]], transformed[b["id"]]
            ba, bb = sha.BoundingBox(), shb.BoundingBox()
            if (ba.xmax <= bb.xmin + 1e-6 or bb.xmax <= ba.xmin + 1e-6 or
                ba.ymax <= bb.ymin + 1e-6 or bb.ymax <= ba.ymin + 1e-6 or
                ba.zmax <= bb.zmin + 1e-6 or bb.zmax <= ba.zmin + 1e-6):
                continue
            overlap = sha.intersect(shb).Volume()
            if overlap > 0.01:
                row = dict(a=a["id"],b=b["id"],yaw_deg=yaw,pitch_deg=pitch,intersection_mm3=overlap)
                reason = exclusions.get(tuple(sorted((a["id"], b["id"]))))
                if reason:
                    row["exclusion"] = reason
                    excluded_clashes.append(row)
                else:
                    clashes.append(row)
    result = dict(revision=P["revision"], geometry_engine="CadQuery2.6.1/OpenCASCADE7.8",
        body_checks=records, pose_samples=[dict(yaw_deg=y,pitch_deg=p) for y,p in samples],
        non_excluded_intersections=clashes, exclusions=excluded_clashes,
        note="Exact B-rep intersections at sampled poses; not continuous motion proof. Screw threads intentionally omitted. Flexible cables/electrical leads not modeled. Fit/stops and incoming purchased hardware require prototype measurement.",
        all_bodies_valid=all(r["valid"] and r["step_valid"] for r in records),
        all_step_volumes_match=all(r["step_volume_relative_error"] < 1e-7 for r in records))
    (HERE / "validation.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-sweep", action="store_true", help="Check only neutral pose (faster editing loop)")
    args = parser.parse_args()
    started = time.time()
    data = manifest()
    print(json.dumps(data["mass_properties"], indent=2), flush=True)
    export_all()
    print("Exports complete; reading STEP and checking solids...", flush=True)
    results = validate(not args.no_sweep)
    print(json.dumps({k:v for k,v in results.items() if k in ("all_bodies_valid","all_step_volumes_match","non_excluded_intersections","exclusions")}, indent=2), flush=True)
    print(f"Built {len(PARTS)} instances in {time.time()-started:.1f}s", flush=True)
