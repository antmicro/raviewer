"""Main functionalities."""

from .image.image import (Image, RawDataContainer)
from .image.color_format import AVAILABLE_FORMATS
from .parser.factory import ParserFactory
import cv2 as cv
import os


def load_image(file_path, color_format, width):
    try:
        image = Image.from_file(file_path)
        parser = ParserFactory.create_object(
            determine_color_format(color_format))
    except Exception as e:
        print(type(e).__name__, e)

    image = parser.parse(image.data_buffer,
                         determine_color_format(color_format), resolution[0],
                         resolution[1])
    return image


def get_displayable(image):

    if image.color_format is None:
        raise Exception("Image should be already parsed!")
    parser = ParserFactory.create_object(image.color_format)

    return parser.get_displayable(image)


def determine_color_format(format_string):

    if format_string in AVAILABLE_FORMATS.keys():
        return AVAILABLE_FORMATS[format_string]
    else:
        raise NotImplementedError(
            "Provided string is not name of supported format.")


def save_image_as_file(image, file_path):

    directory = file_path.replace('\\', '/')
    if directory.rfind('/') == -1:
        directory = './'
    else:
        directory = directory[:directory.rfind("/")]

    if not os.path.isdir(directory):
        os.makedirs(directory)

    try:
        cv.imwrite(file_path, cv.cvtColor(image, cv.COLOR_RGB2BGR))
    except Exception as e:
        print(type(e).__name__, e)
