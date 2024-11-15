"""Parser implementation for grayscale pixel format"""

from ..image.image import Image
from ..image.color_format import Endianness
from .common import AbstractParser
from ..src.utils import pad_modulo

import numpy
import cv2 as cv


class ParserGrayscale(AbstractParser):
    """A grayscale implementation of a parser"""

    def parse(self, raw_data, color_format, width, reverse_bytes=0):
        """Parses provided raw data to an image, calculating height from provided width.

        Keyword arguments:

            raw_data: bytes object
            color_format: target instance of ColorFormat
            width: target width to interpret

        Returns: instance of Image processed to chosen format
        """

        bits_per_gray = color_format.bits_per_components[0]
        curr_dtype = self.get_dtype(bits_per_gray, color_format.endianness)

        raw_data = bytearray(raw_data)
        if len(raw_data) % numpy.dtype(curr_dtype).alignment != 0:
            raw_data += (0).to_bytes(len(raw_data) %
                                     numpy.dtype(curr_dtype).alignment,
                                     byteorder="little")
        processed_data = numpy.frombuffer(self.reverse(raw_data,
                                                       reverse_bytes),
                                          dtype=curr_dtype)
        processed_data = pad_modulo(processed_data, (width, ))

        return Image(raw_data, color_format, processed_data, width,
                     processed_data.size // width)

    def get_displayable(self, image):
        """Provides displayable image data (RGB formatted)

        Returns: Numpy array containing displayable data.
        """
        return_data = image.processed_data

        data_array = numpy.reshape(return_data,
                                   (image.height, image.width)).astype('float')

        data_array[:] = 255 * (
            data_array[:] / (2**image.color_format.bits_per_components[0] - 1))

        return_data = cv.cvtColor(data_array.astype('uint8'),
                                  cv.COLOR_GRAY2RGB)
        return return_data

    def get_pixel_raw_components(self, image, row, column, index):
        return image.processed_data[index:index + 1]

    def crop_image2rawformat(self, img, up_row, down_row, left_column,
                             right_column):
        reshaped_image = numpy.reshape(img.processed_data.astype(numpy.byte),
                                       (img.height, img.width))
        truncated_image = reshaped_image[up_row:down_row,
                                         left_column:right_column]
        return truncated_image
