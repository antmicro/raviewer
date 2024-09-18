from raviewer.format_recognition.detect import classify_all, find_resolution, predict_resolution, find_in_formats, classify, top2_dict, list_of_groups
from raviewer.format_recognition.generate_images import convert
from raviewer.image.color_format import AVAILABLE_FORMATS, Endianness
from raviewer.src.core import load_image
import numpy as np
import os
import sys
import re
import cv2
from typing import Pattern

minimal_thresholds = {
    'format': 85.0,
    'resolution': 60.0,
    'endianness': 95.0,
}


def run_prediction(
    directory: str = "./test_images",
    filename_regex: Pattern[
        str] = r"([a-zA-Z0-9]+)(_\([0-9]+\))?_([a-zA-Z0-9]+)_([0-9]+)_([0-9]+)"
) -> None:
    """Predicts format, resolution and endianness of images in given directory, then summarizes and visualizes results.
    This function is meant for manual testing.
    Keyword arguments:
        directory: name of the directory with test images
        filename_regex: string with regex matching test image names
    """
    import matplotlib.pyplot as plt

    filename_regex = re.compile(filename_regex)
    files = sorted(os.listdir(directory))
    files = filter(lambda x: x is not None, map(filename_regex.match, files))
    acc = 0
    acc2 = 0
    tests = 0
    acc_res = 0
    acc_res3 = 0
    acc_res_cond = 0
    acc_res_cond3 = 0
    acc_res_common = 0
    acc_end = 0
    acc_end_cond = 0
    confusion = np.zeros((len(list_of_groups), len(list_of_groups)))
    deviations1 = []
    deviations2 = []
    for f in files:
        img = load_image(os.path.join(directory, f.group(0)))
        name = f.group(1)
        fmt = f.group(3)
        width = int(f.group(4))
        format_predictions, endianness_prediction = classify(img)
        if Endianness[endianness_prediction] == AVAILABLE_FORMATS[
                fmt].endianness:
            acc_end += 1
        if Endianness[endianness_prediction] == AVAILABLE_FORMATS[
                format_predictions[0]].endianness:
            acc_end_cond += 1
        resolution_predictions = find_resolution(img, format_predictions[0])
        tests += 1
        if fmt in format_predictions:
            acc += 1
        else:
            second_format_prediction = top2_dict.get(format_predictions[0])
            if second_format_prediction is not None:
                if fmt in second_format_prediction:
                    acc2 += 1
        if width == 2 * resolution_predictions[0][0]:
            acc_res += 1
        if width in [wh[0] for wh in resolution_predictions]:
            acc_res3 += 1
        if width == resolution_predictions[0][
                0] or resolution_predictions[0][0] * 2 == width:
            acc_res_common += 1
        deviation = width / resolution_predictions[0][0]
        if deviation > 1:
            deviations1.append(deviation)
        elif deviation < 1:
            deviations2.append(1 / deviation)
        resolution_predictions = find_resolution(img, fmt)
        if width == 2 * resolution_predictions[0][0]:
            acc_res_cond += 1
        if width in [wh[0] for wh in resolution_predictions]:
            acc_res_cond3 += 1
        correct = find_in_formats(fmt)
        predicted = find_in_formats(format_predictions[0])
        confusion[correct, predicted] += 1
        if tests % 50 == 0:
            print("Format accuracy", acc, "/", tests, " ~ ", acc / tests * 100)
            print("Format top 2 accuracy", acc + acc2, "/", tests, " ~ ",
                  (acc + acc2) / tests * 100)
            print("Resolution accuracy", acc_res, "/", tests, " ~ ",
                  acc_res / tests * 100)
            print("Resolution top 3 accuracy", acc_res3, "/", tests, " ~ ",
                  acc_res3 / tests * 100)
            print("Resolution accuracy given correct format", acc_res3, "/",
                  tests, " ~ ", acc_res_cond / tests * 100)
            print("Resolution top 3 accuracy given correct format",
                  acc_res_cond3, "/", tests, " ~ ",
                  acc_res_cond3 / tests * 100)
            print("Resolution matches prediction or doubled prediction",
                  acc_res_common, "/", tests, " ~ ",
                  acc_res_common / tests * 100)
            print("Endianness accuracy", acc_end, "/", tests, " ~ ",
                  acc_end / tests * 100)
            print("Endianness accuracy given correct format", acc_end_cond,
                  "/", tests, " ~ ", acc_end_cond / tests * 100)
            print()
    print("Format accuracy", acc, "/", tests, " ~ ", acc / tests * 100)
    print("Format top 2 accuracy", acc + acc2, "/", tests, " ~ ",
          (acc + acc2) / tests * 100)
    print("Resolution accuracy", acc_res, "/", tests, " ~ ",
          acc_res / tests * 100)
    print("Resolution top 3 accuracy", acc_res3, "/", tests, " ~ ",
          acc_res3 / tests * 100)
    print("Resolution accuracy given correct format", acc_res3, "/", tests,
          " ~ ", acc_res_cond / tests * 100)
    print("Resolution top 3 accuracy given correct format", acc_res_cond3, "/",
          tests, " ~ ", acc_res_cond3 / tests * 100)
    print("Resolution matches prediction or doubled prediction",
          acc_res_common, "/", tests, " ~ ", acc_res_common / tests * 100)
    print("Endianness accuracy", acc_end, "/", tests, " ~ ",
          acc_end / tests * 100)
    print("Endianness accuracy given correct format", acc_end_cond, "/", tests,
          " ~ ", acc_end_cond / tests * 100)

    fig = plt.figure()
    ax = fig.add_subplot(111)
    cax = ax.matshow(confusion, interpolation='nearest')
    fig.colorbar(cax)
    alpha = list(map(str, list_of_groups))
    xaxis = np.arange(len(alpha))
    ax.set_xticks(xaxis)
    ax.set_yticks(xaxis)
    ax.set_xticklabels(alpha, rotation=90)
    ax.set_yticklabels(alpha)
    plt.show()


