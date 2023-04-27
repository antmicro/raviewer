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
    def get_displayable(self, image):
        """Provides displayable image data (RGB formatted)
        
        Keyword arguments:

            image: processed image object

        Returns: Numpy array containing displayable data.
        """
        pass

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

    def parse(self, raw_data, color_format, width, reverse_bytes=0):
        """Parses provided raw data to an image, calculating height from provided width.

        Keyword arguments:

            raw_data: bytes object
            color_format: target instance of ColorFormat
            width: target width to interpret

        Returns: instance of Image processed to chosen format
        """
        max_value = max(color_format.bits_per_components)
        curr_dtype = self.get_dtype(max_value, color_format.endianness)

        temp_set = set(color_format.bits_per_components)

        raw_data = bytearray(raw_data)
        if (len(temp_set) == 1 or len(temp_set) == 2
                and not temp_set.add(0)) and max_value % 8 == 0:
            if len(raw_data) % numpy.dtype(curr_dtype).alignment != 0:
                raw_data += (0).to_bytes(len(raw_data) %
                                         numpy.dtype(curr_dtype).alignment,
                                         byteorder="little")
            temp_raw_data = self.reverse(raw_data, reverse_bytes)
            temp = numpy.frombuffer(temp_raw_data, curr_dtype)
            processed_data = temp
            if len(temp_set) == 2:
                if (temp.size % (width * 3) != 0):
                    temp = numpy.concatenate(
                        (temp,
                         numpy.zeros((width * 3) - (temp.size % (width * 3)),
                                     dtype=curr_dtype)))

                temp = cv.cvtColor(
                    numpy.reshape(temp,
                                  (int(temp.size / (3 * width)), width, 3)),
                    cv.COLOR_RGB2RGBA)
                processed_data = numpy.reshape(temp, temp.size)
        else:
            temp_raw_data = self.reverse(raw_data, reverse_bytes)
            processed_data = self._parse_not_bytefilled(
                temp_raw_data, color_format)

        if (processed_data.size % (width * 4) != 0):
            processed_data = numpy.concatenate(
                (processed_data,
                 numpy.zeros((width * 4) - (processed_data.size %
                                            (width * 4)))))
        return Image(raw_data, color_format, processed_data, width,
                     processed_data.size // (width * 4))

    def _parse_not_bytefilled(self, raw_data, color_format):
        """Parses provided raw data to an image - bits per component are not multiple of 8.

        Keyword arguments:

            raw_data: bytes object
            color_format: target instance of ColorFormat

        Returns: properly parsed buffer data (numpy ndarray)
        """
        pixel_size = sum(color_format.bits_per_components)
        if pixel_size & 7 != 0:
            raise Exception("Invalid pixel format")
        curr_dtype = self.get_dtype(pixel_size, color_format.endianness)
        if len(raw_data) % (pixel_size // 8) != 0:
            raw_data += b'\x00' * (pixel_size // 8 - (len(raw_data) %
                                                      (pixel_size // 8)))
        processed_data = numpy.frombuffer(raw_data, dtype=curr_dtype)
        temp = pixel_size
        res = numpy.empty((4 * len(processed_data), ), dtype=curr_dtype)
        for j, i in enumerate(color_format.bits_per_components):
            mask = (1 << i) - 1
            mask <<= temp - i
            temp -= i
            channel = numpy.bitwise_and(processed_data, mask)
            numpy.right_shift(channel, temp, out=res[j::4])
        return res
