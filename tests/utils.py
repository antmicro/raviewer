from raviewer.src.utils import save_image_as_file
from raviewer.src.core import load_image
from raviewer.image.image import Image
import os
import importlib.resources
import numpy
import cv2 as cv
import pytest


def perform_check(image, ref, tolerance, dir=None, blur=False):
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
        if not dir:
            return False

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


def resource_image(fmt: str, width: int, height: int) -> Image:
    """Loads image from `resources` directory.

    Keyword arguments:

        fmt: format of the image
        width: width of the image
        height: height of the image

    Returns: packed image into a custom image representation
    """
    try:
        f = importlib.resources.files('resources') / f'{fmt}_{width}_{height}'
        return load_image(f)
    except FileNotFoundError:
        pytest.skip(
            f"Raw image for format {fmt} not found in resources directory")


def resource_image_reference(fmt: str, width: int,
                             height: int) -> numpy.ndarray:
    """Loads reference for an image.

    Keyword arguments:

        fmt: format of the image
        width: width of the image
        height: height of the image

    Returns: numpy image representation
    """
    try:
        path = importlib.resources.files('resources') / 'test_reference'
        path /= f"{fmt}_{width}_{height}"
        with path.open('rb') as f:
            return numpy.fromfile(f, dtype='u1').reshape((height, width, -1))
    except FileNotFoundError:
        pytest.skip(
            f"Exemplar parsed image for format {fmt} not found in resources/test_reference directory"
        )