def main():
    original_images = "./raviewer/format_recognition/original_images"
    test_images = "test_images"
    filename_regex = re.compile(
        r'([a-zA-Z0-9]+)(_\([0-9]+\))?\.(jpg|jpeg|png)')
    try:
        files = sorted(os.listdir(os.path.abspath(original_images)))
    except:
        return 0
    files = filter(lambda x: x is not None, map(filename_regex.match, files))

    if not os.path.exists(test_images):
        os.makedirs(test_images)

    testcases = 0
    acc_format = 0
    acc_resolution = 0
    acc_endianness = 0

    for f in files:
        impath = os.path.join(original_images, f.group(0))
        img = cv2.imread(impath)
        name = f.group(1)
        if f.group(2) is not None:
            name = name + f.group(2)
        convert(img, name, test_images, impath)
        test_filename_regex = re.compile(
            r"([a-zA-Z0-9]+)(_\([0-9]+\))?_([a-zA-Z0-9]+)_([0-9]+)_([0-9]+)")
        test_files = sorted(os.listdir(test_images))
        test_files = filter(lambda x: x is not None,
                            map(test_filename_regex.match, test_files))

        for t in test_files:
            img = load_image(os.path.join(test_images, t.group(0)))
            name = t.group(1)
            fmt = t.group(3)
            width = int(t.group(4))
            testcases += 1
            predicted_formats, endianness = classify_all(img)
            r = predict_resolution(img, predicted_formats[0])

            # format
            if fmt in predicted_formats:
                acc_format += 1

            # resolution
            if width == r[0][0] or width == r[1][0]:
                acc_resolution += 1

            # endianness
            if Endianness[endianness] == AVAILABLE_FORMATS[fmt].endianness:
                acc_endianness += 1

            os.remove(os.path.join(test_images, t.group(0)))
    os.rmdir(test_images)

    print()
    print(
        f"Format accuracy: {100*acc_format/testcases:2.1f}, required: {minimal_thresholds['format']}"
    )
    print(
        f"Resolution accuracy: {100*acc_resolution/testcases:2.1f}, required: {minimal_thresholds['resolution']}"
    )
    print(
        f"Endianness accuracy: {100*acc_endianness/testcases:2.1f}, required: {minimal_thresholds['endianness']}"
    )


if __name__ == "__main__":
    sys.exit(main())
