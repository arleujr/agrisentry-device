"""AgriSentry Device v2 first vertical slice.

This version publishes all seven telemetry channels using simulated values.
Physical sensor drivers and actuator commands are added in later slices.
"""

import time

import config
from cache import TelemetryCache
from networking import ensure_wifi
from sequence_store import SequenceStore
from simulated_sensors import read_all
from telemetry import build_envelope, serialize
from time_sync import sync_utc_clock, utc_now_iso
from umqtt.simple import MQTTClient

DEVICE_ID = config.DEVICE_ID
TELEMETRY_TOPIC = "agrisentry/v1/devices/%s/telemetry" % DEVICE_ID

sequence_store = SequenceStore()
telemetry_cache = TelemetryCache()
mqtt_client = None


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

    print("[MQTT] Connected to %s:%s" % (
        config.MQTT_BROKER,
        getattr(config, "MQTT_PORT", 1883),
    ))
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


def create_telemetry():
    """Build the next simulated MQTT v1 envelope."""
    sequence = sequence_store.next()

    if not getattr(config, "SIMULATION_MODE", True):
        raise RuntimeError(
            "Physical sensor mode is not implemented in this firmware slice"
        )

    readings = read_all(sequence)

    return build_envelope(
        device_id=DEVICE_ID,
        firmware_version=config.FIRMWARE_VERSION,
        sequence=sequence,
        observed_at=utc_now_iso(),
        readings=readings,
    )


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
    print("[APP] Simulation mode enabled")

    interval = max(5, getattr(config, "TELEMETRY_INTERVAL_SECONDS", 10))

    while True:
        try:
            ensure_mqtt()
            replay_cache()

            envelope = create_telemetry()

            try:
                publish_envelope(envelope)
            except Exception as error:
                telemetry_cache.append(envelope)
                mark_connection_lost(error)
                print("[CACHE] Envelope stored for later replay")

        except Exception as error:
            print("[APP] Cycle failed:", error)

        time.sleep(interval)


run()
