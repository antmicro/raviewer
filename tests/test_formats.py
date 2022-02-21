"""Module for testing formats on resources entities"""

from raviewer.src.core import (get_displayable, load_image, parse_image)
from terminaltables import AsciiTable
from raviewer.image.color_format import AVAILABLE_FORMATS
import os
import pkg_resources
import time
import pytest


@pytest.fixture
def formats():
    return AVAILABLE_FORMATS


def test_all(formats):
    """Test all formats"""
    print("Testing all formats, It may take a while...")
    table_data = [["Format", "Passed", "Performance"]]
    start_range = 800
    end_range = 810
    for color_format in formats.keys():
        file_path = pkg_resources.resource_filename('resources',
                                                    color_format + "_1000_750")
        passed_results = 0
        format_performance = 0
        start = time.time()
        for width in range(start_range, end_range):
            try:
                if not os.path.exists(file_path):
                    break
                img = load_image(file_path)
                img = parse_image(img.data_buffer, color_format, width)
                get_displayable(img)
                passed_results += 1
            except:
                continue
        end = time.time()
        #Stats
        format_performance = "{:.3f}".format(round(end - start, 3))
        table_data.append([
            color_format, "{}/{}".format(passed_results,
                                         end_range - start_range),
            format_performance
        ])

    table = AsciiTable(table_data)
    table.title = 'Test all formats'
    print(table.table)
