"""AgriSentry Device v2 physical environmental telemetry slice."""

import time

import config
from cache import TelemetryCache
from networking import ensure_wifi
from sequence_store import SequenceStore
from telemetry import build_envelope, serialize
from time_sync import sync_utc_clock, utc_now_iso
from umqtt.simple import MQTTClient


DEVICE_ID = config.DEVICE_ID
TELEMETRY_TOPIC = "agrisentry/v1/devices/%s/telemetry" % DEVICE_ID
SIMULATION_MODE = getattr(config, "SIMULATION_MODE", True)

sequence_store = SequenceStore()
telemetry_cache = TelemetryCache()
mqtt_client = None
sensor_reader = None
display = None


def initialize_inputs():
    """Initialize either deterministic simulation or physical hardware."""
    global sensor_reader, display

    if SIMULATION_MODE:
        from simulated_sensors import read_all

        sensor_reader = read_all
        print("[APP] Simulation sensors enabled")
        return

    from display import OledDisplay
    from physical_sensors import PhysicalSensors

    physical = PhysicalSensors()
    sensor_reader = lambda _sequence: physical.read_all()
    display = OledDisplay(physical.i2c)
    print("[APP] Physical sensors enabled")


def build_client():
    """Create and connect the MQTT client."""
    client_id = "agrisentry-device-%s" % DEVICE_ID
    client = MQTTClient(
        client_id=client_id,
        server=config.MQTT_BROKER,
        port=getattr(config, "MQTT_PORT", 1883),
        user=getattr(config, "MQTT_USER", None),
        password=getattr(config, "MQTT_PASSWORD", None),
        keepalive=getattr(config, "MQTT_KEEPALIVE_SECONDS", 30),
        ssl=getattr(config, "MQTT_TLS", False),
    )
    client.connect()
    print(
        "[MQTT] Connected to %s:%s"
        % (
            config.MQTT_BROKER,
            getattr(config, "MQTT_PORT", 1883),
        )
    )
    return client


def ensure_mqtt():
    """Reconnect Wi-Fi, synchronize time and connect MQTT when needed."""
    global mqtt_client

    if mqtt_client is not None:
        return mqtt_client

    ensure_wifi(
        config.WIFI_SSID,
        config.WIFI_PASSWORD,
        getattr(config, "WIFI_CONNECT_TIMEOUT_SECONDS", 20),
    )

    try:
        utc_now_iso()
    except RuntimeError:
        sync_utc_clock()

    mqtt_client = build_client()
    return mqtt_client


def publish_envelope(envelope):
    """Publish one envelope using MQTT QoS 1."""
    client = ensure_mqtt()
    payload = serialize(envelope).encode("utf-8")
    client.publish(TELEMETRY_TOPIC, payload, qos=1)
    print(
        "[MQTT] Published event=%s sequence=%s readings=%s"
        % (
            envelope["event_id"],
            envelope["sequence"],
            len(envelope["readings"]),
        )
    )


def replay_cache():
    """Publish cached envelopes and preserve the first unsent item onward."""
    cached = telemetry_cache.load()
    if not cached:
        return

    print("[CACHE] Replaying %s envelope(s)" % len(cached))

    for index, envelope in enumerate(cached):
        try:
            publish_envelope(envelope)
        except Exception as error:
            telemetry_cache.replace(cached[index:])
            print("[CACHE] Replay interrupted:", error)
            return

    telemetry_cache.clear()
    print("[CACHE] Replay completed")


def read_inputs(sequence):
    """Read simulated or physical inputs once."""
    result = sensor_reader(sequence)

    if SIMULATION_MODE:
        return result, {}

    return result


def build_current_envelope(sequence, readings):
    """Build an MQTT envelope after the device clock is valid."""
    return build_envelope(
        device_id=DEVICE_ID,
        firmware_version=config.FIRMWARE_VERSION,
        sequence=sequence,
        observed_at=utc_now_iso(),
        readings=readings,
    )


def update_display(snapshot, status):
    """Update the optional display without affecting the main loop."""
    if display is not None:
        display.show(snapshot, status)


def mark_connection_lost(error):
    """Dispose the current client after a connectivity failure."""
    global mqtt_client

    print("[MQTT] Connection lost:", error)

    if mqtt_client is not None:
        try:
            mqtt_client.disconnect()
        except Exception:
            pass

    mqtt_client = None


def run():
    """Run the resilient device telemetry loop."""
    print("[APP] Device:", DEVICE_ID)
    print("[APP] Topic:", TELEMETRY_TOPIC)
    print(
        "[APP] Mode:",
        "simulation" if SIMULATION_MODE else "physical",
    )

    initialize_inputs()
    interval = max(
        5,
        getattr(config, "TELEMETRY_INTERVAL_SECONDS", 10),
    )

    while True:
        snapshot = {}
        envelope = None

        try:
            sequence = sequence_store.next()
            readings, snapshot = read_inputs(sequence)
            update_display(snapshot, "CONNECT")

            # A cold boot needs Wi-Fi/NTP before an envelope can be timestamped.
            # After the RTC is valid, an MQTT outage can still be cached.
            try:
                observed_at = utc_now_iso()
            except RuntimeError:
                ensure_mqtt()
                observed_at = utc_now_iso()

            envelope = build_envelope(
                device_id=DEVICE_ID,
                firmware_version=config.FIRMWARE_VERSION,
                sequence=sequence,
                observed_at=observed_at,
                readings=readings,
            )

            try:
                ensure_mqtt()
                replay_cache()
                publish_envelope(envelope)
                update_display(snapshot, "ONLINE")
            except Exception as error:
                telemetry_cache.append(envelope)
                mark_connection_lost(error)
                update_display(snapshot, "OFFLINE")
                print("[CACHE] Envelope stored for later replay")
        except Exception as error:
            print("[APP] Cycle failed:", error)
            update_display(snapshot, "ERROR")

        time.sleep(interval)


run()
