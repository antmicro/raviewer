from abc import ABCMeta, abstractmethod
from ..image.image import Image
from ..image.color_format import PixelFormat
from .common import AbstractParser
from ..src.utils import pad_modulo

import numpy


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
    return data


def fix_alpha(data, cbits):
    if cbits[3] == 0:
        data[:, :, 3] = numpy.uint8(255)
    return data


class AbstractParserRGBA(AbstractParser, metaclass=ABCMeta):
    """An abstract parser for RGBA and its variants (e.g. ARGB, ABGR)"""

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
            res = numpy.bitwise_and(res, mask, out=res)

        if min(color_format.bits_per_components) == 0:
            return numpy.delete(res.reshape(-1, 4), 3, 1).flatten()

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

    def _convert(self, color_format, im):
        return im[:, :, [self._order.find(x) for x in "RGBA"]]

    @property
    @abstractmethod
    def _order(self):
        pass

    def _fix_alignment(self, raw_data, curr_dtype):
        if len(raw_data) % numpy.dtype(curr_dtype).alignment != 0:
            raw_data += (0).to_bytes(len(raw_data) %
                                     numpy.dtype(curr_dtype).alignment,
                                     byteorder="little")
        return raw_data

    def _pad(self, im, width, curr_dtype):
        return pad_modulo(im, (width * 4, ))

    def _raw_channel_color(self, image, im):
        im = numpy.copy(im)
        p = [image.color_format.palette[x] for x in self._order]
        p = numpy.array(p).astype('float64').reshape((1, -1, 3))

        im = im.astype('float64')

        im = im.reshape((-1, p.shape[1], 1))
        im = im * p

        return im.reshape((-1, image.width, 3))

    def get_displayable(self,
                        image,
                        channels={
                            "r_y": True,
                            "g_u": True,
                            "b_v": True,
                            "a_v": True
                        }):
        """Provides displayable image data (RGB formatted)

        Returns: Numpy array containing displayable data.
        """

        return_data = numpy.reshape(
            image.processed_data.astype('uint8'),
            (image.height, image.width, len(self._order)))

        return_data = rescale_to_8bit(return_data,
                                      image.color_format.bits_per_components)

        return_data = self._convert(image.color_format, return_data)

        return_data = fix_alpha(return_data,
                                image.color_format.bits_per_components)

        return self._color_mask(return_data, channels)

    def raw_coloring(self, image, height=0):
        return_data = numpy.reshape(
            image.processed_data.astype('uint8'),
            (image.height, image.width, len(self._order)))

        return_data = rescale_to_8bit(return_data,
                                      image.color_format.bits_per_components)

        out = self._raw_channel_color(image, return_data).astype('uint8')
        return out.reshape(-1, image.width * len(self._order), 3)

    def parse(self, raw_data, color_format, width, reverse_bytes=0):
        max_val = max(color_format.bits_per_components)

        curr_dtype = self.get_dtype(max_val, color_format.endianness)

        if max_val % 8 == 0:
            raw_data = self._fix_alignment(raw_data, curr_dtype)
            reversed_raw_data = self.reverse(raw_data, reverse_bytes)
            processed_data = numpy.frombuffer(reversed_raw_data, curr_dtype)
        else:
            reversed_raw_data = self.reverse(raw_data, reverse_bytes)
            processed_data = self._parse_not_bytefilled(
                reversed_raw_data, color_format)

        processed_data = self._pad(processed_data, width, curr_dtype)

        return Image(raw_data, color_format, processed_data, width,
                     processed_data.size // (width * len(self._order)))

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


class AbstractParserRGB(AbstractParserRGBA, metaclass=ABCMeta):
    """An abstract parser for RGB and its variants"""

    def _convert(self, color_format, im):
        im = im[:, :, [self._order.find(x) for x in "RGB"]]
        return numpy.pad(im, ((0, 0), (0, 0), (0, 1)),
                         'constant',
                         constant_values=(0, 255))

    def _pad(self, im, width, curr_dtype):
        return pad_modulo(im, (width * 3, ))


class ParserRGB(AbstractParserRGB):
    """RGB parser (RGB24, RGB565, RGB332)"""

    @property
    def _order(self):
        return "RGB"


class ParserBGR(AbstractParserRGB):
    """BGR parser (BGR24)"""

    @property
    def _order(self):
        return "BGR"


class ParserRGBA(AbstractParserRGBA):
    """RGBA parser (RGBA32, RGBA444, RGBA555)"""

    @property
    def _order(self):
        return "RGBA"


class ParserBGRA(AbstractParserRGBA):
    """BGRA parser (BGRA32, BGRA444, BGRA555)"""

    @property
    def _order(self):
        return "BGRA"


class ParserARGB(AbstractParserRGBA):
    """ARGB parser (ARGB32, ARGB444, ARGB555)"""

    @property
    def _order(self):
        return "ARGB"


class ParserABGR(AbstractParserRGBA):
    """ABGR parser (ABGR32, ABGR444, ABGR555)"""

    @property
    def _order(self):
        return "ABGR"
