"""Local device configuration template.

Copy this file to ``config.py`` and replace the placeholders.
Never commit ``config.py``.
"""

WIFI_SSID = "YOUR_WIFI_NETWORK"
WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"

DEVICE_ID = "hydro-lab-node-01"
FIRMWARE_VERSION = "2.0.0-alpha.2"

# Use the LAN IP address of the computer running Mosquitto.
MQTT_BROKER = "192.168.0.100"
MQTT_PORT = 1883
MQTT_USER = None
MQTT_PASSWORD = None
MQTT_TLS = False
MQTT_KEEPALIVE_SECONDS = 30

TELEMETRY_INTERVAL_SECONDS = 10
WIFI_CONNECT_TIMEOUT_SECONDS = 20

# Keep True for host/demo simulation. Set False on the physical ESP32.
SIMULATION_MODE = True

# Physical environmental sensors.
DHT_PIN = 27
I2C_BUS_ID = 0
I2C_SDA_PIN = 21
I2C_SCL_PIN = 22
I2C_FREQUENCY_HZ = 100_000

BH1750_PRIMARY_ADDRESS = 0x23
BH1750_SECONDARY_ADDRESS = 0x5C

OLED_ADDRESS = 0x3C
OLED_WIDTH = 128
OLED_HEIGHT = 32

# Temporary compatibility conversion for MQTT v1 ``relative_light``.
# Replace this value after measuring the intended full-light condition.
RELATIVE_LIGHT_FULL_SCALE_LUX = 20_000.0
