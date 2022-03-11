import unittest
import numpy
import os
import raviewer.image.image as image
import raviewer.image.color_format as cf


class TestImageClass(unittest.TestCase):

    def setUp(self):
        self.TEST_FILE_BGR = os.path.join(os.path.dirname(__file__),
                                          "../resources/RGB24_1000_750")
        self.empty_img = image.Image(None)
        with open(self.TEST_FILE_BGR, "rb") as file:
            self.img = image.Image(file.read(), cf.AVAILABLE_FORMATS['RGB24'],
                                   numpy.zeros(720 * 1280 * 4), 1280, 720)

    def test_from_file(self):
        self.assertEqual(
            image.Image.from_file(self.TEST_FILE_BGR).data_buffer,
            self.img.data_buffer)
        with self.assertRaises(Exception):
            image.Image.from_file("not_real_path")

    def test_height_width(self):
        self.assertEqual(self.img.width, 1280)
        self.assertEqual(self.img.height, 720)
        self.assertEqual(self.empty_img.width, None)
        self.assertEqual(self.empty_img.height, None)


if __name__ == "__main__":
    unittest.main()
