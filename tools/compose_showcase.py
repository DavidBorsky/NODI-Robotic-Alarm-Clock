"""Compose the showcase and report from the executed analysis and CAD records.
This does not run CAD or analysis. Run those before this script.
"""
import json,re,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
a=json.loads((ROOT/'Analysis/analysis_results.json').read_text())
m=json.loads((ROOT/'CAD/manifest.json').read_text())
v=json.loads((ROOT/'CAD/validation.json').read_text())
mass=a['mass'];motor=a['motor'];s=a['structure'];tip=a['stability'];t=a['thermal_and_power']
readme=f'''# NODI — a little clock that wakes up with you

**An expressive, two-axis robotic alarm clock.** Sleepy at rest, reluctant when snoozed, cheerful when you get up.

![NODI assembled CAD render](Images/nodi_hero.png)

[**Read the engineering report (PDF)**](Documentation/NODI_Engineering_Design_Report.pdf) · [**Download the STEP assembly**](CAD/exports/NODI_Assembly_RevA.step) · [**Manufacturing drawing (PDF)**](Drawings/NODI-P03_Yoke_RevA.pdf)

Prepared for Human Computer Lab's Mechanical Engineering Internship challenge · David Borsky · Revision A · October 2026

> **Evidence status:** This is an unbuilt digital engineering proof of concept. The parametric CAD, exports, calculations and software checks were executed. Renders show the actual CAD with illustrative OLED pixels. Hardware performance remains untested; no FEA was run. [Design provenance and evidence boundaries](Documentation/design_provenance.md).

## A character made from motion

NODI slowly raises its head before the alarm, looks around and nods while ringing, droops for a five-minute snooze, and lifts its head when dismissed. A short button press snoozes; a 1.5-second hold dismisses the active alarm. Time and alarm settings are configured through USB serial and retained by the RTC and controller.

![CAD key-pose sequence: sleepy, awake and cheerful](Images/nodi_pose_sequence.gif)

*Discrete CAD key poses illustrate the character; this is not a recording or a time-accurate trajectory animation.*

The motion uses bounded quintic trajectories rather than instant angle jumps. See the [executed command-motion plots](Analysis/command_motion_profiles.pdf), [motion samples](Analysis/motion_profile.csv), and [controller state logic](Firmware/NODI/NodiCore.h). These describe commanded motion, not measured servo response.

| Design specification | Value / status |
|---|---|
| Physical axes | Yaw ±30°; pitch −15° to +25° |
| Base / head | 120 × 100 × 32 mm / 86 × 48 × 60 mm |
| Pitch axis | 88 mm above base datum; passive pivot opposite the motor |
| Motion limits | ≤60°/s and ≤180°/s² commanded; calibration required |
| Mass | {mass['cad_total_kg']*1000:.1f} g CAD material/envelope estimate; {mass['total_design_budget_kg']*1000:.1f} g design budget; 500 g target |
| Actuation | Two Tower Pro MG90S analog microservos, 5 V rail |
| Time / display | Raspberry Pi Pico, DS3231 RTC, 128 × 64 OLED |
| Power | Dedicated regulated 5 V / 3 A USB supply, fused rail, Schottky-fed logic |
| Prototype process | PETG FFF shells/yoke; cut PTFE thrust washer; retained steel ballast |
| Assembly target | ≤30 min, excluding fabrication, wiring and programming; unmeasured |

## The mechanism

The yaw servo turns a U-yoke through a match-drilled disc horn. An annular PTFE thrust washer supports the rotating table; a printed pilot locates it radially. The servo is not intended to carry the assembly's axial weight.

The pitch servo is mounted **inside the head**. Its horn is fixed to the yoke, so the servo case and head rotate together. A brass sleeve and M3 fastener support the opposite side. Printed stops sit beyond software travel. Cable service loops pass through the head's lower opening and the open rear of the mechanism.

![Exploded assembly generated from the same solids](Images/nodi_exploded.png)

[Exploded STEP](CAD/exports/NODI_Exploded_RevA.step) · [Part identification and counts](Manufacturing/BOM.csv) · [Detailed assembly instructions](Manufacturing/assembly_instructions.md)

| Front assembly | Side assembly |
|---|---|
| ![Front view](Images/nodi_front.png) | ![Side view](Images/nodi_side.png) |

[Top view](Images/nodi_top.png) · [Internal component view](Images/nodi_cutaway.png). The internal view omits covers and shells to expose components; it is not a physical assembly state.

## Engineering decisions and results

Three mechanisms were scored against eight criteria. Pan-tilt scores **4.13/5**, single-axis nodding **3.93/5**, and mechanical eyelids **3.05/5**. A 40% expressiveness weight selects pan-tilt; shifting five percentage points to simplicity creates a tie. Single-axis nodding wins with equal weights. The [decision matrix](Documentation/concept_selection.md) makes that preference explicit.

| Reproducible analytical result | Interpretation |
|---|---|
| Pitch torque: {motor['pitch_factored_required_Nm']:.4f} N·m, including 2× load factor | {motor['pitch_budget_reserve_ratio']:.2f}× reserve against a designer budget of 25% of rated stall torque |
| Yaw torque: {motor['yaw_factored_required_Nm']:.4f} N·m | {motor['yaw_budget_reserve_ratio']:.2f}× reserve against the same assumed operating budget |
| Yoke stress / displacement: {s['combined_screen_stress_MPa']:.3f} MPa / {s['combined_arm_deflection_mm']:.3f} mm | Reduced assumed PETG properties and a 3 g vertical proof case; no FEA or coupon test |
| Deck beam surrogate: {s['deck_beam_surrogate_3g_deflection_mm']:.2f} mm at 3 g; {s['deck_beam_surrogate_1g_deflection_mm']:.2f} mm at 1 g | Rough compliance estimate; check pilot/horn rubbing under load; whole-assembly stiffness remains unverified |
| Push-plus-motion stability: {tip['push_with_dynamic_margin_ratio']:.2f}× moment reserve | Added retained ballast and outboard feet after the initial 0.80× result failed |
| Static tipping angle: {tip['static_tip_angle_deg']:.1f}° | Conservative mass and center-of-gravity assumptions; physical tilt test still required |
| Finished pilot clearance: 0.30 mm minimum diametral | Requires specified finishing/gauging; as-printed tolerance stack can close the gap |
| Rail current budget: {t['assumed_peak_current_A']:.2f} A / 3 A source | Servo current is an assumption; simultaneous-stall and brownout tests required |
| Surface temperature estimate: {t['estimated_surface_low_C']:.1f}–{t['estimated_surface_high_C']:.1f} °C at 30 °C ambient | The conservative case exceeds the 45 °C target; thermal acceptance remains open |

Stall torque is not continuous torque. The manufacturer's 4.8 V stall value is **0.1765 N·m**; the **0.0441 N·m** operating budget is a design assumption requiring loaded current and temperature measurements. Stability assumes at least **{math.ceil(tip['minimum_total_mass_kg']*1000)} g** as-built mass and the stated CG bounds; infill can reduce the fully solid CAD mass. Weigh the prototype before accepting that result. Head mass, bounding-box inertias, cable drag, fastener bearing, stops, stability, tolerances and heat assumptions are documented in the [engineering analysis](Analysis/engineering_analysis.md) and [input file](Analysis/analysis_inputs.json). The [ballast and foot-placement iteration](Documentation/design_iteration.md) preserves the initial failed stability screen and the resulting mechanical change.

The final mechanical checks record **67 valid solid bodies**, matching STEP readbacks, and **490 targeted solid-pair checks at 1° increments with no intersections**. The minimum checked head/yoke separation is 1.00 mm. [Coverage and limits](CAD/motion_validation.json). These are digital geometry checks.

## Manufacturing and assembly

The prototype uses nine printable custom rigid parts, standard screws, replaceable purchased modules and a machined stock ballast. The complete BOM totals **$107.32 in preliminary material/component allowances**, excluding labor, shipping, tools and certification. The removable deck, electronics trays and bezel expose service joints. [Materials and DFM/DFA](Manufacturing/materials_and_processes.md) distinguishes the PETG prototype from a future PC-ABS molding redesign with draft, uniform walls, ribs and tooling review.

![Yoke drawing preview with datums and GD&T](Images/nodi_yoke_drawing.png)

[Two-sheet yoke drawing (PDF)](Drawings/NODI-P03_Yoke_RevA.pdf) · [Editable vector drawing source](Drawings/generate_yoke_drawing.py) · [Drawing/CAD parameter agreement](Drawings/drawing_geometry_check.json)

The yoke drawing defines functional datums, axis position tolerances, bearing fits, stop locations and process notes using ASME Y14.5 principles. It is a prototype definition requiring inspection, not a released production drawing.

## Electrical integration and software

![Electrical architecture](Electronics/wiring_block_diagram.svg)

[Wiring, pin assignments and power architecture](Electronics/architecture.md) · [Firmware and build instructions](Firmware/README.md) · [Actual compiler and host-test results](Firmware/verification_results.md)

The Pico sketch compiles for the ARM target. Fifteen host scenario groups pass, including midnight, snooze, dismissal, clock invalidity, reboot consumption, debounce, timer rollover and trajectory limits. The physical RTC, display, audio, flash retention, pulse-to-angle calibration and power circuitry have not been tested.

## Review or regenerate

1. Open [the assembly STEP](CAD/exports/NODI_Assembly_RevA.step) in FreeCAD, SolidWorks, Onshape or another STEP-capable modeler. STEP contains named/colorized component instances; it does not preserve a SolidWorks feature tree.
2. Edit [CAD/parameters.json](CAD/parameters.json) and [CAD/build_nodi.py](CAD/build_nodi.py) for parametric source. Use [CAD instructions](CAD/README.md) for export layout, coordinates, mounting assumptions and validation coverage.
3. Download [printable STLs](CAD/exports/STL) individually, or clone the repository. STLs are nominal geometry; orient parts and inspect coupons before printing.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python CAD/build_nodi.py
python CAD/check_motion.py
python CAD/verify_exports.py
python Analysis/engineering_calculations.py
python Analysis/plot_analysis.py
python Drawings/generate_yoke_drawing.py
bash Firmware/tests/run_tests.sh
python tools/compose_showcase.py
python tools/build_report.py
python tools/audit_package.py
```

Optional renders require Blender 4.5.3: `blender -b --python tools/render_cad.py -- hero` (also `exploded`, `front`, `side`, `top`, `cutaway`, `sleepy`, `awake`, `cheerful`). [Render source](tools/render_cad.py) imports exported CAD meshes; [the Blender scene](CAD/nodi_render_scene.blend) is included for visual review. Compiler setup is pinned separately in the firmware README.

| Deliverable | Files |
|---|---|
| Editable CAD, STEP and STL | [CAD](CAD/README.md), [assembly](CAD/exports/NODI_Assembly_RevA.step), [parts](CAD/exports/STEP), [print files](CAD/exports/STL) |
| Renders and exploded view | [Images](Images), [exploded assembly STEP](CAD/exports/NODI_Exploded_RevA.step) |
| Manufacturing drawing and GD&T | [Drawing PDF](Drawings/NODI-P03_Yoke_RevA.pdf), [editable source](Drawings/generate_yoke_drawing.py) |
| Calculations and numerical evidence | [Analysis](Analysis/engineering_analysis.md), [machine-readable results](Analysis/analysis_results.json) |
| Materials, BOM and assembly | [Process plan](Manufacturing/materials_and_processes.md), [BOM](Manufacturing/BOM.csv), [assembly](Manufacturing/assembly_instructions.md) |
| Functional integration | [Electronics](Electronics/architecture.md), [firmware](Firmware/README.md) |
| Requirements and proposed tests | [Verification matrix](Documentation/requirements_and_verification.md) |
| Development and launch | [24-hour scope and 30-week roadmap](Documentation/development_timeline.md) |
| Final report | [PDF](Documentation/NODI_Engineering_Design_Report.pdf), [editable Markdown](Documentation/engineering_report.md) |
| Package checks | [Verification summary](Documentation/verification_summary.md), [audit record](Documentation/package_audit.json), [CAD checks](CAD/validation.json), [drawing check](Drawings/drawing_geometry_check.json) |

## What remains before a physical proof of concept

Fabricate and gauge the parts, verify the actual servo/horn lot, assemble the harness, calibrate travel, measure head mass and cable drag, and test loaded torque/current, stability, acoustics, temperature and reliability. The 490 g budget leaves limited mass-growth allowance. FFF creep, local stress concentrations, fatigue and finger clearance require physical evaluation. The thermal upper estimate misses its target; reduce measured losses or improve heat rejection before accepting it.

The [verification matrix](Documentation/requirements_and_verification.md) defines acceptance criteria. The [development roadmap](Documentation/development_timeline.md) separates this digital challenge package from EVT, DVT, tooling, PVT and commercial release. No physical performance or product certification is claimed.
'''
(ROOT/'README.md').write_text(readme)
report=f'''# NODI
## Expressive robotic alarm clock

**Mechanical engineering design challenge · David Borsky · Revision A · 24 October 2026**

A two-axis desktop character that physically wakes up with its user. The design combines a serviceable pan-tilt mechanism, a time-and-eye OLED, audible alarm and one accessible snooze/dismiss button.

![Actual CAD assembly; illustrative OLED pixels. Hardware has not been built.](Images/nodi_hero.png)

| Key specification | Revision A definition |
|---|---|
| Motion | Yaw ±30°; pitch −15°/+25°; commanded ≤60°/s and ≤180°/s² |
| Envelope | Base120×100×32 mm; head86×48×60 mm; pitch axis Z = 88 mm |
| Estimated mass | {mass['cad_total_kg']*1000:.1f} g CAD estimate; {mass['total_design_budget_kg']*1000:.1f} g design budget; target ≤500 g |
| Main hardware | 2×MG90S; Pico; DS3231; 128×64 OLED; piezo; tactile button |
| Prototype materials | PETG printed rigid parts, PTFE thrust washer, steel ballast |
| Power | Dedicated regulated5V/3A USB source; fuse and Schottky-fed logic |

**Status:** Executed parametric CAD, exports, analytical scripts, ARM firmware compilation and host software tests. No fabrication, hardware tests or FEA. Results below are computational checks and calculated estimates. AI assistance was used to create this design package; see the repository provenance record.

<!-- pagebreak -->
## 1. Mechanical architecture and concept choice

NODI uses a U-yoke with a yaw table and an inverse tilt drive. A PTFE annular washer carries axial weight above the removable base deck. The integral pilot locates the table radially. A yaw servo below the deck drives the table through a purchased, match-drilled horn. Its shaft is not the intended thrust support.

The pitch servo is fixed inside the head while its output horn is fixed to the right yoke arm. The servo case and head therefore rotate together. A brass sleeve, PTFE washer and M3 fastener support the left side; the sleeve sets endfloat so tightening does not clamp the head. This keeps the drive within the head envelope and balances mass around the pitch axis.

![Exploded configuration from the same CAD solids. Identify components using the BOM and CAD manifest.](Images/nodi_exploded.png)

| Concept | Weighted score / 5 | Principal tradeoff |
|---|---|---|
| A. Two-axis pan-tilt | 4.13 | Most expressive; two joints and a flexible harness |
| B. Single-axis nod | 3.93 | Easier assembly and lower mechanical risk |
| C. Mechanical eyelids | 3.05 | Expressive face detail; links and small clearances |

Eight criteria cover expression, simplicity, assembly, cost, reliability, risk, integration and 24-hour feasibility. Expressiveness receives40% because character behavior is central to the brief. A five-percentage-point transfer to simplicity ties A and B; equal weighting selects B. The selection is a documented product preference rather than a uniquely optimal mechanism.

Software limits remain5° inside hard pitch limits−20°/+30° and yaw±35°. Hard stops are fault arrestors, not normal operating endpoints. The cable harness is not represented as a flexible solid; combined-limit manual sweeps are required after assembly.

<!-- pagebreak -->
## 2. First-principles actuation and structure

All calculations run from a shared CAD manifest and an explicit assumptions file. Masses of custom solids use nominal material density; purchased modules use stated estimates. A25% mass growth allowance and wiring budgets produce a{mass['head_design_budget_kg']*1000:.1f} g moving-head budget. The CAD head CG lies close to the axis; a conservative10 mm gravity offset is used to cover harness and assembly variation.

**Pitch torque:** τ = SF × (mge + Iα + τfriction + τcable). UseSF=2, g=9.80665m/s², α≤πrad/s², assumed friction0.003N·m and cable drag0.002N·m. Bounding boxes provide conservative inertia limits; these are not measured inertia tensors.

| Calculation | Result | Interpretation |
|---|---|---|
| Pitch gravity moment | {motor['pitch_gravity_Nm']:.5f} N·m |10mmCG budget |
| Pitch factored demand | {motor['pitch_factored_required_Nm']:.5f} N·m |Includes gravity, inertia, friction, cable andSF2 |
| Yaw factored demand | {motor['yaw_factored_required_Nm']:.5f} N·m |No gravity torque about vertical axis |
| Manufacturer stall torque at4.8V |0.17652N·m |1.8kgf·cm, not continuous rating |
| Assumed operating budget |0.04413N·m |Designer allowance at25% of stall |
| Pitch/yaw reserve ratio |{motor['pitch_budget_reserve_ratio']:.2f} / {motor['yaw_budget_reserve_ratio']:.2f} |Requires loaded actuator characterization |

Manufacturer data: [Tower Pro MG90S](https://torqpro.com/product/mg90s-analog/). Nominal envelope22.8×12.2×28.5mm and mass13.4g are procurement references. Flange/horn details vary; inspect the actual lot before fabrication and adjust parametric mounting features if necessary.

The yoke arms are reduced to4×12mm cantilevers of50mm free length. The model combines axial compression, driven-arm bending and lateral inertial bending. PETG uses assumedE=1GPa and a10MPa screening allowable. These reduced values are not qualified FFF material properties. The vertical proof case is3g, not an all-direction drop specification.

| Structural screen | Calculated estimate |
|---|---|
| Combined arm stress |{s['combined_screen_stress_MPa']:.3f}MPa against10MPa assumed allowable |
| Arm displacement |{s['combined_arm_deflection_mm']:.3f}mm against0.5mm target |
| Pivot shank shear |{s['pivot_shear_MPa']:.3f}MPa |
| Printed boss bearing |{s['printed_pivot_bearing_MPa']:.3f}MPa |

These simple sections do not resolve local root notches, screw thread pullout, contact, creep or fatigue. No finite-element solver was run. Coupons and a controlled assembled proof load are the next evidence needed.

The2.4mm base deck also needs compliance review. A simply supported beam surrogate under the rotating assembly's3g proof load gives approximately{s['deck_beam_surrogate_3g_stress_MPa']:.2f}MPa stress and{s['deck_beam_surrogate_3g_deflection_mm']:.2f}mm displacement; at normal1g its estimated displacement is{s['deck_beam_surrogate_1g_deflection_mm']:.2f}mm. Actual plate action, counterbores and edge contact are omitted. This is an open pilot/horn rubbing risk, not a qualified stiffness result. The0.5mm displacement target above applies to the yoke arm only; add ribbing or a bearing bridge if physical load tests change running clearance.

<!-- pagebreak -->
## 3. Motion, stability, fits and temperature

The shared controller uses q(u)=10u³−15u⁴+6u⁵ for rest-to-rest segments. Duration satisfies both maxspeed=1.875Δθ/T and maxacceleration=5.773503Δθ/T², with a0.5s minimum. New targets wait for the current segment to finish. Full40° pitch and60° yaw travel require1.25s and1.875s respectively at the command limits; real servo tracking remains unmeasured.

**A calculation-driven revision:** The initial base failed the1N horizontal push screen at100mm height, with a0.80 restoring/demand ratio. Revision A adds a mechanically retained steel ballast and moves the feet outward. The final conservative model uses minimum mass{tip['minimum_total_mass_kg']*1000:.1f}g, CG height{tip['conservative_cg_height_mm']:.0f}mm and support lever{tip['support_lever_mm']:.2f}mm. Gravity is included through the whole-device CG; internal servo gravity torque is not counted a second time.

| Stability screen | Final result |
|---|---|
| Restoring moment |{tip['restoring_moment_Nm']:.5f}N·m |
|1Npush + motion demand |{0.1+a['dynamics']['dynamic_overturning_moment_Nm']:.5f}N·m |
| Moment reserve |{tip['push_with_dynamic_margin_ratio']:.2f}×, analytical only |
| Static tipping angle |{tip['static_tip_angle_deg']:.1f}° against10° target |

Friction and support assumptions still require force-gauge and tilt-table tests. Stop loading is screened from kinetic energy and assumed compliance, including motor stall loading. Printed stop strength and wear are not physically validated.

The minimum stabilizing mass is an assumption, not measured evidence. Fully solid CAD polymer masses can overestimate printed parts with infill. Weigh the finished unit and confirm its CG bounds; if it falls below the analyzed mass floor, increase ballast or rerun the stability balance using measured properties. The490g upper design budget must not be used as guaranteed stabilizing weight.

**Fits:** The88mm yoke gap provides2mm nominal total head clearance. The1mm left pivot washer consumes part of this space. TheØ24pilot/Ø24.4bore stack can reach zero clearance as printed. Finish the pilot toØ24±0.10 and gauge the bore toØ24.40+0.20/−0 for at least0.30mm diametral clearance. Gauge M3 carrier holes to at leastØ3.20. Global STL scaling is not an acceptable substitute for local fit correction.

**Power and heat:** The estimated{t['assumed_peak_current_A']:.2f}A peak current is below the3A source rating;1A per servo and0.20A for logic/audio/display are assumed allowances because the selected manufacturer page does not specify servo stall current. A1000µF capacitor alone drops1V under a1A,1ms step, so wiring and source transient response matter. Common grounding, a Schottky logic feed, a fuse and a5V signal buffer are specified in the electrical architecture.

Estimated1.3W enclosure heat with uncertain natural convection gives{t['estimated_surface_low_C']:.1f}–{t['estimated_surface_high_C']:.1f}°C at30°C ambient. The conservative value exceeds the45°C surface target. Thermal acceptance remains open; measure duty-dependent losses and improve heat rejection or reduce power before release.

<!-- pagebreak -->
## 4. Manufacturing, drawings and assembly

Nine custom rigid components are printed in PETG: base cup, deck, yoke, head shell, bezel, rear electronics carrier, power carrier, switch carrier and button cap. PTFE sheet provides the yaw washer and passive-pivot thrust surface. A stock steel bar is cut and drilled for ballast. Purchased sleeves, hardware, feet and modules complete the assembly.

PETG is selected for accessible prototype fabrication and toughness; PLA is suitable for initial fit coupons, while aluminum remains an option for a support insert if physical testing reveals creep or wear. Production housings are candidates for PC-ABS molding, requiring a separate redesign, resin selection and tooling review. The printed prototype is not a mold-ready design.

![NODI-P03 yoke drawing, sheet1. The linked PDF includes the complete second sheet and section detail.](Images/nodi_yoke_drawing.png)

The two-sheet drawing defines datumsA(plate underside),B(left arm outer plane) andC(front plate edge), axis position toleranceØ0.30RFS, datum flatness0.20, controlled fits and a complete feature schedule. Finish-drilling and gauging are part of the process. General tolerances reflect a prototype process rather than cosmetic precision. Drawing parameters are compared programmatically against the CAD manifest.

**Assembly order:** Inspect coupons and incoming components; retain the ballast; wire and test logic on removable trays; center servos; install yaw motor, deck, thrust washer, horn and yoke; mount the pitch servo in the head; install the sleeve-supported passive pivot and fixed pitch horn; fit the OLED and bezel; route and strain-relieve flexible loops; then perform unpowered clearance checks and current-limited one-axis commissioning.

The full BOM, fastening quantities, required tools, inspection points and service sequence are supplied in the repository. Assembly≤30min is a target excluding printing, soldering and programming; no timed build has been performed. Structural joints remain accessible; unloaded electronics pads and feet may use adhesive.

<!-- pagebreak -->
## 5. Alarm electronics and executed software checks

The Pico usesGP4/GP5 for the I²C RTC/display bus, GP2/GP3 for yaw/pitch servo commands, GP15 for the active-low button andGP16 for a transistor-driven piezo. A74AHCT125 buffer translates servo commands to the5V rail. The dedicated5V/3A source feeds a fused servo branch; a Schottky feed into PicoVSYS avoids backfeeding the logic supply. The full pin table and wiring diagram control the electrical build.

A DS3231 retains local civil time using a CR1220 cell. USB serial commands set time and alarm, and controller settings retain alarm state. Invalid RTC state suppresses the alarm instead of inventing time. No network or daylight-saving service is included. A short press snoozes five minutes; a1.5s hold dismisses the active occurrence. An unattended ring times out after ten minutes.

| Executed check | Evidence / limit |
|---|---|
| Portable C++ controller tests |15 scenario groups pass |
| Alarm edge cases |Minute window, midnight, snooze over midnight, timeout, invalid clock and daily consumption |
| Input/timing cases |Debounce, long press, unsigned millisecond rollover |
| Command-motion sampling |57.329°/s and179.921°/s² for the tested30° trajectory at10ms sampling |
| Actual ARM target compilation |Pico core6.1.0;82,776 flash bytes;10,620 static RAM bytes; exit0 |
| Hardware integration |Not performed; no firmware flashed to a physical Pico |

Compilation and host execution do not validate power integrity, I²C wiring, flash endurance, real RTC retention, servo angle calibration, loudness or user interaction. The sources, pinned dependencies, commands and source hashes are preserved in Firmware/verification_results.md.

The mechanical model uses dimensioned commercial envelopes. It does not contain a detailed PCB layout, certified power design, deformable harness or supplier-approved servo internals. Incoming hardware inspection is a required gate.

<!-- pagebreak -->
## 6. Verification and development roadmap

The requirements matrix maps22 measurable requirements to CAD, calculation, software simulation or future bench testing. Mandatory physical targets include alarm timing,60dBA audible output at0.5m,10,000-cycle screening,≤3° pointing repeatability, loaded motion, thermal limits, stability, safe cable routing and a serviceable assembly. These targets are not claims of completed tests.

| Evidence completed | Physical evidence still required |
|---|---|
| Regenerated solid CAD and exported STEP/STL |Printed-part fit, tool access and incoming module dimensions |
| Solid validity, STEP volume agreement and sampled collision checks |Manual combined-limit cable sweep and calibrated actual travel |
| Reproducible torque, structure, stability, fits and thermal screening |Measured mass/CG, drag, proof load, tipping, current and thermal soak |
| Drawing/CAD parameter comparison |Datum and hole inspection on finished parts |
| ARM compile and host state/motion tests |Complete hardware alarm cycle, sound level, brownout and endurance tests |

**Next prototype gates:**1) fabricate and gauge parts;2) verify the actual servo/horn lot and assemble unpowered;3) power logic alone;4) center and calibrate one actuator at a time;5) test simultaneous alarm/motion;6) close tip, thermal and power requirements before endurance. Stop on contact, sustained stall, repeated brownout or temperature limits. Pinch clearance and consumer compliance need later review.

| Proposed program | Relative schedule and exit |
|---|---|
| Concept and architecture |Weeks1–3: measurable requirements and demonstrated actuator feasibility |
| Detailed CAD / physical prototypes / integration |Weeks4–8: controlled assembly and complete alarm sequence |
| EVT |Weeks9–11: load, tip, heat, noise and initial cycling evidence |
| Iteration |Weeks12–14: root-cause fixes and DVT design freeze |
| DVT and manufacturing development |Weeks15–23: representative units, compliance work, DFM, tooling and first articles |
| PVT |Weeks24–27: pilot yield≥95%, fixtures and traceability |
| Release and ramp |Weeks28–30: approvals, qualified supply and field support |

The critical path runs through architecture, valid CAD, physical integration, EVT, iteration, tooling, PVT and release. DVT/tooling overlap is an explicit cost risk. Reserve2–4extraweeks for a tool correction. The one-day challenge scope covers digital design and documentation; it is separate from this proposed30-week commercial program.

**Review package:** Start with README.md, open CAD/exports/NODI_Assembly_RevA.step, review Drawings/NODI-P03_Yoke_RevA.pdf, then run the calculation and software commands in the README. Detailed sources and assumptions are in Analysis/sources.md and Electronics/architecture.md. No FEA results or physical test data are included because none were produced.
'''
report=report.replace('](Images/','](../Images/')
report=re.sub(r'([a-z]{2,})(?=\d)',r'\1 ',report)
report=re.sub(r'(\d)(mm|MPa|GPa|dBA|m/s²|rad/s²|N·m|ms|µF|°C|°/s|g|V|A|W|s)(?![A-Za-z])',r'\1 \2',report)
for old,new in {'UseSF':'Use SF','useSF':'use SF','SF=':'SF = ','SF2':'SF 2','usesGP':'uses GP','TheØ':'The Ø','toØ':'to Ø','boreØ':'bore Ø','2–4extraweeks':'2–4 extra weeks','receive40':'receive 40','conservative10':'conservative 10','Fifteen':'Fifteen'}.items():report=report.replace(old,new)
(ROOT/'Documentation/engineering_report.md').write_text(report)
print('Composed README.md and Documentation/engineering_report.md from current analysis.')
