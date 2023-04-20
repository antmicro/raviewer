"""Tests performance of various parsers"""
import argparse
import timeit
import sys
import os
import re

from raviewer.src.core import load_image, parse_image
from raviewer.image.color_format import AVAILABLE_FORMATS
from raviewer.image.image import Image
from raviewer.src.utils import determine_color_format


def print_result(fmt, res):
    """Print one row of table with format name and results"""
    print(f'{fmt:20}', end='')
    for r in res:
        print(f' {r:<14.6f}', end='')
    print()


def print_header(sizes):
    """Print header of the table with sizes of test images"""
    print(f'{"Format":20}', end='')
    for i in range(0, len(sizes), 2):
        print(f' {str(sizes[i])+"x"+str(sizes[i+1])+"[sec]":14}', end='')
    print()


def directory_mode(args):
    """Run benchkmark for all files in specified directory"""
    filename_regex = re.compile('([a-zA-Z0-9]+)_([0-9]+)_([0-9]+)')
    files = sorted(os.listdir(args.DIRECTORY))
    files = filter(lambda x: x is not None, map(filename_regex.match,
                                                files))
    for f in files:
        img = load_image(os.path.join(args.DIRECTORY, f.group(0)))
        fmt = f.group(1)
        width = f.group(2)
        if fmt not in args.image_formats:
            continue
        t = timeit.Timer(
            lambda: parse_image(img.data_buffer, fmt, int(width)))
        res = t.timeit(args.count) / args.count
        print_result(fmt, [res])
    return 0


def coverage_mode(args):
    """For each supported format run dedicated test from specified directory"""
    for fmt in args.image_formats:
        fmt_name = determine_color_format(fmt).name
        try:
            img = load_image(
                os.path.join(
                    args.coverage, fmt_name + '_' + str(args.size[0]) +
                    '_' + str(args.size[1])))
            t = timeit.Timer(
                lambda: parse_image(img.data_buffer, fmt, args.size[0]))
            res = t.timeit(args.count) / args.count
        except FileNotFoundError:
            res = [float('nan')] * len(args.count)
        print_result(fmt, [res])
    return 0


def file_mode(args):
    """Run benchmark on specified file"""
    img = load_image(args.FILE_PATH)
    for fmt in args.image_formats:
        t = timeit.Timer(
            lambda: parse_image(img.data_buffer, fmt, args.size[0]))
        res = t.timeit(args.count)
        print_result(fmt, [res])


def random_mode(args):
    """Run benchmark on random data"""
    for fmt in args.image_formats:
        format = determine_color_format(fmt)
        num_bits = sum(format.bits_per_components)
        res = []
        for i in range(0, len(args.size), 2):
            img_size = (args.size[i] * args.size[i+1] * num_bits // 8) \
                + num_bits * (num_bits % 8 > 0)
            img = Image(os.urandom(img_size))
            t = timeit.Timer(
                lambda: parse_image(img.data_buffer, format.name, args.size[i]))
            res.append(t.timeit(args.count) / args.count)
        print_result(fmt, res)


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
    group.add_argument('--coverage',
                       help=('Run dedicated test from specified '
                             'directory for each supported format'))
    parser.add_argument('-s',
                        '--size',
                        default=[1000, 750],
                        nargs='+',
                        type=int,
                        help='Sizes of images to test')
    parser.add_argument('-c',
                        '--count',
                        default=10,
                        type=int,
                        help='Number of repetitions')
    parser.add_argument('-i',
                        '--image_formats',
                        default=AVAILABLE_FORMATS.keys(),
                        nargs='+',
                        help=('List of image formats to be benchmarked. '
                              'By default all supported formats are tested'))
    args = parser.parse_args()

    print_header(args.size)

    if args.DIRECTORY is not None:
        return directory_mode(args)

    if args.coverage is not None:
        return coverage_mode(args)

    if args.FILE_PATH is not None:
        return file_mode(args)

    return random_mode(args)


if __name__ == '__main__':
    sys.exit(main())
