# AgriSentry Device Firmware

MicroPython firmware for the ESP32 edge device used by the AgriSentry platform.

The hydroponics setup is the first physical laboratory for the platform. The
firmware itself follows a generic agricultural telemetry contract and is not
limited to hydroponics.

## Current milestone

`2.0.0-alpha.1` implements the first firmware-to-gateway vertical slice:

- Wi-Fi connection with timeout;
- NTP clock synchronization;
- MQTT v1 telemetry topic;
- seven simulated sensor channels;
- durable monotonic sequence;
- UUID v4 event identifiers;
- QoS 1 publication;
- complete-envelope offline JSONL cache;
- automatic replay after reconnection;
- host-side contract tests.

Physical sensor drivers, OLED output, buttons and relay commands are the next
firmware milestones.

## MQTT topic

```text
agrisentry/v1/devices/{device_id}/telemetry
```

## Sensor channels

- `air_temperature`
- `air_relative_humidity`
- `solution_temperature`
- `solution_ph`
- `solution_tds`
- `reservoir_level`
- `relative_light`

## Device setup

1. Flash a current MicroPython build on the ESP32.
2. Install `micropython-umqtt.simple`.
3. Copy `config.example.py` to `config.py`.
4. Set Wi-Fi and MQTT values in `config.py`.
5. Upload these files to the ESP32 root:

```text
boot.py
main.py
networking.py
time_sync.py
identifiers.py
telemetry.py
simulated_sensors.py
sequence_store.py
cache.py
config.py
```

The MQTT broker address must be the LAN IP address of the computer running the
broker, not `127.0.0.1`.

## Host-side validation

No ESP32 is required to test the contract-building modules:

```powershell
python -m unittest discover -s tests -v
```

## Secrets

`config.py` is ignored by Git. Commit only `config.example.py`.
