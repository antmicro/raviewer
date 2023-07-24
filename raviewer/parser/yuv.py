"""Parser implementation for YUV pixel format"""
from abc import abstractmethod, ABCMeta

from ..image.color_format import PixelFormat, Endianness
from ..image.image import Image
from .common import AbstractParser

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
        numpy.concatenate(frames, axis=0)


class ParserYUV420(AbstractParser, metaclass=ABCMeta):
    """A semi-planar YUV420 implementation of a parser"""

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
        if (processed_data.size % width != 0):
            processed_data = numpy.concatenate(
                (processed_data,
                 numpy.zeros(width - (processed_data.size % width))))

        new_height = math.ceil(math.ceil(processed_data.size / width) / 1.5)
        return Image(raw_data, color_format, processed_data, width, new_height)

    @abstractmethod
    def _channel_mask(self, channels, image, im, height):
        pass

    def _raw_channel_color(self, image, im):
        p = (image.color_format.palette[x] for x in self._order)
        p = [numpy.array(x).reshape((1, 1, 3)).astype('float64') for x in p]

        im = im.astype('float64')

        im[:image.height, :] *= p[0]

        cmap = numpy.array(p[1:]).reshape((1, 2, 3))

        uv = im[image.height:, :].reshape((-1, 2, 3))
        uv *= cmap

        return im

    def _preprocess(self, image, i, height):
        return image.processed_data[i * image.width *
                                    int(height * 1.5):(1 + i) * image.width *
                                    int(height * 1.5)]

    def _pad(self, image, im):
        processed_data = numpy.reshape(
            im, (int(im.size / image.width), image.width)).astype('uint8')

        if processed_data.shape[0] % 3 != 0:
            processed_data = numpy.concatenate(
                (processed_data,
                 numpy.zeros(
                     (3 -
                      (processed_data.shape[0] % 3), processed_data.shape[1]),
                     dtype=numpy.uint8)))

        if processed_data.shape[1] % 2 != 0:
            processed_data = numpy.concatenate(
                (processed_data,
                 numpy.zeros((processed_data.shape[0], 1), dtype=numpy.uint8)),
                axis=1)

        return processed_data

    @property
    @abstractmethod
    def _conversion_const(self):
        pass

    @property
    @abstractmethod
    def _order(self):
        pass

    def _get_nframes(self, image, height):
        return 0 if image.height == 0 else math.ceil(image.height / height)

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
            processed_data = self._pad(image, return_data)

            return_data = cv.cvtColor(processed_data, self._conversion_const)
            tmp.append(return_data)

        return concatenate_frames(tmp)

    def raw_coloring(self, image):
        tmp = []

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


class ParserYUVSP(ParserYUV420):

    @property
    def _order(self):
        return ['Y', 'U', 'V']

    def _channel_mask(self, channels, image, im, height):
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


class ParserYVUSP(ParserYUV420):

    @property
    def _order(self):
        return ['Y', 'V', 'U']

    def _channel_mask(self, channels, image, im, height):
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


class ParserYUV420Planar(ParserYUV420, metaclass=ABCMeta):
    """A planar YUV420 implementation of a parser"""

    def _get_nframes(self, image, height):
        return 0 if image.height == 0 else math.ceil(
            len(image.processed_data) / image.width / height / 1.5)

    def _raw_channel_color(self, image, im):
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


class ParserYUVP(ParserYUV420Planar):

    def _channel_mask(self, channels, image, im, height):
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
        return ['Y', 'U', 'V']


class ParserYVUP(ParserYUV420Planar):

    def _channel_mask(self, channels, image, im, height):
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
        return ['Y', 'V', 'U']


