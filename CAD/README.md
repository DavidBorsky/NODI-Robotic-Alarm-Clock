# Editable mechanical assembly — revision A

The source is **[build_nodi.py](build_nodi.py)**, an executable CadQuery boundary-representation model. Dimensions, bores, walls, bosses, mounting interfaces and stops are editable in the Python source; selected design parameters are also collected in [parameters.json](parameters.json). This is actual solid CAD, with individual STEP files and printable meshes, rather than geometry reconstructed from a render. The design is a digital proof of concept; no physical prototype has been fabricated or measured.

## Open the design

- **Complete, colored assembly:** [NODI_Assembly_RevA.step](exports/NODI_Assembly_RevA.step). Open with FreeCAD, SolidWorks, Fusion, Onshape or another STEP-capable CAD system. STEP imports are editable solids, but preserve no CadQuery feature history; edit the Python source to regenerate the design intent.
- **Exploded assembly:** [NODI_Exploded_RevA.step](exports/NODI_Exploded_RevA.step). Explode vectors are presentation offsets, not a mandatory assembly sequence.
- **Individual solid bodies:** [exports/STEP](exports/STEP). Files use descriptive instance names, including purchased envelopes and fasteners.
- **Custom PETG part meshes:** [exports/STL](exports/STL). Each is recentered in X/Y and moved to minimum Z=0. Orient it in the slicer as described below.
- **Every component mesh in assembled coordinates:** [exports/meshes](exports/meshes), including the machined steel ballast; these placed meshes also drive the rendered images. A mesh export does not imply a steel component should be printed.
- **Exact part inventory, colors, estimated masses, centers, motion groups and explode vectors:** [manifest.json](manifest.json).

All dimensions use millimetres. X points right, Y rearward and Z upward. The front faces −Y. Neutral pitch passes through `(0,0,88)` parallel to X. The yaw axis is the Z axis at X=Y=0. Travel is yaw ±30° and pitch −15°/+25°. Mechanical stop contacts are nominally yaw ±35° and pitch −20°/+30°.

## Regenerate

From the repository root, using Python 3.11:

```bash
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python CAD/build_nodi.py
.venv/bin/python CAD/check_motion.py
.venv/bin/python CAD/verify_exports.py
```

CadQuery 2.6.1 with OpenCASCADE 7.8.1.1 generated the committed exports. `build_nodi.py` regenerates the manifest, STEP assemblies, individual STEP bodies, placed component meshes, printable custom meshes and [validation.json](validation.json). `check_motion.py` generates [motion_validation.json](motion_validation.json). `verify_exports.py` reads both assembly STEP files and all76 STLs, checks mesh watertightness and records the all-body neutral-pose audit with explicit thread-engagement exceptions in [export_validation.json](export_validation.json). Run the analysis script again after changing CAD so its recorded mass properties match the exported assembly.

The Python source is the manufacturing geometry authority. Interface coordinates are deliberately fixed at revision A, including display mounting, stock servo tabs and fasteners; changing an envelope parameter requires updating its dependent interface dimensions and re-running clearance checks. The script is not intended to scale the complete robot by changing one number. Each feature remains editable in source.

## Mechanism and load path

The pan servo sits on two integral cup supports at its mounting flange. A match-drilled 19 mm disc horn drives the yoke. The yoke's Ø24 pilot runs in the deck's Ø24.4 bore; an OD40/ID25×2 PTFE annular washer carries axial weight. The yaw servo positions the stage and does not serve as the sole head-weight bearing. Check the actual washer thickness and servo shaft engagement before assembly; the interface drawing assumes the washer is 2 mm thick at assembly load.

The tilt motor is **inside the head**. Its case mounts to two integral posts, while its output horn is fixed to the right yoke arm. Commanding the motor rotates its case and the head relative to that fixed horn. The left head boss turns on a brass sleeve OD4/ID3.2×14.2 mm. An M3×20 bolt and DIN985 locking nut clamp the sleeve. Yoke arm4 + PTFE washer1 + head boss9 =14 mm, leaving nominal 0.2 mm axial float. Confirm this float by hand; trim the sleeve only after measuring the manufactured stack.

The left yoke pad has an OD28/ID19 annular recess 1.4 mm deep on its inner face to clear the moving stop lug; the central thrust-washer seat remains intact. The sleeve and two horns need no modeled rolling bearing. Printed pilot and sleeve fits require reaming/sanding and a prototype rotation check. All shaft and fastener models are simplified, and modeled fastener threads are omitted.

## Purchased interface assumptions

