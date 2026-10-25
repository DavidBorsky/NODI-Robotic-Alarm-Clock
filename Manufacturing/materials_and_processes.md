# Materials, manufacturing and release plan — revision A

This package is an unbuilt engineering proof of concept. Processes, prices and inspection criteria below are proposed; no supplier qualification or production tooling has been completed. Part identifiers and quantities are controlled by [the BOM](BOM.csv) and [CAD manifest](../CAD/manifest.json).

## Material selection

| Candidate | Prototype advantages | Main limitations for NODI | Decision |
|---|---|---|---|
| PLA, FFF | Easy dimensional trials; stiff; clean face detail | Warm-enclosure creep and brittle fastener features; not preferred for cyclic support arms | Fit coupons only; do not substitute its stiffness in PETG calculations |
| PETG, FFF | Tough, accessible and repairable; useful for low-load housings and yoke | Layer anisotropy, stringing, creep, variable bore accuracy; elastic and strength values depend on printing | Selected for custom prototype rigid parts; local solid regions around pivots and screws |
| ABS, FFF | Tough; useful thermal margin relative to common PLA | Warping and enclosed-printer requirements complicate a short challenge | Alternative only after process tuning and coupon checks |
| PC-ABS, injection molded | Candidate for durable consumer housings, finish and integrated assembly features | Requires resin grade selection, shrink compensation, draft, tooling and molded-part validation | Production candidate; the FFF CAD is not a released mold design |
| 6061 aluminum | Stiff, durable pivot or bracket insert; easy threaded features | Extra machining/setup cost; unnecessary if polymer coupons and support analysis pass | Contingency for yoke or pivot load path after physical testing |
| PTFE sheet | Low-friction axial sliding washer isolates yaw servo from base weight | Creep and wear; no radial bearing function; joint must retain clearance | Cut washer for prototype; inspect after cycling |
| Steel / brass | Standard metric fasteners and replaceable inserts | Over-tightening can crush polymer; inserts need installation coupons | Purchased hardware; no printed threads in service joints |
| Silicone elastomer | Compliant grip and vibration isolation | Adhesive aging and friction uncertainty | Four purchased feet; grip must be measured on desk surfaces |

The [Prusament PETG manufacturer guide](https://prusament.com/materials/prusament-petg/) supports PETG as a practical mechanical-part material and discusses print behavior. It does not establish a design allowable for this printer or geometry. Calculations use explicitly conservative assumed properties and require coupons. [Stratasys PC-ABS data](https://www.stratasys.com/assets/material-wizard/direct/material-datasheets/fused-deposition-modeling/spec-sheet---pc-abs-en.pdf) illustrates orientation dependence in printed PC-ABS; those values are **not** used as injection-molded resin properties.

## Prototype fabrication route

1. Regenerate the CAD before printing. Review the [geometry report](../CAD/validation.json), the critical-part drawing and the [verification matrix](../Documentation/requirements_and_verification.md).
2. Print a hole/insert/pivot coupon using the actual filament, machine and orientation. A proposed starting process is 0.4 mm nozzle, 0.2 mm layers, five perimeters, five top/bottom layers and 35–45% infill. Use locally solid regions at load paths. These settings have not been qualified.
3. Orient the housing open side upward where possible. Keep exterior face surfaces off supports. Orient the yoke to avoid interlayer tension at arm roots; if upright printing is used, the conservative through-layer assumption remains necessary. Verify the chosen orientation with a bent coupon rather than using bulk-resin strength.
4. Deburr cable slots and break sharp edges approximately 0.3 mm. Ream/drill critical small bores to drawing sizes. Do not force a misaligned servo or pivot into a printed hole.
5. Install inserts only where CAD/BOM calls for them, using a temperature-controlled tool and a stop. Perform a sacrificial installation first. Through-bolts and retained nuts remain preferred where accessible.
6. Cut the thrust washer from sheet stock, check burr-free surfaces, and clean the contact track. The washer carries axial compression; the pilot controls radial location.
7. Inspect datums, the pivot axis and moving-part envelope before fitting electronics. Follow the assembly guide and perform current-limited motion checks before closing covers.

STLs are nominal solids. The slicer must not globally scale the assembly to compensate a tight bore; adjust the relevant CAD parameter after measuring a coupon. Material density in CAD is a geometric mass estimate and does not model sparse infill, wiring, adhesive or moisture.

## Design for assembly and maintenance

Separate base cover, electronics carrier, head housing and face bezel keep all service tasks reachable. The yaw joint uses a thrust contact and pilot rather than relying on the microservo shaft for axial support. The tilt servo case travels with the head, reacting against its fixed horn on the yoke; the opposite pivot closes the support load path. Covers are removable. The servo spline/horn screw remains a purchased interface and must match the physical servo lot.

Cable passages are deliberately open and deburred. Provide flexible stranded wire and strain relief at both ends of each moving loop. Route a yaw loop behind the tilt axis and a smaller pitch loop inside the head; verify neither reaches tension nor the stop path at any combined limit. Clip and connector geometry is represented only where identified in CAD; the complete harness is not simulated as a deformable solid.

## Transition to production

At an indicative 5,000-unit annual volume, obtain competing quotes before selecting tooling. Estimated volume is a planning assumption, not market validation. Retain machined or bought hardware in the pivot path and use a specified molded resin grade for housings. A molding redesign must include:

- Approximately 1–2 degrees of draft as an initial discussion with the toolmaker; texture and resin determine final draft.
- Near-uniform nominal walls around 2 mm with transitions, cored bosses and ribs around 0.5–0.6 times wall thickness to limit sink. Recalculate stiffness after changing the FFF yoke or its wall structure.
- Split lines that avoid external cosmetic faces; removable carrier and bezel tooling without hidden undercuts. Any retained undercut needs a deliberate side action, lifter or redesigned fastening feature.
- Gate/vent/ejector locations, weld lines near loaded roots, resin shrinkage, molded-in stresses and a mold-flow review.
- Molded datum pads, go/no-go fit gauges and a controlled pivot/horn interface. Threaded metal hardware remains serviceable.
- Resin flammability, electrical construction, acoustic performance and applicable market compliance review during DVT. No compliance claim is made here.

Tooling is gated by EVT fit/load/cycle evidence, DVT environmental and user testing, supplier capability data, and PVT yield. Do not order hard tools from these prototype STLs.

## Preliminary cost basis

All BOM unit costs are USD planning allowances for one prototype, excluding labor, shipping, tax, printer capital, tooling and certification. They are not quotations or current purchase offers. Print material allowance includes waste. The production roadmap requires supplier quotes and a recurring-cost model before a commercial target price is set.
