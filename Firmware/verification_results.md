# Firmware verification record

Date: **2026-10-24**. Hardware test status: **not performed**.

## Host execution

Executed from the repository root with the system `g++`, using `bash Firmware/tests/run_tests.sh`:

```text
Measured sampled command limits: 57.329 deg/s, 179.921 deg/s^2 (10ms sampling).
PASS: 15 scenario groups (alarm, snooze, dismiss, midnight, timeout, reboot, clock invalid, debounce, millis rollover, bounded smooth motion).
```

The command limits are finite differences of a **software command trajectory**, not measured mechanical motion. The 30° rest-to-rest step is sampled every 10 ms. Duration is chosen from the analytic quintic derivative bounds (1.875 Δθ / T and 5.773503 Δθ / T²); the test independently differentiates the resulting samples and checks their maxima. Other tests check clamp endpoints, pending target behavior, time rollover and the CAD pose convention (positive pitch lowers the face; sleep points down and waking/cheerful poses point up). The host tests do not emulate the Arduino libraries, flash circuitry, timer/PWM implementation or I²C hardware.

## Actual Pico compilation

Executed the real ARM build with Arduino CLI **1.5.2-rc.1**, Pico board core **6.1.0**, and the pinned libraries listed in [README.md](README.md). The toolchain and build directory were kept in `/tmp`, outside the submission. Command, with temporary tool configuration omitted:

```bash
arduino-cli compile --fqbn rp2040:rp2040:rpipico --warnings all Firmware/NODI
```

Final compiler output (exit code **0**, no warnings in final build):

```text
Sketch uses 82776 bytes (3%) of program storage space. Maximum is 2093056 bytes.
Global variables use 10620 bytes (4%) of dynamic memory, leaving 251524 bytes for local variables. Maximum is 262144 bytes.
```

Source SHA-256 at verification:

```text
922cef0827b3e7bce3602f8758880988470c45de20d9d51e885c9dd2e92818e9  Firmware/NODI/NODI.ino
5bddd702b7564ab5180f42b10281f913bb543e719244b19ab4511c47e75af421  Firmware/NODI/NodiCore.h
```

No code has been flashed to a Pico. Electrical assembly, pulse-to-angle calibration, physical travel, sound pressure, button feel, power interruption behavior, real RTC retention, supply droop and thermal operation remain proposed physical verification tasks. The memory numbers above are compiler-reported static allocations; they do not measure worst-case stack or runtime display-buffer allocations.
