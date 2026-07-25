"""Local device configuration template.

Copy this file to ``config.py`` and replace the placeholders.
Never commit ``config.py``.
"""

WIFI_SSID = "YOUR_WIFI_NETWORK"
WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"

DEVICE_ID = "hydro-lab-node-01"
FIRMWARE_VERSION = "2.0.0-alpha.1"

# Use the LAN IP address of the computer running Mosquitto.
MQTT_BROKER = "192.168.0.100"
MQTT_PORT = 1883
MQTT_USER = None
MQTT_PASSWORD = None
MQTT_TLS = False
MQTT_KEEPALIVE_SECONDS = 30

TELEMETRY_INTERVAL_SECONDS = 10
WIFI_CONNECT_TIMEOUT_SECONDS = 20

# The first vertical slice uses deterministic simulated readings.
SIMULATION_MODE = True
