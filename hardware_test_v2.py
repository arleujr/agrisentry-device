"""AgriSentry hardware diagnostic v2 for ESP32/MicroPython."""

from machine import I2C, Pin
import sys
import time

DHT_PIN = 27
SDA_PIN = 21
SCL_PIN = 22
I2C_FREQ = 100_000

BH1750_LOW = 0x23
BH1750_HIGH = 0x5C
OLED_CANDIDATES = (0x3C, 0x3D)


def log(message=""):
    print(message)
    try:
        sys.stdout.flush()
    except Exception:
        pass


def read_dht11():
    log("")
    log("[1/4] DHT11 on GPIO27")

    try:
        import dht
        sensor = dht.DHT11(Pin(DHT_PIN, Pin.IN, Pin.PULL_UP))
    except Exception as error:
        log("[FAIL] DHT11 init: {}".format(repr(error)))
        return None

    for attempt in range(1, 6):
        try:
            time.sleep_ms(2500)
            sensor.measure()
            temperature = sensor.temperature()
            humidity = sensor.humidity()
            log("[PASS] DHT11 attempt {}".format(attempt))
            log("       temperature={} C humidity={} %".format(
                temperature,
                humidity,
            ))
            return temperature, humidity
        except Exception as error:
            log("[WARN] DHT11 attempt {}: {}".format(
                attempt,
                repr(error),
            ))

    log("[FAIL] DHT11 did not respond after 5 attempts")
    return None


def start_i2c():
    log("")
    log("[2/4] I2C bus SDA21 / SCL22")

    try:
        bus = I2C(
            0,
            scl=Pin(SCL_PIN),
            sda=Pin(SDA_PIN),
            freq=I2C_FREQ,
        )
    except Exception as error:
        log("[FAIL] I2C init: {}".format(repr(error)))
        return None, []

    addresses = []

    for attempt in range(1, 4):
        try:
            time.sleep_ms(250)
            addresses = bus.scan()
            log("[INFO] I2C scan {}: {}".format(
                attempt,
                [hex(address) for address in addresses],
            ))

            if 0 < len(addresses) <= 20:
                break
        except Exception as error:
            log("[WARN] I2C scan {}: {}".format(
                attempt,
                repr(error),
            ))

    if not addresses:
        log("[FAIL] No I2C devices found")
    elif len(addresses) > 20:
        log("[FAIL] I2C bus unhealthy: too many addresses")
    else:
        log("[PASS] I2C bus is responding")

    return bus, addresses


def read_bh1750(bus, address):
    for attempt in range(1, 4):
        try:
            bus.writeto(address, b"\x01")
            time.sleep_ms(10)
            bus.writeto(address, b"\x10")
            time.sleep_ms(200)
            data = bus.readfrom(address, 2)
            raw = (data[0] << 8) | data[1]
            lux = raw / 1.2
            return round(lux, 2)
        except Exception as error:
            log("[WARN] BH1750 {} attempt {}: {}".format(
                hex(address),
                attempt,
                repr(error),
            ))
            time.sleep_ms(300)

    return None


def test_lux(bus, addresses):
    log("")
    log("[3/4] BH1750 light sensors")
    readings = {}

    if bus is None:
        log("[SKIP] I2C unavailable")
        return readings

    for address in (BH1750_LOW, BH1750_HIGH):
        if address not in addresses:
            log("[INFO] {} not found".format(hex(address)))
            continue

        lux = read_bh1750(bus, address)

        if lux is None:
            log("[FAIL] {} found but could not be read".format(
                hex(address),
            ))
        else:
            readings[address] = lux
            log("[PASS] {} = {} lux".format(
                hex(address),
                lux,
            ))

    return readings


def test_oled(bus, addresses, dht_result, lux_results):
    log("")
    log("[4/4] OLED SSD1306")

    if bus is None:
        log("[SKIP] I2C unavailable")
        return False

    oled_address = None
    for candidate in OLED_CANDIDATES:
        if candidate in addresses:
            oled_address = candidate
            break

    if oled_address is None:
        log("[FAIL] OLED not found at 0x3C or 0x3D")
        return False

    try:
        from ssd1306 import SSD1306_I2C
        oled = SSD1306_I2C(128, 32, bus, addr=oled_address)
        oled.fill(0)
        oled.text("AgriSentry", 0, 0)

        if dht_result is None:
            oled.text("DHT11: FAIL", 0, 10)
        else:
            temperature, humidity = dht_result
            oled.text(
                "T:{}C H:{}%".format(temperature, humidity),
                0,
                10,
            )

        # Mostrar os dois sensores de lux
        lux_low = lux_results.get(BH1750_LOW)
        lux_high = lux_results.get(BH1750_HIGH)

        if lux_low is not None and lux_high is not None:
            oled.text("L:{:.0f} R:{:.0f}".format(lux_low, lux_high), 0, 20)
        elif lux_low is not None:
            oled.text("Lux L:{:.1f}".format(lux_low), 0, 20)
        elif lux_high is not None:
            oled.text("Lux R:{:.1f}".format(lux_high), 0, 20)
        else:
            oled.text("Lux: FAIL", 0, 20)

        oled.show()
        log("[PASS] OLED {} updated".format(hex(oled_address)))
        return True
    except Exception as error:
        log("[FAIL] OLED: {}".format(repr(error)))
        return False


def main():
    log("AgriSentry hardware test v2")
    log("Do not move wires during the test")

    dht_result = read_dht11()
    bus, addresses = start_i2c()
    lux_results = test_lux(bus, addresses)
    oled_ok = test_oled(
        bus,
        addresses,
        dht_result,
        lux_results,
    )

    log("")
    log("=" * 44)
    log("SUMMARY")
    log("=" * 44)
    log("DHT11: {}".format(
        "PASS" if dht_result is not None else "FAIL"
    ))
    log("BH1750 0x23: {}".format(
        "PASS" if BH1750_LOW in lux_results else "FAIL/ABSENT"
    ))
    log("BH1750 0x5C: {}".format(
        "PASS" if BH1750_HIGH in lux_results else "FAIL/ABSENT"
    ))
    log("OLED: {}".format(
        "PASS" if oled_ok else "FAIL/ABSENT"
    ))
    log("Test finished")


main()
