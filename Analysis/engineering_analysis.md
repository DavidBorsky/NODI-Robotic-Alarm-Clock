# Engineering analysis — revision A

**Calculated screening results, not experimental validation.** Reproduce with `python Analysis/engineering_calculations.py` after CAD generation. Numeric inputs are in [analysis_inputs.json](analysis_inputs.json); complete outputs are in [analysis_results.json](analysis_results.json). The script reads the actual [CAD manifest](../CAD/manifest.json), records its SHA-256, and derives moving groups from instance membership. No finite-element solver was successfully run; no FEA results are claimed.

## Mass, actuator and geometry basis

| Quantity | Value | Basis |
|---|---:|---|
| CAD assembly mass | 375.5 g | Solid volume × stated density; purchased-component overrides |
| CAD pitch group mass | 92.6 g | Includes the head, display and moving tilt servo |
| Head design mass | 120.7 g | CAD ×1.25 + 5 g cable allowance |
| Total design mass budget | 489.3 g | CAD ×1.25 + 20 g unmodeled wiring allowance |
| Head CAD CG radius from pitch axis | 1.36 mm | Mass-weighted CAD component centers |
| Design CG offset | 10.00 mm | Maximum of CAD radius +5 mm and 10 mm minimum |
| MG90S stall torque at 4.8 V | 0.17652 N·m | Manufacturer 1.8 kgf·cm; conversion 1 kgf·cm = 0.0980665 N·m |
| Assumed operating budget | 0.04413 N·m | Designer-selected 25% of stall, not a continuous rating |

The [source register](sources.md) identifies the manufacturer data and their limitations. Printed PETG density is 1.27 g/cm³. Calculations use reduced modulus **1.0 GPa** and a **10 MPa** stress screening allowable. Neither is a material certificate; interlayer strength, creep and manufacturing variation remain prototype risks. Purchased masses and modeled centers are nominal envelopes, not measured parts.

## Motor sizing and motion

Pitch: `T_required = SF × (m g e + I α + T_friction + T_cable)`, with SF=2, friction=0.003 N·m and cable drag=0.002 N·m. Gravity uses the full design offset in its worst orientation. Inertia is bounded by placing each part's mass at the farthest corner of its actual bounding box in the rotation plane, then applying the mass margin. This avoids an optimistic uniform-box approximation.

| Pitch torque term | N·m |
|---|---:|
| Gravity | 0.01184 |
| Inertia at 180°/s² | 0.00051 |
| Friction + cable allowance | 0.00500 |
| Required including SF=2 | **0.03469** |
| Assumed operating budget / required | **1.27** |

Yaw has no intended gravity term about a vertical axis. Its inertia bound includes the whole tilted head in a bounding sphere plus the yaw platform. `T_yaw = 2 × (I α + 0.003 + 0.002)` = **0.01356 N·m**, with budget reserve **3.25**. Desk inclination, binding, harness drag and servo gear friction can invalidate this allowance. Measure current and cable torque at the travel corners before increasing duty.

For the Ø40/25 mm annular thrust washer, uniform-pressure effective radius is `R_eff=(2/3)(R_o³−R_i³)/(R_o²−R_i²)` = 16.54 mm. A **purely assumed** dry friction coefficient μ=0.10 gives `T≈μ m g R_eff` = 0.00271 N·m, consistent with the 0.003 N·m allowance but leaving little friction margin. Surface finish, preload, contamination and pilot rubbing can increase this. The 0.002 N·m cable-drag allowance corresponds to only 0.10 N tangential force at a 20 mm lever; measure it with a spring scale or torque fixture at combined travel limits.

Stall torque is the zero-speed maximum from the vendor. It is not a safe holding or running rating. The no-load transit speed is about 600°/s; loaded speed under the required torque is not specified. The commanded 60°/s ceiling is deliberately much slower, but that comparison does not validate loaded tracking or life.

Firmware and this analysis use `q(u)=10u³−15u⁴+6u⁵`, with zero endpoint speed and acceleration. `max|q'|=1.875` and `max|q''|=10/√3`; choose `T=max(0.5,1.875 Δθ/60,√((10/√3) Δθ/180))` in seconds/degrees. Full pitch travel takes **1.250 s**, full yaw **1.875 s**. The [sampled profile](motion_profile.csv) is a calculated command trajectory, not a measured response.

## Structural load path

Head → servo horn/opposite pivot → two yoke arms → yaw platform → thrust washer/pilot → base lid → shell/feet. The servo horn transmits drive torque; the washer and opposite pivot are intended to relieve external cantilever loading on servo shafts. Contact, horn spline fit, screw engagement and actual load sharing require bench confirmation.

