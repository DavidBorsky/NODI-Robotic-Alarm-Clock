# NODI complete electrical package — revision B

Start with the [full three-sheet circuit PDF](Schematics/NODI_System_RevB.pdf) and [four-page pin-to-pin wiring PDF](Wiring/NODI_Wiring_RevB.pdf). These supplement the earlier overview with every external module pin, unused-pin marker, component value, IC supply/enable tie, connector number and physical wire run. **Hardware is unbuilt and untested.** Revision B changes the electrical documentation and input procurement; the mechanical CAD remains revision A.

| Deliverable | Contents |
|---|---|
| [Native KiCad project](Schematics/NODI_System_RevB.kicad_pro) and [root schematic](Schematics/NODI_System_RevB.kicad_sch) | Editable three-sheet hierarchy, embedded symbols and local symbol library; open in KiCad10 |
| [Circuit PDF](Schematics/NODI_System_RevB.pdf) | Power entry/distribution; Pico, OLED, RTC and four-leg switch; AHCT125, servos and discrete audio driver |
| [Wiring PDF](Wiring/NODI_Wiring_RevB.pdf) / [colored SVG](Wiring/NODI_Wiring_RevB.svg) | 36 explicitly numbered wire runs, all7 moving conductors, connector-face/pad maps and physical switch common-pair diagram |
| [Wire schedule CSV](wiring_schedule.csv) | Every physical wire's endpoints, net, gauge, color, proposed cut allowance and movement status |
| [Pin/net CSV](netlist.csv) / [actual KiCad XML export](Schematics/NODI_System_RevB.net) |142 explicit schematic pin rows including3 ERC power flags;139 physical/module pins,85 connected and54 external NC;19 functional nets |
| [Component references](schematic_components.csv) / [electrical BOM](electronics_BOM.csv) |30 schematic symbols, including3 nonphysical ERC flags and2 covered solder-star points; CC resistors are already included in the USB-C module |
| [ERC JSON](Schematics/erc_report.json), [verification JSON](validation.json), [export provenance](export_provenance.json) | Actual KiCad10.0.7 ERC and exact source/output hashes, plus exported-netlist/CSV/firmware checks |

The editable files are complete **system-level circuits assembled from purchased modules**. The Pico's regulator/USB circuitry and the display/RTC module internals are not redrawn as hypothetical new PCBs. Their exact primary-source board schematics are linked in [architecture.md](architecture.md); all their external interfaces, including intentionally unused pads, are exposed here. For the OLED, `H1`–`H8` mean vendor JP2 header pads1–8; `QA1`–`QA4` and `QB1`–`QB4` mean the two physical STEMMA QT connectors. These project IDs avoid confusing an eight-pin header with a four-pin QT plug.

The selected input is **current resistor-equipped SparkFun BOB-15100**, with its two existing5.1kΩ CC resistors shown inside the module boundary. The official source is pinned at commit `3ba323b8a051d6f4672e8ba8883e5a11f7e75076`; its older CDN PDF differs. Do not add parallel CC resistors. The breakout and insulated input pod sit outside the modeled base and feed a rated captive cable. J4 is a separately retained, insulated fixed-base disconnect: JST XH2.50mm pitch is not assumed to fit2.54mm perfboard. Incoming inspection, exact fit, cable retention and connector mass remain physical work. Electrical BOM allowance is **$89.60**, not a quotation.

Read the [architecture, exact pins, power design and commissioning sequence](architecture.md) before assembly. `TP1` and `TP2` are covered solder-star junctions, not extra PCB hardware. Servo plugs use explicitly marked project cavity numbering; verify actual polarity and continuity. Switch terminal labels A1/A2 and B1/B2 identify the two common pairs. Establish those pairs with a continuity check before wiring. All spare Pico GPIO and debug pads, unused display headers/QT port, RTC BAT/32K/SQW/RST pads, AHCT unused outputs and USB D+/D− are explicitly marked unused externally. The RTC CR1220 goes in its onboard holder, with no external BAT wire.

## Open and regenerate

Keep all files in `Schematics/` together and open `NODI_System_RevB.kicad_pro`. Native symbols are both embedded and supplied in `NODI_System.kicad_sym` via the local `sym-lib-table`. No external symbol download is needed. The project has no custom ERC suppressions. Used Pico GPIO/power pins and AHCT inputs/outputs have meaningful electrical types; source flags are placed only on the fused rail, post-diode VSYS input and ground return.

From the repository root, with Python plus the repository's `reportlab` dependency and KiCad10 installed:

```bash
python3 Electronics/generate_electrical.py
python3 Electronics/export_electrical.py
python3 Electronics/verify_electrical.py
```

The first script regenerates native sheets, library, pin/net CSV and harness SVG/PDF. The second actually runs KiCad netlist export, ERC and PDF plotting, then records hashes binding the precise sources to those outputs. The third checks that frozen binding, independently parses the **actual KiCad XML**, compares every pin to the expected CSV, verifies every harness wire joins the specified equal-potential endpoints, checks fixed power/interface contracts and verifies the firmware's six GPIO constants. It does not refresh stale export provenance. CI can run this last command without downloading KiCad; editing native sources requires rerunning the real KiCad export step before CI will pass.

An extracted official AppImage can be used with `python3 Electronics/export_electrical.py --launcher /path/to/squashfs-root/AppRun`. In a restricted environment, set `XDG_CONFIG_HOME`, `XDG_CACHE_HOME` and `XDG_DATA_HOME` to writable temporary directories before launching KiCad.

## Executed checks and limits

KiCad10.0.7 successfully parsed all three sheets, exported the three-page PDF and XML netlist, and ran ERC with **zero reported violations**. The report retains KiCad's default ignored checks: single-use global labels, four-way junction style, SPICE models and footprint-filter matching. These are disclosed in the report and validation JSON; no electrical pin-check suppression or blanket passive-pin conversion was used. There is no custom PCB footprint layout or SPICE model in this package.

This establishes file readability and the documented logical connections. It does not establish purchased-board authenticity, current capacity under fault, EMC, sound pressure, assembly fit, startup pulse behavior, physical isolation or environmental reliability. The AHCT125 selection was reviewed against TI RevR's input leakage specification at VCC=0; its outputs still need real startup/power-down testing. No physical electrical measurement or successful hardware demonstration is claimed.
