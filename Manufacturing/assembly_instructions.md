# Assembly and service — revision A

NODI is an **unbuilt digital proof of concept**. This sequence is derived from the CAD and wiring architecture; it has not been timed or performed on physical parts. The repeated-assembly target is **30 minutes from a prepared kit**, with all parts printed, finished, matched to incoming components, electronics soldered and bench checked, horns drilled, and firmware loaded. First-build fitting and electrical work should be allowed several hours in addition to printing; they are outside that target.

Use [BOM.csv](BOM.csv), [CAD/manifest.json](../CAD/manifest.json), the [exploded assembly](../CAD/exports/NODI_Exploded_RevA.step), and the [manufacturing drawing](../Drawings/NODI-P03_Yoke_RevA.pdf). The manifest's component IDs identify individual instances. Coordinates are X right, Y rear, Z up; the face points toward −Y. Screws are conventional purchased parts represented without thread geometry. Do not interpret intentional thread-zone overlaps in the CAD as clearance fits.

## Kit, tools and preparation

Required tools: FFF printer and slicer, calipers, small drill/reamer set, M2 × 0.4 and M3 × 0.5 taps with hand holder, fine file/deburring tool, miniature driver bits matching the purchased screw heads, a small 5.5 mm nut driver or spanner for M3, tube cutter/fine saw, soldering iron, heat-shrink tools, wire stripper, multimeter, regulated current-limited 5 V supply, programming computer and USB lead. A drill press and a simple horn-drilling fixture improve alignment.

1. Print PETG parts P01–P09 using the proposed process in [materials_and_processes.md](materials_and_processes.md). P10 is a **steel ballast**, not an STL-printing task. Inspect the yoke drawing datums, bores and stop features. Remove supports and burrs without altering bearing positions.
2. Incoming-check the actual MG90S flange, output spline, center screw and horn. The body envelope is manufacturer based; the flange and 19 mm horn interfaces are design assumptions. Do not force an incompatible spline. Check the current-revision Adafruit 938 board against the 30.5 × 28 mm hole rectangle.
3. The prototype uses M2 machine screws into nominal Ø1.8 mm printed pilots and M3 screws into Ø2.7 mm pilots. **Pre-tap gently by hand**, clear chips and verify on a coupon. These oversize pilots provide limited polymer thread engagement and are not a claim of standard full-depth metal threads or validated pull-out strength. Do not drive screws as improvised thread-forming tools. Use low hand tightening only; stop when seated, with no visible boss distortion. Strip/pull-out and repeated service performance remain physical tests. Heat-set inserts require revised CAD and are not installed in Rev A.
4. Match-drill the two purchased 19 mm nylon disc horns to Ø1.8 mm at ±7 mm from center, and hand-tap M2. The **yoke** mating holes remain Ø2.2 mm clearance. Keep swarf out of servo gears and verify the actual horn center recess fits the vendor retaining screw. The modeled M2.2 × 6 mm center screw is an envelope; use the screw supplied for the servo's output shaft.
5. Cut the brass pivot sleeve C04 square to **14.2 mm**, OD4 / ID3.2 mm. Deburr both ends and confirm the M3 screw passes through it freely. Make the PTFE washers C01 (OD40 / ID25 / 2 mm) and C05 (OD8 / ID4.3 / 1 mm) from sheet, or buy matching parts.
6. Cut/drill steel ballast P10 to 40 × 18 × 12.5 mm with two Ø3.4 mm through holes on 28 mm pitch. Deburr thoroughly and protect it from corrosion. Check no metal edge can contact a wire. Its retention is two screws into integral base posts; adhesive is not a substitute.
7. Prepare the 31 × 24 mm power perfboard and the Pico/RTC harness outside the case. Use insulating pads beneath boards, covered solder joints and no tall sockets that exceed the CAD envelope. Follow the full [wiring and polarity checklist](../Electronics/architecture.md). Adhesive pads retain unloaded electronics/piezo and elastomer feet; load-bearing head, motors, yoke and ballast use mechanical fasteners.

## Assembly sequence

