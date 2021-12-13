from app.parser.bayer import ParserBayerRG
import unittest
import numpy
from unittest.mock import (Mock, patch)
from enum import Enum


class DummyPixelFormat(Enum):
    Bayer_RG = 1


class DummyEndianness(Enum):
    LITTLE_ENDIAN = 1
    BIG_ENDIAN = 2


class DummyPixelPlane(Enum):
    PACKED = 1


class TestBayerParserClass(unittest.TestCase):

    def setUp(self):

        self.RGGB_FORMAT = Mock(pixel_format=DummyPixelFormat.Bayer_RG,
                                endianness=DummyEndianness.BIG_ENDIAN,
                                pixel_plane=DummyPixelPlane.PACKED)
        self.RGGB_FORMAT.bits_per_components = (8, 8, 8, 0)

        self.RGGB_IMAGE = Mock(color_format=self.RGGB_FORMAT,
                               width=2,
                               height=2)
        self.RGGB_IMAGE.processed_data = numpy.array([0, 255, 255, 255])

        self.raw_data = bytes((0, 255, 255, 255))

        self.RGGB_IMAGE.data_buffer = self.raw_data

        self.parser = ParserBayerRG()

    def test_parse(self):

        parsed_img = self.parser.parse(self.raw_data, self.RGGB_FORMAT, 2)

        self.assertEqual(parsed_img.data_buffer, self.RGGB_IMAGE.data_buffer)
        self.assertEqual(parsed_img.width, self.RGGB_IMAGE.width)
        self.assertEqual(parsed_img.height, self.RGGB_IMAGE.height)
        self.assertEqual(parsed_img.color_format, self.RGGB_IMAGE.color_format)
        self.assertTrue((
            parsed_img.processed_data == self.RGGB_IMAGE.processed_data).all())

    def test_get_displayable(self):
        """
        Too complicated algorithm.
        """
        pass
