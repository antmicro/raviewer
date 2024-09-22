"""Module for testing resizing on resources entities"""
from raviewer.image.color_format import AVAILABLE_FORMATS
from raviewer.src.core import parse_image, get_displayable, determine_color_format, ParserFactory
from .utils import perform_check, resource_image
import random
import pytest


def _test_resize(func,
                 fmt,
                 preprocess,
                 width=1000,
                 height=750,
                 repetitions=10):
    """Runs a given function multiple times, and then verifies
    whether displayable part has changed"""
    img = resource_image(fmt, width, height)
    reference = resource_image(fmt, width, height)
    reference = parse_image(reference.data_buffer, fmt, width)
    reference = get_displayable(reference)

    for _ in range(repetitions):
        random_width = random.randint(1, width * 2 + 1)
        img = parse_image(img.data_buffer, fmt, random_width)
        func(img)

    # Verify that image has not changed
    img = parse_image(img.data_buffer, fmt, width)
    img = get_displayable(img)
    blur = preprocess == "blur"
    assert perform_check(img, reference, 0, blur=blur)


@pytest.mark.parametrize('fmt', AVAILABLE_FORMATS.keys())
@pytest.mark.parametrize('preprocess', [None, 'blur'])
def test_resize_displayable(fmt,
                            preprocess,
                            width=1000,
                            height=750,
                            repetitions=10):
    """Verifies parsed displayable image against reference"""
    _test_resize(get_displayable, fmt, preprocess, width, height, repetitions)


@pytest.mark.parametrize('fmt', AVAILABLE_FORMATS.keys())
@pytest.mark.parametrize('preprocess', [None, 'blur'])
def test_resize_raw_coloring(fmt,
                             preprocess,
                             width=1000,
                             height=750,
                             repetitions=3):
    """Verifies whether raw coloring of a parsed image works"""
    if fmt == "RGGB":
        pytest.xfail("TO-DO")
    parser = ParserFactory.create_object(determine_color_format(fmt))
    _test_resize(lambda x: parser.raw_coloring(x), fmt, preprocess, width,
                 height, repetitions)
