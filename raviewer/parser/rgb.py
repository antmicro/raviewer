"""Parser implementation for RGBA pixel format"""

from ..image.color_format import PixelFormat, Endianness
from ..image.image import Image
from .common import AbstractParser

import numpy
import cv2 as cv


class ParserRGBA(AbstractParser):
    """An RGB/BGR implementation of a parser - ALPHA LAST"""

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
        return_data = numpy.reshape(image.processed_data.astype('uint8'),
                                    (image.height, image.width, 4))

        bpcs = 4
        cbits = image.color_format.bits_per_components

        if image.color_format.bits_per_components[3] == 0:
            bpcs = 3
        for i in range(bpcs):
            if cbits[i] != 8:
                coeff = 255 / (2**cbits[i] - 1)
                numpy.multiply(return_data[:, :, i],
                               coeff,
                               out=return_data[:, :, i],
                               casting="unsafe")
        if image.color_format.bits_per_components[3] == 0:
            return_data[:, :, 3] = numpy.uint8(255)

        if image.color_format.pixel_format in [
                PixelFormat.BGRA, PixelFormat.BGR
        ]:
            return_data = return_data[:, :, [2, 1, 0, 3]]

        #Set RGB channels
        if not channels["r_y"]:
            return_data[:, :, 0] = 0
        if not channels["g_u"]:
            return_data[:, :, 1] = 0
        if not channels["b_v"]:
            return_data[:, :, 2] = 0
        if not channels["a_v"]:
            return_data[:, :, 3] = 255
        return return_data

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


class ParserARGB(AbstractParser):
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

        return_data = numpy.reshape(image.processed_data.astype('uint8'),
                                    (image.height, image.width, 4))
        cbits = image.color_format.bits_per_components
        bpcs = 4
        cbits = image.color_format.bits_per_components

        if image.color_format.bits_per_components[3] == 0:
            bpcs = 3
        for i in range(bpcs):
            if cbits[i] != 8:
                coeff = 255 / (2**cbits[i] - 1)
                numpy.multiply(return_data[:, :, i],
                               coeff,
                               out=return_data[:, :, i],
                               casting="unsafe")
        if image.color_format.bits_per_components[3] == 0:
            return_data[:, :, 3] = numpy.uint8(255)

        if image.color_format.pixel_format == PixelFormat.ABGR:
            return_data = return_data[:, :, [3, 2, 1, 0]]
        else:
            return_data = return_data[:, :, [1, 2, 3, 0]]

        #Set ARGB channels
        if not channels["r_y"]:
            return_data[:, :, 0] = 0
        if not channels["g_u"]:
            return_data[:, :, 1] = 0
        if not channels["b_v"]:
            return_data[:, :, 2] = 0
        if not channels["a_v"]:
            return_data[:, :, 3] = 255

        return return_data

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