The MG90S body envelope and 13.4 g mass follow the [manufacturer listing](https://torqpro.com/product/mg90s-analog/). The tab pattern and output shoulder locations in this model are engineering interface assumptions; the manufacturer's public size specification does not fully constrain them. **Measure the incoming servo sample before printing the final head and base.** The disc horns must fit that sample's spline and must be match-drilled and tapped M2 using the yoke's clearance pattern; do not assume every nominally compatible micro-servo horn is interchangeable. Horn axial envelopes include a spline socket, but spline teeth are omitted.

The OLED envelope uses the Adafruit938 PCB35.6×33 mm and mounting pattern30.5×28 mm, with actual active screen area29.42×14.70 mm. Other purchased electronics are packaging envelopes for integration, not detailed vendor CAD. Modules are bonded to their removable carriers with insulated adhesive mounting pads; wiring, adhesive films, board-level passive components and solder joints are omitted from solid geometry. Their allowance belongs in the analysis mass budget.

M2 mounting pilots are Ø1.8 and M3 pilots Ø2.7 for hand tapping into the PETG proof of concept. Tap and trial-fit on a printed coupon. They are not clearance holes. Repeated service is a reason to introduce heat-set inserts in a subsequent revision, rather than repeatedly recutting plastic threads. The four power-carrier screws are M3×5; their blind pilots leave 0.6 mm of base floor and the screw tips stop above that floor.

## Harness route and access

The head has an Ø8 bottom exit at local `(0,15,58)`. Route the moving display and tilt leads in an approximately 80 mm loose rear service loop to the fixed deck's Ø10 grommet bore centered at `(0,34)`. Use an insulating grommet with approximately Ø6 clear ID. Keep the loop above and behind the yoke plate, restrained on both sides with adhesive tie mounts. The pan pilot is occupied by the horn and is **not a cable passage**. At the USB cable inlet, an insulating sleeve and nylon tie through the two Ø2.5 floor holes at X45/Y24 and32 provide strain relief; keep the tie below 2.5 mm protrusion under the 3 mm feet. Inside the base, run the harness below the deck to the board headers, maintaining clearance from the pan horn and stop lug.

The snooze cap rests 0.8 mm above the deck (cap undersideZ32.8, deckZ32), leaving clearance for the switch stroke; bond its stem to the actuator with a small removable adhesive pad and verify release. Cable bend radius, pinching and service-loop placement need a physical motion test at all pitch/yaw combinations. Cables are absent from the collision model; geometric solid clearance is not evidence of cable fatigue life. Fasten the pan horn and its retaining screw before installing the head so the central screwdriver path remains accessible. The front bezel removes independently to access the display and tilt servo.

## Prototype printing and machining

Use PETG, nominal 0.4 mm nozzle, 0.2 mm layer height, five perimeters and locally solid arm/pivot/boss regions as an initial process proposal. Slicer settings and printed material properties have not been tested. CAD-derived polymer masses assume fully solid material and are upper-bound geometric estimates rather than slicer predictions.

- Base cup: floor down; inspect the raised servo and switch supports.
- Deck and electronic carriers: flat on the bed. Carrier fastener counterbores face up.
- Yoke: orient so arm bending stress lies predominantly in the printer's stronger plane, use local solid infill and support the pilot; compare an upright print with a side print before structural acceptance. Printed orientation is part of the planned proof test.
- Head shell: rotate so its open front faces upward; use support under the passive pivot and internal cradle where needed. Inspect bore alignment before tapping.
- Bezel: external face down on a clean bed, stand-offs upward.
- Button: cap face down, stem upward.
- Ballast NODI-P10: saw/mill 40×18×12.5 mm low-carbon-steel plate, drill two Ø3.4 through holes at X=−10 and18 relative to assembly coordinates (6 and34 mm from the left edge), Y on the centerline. Deburr and corrosion-protect; retain with both M3×18 screws. This part is not a printed mass substitute.

The steel ballast and outboard silicone feet are necessary parts of the analyzed stability configuration. Do not remove the ballast and claim the same push resistance.

## What the CAD checks establish

[validation.json](validation.json) records per-body validity, STEP read-back and exact solid intersection tests at seven poses, including all extreme soft-limit combinations. Commercial envelopes and all main structural parts participate in the structural overlap audit; no broad overlap exclusions conceal geometry clashes. Screw/pilot engagements are represented by nominal smooth shanks, so their intentional thread engagement is outside that audit.

[motion_validation.json](motion_validation.json) separately records selected interacting pairs at 1° increments and checks nominal hard-stop contact plus interference one degree beyond. Touching bearing, sleeve and horn interface surfaces are intentional. A discrete digital sweep is not a continuous contact simulation, and these checks do not validate friction, tolerances, cable behavior, actuator backlash, printed strength or physical assembly. Those remain in the prototype test plan.
