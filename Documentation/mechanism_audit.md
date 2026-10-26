# Mechanism audit — revision A

Audit date: 25 October 2026. Scope: the committed solid geometry, its drive interfaces and the evidence needed to establish real motion. This is an independent source/geometry review, not a fabricated assembly or a measured test.

## Finding

The design contains a mechanically plausible two-axis arrangement: a base-mounted yaw servo drives the yoke, and a head-mounted pitch servo reacts against a horn attached to that yoke. The nominal bodies and screws connect the intended parts. That supports the design concept; it does **not** establish that an assembly made from these files will move correctly.

The original assembly STEP contains positioned solids, without joint definitions. The original pose function rotates tagged groups around prescribed axes. Its collision sweep asks whether those prescribed positions overlap; it does not discover the degrees of freedom, solve a powered mechanism, or prove that the motor/horn interface transmits torque. Any separately supplied articulated assembly must be interpreted within that same physical evidence boundary.

## Interfaces traced in the source

Dimensions below are nominal millimetres in assembly coordinates: X right, Y rear, Z up. The front faces −Y.

| Interface | Geometry and attachment | Audit conclusion |
|---|---|---|
| Yaw servo case → base | Base posts reach Z24; the servo flange occupies Z24–26. Two M2×8 screws pass through the flange and into base pilots. | A nominal mounting path is present. The tab pattern remains an incoming-component assumption. |
| Yaw shaft → horn | Shaft Ø4.8 reaches Z32.4; the horn socket occupies Z30.4–32.4. Its disc reaches Z34. A central retaining screw seats on the horn through the yoke access opening. | There is 2.0 mm of nominal socket/shaft overlap. The smooth coaxial surfaces do not model a torque-transmitting spline. |
| Yaw horn → yoke | Horn disc ends at Z34 and the plate begins at Z34. Two screws at X=±7 pass through the plate into the horn. | Contact and a fastening path are present; there is no unexplained axial gap. |
| Yoke → deck | Plate underside Z34 rests on a PTFE washer at Z32–34. The Ø24 pilot spans Z29–34 inside a Ø24.4 deck bore at Z29.6–32. | The intended axial/radial support is represented. Actual support load sharing and free rotation remain unverified. |
| Pitch horn → yoke | Horn disc spans X41.8–44 and the right arm begins at X44. Two screws at Y=±7 pass through the arm into the horn. | The horn is nominally fixed to the yoke, not to the head. |
| Pitch servo case → head | Transformed flange spans X33.4–35.4; head mounting posts begin at X35.4. Two mounting screws enter the head posts. | The case and head form the moving side of the pitch actuator. The inverse drive arrangement is mechanically possible. |
| Pitch shaft → horn | Shaft reaches X41.8; horn socket spans X39.8–41.8. The center retaining screw is accessible through a Ø6 right-arm opening. | Again, 2.0 mm of nominal engagement is modeled, but the purchased spline is not defined. |
| Left head → passive support | Yoke arm X−48…−44, PTFE washer −44…−43, head boss −43…−34. Sleeve length 14.2 spans −48…−33.8, retained by an M3 screw and nut. | The nominal bearing stack is 14.0 mm with 0.2 mm axial clearance. Neither that clearance nor sleeve stationarity is guaranteed after manufacture. |

