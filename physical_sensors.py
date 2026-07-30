"""Physical environmental sensor support for the ESP32.

This module keeps hardware imports inside ``PhysicalSensors`` so the
conversion helper can also be tested on a regular Python interpreter.
"""

import time

from telemetry import make_reading


BH1750_POWER_ON = b"\x01"
BH1750_CONTINUOUS_HIGH_RES = b"\x10"


def relative_light_percent(lux, full_scale_lux):
    """Convert illuminance to the temporary MQTT v1 relative-light scale."""
    if not isinstance(lux, (int, float)):
        raise TypeError("lux must be numeric")
    if not isinstance(full_scale_lux, (int, float)) or full_scale_lux <= 0:
        raise ValueError("full_scale_lux must be greater than zero")

    percentage = (max(0.0, float(lux)) / float(full_scale_lux)) * 100.0
    return round(min(100.0, percentage), 2)


class PhysicalSensors:
    """Read the DHT11 and two BH1750 sensors on the shared I2C bus."""

    def __init__(self):
        import config
        import dht
        from machine import I2C, Pin

        self._config = config
        self._dht = dht.DHT11(
            Pin(
                getattr(config, "DHT_PIN", 27),
                Pin.IN,
                Pin.PULL_UP,
            )
        )

        self.i2c = I2C(
            getattr(config, "I2C_BUS_ID", 0),
            scl=Pin(getattr(config, "I2C_SCL_PIN", 22)),
            sda=Pin(getattr(config, "I2C_SDA_PIN", 21)),
            freq=getattr(config, "I2C_FREQUENCY_HZ", 100_000),
        )
        self.addresses = self.i2c.scan()
        self.light_primary_address = getattr(config, "BH1750_PRIMARY_ADDRESS", 0x23)
        self.light_secondary_address = getattr(config, "BH1750_SECONDARY_ADDRESS", 0x5C)

        print(
            "[SENSORS] I2C devices:",
            [hex(address) for address in self.addresses],
        )

    def _read_dht11(self):
        last_error = None

        for attempt in range(1, 4):
            try:
                if attempt > 1:
                    time.sleep_ms(1200)

                self._dht.measure()
                temperature = float(self._dht.temperature())
                humidity = float(self._dht.humidity())
                return temperature, humidity
            except Exception as error:
                last_error = error
                print(
                    "[SENSORS] DHT11 attempt %s/3 failed: %s"
                    % (attempt, error)
                )

        raise RuntimeError("DHT11 read failed: %s" % last_error)

    def _read_bh1750(self, address):
        if address not in self.addresses:
            raise RuntimeError("BH1750 %s is absent" % hex(address))

        last_error = None

        for attempt in range(1, 4):
            try:
                self.i2c.writeto(address, BH1750_POWER_ON)
                time.sleep_ms(10)
                self.i2c.writeto(address, BH1750_CONTINUOUS_HIGH_RES)
                time.sleep_ms(200)

                data = self.i2c.readfrom(address, 2)
                raw = (data[0] << 8) | data[1]
                lux = raw / 1.2
                return raw, round(lux, 2)
            except Exception as error:
                last_error = error
                print(
                    "[SENSORS] BH1750 %s attempt %s/3 failed: %s"
                    % (hex(address), attempt, error)
                )
                time.sleep_ms(300)

        raise RuntimeError(
            "BH1750 %s read failed: %s" % (hex(address), last_error)
        )

    def read_all(self):
        """Return MQTT v1 readings and a display-friendly snapshot."""
        readings = []
        snapshot = {
            "temperature_c": None,
            "humidity_pct": None,
            "light_primary_lux": None,
            "light_secondary_lux": None,
            "errors": [],
        }

        try:
            temperature, humidity = self._read_dht11()
            snapshot["temperature_c"] = temperature
            snapshot["humidity_pct"] = humidity

            temperature_quality = (
                "valid" if -40.0 <= temperature <= 80.0 else "out_of_range"
            )
            humidity_quality = (
                "valid" if 0.0 <= humidity <= 100.0 else "out_of_range"
            )

            readings.append(
                make_reading(
                    "air_temperature",
                    temperature,
                    temperature,
                    temperature_quality,
                )
            )
            readings.append(
                make_reading(
                    "air_relative_humidity",
                    humidity,
                    humidity,
                    humidity_quality,
                )
            )
        except Exception as error:
            snapshot["errors"].append("DHT11: %s" % error)
            print("[SENSORS] DHT11 unavailable:", error)

        lux_values = []

        for snapshot_key, address in (
            ("light_primary_lux", self.light_primary_address),
            ("light_secondary_lux", self.light_secondary_address),
        ):
            try:
                _raw, lux = self._read_bh1750(address)
                snapshot[snapshot_key] = lux
                lux_values.append(lux)
            except Exception as error:
                snapshot["errors"].append(
                    "BH1750 %s: %s" % (hex(address), error)
                )
                print("[SENSORS] BH1750 unavailable:", error)

        if lux_values:
            average_lux = round(sum(lux_values) / len(lux_values), 2)
            full_scale_lux = getattr(
                self._config,
                "RELATIVE_LIGHT_FULL_SCALE_LUX",
                20_000.0,
            )
            relative_light = relative_light_percent(
                average_lux,
                full_scale_lux,
            )
            readings.append(
                make_reading(
                    "relative_light",
                    average_lux,
                    relative_light,
                    "estimated",
                    "bh1750-average-relative-v1",
                )
            )

        if not readings:
            raise RuntimeError("No physical sensor produced a reading")

        return readings, snapshot
