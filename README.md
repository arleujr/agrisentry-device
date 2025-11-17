# AgriSentry Device Firmware

**Author:** [Arleu Júnior](https://github.com/arleujr)

[](https://www.google.com/search?q=https://github.com/arleujr/agrisentry-device/blob/main/LICENSE)
[](https://micropython.org/)

Resilient MicroPython firmware for the AgriSentry IoT platform, designed for field autonomy on ESP32 hardware.

-----

## Core Principles

This firmware is engineered to solve a common problem in real-world IoT: network instability. It is built to be an autonomous, reliable field agent, not a "dumb" client.

1.  **Resilience First:** Network connections are unreliable. This firmware is offline-first. Sensor data is the most valuable asset, and it must never be lost.
2.  **Autonomy:** Automation logic (the rules) is executed *on the device*. A network failure must not stop the system from protecting its crop.
3.  **Security:** All communication is authenticated. No anonymous clients are permitted to connect.

## System Overview

The firmware runs a main loop that connects to the `agrisentry-iot-gateway`, subscribes to its configuration topic (`.../config/set`), and then requests its rules. Once the rules are received, the device operates autonomously.

```
[Gateway (Rust)] <--- (MQTT) ---> [Mosquitto Broker] <--- (MQTT) --- [ESP32 Device]
 (Backend)                                                        (This Firmware)
                                                                      |
                                                                      v
                                                    [Sensor(s)] ---- [GPIO] ---- [Relay(s)]
                                                    (DHT11, ADC)                (Actuator)
```

## Features

  - **Secure MQTT:** Connects to the broker using `MQTT_USER` and `MQTT_PASSWORD` credentials.
  - **Offline Cache (JSONL):** On connection loss, all telemetry is spooled to a simple, efficient `cache.jsonl` file on the device's filesystem.
  - **Automatic Synchronization:** Upon reconnection, the device uploads the entire cached log (all missed readings) to the gateway and then clears the file, ensuring **zero data loss**.
  - **Local Rule Engine:** Automation rules (e.g., `IF SOIL_MOISTURE < 30 THEN TURN_ON relay`) are evaluated locally by the ESP32 for real-time response.
  - **Hardware I/O:** Built-in logic for reading common agricultural sensors (DHT11, analog capacitive soil sensors) and controlling physical relays.

## Setup & Configuration

### 1\. Prerequisites

  - An ESP32 board.
  - A MicroPython firmware `.bin` flashed onto the device. The standard build is sufficient.
  - [Thonny IDE](https://thonny.org/) (recommended for managing files and packages).

### 2\. Install Libraries

Using the Thonny package manager (`Tools > Manage packages`), install the following libraries to the MicroPython device:

  * `micropython-umqtt.simple`
  * `micropython-dht`

### 3\. Configuration

1.  Clone this repository.
2.  Create a `config.py` file based on `config.example.py`.
3.  Upload all project files (`boot.py`, `main.py`, `config.py`, `cache.py`) to the root of the ESP32.
4.  Fill in `config.py` with your credentials:

<!-- end list -->

```python
# config.py

# Wi-Fi Network credentials
WIFI_SSID = "YOUR_WIFI_NETWORK"
WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"

# MQTT Broker configuration
MQTT_BROKER = "IP_OF_YOUR_GATEWAY_COMPUTER" # e.g., "192.168.0.102"
MQTT_USER = "agrisentry_user"
MQTT_PASSWORD = "YOUR_MQTT_PASSWORD"
```

## Operation

The device has two main files:

  * `boot.py`: Runs on power-on. Its only job is to connect the device to the Wi-Fi network.
  * `main.py`: The main application loop.
    1.  Connects to the MQTT broker using the secure credentials.
    2.  Subscribes to its unique `.../config/set` topic.
    3.  Publishes to `.../config/get` to request its rules from the gateway.
    4.  Enters an infinite loop where it:
          - Listens for new rule updates (`check_msg()`).
          - Reads physical sensors (`ler_sensores()`).
          - Evaluates the rules against sensor data (`evaluate_rule()`).
          - Controls the relay (`controlar_rele()`).
          - Attempts to send telemetry. If it fails, it calls `cache.save_reading()`. If it succeeds, it checks for and syncs any old data from the cache.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.