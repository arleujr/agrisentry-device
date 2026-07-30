"""Local SSD1306 OLED output for the physical firmware slice."""


class OledDisplay:
    """Render the latest environmental readings without affecting telemetry."""

    def __init__(self, i2c):
        import config

        self._oled = None
        address = getattr(config, "OLED_ADDRESS", 0x3C)

        try:
            if address not in i2c.scan():
                print("[DISPLAY] OLED %s not found" % hex(address))
                return

            from ssd1306 import SSD1306_I2C

            self._oled = SSD1306_I2C(
                getattr(config, "OLED_WIDTH", 128),
                getattr(config, "OLED_HEIGHT", 32),
                i2c,
                addr=address,
            )
            print("[DISPLAY] OLED ready at %s" % hex(address))
        except Exception as error:
            print("[DISPLAY] OLED initialization failed:", error)

    @staticmethod
    def _number(value, decimals=0):
        if value is None:
            return "--"

        if decimals == 0:
            return str(int(round(value)))

        return ("%." + str(decimals) + "f") % value

    def show(self, snapshot, status):
        """Display readings and connectivity status; never raise to the caller."""
        if self._oled is None:
            return

        try:
            temperature = self._number(snapshot.get("temperature_c"))
            humidity = self._number(snapshot.get("humidity_pct"))
            primary_lux = self._number(snapshot.get("light_primary_lux"))
            secondary_lux = self._number(snapshot.get("light_secondary_lux"))

            self._oled.fill(0)
            self._oled.text("AgriSentry PHY", 0, 0)
            self._oled.text("T:%sC H:%s%%" % (temperature, humidity), 0, 8)
            self._oled.text("A:%s B:%s lx" % (primary_lux, secondary_lux), 0, 16)
            self._oled.text("MQTT:%s" % status[:10], 0, 24)
            self._oled.show()
        except Exception as error:
            print("[DISPLAY] Update failed:", error)
