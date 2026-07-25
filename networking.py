"""Wi-Fi connectivity helpers for MicroPython."""

import time

import network


def connect_wifi(ssid, password, timeout_seconds=20):
    """Connect to Wi-Fi and return the active station interface."""
    station = network.WLAN(network.STA_IF)
    station.active(True)

    if station.isconnected():
        print("[WIFI] Already connected:", station.ifconfig())
        return station

    print("[WIFI] Connecting to:", ssid)
    station.connect(ssid, password)

    started_at = time.time()
    while not station.isconnected():
        if time.time() - started_at >= timeout_seconds:
            raise RuntimeError("Wi-Fi connection timed out")
        time.sleep(1)

    print("[WIFI] Connected:", station.ifconfig())
    return station


def ensure_wifi(ssid, password, timeout_seconds=20):
    """Reconnect only when the station is currently offline."""
    station = network.WLAN(network.STA_IF)
    if station.isconnected():
        return station

    return connect_wifi(ssid, password, timeout_seconds)
