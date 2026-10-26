# Independent electrical design review

**Reviewed 25 October 2026 — electrical revision B, mechanical revision A.** No blocking pinout or power-topology error was identified in the reviewed system schematic. This is a source, netlist and documentation review; no electrical hardware was built or measured.

## Executed checks

- Exported the actual native KiCad hierarchy independently to XML. All **85 connected pins** agree with the intended CSV across **19 functional nets**. The other **54 exported pins** are explicitly unconnected externally; three additional CSV rows are ERC power-source assertions, giving **142 explicit pin rows**.
- Checked all **40 Pico header pin labels** against the official board pinout and **43 critical pin/net assignments** against separate power, connector and IC expectations. Checked the six GPIO assignments against the firmware.
- Ran **KiCad 10.0.7 ERC on a separate copy** of the hierarchy: exit code 0, **zero reported violations**. The retained report identifies default ignored checks; this is not a claim that ERC checks every engineering property.
- Inspected the three-sheet circuit PDF and the harness PDF, including its final four-page version with connector-face diagrams. All **36 wire IDs** appear in the harness PDF; the schedule identifies **seven moving conductors**, W14–W20. Their endpoints agree with the circuit nets, including separate motor and display returns.

The committed [native circuit and PDF](../Electronics/Schematics/NODI_System_RevB.kicad_sch), [wire schedule](../Electronics/wiring_schedule.csv), [ERC record](../Electronics/Schematics/erc_report.json) and [connectivity record](../Electronics/validation.json) preserve the reviewed definitions. The connectivity record contains the source-file SHA-256 values; rerun export, ERC and verification after editing them.

## Interface findings

| Interface | Review finding and source |
|---|---|
| Pico power | D1 anode takes fused 5 V; its cathode feeds physical **39 VSYS**. Physical **40 VBUS** has no external connection. This matches the manufacturer’s diode-OR arrangement for simultaneous programming USB and external power. **36 is 3V3 OUT**, not VSYS. [Pico datasheet, Figure 2 and §§4.4–4.5](https://datasheets.raspberrypi.com/pico/pico-datasheet.pdf). |
| Pico signals | GP2/3/4/5/15/16 correspond to physical **4/5/6/7/20/21**, matching yaw, pitch, SDA, SCL, button and audio in the firmware. Unused pins are identified as having no external wire; purchased-board internal connections remain present. [Official pinout](https://datasheets.raspberrypi.com/pico/Pico-R3-A4-Pinout.pdf). |
| Servo buffer | TI **SN74AHCT125N** has the correct TTL input threshold for 3.3 V commands with a 5 V supply. Active enables 1/4 are grounded; unused enables 10/13 are high, inputs 9/12 low, outputs 8/11 unconnected. Inputs tolerate the specified voltage with VCC=0 under §5.4; this does not establish valid output behavior during rail transitions. [TI revision R, §§4–5](https://www.ti.com/lit/ds/symlink/sn74ahct125.pdf). |
| USB-C entry | Current BOB-15100 header: **1 CC2, 2 D+, 3 D−, 4 CC1, 5 GND, 6 VBUS**. Independent parsing confirmed two onboard 5.1 kΩ terminations. NODI R7/R8 represent those included resistors; adding another pair would be incorrect. The older CDN drawing does not define the selected resistor-equipped revision. [Pinned manufacturer Eagle source](https://github.com/sparkfun/USB-C-Breakout/blob/3ba323b8a051d6f4672e8ba8883e5a11f7e75076/Hardware/USB-C-Breakout.sch). |
| OLED and RTC | OLED QT contacts **1 GND, 2 VIN, 3 SDA, 4 SCL** match the vendor package-to-pad mapping. Its current board has I²C jumpers closed and automatic reset, consistent with the four-wire firmware interface. RTC header **1 VIN, 2 GND, 3 SCL, 4 SDA** is correct; BAT is left externally unused. Both receive 3.3 V so their bus pullups do not raise Pico pins to 5 V. [OLED native source](https://github.com/adafruit/Adafruit-1.3inch-128x64-Mono-OLED-PCB), [RTC pinout](https://learn.adafruit.com/adafruit-ds3231-precision-rtc-breakout/pinouts). |
| Audio | Q1 uses the selected onsemi TO-92 mapping **1 emitter, 2 base, 3 collector**. The 4.7 kΩ base resistor, base pulldown and 1 kΩ piezo discharge resistor are connected correctly. The parallel discharge resistor agrees with Murata’s transistor-drive guidance; sound pressure remains unmeasured. [onsemi datasheet](https://www.onsemi.com/pdf/datasheet/2n3904-d.pdf), [Murata drive guidance](https://www.murata.com/en-global/support/faqs/sound/diaphragm/char/sch0001). |
| Moving disconnect | J4 keeps servo 5 V separate from OLED 3.3 V and provides distinct return wires. The review identified that **2.50 mm XH is not a drop-in 2.54 mm perfboard interface**; revision B explicitly specifies a separately retained insulated disconnect or a correctly drilled adapter. Fit and retention are not claimed in the CAD. [JST XH drawing](https://www.jst-mfg.com/product/pdf/eng/eXH.pdf). |

## What remains unverified

The circuit is defined for a **dedicated 5.0–5.1 V, 3 A source**. Its passive USB-C entry does not detect advertised current; it is not a universal USB-port power implementation. The 2.20 A budget includes assumed servo currents, not measured stall ratings.

ERC cannot establish rail droop, fuse coordination, startup pulses, I²C signal quality, acoustic output, transistor transients, component temperature, crimp quality or wiring fatigue. Those need the commissioning measurements in the [electrical architecture](../Electronics/architecture.md) and [verification plan](requirements_and_verification.md). The external input pod and J4 retention are disclosed, unmodeled assembly details. The schematic is a complete **module-level system definition**, not a custom PCB layout, a recreation of supplier PCB internals, or evidence of physical alarm operation.
