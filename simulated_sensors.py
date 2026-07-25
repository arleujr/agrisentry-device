"""Deterministic readings used before the physical sensors are connected."""

from telemetry import make_reading


def read_all(sequence):
    """Return all seven AgriSentry v1 channels with realistic test variation."""
    phase = sequence % 10

    air_temperature = round(24.0 + phase * 0.3, 1)
    air_humidity = round(72.0 - phase * 0.5, 1)
    solution_temperature = round(22.0 + phase * 0.1, 1)
    solution_ph = round(6.0 + (phase - 5) * 0.02, 2)
    solution_tds = 720 + phase * 4
    reservoir_level = max(0, 82 - phase)
    relative_light = 75 + phase * 2

    return [
        make_reading(
            "air_temperature",
            air_temperature,
            air_temperature,
            "valid",
        ),
        make_reading(
            "air_relative_humidity",
            air_humidity,
            air_humidity,
            "valid",
        ),
        make_reading(
            "solution_temperature",
            2000 + phase * 8,
            solution_temperature,
            "estimated",
            "sim-ntc-v1",
        ),
        make_reading(
            "solution_ph",
            1850 + phase * 3,
            solution_ph,
            "not_calibrated",
        ),
        make_reading(
            "solution_tds",
            1400 + phase * 5,
            solution_tds,
            "estimated",
            "sim-tds-v1",
        ),
        make_reading(
            "reservoir_level",
            2500 - phase * 20,
            reservoir_level,
            "estimated",
            "sim-level-v1",
        ),
        make_reading(
            "relative_light",
            3000 + phase * 15,
            relative_light,
            "estimated",
            "sim-light-v1",
        ),
    ]
