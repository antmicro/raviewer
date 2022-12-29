#!/usr/bin/env python
"""Raviewer - terminal functionality."""

try:
    GUI = True

    #since dearpygui>0.8.64
    import dearpygui.dearpygui as dpg
    dpg.create_context()

    from .gui.gui_init import AppInit
except ImportError:
    GUI = False

import argparse
import os
import sys
import logging
from .src.core import (get_displayable, load_image, parse_image)
from .src.utils import save_image_as_file
from .image.color_format import AVAILABLE_FORMATS
from tests import test_formats


def list_formats():
    '''Print all supported formats'''
    for f in AVAILABLE_FORMATS.keys():
        print(f)


def check_formats():
    test_formats.test_all(AVAILABLE_FORMATS)


def run(file_path, width, height, color_format, export, args):
    if args["software_rendering"]:
        # These variables are needed to force OpenGL software rendering
        # Deleting textures causes segfaults when rendering with NVIDIA GPU
        # See: https://github.com/hoffstadt/DearPyGui/issues/1371
        os.environ['__GLX_VENDOR_LIBRARY_NAME'] = 'mesa'
        os.environ['LIBGL_ALWAYS_SOFTWARE'] = 'true'

    log_level = logging.DEBUG if args["debug"] else logging.WARNING
    logging.basicConfig(level=log_level,
                        format="%(asctime)s - %(levelname)s - %(message)s")

    if export is None:
        if not GUI:
            print("Raviewer was installed in no-gui mode")
            sys.exit(1)

        app = AppInit(args)
        app.run_gui()
    else:
        '''
        if a given path represents an existing directory - save image in that directory with the same name as input file (but ending with .png")
        if os.path.dirname(export) (everything exept for last component of the path) represents an existing directory - append ".png" (if needed) and save the image
        otherwise - raise an exception
        '''
        if not export.endswith(".png"):
            if os.path.isdir(export):
                export = os.path.join(export,
                                      os.path.basename(file_path)) + ".png"
            elif os.path.isdir(os.path.dirname(export)):
                export += ".png"
            else:
                raise FileNotFoundError(
                    "{} - no such file or directory".format(export))
        elif not os.path.isdir(os.path.dirname(export)):
            raise FileNotFoundError(
                "{} - no such file or directory".format(export))
        img = load_image(file_path)
        img = parse_image(img.data_buffer, color_format, width)
        if height < 1: height = img.height
        save_image_as_file(get_displayable(img, height), export)


def main():
    parser = argparse.ArgumentParser(
        prog=__package__,
        description="Preview raw data as an image of chosen format")

    parser.add_argument("-f",
                        "--FILE_PATH",
                        help="File containing raw image data",
                        default=None)

    parser.add_argument("-c",
                        "--color_format",
                        default=list(AVAILABLE_FORMATS.keys())[0],
                        help="Target color format (default: %(default)s)")

    parser.add_argument("-w",
                        "--width",
                        metavar=("width"),
                        type=int,
                        default=800,
                        help="Target width (default: %(default)s)")

    parser.add_argument("-e",
                        "--export",
                        metavar="RESULT_PATH",
                        help="Destination file for parsed image")

    parser.add_argument('--list-formats',
                        action='store_true',
                        help='Available predefined formats')

    parser.add_argument('--check-formats',
                        action='store_true',
                        help='Test all formats')

    parser.add_argument('-H',
                        '--height',
                        type=int,
                        default=0,
                        help="Image height")

    parser.add_argument("--software-rendering",
                        action=argparse.BooleanOptionalAction,
                        default=True,
                        help="Use OpenGL software rendering"),

    parser.add_argument('--debug',
                        action=argparse.BooleanOptionalAction,
                        default=False,
                        help="Turn on/off debug mode")

    args = vars(parser.parse_args())

    if isinstance(args["FILE_PATH"], str):
        if not os.path.isfile(args["FILE_PATH"]):
            raise Exception("Given path does not lead to a file")

    if args["list_formats"]:
        list_formats()
    elif args["check_formats"]:
        check_formats()
    else:
        run(file_path=args["FILE_PATH"],
            width=args["width"],
            color_format=args["color_format"],
            export=args["export"],
            height=args["height"],
            args=args)


if __name__ == "__main__":
    sys.exit(main())
