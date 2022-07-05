"""Parser implementation for YUV pixel format"""

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


class ParserYUV420(AbstractParser):
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

        data_array = []
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
        data_array = numpy.frombuffer(self.reverse(raw_data, reverse_bytes),
                                      dtype=curr_dtype)
        processed_data = numpy.array(data_array, dtype=curr_dtype)
        if (processed_data.size % width != 0):
            processed_data = numpy.concatenate(
                (processed_data,
                 numpy.zeros(width - (processed_data.size % width))))

        new_height = math.ceil(math.ceil(processed_data.size / width) / 1.5)
        return Image(raw_data, color_format, processed_data, width, new_height)

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
        return_data = image.processed_data
        conversion_const = None
        if height < 1: height = image.height
        n_frames = 0 if image.height == 0 else math.ceil(image.height / height)
        for i in range(n_frames):
            return_data = image.processed_data[i * image.width *
                                               int(height * 1.5):(1 + i) *
                                               image.width * int(height * 1.5)]
            if image.color_format.pixel_format == PixelFormat.YUV:
                conversion_const = cv.COLOR_YUV2RGB_NV12
                if not channels["r_y"]:
                    return_data[0:image.width * height] = 0
                if not channels["g_u"]:
                    return_data[image.width * height::2] = 0
                if not channels["b_v"]:
                    return_data[image.width * height + 1::2] = 0
                if not channels["b_v"] and not channels["g_u"] and channels[
                        "r_y"]:
                    return_data = return_data[0:image.width * height]
                    conversion_const = cv.COLOR_GRAY2RGB
            elif image.color_format.pixel_format == PixelFormat.YVU:
                conversion_const = cv.COLOR_YUV2RGB_NV21
                if not channels["r_y"]:
                    return_data[0:image.width * height] = 0
                if not channels["g_u"]:
                    return_data[image.width * height + 1::2] = 0
                if not channels["b_v"]:
                    return_data[image.width * height::2] = 0
                if not channels["b_v"] and not channels["g_u"] and channels[
                        "r_y"]:
                    return_data = return_data[0:image.width * height]
                    conversion_const = cv.COLOR_GRAY2RGB

            data_array = numpy.reshape(return_data, (int(
                return_data.size / image.width), image.width)).astype('uint8')

            if conversion_const != cv.COLOR_GRAY2RGB:
                if (data_array.shape[0] % 3 != 0):
                    data_array = numpy.concatenate(
                        (data_array,
                         numpy.zeros(
                             (3 -
                              (data_array.shape[0] % 3), data_array.shape[1]),
                             dtype=numpy.uint8)))
                if (data_array.shape[1] % 2 != 0):
                    data_array = numpy.concatenate(
                        (data_array,
                         numpy.zeros(
                             (data_array.shape[0], 1), dtype=numpy.uint8)),
                        axis=1)

            return_data = cv.cvtColor(data_array, conversion_const)
            tmp.append(return_data)
        return numpy.array([]) if tmp == [] else numpy.concatenate(tmp, axis=0)

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
        tmp = []
        if height < 1: height = image.height
        n_frames = 0 if image.height == 0 else math.ceil(
            len(image.processed_data) / image.width / height / 1.5)
        for i in range(n_frames):
            return_data = image.processed_data[int(height * 1.5) *
                                               image.width * i:(1 + i) *
                                               image.width * int(height * 1.5)]

            conversion_const = None
            if image.color_format.pixel_format == PixelFormat.YUV:
                conversion_const = cv.COLOR_YUV2RGB_I420
                if not channels["r_y"]:
                    return_data[0:image.width * height] = 0
                if not channels["g_u"]:
                    return_data[image.width * height + 1:image.width * height +
                                image.width * height // 4] = 0
                if not channels["b_v"]:
                    return_data[image.width * height +
                                image.width * height // 4:] = 0
                if not channels["b_v"] and not channels["g_u"] and channels[
                        "r_y"]:
                    return_data = return_data[0:height * image.width]
                    conversion_const = cv.COLOR_GRAY2RGB

            elif image.color_format.pixel_format == PixelFormat.YVU:
                conversion_const = cv.COLOR_YUV2RGB_YV12
                if not channels["r_y"]:
                    return_data[0:image.width * height] = 0
                if not channels["g_u"]:
                    return_data[image.width * height +
                                image.width * height // 4:] = 0
                if not channels["b_v"]:
                    return_data[image.width * height + 1:image.width * height +
                                image.width * height // 4] = 0
                if not channels["b_v"] and not channels["g_u"] and channels[
                        "r_y"]:
                    return_data = return_data[0:height * image.width]
                    conversion_const = cv.COLOR_GRAY2RGB

            data_array = numpy.reshape(return_data, (int(
                return_data.size / image.width), image.width)).astype('uint8')
            if conversion_const != cv.COLOR_GRAY2RGB:
                if (data_array.shape[0] % 3 != 0):
                    data_array = numpy.concatenate(
                        (data_array,
                         numpy.zeros(
                             (3 -
                              (data_array.shape[0] % 3), data_array.shape[1]),
                             dtype=numpy.uint8)))
                if (data_array.shape[1] % 2 != 0):
                    data_array = numpy.concatenate(
                        (data_array,
                         numpy.zeros(
                             (data_array.shape[0], 1), dtype=numpy.uint8)),
                        axis=1)
            tmp.append(cv.cvtColor(data_array, conversion_const))
        return numpy.array([]) if tmp == [] else numpy.concatenate(tmp, axis=0)

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

        data_array = numpy.frombuffer(self.reverse(raw_data, reverse_bytes),
                                      dtype=curr_dtype)
        processed_data = numpy.array(data_array, dtype=curr_dtype)

        if (processed_data.size % (width * 2) != 0):
            processed_data = numpy.concatenate(
                (processed_data,
                 numpy.zeros((width * 2) - (processed_data.size %
                                            (width * 2)))))

        return Image(raw_data, color_format, processed_data, width,
                     processed_data.size // (width * 2))

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
            if not channels["r_y"]:
                temp_processed_data[self.yuv_442_offsets[
                    image.color_format.pixel_format]["Y"]::2] = 0
            if not channels["g_u"]:
                temp_processed_data[self.yuv_442_offsets[
                    image.color_format.pixel_format]["U"]::4] = 0
            if not channels["b_v"]:
                temp_processed_data[self.yuv_442_offsets[
                    image.color_format.pixel_format]["V"]::4] = 0

            return_data = numpy.reshape(
                temp_processed_data.copy(),
                (height, image.width, 2)).astype('uint8')
            conversion_const = None
            if image.color_format.pixel_format == PixelFormat.YUYV:
                conversion_const = cv.COLOR_YUV2RGB_YUYV
            elif image.color_format.pixel_format == PixelFormat.UYVY:
                conversion_const = cv.COLOR_YUV2RGB_UYVY
            elif image.color_format.pixel_format == PixelFormat.YVYU:
                conversion_const = cv.COLOR_YUV2RGB_YVYU
            elif image.color_format.pixel_format == PixelFormat.VYUY:
                conversion_const = cv.COLOR_YUV2RGB_UYVY

            if not channels["b_v"] and not channels["g_u"] and channels["r_y"]:
                return_data = cv.cvtColor(return_data[:, :, 0],
                                          cv.COLOR_GRAY2RGB)
            else:
                return_data = self.convert2RGB(temp_processed_data,
                                               image.width, height,
                                               conversion_const, image)
            tmp.append(return_data)
        return numpy.array([]) if tmp == [] else numpy.concatenate(tmp, axis=0)

    def convert2RGB(self, processed_data, width, height, conversion, image):
        y = processed_data[self.yuv_442_offsets[image.color_format.
                                                pixel_format]["Y"]::2]
        u = processed_data[self.yuv_442_offsets[image.color_format.
                                                pixel_format]["U"]::4]
        v = processed_data[self.yuv_442_offsets[image.color_format.
                                                pixel_format]["V"]::4]
        u = numpy.resize(numpy.array([x for x in u for _ in (0, 1)]), len(y))
        v = numpy.resize(numpy.array([x for x in v for _ in (0, 1)]), len(y))
        plane_y = y.reshape((height, width, 1))
        plane_u = u.reshape((height, width, 1))
        plane_v = v.reshape((height, width, 1))
        yuv = numpy.concatenate((plane_y, plane_u, plane_v),
                                axis=2).astype('uint8')
        rgb = cv.cvtColor(yuv, cv.COLOR_YUV2RGB)
        return rgb

    def get_pixel_raw_components(self, image, row, column, index):
        return image.processed_data[(index // 2) * 4:(index // 2) * 4 + 4]

    def crop_image2rawformat(self, image, up_row, down_row, left_column,
                             right_column):
        return_data = numpy.reshape(
            image.processed_data.astype(numpy.byte),
            (image.height, len(image.processed_data) // image.height))
        return return_data[up_row:down_row, left_column * 2:right_column * 2]


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
            return_data = numpy.zeros((height, image.width, 2)).astype('uint8')
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
            data_array = numpy.reshape(
                temp_processed_data[:(height * image.width)],
                (height, image.width)).astype('uint8')
            return_data[:, :, 0] = data_array
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
        return numpy.array([]) if tmp == [] else numpy.concatenate(tmp, axis=0)

    def convert2RGB(self, processed_data, width, height, conversion):
        y = processed_data[0:height * width:]
        u = processed_data[height * width:height *
                           (3 * width // 2 + width % 2)]
        v = processed_data[height * (3 * width // 2 + width % 2):]

        u = numpy.resize(numpy.array([x for x in u for _ in (0, 1)]), len(y))
        v = numpy.resize(numpy.array([x for x in v for _ in (0, 1)]), len(y))
        plane_y = y.reshape((height, width, 1))
        plane_u = u.reshape((height, width, 1))
        plane_v = v.reshape((height, width, 1))
        yuv = numpy.concatenate((plane_y, plane_u, plane_v),
                                axis=2).astype('uint8')
        rgb = cv.cvtColor(yuv, cv.COLOR_YUV2RGB)
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
