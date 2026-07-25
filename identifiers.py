"""Identifier generation compatible with CPython and MicroPython."""

try:
    import urandom as _random
except ImportError:  # CPython test environment
    import random as _random


def uuid4():
    """Generate a UUID v4 string without requiring the CPython uuid module."""
    data = bytearray(_random.getrandbits(8) for _ in range(16))
    data[6] = (data[6] & 0x0F) | 0x40
    data[8] = (data[8] & 0x3F) | 0x80

    hexadecimal = "".join("%02x" % byte for byte in data)

    return "%s-%s-%s-%s-%s" % (
        hexadecimal[0:8],
        hexadecimal[8:12],
        hexadecimal[12:16],
        hexadecimal[16:20],
        hexadecimal[20:32],
    )
