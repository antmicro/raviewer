#!/usr/bin/env python
import cv2 as cv
"""Raviewer - terminal functionality."""

import argparse
import os
from .core import (save_image_as_file, get_displayable, load_image)
from .image.color_format import AVAILABLE_FORMATS
from .gui import MainWindow

parser = argparse.ArgumentParser(
    prog=__package__,
    description="preview raw data as an image of chosen format")

parser.add_argument("-f",
                    "--FILE_PATH",
                    help="file containing raw image data",
                    default=None)

parser.add_argument("-c",
                    "--color_format",
                    choices=AVAILABLE_FORMATS.keys(),
                    default=list(AVAILABLE_FORMATS.keys())[0],
                    help="target color format (default: %(default)s)")

parser.add_argument("-w",
                    "--width",
                    metavar=("width"),
                    type=int,
                    default=800,
                    help="target width (default: %(default)s)")

parser.add_argument(
    "-e",
    "--export",
    metavar="RESULT_PATH",
    help="destination file for parsed image, and it's extension")

args = vars(parser.parse_args())

if isinstance(args["FILE_PATH"], str):
    if not os.path.isfile(args["FILE_PATH"]):
        raise Exception("Given path does not lead to a file")

if args["export"] is None:
    app = MainWindow(args)
    app.run_gui()
else:
    img = load_image(args["FILE_PATH"], args["color_format"], args["width"])
    save_image_as_file(get_displayable(img), args["export"])
