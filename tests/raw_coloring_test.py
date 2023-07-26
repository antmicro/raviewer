from glob import glob
from os import path
from os.path import basename

import numpy as np
import pytest

from raviewer.image.color_format import AVAILABLE_FORMATS
from raviewer.parser.factory import ParserFactory
from raviewer.src.utils import determine_color_format


@pytest.fixture(params=AVAILABLE_FORMATS.keys())
def test_data(request):
    color_format = determine_color_format(request.param)
    parser = ParserFactory.create_object(color_format)

    image = None
    expected = None

    for name in glob("resources/*"):
        if len(sname := basename(name).strip().split("_")) < 3:
            continue

        cf, width, height, *_ = sname

        try:
            width, height = int(width), int(height)
        except ValueError:
            continue

        if cf != request.param:
            continue

        with open(name, "rb") as f:
            buffer = f.read()

        image = parser.parse(buffer, color_format, width)

        # out = parser.raw_coloring(image)
        # if out is not None:
        #     np.save(path.join("resources/test_reference/", "RAW_%s_%d_%d" % (cf, width, height)), out)

        try:
            expected = np.load(
                path.join("resources/test_reference/",
                          "RAW_%s_%d_%d.npy" % (cf, width, height)))
        except FileNotFoundError:
            pass

        break

    return color_format, parser, image, expected


def test_compare_with_expected(test_data):
    color_format, parser, image, expected = test_data

    if image is None:
        pytest.skip("Couldn't find an image for %s in resources." %
                    color_format.name)

    if expected is None:
        pytest.skip("Couldn't find a reference for %s in test_references." %
                    color_format.name)

    out = parser.raw_coloring(image)

    assert (out == expected).all()
