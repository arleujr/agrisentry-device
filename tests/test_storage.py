import tempfile
import unittest
from pathlib import Path

from cache import TelemetryCache
from sequence_store import SequenceStore


class StorageTests(unittest.TestCase):
    def test_sequence_survives_new_store_instance(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "sequence.state")

            self.assertEqual(SequenceStore(path).next(), 1)
            self.assertEqual(SequenceStore(path).next(), 2)
            self.assertEqual(SequenceStore(path).current(), 2)

    def test_cache_preserves_complete_envelopes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "telemetry_cache.jsonl")
            cache = TelemetryCache(path)

            first = {"event_id": "first", "readings": [{"channel": "a"}]}
            second = {"event_id": "second", "readings": [{"channel": "b"}]}

            cache.append(first)
            cache.append(second)

            self.assertEqual(cache.load(), [first, second])
            self.assertEqual(cache.count(), 2)

            cache.replace([second])
            self.assertEqual(cache.load(), [second])

            cache.clear()
            self.assertEqual(cache.load(), [])


if __name__ == "__main__":
    unittest.main()
