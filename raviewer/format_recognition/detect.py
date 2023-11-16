from collections.abc import Callable
import numpy as np
import numpy.typing as npt
from raviewer.image.color_format import PixelFormat, SubsampledColorFormat, AVAILABLE_FORMATS, Endianness
from raviewer.src.utils import determine_color_format
from raviewer.src.core import load_image, parse_image, get_displayable
from raviewer.image.image import Image
import cv2

# constants used for differentiating formats based on the rolling standard deviation of the data
# the value of the constant is the maximal median of the rolling standar deviation for one of the formats

# constant used to differentiate BAYER and GRAY formats from byte unaligned formats
BAYER_AND_GRAY_CUTOFF = 0.001
# constant used to differentiate RGB565 from RGB332 format
RGB565_CUTOFF = 0.03
# constants used to differentiate GRAY formats from multichannel formats
GRAY_CUTOFF_12BIT = 0.275 * 2**12
GRAY_CUTOFF_10BIT = 0.275 * 2**10
# constant used to differentiate GRAY from BAYER formats
GRAY_CUTOFF = 6
# constant used to differentiate RGGB from RG16 format
RGGB_CUTOFF = 2300

# list of recognized formats, grouped together if indistinguishable
list_of_groups = [["unknown"], ["GRAY"], ["I422"], ["I420", "YV12"],
                  ["NV12", "NV21"], ["YUY2", "YVYU"], ["UYVY", "VYUY"],
                  ["RG12"], ["GRAY12"], ["RG10"], ["GRAY10"],
                  ["RGBA32", "BGRA32"], ["ARGB32", "ABGR32"],
                  ["RGBA444", "BGRA444"], ["ARGB444", "ABGR444"],
                  ["RGBA555", "BGRA555"], ["ARGB555", "ABGR555"], ["RGB332"],
                  ["RGB565"], ["RGGB"], ["RG16"], ["RGB24", "BGR24"]]
# dictionary with formats that are often confused
# based on statistics from previous runs and natural similarity between formats
top2_dict = {
    "I422": ["I420", "YV12"],
    "I420": ["I422"],
    "YUY2": ["UYVY", "VYUY"],
    "UYVY": ["YUY2", "YVYU"],
    "RG12": ["GRAY12"],
    "GRAY12": ["RG12"],
    "RG10": ["GRAY10"],
    "GRAY10": ["RG10"]
}


def check_channel_number(img: Image, num_channels: int) -> bool:
    """Checks if the image is guaranteed to have 3 or 4 channels"""
    supported_num_channels = [3, 4]
    if num_channels not in supported_num_channels:
        return False
    buffer_length = len(img.data_buffer)
    if buffer_length % num_channels != 0:
        return False
    num_divs = sum(
        map((lambda x: 1 if buffer_length % x == 0 else 0),
            supported_num_channels))
    if num_divs == 1 and buffer_length % num_channels == 0:
        return True
    return False


def is_four_channel(img: Image) -> bool:
    return check_channel_number(img, 4)


def is_three_channel(img: Image) -> bool:
    return check_channel_number(img, 3)


def is_every_fourth_max(img: Image, start: int = 3) -> bool:
    """Checks if every fourth pixel value is set to 255"""
    data = np.frombuffer(img.data_buffer, dtype=np.uint8)
    if np.all(data[start::4] == 255):
        return True
    else:
        return False


def are_bits_set(img: Image,
                 num_bits: int = 1,
                 start: bool = True,
                 dtype: str = '<u2') -> bool:
    """Checks if every two bytes have have their prefix/suffix set to ones"""
    #0x8000, 0x0001, 0xF000, 0x000F
    if num_bits not in [1, 4]:
        return False
    if start and num_bits == 1:
        mask = 0x8000
    elif start and num_bits == 4:
        mask = 0xF000
    elif not start and num_bits == 1:
        mask = 0x0001
    else:
        mask = 0x000F
    try:
        data = np.frombuffer(img.data_buffer, dtype=np.dtype(dtype))
    except ValueError:
        return False
    data = np.bitwise_and(data, mask)
    if np.all(data == mask):
        return True
    else:
        return False


