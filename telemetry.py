"""AgriSentry MQTT telemetry contract v1."""

try:
    import ujson as json
except ImportError:
    import json

from identifiers import uuid4

PROTOCOL_VERSION = "1.0"

CHANNEL_UNITS = {
    "air_temperature": "celsius",
    "air_relative_humidity": "percent",
    "solution_temperature": "celsius",
    "solution_ph": "ph",
    "solution_tds": "ppm",
    "reservoir_level": "percent",
    "relative_light": "percent",
}

QUALITY_VALUES = {
    "valid",
    "estimated",
    "unstable",
    "out_of_range",
    "sensor_error",
    "not_calibrated",
}


def make_reading(
    channel,
    raw_value,
    value,
    quality,
    calibration_id=None,
):
    """Create and validate one sensor reading."""
    if channel not in CHANNEL_UNITS:
        raise ValueError("Unsupported telemetry channel: %s" % channel)

    if quality not in QUALITY_VALUES:
        raise ValueError("Unsupported telemetry quality: %s" % quality)

    if not isinstance(raw_value, (int, float)):
        raise TypeError("raw_value must be numeric")

    if value is not None and not isinstance(value, (int, float)):
        raise TypeError("value must be numeric or None")

    return {
        "channel": channel,
        "raw_value": raw_value,
        "value": value,
        "unit": CHANNEL_UNITS[channel],
        "quality": quality,
        "calibration_id": calibration_id,
    }


def build_envelope(
    device_id,
    firmware_version,
    sequence,
    observed_at,
    readings,
    event_id=None,
):
    """Build one MQTT v1 telemetry envelope."""
    if not device_id:
        raise ValueError("device_id is required")

    if not firmware_version:
        raise ValueError("firmware_version is required")

    if not isinstance(sequence, int) or sequence < 0:
        raise ValueError("sequence must be a non-negative integer")

    if not readings:
        raise ValueError("at least one reading is required")

    channels = [reading["channel"] for reading in readings]
    if len(channels) != len(set(channels)):
        raise ValueError("telemetry channels must be unique per envelope")

    return {
        "protocol_version": PROTOCOL_VERSION,
        "event_id": event_id or uuid4(),
        "device_id": device_id,
        "sequence": sequence,
        "observed_at": observed_at,
        "firmware_version": firmware_version,
        "readings": readings,
    }


def serialize(envelope):
    """Serialize an envelope into compact JSON."""
    try:
        return json.dumps(envelope, separators=(",", ":"))
    except TypeError:
        # MicroPython ujson versions may not accept ``separators``.
        return json.dumps(envelope)
