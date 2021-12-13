import unittest
import app.image.color_format as cf


class TestColorFormat(unittest.TestCase):

    def setUp(self):
        self.color_format = cf.ColorFormat(cf.PixelFormat.RGBA,
                                           cf.Endianness.BIG_ENDIAN,
                                           cf.PixelPlane.PACKED,
                                           8,
                                           8,
                                           8,
                                           name="RGB24")

    def test_bpcs_setter(self):
        self.color_format.bits_per_components = (8, 8, 8, 0)
        self.assertEqual(self.color_format.bits_per_components, (8, 8, 8, 0))
        self.color_format.bits_per_components = (8, 8, 8)
        self.assertEqual(self.color_format.bits_per_components, (8, 8, 8, 0))
        with self.assertRaises(ValueError):
            self.color_format.bits_per_components = (8, 8, 8, 8, 8)
        with self.assertRaises(ValueError):
            self.color_format.bits_per_components = 1


if __name__ == "__main__":
    unittest.main()
