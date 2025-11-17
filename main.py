import time
import machine
import ubinascii
import json
import dht
from machine import Pin, ADC
from umqtt.simple import MQTTClient
from config import MQTT_BROKER, MQTT_USER, MQTT_PASSWORD
import cache

print("--- Starting AgriSentry Field Agent (Hardware + Security) ---")

# --- Hardware Initialization ---
try:
    sensor_dht = dht.DHT11(Pin(4))
    adc_solo = ADC(Pin(34))
    adc_solo.atten(ADC.ATTN_11DB)
    rele_pin = Pin(26, Pin.OUT)
    rele_pin.on() # Failsafe: Set pin HIGH to keep active-low relay OFF on boot.
except Exception as e:
    print(f"[FATAL ERROR] Failed to initialize pins: {e}. Resetting in 10s.")
    time.sleep(10)
    machine.reset()

# --- Global State ---
current_rule = None
mqtt_client = None
loop_counter = 0

# --- Hardware Logic ---

def convert_soil_to_percentage(raw_value, val_max_dry=4095, val_min_wet=1500):
    """ Converts raw ADC reading to a 0-100% moisture value. """
    percentage = 100 * (val_max_dry - raw_value) / (val_max_dry - val_min_wet)
    if percentage < 0: return 0
    if percentage > 100: return 100
    return round(percentage, 2)

def read_sensors():
    """ Reads all physical sensors and returns a data dictionary. """
    try:
        sensor_dht.measure()
        temperatura = sensor_dht.temperature()
        umidade_ar = sensor_dht.humidity()
        
        valor_solo_raw = adc_solo.read()
        umidade_solo = convert_soil_to_percentage(valor_solo_raw)
        
        print(f"[SENSOR] Read: {temperatura}°C, {umidade_ar}% Air, {umidade_solo}% Soil")
        return {"TEMPERATURE": temperatura, "HUMIDITY": umidade_ar, "SOIL_MOISTURE": umidade_solo}
    except Exception as e:
        print(f"[SENSOR ERROR] Failed to read sensors: {e}")
        return None

def control_relay(state):
    """ Controls the physical relay (assumes active-low). """
    if state:
        rele_pin.off() # Set pin LOW to turn relay ON
        print("[ACTION] Relay: ON")
    else:
        rele_pin.on()  # Set pin HIGH to turn relay OFF
        print("[ACTION] Relay: OFF")

def evaluate_rule(sensor_readings):
    """ Evaluates the current rule against new sensor data. """
    if not current_rule or not sensor_readings:
        control_relay(False) # Failsafe
        return

    try:
        condition = current_rule.get('condition')
        threshold = current_rule.get('threshold')
        action = current_rule.get('action')
        
        # Rule logic is currently hardcoded to SOIL_MOISTURE
        sensor_value = sensor_readings.get("SOIL_MOISTURE")
        if sensor_value is None:
            return 
            
        should_activate = False
        if condition == "LESS_THAN" and sensor_value < threshold:
            should_activate = True
        elif condition == "GREATER_THAN" and sensor_value > threshold:
            should_activate = True
        
        print(f"[LOGIC] Evaluating: {sensor_value} (Soil) {condition} {threshold}? -> Activate: {should_activate}")

        if should_activate:
            control_relay(action == "TURN_ON")
        else:
            control_relay(action == "TURN_OFF")
    
    except Exception as e:
        print(f"[ERROR] Failed to evaluate rule: {e}")

# --- Connectivity & Caching Logic ---

def on_message(topic, msg):
    """ Callback for handling subscribed MQTT messages. """
    global current_rule
    topic_str = topic.decode()
    payload_str = msg.decode()
    
    print(f"\n[MQTT] Message received!")
    print(f"   > Topic: {topic_str}")

    if topic_str.endswith("/config/set"):
        print(f"   > Config Payload: {payload_str}")
        try:
            rule = json.loads(payload_str)
            if rule:
                current_rule = rule
                print(f"[INFO] Rule updated: {current_rule}")
            else:
                current_rule = None
        except Exception as e:
            print(f"[ERROR] Failed to decode rule JSON: {e}")

