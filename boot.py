"""ESP32 boot sequence: connect Wi-Fi and synchronize the UTC clock."""

import config

from networking import connect_wifi
from time_sync import sync_utc_clock

print("[BOOT] AgriSentry Device v2 starting")

connect_wifi(
    config.WIFI_SSID,
    config.WIFI_PASSWORD,
    timeout_seconds=getattr(config, "WIFI_CONNECT_TIMEOUT_SECONDS", 20),
)

sync_utc_clock()
print("[BOOT] Boot sequence completed")
