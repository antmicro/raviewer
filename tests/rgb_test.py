import unittest
import numpy
import os
from unittest.mock import (Mock, patch)
from raviewer.parser.rgb import ParserARGB, ParserRGBA, ParserBGRA, ParserABGR, ParserRGB, ParserBGR
from enum import Enum


class DummyPixelFormat(Enum):
    RGBA = 1
    BGRA = 2
    ARGB = 3
    ABGR = 4
    RGB = 5
    BGR = 6


class DummyEndianness(Enum):
    LITTLE_ENDIAN = 1
    BIG_ENDIAN = 2


class DummyPixelPlane(Enum):
    PACKED = 1


class TestRGBParserClass(unittest.TestCase):

    def setUp(self):

        self.RGB565_FORMAT = Mock(pixel_format=DummyPixelFormat.RGB,
                                  endianness=DummyEndianness.LITTLE_ENDIAN,
                                  pixel_plane=DummyPixelPlane.PACKED)
        self.RGB565_FORMAT.bits_per_components = (5, 6, 5, 0)

        self.BGR24_FORMAT = Mock(pixel_format=DummyPixelFormat.BGR,
                                 endianness=DummyEndianness.BIG_ENDIAN,
                                 pixel_plane=DummyPixelPlane.PACKED)
        self.BGR24_FORMAT.bits_per_components = (8, 8, 8, 0)

        self.RGB565_IMAGE = Mock(color_format=self.RGB565_FORMAT,
                                 width=2,
                                 height=1)
        self.RGB565_IMAGE.processed_data = numpy.array([0, 0, 0, 31, 63, 31])

        self.raw_data = bytes((0, 0, 255, 255))

        self.RGB565_IMAGE.data_buffer = self.raw_data

        self.BGR24_IMAGE = Mock(color_format=self.BGR24_FORMAT,
                                width=2,
                                height=1)
        self.BGR24_IMAGE.processed_data = numpy.array([0, 0, 255, 255, 0, 0])
        self.BGR24_IMAGE.data_buffer = self.raw_data

        self.parserRGB = ParserRGB()
        self.parserBGR = ParserBGR()

    @patch("raviewer.parser.common.Endianness", DummyEndianness)
    @patch("raviewer.parser.rgb.PixelFormat", DummyPixelFormat)
    def test_parse(self):

        parsed_img = self.parserRGB.parse(self.raw_data, self.RGB565_FORMAT, 2)

        self.assertEqual(parsed_img.data_buffer, self.RGB565_IMAGE.data_buffer)
        self.assertEqual(parsed_img.width, self.RGB565_IMAGE.width)
        self.assertEqual(parsed_img.height, self.RGB565_IMAGE.height)
        self.assertEqual(parsed_img.color_format,
                         self.RGB565_IMAGE.color_format)
        self.assertTrue(
            (parsed_img.processed_data == self.RGB565_IMAGE.processed_data
             ).all())

        parsed_img = self.parserRGB.parse(self.raw_data, self.BGR24_FORMAT, 2)

        self.assertEqual(parsed_img.data_buffer, self.BGR24_IMAGE.data_buffer)
        self.assertEqual(parsed_img.width, self.BGR24_IMAGE.width)
        self.assertEqual(parsed_img.height, self.BGR24_IMAGE.height)
        self.assertEqual(parsed_img.color_format,
                         self.BGR24_IMAGE.color_format)

        self.assertTrue(
            (parsed_img.processed_data == self.BGR24_IMAGE.processed_data
             ).all())

    @patch("raviewer.parser.rgb.PixelFormat", DummyPixelFormat)
    def test_get_displayable(self):
        displayable = self.parserRGB.get_displayable(self.RGB565_IMAGE)
        self.assertEqual(
            displayable.shape,
            (self.RGB565_IMAGE.height, self.RGB565_IMAGE.width, 4))

        self.assertTrue((displayable == numpy.array([[[0, 0, 0, 255],
                                                      [255, 255, 255,
                                                       255]]])).all())

        displayable = self.parserBGR.get_displayable(self.BGR24_IMAGE)
        self.assertEqual(displayable.shape,
                         (self.BGR24_IMAGE.height, self.BGR24_IMAGE.width, 4))

        print(displayable)
        self.assertTrue((displayable == numpy.array([[[255, 0, 0, 255],
                                                      [0, 0, 255,
                                                       255]]])).all())


