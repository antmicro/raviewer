"""Parser implementation for Bayer pixel format"""

from ..image.image import Image
from ..image.color_format import Endianness
from .common import AbstractParser

import numpy
import cv2 as cv


class ParserBayerRG(AbstractParser):
    """A Bayer RGGB implementation of a parser"""

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

        processed_data = []
        raw_data = bytearray(raw_data)
        if len(set(color_format.bits_per_components)) == 2 or len(
                set(color_format.bits_per_components)
        ) == 1 and max_value % 8 == 0:

            if len(raw_data) % numpy.dtype(curr_dtype).alignment != 0:
                raw_data += (0).to_bytes(len(raw_data) %
                                         numpy.dtype(curr_dtype).alignment,
                                         byteorder="little")
            processed_data = numpy.frombuffer(self.reverse(
                raw_data, reverse_bytes),
                                              dtype=curr_dtype)
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

    def get_displayable(self, image, channels):
        """Provides displayable image data (RGB formatted)

        Returns: Numpy array containing displayable data.
        """
        return_data = numpy.reshape(
            image.processed_data, (image.height, image.width)).astype('float')

        #Set RGGB channels
        if not channels["r_y"]:
            return_data[0::2, 0::2] = 0
        if not channels["g_u"]:
            return_data[1::2, 0::2] = 0
            return_data[0::2, 1::2] = 0
        if not channels["b_v"]:
            return_data[1::2, 1::2] = 0

        return_data[:, :] = (255 * return_data[:, :]) / (
            2**image.color_format.bits_per_components[0] - 1)
        # Converting from Bayer BG (but data is Bayer RG) to RGB -> THIS IS A BUG IN OPENCV
        return cv.cvtColor(return_data.astype('uint8'), cv.COLOR_BAYER_BG2RGB)

    def get_pixel_raw_components(self, image, row, column, index):
        #Bayer interpolation
        step_bytes = len([i for i in image.color_format._bpcs if i != 0])
        index = row // 2 * image.width // 2 * step_bytes + column // 2 * step_bytes
        return image.processed_data[index:index + 3]

    def crop_image2rawformat(self, img, up_row, down_row, left_column,
                             right_column):
        max_value = max(img.color_format.bits_per_components)
        curr_dtype = self.get_dtype(max_value, img.color_format.endianness)

        reshaped_image = numpy.reshape(
            img.processed_data.astype(numpy.dtype(curr_dtype)),
            (img.height, img.width))
        truncated_image = reshaped_image[up_row:down_row,
                                         left_column:right_column]
        return truncated_image
