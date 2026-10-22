"""Unit tests for media inspector parsing helpers."""

import unittest
from src.core.inspector import _parse_fraction


class TestInspector(unittest.TestCase):

    def test_parse_fraction(self):
        # NTSC telecine 23.976 fps
        ntsc = _parse_fraction("24000/1001")
        self.assertAlmostEqual(ntsc, 23.976023976, places=5)

        # Standard 24 fps
        p24 = _parse_fraction("24/1")
        self.assertEqual(p24, 24.0)

        # PAL 25 fps
        pal = _parse_fraction("25/1")
        self.assertEqual(pal, 25.0)

        # NTSC 29.97 fps
        ntsc30 = _parse_fraction("30000/1001")
        self.assertAlmostEqual(ntsc30, 29.97002997, places=5)

        # Floating string
        flt = _parse_fraction("23.976")
        self.assertAlmostEqual(flt, 23.976, places=3)

        # Invalid cases
        self.assertEqual(_parse_fraction("0/0"), 0.0)
        self.assertEqual(_parse_fraction(""), 0.0)
        self.assertEqual(_parse_fraction("invalid/data"), 0.0)


if __name__ == "__main__":
    unittest.main()
