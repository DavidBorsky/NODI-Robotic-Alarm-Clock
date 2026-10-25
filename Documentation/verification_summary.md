# Executed verification — revision A

Date: 2026-10-24. This record describes executed computational checks. No prototype was fabricated, powered or physically tested.

| Check | Executed result | Evidence |
|---|---|---|
| Parametric CAD regeneration | 67 valid, single solid bodies | [CAD validation](../CAD/validation.json) |
| Individual STEP readback | All 67 valid; relative volume error <1e−7 | [CAD validation](../CAD/validation.json) |
| Assembly / exploded STEP readback | Both contain 67 valid solids | [Export audit](../CAD/export_validation.json) |
| STL readback | All 76 meshes watertight, positive volume and consistent winding | [Export audit](../CAD/export_validation.json) |
| All-body neutral overlap audit | No unexpected intersections; 35 explicit smooth-shank/thread-pilot engagements | [Audit and exact exclusions](../CAD/export_validation.json) |
| Motion geometry | 490 selected exact solid-pair checks at 1° increments, no intersections; nominal hard-stop contact checked | [Motion coverage and limits](../CAD/motion_validation.json) |
| Minimum checked head/yoke gap | 1.00 mm nominal | [Motion report](../CAD/motion_validation.json) |
| Analytical calculations | Executed from current CAD manifest; hashes bind geometry and assumptions | [Numerical results](../Analysis/analysis_results.json) |
| Drawing agreement | 27 dimensions/feature groups agree with CAD manifest | [Drawing check](../Drawings/drawing_geometry_check.json) |
| BOM reconciliation | 47 rows; all 66 nonvisual CAD instances and 20 electrical items mapped once | [BOM](../Manufacturing/BOM.csv), [check script](../Manufacturing/build_bom.py) |
| Controller host execution | 15 scenario groups pass | [Firmware verification](../Firmware/verification_results.md) |
| Actual ARM compilation | Exit 0; 82,776 bytes flash; 10,620 bytes static RAM | [Compiler record and source hashes](../Firmware/verification_results.md) |
| Documents and links | PDFs parse; local Markdown links and credential patterns checked | [Package audit](package_audit.json) |

The motion sweep is discrete and covers the interacting pairs listed in its source; it is not a continuous flexible-harness simulation. Threads are omitted from commercial fastener solids. Commercial modules are nominal envelopes; incoming dimensions and spline interfaces require inspection.

The analytical pass conditions depend on measured mass/CG, assumed friction, cable drag, reduced material properties and finished fits. Raw printed pilot and carrier-hole tolerance stacks can close their clearances, so finishing and gauging are required. The thermal upper estimate exceeds its target; deck compliance, local stress concentrations, creep and fatigue require physical tests. No FEA was run or claimed.

Reproduce the checks using the commands in [the README](../README.md). The [requirements matrix](requirements_and_verification.md) preserves all physical acceptance tests still open. Publication access is checked separately after the repository is pushed.
