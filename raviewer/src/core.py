"""Main format functionalities dispatcher based on factory pattern."""

from ..image.image import (Image, RawDataContainer)
from ..parser.factory import ParserFactory
from .utils import determine_color_format
from ..image.color_format import PixelFormat


def load_image(file_path,
               color_format,
               width,
               frame=1,
               n_frames=1,
               reverse_bytes=0):
    try:
        image = Image.from_file(file_path, frame, n_frames)
        parser = ParserFactory.create_object(
            determine_color_format(color_format))
    except Exception as e:
        print(type(e).__name__, e)

    #Stride image
    image = parser.parse(image.data_buffer,
                         determine_color_format(color_format), width,
                         reverse_bytes)

    return image


def get_displayable(image, channels={"r_y": True, "g_u": True, "b_v": True}):

    if image.color_format is None:
        raise Exception("Image should be already parsed!")
    parser = ParserFactory.create_object(image.color_format)

    if image.color_format.pixel_format == PixelFormat.MONO:
        return parser.get_displayable(image)
    else:
        return parser.get_displayable(image, channels)


"""Resolve picked pixel's raw integrants."""


def get_pixel_raw_components(image: Image, row: int, column: int,
                             pixel_index: int):
    """
    Keyword arguments:
        Image: Image instance
        row: row number on the plot
        column: column number on the plot
        pixel_index: relative pixel position from the first one
    """
    parser = ParserFactory.create_object(image.color_format)
    return parser.get_pixel_raw_components(image, row, column, pixel_index)


"""Crop selected area to raw format."""


def crop_image2rawformat(image: Image, up_row: int, down_row: int,
                         left_column: int, right_column: int):
    """
    Keyword arguments:
        Image: Image instance 
        up_row:  position of up row within a selected area
        down_row: position of down row within a selected area
        left_column: position of left column within a selected area
        right_column: position of right column within a selected area.   
    """
    parser = ParserFactory.create_object(image.color_format)
    return parser.crop_image2rawformat(image, up_row, down_row, left_column,
                                       right_column)