The yoke arm is idealized as a cantilever of free length 50 mm, section 4 mm in X ×12 mm in Y. Vertical **3 g** head load is axial; it is not treated as an arbitrary horizontal shock. Pitch reaction bends the arm in its stiffer plane, with the full drive moment assigned to one arm. `I_strong=b d³/12`, `I_weak=d b³/12`, `σ=F/A+Mc/I`, `δ_M=M L²/(2 E I)`, `δ_F=F L³/(3 E I)`. Lateral load includes tangential `m r α` and centripetal `m r ω²` terms using a conservative CG radius.

| Structural screen | Result |
|---|---:|
| Vertical proof load per arm | 1.776 N |
| Driven-arm pitch moment | 0.04653 N·m |
| Combined axial + bending stress | **0.545 MPa** |
| 10 MPa allowable / modeled stress | 18.3 |
| Combined arm displacement | **0.113 mm** |
| M3 pivot single-shear stress | 0.251 MPa |
| Printed pivot bearing stress | 0.148 MPa |
| Base screw-boss average vertical bearing | 0.087 MPa |
| Average four-foot contact pressure | 0.0106 MPa |
| Main shell average vertical wall stress at 3 g | 0.0136 MPa |

The main 2.4 mm deck is also screened as a simply supported beam surrogate: span 95.2 mm, effective width `120−24.4=95.6 mm` (the central bore removed over the whole span), central rotating-assembly proof load 4.92 N. `σ=(F L/4)(t/2)/I` and `δ=F L³/(48 E I)` give **1.28 MPa**, **0.80 mm at 3 g**, and **0.27 mm at normal 1 g**. This rough model omits two-dimensional plate action, counterbores, load distribution and the actual edge/fastener contacts, so it is not a validated displacement prediction or upper bound. It identifies deck compliance and pilot/horn rubbing as physical inspection priorities. The 0.5 mm displacement acceptance applies to the yoke arm; **the complete assembly has not demonstrated equivalent stiffness**. Increase deck ribbing/thickness or add a supported bearing bridge if measured movement changes running clearance.

Fastener calculations check external load only: `τ=F/(πd²/4)` and printed bearing `p=F/(d t)`. Bearing uses a conservative 3 mm projected diameter; the actual passive pivot includes a 4 mm sleeve. These checks do **not** establish thread pullout, insert retention, horn strength, preload or resistance to loosening. Boss calculation uses four effective 8 mm OD /3.4 mm ID net bearing sections, conservatively removing more material than the CAD Ø2.7 thread pilot. Inspect the actual boss load path. Do not torque polymer screws to metal-joint values. Use low assembly torque and mark/check fasteners during cycling.

The idealized weak-plane arm mode is **25.4 Hz**, obtained from `k=3EI/L³` and `f=(1/2π)√(2k/m)`. This is not a modal FEA or measured resonance; joint compliance, servo control and plastic damping are omitted. Slow gestures avoid deliberate excitation near this estimate, but camera/accelerometer and acoustic checks remain necessary.

## Dynamics, tipping and stop fault

At the 60°/s ceiling the bounded pitch kinetic energy is **0.000088 J**. If absorbed over an assumed 2° compliant stop travel, energy balance gives average inertial torque **0.00253 N·m**. Adding a stalled motor gives an average force of **14.92 N** at the CAD's 12 mm pitch-stop radius. Peak force may be substantially higher. The current printed stop has no characterized compliant bumper, so the assumed 2° absorption must not be treated as a provided feature or guaranteed deflection. This is a **fault-load estimate**, not demonstrated stop survival. Printed stops are secondary travel protection; firmware limits must avoid contacting them.

Stability uses a minimum mass equal to **80%** of nominal CAD mass (not the heavy mass budget), a foot support half-span of 49 mm in Y, and whole-assembly CG offset enlarged by the head design eccentricity. CG height is at least 60 mm. Modeled restoring moment is **0.1223 N·m**; horizontal dynamic reaction is **0.042 N**. Gravity is included once through the displaced whole-device CG; the added dynamic moment includes translational and rotational inertia, without double-counting internal servo/cable reaction torque. Predicted static tip angle is **34.7°**. Restoring / (1 N push at 100 mm + dynamic moment) is **1.17**. These calculations omit table motion, an off-axis power cable pull and compliant feet. Measured tip, slip and impulse tests are required. Assumed foot friction μ=0.4 gives a sliding threshold of **1.18 N**; the actual desk/foot pair can differ greatly.

