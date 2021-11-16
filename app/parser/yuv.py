"""Parser implementation for YUV pixel format"""

from ..image.color_format import PixelFormat
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


class ParserYUV420(AbstractParser):
    """A semi-planar YUV420 implementation of a parser"""
    def parse(self, raw_data, color_format, width):
        """Parses provided raw data to an image, calculating height from provided width.

        Keyword arguments:

            raw_data: bytes object
            color_format: target instance of ColorFormat
            width: target width to interpret

        Returns: instance of Image processed to chosen format
        """

        max_value = max(color_format.bits_per_components)
        curr_dtype = numpy.uint8

        data_array = []
        if len(set(
                color_format.bits_per_components)) == 2 and max_value % 8 == 0:
            raw_data = bytearray(raw_data)
            if len(raw_data) % numpy.dtype(curr_dtype).alignment != 0:
                raw_data += (0).to_bytes(len(raw_data) %
                                         numpy.dtype(curr_dtype).alignment,
                                         byteorder="little")
            data_array = numpy.frombuffer(raw_data, dtype=curr_dtype)
        else:
            raise NotImplementedError(
                "Other than 8-bit YUVs are not currently supported")

        processed_data = numpy.array(data_array, dtype=curr_dtype)

        if (processed_data.size % width != 0):
            processed_data = numpy.concatenate(
                (processed_data,
                 numpy.zeros(width - (processed_data.size % width))))

        new_height = normal_round(math.ceil(processed_data.size / width) / 1.5)
        return Image(raw_data, color_format, processed_data, width, new_height)

    def get_displayable(self, image, channels):
        """Provides displayable image data (RGB formatted)

        Returns: Numpy array containing displayable data.
        """
        return_data = image.processed_data
        conversion_const = None
        if image.color_format.pixel_format == PixelFormat.YUV:
            conversion_const = cv.COLOR_YUV2RGB_NV12
            if not channels["r_y"]:
                return_data[0:image.width * image.height] = 0
            if not channels["g_u"]:
                return_data[image.width * image.height::2] = 0
            if not channels["b_v"]:
                return_data[image.width * image.height + 1::2] = 0
            if not channels["b_v"] and not channels["g_u"] and channels["r_y"]:
                conversion_const = cv.COLOR_GRAY2RGB
        elif image.color_format.pixel_format == PixelFormat.YVU:
            conversion_const = cv.COLOR_YUV2RGB_NV21
            if not channels["r_y"]:
                return_data[0:image.width * image.height] = 0
            if not channels["g_u"]:
                return_data[image.width * image.height + 1::2] = 0
            if not channels["b_v"]:
                return_data[image.width * image.height::2] = 0
            if not channels["b_v"] and not channels["g_u"] and channels["r_y"]:
                conversion_const = cv.COLOR_GRAY2RGB

        data_array = numpy.reshape(
            return_data,
            (int(return_data.size / image.width), image.width)).astype('uint8')

        if (data_array.shape[0] % 3 != 0):
            data_array = numpy.concatenate(
                (data_array,
                 numpy.zeros(
                     (3 - (data_array.shape[0] % 3), data_array.shape[1]),
                     dtype=numpy.uint8)))
        if (data_array.shape[1] % 2 != 0):
            data_array = numpy.concatenate(
                (data_array,
                 numpy.zeros((data_array.shape[0], 1), dtype=numpy.uint8)),
                axis=1)

        return_data = cv.cvtColor(data_array, conversion_const)
        return return_data

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
        u = [x for x in u for _ in (0, 1)]
        u = numpy.array(u)
        u = numpy.reshape(u.astype('uint8'), (image.height // 2, image.width))
        u = u[up_row // 2:down_row // 2, left_column:right_column:2]

        v = [x for x in v for _ in (0, 1)]
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


class ParserYUV420Planar(ParserYUV420):
    """A planar YUV420 implementation of a parser"""
    def get_displayable(self, image, channels):
        """Provides displayable image data (RGB formatted)

        Returns: Numpy array containing displayable data.
        """
        return_data = image.processed_data

        conversion_const = None
        if image.color_format.pixel_format == PixelFormat.YUV:
            conversion_const = cv.COLOR_YUV2RGB_I420
            if not channels["r_y"]:
                return_data[0:image.width * image.height] = 0
            if not channels["g_u"]:
                return_data[image.width * image.height +
                            1:image.width * image.height +
                            image.width * image.height // 4] = 0
            if not channels["b_v"]:
                return_data[image.width * image.height +
                            image.width * image.height // 4:] = 0
            if not channels["b_v"] and not channels["g_u"] and channels["r_y"]:
                conversion_const = cv.COLOR_GRAY2RGB

        elif image.color_format.pixel_format == PixelFormat.YVU:
            conversion_const = cv.COLOR_YUV2RGB_YV12
            if not channels["r_y"]:
                return_data[0:image.width * image.height] = 0
            if not channels["g_u"]:
                return_data[image.width * image.height +
                            image.width * image.height // 4:] = 0
            if not channels["b_v"]:
                return_data[image.width * image.height +
                            1:image.width * image.height +
                            image.width * image.height // 4] = 0
            if not channels["b_v"] and not channels["g_u"] and channels["r_y"]:
                conversion_const = cv.COLOR_GRAY2RGB

        data_array = numpy.reshape(
            return_data,
            (int(return_data.size / image.width), image.width)).astype('uint8')

        if (data_array.shape[0] % 3 != 0):
            data_array = numpy.concatenate(
                (data_array,
                 numpy.zeros(
                     (3 - (data_array.shape[0] % 3), data_array.shape[1]),
                     dtype=numpy.uint8)))
        if (data_array.shape[1] % 2 != 0):
            data_array = numpy.concatenate(
                (data_array,
                 numpy.zeros((data_array.shape[0], 1), dtype=numpy.uint8)),
                axis=1)

        return_data = cv.cvtColor(data_array, conversion_const)
        return return_data

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
        u = [x for x in u for _ in (0, 1)]
        u = numpy.array(u)
        u = numpy.reshape(u.astype('uint8'), (image.height // 2, image.width))
        u = u[up_row // 2:(down_row // 2) + 1, left_column:right_column:2]
        u = u.flatten()
        v = numpy.array(image.processed_data[image.width * image.height +
                                             image.width * image.height // 4:])
        v = [x for x in v for _ in (0, 1)]
        v = numpy.array(v)
        v = numpy.reshape(v.astype('uint8'), (image.height // 2, image.width))
        v = v[up_row // 2:(down_row // 2) + 1, left_column:right_column:2]
        v = v.flatten()
        yuv = numpy.concatenate([
            numpy.array(return_data[up_row:down_row,
                                    left_column:right_column]).flatten(), u, v
        ])
        return yuv


class ParserYUV422(AbstractParser):
    """Respresenation defining YUV component offsets of packed YUV422"""
    yuv_442_offsets = {
        PixelFormat.YUYV: {
            "Y": 0,
            "U": 1,
            "V": 3,
        },
        PixelFormat.UYVY: {
            "Y": 1,
            "U": 0,
            "V": 2,
        },
        PixelFormat.VYUY: {
            "Y": 1,
            "U": 2,
            "V": 0,
        },
        PixelFormat.YVYU: {
            "Y": 0,
            "U": 3,
            "V": 1,
        },
    }
    """A packed YUV422 implementation of a parser"""
    def parse(self, raw_data, color_format, width):
        """Parses provided raw data to an image, calculating height from provided width.
        Keyword arguments:

            raw_data: bytes object
            color_format: target instance of ColorFormat
            width: target width to interpret

        Returns: instance of Image processed to chosen format
        """
        max_value = max(color_format.bits_per_components)
        curr_dtype = numpy.uint8

        data_array = []
        bpcs_set = set(color_format.bits_per_components)
        if len(bpcs_set) == 2 or len(bpcs_set) == 1 and max_value % 8 == 0:
            raw_data = bytearray(raw_data)
            if len(raw_data) % numpy.dtype(curr_dtype).alignment != 0:
                raw_data += (0).to_bytes(len(raw_data) %
                                         numpy.dtype(curr_dtype).alignment,
                                         byteorder="little")
            data_array = numpy.frombuffer(raw_data, dtype=curr_dtype)
        else:
            raise NotImplementedError(
                "Other than 8-bit YUVs are not currently supported")

        processed_data = numpy.array(data_array, dtype=curr_dtype)

        if (processed_data.size % (width * 2) != 0):
            processed_data = numpy.concatenate(
                (processed_data,
                 numpy.zeros((width * 2) - (processed_data.size %
                                            (width * 2)))))

        return Image(raw_data, color_format, processed_data, width,
                     processed_data.size // (width * 2))

    def get_displayable(self, image, channels):
        """Provides displayable image data (RGB formatted)

        Returns: Numpy array containing displayable data.
        """
        if not channels["r_y"]:
            image.processed_data[self.yuv_442_offsets[
                image.color_format.pixel_format]["Y"]::2] = 0
        if not channels["g_u"]:
            image.processed_data[self.yuv_442_offsets[
                image.color_format.pixel_format]["U"]::4] = 0
        if not channels["b_v"]:
            image.processed_data[self.yuv_442_offsets[
                image.color_format.pixel_format]["V"]::4] = 0

        return_data = numpy.reshape(
            image.processed_data.copy(),
            (image.height, image.width, 2)).astype('uint8')
        conversion_const = None
        if image.color_format.pixel_format == PixelFormat.YUYV:
            conversion_const = cv.COLOR_YUV2RGB_YUYV
        elif image.color_format.pixel_format == PixelFormat.UYVY:
            conversion_const = cv.COLOR_YUV2RGB_UYVY
        elif image.color_format.pixel_format == PixelFormat.YVYU:
            conversion_const = cv.COLOR_YUV2RGB_YVYU
        elif image.color_format.pixel_format == PixelFormat.VYUY:
            conversion_const = cv.COLOR_YUV2RGB_UYVY
            temp = numpy.copy(return_data[:, ::2, 0])
            return_data[:, ::2, 0] = return_data[:, 1::2, 0]
            return_data[:, 1::2, 0] = temp

        if not channels["b_v"] and not channels["g_u"] and channels["r_y"]:
            return_data = cv.cvtColor(return_data[:, :, 0], cv.COLOR_GRAY2RGB)
        else:
            return_data = cv.cvtColor(return_data, conversion_const)
        return return_data

    def get_pixel_raw_components(self, image, row, column, index):
        return image.processed_data[(index // 2) * 4:(index // 2) * 4 + 4]

    def crop_image2rawformat(self, image, up_row, down_row, left_column,
                             right_column):
        return_data = numpy.reshape(
            image.processed_data.astype(numpy.byte),
            (image.height, len(image.processed_data) // image.height))
        return return_data[up_row:down_row, left_column * 2:right_column * 2]


class ParserYUV422Planar(ParserYUV422):
    def get_displayable(self, image, channels):
        """Provides displayable image data (RGB formatted)

        Returns: Numpy array containing displayable data.
        """

        return_data = numpy.zeros(
            (image.height, image.width, 2)).astype('uint8')
        conversion_const = None
        if image.color_format.pixel_format == PixelFormat.YUV:
            conversion_const = cv.COLOR_YUV2RGB_YUYV
            if not channels["r_y"]:
                image.processed_data[0:image.height * image.width:] = 0
            if not channels["g_u"]:
                image.processed_data[image.height * image.width:image.height *
                                     (3 * image.width // 2 +
                                      image.width % 2)] = 0
            if not channels["b_v"]:
                image.processed_data[image.height * (3 * image.width // 2 +
                                                     image.width % 2):] = 0

        data_array = numpy.reshape(
            image.processed_data[:(image.height * image.width)],
            (image.height, image.width)).astype('uint8')
        return_data[:, :, 0] = data_array
        chromas_data = numpy.reshape(
            image.processed_data[(image.height * image.width):image.height *
                                 (3 * image.width // 2 + image.width % 2)],
            (image.height, image.width // 2 + image.width % 2)).astype('uint8')
        return_data[:, ::2, 1] = chromas_data
        chromas_data = numpy.reshape(
            image.processed_data[image.height *
                                 (3 * image.width // 2 + image.width % 2):],
            (image.height, image.width // 2)).astype('uint8')
        return_data[:, 1::2, 1] = chromas_data

        if not channels["b_v"] and not channels["g_u"] and channels["r_y"]:
            return_data = cv.cvtColor(return_data[:, :, 0], cv.COLOR_GRAY2RGB)
        else:
            return_data = cv.cvtColor(return_data, conversion_const)
        return return_data

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
        u = [x for x in u for _ in (0, 1)]
        u = numpy.array(u)
        u = numpy.reshape(u.astype('uint8'), (image.height, image.width))
        u = u[up_row:down_row, left_column:right_column:2]
        u = u.flatten()

        v = numpy.array(
            image.processed_data[image.height *
                                 (3 * image.width // 2 + image.width % 2):])
        v = [x for x in v for _ in (0, 1)]
        v = numpy.array(v)
        v = numpy.reshape(v.astype('uint8'), (image.height, image.width))
        v = v[up_row:down_row, left_column:right_column:2]
        v = v.flatten()
        yuv = numpy.concatenate([
            numpy.array(return_data[up_row:down_row,
                                    left_column:right_column]).flatten(), u, v
        ])
        return yuv
