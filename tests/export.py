import argparse
import os
import re
import sys
import subprocess


def display_width(width):
    if width is None:
        return "Auto"
    return f"{width}px"


def print_header(widths):
    """Print header of the table with sizes of test images"""
    print(f'{"Image":40}', end='')
    for w in map(display_width, widths):
        print(f' {w:>8}', end='')
    print()


def print_result(img, res):
    """Print one row of table with format name and results"""
    print(f'{img:40}', end='')
    for r in res:
        label = "✓" if r == 0 else "x"
        print(f' {label:>8}', end='')
    print()


def print_errors(errors):
    for path, w, message in errors:
        w = display_width(w)
        print(f"An error ocurred during exporting {path} for width {w}")
        print(message.decode('utf-8'))
        print()


def run(src_directory, dst_directory, widths):
    """Export for all files in specified directory"""
    print_header(widths)

    # Use source if destination is not given
    dst_directory = dst_directory or src_directory

    # Get files
    filename_regex = re.compile('([a-zA-Z0-9]+)_([0-9]+)_([0-9]+)')
    files = sorted(os.listdir(src_directory))
    files = filter(lambda x: x is not None, map(filename_regex.match, files))

    errors = []
    for f in files:
        name = f.group(0)
        src_path = os.path.join(src_directory, name)
        results = []
        for w in widths:
            # Args
            dst_path = os.path.join(
                dst_directory,
                f"export_{f.group(2) if w is None else w}_{name}")
            args = ["raviewer", "-f", src_path, "-e", dst_path]
            if w is not None:
                args.extend(["-w", str(w)])

            process = subprocess.run(args,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)

            results.append(process.returncode)
            if process.returncode != 0:
                errors.append((src_path, w, process.stderr))

        print_result(src_path, results)

    print_errors(errors)
    return bool(errors)


def main():
    parser = argparse.ArgumentParser(prog='Parser for export testing')
    parser.add_argument('DIRECTORY',
                        help='Path to directory, containing files for testing')
    parser.add_argument(
        "-dst",
        "--destination",
        default=None,
        help="Path to directory for exported images. Defaults to DIRECTORY"),
    parser.add_argument("--use-prediction-width",
                        action=argparse.BooleanOptionalAction,
                        default=True,
                        help="If true, test detected width"),
    parser.add_argument('-w',
                        '--width',
                        default=[],
                        required=False,
                        nargs='+',
                        type=int,
                        help='Widths of images to test')

    args = parser.parse_args()

    # Prepend with
    widths = []
    if args.use_prediction_width:
        widths.append(None)

    widths.extend(args.width)
    return run(args.DIRECTORY, args.destination, widths)


if __name__ == "__main__":
    sys.exit(main())
