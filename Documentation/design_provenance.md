# Design provenance and evidence boundaries

NODI revision A is a computational engineering design package prepared for David Borsky's Human Computer Lab mechanical engineering challenge. CAD, calculations, software and documentation were created with AI assistance and checked by executable geometry, numerical and software checks documented in this repository. The design has not been fabricated or tested on hardware. It should be reviewed and understood by the applicant before submission.

The product views are renders of the exported CAD meshes. OLED pixel artwork illustrates intended time/eye graphics; it is not a photograph or evidence that the electronics were operated. Commercial modules are simplified dimensioned envelopes, not reverse-engineered vendor manufacturing models. The rendered wiring is not a validated flexible harness.

| Evidence class | What it means here |
|---|---|
| Executed computational check | A script actually ran; its assumptions and output are supplied. Solid validity, STEP readback, checked collision poses and firmware host scenarios fall here. |
| Calculated estimate | A first-principles equation or CAD volume with assumed inputs. It is reproducible but does not establish physical performance. |
| Software simulation | Deterministic controller/motion execution without the motors, power rail, RTC or display hardware. |
| Proposed test | A future physical measurement with pass criteria. No measured outcome is implied. |
| Purchased specification | A linked manufacturer's nominal value. The selected procurement lot must be checked, especially microservo dimensions, horn spline and stall current. |

No FEA solver was run; there are no finite-element stress contours or FEA result files. Analytical stresses are not labeled as FEA. No assembly, acoustic, durability, power, thermal or alarm hardware tests have occurred. Firmware hardware builds and simulation results are distinguished in the firmware documentation.

The 24-hour challenge scope is the intended scope of the proof of concept, not a claim about human labor hours. The product-development roadmap is a proposed commercial program, not completed development.
