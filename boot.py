# boot.py
#
# This script runs on device boot-up.
# Its sole responsibility is to connect the device to the Wi-Fi network.
# The main application logic is in main.py.

import network
import time
from config import WIFI_SSID, WIFI_PASSWORD

# Define a connection timeout in seconds
WIFI_TIMEOUT_SECONDS = 15

print("--- AgriSentry Field Agent Booting ---")

# Initialize the station interface
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

if not wlan.isconnected():
    print(f"Connecting to Wi-Fi network: {WIFI_SSID}...")
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    
    # Wait for the connection to establish, with a timeout
    wait_start_time = time.time()
    while not wlan.isconnected():
        if time.time() - wait_start_time > WIFI_TIMEOUT_SECONDS:
            print("\n[FAILURE] Wi-Fi connection timed out.")
            break
        time.sleep(1)

# Check the final status and log the outcome
if wlan.isconnected():
    print(f"\n[SUCCESS] Wi-Fi connected. Network config: {wlan.ifconfig()}")
else:
    print("\n[FAILURE] Failed to connect to Wi-Fi.")

print("--- Boot sequence finished. Starting main.py ---")