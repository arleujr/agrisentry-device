"""Durable monotonic sequence storage."""

try:
    import uos as os
except ImportError:
    import os


class SequenceStore:
    """Persist the last allocated device sequence in a small text file."""

    def __init__(self, path="sequence.state"):
        self.path = path
        self.temporary_path = path + ".tmp"

    def current(self):
        try:
            with open(self.path, "r") as file_handle:
                value = int(file_handle.read().strip())
                return max(0, value)
        except (OSError, ValueError):
            return 0

    def next(self):
        value = self.current() + 1
        self._write_atomically(value)
        return value

    def _write_atomically(self, value):
        with open(self.temporary_path, "w") as file_handle:
            file_handle.write(str(value))

        try:
            os.remove(self.path)
        except OSError:
            pass

        os.rename(self.temporary_path, self.path)