def check_bits_per_channel(img: Image,
                           num_bits: int,
                           dtype: str = '>u2') -> bool:
    """Checks if the image uses 10 or 12 bits per pixel channel"""
    try:
        interpreted = np.frombuffer(img.data_buffer, dtype=np.dtype(dtype))
    except ValueError:
        return False
    if num_bits == 12:
        mask = 0xF000
        mask2 = 0xF800
    elif num_bits == 10:
        mask = 0xFC00
        mask2 = 0xFE00
    else:
        return False
    masked = np.bitwise_and(interpreted, mask)
    all_zeros = not np.any(masked)
    if not all_zeros:
        return False
    num_bits_required = np.any(np.bitwise_and(interpreted, mask2))
    if num_bits_required:
        return True
    else:
        return False


def check_12bits_per_channel(img: Image, dtype: str = ">u2") -> bool:
    return check_bits_per_channel(img, 12, dtype)


def check_10bits_per_channel(img: Image, dtype: str = ">u2") -> bool:
    return check_bits_per_channel(img, 10, dtype)


def rolling_window(array: npt.NDArray, window: int) -> npt.NDArray:
    """Prepares view of array for fast calculation of rolling statistics like variance
    Keyword arguments:
        array: Numpy array
        window: length of the sampling window

    Returns: Numpy array with rolling window view of the original array
    """
    return np.lib.stride_tricks.sliding_window_view(array, window)


def is_yuv(img: Image) -> bool:
    """Checks if image is in YUV format based on used pixel range"""
    data = np.frombuffer(img.data_buffer, dtype=np.uint8)
    buffer_length = len(data)
    #if "digital" YUV is going to be supported then it should be adjusted to match only UV channels
    #analog YUV permits some points exceeding range
    if np.count_nonzero(
            data >= 10) / buffer_length >= 0.999 and np.count_nonzero(
                data <= 240) / buffer_length >= 0.999:
        return True
    return False


