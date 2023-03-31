'''Tests performance of various parsers'''
import argparse
import timeit
import sys
import os
import re

from raviewer.src.core import load_image, parse_image
from raviewer.image.color_format import AVAILABLE_FORMATS
from raviewer.image.image import Image
from raviewer.src.utils import determine_color_format


def print_result(fmt, width, height, counts, res):
    print(f'{fmt:20} {width:<6} {height:<6}', end='')
    maxcount = max(len(str(max(counts))), len("Runs"))
    for c, r in zip(counts, res):
        print(f' {c:<{maxcount}} {r:<12.6f}', end='')
    print()


def print_header(counts):
    print(f'{"Format":20} {"Width":6} {"Height":6}', end='')
    maxcount = max(len(str(max(counts))), len("Runs"))
    for _ in counts:
        print(f' {"Runs":{maxcount}} {"Result[sec]":12}', end='')
    print()


def main():
    parser = argparse.ArgumentParser(
        prog='Parser performance benchmark script')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '-f',
        '--FILE_PATH',
        help='Path to file, which will be used for benchmarking')
    group.add_argument(
        '-d',
        '--DIRECTORY',
        help='Path to directory, containing files for benchmarking')
    group.add_argument('-r',
                       '--random',
                       action='store_true',
                       help='Use random data for testing')
    group.add_argument(
        '--coverage',
        help=
        'Run dedicated test from specified directory for each supported format'
    )
    parser.add_argument('-s',
                        '--size',
                        default=[1000, 750],
                        nargs=2,
                        type=int,
                        help='Size of image')
    parser.add_argument('-c',
                        '--count',
                        default=[100],
                        nargs='+',
                        type=int,
                        help='Number of repetitions')
    parser.add_argument('-i',
                        '--image_formats',
                        default=AVAILABLE_FORMATS.keys(),
                        nargs='+',
                        help=('List of image formats to be benchmarked. '
                              'By default all supported formats are tested'))
    args = parser.parse_args()

    print_header(args.count)

    if args.DIRECTORY is not None:
        filename_regex = re.compile('([a-zA-Z0-9]+)_([0-9]+)_([0-9]+)')
        files = sorted(os.listdir(args.DIRECTORY))
        files = filter(lambda x: x is not None, map(filename_regex.match,
                                                    files))
        for f in files:
            img = load_image(os.path.join(args.DIRECTORY, f.group(0)))
            fmt = f.group(1)
            width = f.group(2)
            height = f.group(3)
            if fmt not in args.image_formats:
                continue
            t = timeit.Timer(
                lambda: parse_image(img.data_buffer, fmt, int(width)))
            res = map(t.timeit, args.count)
            print_result(fmt, width, height, args.count, res)
        return 0

    if args.coverage is not None:
        for fmt in args.image_formats:
            fmt_name = determine_color_format(fmt).name
            try:
                img = load_image(
                    os.path.join(
                        args.coverage, fmt_name + '_' + str(args.size[0]) +
                        '_' + str(args.size[1])))
                t = timeit.Timer(
                    lambda: parse_image(img.data_buffer, fmt, args.size[0]))
                res = map(t.timeit, args.count)
            except FileNotFoundError:
                res = [float('nan')] * len(args.count)
            print_result(fmt, args.size[0], args.size[1], args.count, res)
        return 0

    if args.FILE_PATH is not None:
        img = load_image(args.FILE_PATH)
    else:
        img = Image(os.urandom(args.size[0] * args.size[1]))

    if args.coverage is None and args.DIRECTORY is None:
        for fmt in args.image_formats:
            t = timeit.Timer(
                lambda: parse_image(img.data_buffer, fmt, args.size[0]))
            res = map(t.timeit, args.count)
            print_result(fmt, args.size[0], args.size[1], args.count, res)
    return 0


if __name__ == '__main__':
    sys.exit(main())
