"""Module for testing formats on resources entities"""

from raviewer.src.core import (get_displayable, load_image, parse_image)
from raviewer.image.image import Image
from raviewer.image.color_format import AVAILABLE_FORMATS
import pytest


@pytest.mark.parametrize('fmt', AVAILABLE_FORMATS.keys())
@pytest.mark.parametrize('width', range(4, 8))
@pytest.mark.parametrize('height', range(8))
def test_format_conversion(fmt, width, height):
    """Test format"""
    img = Image(bytearray([0] * 64))
    parsed_img = parse_image(img.data_buffer, fmt, width, height)
    get_displayable(parsed_img)
