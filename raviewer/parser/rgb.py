"""Parser implementation for RGBA pixel format"""
from abc import ABCMeta, abstractmethod

from ..image.color_format import PixelFormat, Endianness
from ..image.image import Image
from .common import AbstractParser

import numpy
import cv2 as cv


def rescale_to_8bit(data, cbits):
    bpcs = 4
    if cbits[3] == 0:
        bpcs = 3
    for i in range(bpcs):
        if cbits[i] != 8:
            coeff = 255 / (2**cbits[i] - 1)
            numpy.multiply(data[:, :, i],
                           coeff,
                           out=data[:, :, i],
                           casting="unsafe")
    if cbits[3] == 0:
        data[:, :, 3] = numpy.uint8(255)
    return data


class AbstractParserRGB(AbstractParser, metaclass=ABCMeta):

    def _parse_not_bytefilled(self, raw_data, color_format):
        """Parses provided raw data to an image - bits per component are not multiple of 8.

        Keyword arguments:

            raw_data: bytes object
            color_format: target instance of ColorFormat

        Returns: properly parsed buffer data (numpy ndarray)
        """
        cbits = color_format.bits_per_components
        pixel_size = sum(cbits)
        if pixel_size & 7 != 0:
            raise Exception("Invalid pixel format")
        curr_dtype = self.get_dtype(pixel_size, color_format.endianness)
        if len(raw_data) % (pixel_size // 8) != 0:
            raw_data += b'\x00' * (pixel_size // 8 - (len(raw_data) %
                                                      (pixel_size // 8)))
        processed_data = numpy.frombuffer(raw_data, dtype=curr_dtype)
        temp = pixel_size
        res = numpy.empty((4 * len(processed_data), ), dtype=curr_dtype)
        all_equal = True
        for j, i in enumerate(cbits):
            if i != cbits[0]:
                all_equal = False
        mask = 0
        for j, i in enumerate(cbits):
            mask = (1 << i) - 1
            mask <<= temp - i
            temp -= i
            if all_equal:
                numpy.right_shift(processed_data, temp, out=res[j::4])
            else:
                channel = numpy.bitwise_and(processed_data, mask)
                numpy.right_shift(channel, temp, out=res[j::4])
        if all_equal:
            return numpy.bitwise_and(res, mask, out=res)
        return res

    def _color_mask(self, im, channels):
        im = numpy.copy(im)
        if not channels["r_y"]:
            im[:, :, 0] = 0
        if not channels["g_u"]:
            im[:, :, 1] = 0
        if not channels["b_v"]:
            im[:, :, 2] = 0
        if not channels["a_v"]:
            im[:, :, 3] = 255
        return im

    def _reorder(self, im):
        return im[:, :, [self._order.find(x) for x in "RGBA"]]

    @property
    @abstractmethod
    def _order(self):
        pass

    def get_displayable(self,
                        image: Image,
                        channels={
                            "r_y": True,
                            "g_u": True,
                            "b_v": True,
                            "a_v": True
                        }):

        return_data = numpy.reshape(image.processed_data.astype('uint8'),
                                    (image.height, image.width, 4))

        return_data = rescale_to_8bit(return_data,
                                      image.color_format.bits_per_components)

        return_data = self._reorder(return_data)

        return self._color_mask(return_data, channels)

    def get_pixel_raw_components(self, image, row, column, index):
        step_bytes = len(image.color_format._bpcs)
        return image.processed_data[index * step_bytes:index * step_bytes +
                                    step_bytes]

    def crop_image2rawformat(self, img, up_row, down_row, left_column,
                             right_column):
        reshaped_image = numpy.reshape(img.processed_data.astype(numpy.byte),
                                       (img.height, img.width, 4))
        truncated_image = reshaped_image[up_row:down_row,
                                         left_column:right_column]
        return truncated_image


class AbstractParserRGBA(AbstractParserRGB, metaclass=ABCMeta):
    """An RGB/BGR implementation of a parser - ALPHA LAST"""

    def parse(self, raw_data, color_format, width, reverse_bytes=0):
        max_value = max(color_format.bits_per_components)
        curr_dtype = self.get_dtype(max_value, color_format.endianness)

        # temp_set is used to differentiate between RGB24 and RGBA32
        # RGB24  - (8, 8, 8, 0)   temp_set = {8, 0}   len = 2
        # RGBA32 - (8, 8, 8, 8)   temp_set = {8}      len = 1
        #
        # for some inexplicable reason 0 is added to temp_set of length 2
        # even though, in implemented color formats it doesn't change anything
        #
        # I don't know whether this method generalizes to other color formats
        temp_set = set(color_format.bits_per_components)

        raw_data = bytearray(raw_data)
        if ((len(temp_set) == 1 or
             (len(temp_set) == 2
              and not temp_set.add(0)))) and max_value % 8 == 0:

            # alignment fixing padding
            if len(raw_data) % numpy.dtype(curr_dtype).alignment != 0:
                raw_data += (0).to_bytes(len(raw_data) %
                                         numpy.dtype(curr_dtype).alignment,
                                         byteorder="little")

            temp_raw_data = self.reverse(raw_data, reverse_bytes)
            temp = numpy.frombuffer(temp_raw_data, curr_dtype)
            processed_data = temp

            # this applies to RGB24 and its variants
            if len(temp_set) == 2:

                # this will be moved to _pad
                if (temp.size % (width * 3) != 0):
                    temp = numpy.concatenate(
                        (temp,
                         numpy.zeros((width * 3) - (temp.size % (width * 3)),
                                     dtype=curr_dtype)))

                # this part should be moved to get_displayable
                # because converting image into a displayable format should not be handled by parse
                temp = cv.cvtColor(
                    numpy.reshape(temp,
                                  (int(temp.size / (3 * width)), width, 3)),
                    cv.COLOR_RGB2RGBA)
                processed_data = numpy.reshape(temp, temp.size)
        else:
            # this is used for color formats with components not divisible by 8 (e.g. RGB565, RGB332)
            temp_raw_data = self.reverse(raw_data, reverse_bytes)
            processed_data = self._parse_not_bytefilled(
                temp_raw_data, color_format)

        # this applies to RGBA32 and its variants and will be moved to _pad
        if (processed_data.size % (width * 4) != 0):
            processed_data = numpy.concatenate(
                (processed_data,
                 numpy.zeros((width * 4) - (processed_data.size %
                                            (width * 4)))))
        return Image(raw_data, color_format, processed_data, width,
                     processed_data.size // (width * 4))


class ParserRGBA(AbstractParserRGBA):

    @property
    def _order(self):
        return "RGBA"


class ParserBGRA(AbstractParserRGBA):

    @property
    def _order(self):
        return "BGRA"


class AbstractParserARGB(AbstractParserRGB, metaclass=ABCMeta):
    """An RGB/BGR implementation of a parser - ALPHA FIRST"""

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
                         numpy.zeros((width * 3) - (temp.size % (width * 3)))))

                # this is the only place where parse methods differ
                # this is a conversion from RGB24 to ARGB32
                # A blank array (height, width, 1) is generated and attached to image array along the color axis
                temp = numpy.concatenate(
                    (numpy.full((int(temp.size / (width * 3)), width, 1),
                                (2**color_format.bits_per_components[0] - 1),
                                dtype=curr_dtype),
                     numpy.reshape(temp,
                                   (int(temp.size / (width * 3)), width, 3))),
                    axis=2)
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


class ParserARGB(AbstractParserRGBA):

    @property
    def _order(self):
        return "ARGB"


class ParserABGR(AbstractParserRGBA):

    @property
    def _order(self):
        return "ABGR"
