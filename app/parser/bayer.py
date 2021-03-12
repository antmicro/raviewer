"""Parser implementation for Bayer pixel format"""

from ..image.image import Image
from .common import AbstractParser

import numpy
import cv2 as cv


class ParserBayerRG(AbstractParser):
    """A Bayer RGGB implementation of a parser"""
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
            curr_dtype = '>u1'
        else:
            curr_dtype = '>u2'

        processed_data = []
        if len(set(color_format.bits_per_components)) == 2 or len(
                set(color_format.bits_per_components)) == 1:

            raw_data = bytearray(raw_data)
            if len(raw_data) % numpy.dtype(curr_dtype).alignment != 0:
                raw_data += (0).to_bytes(len(raw_data) %
                                         numpy.dtype(curr_dtype).alignment,
                                         byteorder="little")

            processed_data = numpy.frombuffer(raw_data, dtype=curr_dtype)
        else:
            raise NotImplementedError(
                "All color components needs to have same bits per pixel. Current: 1: {} bpp, 2: {} bpp, 3: {} bpp"
                .format(color_format.bits_per_components[0],
                        color_format.bits_per_components[1],
                        color_format.bits_per_components[2]))

        if (processed_data.size % width != 0):
            processed_data = numpy.concatenate(
                (processed_data,
                 numpy.zeros(width - (processed_data.size % width))))

        return Image(raw_data, color_format, processed_data, width,
                     processed_data.size // width)

    def get_displayable(self, image):
        """Provides displayable image data (RGB formatted)

        Returns: Numpy array containing displayable data.
        """

        return_data = numpy.reshape(
            image.processed_data, (image.height, image.width)).astype('float')

        return_data[:, :] = (255 * return_data[:, :]) / (
            2**image.color_format.bits_per_components[0] - 1)

        # Converting from Bayer BG (but data is Bayer RG) to RGB -> THIS IS A BUG IN OPENCV
        return cv.cvtColor(return_data.astype('uint8'), cv.COLOR_BAYER_BG2RGB)
