# Device implementation of MQTT telemetry v1

The device publishes one envelope containing every sampled channel. A single
`event_id` identifies the complete observation and `sequence` is durable across
device reboots.

Example topic:

```text
agrisentry/v1/devices/hydro-lab-node-01/telemetry
```

The first firmware slice intentionally uses simulated values. This isolates
Wi-Fi, time synchronization, MQTT, idempotency and offline replay from physical
sensor wiring and calibration.

## Offline behavior

When publication fails, the complete envelope is appended to
`telemetry_cache.jsonl`. Reconnection replays the original envelope, preserving
its `event_id`, `sequence` and `observed_at`. The gateway can therefore identify
a replay as the same event instead of storing a duplicate.

## Sequence behavior

`sequence.state` stores the most recently allocated sequence. The value is
incremented before the envelope is built, preventing sequence reuse after a
restart.