**Mass acceptance gate:** The fully solid CAD polymer mass is not a measured lower bound; slicer infill can substantially reduce it. This result assumes an as-built stabilizing mass of at least **301 g** and the stated CG bounds. Weigh the finished unit and verify CG/tilt before claiming that reserve. Solving the same level-desk moment balance gives a theoretical threshold of **260 g** at the assumed CAD CG and head-offset allowance, but that threshold has no reserve and is not an acceptance substitute. If the unit is below the modeled mass floor, increase/retain ballast or rerun the balance with measured mass/CG; do not use the 490 g upper mass budget as stabilizing weight.

The assumed static sliding reserve is **1.13** against the 1 N push plus simultaneous horizontal inertia (1.042 N). This is conditional on μ=0.4; force-gauge testing on the intended desk must establish actual friction. A tip calculation alone does not establish resistance to sliding.

## Fit and tolerance chains

| Interface | Nominal | Worst case with stated assumptions | Disposition |
|---|---:|---:|---|
| 88 mm yoke gap −86 mm head width | 2.00 mm total | 1.60 mm total | Accounts for ±0.2 mm on each linear dimension |
| Above gap after one 1.0±0.1 mm washer | — | 0.50 mm remaining | Set axial retention with actual horn/pivot stack; this is not automatic equal side clearance |
| Ø24.4 bore −Ø24.0 pilot | 0.40 mm diametral | -0.00 mm | As-printed tolerance stack can consume all clearance; measure/finish the bore and pilot before operation |
| Finished bore Ø24.40 +0.20/−0 and pilot Ø24.00±0.10 | 0.40 mm diametral | 0.30 mm | Drawing/process fit after controlled finishing and gauging; not an as-printed guarantee |
| Ø3.3 deck hole −M3 nominal screw | 0.30 mm diametral | 0.10 mm | Deburr and gauge; position error is separate from size clearance |
| Ø3.2 carrier hole −M3 nominal screw | 0.20 mm diametral | 0.00 mm raw; 0.20 mm after finishing | Ream/drill and gauge finished hole ≥3.20 mm; nominal printing alone can consume all clearance |

The pan pilot is an intentional unresolved process risk: use a calibration coupon, deburr and finish to a freely rotating measured fit. Simply printing the nominal CAD does not guarantee motion. Cable bend radius, vendor servo ear offsets, horn thickness and commercial-module tolerances require the assembly inspection. CAD collision checks do not include flexible cable shape or printed surface roughness.

## Thermal and power screen

Assumed dissipated heat is **1.30 W** (logic/display/alarm 0.8 W plus 0.25 W average heat per servo). For a 120×100×32 mm base, bottom excluded and 75% effective exposed area, `A=0.01956 m²`. A lumped convection/radiation estimate `T_surface=T_ambient+P/(h_eff A)` at 30 °C gives **36.6–46.6 °C** across `h_eff=10–4 W/m²K`. The low-transfer case can exceed the 45 °C target. Heat is spatially distributed, so this base-only lumped screen cannot predict servo winding or controller junction temperature. Actual power/duty and blocked-vent tests must resolve it.

Provisional peak-current budget is **2.20 A** (0.20 A logic + two assumed 1.0 A stalled servos) against a proposed 5 V/3 A external supply, matching the electrical architecture. Manufacturer servo stall current is not specified. Use protected power distribution, common ground, decoupling and a current-limited first power-up; verify the actual servo supply stays within its rated range. A 1,000 µF capacitor alone supporting a 1 A transient for 1 ms would droop **1.0 V** by `ΔV=IΔt/C`: capacitance is not a substitute for a suitable supply, wiring and transient measurements.

## Numerical acceptance record

| Analytical check | Result |
|---|---|
| pitch torque within assumed operating budget | PASS within stated model |
| yaw torque within assumed operating budget | PASS within stated model |
| yaw washer friction estimate within allowance | PASS within stated model |
| mass budget below 0 50kg | PASS within stated model |
| arm stress below screening allowable | PASS within stated model |
| arm displacement below 0 5mm | PASS within stated model |
| static tip angle at least 10deg | PASS within stated model |
| one newton push tip screen | PASS within stated model |
| one newton push sliding screen with assumed friction | PASS within stated model |
| pan pilot has positive worst case clearance as printed | OPEN / model does not demonstrate target |
| pan pilot has positive clearance after specified finishing | PASS within stated model |
| carrier holes have positive worst case clearance as printed | OPEN / model does not demonstrate target |
| carrier holes have positive clearance after specified finishing | PASS within stated model |
| thermal low h below surface target | OPEN / model does not demonstrate target |
| assumed peak current below supply rating | PASS within stated model |

Every pass is conditional on the model assumptions. Open screens are deliberately retained. The [verification plan](../Documentation/requirements_and_verification.md) lists the required prototype tests, and [development roadmap](../Documentation/development_timeline.md) separates the one-day digital scope from commercial EVT/DVT/PVT.
