"""Parser implementation for YUV pixel format"""
from abc import abstractmethod, ABCMeta

from ..image.color_format import PixelFormat, Endianness
from ..image.image import Image
from .common import AbstractParser
from ..src.utils import pad_modulo

import numpy
import cv2 as cv
import math
from itertools import cycle


def normal_round(n):
    if n - math.floor(n) < 0.5:
        return int(math.floor(n))
    return int(math.ceil(n))


def interleave_channels(u, v):
    data = [
        combined for component in zip(cycle(u), v) for combined in component
    ]
    return data


def is_luma_only(channels):
    return not channels["b_v"] and not channels["g_u"] and channels["r_y"]


def concatenate_frames(frames):
    """Concatenates list of images into one image

    Keyword arguments:

        frames: list of images (numpy ndarray) of the same shape

    Returns: concatenated image (numpy ndarray)
    """
    if frames == []:
        return numpy.array([], dtype=numpy.uint8)
    elif len(frames) == 1:
        return frames[0]
    else:
        return numpy.concatenate(frames, axis=0)


class AbstractParserYUV420(AbstractParser, metaclass=ABCMeta):
    """An abstract YUV420 parser"""

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

        raw_data = bytearray(raw_data)
        if len(set(
                color_format.bits_per_components)) == 2 and max_value % 8 == 0:
            if len(raw_data) % numpy.dtype(curr_dtype).alignment != 0:
                raw_data += (0).to_bytes(len(raw_data) %
                                         numpy.dtype(curr_dtype).alignment,
                                         byteorder="little")
        else:
            raise NotImplementedError(
                "Other than 8-bit YUVs are not currently supported")
        processed_data = numpy.frombuffer(self.reverse(raw_data,
                                                       reverse_bytes),
                                          dtype=curr_dtype)
        processed_data = numpy.array(processed_data, dtype=curr_dtype)
        processed_data = pad_modulo(processed_data, (width, ))

        new_height = math.ceil(math.ceil(processed_data.size / width) / 1.5)
        return Image(raw_data, color_format, processed_data, width, new_height)

    @abstractmethod
    def _channel_mask(self, channels, image, im, height):
        pass

    @property
    @abstractmethod
    def _conversion_const(self):
        pass

    @property
    @abstractmethod
    def _order(self):
        pass

    @abstractmethod
    def _raw_channel_color(self, image, im):
        pass

    @abstractmethod
    def _get_nframes(self, image, height):
        pass

    def _preprocess(self, image, i, height):
        return numpy.copy(
            image.processed_data[i * image.width * int(height * 1.5):(1 + i) *
                                 image.width * int(height * 1.5)])

    def _pad(self, image, im):
        im = numpy.copy(im)
        processed_data = numpy.reshape(
            im, (int(im.size / image.width), image.width)).astype('uint8')

        return pad_modulo(processed_data, (3, 2))

    def get_displayable(self,
                        image,
                        height=0,
                        channels={
                            "r_y": True,
                            "g_u": True,
                            "b_v": True
                        }):
        """Provides displayable image data (RGB formatted)

        Returns: Numpy array containing displayable data.
        """
        tmp = []
        if height < 1:
            height = image.height

        n_frames = self._get_nframes(image, height)

        for i in range(n_frames):
            return_data = self._preprocess(image, i, height)
            return_data = self._channel_mask(channels, image, return_data,
                                             height)
            return_data = self._convert(return_data, image, height, channels)
            tmp.append(return_data)

        return concatenate_frames(tmp)

    def _convert(self, im, image, height, channels):
        if is_luma_only(channels):
            return cv.cvtColor(im[0:image.width * height], cv.COLOR_GRAY2RGB)
        else:
            im = self._pad(image, im)
            return cv.cvtColor(im, self._conversion_const)

    def raw_coloring(self, image, height=0):
        tmp = []

        if height < 1:
            height = image.height

        n_frames = self._get_nframes(image, height)

        for i in range(n_frames):
            return_data = self._preprocess(image, i, height)

            processed_data = self._pad(image, return_data)

            processed_data = numpy.expand_dims(processed_data, 2)

            return_data = processed_data * numpy.array([1, 1, 1]).reshape(
                (1, 1, 3))

            return_data = self._raw_channel_color(image, return_data)

            return_data = return_data.astype('uint8')
            tmp.append(return_data)

        return concatenate_frames(tmp)