| Step | Operation | Hardware and inspection |
|---|---|---|
| 1 | Fit the four silicone feet C14 to the clean base underside at X = ±45, Y = ±44 mm. | Four Ø12 × 3 mm feet. Verify the base sits on all four; do not trap a cable tie below their support plane. |
| 2 | Install the steel ballast P10 inside the front base at center X = 4, Y = −19 mm. | Two F10 M3 × 18 screws at X = −10/+18 mm. The bar sits on posts at Z = 8.4 mm. Tighten evenly into prepared pilots; it must not rattle or move. |
| 3 | Mount the yaw MG90S C02 vertically on the base's two flange supports. | Two F06 M2 × 8 screws. Shaft points up at X = Y = 0. Body, supports and connector must match the actual servo; do not preload the plastic case. |
| 4 | Fit rear carrier P06 with Pico C07 and RTC C08, then side carrier P07 with populated power board C09. | Rear: four F08 M3 × 6. Power: **four F11 M3 × 5**, not 6 mm; shorter screws avoid underside breakthrough. The Ø10 × 16 mm capacitor top is Z = 24.6 mm, below the 29.6 mm deck underside. Check covered solder joints cannot contact steel ballast. |
| 5 | Fit switch carrier P08 at Y = −36 mm and retain its switch C12 on a small insulated solder pad, with body seated on the carrier. Place piezo C13 on its insulated mounting pad near X = 32, Y = −28 mm. | Switch carrier: two F08 M3 × 6. Total rear/switch F08 quantity is six. Confirm button actuator reaches Z = 30.5 mm, with no preload, and acoustic openings remain clear. |
| 6 | Insert the power pigtail through the rear Ø7.2 mm passage at X = 34, Z = 12 mm; fit rubber sleeve/grommet and strain relief. Connect the inline fuse and distribution wiring. | Route a nylon tie through the two Ø2.5 mm floor holes at X = 45, Y = 24/32 mm and around a rubber-sleeved section of cable. Tie loop must retain outer jacket, not individual conductors; keep underside thickness <2.5 mm under the 3 mm feet. Tug gently and verify no force reaches solder joints. Pull-test value remains to be established. |
| 7 | Bench check logic with servos unplugged; then center both servos at nominal 1500 µs with their horns disconnected. Power down before handling gears. | Verify rail polarity, RTC/address detection and no USB backfeed as in the electrical guide. Install the RTC cell and set local time. Keep the head supported throughout commissioning. |
| 8 | Feed the seven-wire moving harness through the deck's **Ø10 mm rear grommet bore** at X = 0, Y = +34 mm, then fit deck P02. Place cap P09 above the switch through the smaller front stem opening. | Four F03 M3 × 10 deck screws. Grommet free ID about 6 mm, bundle ≤3.5 mm. Cap underside Z = 32.8 mm gives 0.8 mm clearance above the deck; top Z = 36.3 mm. Verify sufficient travel for the incoming switch's measured stroke and no preloading. Switch cap is gravity seated in Rev A; check return after pressing. Remove it before inverting the unit. A captive cap is a future product refinement. |
| 9 | Place PTFE yaw thrust washer C01 on the deck. Fit the centered yaw horn to the servo, then lower yoke P03 over its pilot and horn. | One F09 vendor retaining screw through the yoke's Ø9 center access; two F07 M2 × 6 at X = ±7 mm secure the yoke to the tapped horn. Ensure the Ø24 pilot turns freely in the deck bore, washer carries axial weight, and horn hub does not bottom on the deck. Do not glue the bearing joint. |
| 10 | With head face still open, fit the second MG90S inside shell P04 with its output pointing +X. Slip its centered round horn over the spline through the Ø21 mm shell opening. | Two F06 M2 × 8 from inside the shell into prepared posts. **The pitch servo case moves with the head; its horn is fixed to the yoke.** This arrangement is intentional. Do not fasten the pitch case to the yoke. |
| 11 | Support the head at neutral between the yoke arms. Attach the pitch horn to the right arm and secure the servo's output screw through the arm access bore. | Two F07 M2 × 6 fix horn to arm; one F09 vendor retaining screw is reached through the Ø6 mm outer access. Keep the central retaining screw clear of the yoke access bore. |
| 12 | Assemble the left passive pivot: washer C05 between left arm and head boss, sleeve C04 through both, then F01 screw and F02 nut. | F01 **M3 × 20**, F02 standard M3 DIN985 locknut (~4 mm envelope). The sleeve spans 14.2 mm; arm4 + washer1 + boss9 = 14.0 mm, giving nominal **0.2 mm axial float**. Tighten against sleeve ends, not against the rotating PETG boss. Verify free rotation and small end float after tightening. If tolerances remove float, correct the sleeve length or washer stack before powering. |
| 13 | Fit OLED C06 to bezel P05 from behind, route the display lead, and close the face. | Four F05 M2 × 5 for OLED, four F04 M2 × 8 for bezel. PCB and display glass are **one purchased module**. Tighten PCB screws evenly with no glass stress. Route all leads clear of bezel screw ends. |
| 14 | Form the external rear service loop, connect the moving harness and perform the unpowered sweep. | At least 80 mm free fine-stranded harness between fixed deck and head-bottom Ø8 mm exit at X = 0, Y = +15 mm. Use edge protection, ≥15 mm bend radius and tie points at each end. A head-side tie can pass through two existing rear vent slots after deburring; a base-side stop tie below the grommet prevents load reaching the PCB. Keep the loop behind/above the yoke rear edge, away from stops. **Do not route through the yaw pilot: the horn occupies it.** |
| 15 | Commission motion gradually, then verify the actual alarm sequence with the external computer disconnected. | Start ±5°, verify signs and pulse scale, then increase to yaw ±30° and pitch −15°/+25°. **Positive pitch lowers the face**, negative pitch raises it; the moving pitch-servo case reverses the shaft-to-head relation. Mechanical stops are nominal ±35° yaw and −20°/+30° pitch; they are fault containment, not regular endpoints. Log supply droop, current, motion clearance, timekeeping, sound level and temperature. |