def connect_and_subscribe():
    """ Connects to the MQTT broker and subscribes to config topics. """
    global mqtt_client
    mac = ubinascii.hexlify(machine.unique_id()).decode()
    client_id = f"agrisentry-device-{mac}"
    
    try:
        print(f"Attempting to connect to MQTT broker at {MQTT_BROKER}...")
        client = MQTTClient(
            client_id, 
            MQTT_BROKER, 
            user=MQTT_USER, 
            password=MQTT_PASSWORD, 
            keepalive=60
        )
        client.set_callback(on_message)
        client.connect()
        print("[SUCCESS] Connected to MQTT Broker.")
        
        response_topic = f"agrisentry/devices/{mac}/config/set"
        client.subscribe(response_topic)
        print(f"[MQTT] Subscribed to: {response_topic}")
        
        config_topic = f"agrisentry/devices/{mac}/config/get"
        client.publish(config_topic, b'{}')
        print(f"[MQTT] Configuration request sent.")
        
        mqtt_client = client
        return True
    except Exception as e:
        print(f"[FAILURE] Error connecting to MQTT: {e}")
        mqtt_client = None
        return False

def sync_offline_readings():
    """ Publishes all cached readings when connection is restored. """
    if not mqtt_client: return

    print("[SYNC] Checking for offline readings...")
    lines = cache.get_unsent_readings()
    if not lines:
        print("[SYNC] No offline readings to sync.")
        return

    print(f"[SYNC] Found {len(lines)} readings. Sending...")
    mac = ubinascii.hexlify(machine.unique_id()).decode()
    telemetry_topic = f"agrisentry/devices/{mac}/telemetry"
    
    success = True
    for i, line in enumerate(lines):
        try:
            mqtt_client.publish(telemetry_topic, line.strip())
            print(f"  > Sent offline reading {i+1}/{len(lines)}...")
            time.sleep(0.1) # Prevent network flooding
        except Exception as e:
            print(f"[SYNC ERROR] Failed to send reading: {e}. Stopping sync.")
            success = False
            break

    if success:
        cache.clear_cache()
    print("[SYNC] Synchronization complete.")

# --- Main Application Loop ---
while True:
    try:
        # Connection Management
        if mqtt_client is None:
            if connect_and_subscribe():
                sync_offline_readings()

        if mqtt_client:
            mqtt_client.check_msg()

        # Scheduled Tasks (every 10 seconds)
        if loop_counter % 10 == 0:
            readings = read_sensors()
            
            if readings:
                evaluate_rule(readings)
                
                sensor_value = readings.get("SOIL_MOISTURE")
                
                payload = json.dumps({
                    "value": sensor_value,
                    "sensor_type": "SOIL_MOISTURE",
                    "timestamp": time.time()
                })

                if mqtt_client:
                    try:
                        mac = ubinascii.hexlify(machine.unique_id()).decode()
                        telemetry_topic = f"agrisentry/devices/{mac}/telemetry"
                        mqtt_client.publish(telemetry_topic, payload)
                        print("[MQTT] Online telemetry sent.")
                    except Exception as e:
                        print(f"[ERROR] Failed to send telemetry: {e}. Connection lost.")
                        mqtt_client = None
                        cache.save_reading(sensor_value, time.time())
                else:
                    print("[OFFLINE] No connection. Saving reading to cache.")
                    cache.save_reading(sensor_value, time.time())

        loop_counter += 1
        time.sleep(1) # Main loop tick

    except Exception as e:
        print(f"[FATAL ERROR] Critical error in main loop: {e}")
        print("Restarting in 10 seconds...")
        time.sleep(10)
        machine.reset()