"""Set of general tools used in application."""
import numpy as np
import os
import cv2
from ..image.color_format import AVAILABLE_FORMATS
"""Convert RGB to YUV format values."""


def RGBtoYUV(rgb_format, components_n):
    #The CCIR 601 Standard (now ITU-R 601)
    """Conversion formula
    Y = R *  .299000 + G *  .587000 + B *  .114000
    U = R * -.168736 + G * -.331264 + B *  .500000 + 128
    V = R *  .500000 + G * -.418688 + B * -.081312 + 128
    """
    if components_n == 4:
        rgb_format.pop()
    sub_rgb = np.array([[0.29900, -0.168736, 0.50000],
                        [0.58700, -0.331264, -0.418688],
                        [0.11400, 0.50000, -0.08132]])
    #Matrix formula: rows X columns
    sub_yuv = np.dot(rgb_format, sub_rgb)
    sub_yuv[1:] += 128.0
    yuv_float = sub_yuv.clip(0, 255)
    yuv_int = [int(i) for i in yuv_float]
    return yuv_int


def save_image_as_file(image, file_path):

    directory = file_path.replace('\\', '/')
    if directory.rfind('/') == -1:
        directory = './'
    else:
        directory = directory[:directory.rfind("/")]

    if not os.path.isdir(directory):
        os.makedirs(directory)

    try:
        cv2.imwrite(file_path, image)
    except Exception as e:
        print(type(e).__name__, e)


def determine_color_format(format_string):

    if format_string in AVAILABLE_FORMATS.keys():
        return AVAILABLE_FORMATS[format_string]
    else:
        raise NotImplementedError(
            "Provided string is not name of supported format.")
