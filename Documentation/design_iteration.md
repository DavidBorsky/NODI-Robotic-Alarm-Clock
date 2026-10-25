# An analysis-driven design change

The first completed CAD assembly had no ballast and feet at Y = ±35 mm. The calculation run used a conservative support half-span of 40 mm, 80% of nominal CAD mass as the minimum stabilizing weight, a 60 mm minimum CG height, and an enlarged head CG offset. It predicted sufficient static tilt resistance, but the **1 N horizontal push at 100 mm height did not pass**.

This finding triggered a mechanical change: a low-mounted steel ballast block and wider foot placement. The ballast is included in the parametric assembly, manufacturing plan and BOM; it is not an unmodeled mass added only to the calculation. Two accessible M3 screws retain it on integral base bosses.

| Quantity | First assembly | Revised submission assembly |
|---|---:|---:|
| Nominal CAD mass | 304.6 g | 375.4 g |
| Foot centers in Y | ±35 mm | ±44 mm |
| Conservative support half-span | 40 mm | 49 mm |
| Minimum stabilizing mass (80% CAD) | 243.6 g | 300.3 g |
| Restoring moment | 0.08311 N·m | 0.12229 N·m |
| 1 N push + bounded inertial moment | 0.10415 N·m | 0.10415 N·m |
| Restoring / applied moment | **0.798 — fails screen** | **1.174 — passes screen** |
| Conservative static tip angle | 30.10° | 34.68° |

The added ballast is 40 ×18 ×12.5 mm steel, with two Ø3.4 mm through holes, mounted low in the base. The final approximately 489.3 g total design mass budget includes the nominal CAD mass ×1.25 and 20 g unmodeled wiring. Its margin to the 500 g target is only approximately 10.7 g; weigh the real assembly and revisit the mass budget if any purchased module, cable or fastener differs.

The unballasted [executed result record](../Analysis/iteration_01_unballasted_results.json) retains its original CAD-manifest hash. The [final result](../Analysis/analysis_results.json) is regenerated from the current CAD manifest. The old CAD geometry is not a second submission assembly; the record is retained to show the numerical reason for the change. Both results are calculations, not measured tip tests.

The whole-device stability equation includes head gravity once through the displaced total CG. Only translational/rotational inertial moments are added dynamically; an early review removed double-counting of internal servo gravity reaction. The table uses the corrected equation consistently before and after the design change.

The final 1.174 reserve is an early screen, not a robust qualification margin. It assumes at least 301 g as-built stabilizing mass (rounded up from the model's 300.3 g floor) and the modeled CG bounds. Infill can make printed parts lighter than the fully solid CAD estimate. Desk friction, cable pull, foot compliance and actual mass distribution still need force-gauge and tilt-table tests. Remaining process risks include printed pilot/carrier fits, deck compliance and thermal uncertainty, recorded explicitly in the analysis and verification plan.
