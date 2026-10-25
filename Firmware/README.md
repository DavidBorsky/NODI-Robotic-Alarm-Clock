# NODI firmware

The Arduino sketch is a real, build-checked implementation for the original Raspberry Pi Pico. Its alarm and motion core also compiles and passes executable host tests. **No Pico, servo, RTC, button, buzzer or display has been tested on physical hardware.** Compilation and host tests establish software properties; they do not establish the clock's mechanical function, sound pressure, time accuracy, electrical robustness or servo calibration.

## What it does

- Reads a battery-backed DS3231; displays local time plus a simple face on an SSD1306 128 × 64 OLED.
- Wakes 30 seconds before one daily alarm, then sounds a 4 kHz piezo with 400 ms on / 600 ms off cadence while nodding and looking side to side.
- Short button press during ringing: five-minute snooze. Hold ≥1.5 seconds while ringing or snoozed: dismiss today's alarm, with a four-second cheerful pose. Hold while idle: toggle daily alarm enable. Input debounce is 30 ms.
- Stops an unattended ringing episode after ten minutes. The normal daily alarm can fire at any second within its scheduled minute, so polling need not land on second zero.
- Stores alarm settings and the most recently consumed civil day in flash. A normal reboot within the same day's alarm minute does not duplicate that occurrence. A corrupted settings record is rejected by checksum.
- Bounds yaw to ±30° and pitch to −15°/+25°, with rest-to-rest quintic trajectories targeting ≤60°/s and ≤180°/s². A changed target waits for the current segment to end, preserving zero endpoint speed/acceleration. This can delay a snooze pose by up to the current segment duration; audio stops immediately through state logic.

The sketch uses no Wi-Fi, network time or runtime cloud service. The RTC stores **local civil time**. Set it manually when moving between time zones or changing daylight saving time. There is no automatic missed-alarm replay, battery-powered sounding, or calendar/weekend schedule. A power loss or reboot during snooze cancels that snooze; the daily occurrence remains consumed and the next alarm is the following day. Flash writes are limited to settings changes and alarm occurrences, not performed on every loop. Flash persistence is not power-failure-atomic; an interrupted write can restore defaults.

## Open and build

Open [NODI/NODI.ino](NODI/NODI.ino) in Arduino IDE, install the **Earle Philhower Arduino-Pico** board package, and select **Raspberry Pi Pico**. Do not select the Arduino Mbed Nano RP2040 board definition. Install RTClib, Adafruit SSD1306, Adafruit GFX Library and Adafruit BusIO. Servo, Wire and EEPROM come with the Pico board package.

The source was compiled using these pinned versions:

| Dependency | Version |
|---|---|
| Arduino-Pico / `rp2040:rp2040` | 6.1.0 |
| RTClib | 2.1.4 |
| Adafruit SSD1306 | 2.5.16 |
| Adafruit GFX Library | 1.12.4 |
| Adafruit BusIO | 1.17.4 |

Equivalent Arduino CLI commands, from the repository root:

```bash
arduino-cli core update-index --additional-urls https://github.com/earlephilhower/arduino-pico/releases/download/global/package_rp2040_index.json
arduino-cli core install rp2040:rp2040@6.1.0 --additional-urls https://github.com/earlephilhower/arduino-pico/releases/download/global/package_rp2040_index.json
arduino-cli lib install "RTClib@2.1.4" "Adafruit SSD1306@2.5.16" "Adafruit GFX Library@1.12.4" "Adafruit BusIO@1.17.4"
arduino-cli compile --fqbn rp2040:rp2040:rpipico --warnings all Firmware/NODI
```

To upload, identify the Pico's serial port using `arduino-cli board list`, then use `arduino-cli upload --fqbn rp2040:rp2040:rpipico --port YOUR_PICO_PORT Firmware/NODI`. Follow the board package's BOOTSEL instructions for first programming. The carrier and rear cover provide service access; do not flash with horns installed until the commissioning steps below are complete.

## Set the clock and alarm

Connect Pico's programming USB, open a 115200-baud serial monitor with newline line ending, and send, for example:

```text
TIME 2026-10-24 22:15:00
ALARM 07:30
ON
STATUS
```

Commands are case sensitive. `TIME` accepts valid dates 2000–2099. `ALARM HH:MM` retains the existing enable state. `ON` / `OFF` enable or disable the daily alarm. The default for an uninitialized settings record is **07:00 ON**, but an absent RTC, an invalid date, a lost-power RTC flag, or failed I²C acknowledgement inhibits ringing until corrected. The firmware never silently sets the RTC to its compilation date.

Set an alarm a minute ahead to check the flow. Then power down and restart within that alarm minute to verify that occurrence suppression survives a normal reboot. The selected RTC's coin cell retains time; the computer is unnecessary after setup.

## Motion commissioning

The generated CAD defines zero yaw straight ahead and **positive pitch face-down** (right-hand rotation about +X for a face pointing −Y). Idle +8° and snooze +20° lower the face; prewake −8° and cheerful −12° lift it. The nominal **1500 µs center** and **1000/180 µs per degree** scale in the sketch are starting assumptions. MG90S units and horn installations vary. The host tests verify the commanded angles, not physical servo angles.

1. Disconnect both horns and support the head. Start at neutral and verify both servos center without buzzing or driving into a stop.
2. Fit horns at mechanical zero. Check `YAW_SIGN` and `PITCH_SIGN` using small commanded angles; flip the sign constants if needed. The nominal pitch sign is −1 because the servo case moves against a fixed horn, reversing the shaft-to-head relation; actual electrical polarity remains a commissioning measurement.
3. Measure pulse-to-angle response and edit center/scale constants. Confirm the requested operating ranges have ≥5° remaining before mechanical stops, at every combined yaw/pitch pose.
4. Keep actuator power accessible and check cable sweep, electrical rail droop and heat. The code has no angle feedback or jam detection. Refer to the full [electrical commissioning sequence](../Electronics/architecture.md).

The scheduler is nonblocking and uses unsigned monotonic subtraction for snooze, timeout and debounce. The hardware sketch performs short synchronous I²C transfers and flash writes; no real-time deadline has been measured. If the RTC stops responding while ringing, the alarm is inhibited. Closed-loop position confirmation and motor-current cutoff are future design work.

## Executable verification

From the repository root:

```bash
bash Firmware/tests/run_tests.sh
```

This compiles the **same** [NodiCore.h](NODI/NodiCore.h) used by the Arduino sketch with `g++ -std=c++17 -Wall -Wextra -Werror -pedantic -O2`. The binary is built in a temporary directory and removed afterward. Tests cover the schedule minute, prewake, snooze, long dismissal, timeout, midnight and cross-midnight snooze, normal reboot persistence, invalid clock, button bounce, uint32 `millis()` rollover, target changes, travel clamps and sampled motion derivatives. Results and scope are recorded in [verification_results.md](verification_results.md).

## Primary software references

- [Arduino-Pico Servo library](https://arduino-pico.readthedocs.io/en/latest/servo.html), [I²C](https://arduino-pico.readthedocs.io/en/latest/wire.html), and [EEPROM](https://arduino-pico.readthedocs.io/en/latest/eeprom.html).
- [Adafruit RTClib source and API](https://github.com/adafruit/RTClib), [SSD1306 library](https://github.com/adafruit/Adafruit_SSD1306), [GFX library](https://github.com/adafruit/Adafruit-GFX-Library), [BusIO library](https://github.com/adafruit/Adafruit_BusIO).
