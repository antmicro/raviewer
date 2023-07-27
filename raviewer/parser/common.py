"""Support for parsing raw data."""

from abc import ABCMeta, abstractmethod
from ..image.image import Image
from ..image.color_format import Endianness
import numpy
import math
import cv2 as cv


class AbstractParser(metaclass=ABCMeta):
    """An abstract data parser"""

    @abstractmethod
    def get_displayable(self, image: Image):
        """Provides displayable image data (RGB formatted)
        
        Keyword arguments:

            image: processed image object

        Returns: Numpy array containing displayable data.
        """
        pass

    def raw_coloring(self, image, height=0):
        return None

    def get_dtype(self, max_value, endianness):
        if max_value <= 8:
            return '>u1' if endianness == Endianness.BIG_ENDIAN else '<u1'
        else:
            return '>u2' if endianness == Endianness.BIG_ENDIAN else '<u2'

    def reverse(self, raw_data, reverse_bytes):
        temp_raw_data = bytearray()
        if reverse_bytes > 1:
            for i in range(0, len(raw_data) + 1, reverse_bytes):
                temp_raw_data += raw_data[i:i + reverse_bytes][::-1]
            return temp_raw_data
        else:
            return raw_data

    @abstractmethod
    def parse(self, raw_data, color_format, width, reverse_bytes=0):
        """Parses provided raw data to an image, calculating height from provided width.

                Keyword arguments:

                    raw_data: bytes object
                    color_format: target instance of ColorFormat
                    width: target width to interpret

                Returns: instance of Image processed to chosen format
        """
        pass