class ParserYUV422(AbstractParser, metaclass=ABCMeta):
    """A packed YUV422 implementation of a parser"""

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
        if (processed_data.size % (width * 2) != 0):
            processed_data = numpy.concatenate(
                (processed_data,
                 numpy.zeros((width * 2) - (processed_data.size %
                                            (width * 2)))))

        return Image(raw_data, color_format, processed_data, width,
                     processed_data.size // (width * 2))


class ParserYUV422Packed(ParserYUV422, metaclass=ABCMeta):

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
            return_data = self._conversion_func(temp_processed_data, height,
                                                image.width)
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
    def _conversion_func(self, im, height, width):
        pass

    @property
    @abstractmethod
    def _offset(self):
        pass

    def _color_mask(self, im, channels):
        if not channels["r_y"]:
            im[self._offset["Y"]::2] = 0
        if not channels["g_u"]:
            im[self._offset["U"]::4] = 0
        if not channels["b_v"]:
            im[self._offset["V"]::4] = 0

        return im


class ParserYUYV(ParserYUV422Packed):

    @property
    def _offset(self):
        return {
            "Y": 0,
            "U": 1,
            "V": 3,
        }

    def _conversion_func(self, im, height, width):
        return cv.cvtColor(im.reshape(height, width, 2), cv.COLOR_YUV2RGB_YUYV)


class ParserUYVY(ParserYUV422Packed):

    @property
    def _offset(self):
        return {
            "Y": 1,
            "U": 0,
            "V": 2,
        }

    def _conversion_func(self, im, height, width):
        return cv.cvtColor(im.reshape(height, width, 2), cv.COLOR_YUV2RGB_UYVY)


class ParserVYUY(ParserYUV422Packed):

    @property
    def _offset(self):
        return {
            "Y": 1,
            "U": 2,
            "V": 0,
        }

    def _conversion_func(self, im, height, width):
        im = im.reshape((-1, 4))[:, [2, 1, 0, 3]]
        return cv.cvtColor(im.reshape(height, width, 2), cv.COLOR_YUV2RGB_UYVY)


class ParserYVYU(ParserYUV422Packed):

    @property
    def _offset(self):
        return {
            "Y": 0,
            "U": 3,
            "V": 1,
        }

    def _conversion_func(self, im, height, width):
        return cv.cvtColor(im.reshape(height, width, 2), cv.COLOR_YUV2RGB_YVYU)


class ParserYUV422Planar(ParserYUV422):

    def get_displayable(self,
                        image,
                        height,
                        channels={
                            "r_y": True,
                            "g_u": True,
                            "b_v": True
                        }):
        """Provides displayable image data (RGB formatted)

        Returns: Numpy array containing displayable data.
        """
        conversion_const = None
        if image.color_format.pixel_format == PixelFormat.YUV:
            conversion_const = cv.COLOR_YUV2RGB_YUYV
        if height < 1: height = image.height
        tmp = []
        n_frames = 0 if image.height == 0 else math.ceil(
            len(image.processed_data) / image.width / height / 2)
        for i in range(n_frames):
            temp_processed_data = image.processed_data[int(i * (
                image.width * height) * 2):int((1 + i) *
                                               (image.width * height) * 2)]
            height = math.ceil(len(temp_processed_data) / image.width / 2)
            return_data = numpy.zeros((height, image.width, 2),
                                      dtype=numpy.uint8)
            if image.color_format.pixel_format == PixelFormat.YUV:
                if not channels["r_y"]:
                    temp_processed_data[0:height * image.width:] = 0
                if not channels["g_u"]:
                    temp_processed_data[height * image.width:height *
                                        (3 * image.width // 2 +
                                         image.width % 2)] = 0
                if not channels["b_v"]:
                    temp_processed_data[height * (3 * image.width // 2 +
                                                  image.width % 2):] = 0
            processed_data = numpy.reshape(
                temp_processed_data[:(height * image.width)],
                (height, image.width)).astype('uint8')
            return_data[:, :, 0] = processed_data
            chromas_data = numpy.reshape(
                temp_processed_data[(height * image.width):height *
                                    (3 * image.width // 2 + image.width % 2)],
                (height, image.width // 2 + image.width % 2)).astype('uint8')
            return_data[:, ::2, 1] = chromas_data
            chromas_data = numpy.reshape(
                temp_processed_data[height *
                                    (3 * image.width // 2 + image.width % 2):],
                (height, image.width // 2)).astype('uint8')
            return_data[:, 1::2, 1] = chromas_data
            if not channels["b_v"] and not channels["g_u"] and channels["r_y"]:
                return_data = cv.cvtColor(return_data[:, :, 0],
                                          cv.COLOR_GRAY2RGB)
            else:
                return_data = self.convert2RGB(temp_processed_data,
                                               image.width, height,
                                               conversion_const)
            tmp.append(return_data)

        return concatenate_frames(tmp)

    def convert2RGB(self, processed_data, width, height, conversion):
        y = processed_data[0:height * width:]
        u = processed_data[height * width:height *
                           (3 * width // 2 + width % 2)]
        v = processed_data[height * (3 * width // 2 + width % 2):]
        yuv = numpy.empty((height * width, 2), dtype=numpy.uint8)
        yuv[:, 0] = y
        yuv[0::2, 1] = u
        yuv[1::2, 1] = v
        rgb = cv.cvtColor(yuv.reshape((height, width, 2)), conversion)
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