def yuv_type(img: Image) -> list[str]:
    """For given YUV image determines its specific format"""
    data = np.frombuffer(img.data_buffer, dtype=np.uint8)
    buffer_length = len(data)

    #extract information about Y and UV channels
    roll_std1 = np.std(data[:(buffer_length // 2)])
    roll_std2 = np.std(data[(buffer_length // 2):])
    #planar like I422
    planar1 = np.median(roll_std1)
    planar2 = np.median(roll_std2)

    roll_std1 = np.std(data[:int(buffer_length * (2 / 3))])
    roll_std2 = np.std(data[int(buffer_length * (2 / 3)):])
    #planar like I420 or semiplanar
    planar_or_semi1 = np.median(roll_std1)
    planar_or_semi2 = np.median(roll_std2)

    roll_std1 = np.std(data[0::2])
    roll_std2 = np.std(data[1::2])
    #packed
    packed1 = np.median(roll_std1)
    packed2 = np.median(roll_std2)

    planar_score = max(planar1, planar2) / min(planar1, planar2)
    planar_or_semi_score = max(planar_or_semi1, planar_or_semi2) / min(
        planar_or_semi1, planar_or_semi2)
    packed_score = max(packed1, packed2) / min(packed1, packed2)
    winning_score = max(planar_score, planar_or_semi_score, packed_score)

    if planar_score == winning_score:
        return ["I422"]
    elif planar_or_semi_score == winning_score:

        semiplanar_uv_1 = data[int(buffer_length * 2 / 3)::2]
        semiplanar_uv_2 = data[int(buffer_length * 2 / 3) + 1::2]
        planar_uv_1 = data[int(buffer_length * 2 / 3):int(buffer_length *
                                                          (5 / 6))]
        planar_uv_2 = data[int(buffer_length * (5 / 6)):]

        semiplanar_score = np.std(semiplanar_uv_1) + np.std(semiplanar_uv_2)
        planar_score = np.std(planar_uv_1) + np.std(planar_uv_2)
        winning_score = max(semiplanar_score, planar_score)
        if semiplanar_score == winning_score:
            return ["I420", "YV12"]
        else:
            return ["NV12", "NV21"]
    else:
        #extract information about U and V channels
        channel1 = data[0::2]
        channel2 = data[1::2]
        roll_std1 = np.std(rolling_window(channel1, 20), axis=-1)
        roll_std2 = np.std(rolling_window(channel2, 20), axis=-1)
        rolling_variance_median_1 = np.median(roll_std1)
        rolling_variance_median_2 = np.median(roll_std2)
        if rolling_variance_median_1 < rolling_variance_median_2:
            return ["YUY2", "YVYU"]
        else:
            return ["UYVY", "VYUY"]


def dtype_to_endianness(dtype: str) -> str:
    if dtype[0] == '<':
        return "LITTLE_ENDIAN"
    return "BIG_ENDIAN"


def try_endianness(img: Image, f: Callable[..., bool], **kwargs) -> str | None:
    dtype = None
    if f(img, dtype='<u2', **kwargs):
        dtype = '<u2'
    if f(img, dtype='>u2', **kwargs):
        dtype = '>u2'
    return dtype


def classify(img: Image) -> tuple[list[str], str]:
    """Predicts image format and its endianness"""
    if is_yuv(img):
        return yuv_type(img), "BIG_ENDIAN"
    else:
        dtype = try_endianness(img, check_12bits_per_channel)
        if dtype is not None:
            deviation = np.std(
                np.frombuffer(img.data_buffer, dtype=np.dtype(dtype)))
            if GRAY_CUTOFF_12BIT < deviation:
                return ["RG12"], dtype_to_endianness(dtype)
            else:
                return ["GRAY12"], dtype_to_endianness(dtype)

        dtype = try_endianness(img, check_10bits_per_channel)
        if dtype is not None:
            deviation = np.std(
                np.frombuffer(img.data_buffer, dtype=np.dtype(dtype)))
            if GRAY_CUTOFF_10BIT < deviation:
                return ["RG10"], dtype_to_endianness(dtype)
            else:
                return ["GRAY10"], dtype_to_endianness(dtype)

        if is_every_fourth_max(img, start=3):
            return ["RGBA32", "BGRA32"], "BIG_ENDIAN"
        if is_every_fourth_max(img, start=0):
            return ["ARGB32", "ABGR32"], "BIG_ENDIAN"

        dtype = try_endianness(img, are_bits_set, num_bits=4, start=False)
        if dtype is not None:
            return ["RGBA444", "BGRA444"], dtype_to_endianness(dtype)
        dtype = try_endianness(img, are_bits_set, num_bits=4, start=True)
        if dtype is not None:
            return ["ARGB444", "ABGR444"], dtype_to_endianness(dtype)
        dtype = try_endianness(img, are_bits_set, num_bits=1, start=False)
        if dtype is not None:
            return ["RGBA555", "BGRA555"], dtype_to_endianness(dtype)
        dtype = try_endianness(img, are_bits_set, num_bits=1, start=True)
        if dtype is not None:
            return ["ARGB555", "ABGR555"], dtype_to_endianness(dtype)

        data = np.frombuffer(img.data_buffer, dtype=np.uint8)
        hists = []
        divisible = True
        try:
            for i in range(2, -1, -1):
                hist, _ = np.histogram(data.reshape(-1, 3)[:, i],
                                       bins=256,
                                       range=(0, 256))
                hists.append(hist)
        except ValueError:
            divisible = False
            data = np.pad(data, (0, 3 - len(data) % 3), 'constant')
            for i in range(2, -1, -1):
                hist, _ = np.histogram(data.reshape(-1, 3)[:, i],
                                       bins=256,
                                       range=(0, 256))
                hists.append(hist)

        channel_length = len(data) // 3
        roll_std = np.std(rolling_window(hists[0] / channel_length,
                                         len(hists[0]) // 10),
                          axis=-1)
        if np.median(roll_std) >= BAYER_AND_GRAY_CUTOFF:
            parsed = parse_image(img.data_buffer.copy(), 'RGB565',
                                 len(data) // 2)
            hists = []
            for i in range(2, -1, -1):
                hist, _ = np.histogram(parsed.processed_data[i::4],
                                       bins=64,
                                       range=(0, 64))
                hists.append(hist)
            roll_std = np.std(rolling_window(hists[0][:32] / channel_length,
                                             len(hists[0]) // 10),
                              axis=-1)
            if np.median(roll_std) >= RGB565_CUTOFF:
                return ["RGB332"], "LITTLE_ENDIAN"
            else:
                try:
                    endianness = "LITTLE_ENDIAN"
                    big_endian = np.frombuffer(img.data_buffer,
                                               dtype=np.dtype('>u2'))
                    little_endian = np.frombuffer(img.data_buffer,
                                                  dtype=np.dtype('<u2'))
                    big_endian_variance = np.median(
                        np.std(rolling_window(big_endian, 10), axis=-1))
                    little_endian_variance = np.median(
                        np.std(rolling_window(little_endian, 10), axis=-1))
                    if big_endian_variance < little_endian_variance:
                        endianness = "BIG_ENDIAN"
                except ValueError:
                    endianness = "LITTLE_ENDIAN"
                return ["RGB565"], endianness
        corr = np.corrcoef(hists[0], hists[1])[0, 1]
        #if the image does not have 3 channels then the correlation between 3 arbitrary channels is higher
        if corr >= 0.95 or not divisible:
            roll_std = np.std(rolling_window(data, 5), axis=-1)
            if np.median(roll_std) <= GRAY_CUTOFF:
                return ["GRAY"], "BIG_ENDIAN"
            try:
                data = np.frombuffer(img.data_buffer, dtype=np.dtype('>u2'))
                roll_std = np.std(rolling_window(data, 5), axis=-1)
                if np.median(roll_std) <= RGGB_CUTOFF:
                    return ["RGGB"], "BIG_ENDIAN"
                else:
                    return ["RG16"
                            ], "BIG_ENDIAN"  #TODO: add test for endianness
            except ValueError:
                return ["RGGB"], "BIG_ENDIAN"
        return ["RGB24", "BGR24"], "BIG_ENDIAN"


def find_in_formats(fmt: str) -> int:
    """Finds index of the format group in list_of_groups for given format. If format was not found return -1"""
    for i, l in enumerate(list_of_groups):
        if fmt in l:
            return i
    return -1


def classify_top1(img: Image) -> tuple[str, str]:
    """Predicts format of the image and its endianness
    Keyword arguments:
        img: Image instance

    Returns: string with image format and string with endianness
    """
    fmts, endianness = classify(img)
    return fmts[0], endianness


def classify_all(img: Image) -> tuple[list[str], str]:
    """Predicts format of the image and its endianness
    Keyword arguments:
        img: Image instance

    Returns: list of strings with image formats and string with endianness
    """
    fmts, endianness = classify(img)
    top2 = top2_dict.get(fmts[0])
    if top2 is not None:
        fmts += top2
    return fmts, endianness


def possible_resolutions(length: int, ratio_limit: int = 4) -> list[int]:
    """Finds every possible image width, limited to 1:4 height to width ratio"""
    widths = []
    for i in range(int((length / ratio_limit)**0.5), int((length)**0.5) + 1):
        if length % i == 0:
            widths.append(i)
    return widths


def find_resolution(img: Image, fmt_name: str) -> list[list[int]]:
    """Predicts resolution of image in given format
    Keyword arguments:
        img: Image instance
        fmt_name: string with color format

    Returns: list of up to 3 best widths and heights
    """
    color_fmt = determine_color_format(fmt_name)
    buffer_length = len(img.data_buffer)
    num_bits = sum(color_fmt.bits_per_components)
    if color_fmt == PixelFormat.BAYER_RG:
        num_bits = color_fmt.bits_per_components
    if num_bits % 8 != 0:
        num_bits += 8 - (num_bits % 8)
    final_len = 8 * buffer_length // num_bits
    if isinstance(color_fmt, SubsampledColorFormat):
        num_bits = color_fmt.bits_per_components[0]
        final_len = 8 * buffer_length * 6 // (
            num_bits * 3 * (2 + (3 - color_fmt.subsampling_vertical) *
                            (3 - color_fmt.subsampling_horizontal)))
    widths = possible_resolutions(final_len)
    edgesDetected = []
    for width in widths:
        try:
            parsed = parse_image(img.data_buffer, fmt_name, width, 0)
            displayable = get_displayable(parsed)
        except (ValueError, cv2.error):
            return [[1000, final_len // 2]]
        if displayable.shape[2] == 3:
            gray = cv2.cvtColor(displayable, cv2.COLOR_RGB2GRAY)
        else:
            gray = cv2.cvtColor(displayable, cv2.COLOR_RGBA2GRAY)

        _, binaryImage = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)
        kern = np.array([[-1, -1, -1], [-1, 8, -1], [-1, -1, -1]],
                        dtype=np.int64)
        filtered = cv2.filter2D(src=binaryImage, ddepth=-1, kernel=kern)
        edgesDetected.append(np.sum(filtered))
    evaluation = [list(pair) for pair in zip(edgesDetected, widths)]
    evaluation.sort(key=lambda x: x[0])
    if len(evaluation) == 0:
        return [[1000, final_len // 1000]]
    resolutions = []
    for i in range(0, min(3, len(evaluation))):
        resolutions.append([evaluation[i][1], final_len // 2])
    return resolutions


def predict_resolution(img: Image, fmt_name: str) -> list[list[int]]:
    """Predicts resolution of image in given format
    Keyword arguments:
        img: Image instance
        fmt_name: string with color format

    Returns: list of 2 best widths and heights
    """
    resolutions = find_resolution(img, fmt_name)
    return [[resolutions[0][0] * 2, resolutions[0][1] // 2], resolutions[0]]
