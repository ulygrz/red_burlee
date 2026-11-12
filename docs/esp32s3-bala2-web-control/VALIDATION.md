# Bring-up and acceptance checklist

Status: **not executed on hardware**. Source inspection established the proposed
pin mapping and firmware starting point; it does not validate electrical wiring,
compilation, controller tuning or performance. Record actual results below or
in a dated sibling report, including board revisions and firmware commits.

Use a stable support fixture for first motor tests, keep wheels clear and have
a physical power stop available. Move to floor tests only after link-loss and
motor-fault behavior pass.

| Stage | Test | Initial acceptance criterion |
| --- | --- | --- |
| Wiring | Continuity, voltage, TX/RX direction, power-source isolation | Matches HARDWARE.md; no 5 V on logic; GPIO16/17 unused by gateway |
| Baselines | Build/boot each board, PSRAM, camera sensor, original balance | Record pinned dependencies, logs, calibration and successful behavior |
| UART | 10-minute bidirectional frames, motors disabled | No unexplained resets/errors; count CRC failures and overflows |
| Parser | Garbage, truncated frame, embedded sync, bad CRC/version/type, invalid ranges | No command accepted; next valid frame recovers |
| Session | Wrong nonce, duplicate/reordered sequence, wraparound, board reboot | Stale commands rejected; no automatic movement after reconnect |
| UI | Touch/mouse release, cancel, blur, hidden tab and two clients | Neutral/revoked ownership; exactly one controller |
| Timeout | Close browser, kill Wi-Fi, unplug UART, freeze gateway task | Fire initiates zero-reference behavior by 250 ms plus one balance cycle |
| Stale replay | Continue telemetry/HELLO or repeat old DRIVE after browser loss | Motion deadline still expires |
| Video load | One viewer, slow viewer, stream disconnect and repeated reloads | Control remains responsive; no accumulating frame buffers or command queue |
| Timing | Record loop duration/jitter with video off/on | Target 5 ms loop maintained; investigate every deadline overrun |
| Latency | Instrument browser send through Fire acceptance | Initial target p95 below 100 ms; report method and worst case |
| Power | Camera/Wi-Fi plus motor acceleration and low-battery conditions | No brownouts or unstable supply; measured rail stays within board limits |
| Motor control | Axis signs, neutral, limits, saturation and arm at non-neutral | Correct signs, bounded references, non-neutral arm rejected |
| Faults | Simulated IMU stale data, motor bus failure, excessive tilt | Local fault handling does not depend on browser or UART |
| Endurance | 30-minute combined stream/control after earlier stages pass | No growing memory loss, reset, unsafe reconnect or unexplained timing failure |

For latency, browser and Fire clocks are not directly comparable. Measure
round-trip sequence acknowledgments with the browser clock, or instrument a
shared logic-analyzer timebase for one-way timing. Label RTT as RTT, not one-way
latency. Separately film a changing scene/display to estimate glass-to-glass
video delay; FPS alone does not measure delay.

Keep counters for accepted/rejected frames, parser resets, UART overflow,
command age, watchdog activations, camera acquisition failures, free/minimum
heap, loop worst-case time and reset reason. Logs must not block the balance loop.

## Troubleshooting

| Symptom | First checks |
| --- | --- |
| Fire crashes after UART enabled | Accidental default pins 16/17, PSRAM conflict, two UART owners |
| No Fire commands | Cross TX/RX correctly; RX36/TX26 order; common ground and matching baud |
| Noise while camera boots | Console/boot output on GPIO43; framing rejection and explicit arm |
| Camera fails initialization | Actual sensor/pin map, PSRAM/partition settings, power and ribbon seating |
| Joystick freezes while streaming | Blocking stream handler, shared server task, unbounded socket writes |
| Motion persists after disconnect | Old commands re-sequenced, telemetry refreshing watchdog, expiry outside control task |
| I2C causes balance instability | Shared-bus contention, wrong pull-up voltage, camera controller collision, unbounded polling |
| Random resets during movement | Supply droop, ground routing, motor noise, cable strain |

## Result record template

```text
Date / operator:
Fire / base / XIAO / camera revisions:
Firmware commits and dependency versions:
Power and wiring revision:
Test / procedure:
Expected / measured result:
Logs or captures:
Pass / fail / corrective action:
```
