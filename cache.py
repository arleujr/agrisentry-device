"""Offline JSONL cache for complete MQTT v1 telemetry envelopes."""

try:
    import ujson as json
except ImportError:
    import json

try:
    import uos as os
except ImportError:
    import os


class TelemetryCache:
    """Append, replay and safely retain unsent telemetry payloads."""

    def __init__(self, path="telemetry_cache.jsonl"):
        self.path = path
        self.temporary_path = path + ".tmp"

    def append(self, envelope):
        with open(self.path, "a") as file_handle:
            file_handle.write(json.dumps(envelope))
            file_handle.write("\n")

    def load(self):
        payloads = []

        try:
            with open(self.path, "r") as file_handle:
                for line in file_handle:
                    line = line.strip()
                    if line:
                        payloads.append(json.loads(line))
        except OSError:
            return []

        return payloads

    def replace(self, payloads):
        if not payloads:
            self.clear()
            return

        with open(self.temporary_path, "w") as file_handle:
            for payload in payloads:
                file_handle.write(json.dumps(payload))
                file_handle.write("\n")

        try:
            os.remove(self.path)
        except OSError:
            pass

        os.rename(self.temporary_path, self.path)

    def clear(self):
        try:
            os.remove(self.path)
        except OSError:
            pass

    def count(self):
        return len(self.load())
