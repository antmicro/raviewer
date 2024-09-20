"""Module for testing formats on resources entities"""

from raviewer.src.core import get_displayable, parse_image
from raviewer.image.color_format import AVAILABLE_FORMATS
from .utils import perform_check, resource_image, resource_image_reference
import pytest
import os
from datetime import datetime


@pytest.mark.parametrize('fmt', AVAILABLE_FORMATS.keys())
@pytest.mark.parametrize('preprocess', [None, 'blur'])
def test_conversion_correctness(fmt, preprocess, width=1000, height=750):
    """Loads and parses image of specifed format, then compares it to corresponding reference image

    Keyword arguments:

        fmt: string specifying image format, must be a key in AVAILABLE_FORMATS
        preprocess: Union[None, string] if set to 'blur' images are blurred before comparison
        width: width of image
        height: height of image
    """
    img = resource_image(fmt, width, height)
    reference = resource_image_reference(fmt, width, height)

    parsed_img = parse_image(img.data_buffer, fmt, width)
    displayable_img = get_displayable(parsed_img)

    assert displayable_img.shape == reference.shape, "Shape of the parsed image does not match shape of reference image"
    tolerance = 8
    cur_time = datetime.now().strftime('%Y%m%d%H%M')
    dir = os.path.join("tests", "logs", f"{fmt}_{cur_time}")
    blur = preprocess == "blur"
    assert perform_check(displayable_img, reference, tolerance, dir,
                         blur), "Images differ. Check logs for details"
