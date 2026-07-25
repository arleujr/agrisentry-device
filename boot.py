"""ESP32 boot sequence."""

import config
from networking import connect_wifi

print("[BOOT] AgriSentry Device v2 starting")

try:
    connect_wifi(
        config.WIFI_SSID,
        config.WIFI_PASSWORD,
        timeout_seconds=getattr(
            config,
            "WIFI_CONNECT_TIMEOUT_SECONDS",
            20,
        ),
    )
except Exception as error:
    print("[WIFI] Boot connection unavailable:", error)
    print("[WIFI] The application will retry automatically.")

print("[BOOT] Boot sequence completed")