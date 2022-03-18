from raviewer.parser.grayscale import ParserGrayscale
import unittest
import numpy
from unittest.mock import (Mock, patch)
from enum import Enum


class DummyPixelFormat(Enum):
    MONO = 1


class DummyEndianness(Enum):
    LITTLE_ENDIAN = 1
    BIG_ENDIAN = 2


class DummyPixelPlane(Enum):
    PACKED = 1


class TestGrayscaleParserClass(unittest.TestCase):

    def setUp(self):

        self.GRAY_FORMAT = Mock(pixel_format=DummyPixelFormat.MONO,
                                endianness=DummyEndianness.BIG_ENDIAN,
                                pixel_plane=DummyPixelPlane.PACKED)
        self.GRAY_FORMAT.bits_per_components = (8, 0, 0, 0)

        self.GRAY12_FORMAT = Mock(pixel_format=DummyPixelFormat.MONO,
                                  endianness=DummyEndianness.BIG_ENDIAN,
                                  pixel_plane=DummyPixelPlane.PACKED)
        self.GRAY12_FORMAT.bits_per_components = (12, 0, 0, 0)

        self.GRAY_IMAGE = Mock(color_format=self.GRAY_FORMAT,
                               width=2,
                               height=1)
        self.GRAY_IMAGE.processed_data = numpy.array([0, 255])

        self.raw_data = bytes((0, 255))

        self.GRAY_IMAGE.data_buffer = self.raw_data

        self.GRAY12_IMAGE = Mock(color_format=self.GRAY12_FORMAT,
                                 width=1,
                                 height=1)
        self.GRAY12_IMAGE.processed_data = numpy.array([255])
        self.GRAY12_IMAGE.data_buffer = self.raw_data

        self.parser = ParserGrayscale()

    @patch("raviewer.parser.common.Endianness", DummyEndianness)
    def test_parse(self):

        parsed_img = self.parser.parse(self.raw_data, self.GRAY_FORMAT, 2)

        self.assertEqual(parsed_img.data_buffer, self.GRAY_IMAGE.data_buffer)
        self.assertEqual(parsed_img.width, self.GRAY_IMAGE.width)
        self.assertEqual(parsed_img.height, self.GRAY_IMAGE.height)
        self.assertEqual(parsed_img.color_format, self.GRAY_IMAGE.color_format)
        self.assertTrue((
            parsed_img.processed_data == self.GRAY_IMAGE.processed_data).all())

        parsed_img = self.parser.parse(self.raw_data, self.GRAY12_FORMAT, 1)

        self.assertEqual(parsed_img.data_buffer, self.GRAY12_IMAGE.data_buffer)
        self.assertEqual(parsed_img.width, self.GRAY12_IMAGE.width)
        self.assertEqual(parsed_img.height, self.GRAY12_IMAGE.height)
        self.assertEqual(parsed_img.color_format,
                         self.GRAY12_IMAGE.color_format)

        self.assertTrue(
            (parsed_img.processed_data == self.GRAY12_IMAGE.processed_data
             ).all())

    def test_get_displayable(self):

        displayable = self.parser.get_displayable(self.GRAY_IMAGE)
        self.assertEqual(displayable.shape,
                         (self.GRAY_IMAGE.height, self.GRAY_IMAGE.width, 3))

        self.assertTrue(
            (displayable == numpy.array([[[0, 0, 0], [255, 255, 255]]])).all())

        displayable = self.parser.get_displayable(self.GRAY12_IMAGE)
        self.assertEqual(
            displayable.shape,
            (self.GRAY12_IMAGE.height, self.GRAY12_IMAGE.width, 3))
        self.assertTrue((displayable == numpy.array([[[15, 15, 15]]])).all())
