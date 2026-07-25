import json
import re
import unittest

from simulated_sensors import read_all
from telemetry import build_envelope, make_reading, serialize


class TelemetryContractTests(unittest.TestCase):
    def test_builds_all_seven_contract_channels(self):
        readings = read_all(1)
        envelope = build_envelope(
            device_id="hydro-lab-node-01",
            firmware_version="2.0.0-alpha.1",
            sequence=1,
            observed_at="2026-07-25T01:00:00Z",
            readings=readings,
            event_id="7d30ef8f-7835-4f38-a687-e530195891ad",
        )

        self.assertEqual(envelope["protocol_version"], "1.0")
        self.assertEqual(len(envelope["readings"]), 7)
        self.assertEqual(
            {reading["channel"] for reading in envelope["readings"]},
            {
                "air_temperature",
                "air_relative_humidity",
                "solution_temperature",
                "solution_ph",
                "solution_tds",
                "reservoir_level",
                "relative_light",
            },
        )

    def test_generated_event_id_is_uuid_v4(self):
        envelope = build_envelope(
            device_id="hydro-lab-node-01",
            firmware_version="2.0.0-alpha.1",
            sequence=2,
            observed_at="2026-07-25T01:00:00Z",
            readings=[make_reading("air_temperature", 25, 25, "valid")],
        )

        self.assertRegex(
            envelope["event_id"],
            re.compile(
                r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-"
                r"[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
            ),
        )

    def test_serialized_payload_is_valid_json(self):
        envelope = build_envelope(
            device_id="hydro-lab-node-01",
            firmware_version="2.0.0-alpha.1",
            sequence=3,
            observed_at="2026-07-25T01:00:00Z",
            readings=[make_reading("relative_light", 3000, 80, "estimated")],
        )

        decoded = json.loads(serialize(envelope))
        self.assertEqual(decoded["device_id"], "hydro-lab-node-01")

    def test_rejects_duplicate_channels(self):
        reading = make_reading("air_temperature", 25, 25, "valid")

        with self.assertRaisesRegex(ValueError, "unique"):
            build_envelope(
                device_id="hydro-lab-node-01",
                firmware_version="2.0.0-alpha.1",
                sequence=4,
                observed_at="2026-07-25T01:00:00Z",
                readings=[reading, reading.copy()],
            )

    def test_rejects_incompatible_or_unknown_quality(self):
        with self.assertRaisesRegex(ValueError, "quality"):
            make_reading("solution_ph", 1800, 6.2, "perfect")


if __name__ == "__main__":
    unittest.main()
