"""Tests performance of various parsers"""
import argparse
import timeit
import sys
import os
import re

from raviewer.src.core import load_image, parse_image
from raviewer.image.color_format import AVAILABLE_FORMATS, PixelFormat, SubsampledColorFormat
from raviewer.image.image import Image
from raviewer.src.utils import determine_color_format


def print_result(fmt, res):
    """Print one row of table with format name and results"""
    print(f'{fmt:20}', end='')
    for r in res:
        print(f' {r:>14.3f}', end='')
    print()


def print_header(sizes):
    """Print header of the table with sizes of test images"""
    print(f'{"Format":20}', end='')
    for i in range(0, len(sizes), 2):
        print(f' {str(sizes[i])+"x"+str(sizes[i+1])+"[ms]":>14}', end='')
    print()


def directory_mode(directory, sizes, image_formats, count):
    """Run benchmark for all files in specified directory"""
    print_header(sizes)
    filename_regex = re.compile('([a-zA-Z0-9]+)_([0-9]+)_([0-9]+)')
    files = sorted(os.listdir(directory))
    files = filter(lambda x: x is not None, map(filename_regex.match, files))
    for f in files:
        img = load_image(os.path.join(directory, f.group(0)))
        fmt = f.group(1)
        width = f.group(2)
        if fmt not in image_formats:
            continue
        t = timeit.Timer(lambda: parse_image(img.data_buffer, fmt, int(width)))
        res = 1000 * t.timeit(count) / count
        print_result(fmt, [res])
    return 0


def coverage_mode(coverage, sizes, image_formats, count):
    """For each supported format run dedicated test from specified directory"""
    print_header(sizes)
    for fmt in image_formats:
        fmt_name = determine_color_format(fmt).name
        try:
            img = load_image(
                os.path.join(coverage, f'{fmt_name}_{sizes[0]}_{sizes[1]}'))
            t = timeit.Timer(
                lambda: parse_image(img.data_buffer, fmt, sizes[0]))
            res = 1000 * t.timeit(count) / count
        except FileNotFoundError:
            res = float('nan')
        print_result(fmt, [res])
    return 0


def file_mode(file_path, sizes, image_formats, count):
    """Run benchmark on specified file"""
    print_header(sizes)
    img = load_image(file_path)
    for fmt in image_formats:
        t = timeit.Timer(lambda: parse_image(img.data_buffer, fmt, sizes[0]))
        res = 1000 * t.timeit(count) / count
        print_result(fmt, [res])


def random_mode(sizes, image_formats, count):
    """Run benchmark on random data"""
    print_header(sizes)
    for fmt in image_formats:
        format = determine_color_format(fmt)
        num_bits = sum(format.bits_per_components)
        if format.pixel_format == PixelFormat.BAYER_RG or isinstance(
                format, SubsampledColorFormat):
            num_bits = format.bits_per_components[0]
        if num_bits % 8 != 0:
            num_bits += 8 - (num_bits % 8)
        res = []
        for i in range(0, len(sizes), 2):
            img_size = (sizes[i] * sizes[i + 1] * num_bits // 8)
            if isinstance(format, SubsampledColorFormat):
                img_size += 2 * img_size // (format.subsampling_horizontal *
                                             format.subsampling_vertical)
            img = Image(os.urandom(img_size))
            t = timeit.Timer(
                lambda: parse_image(img.data_buffer, format.name, sizes[i]))
            res.append(1000 * t.timeit(count) / count)
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

    if args.DIRECTORY is not None:
        return directory_mode(args.DIRECTORY, args.size, args.image_formats,
                              args.count)

    if args.coverage is not None:
        return coverage_mode(args.coverage, args.size, args.image_formats,
                             args.count)

    if args.FILE_PATH is not None:
        return file_mode(args.FILE_PATH, args.size, args.image_formats,
                         args.count)

    return random_mode(args.size, args.image_formats, args.count)


if __name__ == '__main__':
    sys.exit(main())
