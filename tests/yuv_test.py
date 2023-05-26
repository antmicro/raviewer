import unittest
import numpy
import os
from unittest.mock import (Mock, patch)
from raviewer.parser.yuv import ParserYUV420, ParserYUV422, ParserYUV420Planar, ParserYUV422Planar
from enum import Enum


class DummyPixelFormat(Enum):
    YUV = 1
    YVU = 2
    UYVY = 3
    YUYV = 4


class DummyEndianness(Enum):
    LITTLE_ENDIAN = 1
    BIG_ENDIAN = 2


class DummyPixelPlane(Enum):
    PACKED = 1
    SEMIPLANAR = 2
    PLANAR = 3


class TestYUVParserClass(unittest.TestCase):

    def setUp(self):

        #YUV420 Parser
        self.Y420_FORMAT = Mock(pixel_format=DummyPixelFormat.YUV,
                                endianness=DummyEndianness.BIG_ENDIAN,
                                pixel_plane=DummyPixelPlane.SEMIPLANAR)
        self.Y420_FORMAT.bits_per_components = (8, 8, 8, 0)
        self.Y420_IMAGE = Mock(color_format=self.Y420_FORMAT,
                               width=2,
                               height=2)
        self.Y420_IMAGE.processed_data = numpy.array([255, 255, 0, 0, 255, 0],
                                                     dtype=numpy.uint8)
        self.raw_data_Y420 = bytes((255, 255, 0, 0, 255, 0))
        self.Y420_IMAGE.data_buffer = self.raw_data_Y420

        self.parserY420 = ParserYUV420()

        #YUV422 Parser
        self.Y422_FORMAT = Mock(pixel_format=DummyPixelFormat.UYVY,
                                endianness=DummyEndianness.BIG_ENDIAN,
                                pixel_plane=DummyPixelPlane.PACKED)
        self.Y422_FORMAT.bits_per_components = (8, 8, 8, 8)

        self.Y422_IMAGE = Mock(color_format=self.Y422_FORMAT,
                               width=2,
                               height=2)
        self.Y422_IMAGE.processed_data = numpy.array(
            [255, 255, 0, 255, 0, 0, 255, 0], dtype=numpy.uint8)
        self.raw_data_Y422 = bytes((255, 255, 0, 255, 0, 0, 255, 0))
        self.Y422_IMAGE.data_buffer = self.raw_data_Y422

        self.parserY422 = ParserYUV422()

    @patch("raviewer.parser.common.Endianness", DummyEndianness)
    @patch("raviewer.parser.yuv.PixelFormat", DummyPixelFormat)
    def test_parse_Y420(self):

        parsed_img = self.parserY420.parse(self.raw_data_Y420,
                                           self.Y420_FORMAT, 2)

        self.assertEqual(parsed_img.data_buffer, self.Y420_IMAGE.data_buffer)
        self.assertEqual(parsed_img.width, self.Y420_IMAGE.width)
        self.assertEqual(parsed_img.height, self.Y420_IMAGE.height)
        self.assertEqual(parsed_img.color_format, self.Y420_IMAGE.color_format)
        self.assertTrue((
            parsed_img.processed_data == self.Y420_IMAGE.processed_data).all())

    @patch("raviewer.parser.common.Endianness", DummyEndianness)
    @patch("raviewer.parser.yuv.PixelFormat", DummyPixelFormat)
    def test_parse_Y422(self):
        parsed_img = self.parserY422.parse(self.raw_data_Y422,
                                           self.Y422_FORMAT, 2)

        self.assertEqual(parsed_img.data_buffer, self.Y422_IMAGE.data_buffer)
        self.assertEqual(parsed_img.width, self.Y422_IMAGE.width)
        self.assertEqual(parsed_img.height, self.Y422_IMAGE.height)
        self.assertEqual(parsed_img.color_format, self.Y422_IMAGE.color_format)
        self.assertTrue((
            parsed_img.processed_data == self.Y422_IMAGE.processed_data).all())

    @patch("raviewer.parser.yuv.PixelFormat", DummyPixelFormat)
    def test_get_displayable_Y420(self):

        displayable = self.parserY420.get_displayable(self.Y420_IMAGE)
        self.assertEqual(displayable.shape,
                         (self.Y420_IMAGE.height, self.Y420_IMAGE.width, 3))
        self.assertTrue((displayable == numpy.array([[[74, 255, 255],
                                                      [74, 255, 255]],
                                                     [[0, 54, 255],
                                                      [0, 54, 255]]])).all())

    @patch("raviewer.parser.yuv.PixelFormat", DummyPixelFormat)
    @patch(
        "raviewer.parser.yuv.ParserYUV422.yuv_442_offsets", {
            DummyPixelFormat.UYVY: {
                "Y": 1,
                "U": 0,
                "V": 2,
            },
            DummyPixelFormat.YUYV: {
                "Y": 0,
                "U": 1,
                "V": 3,
            },
        })
    def test_get_displayable_Y422(self):

        displayable = self.parserY422.get_displayable(self.Y422_IMAGE)
        self.assertEqual(displayable.shape,
                         (self.Y422_IMAGE.height, self.Y422_IMAGE.width, 3))
        print(displayable)
        self.assertTrue((displayable == numpy.array([[[74, 255, 255],
                                                      [74, 255, 255]],
                                                     [[203, 0, 0],
                                                      [203, 0, 0]]])).all())


