"""UTC clock synchronization and RFC 3339 timestamp formatting."""

import time

import ntptime


def sync_utc_clock(attempts=3):
    """Synchronize the ESP32 real-time clock using NTP."""
    last_error = None

    for attempt in range(1, attempts + 1):
        try:
            ntptime.settime()
            print("[TIME] UTC clock synchronized")
            return
        except Exception as error:
            last_error = error
            print("[TIME] NTP attempt %s/%s failed: %s" % (attempt, attempts, error))
            time.sleep(2)

    raise RuntimeError("Unable to synchronize UTC clock: %s" % last_error)


def utc_now_iso():
    """Return the current device clock as an RFC 3339 UTC timestamp."""
    now = time.gmtime()

    if now[0] < 2024:
        raise RuntimeError("Device clock is not synchronized")

    return (
        "%04d-%02d-%02dT%02d:%02d:%02dZ"
        % (now[0], now[1], now[2], now[3], now[4], now[5])
    )