class TestARGBParserClass(unittest.TestCase):

    def setUp(self):

        self.ARGB444_FORMAT = Mock(pixel_format=DummyPixelFormat.ARGB,
                                   endianness=DummyEndianness.LITTLE_ENDIAN,
                                   pixel_plane=DummyPixelPlane.PACKED)
        self.ARGB444_FORMAT.bits_per_components = (4, 4, 4, 4)

        self.ABGR32_FORMAT = Mock(pixel_format=DummyPixelFormat.ABGR,
                                  endianness=DummyEndianness.BIG_ENDIAN,
                                  pixel_plane=DummyPixelPlane.PACKED)
        self.ABGR32_FORMAT.bits_per_components = (8, 8, 8, 8)

        self.ARGB444_IMAGE = Mock(color_format=self.ARGB444_FORMAT,
                                  width=2,
                                  height=1)
        self.ARGB444_IMAGE.processed_data = numpy.array(
            [0, 0, 0, 0, 15, 15, 15, 15])

        self.raw_data = bytes((0, 0, 255, 255))

        self.ARGB444_IMAGE.data_buffer = self.raw_data

        self.ABGR32_IMAGE = Mock(color_format=self.ABGR32_FORMAT,
                                 width=1,
                                 height=1)
        self.ABGR32_IMAGE.processed_data = numpy.array([0, 0, 255, 255])
        self.ABGR32_IMAGE.data_buffer = self.raw_data

        self.parserARGB = ParserARGB()
        self.parserABGR = ParserABGR()

    @patch("raviewer.parser.common.Endianness", DummyEndianness)
    @patch("raviewer.parser.rgb.PixelFormat", DummyPixelFormat)
    def test_parse(self):

        parsed_img = self.parserARGB.parse(self.raw_data, self.ARGB444_FORMAT,
                                           2)

        self.assertEqual(parsed_img.data_buffer,
                         self.ARGB444_IMAGE.data_buffer)
        self.assertEqual(parsed_img.width, self.ARGB444_IMAGE.width)
        self.assertEqual(parsed_img.height, self.ARGB444_IMAGE.height)
        self.assertEqual(parsed_img.color_format,
                         self.ARGB444_IMAGE.color_format)
        self.assertTrue(
            (parsed_img.processed_data == self.ARGB444_IMAGE.processed_data
             ).all())

        parsed_img = self.parserARGB.parse(self.raw_data, self.ABGR32_FORMAT,
                                           1)

        self.assertEqual(parsed_img.data_buffer, self.ABGR32_IMAGE.data_buffer)
        self.assertEqual(parsed_img.width, self.ABGR32_IMAGE.width)
        self.assertEqual(parsed_img.height, self.ABGR32_IMAGE.height)
        self.assertEqual(parsed_img.color_format,
                         self.ABGR32_IMAGE.color_format)

        self.assertTrue(
            (parsed_img.processed_data == self.ABGR32_IMAGE.processed_data
             ).all())

    @patch("raviewer.parser.rgb.PixelFormat", DummyPixelFormat)
    def test_get_displayable(self):

        displayable = self.parserARGB.get_displayable(self.ARGB444_IMAGE)
        self.assertEqual(
            displayable.shape,
            (self.ARGB444_IMAGE.height, self.ARGB444_IMAGE.width, 4))

        self.assertTrue((displayable == numpy.array([[[0, 0, 0, 0],
                                                      [255, 255, 255,
                                                       255]]])).all())

        displayable = self.parserABGR.get_displayable(self.ABGR32_IMAGE)
        self.assertEqual(
            displayable.shape,
            (self.ABGR32_IMAGE.height, self.ABGR32_IMAGE.width, 4))
        print(displayable)
        self.assertTrue((displayable == numpy.array([[[255, 255, 0,
                                                       0]]])).all())


if __name__ == "__main__":
    unittest.main()