Before fitting the face, check access for the pivot nut driver and the two pitch-servo screws. Never use servo power to pull a misaligned joint into place. The passive pivot must rotate freely with its clamping screw fully seated on the sleeve; merely leaving a screw loose is not the bearing design.

## Fastener kit

| ID | Specification | Quantity / use |
|---|---|---|
| F01 | M3 × 20 | 1 passive pivot screw |
| F02 | M3 DIN985 locking nut | 1 passive pivot nut |
| F03 | M3 × 10 low-profile head | 4 deck screws |
| F04 | M2 × 8 | 4 bezel screws |
| F05 | M2 × 5 | 4 OLED screws |
| F06 | M2 × 8 | 4 servo flange screws, two per servo |
| F07 | M2 × 6 | 4 horn-to-yoke screws, two per horn |
| F08 | M3 × 6 low-profile head | 6 rear/switch carrier screws |
| F09 | Vendor horn retaining screw, nominal M2.2 × 6 envelope | 2; included with servo purchase, verify actual shaft thread |
| F10 | M3 × 18 low-profile head | 2 steel ballast screws |
| F11 | M3 × 5 low-profile head | 4 power carrier screws |

There are **35 screws and one nut** in the final CAD assembly. The firmware can be programmed and electronics assembled outside the case, so these fasteners remain reachable. Servo-kit screws are counted for assembly but not priced a second time. The BOM gives head-envelope requirements; verify real driver recesses and head diameters before purchase. A production revision should reduce screw variety after prototype assembly evidence identifies safe consolidation opportunities.

## Inspection, service and limitations

- Inspect print layer adhesion, pivot-hole coaxiality, stop gaps, ballast retention, sleeve end float, the full combined movement sweep, and wire clearance. Model-derived gaps do not establish actual printed fits.
- Confirm the cap presses and returns without holding the switch closed. Its height depends on the incoming tactile switch and printed carrier; shim the unloaded switch pad or revise the parameter after measurement. The gravity-seated cap is not a shipping-qualified retention solution.
- On power-up with horns disconnected, confirm neutral pulses before mechanical attachment. Recheck the ≥5° intended soft-to-hard-stop margin after calibrating pulse-to-angle response; firmware limits alone do not measure real angles.
- Test short snooze, long dismissal, unattended timeout and a normal reboot within the alarm minute. The RTC cell maintains time but cannot operate the alarm during a power outage. No physical functional test has yet been performed.
- To service: unplug external power and programming USB, remove the loose cap, support the head, then remove the four deck screws. Disconnect the labeled moving harness before lifting far. For OLED or pitch-servo service, remove four front-bezel screws first; avoid pulling the display cable.
- Replace a stripped polymer boss by reprinting the affected part. Do not install a larger screw into a cracked boss. Record rework counts; repeated service joints need insert redesign before product release.
- Structural adhesive is not used in the head support or steel ballast load path. PCB pads and piezo pads carry only their small component loads. Nylon cable ties, grommets and wire insulation are assembly consumables whose exact installed shapes are not modeled.

## BOM regeneration and cost scope

Run from the repository root:

```bash
python3 Manufacturing/build_bom.py
python3 Manufacturing/build_bom.py --check
```

The script maps every nonvisual CAD instance once, consolidates the OLED's two solids into one purchase, retains two servos, and adds electrical items omitted from simplified CAD envelopes. The electrical subtotal is **$84.65**. All prices are one-prototype planning allowances in USD, excluding labor, machine time, tooling, shipping and tax; they are not supplier quotations. Printing allowance uses solid CAD material mass at $25/kg plus 25% waste, so a slicer's actual infill consumption may be lower. Hardware pack minimum quantities and procurement substitutions can raise the checkout total.
