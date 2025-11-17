import uos
import json

CACHE_FILE = "readings_cache.jsonl" # JSON Lines format

def save_reading(value, timestamp):
    """
    Saves a single sensor reading as a new line in the cache file.
    Uses 'append' mode ('a') for file system efficiency.
    """
    reading_data = {
        "value": value,
        "timestamp": timestamp,
        "sensor_type": "SOIL_MOISTURE_OFFLINE"
    }
    try:
        # 'a' = append mode, adds to the end of the file
        with open(CACHE_FILE, "a") as f:
            f.write(json.dumps(reading_data) + "\n") # Write the JSON and a newline
        print(f"[CACHE] Offline reading saved: {value}")
    except Exception as e:
        print(f"[CACHE] Error saving reading: {e}")

def get_unsent_readings():
    """
    Reads all lines from the cache and returns them as a list of strings.
    """
    try:
        # 'r' = read mode
        with open(CACHE_FILE, "r") as f:
            lines = f.readlines()
        if lines:
            print(f"[CACHE] Found {len(lines)} unsent readings.")
            return lines
        else:
            return []
    except OSError:
        # [Errno 2] ENOENT: File does not exist, which is normal if no cache exists.
        print("[CACHE] No cache file found.")
        return []
    except Exception as e:
        print(f"[CACHE] Error reading cache: {e}")
        return []

def clear_cache():
    """
    Deletes the cache file. Called after a successful sync.
    """
    try:
        uos.remove(CACHE_FILE)
        print("[CACHE] Cache cleared successfully.")
    except OSError:
        # File already deleted or never existed. This is fine.
        pass
    except Exception as e:
        print(f"[CACHE] Error clearing cache: {e}")