Source locations: [base supports](../CAD/build_nodi.py#L103), [washer, deck and pilot](../CAD/build_nodi.py#L132), [yoke interfaces](../CAD/build_nodi.py#L146), [head cradle and passive boss](../CAD/build_nodi.py#L172), [servo and horn envelopes](../CAD/build_nodi.py#L207), [passive pivot](../CAD/build_nodi.py#L243), and [fasteners](../CAD/build_nodi.py#L310).

Read-only OpenCASCADE checks on 25 October found zero gap and zero positive intersection volume for each horn/servo and horn/yoke pair in neutral. The sleeve has 0.10 mm radial clearance to each of the nominal Ø4.2 yoke/head bores. These are geometry observations; zero gap is not proof of a secured joint.

## Open engineering issues

### 1. The torque coupling is a purchased interface assumption

Both servo outputs are modeled as cylinders, and both horn sockets as smooth matching bores. The source explicitly identifies the flange/horn pattern as an assumed interface. A smooth cylindrical fit supplies no positive rotational lock; real operation depends on purchasing a horn with the correct spline, sufficient socket depth, the actual output shoulder position and a compatible retaining screw. The simplified model is appropriate for an envelope check, but cannot certify that coupling.

Before releasing print geometry, measure an actual selected servo/horn set, record the spline compatibility and axial stack, and replace the assumed dimensions with checked component interfaces. Keep the real horn's spline feature as supplied vendor CAD where available, or identify it in a controlled interface drawing; inventing plausible teeth would add no verification. [Purchased-interface limitations](../CAD/README.md#purchased-interface-assumptions).

### 2. A stationary passive sleeve is not positively located

The Ø4 sleeve is a clearance fit in both the head boss and the yoke. The bolt and nut clamp the sleeve ends, but no key, press fit, split clamp or other antirotation feature attaches the sleeve to the yoke. The bolt/sleeve/nut may rotate relative to the yoke, depending on friction. The source's assignment of this hardware to the yaw group is therefore an assumed behavior, not an enforced constraint.

This does not by itself prevent head motion: a floating sleeve may act as a plain bearing. Choose and document the intended bearing arrangement. If the sleeve must stay fixed to the yoke, add a deliberate retention/antirotation feature and check its effects on the thin printed arm. Otherwise model and describe it as a retained floating sleeve, and test wear at both interfaces.

### 3. Nominal 0.2 mm endfloat is smaller than the unfinished tolerance stack

The sleeve is only 0.2 mm longer than arm + washer + boss. The yoke drawing's general ±0.25 mm linear tolerance alone can consume that nominal clearance; the washer, boss and cut sleeve add further variation. The documents already require fitting by measurement. A calculated 0.2 mm nominal gap is therefore not an as-built clearance guarantee.

Measure the complete stack and select/finish the sleeve to a defined positive clearance. Confirm the head rotates freely with the fastener tightened against the sleeve. A loose nut is not a valid substitute. Introduce specific length tolerances or a shim/shoulder arrangement before claiming repeatable kit assembly. [Assembly instructions, step 12](../Manufacturing/assembly_instructions.md#assembly-sequence).

### 4. Axial load sharing is not solved

At nominal geometry, the horn simultaneously fixes the yoke height relative to the servo shaft and the PTFE washer touches the deck. No compliant or floating drive feature separates these axial constraints. Washer thickness, horn seating and deck deflection determine how much load reaches the servo shaft. The deck's separate beam surrogate predicts approximately 0.27 mm deflection at 1 g; it is not a coupled contact analysis of this interface.

Check the assembled stack and deck deflection under the real head load. Confirm support contact and rotation without shaft preload or rubbing. If this cannot be maintained, stiffen the deck/support or introduce an axially compliant torque coupling. The support concept should be described as intended to relieve the servo shaft, without claiming measured load isolation. [Deck estimate and load path](../Analysis/engineering_analysis.md#structural-load-path).

### 5. Pitch mounting and tool access need an assembly trial

The horn and retaining-screw access bores clear the modeled screw heads. That is useful evidence, but no driver/tool envelope or insertion-path simulation was performed. The two pitch-servo mount screws face along X inside the shell; the side walls block an unrestricted straight approach from outside along X. A suitable short bit/right-angle tool or a demonstrated insertion sequence is needed. The nut may require the specified miniature spanner rather than a conventional long nut driver.

Trial the actual tools on the open shell, servo and passive pivot before accepting the assembly-time target. Update the tool list or access features after that trial. Screw-head clearance alone does not establish tool accessibility.

## What would demonstrate motion

1. An articulated CAD model should define the fixed base, yaw joint and pitch joint with the corresponding rigid component groups. Driving either angle should leave the attachment interfaces together and move the correct case/horn side of the inverse pitch drive.
2. A mechanism view should expose the base servo, both horns, pitch case mounts, passive pivot and support washer, with axis and load-path labels. This makes the intended physical movement inspectable without hiding it behind the shells.
3. Purchased hardware and finished parts must be measured and assembled. Verify the passive bearing and the unpowered combined sweep with the fasteners seated, then calibrate each powered axis gradually and measure travel, current, tracking and clearance under the actual head load.

The first two items establish a better digital mechanism definition. Only the third can establish that the constructed robot actually moves as intended. Existing valid solids, watertight meshes and sampled non-interference results remain useful evidence with that limit.
