# Implementation guide

All rates, limits and timeouts below are initial engineering targets, to be
validated on hardware. They are not measured performance claims.

## 1. Establish independent firmware baselines

1. Record Fire, base, XIAO and camera sensor revisions; photograph connectors.
2. Build and run the complete official BALA2 example, including its companion
   source files and calibration support. Preserve its license and record the
   upstream commit. First verify supported stationary balance with no gateway.
3. Replace the camera project's commented scaffold with a minimal boot/USB
   program, then the camera example configured for XIAO ESP32-S3 Sense.
4. Pin the working PlatformIO platform, Arduino framework and libraries. Record
   PSRAM mode, flash size, partition table, USB flags and camera sensor ID.
   Do not infer these settings from the board ID alone.

The official BALA2 example contains an IMU task, a 5 ms PID task and an I2C
mutex. Its speed feedback uses encoder increments, not SI velocity. Integrate
at the speed-reference layer only after deriving encoder scale and signs;
its equal left/right PWM output needs an explicit yaw-control extension.
Do not blindly assign joystick values to `SetSpeed()` or the pitch setpoint.
[Official BALA2 source](https://github.com/m5stack/M5-ProductExampleCodes/tree/master/Application/Bala2)

Use Espressif's camera driver and CameraWebServer example as references. Start
with JPEG QVGA (320×240), one frame buffer and one viewer; try a second buffer
only after measuring memory and latency. Check successful PSRAM allocation.
Avoid RGB conversion in the streaming path. Always return camera frame buffers,
including on send failure.
[Camera driver](https://github.com/espressif/esp32-camera),
[CameraWebServer](https://github.com/espressif/arduino-esp32/tree/master/libraries/ESP32/examples/Camera/CameraWebServer)

From the repository root, once application sources exist:

```bash
pio run -d .devcontainer/firmware/bala2
pio run -d .devcontainer/firmware/camera
pio device list
# Replace the port placeholders with the detected device paths on the Mac.
pio run -d .devcontainer/firmware/bala2 -t upload --upload-port /dev/cu.FIRE_PORT
pio run -d .devcontainer/firmware/camera -t upload --upload-port /dev/cu.XIAO_PORT
```

Build in the firmware devcontainer or native environment. Upload from macOS as
explained in [development setup](../DEVELOPMENT_SETUP.md); avoid simultaneous
host/container builds into the same `.pio` directory.

## 2. Suggested modules

| Project | Modules to introduce |
| --- | --- |
| camera | `board_pins`, `camera_stream`, `web_control`, `command_gateway`, `uart_link` |
| bala2 | existing balance/IMU/base modules plus `uart_link`, `command_mailbox`, `drive_reference`, `safety_state` |
| shared specification | frame codec, protocol constants and golden byte vectors |

WebSocket callbacks validate and replace a single latest-command slot. UART
parsing runs outside the balance task and atomically publishes a complete
validated command. The balance task reads a snapshot without waiting for UART,
JSON parsing, Wi-Fi or logging. Use fixed buffers and bounded queues; discard
obsolete movement commands rather than accumulating them.

## 3. Web server and joystick

Run a password-protected access point initially. Serve all assets locally so
the page works without Internet/CDNs. Print the actual IP to USB and optionally
the Fire display through telemetry. A proposed endpoint layout is:

| Endpoint | Purpose |
| --- | --- |
| `http://<robot>/` | HTML, CSS and joystick JavaScript |
| `ws://<robot>/ws` | Commands and telemetry |
| `http://<robot>:81/stream` | MJPEG multipart response for an HTML `img` |
| `http://<robot>/status` | Read-only health snapshot |

Use distinct server tasks/instances for the indefinite stream handler and
control requests; assign distinct internal server control ports too. Bound
stream send time and close slow clients. Espressif's example separates the
stream server from the control server; extend that pattern for WebSocket
control using a framework configuration with WebSocket support.
[Reference server implementation](https://raw.githubusercontent.com/espressif/arduino-esp32/master/libraries/ESP32/examples/Camera/CameraWebServer/app_httpd.cpp)

Implement a touch/mouse joystick using Pointer Events, pointer capture and
`touch-action: none`. Normalize forward and turn to [-1, 1], use a radial
approximately 0.08 dead zone, and define forward as pushing upward and positive
turn as left/counterclockwise. Send at 20 Hz while the operator holds the
control; do not rely on pointer motion events for heartbeats. Send neutral on
release, `pointercancel`, lost capture, window blur and page hidden. These
messages are best effort; device-side expiry is authoritative.

Example browser command (proposed schema):

```json
{"v":1,"session":12345,"seq":42,"type":"drive","forward":0.2,"turn":-0.1,"held":true}
```

Reject unsupported versions, unknown types, non-finite/out-of-range numbers,
wrong sessions and oversized messages (initial maximum 256 bytes). Permit one
controlling client; other viewers cannot send motion commands. Issue a new
session on ownership acquisition, require explicit arm at neutral, and check
WebSocket Origin plus a session token. Keep deployment on a trusted local
network; Internet operation needs a separate authentication/encryption design.

Show connection state, Fire-reported arm/fault state, last accepted sequence,
command age and video status. Disable movement if telemetry becomes stale.
A frozen image must not appear to be proof of a healthy control connection.

## 4. UART contract, version 1 proposal

Use 115200 baud, 8N1, no hardware flow control. Define the codec before
integrating motors. One proposed fixed frame is **28 bytes**, all multibyte
integers little-endian; serialize fields explicitly, never transmit a C struct.

| Offset | Size | Field |
| --- | --- | --- |
| 0 | 2 | Sync bytes `A5 5A` |
| 2 | 1 | Version `1` |
| 3 | 1 | Type: HELLO=1, ARM=2, DRIVE=3, STOP=4, DISARM=5, STATUS=6 |
| 4 | 4 | Fire boot-session nonce |
| 8 | 4 | Sequence number |
| 12 | 2 | Signed forward value, -1000 to +1000 |
| 14 | 2 | Signed turn value, -1000 to +1000 |
| 16 | 2 | Flags: bit 0 operator-held; other bits zero for commands |
| 18 | 4 | Sender monotonic milliseconds, diagnostics only |
| 22 | 4 | Reserved zero for commands; STATUS detail field |
| 26 | 2 | CRC-16/CCITT-FALSE over bytes 2..25, stored little-endian |

CRC parameters: polynomial `0x1021`, initial value `0xFFFF`, no reflection,
no final XOR. Check vector ASCII `123456789` gives `0x29B1`. This CRC detects
corruption; it is not authentication. At 20 Hz, command traffic is 560 bytes/s,
about 4.9% of the 11520-byte/s capacity per direction at 8N1.

On boot Fire creates a new random nonzero nonce and remains disarmed. HELLO
from XIAO uses zero session and zero motion; Fire replies STATUS with its nonce.
Only ARM with the current nonce, neutral values and locally satisfied readiness
checks can enable driving. Reset the accepted sequence on a successful new
session, not on every HELLO. XIAO restart/browser ownership change must perform
DISARM then explicit re-arm; never silently resume the previous command.

DRIVE must carry the current session and a newer sequence. Compare uint32
sequence deltas modulo 2^32, accepting deltas 1..2^31-1; duplicates and older
frames do not refresh expiry. Increment the transmitted sequence only for a
fresh accepted browser input. Do not replay the last held input as a new command.
STOP requests zero motion while preserving healthy balance. DISARM disables
motor drive and latches disarmed. Accept valid current-session STOP/DISARM even
if reordered, since they reduce authority; never use them to refresh motion.
Require neutral/held=false for STOP, DISARM, HELLO and ARM.

STATUS at 10 Hz echoes the last accepted command sequence; forward/turn report
applied normalized references. Flags: bit 0 armed, bit 1 healthy balancing,
bit 2 timed out, bit 3 fault. Detail bytes 22..23 contain command age in ms
(saturating at 65535), byte 24 fault code (0 none, 1 tilt, 2 IMU, 3 motor bus,
4 deadline), byte 25 reserved zero. Document additional fields via a new version.

The receiver searches sync, collects exactly 28 bytes, validates CRC/version/
type/session/fields, then publishes. On a bad candidate, resume searching one
byte after its start, preserving possible embedded sync. Abandon a partial
frame after 50 ms. Bound bytes processed per task iteration; malformed data,
boot logs, partial frames and buffer overflow never arm or refresh the watchdog.

## 5. Local command limits and loss handling

The Fire owns configured maximum velocity/yaw rate and acceleration limits.
Convert normalized values into controller references only after measuring
wheel radius, encoder units and wheel separation. Start with very small limits
in a support fixture. Add yaw differential control with saturation that preserves
balance authority. Verify motor signs independently before live balance tests.

Initial timeout proposal:

- XIAO: after 150 ms without a fresh valid browser command, invalidate its
  command slot and send STOP; never keep forwarding stale held inputs.
- Fire: after 250 ms without a fresh valid DRIVE, ramp translation/yaw references
  to zero using validated deceleration, stay balancing if healthy, and latch
  motion inhibited until explicit neutral re-arm.
- Either board reboot, disconnect or controller replacement requires a new
  operator arm action. A fresh network connection alone cannot move the robot.

Expiry must be evaluated each balance cycle using Fire local elapsed time,
not synchronized browser clocks. Telemetry, HELLO, malformed or duplicate frames
do not extend the deadline. Separately monitor IMU freshness, motor-bus failures,
excess tilt and missed control deadlines: these require a local fault response,
including disabling motor output where appropriate. Timeout zero velocity is
not motor power-off; a balancing robot still needs wheel actuation to stand.

Provide an accessible physical stop/power control for testing. A UI emergency
stop cannot be guaranteed when the wireless link is lost. Test motor-disable
behavior while supported because the robot will fall when balance is disabled.

## 6. Delivery sequence

1. Baseline Fire balance and standalone XIAO camera, recording versions.
2. Port B UART HELLO/STATUS and codec tests with motors disabled.
3. Browser joystick to Fire telemetry only; verify axes and expiry.
4. Add video concurrently; measure command latency and control deadlines.
5. Add arm/state machine and bounded references in a support fixture.
6. Run the [validation checklist](VALIDATION.md), then restrained floor trials.
7. Package both firmware binaries, flash metadata, source revisions, protocol
   version, wiring revision and measured operating limits together.
