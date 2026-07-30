import unittest

from physical_sensors import relative_light_percent


class RelativeLightPercentTests(unittest.TestCase):
    def test_converts_half_scale(self):
        self.assertEqual(relative_light_percent(10_000, 20_000), 50.0)

    def test_clamps_negative_value(self):
        self.assertEqual(relative_light_percent(-1, 20_000), 0.0)

    def test_clamps_above_full_scale(self):
        self.assertEqual(relative_light_percent(25_000, 20_000), 100.0)

    def test_rejects_invalid_full_scale(self):
        with self.assertRaises(ValueError):
            relative_light_percent(100, 0)


if __name__ == "__main__":
    unittest.main()
