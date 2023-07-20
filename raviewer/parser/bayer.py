"""Parser implementation for Bayer pixel format"""
from abc import ABCMeta

from ..image.image import Image
from ..image.color_format import Endianness, Platform
from .common import AbstractParser
from ..src.utils import determine_color_format

import numpy
import cv2 as cv


class ParserBayer(AbstractParser, metaclass=ABCMeta):

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
            temp_raw_data = self.reverse(raw_data, reverse_bytes)
            processed_data = numpy.frombuffer(temp_raw_data, dtype=curr_dtype)
        else:
            raise NotImplementedError(
                "All color components needs to have same bits per pixel. Current: 1: {} bpp, 2: {} bpp, 3: {} bpp"
                .format(color_format.bits_per_components[0],
                        color_format.bits_per_components[1],
                        color_format.bits_per_components[2]))
        """
        some Tegra platforms use non-standard data alignment, in order for
        frames captured by these devices to be properly displayed,
        the data needs to be bitwise shifted by a value dependent on the platform
        """
        if color_format.platform == Platform.TX2:
            processed_data = numpy.right_shift(
                processed_data, 16 - color_format.bits_per_components[0] - 2)
        elif color_format.platform == Platform.XAVIER:
            processed_data = numpy.right_shift(
                processed_data, 16 - color_format.bits_per_components[0])

        if (processed_data.size % width != 0):
            processed_data = numpy.concatenate(
                (processed_data,
                 numpy.zeros(width - (processed_data.size % width))))
        return Image(raw_data, color_format, processed_data, width,
                     processed_data.size // width)

    def _preprocess(self, image):
        return_data = numpy.reshape(numpy.copy(image.processed_data),
                                    (image.height, image.width))
        coeff = 255 / (2**image.color_format.bits_per_components[0] - 1)
        numpy.multiply(return_data, coeff, out=return_data, casting="unsafe")

        return return_data

    def _channel_mask(self, im, channels):
        if not channels["r_y"]:
            im[0::2, 0::2] = 0
        if not channels["g_u"]:
            im[1::2, 0::2] = 0
            im[0::2, 1::2] = 0
        if not channels["b_v"]:
            im[1::2, 1::2] = 0

        return im

    def _get_cmap(self, color_format, filter):
        assert len(filter) == 4
        assert set(filter).issubset(['R', 'G', 'B'])

        if color_format is None or color_format.palette is None:
            return None

        cmap = numpy.array([color_format.palette[x] for x in filter]).reshape(
            (1, 4, 3))

        return cmap

    def _bayer_raw_coloring(self, image, filter):
        im = self._preprocess(image)
        if (cmap := self._get_cmap(image.color_format, filter)) is None:
            return None

        return self._non_debayerized_display(im, cmap).astype('uint8')

    def _bayer_get_displayable(self, image, channels, code):
        im = self._preprocess(image)
        im = self._channel_mask(im, channels)

        # Converting from Bayer BG (but data is Bayer RG) to RGB -> THIS IS A BUG IN OPENCV

        return cv.cvtColor(im.astype('uint8'), code)

    @staticmethod
    def _non_debayerized_display(im, cmap):
        """Converts bayer formatted image to displayable image data

        Returns: Numpy array containing displayable data (width x height x 3)
        """

        if cmap.shape != (1, 4, 3):
            raise ValueError("Expected palette to be (1, 4, 3) shaped.")

        # Split image into 2 pixels wide columns and stack them vertically.
        t = numpy.vstack(numpy.hsplit(im, im.shape[1] // 2))

        # Reshape it into a shape (x, 4, 1) broadcastable with the palette (1, 4, 3)
        t = t.reshape(-1, 4, 1)

        # Compute RGB values by scaling each cmap vector by corresponding pixel.
        t = t * cmap

        # Return to the shape obtained in the first step
        t = t.reshape(-1, 2, 3)

        # Perform an inverse operation to one from the first step
        result = numpy.hstack(numpy.vsplit(t, im.shape[1] // 2))

        return result

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


class ParserBayerRG(ParserBayer):

    def get_displayable(self, image: Image, channels):
        # Converting from Bayer BG (but data is Bayer RG) to RGB -> THIS IS A BUG IN OPENCV
        return self._bayer_get_displayable(image, channels,
                                           cv.COLOR_BAYER_BG2RGB)

    def raw_coloring(self, image: Image):
        return self._bayer_raw_coloring(image, ['R', 'G', 'G', 'B'])


class ParserBayerBG(ParserBayer):

    def get_displayable(self, image: Image, channels):
        return self._bayer_get_displayable(image, channels,
                                           cv.COLOR_BAYER_RG2RGB)

    def raw_coloring(self, image: Image):
        return self._bayer_raw_coloring(image, ['B', 'G', 'G', 'R'])


class ParserBayerGB(ParserBayer):

    def get_displayable(self, image: Image, channels):
        return self._bayer_get_displayable(image, channels,
                                           cv.COLOR_BAYER_GR2RGB)

    def raw_coloring(self, image: Image):
        return self._bayer_raw_coloring(image, ['G', 'B', 'R', 'G'])


class ParserBayerGR(ParserBayer):

    def get_displayable(self, image: Image, channels):
        return self._bayer_get_displayable(image, channels,
                                           cv.COLOR_BAYER_GB2RGB)

    def raw_coloring(self, image: Image):
        return self._bayer_raw_coloring(image, ['G', 'R', 'B', 'G'])
