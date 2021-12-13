import unittest
import numpy
import os
from unittest.mock import (Mock, patch)
from app.parser.factory import ParserFactory
from app.parser.common import AbstractParser
from app.image.color_format import (PixelFormat, PixelPlane)
from enum import Enum


class TestParserFactoryClass(unittest.TestCase):

    def setUp(self):
        self.color_format_packed = Mock()
        self.color_format_packed.pixel_format = PixelFormat.RGBA
        self.color_format_packed.pixel_plane = PixelPlane.PACKED

        self.color_format_semiplanar = Mock()
        self.color_format_semiplanar.pixel_format = PixelFormat.YUV
        self.color_format_semiplanar.pixel_plane = PixelPlane.SEMIPLANAR

        self.color_format_dummy = Mock()
        self.color_format_dummy.pixel_format = PixelFormat.CUSTOM
        self.color_format_dummy.pixel_plane = PixelPlane.SEMIPLANAR

    def test_create_object(self):
        self.assertTrue(
            isinstance(ParserFactory.create_object(self.color_format_packed),
                       AbstractParser))
        self.assertTrue(
            ParserFactory.create_object(self.color_format_semiplanar)
            is not None)

        with self.assertRaises(NotImplementedError):
            ParserFactory.create_object(self.color_format_dummy)


if __name__ == "__main__":
    unittest.main()