class AbstractParserYUV420SP(AbstractParserYUV420, metaclass=ABCMeta):
    """An abstract semi-planar YUV420 parser"""

    def _raw_channel_color(self, image, im):
        im = numpy.copy(im)
        p = (image.color_format.palette[x] for x in self._order)
        p = [numpy.array(x).reshape((1, 1, 3)).astype('float64') for x in p]

        im = im.astype('float64')

        im[:image.height, :] *= p[0]

        cmap = numpy.array(p[1:]).reshape((1, 2, 3))

        uv = im[image.height:, :].reshape((-1, 2, 3))
        uv *= cmap

        return im

    def _get_nframes(self, image, height):
        return 0 if image.height == 0 else math.ceil(image.height / height)

    def get_pixel_raw_components(self, image, row, column, index):
        return_data = [
            image.processed_data[index],
            image.processed_data[image.width * image.height +
                                 (row // 2 * image.width) + (column // 2) * 2],
            image.processed_data[image.width * image.height +
                                 (row // 2 * image.width) + (column // 2) * 2 +
                                 1]
        ]
        if image.color_format.pixel_format == PixelFormat.YVU:
            return_data[1], return_data[2] = return_data[2], return_data[1]
        return return_data

    def crop_image2rawformat(self, image, up_row, down_row, left_column,
                             right_column):
        return_data = numpy.reshape(
            image.processed_data.astype('uint8'),
            (len(image.processed_data) // image.width, image.width))
        u = numpy.array(image.processed_data[image.width * image.height +
                                             1::2])
        v = numpy.array(image.processed_data[image.width * image.height::2])
        u = numpy.repeat(u, 2)
        u = numpy.array(u)
        u = numpy.reshape(u.astype('uint8'), (image.height // 2, image.width))
        u = u[up_row // 2:down_row // 2, left_column:right_column:2]

        v = numpy.repeat(v, 2)
        v = numpy.array(v)
        v = numpy.reshape(v.astype('uint8'), (image.height // 2, image.width))
        v = v[up_row // 2:down_row // 2, left_column:right_column:2]
        v = v.flatten()
        u = u.flatten()
        uv = None
        uv = interleave_channels(v, u)
        yuv = numpy.concatenate([
            numpy.array(return_data[up_row:down_row,
                                    left_column:right_column]).flatten(), uv
        ])
        return yuv


class ParserYUV420SP(AbstractParserYUV420SP):
    """A semi-planar YUV420 (NV12) parser"""

    @property
    def _order(self):
        return "YUV"

    def _channel_mask(self, channels, image, im, height):
        im = numpy.copy(im)
        if not channels["r_y"]:
            im[0:image.width * height] = 0
        if not channels["g_u"]:
            im[image.width * height::2] = 0
        if not channels["b_v"]:
            im[image.width * height + 1::2] = 0

        return im

    @property
    def _conversion_const(self):
        return cv.COLOR_YUV2RGB_NV12


class ParserYVU420SP(AbstractParserYUV420SP):
    """A semi-planar YVU420 (NV21) parser"""

    @property
    def _order(self):
        return "YVU"

    def _channel_mask(self, channels, image, im, height):
        im = numpy.copy(im)
        if not channels["r_y"]:
            im[0:image.width * height] = 0
        if not channels["g_u"]:
            im[image.width * height + 1::2] = 0
        if not channels["b_v"]:
            im[image.width * height::2] = 0

        return im

    @property
    def _conversion_const(self):
        return cv.COLOR_YUV2RGB_NV21


class AbstractParserYUV420P(AbstractParserYUV420SP, metaclass=ABCMeta):
    """An abstract planar YUV420 parser"""

    def _get_nframes(self, image, height):
        return 0 if image.height == 0 else math.ceil(
            len(image.processed_data) / image.width / height / 1.5)

    def _raw_channel_color(self, image, im):
        im = numpy.copy(im)
        p = (image.color_format.palette[x] for x in self._order)
        p = [numpy.array(x).reshape((1, 1, 3)).astype('float64') for x in p]

        im = im.astype('float64')
        im[:image.height, :] *= p[0]
        im[image.height:image.height + image.height // 4, :] *= p[1]
        im[image.height + image.height // 4:, :] *= p[2]

        return im

    def get_pixel_raw_components(self, image, row, column, index):
        return_data = [
            image.processed_data[index],
            image.processed_data[image.width * image.height + column // 2 +
                                 row // 2 * image.width // 2],
            image.processed_data[image.width * image.height +
                                 image.width * image.height // 4 +
                                 column // 2 + row // 2 * image.width // 2]
        ]
        if image.color_format.pixel_format == PixelFormat.YVU:
            return_data[1], return_data[2] = return_data[2], return_data[1]
        return return_data

    def crop_image2rawformat(self, image, up_row, down_row, left_column,
                             right_column):
        return_data = numpy.reshape(
            image.processed_data.astype('uint8'),
            (len(image.processed_data) // image.width, image.width))
        u = numpy.array(
            image.processed_data[image.width *
                                 image.height:image.width * image.height +
                                 image.width * image.height // 4])
        u = numpy.repeat(u, 2)
        u = numpy.array(u)
        u = numpy.reshape(u.astype('uint8'), (image.height // 2, image.width))
        u = u[up_row // 2:(down_row // 2) + 1, left_column:right_column:2]
        u = u.flatten()
        v = numpy.array(image.processed_data[image.width * image.height +
                                             image.width * image.height // 4:])
        v = numpy.repeat(v, 2)
        v = numpy.array(v)
        v = numpy.reshape(v.astype('uint8'), (image.height // 2, image.width))
        v = v[up_row // 2:(down_row // 2) + 1, left_column:right_column:2]
        v = v.flatten()
        yuv = numpy.concatenate([
            numpy.array(return_data[up_row:down_row,
                                    left_column:right_column]).flatten(), u, v
        ])
        return yuv


class ParserYUV420P(AbstractParserYUV420P):
    """A planar YUV420 (I420) parser"""

    def _channel_mask(self, channels, image, im, height):
        im = numpy.copy(im)
        if not channels["r_y"]:
            im[0:image.width * height] = 0
        if not channels["g_u"]:
            im[image.width * height + 1:image.width * height +
               image.width * height // 4] = 0
        if not channels["b_v"]:
            im[image.width * height + image.width * height // 4:] = 0

        return im

    @property
    def _conversion_const(self):
        return cv.COLOR_YUV2RGB_I420

    @property
    def _order(self):
        return "YUV"


class ParserYVU420P(AbstractParserYUV420P):
    """A planar YVU420 (YV12) parser"""

    def _channel_mask(self, channels, image, im, height):
        im = numpy.copy(im)
        if not channels["r_y"]:
            im[0:image.width * height] = 0
        if not channels["g_u"]:
            im[image.width * height + image.width * height // 4:] = 0
        if not channels["b_v"]:
            im[image.width * height + 1:image.width * height +
               image.width * height // 4] = 0

        return im

    @property
    def _conversion_const(self):
        return cv.COLOR_YUV2RGB_YV12

    @property
    def _order(self):
        return "YVU"


class AbstractParserYUV422(AbstractParser, metaclass=ABCMeta):
    """An abstract YUV422 parserr"""

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

        bpcs_set = set(color_format.bits_per_components)
        if len(bpcs_set) == 2 or len(bpcs_set) == 1 and max_value % 8 == 0:
            raw_data = bytearray(raw_data)
            if len(raw_data) % numpy.dtype(curr_dtype).alignment != 0:
                raw_data += (0).to_bytes(len(raw_data) %
                                         numpy.dtype(curr_dtype).alignment,
                                         byteorder="little")
        else:
            raise NotImplementedError(
                "Other than 8-bit YUVs are not currently supported")

        processed_data = numpy.frombuffer(self.reverse(raw_data,
                                                       reverse_bytes),
                                          dtype=curr_dtype)
        processed_data = numpy.array(processed_data, dtype=curr_dtype)
        processed_data = pad_modulo(processed_data, (width * 2, ))

        return Image(raw_data, color_format, processed_data, width,
                     processed_data.size // (width * 2))


class AbstractParserYUV422PA(AbstractParserYUV422, metaclass=ABCMeta):
    """An abstract packed YUV422 parser"""

    def get_displayable(self,
                        image,
                        height=0,
                        channels={
                            "r_y": True,
                            "g_u": True,
                            "b_v": True
                        }):
        """Provides displayable image data (RGB formatted)

        Returns: Numpy array containing displayable data.
        """
        tmp = []
        if height < 1: height = image.height
        n_frames = 0 if image.height == 0 else math.ceil(image.height / height)

        for i in range(n_frames):
            temp_processed_data = image.processed_data[i * (
                image.width * height * 2):(1 + i) * (image.width * height * 2)]
            height = math.ceil(len(temp_processed_data) / image.width / 2)

            temp_processed_data = self._color_mask(temp_processed_data,
                                                   channels)
            temp_processed_data = self._convert(temp_processed_data,
                                                image.width, channels)
            tmp.append(temp_processed_data)

        return concatenate_frames(tmp)

    def _pad(self, im, width):
        even_width = width + width % 2
        return pad_modulo(im, (even_width * 2, )), even_width

    def _convert(self, im, width, channels):
        if is_luma_only(channels):
            return self._convert2GRAY(im)
        else:
            im, width = self._pad(im, width)
            return self._convert2RGB(im, width)

    def _convert2GRAY(self, im):
        return cv.cvtColor(im[self._offset["Y"]::2], cv.COLOR_GRAY2RGB)

    def _raw_channel_color(self, image, im, width):
        im = numpy.copy(im)
        p = [image.color_format.palette[x] for x in self._order]
        p = numpy.array(p).astype('float64').reshape((1, 4, 3))

        im = im.astype('float64')

        im = im.reshape((-1, 4, 1))
        im = im * p

        return im.reshape((-1, width, 3))

    def raw_coloring(self, image, height=0):
        tmp = []
        if height < 1:
            height = image.height

        n_frames = 0 if image.height == 0 else math.ceil(image.height / height)

        for i in range(n_frames):
            temp_processed_data = image.processed_data[i * (
                image.width * height * 2):(1 + i) * (image.width * height * 2)]
            height = math.ceil(len(temp_processed_data) / image.width / 2)

            return_data, width = self._pad(temp_processed_data, image.width)
            return_data = self._raw_channel_color(image, return_data, width)
            return_data = return_data.astype('uint8')
            return_data = return_data.reshape((-1, width, 3))

            tmp.append(return_data)

        return concatenate_frames(tmp)

    def get_pixel_raw_components(self, image, row, column, index):
        return image.processed_data[(index // 2) * 4:(index // 2) * 4 + 4]

    def crop_image2rawformat(self, image, up_row, down_row, left_column,
                             right_column):
        return_data = numpy.reshape(
            image.processed_data.astype(numpy.byte),
            (image.height, len(image.processed_data) // image.height))
        return return_data[up_row:down_row, left_column * 2:right_column * 2]

    @abstractmethod
    def _convert2RGB(self, im, width):
        pass

    @property
    @abstractmethod
    def _order(self):
        pass

    @property
    def _offset(self):
        return {c: self._order.find(c) for c in "YUV"}

    def _color_mask(self, im, channels):
        im = numpy.copy(im)
        if not channels["r_y"]:
            im[self._offset["Y"]::2] = 0
        if not channels["g_u"]:
            im[self._offset["U"]::4] = 0
        if not channels["b_v"]:
            im[self._offset["V"]::4] = 0

        return im


class ParserYUYV422PA(AbstractParserYUV422PA):
    """A packed YUYV422 (YUY2) parser"""

    @property
    def _order(self):
        return "YUYV"

    def _convert2RGB(self, im, width):
        return cv.cvtColor(im.reshape(-1, width, 2), cv.COLOR_YUV2RGB_YUYV)


class ParserUYVY422PA(AbstractParserYUV422PA):
    """A packed UYVY422 (UYVY) parser"""

    @property
    def _order(self):
        return "UYVY"

    def _convert2RGB(self, im, width):
        return cv.cvtColor(im.reshape(-1, width, 2), cv.COLOR_YUV2RGB_UYVY)


class ParserVYUY422PA(AbstractParserYUV422PA):
    """A packed VYUY422 (VYUY) parser"""

    @property
    def _order(self):
        return "VYUY"

    def _convert2RGB(self, im, width):
        im = im.reshape((-1, 4))[:, [2, 1, 0, 3]]
        return cv.cvtColor(im.reshape(-1, width, 2), cv.COLOR_YUV2RGB_UYVY)


class ParserYVYU422PA(AbstractParserYUV422PA):
    """A packed YVYU422 (YVYU) parser"""

    @property
    def _order(self):
        return "YVYU"

    def _convert2RGB(self, im, width):
        return cv.cvtColor(im.reshape(-1, width, 2), cv.COLOR_YUV2RGB_YVYU)


class ParserYUV422P(AbstractParserYUV422):
    """A planar YUV422 (I422) parser"""

    def _get_nframes(self, image, height):
        return 0 if image.height == 0 else math.ceil(
            len(image.processed_data) / image.width / height / 2)

    def _preprocess(self, image, height, i):
        return numpy.copy(
            image.processed_data[int(i * (image.width * height) *
                                     2):int((1 + i) * (image.width * height) *
                                            2)])

    def get_displayable(self,
                        image,
                        height=0,
                        channels={
                            "r_y": True,
                            "g_u": True,
                            "b_v": True
                        }):
        """Provides displayable image data (RGB formatted)

        Returns: Numpy array containing displayable data.
        """
        if height < 1: height = image.height
        tmp = []
        n_frames = self._get_nframes(image, height)
        for i in range(n_frames):
            temp_processed_data = self._preprocess(image, height, i)
            height = math.ceil(len(temp_processed_data) / image.width / 2)
            temp_processed_data = self._channel_mask(channels, image,
                                                     temp_processed_data,
                                                     height)
            return_data = self._convert(temp_processed_data, image.width,
                                        height, channels)
            tmp.append(return_data)

        return concatenate_frames(tmp)

    def _channel_mask(self, channels, image, im, height):
        im = im.copy()
        if image.color_format.pixel_format == PixelFormat.YUV:
            if not channels["r_y"]:
                im[0:height * image.width:] = 0
            if not channels["g_u"]:
                im[height * image.width:height *
                   (3 * image.width // 2 + image.width % 2)] = 0
            if not channels["b_v"]:
                im[height * (3 * image.width // 2 + image.width % 2):] = 0
        return im

    def _convert(self, im, width, height, channels):
        if is_luma_only(channels):
            return cv.cvtColor(im[:width * height], cv.COLOR_GRAY2RGB)
        else:
            return self.convert2RGB(im, width, height)

    def raw_coloring(self, image, height=0):
        tmp = []

        if height < 1:
            height = image.height

        n_frames = self._get_nframes(image, height)

        for i in range(n_frames):
            processed_data = self._preprocess(image, height, i)

            processed_data = processed_data.reshape((-1, image.width, 1))

            return_data = processed_data * numpy.array([1, 1, 1]).reshape(
                (1, 1, 3))

            return_data = self._raw_channel_color(image, return_data)

            return_data = return_data.astype('uint8')
            tmp.append(return_data)

        return concatenate_frames(tmp)

    def _raw_channel_color(self, image, im):
        im = numpy.copy(im)

        p = (image.color_format.palette[x] for x in "YUV")
        p = [numpy.array(x).reshape((1, 1, 3)).astype('float64') for x in p]

        im = im.astype('float64')
        im[:image.height, :] *= p[0]
        im[image.height:image.height + image.height // 2, :] *= p[1]
        im[image.height + image.height // 2:, :] *= p[2]

        return im

    def convert2RGB(self, processed_data, width, height):
        y = processed_data[0:height * width:]
        u = processed_data[height * width:height *
                           (3 * width // 2 + width % 2)]
        v = processed_data[height * (3 * width // 2 + width % 2):]
        even_width = width + width % 2
        y = pad_modulo(y, (even_width, ))
        u = numpy.pad(u, (0, max(y.size // 2 - u.size, 0)))[:y.size // 2]
        v = numpy.pad(v, (0, max(y.size // 2 - v.size, 0)))[:y.size // 2]
        yuv = numpy.empty((y.size, 2), dtype=numpy.uint8)
        yuv[:, 0] = y
        yuv[0::2, 1] = u
        yuv[1::2, 1] = v
        rgb = cv.cvtColor(yuv.reshape((-1, even_width, 2)),
                          cv.COLOR_YUV2RGB_YUYV)
        return rgb

    def get_pixel_raw_components(self, image, row, column, index):
        return [
            image.processed_data[index],
            image.processed_data[image.height * image.width + index // 2],
            image.processed_data[image.height *
                                 (3 * image.width // 2 + image.width % 2) +
                                 index // 2]
        ]

    def crop_image2rawformat(self, image, up_row, down_row, left_column,
                             right_column):
        return_data = numpy.reshape(
            image.processed_data.astype('uint8'),
            (len(image.processed_data) // image.width, image.width))
        u = numpy.array(
            image.processed_data[image.height * image.width:image.height *
                                 (3 * image.width // 2 + image.width % 2)])
        u = numpy.repeat(u, 2)
        u = numpy.array(u)
        u = numpy.reshape(u.astype('uint8'), (image.height, image.width))
        u = u[up_row:down_row, left_column:right_column:2]
        u = u.flatten()

        v = numpy.array(
            image.processed_data[image.height *
                                 (3 * image.width // 2 + image.width % 2):])
        v = numpy.repeat(v, 2)
        v = numpy.array(v)
        v = numpy.reshape(v.astype('uint8'), (image.height, image.width))
        v = v[up_row:down_row, left_column:right_column:2]
        v = v.flatten()
        yuv = numpy.concatenate([
            numpy.array(return_data[up_row:down_row,
                                    left_column:right_column]).flatten(), u, v
        ])
        return yuv
