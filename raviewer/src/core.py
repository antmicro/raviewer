"""Main format functionalities dispatcher based on factory pattern."""

from ..image.image import Image
from ..parser.factory import ParserFactory
from .utils import determine_color_format
from ..image.color_format import PixelFormat, PixelPlane

import numpy as np
from pyrav4l2 import Stream


def parse_image(data_buffer, color_format, width, reverse_bytes=0):
    try:
        image = Image(data_buffer)
        parser = ParserFactory.create_object(
            determine_color_format(color_format))
    except Exception as e:
        print(type(e).__name__, e)
    #Stride image
    image = parser.parse(image.data_buffer,
                         determine_color_format(color_format), width,
                         reverse_bytes)

    return image


def load_image(file_path):
    with open(file_path, 'rb') as f:
        data_buffer = bytearray(f.read())
    image = Image(data_buffer)
    return image


def load_from_camera(camera, num_of_frames):
    frames = bytearray()
    for (i, frame) in enumerate(Stream(camera)):
        if i == num_of_frames:
            break
        frames += frame

    return Image(frames)


def get_displayable(image,
                    height=0,
                    channels={
                        "r_y": True,
                        "g_u": True,
                        "b_v": True,
                        "a_v": True
                    },
                    raw=False):
    if image.color_format is None:
        raise Exception("Image should be already parsed!")
    parser = ParserFactory.create_object(image.color_format)

    if image.color_format.pixel_format == PixelFormat.MONO:
        return parser.get_displayable(image)
    elif image.color_format.pixel_plane in [
            PixelPlane.SEMIPLANAR, PixelPlane.PLANAR
    ]:
        return parser.get_displayable(image, height, channels=channels)
    elif image.color_format.pixel_format == PixelFormat.BAYER_RG:
        return parser.get_displayable(image,
                                      channels=channels,
                                      debayer=(not raw))
    else:
        return parser.get_displayable(image, channels=channels)


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


def align_image(data_buffer, nnumber, nvalues=0, frame_num=1):
    """ Add or skip data at the beginning of every frame in the data
    Keyword arguments:
        data_buffer (bytearray): byte array containing raw image data
        nnumber (int): number of bytes to append (or skip)
        nvalues (int): value of bytes to append
        frame_num (int): number of frames
    Returns:
        bytearray: aligned buffer
    """

    raw_data = np.array(data_buffer)
    frames = np.array_split(raw_data, frame_num)
    new_frames = [None] * len(frames)

    if nnumber > 0:
        values_to_insert = np.repeat(nvalues, nnumber)
        for i, frame in enumerate(frames):
            new_frames[i] = np.insert(frame, 0, values_to_insert)
    else:
        frame_len = len(raw_data) // frame_num
        if abs(nnumber) > frame_len:
            return
        for i, frame in enumerate(frames):
            new_frames[i] = frame[abs(nnumber):]

    return bytearray(np.concatenate(new_frames).tobytes())
