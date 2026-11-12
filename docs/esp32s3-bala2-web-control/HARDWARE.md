# Hardware and interface selection

## Why Port B UART is preferred

BALA2 exposes Port A on GPIO21/22, Port B on GPIO26/36 and Port C
on GPIO16/17. Its motor base uses I2C address `0x3A`.
[M5Stack BALA2 documentation](https://docs.m5stack.com/en/app/Bala2-Fire)

**Do not use Port C as the default link on Fire.** M5Stack explicitly identifies
GPIO16/17 as connected to Fire PSRAM. Disabling PSRAM in a build is not evidence
that the pins are electrically free. Port B exposes GPIO26/36 instead.
[M5Stack Fire pin map and PSRAM warning](https://docs.m5stack.com/en/core/Fire)

Route a hardware UART to RX GPIO36 and TX GPIO26. GPIO36 is input-only and has
no internal pull-up; this is suitable for RX, never TX or I2C SCL/SDA. Add an
external approximately 10 kΩ pull-up from RX36 to **Fire 3.3 V** for a defined
idle state when disconnected. GPIO26 must not simultaneously be used for DAC
or another accessory. The GPIO matrix supports peripheral remapping.
[Espressif GPIO reference](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/peripherals/gpio.html)

## UART wiring

Disconnect power before wiring. Check connector orientation and continuity on
your actual BALA2; do not rely solely on wire colors. Use a Grove breakout to
XIAO header cable, short wires (start below 20 cm), and strain relief.

| XIAO ESP32-S3 Sense | BALA2 Fire Port B | Purpose |
| --- | --- | --- |
| D6 / GPIO43, TX | GPIO36, RX (normally white) | Commands to Fire |
| D7 / GPIO44, RX | GPIO26, TX (normally yellow) | Telemetry to XIAO |
| GND | GND (normally black) | Common signal reference |
| No connection initially | 5 V (normally red) | Insulate during separate USB power tests |

D6/D7 are separate from the Sense camera interface. D4/D5 are GPIO5/6
for a possible external I2C bus; the camera's control pins are GPIO40/39.
Use the **Sense**, not Plus, pin map. Reserve camera, microphone and SD pins
for those peripherals; do not guess from the ESP32-S3 chip pinout.
[Seeed pin multiplexing and Sense pin map](https://wiki.seeedstudio.com/xiao_esp32s3_pin_multiplexing/)

Use 3.3 V logic, not RS-232 voltages or 5 V TTL. The connector's 5 V supply
pin is not its signal voltage. During initial tests power each board from its
own USB connection and connect only TX/RX/GND. Do not drive an unpowered peer
through its signal pins.

Illustrative Arduino initialization, after verifying no library owns UART1:

```cpp
// XIAO: hardware UART1 on the D7/D6 pads (RX first, TX second)
Serial1.begin(115200, SERIAL_8N1, 44, 43);

// Fire: separate firmware, UART1 remapped to Port B
Serial1.begin(115200, SERIAL_8N1, 36, 26);
```

Keep debugging off this UART. Use Fire's normal USB serial and XIAO native USB
CDC, configured for the tested framework. XIAO boot output may appear on the
GPIO43 pad before application initialization; the receiver must reject noise
and remain disarmed until a valid session/arm exchange. Explicit UART pins
avoid accidentally selecting Fire's flash/PSRAM-connected defaults.
[Espressif Arduino UART API](https://docs.espressif.com/projects/arduino-esp32/en/latest/api/serial.html)

## Power for mobile operation

After separate-power validation, assess a single regulated supply for the
XIAO. Verify the BALA2 exposed 5 V rail's available current and behavior under
motor load against its schematic and measurements before using it. The
connector label alone does not establish spare capacity. Measure voltage at the
XIAO during Wi-Fi transmission, camera capture and wheel acceleration.

If capacity/noise is unsuitable, use a properly rated regulated 5 V supply
for the camera with common ground and appropriate decoupling. Do not connect
raw robot battery voltage to the XIAO or power it from a GPIO. Verify Seeed's
power-path instructions before combining header power and USB; avoid tying two
5 V sources together. Disconnect the external positive supply during USB
flashing unless the power-path design explicitly supports both.
[Seeed board and power documentation](https://wiki.seeedstudio.com/xiao_esp32s3_getting_started/)

## Alternatives and their tradeoffs

| Link | Assessment |
| --- | --- |
| Port B remapped UART | Preferred: separate from the balance I2C bus, two-way telemetry, simple framing |
| Port C GPIO16/17 UART | Avoid on Fire because of PSRAM connections |
| Port A I2C | Possible with additional work; shares a control-critical bus |
| Second I2C bus on Port B | Not possible with GPIO36 as a bus line because it cannot drive output |
| Other M-Bus pins | Only after an accessory/schematic audit; many are assigned to display, SD, audio or boot strapping |
| Wi-Fi UDP between boards | Fallback if Port B is occupied; needs loss handling, authenticated sessions and network/channel testing |
| UART with RS-485 transceivers | Consider for a longer/noisy harness; adds hardware and direction/termination design |

### If I2C is required

Wire XIAO D4/GPIO5 SDA to Fire GPIO21 and D5/GPIO6 SCL to Fire GPIO22,
plus ground. Keep **Fire as the sole bus master** and make XIAO a slave that
exposes a latest-command mailbox. Fire polls the mailbox; XIAO must not become
a second master or write commands directly to the motor base. Select an unused
7-bit slave address only after inventorying the actual bus (candidate `0x42`).

The Fire IMU and power-management devices also occupy GPIO21/22. A stuck bus
or long slave transaction can therefore interfere with balancing.
[M5Stack Fire internal I2C map](https://docs.m5stack.com/en/core/Fire)

Verify 3.3 V pull-up levels and combined pull-up resistance before connection.
Use the established robot bus speed; do not change it blindly. Serialize every
transaction through the existing bus owner/mutex with bounded timeouts. Poll
at 20 Hz only if measured balance deadlines remain satisfied. Use fixed-size
mailbox snapshots with sequence and checksum; keep callbacks allocation-free
and avoid waiting for the web task. Confirm ESP32-S3 slave support in the exact
framework version and reserve an I2C controller distinct from the camera SCCB
controller. Driver/controller conflicts are another reason to prefer UART.

I2C is not a drop-in replacement for this guide's UART framing. Implement and
test the mailbox adapter, bus recovery and motor-fault response separately.
