# Development roadmap — revision A

This submission is a one-day-scale **digital proof of concept**: CAD, analysis, drawings, proposed manufacturing, controls and verification planning. No elapsed fabrication, assembly, hardware verification or commercial readiness is implied by the completed digital files. A physical one-day build also needs stocked electronics, a functioning printer, and a known print duration.

## 24-hour challenge allocation

| Hours | Work | Exit deliverable | Constraint |
|---|---|---|---|
| 0–2 | Requirements, three concepts, interfaces and actuator sourcing | Requirements and concept selection | Freeze travel, purchased envelopes and evidence labels |
| 2–8 | Parametric assembly, load-path geometry, initial torque/stability model | Regenerable CAD and first sizing results | Keep one common servo family; remove features if inaccessible |
| 8–12 | Motion clearance review, drawings, exploded views | STEP/STL, inspection drawing and assembly order | Resolve collisions before presentation work |
| 12–16 | Electronics architecture, firmware state logic and manufacturing plan | Wiring, BOM, controls and material rationale | Firmware remains untested without hardware |
| 16–20 | Re-run calculations and geometry checks; inspect deliverable consistency | Machine-readable validation records | Correct shared dimensions/mass before release |
| 20–24 | Report, showcase, package and public-link review | Reviewable repository and PDF | Preserve honest limitations; do not replace missing tests with claims |

Parallel work can overlap documentation and electronics with CAD after interface freeze. Physical printing may begin after hour 8 only if stock and print time permit; a long print moves hardware validation to the subsequent program. The critical path is **interfaces → valid CAD → collision/mass checks → drawing consistency → package verification**.

## Commercial development scenario

The schedule below is a planning estimate for a small team with one mechanical engineer, one embedded engineer and part-time industrial design/operations support. Weeks are relative to project kickoff, not promised dates. Allow **approximately 30 weeks**, including explicit iteration and tooling dependencies. Certification, supplier changes or additional tool corrections may extend it.

| Phase | Weeks | Duration | Tasks and deliverables | Dependencies / main risk | Objective exit gate |
|---|---|---:|---|---|---|
| 1. Requirements and concept freeze | 1 | 1 wk | User needs, alarm interaction, safety/use envelope, cost and noise targets | Stakeholder access; unclear user expectations | Signed measurable requirements and agreed cost/volume assumptions |
| 2. Architecture and feasibility | 2–3 | 2 wk | Servo characterization, power transients, mockups, three-concept review | Phase 1; noisy or inadequate actuator | Loaded torque/current/travel margin demonstrated on bench; architecture review passed |
| 3. Detailed prototype CAD and analysis | 4–5 | 2 wk | CAD, tolerance chains, drawings, service access, initial BOM | Phase 2 purchased-part freeze; geometry change | Drawing/CAD review closed; all motion paths and load assumptions identified |
| 4. Fabrication and assembly | 6–7 | 2 wk | Print/CNC brackets, procure stock parts, build 3 prototypes | Phase 3; vendor variation or reprints | Three units assembled to controlled BOM with fit issues recorded |
| 5. Controls/electronics integration | 6–8 | 3 wk | PCB/firmware, timekeeping, brownout mitigation, alarm UX | Phase 2; can overlap fabrication | Full alarm/snooze/dismiss sequence passes on 3 units; power rails meet targets |
| 6. Engineering validation (EVT) | 9–11 | 3 wk | Load, tip, heat, acoustic, cable and 10,000-cycle screening | Phases 4/5; servo/cable failures | EVT matrix closed or approved corrective actions; no unresolved critical failure |
| 7. Design iteration | 12–14 | 3 wk | Root-cause fixes, reduce part count, production material changes | EVT; new mechanism may restart tests | Changed parts revalidated; DVT design and electrical revision frozen |
| 8. Design validation (DVT) | 15–18 | 4 wk | 10 representative units, tolerance validation, drop/abuse and EMC pre-scan, life test | Phase 7; creep/noise/life failures | Requirements pass on DVT population; compliance lab plan accepted |
| 9. Manufacturing development | 15–23 | 9 wk | Mold DFM, draft/ribs/parting, supplier quotes, fixtures, tool build and first articles | Phase 7; at-risk overlap with DVT, tool lead time | DVT changes incorporated; first articles match released CTQ drawings and capability plan |
| 10. Production validation (PVT) | 24–27 | 4 wk | Pilot lot, assembly training, end-of-line station, process capability and packaging | Phases 8/9; low yield or tool correction | ≥95% pilot first-pass yield, no critical defects; line test and traceability accepted |
| 11. Release and ramp | 28–30 | 3 wk | Regulatory closeout, production release, controlled ramp and field support | PVT and required compliance; supply interruption | Release approvals, qualified vendors, complete technical file and warranty process |

**Critical path:** 1 → 2 → 3 → 4/5 completion → 6 → 7 → 9 tooling → 10 → 11. DVT and manufacturing development overlap only after the revision freeze; committing tooling before DVT completion is a schedule/cost risk, not free time. A tool correction should reserve another 2–4 weeks. Early supplier engagement and stocked prototype servos reduce procurement risk; they do not eliminate qualification.

The planned 10,000-cycle EVT screen is not a life claim. The assumed three-year usage (two wake events/day and ten gestures/event) is 21,900 gestures, and a complete qualification must also test powered idle time, pivot creep, button wear, cable flex, alarm reliability, and foreseeable handling.
