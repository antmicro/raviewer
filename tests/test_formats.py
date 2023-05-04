"""Module for testing formats on resources entities"""

from raviewer.src.core import (get_displayable, load_image, parse_image)
from raviewer.image.color_format import AVAILABLE_FORMATS
from raviewer.src.utils import save_image_as_file
import pytest
import importlib.resources
import numpy
import cv2 as cv
import os
from datetime import datetime


def perform_check(image, ref, tolerance, dir, blur=False):
    """Compares pixelwise differences between images

    Keyword arguments:

        image: numpy ndarray representing first image to compare
        ref: numpy ndarray - second image with the same size as image
        tolerance: maximal accepted difference
        dir: string specifying logging directory
        blur: if set to True images are blurred before comparison

    Returns: True if test was passed
    """
    if blur:
        ref = cv.blur(ref, (3, 3))
        image = cv.blur(image, (3, 3))
        blur_suffix = "Blur"
    else:
        blur_suffix = ""

    diff = numpy.array(cv.absdiff(ref, image), dtype=numpy.uint8)
    diff = numpy.where(diff <= tolerance, numpy.uint8(0), numpy.uint8(255))

    if numpy.max(diff) != 0:
        diff = numpy.bitwise_or.reduce(diff, axis=2)
        errorImage = cv.cvtColor(diff, cv.COLOR_GRAY2BGR)
        if not os.path.exists(dir):
            os.makedirs(dir)
        cv.imwrite(os.path.join(dir, f"difference{blur_suffix}.png"),
                   errorImage)
        save_image_as_file(image,
                           os.path.join(dir, f"parsedImage{blur_suffix}.png"))
        save_image_as_file(ref, os.path.join(dir,
                                             f"reference{blur_suffix}.png"))
        return False
    return True


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

    try:
        f = importlib.resources.files('resources').joinpath(
            f'{fmt}_{width}_{height}')
        img = load_image(f)
    except FileNotFoundError:
        pytest.skip(
            f"Raw image for format {fmt} not found in resources directory")

    parsed_img = parse_image(img.data_buffer, fmt, width)
    displayable_img = get_displayable(parsed_img)
    try:
        with importlib.resources.files('resources').joinpath(
                os.path.join('test_reference',
                             f"{fmt}_{width}_{height}")).open('rb') as f:
            reference = numpy.fromfile(f, dtype='u1').reshape(
                (height, width, -1))
    except FileNotFoundError:
        pytest.skip(
            f"Exemplar parsed image for format {fmt} not found in resources/test_reference directory"
        )

    assert displayable_img.shape == reference.shape, "Shape of the parsed image does not match shape of reference image"
    tolerance = 8
    cur_time = datetime.now().strftime('%Y%m%d%H%M')
    dir = os.path.join("tests", "logs", f"{fmt}_{cur_time}")
    blur = False
    if preprocess == 'blur':
        blur = True
    assert perform_check(displayable_img, reference, tolerance, dir,
                         blur), "Images differ. Check logs for details"