class TestYUVPlanarParserClass(unittest.TestCase):

    def setUp(self):

        #YUV420 Parser
        self.Y420_FORMAT = Mock(pixel_format=DummyPixelFormat.YUV,
                                endianness=DummyEndianness.BIG_ENDIAN,
                                pixel_plane=DummyPixelPlane.PLANAR)
        self.Y420_FORMAT.bits_per_components = (8, 8, 8, 0)
        self.Y420_IMAGE = Mock(color_format=self.Y420_FORMAT,
                               width=2,
                               height=2)
        self.Y420_IMAGE.processed_data = numpy.array([255, 255, 0, 0, 255, 0],
                                                     dtype=numpy.uint8)
        self.raw_data_Y420 = bytes((255, 255, 0, 0, 255, 0))
        self.Y420_IMAGE.data_buffer = self.raw_data_Y420

        self.parserY420 = ParserYUV420Planar()

        #YUV422 Parser
        self.Y422_FORMAT = Mock(pixel_format=DummyPixelFormat.YUV,
                                endianness=DummyEndianness.BIG_ENDIAN,
                                pixel_plane=DummyPixelPlane.PLANAR)
        self.Y422_FORMAT.bits_per_components = (8, 8, 8, 0)

        self.Y422_IMAGE = Mock(color_format=self.Y422_FORMAT,
                               width=2,
                               height=2)
        self.Y422_IMAGE.processed_data = numpy.array(
            [255, 255, 0, 0, 255, 0, 0, 255], dtype=numpy.uint8)
        self.raw_data_Y422 = bytes((255, 255, 0, 0, 255, 0, 0, 255))
        self.Y422_IMAGE.data_buffer = self.raw_data_Y422
        self.parserY422 = ParserYUV422Planar()

    @patch("raviewer.parser.common.Endianness", DummyEndianness)
    @patch("raviewer.parser.yuv.PixelFormat", DummyPixelFormat)
    def test_parse_Y420(self):

        parsed_img = self.parserY420.parse(self.raw_data_Y420,
                                           self.Y420_FORMAT, 2)

        self.assertEqual(parsed_img.data_buffer, self.Y420_IMAGE.data_buffer)
        self.assertEqual(parsed_img.width, self.Y420_IMAGE.width)
        self.assertEqual(parsed_img.height, self.Y420_IMAGE.height)
        self.assertEqual(parsed_img.color_format, self.Y420_IMAGE.color_format)
        self.assertTrue((
            parsed_img.processed_data == self.Y420_IMAGE.processed_data).all())

    @patch("raviewer.parser.common.Endianness", DummyEndianness)
    @patch("raviewer.parser.yuv.PixelFormat", DummyPixelFormat)
    def test_parse_Y422(self):
        parsed_img = self.parserY422.parse(self.raw_data_Y422,
                                           self.Y422_FORMAT, 2)

        self.assertEqual(parsed_img.data_buffer, self.Y422_IMAGE.data_buffer)
        self.assertEqual(parsed_img.width, self.Y422_IMAGE.width)
        self.assertEqual(parsed_img.height, self.Y422_IMAGE.height)
        self.assertEqual(parsed_img.color_format, self.Y422_IMAGE.color_format)
        self.assertTrue((
            parsed_img.processed_data == self.Y422_IMAGE.processed_data).all())

    @patch("raviewer.parser.yuv.PixelFormat", DummyPixelFormat)
    def test_get_displayable_Y420(self):

        displayable = self.parserY420.get_displayable(self.Y420_IMAGE,
                                                      self.Y420_IMAGE.height)
        self.assertEqual(displayable.shape,
                         (self.Y420_IMAGE.height, self.Y420_IMAGE.width, 3))
        print(displayable)
        self.assertTrue((displayable == numpy.array([[[74, 255, 255],
                                                      [74, 255, 255]],
                                                     [[0, 54, 255],
                                                      [0, 54, 255]]])).all())

    @patch("raviewer.parser.yuv.PixelFormat", DummyPixelFormat)
    def test_get_displayable_Y422(self):

        displayable = self.parserY422.get_displayable(self.Y422_IMAGE,
                                                      self.Y422_IMAGE.height)
        self.assertEqual(displayable.shape,
                         (self.Y422_IMAGE.height, self.Y422_IMAGE.width, 3))
        print(displayable)
        self.assertTrue((displayable == numpy.array([[[74, 255, 255],
                                                      [74, 255, 255]],
                                                     [[203, 0, 0],
                                                      [203, 0, 0]]])).all())


if __name__ == "__main__":
    unittest.main()
