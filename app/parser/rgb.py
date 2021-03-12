"""Parser implementation for RGBA pixel format"""

from ..image.color_format import PixelFormat
from ..image.image import Image
from .common import AbstractParser

import numpy


class ParserRGBA(AbstractParser):
    """An RGB/BGR implementation of a parser - ALPHA LAST"""
    def get_displayable(self, image):
        """Provides displayable image data (RGB formatted)

        Returns: Numpy array containing displayable data.
        """

        return_data = numpy.reshape(image.processed_data.astype('float64'),
                                    (image.height, image.width, 4))

        bpcs = 4
        if image.color_format.bits_per_components[3] == 0:
            return_data[:, :, 3] = 255
            bpcs = 3

        for i in range(bpcs):
            return_data[:, :, i] = (255 * return_data[:, :, i]) / (
                2**image.color_format.bits_per_components[i] - 1)

        if image.color_format.pixel_format == PixelFormat.BGRA:
            return_data = return_data[:, :, [2, 1, 0, 3]]
        return return_data.astype('uint8')


class ParserARGB(AbstractParser):
    """An RGB/BGR implementation of a parser - ALPHA FIRST"""
    def parse(self, raw_data, color_format, width):
        """Parses provided raw data to an image, calculating height from provided width.

        Keyword arguments:

            raw_data: bytes object
            color_format: target instance of ColorFormat
            width: target width to interpret

        Returns: instance of Image processed to chosen format
        """

        max_value = max(color_format.bits_per_components)
        curr_dtype = None
        if max_value <= 8:
            curr_dtype = numpy.uint8
        else:
            curr_dtype = numpy.uint16

        data_array = []
        temp_set = set(color_format.bits_per_components)

        if (len(temp_set) == 1 or len(temp_set) == 2
                and not temp_set.add(0)) and max_value % 8 == 0:
            raw_data = bytearray(raw_data)
            if len(raw_data) % numpy.dtype(curr_dtype).alignment != 0:
                raw_data += (0).to_bytes(len(raw_data) %
                                         numpy.dtype(curr_dtype).alignment,
                                         byteorder="little")
            temp = numpy.frombuffer(raw_data, dtype=curr_dtype)
            data_array = temp
            if len(temp_set) == 2:
                if (temp.size % (width * 3) != 0):
                    temp = numpy.concatenate(
                        (temp,
                         numpy.zeros((width * 3) - (temp.size % (width * 3)))))
                temp = numpy.concatenate(
                    (numpy.full((int(temp.size / (width * 3)), width, 1),
                                (2**color_format.bits_per_components[0] - 1),
                                dtype=curr_dtype),
                     numpy.reshape(temp,
                                   (int(temp.size / (width * 3)), width, 3))),
                    axis=2)
                data_array = numpy.reshape(temp, temp.size)
        else:
            data_array = self._parse_not_bytefilled(raw_data, color_format)

        processed_data = numpy.array(data_array, dtype=curr_dtype)
        if (processed_data.size % (width * 4) != 0):
            processed_data = numpy.concatenate(
                (processed_data,
                 numpy.zeros((width * 4) - (processed_data.size %
                                            (width * 4)))))
        return Image(raw_data, color_format, processed_data, width,
                     processed_data.size // (width * 4))

    def get_displayable(self, image):
        """Provides displayable image data (RGB formatted)

        Returns: Numpy array containing displayable data.
        """

        return_data = numpy.reshape(image.processed_data.astype('float64'),
                                    (image.height, image.width, 4))

        for i in range(4):
            return_data[:, :, i] = (255 * return_data[:, :, i]) / (
                2**image.color_format.bits_per_components[i] - 1)

        if image.color_format.pixel_format == PixelFormat.ABGR:
            return_data = return_data[:, :, [3, 2, 1, 0]]
        else:
            return_data = return_data[:, :, [1, 2, 3, 0]]

        return return_data.astype('uint8')