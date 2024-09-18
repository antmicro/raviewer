import cv2
import numpy as np
import numpy.typing as npt
import re
import os
import subprocess


def convert_RGBA32_to_RGBA4444(img: npt.NDArray) -> npt.NDArray:
    img = img.astype('uint16')
    rgba4444 = np.empty(img.shape[0:2], dtype=np.uint16)
    rgba4444 = ((img[:, :, 0] >> 4) << 12) | ((img[:, :, 1] >> 4) << 8) | (
        (img[:, :, 2] >> 4) << 4) | (img[:, :, 3] >> 4)
    return rgba4444


def convert_RGBA32_to_RGBA555(img: npt.NDArray) -> npt.NDArray:
    img = img.astype('uint16')
    rgba555 = np.empty(img.shape[0:2], dtype=np.uint16)

    rgba555 = ((img[:, :, 0] >> 3) << 11) | ((img[:, :, 1] >> 3) << 6) | (
        (img[:, :, 2] >> 3) << 1) | (img[:, :, 3] >> 7)
    return rgba555


def convert_RGBA32_to_ARGB555(img: npt.NDArray) -> npt.NDArray:
    img = img.astype('uint16')
    rgba555 = np.empty(img.shape[0:2], dtype=np.uint16)

    rgba555 = ((img[:, :, 0] >> 7) << 15) | ((img[:, :, 1] >> 3) << 10) | (
        (img[:, :, 2] >> 3) << 5) | (img[:, :, 3] >> 3)
    return rgba555


def convert_RGBA32_to_RGGB(img: npt.NDArray) -> npt.NDArray:
    rggb = np.empty(img.shape[0:2], dtype=img.dtype)
    rggb[::2, ::2] = img[::2, ::2, 0]
    rggb[::2, 1::2] = img[::2, 1::2, 1]
    rggb[1::2, ::2] = img[1::2, ::2, 1]
    rggb[1::2, 1::2] = img[1::2, 1::2, 2]
    return rggb


def convert(img: npt.NDArray,
            name: str,
            dir: str,
            impath: str,
            swap_br: bool = False,
            swap_uv: bool = False) -> None:
    """Converts given RGB image to all formats supported by Raviewer.
    Uses ffmpeg for some conversions.
    Keyword arguments:
        img: Numpy array with RGB image to be converted
        name: name of the file to be generated
        dir: output directory
        impath: path to the RGB image for ffmpeg
        swap_br: if True converts the image to formats with R and B channels swapped
        swap_uv: if True converts the image to formats with U and V channels swapped
    
    Returns: None
    """
    width = img.shape[1]
    height = img.shape[0]
    if swap_br:
        img.tofile(f"{dir}/{name}_BGR24_{width}_{height}")
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    rgb.tofile(f"{dir}/{name}_RGB24_{width}_{height}")

    rgba = cv2.cvtColor(rgb, cv2.COLOR_RGB2RGBA)
    argb = rgba[:, :, [3, 0, 1, 2]]
    bgra = rgba[:, :, [2, 1, 0, 3]]
    abgr = rgba[:, :, [3, 2, 1, 0]]
    rgba.tofile(f"{dir}/{name}_RGBA32_{width}_{height}")
    argb.tofile(f"{dir}/{name}_ARGB32_{width}_{height}")
    if swap_br:
        bgra.tofile(f"{dir}/{name}_BGRA32_{width}_{height}")
        abgr.tofile(f"{dir}/{name}_ABGR32_{width}_{height}")

    rgb332 = ((rgb[:, :, 0] >> 5) << 5) | (
        (rgb[:, :, 1] >> 5) << 2) | (rgb[:, :, 2] >> 6)
    rgb332.tofile(f"{dir}/{name}_RGB332_{width}_{height}")
    rgb16 = rgb.astype('uint16')
    rgb565 = np.empty(img.shape[0:2], dtype=np.uint16)
    rgb565 = ((rgb16[:, :, 0] >> 3) << 11) | (
        (rgb16[:, :, 1] >> 2) << 5) | (rgb16[:, :, 2] >> 3)
    rgb565.astype('uint16').tofile(f"{dir}/{name}_RGB565_{width}_{height}")

    convert_RGBA32_to_RGBA4444(rgba).tofile(
        f"{dir}/{name}_RGBA444_{width}_{height}")
    convert_RGBA32_to_RGBA4444(argb).tofile(
        f"{dir}/{name}_ARGB444_{width}_{height}")
    if swap_br:
        convert_RGBA32_to_RGBA4444(bgra).tofile(
            f"{dir}/{name}_BGRA444_{width}_{height}")
        convert_RGBA32_to_RGBA4444(abgr).tofile(
            f"{dir}/{name}_ABGR444_{width}_{height}")

    convert_RGBA32_to_RGBA555(rgba).tofile(
        f"{dir}/{name}_RGBA555_{width}_{height}")
    convert_RGBA32_to_ARGB555(argb).tofile(
        f"{dir}/{name}_ARGB555_{width}_{height}")
    if swap_br:
        convert_RGBA32_to_RGBA555(bgra).tofile(
            f"{dir}/{name}_BGRA555_{width}_{height}")
        convert_RGBA32_to_ARGB555(abgr).tofile(
            f"{dir}/{name}_ABGR555_{width}_{height}")

    convert_RGBA32_to_RGGB(rgba).tofile(f"{dir}/{name}_RGGB_{width}_{height}")
    rgba_uint16 = np.empty(rgba.shape, dtype=np.dtype('>u2'))
    rgba_uint16 = rgba * 257
    convert_RGBA32_to_RGGB(rgba_uint16).tofile(
        f"{dir}/{name}_RG16_{width}_{height}")
    coeff = (2**12 - 1) / 255
    rgba_uint12 = np.empty(rgba.shape, dtype=np.dtype('>u2'))
    np.multiply(rgba, coeff, out=rgba_uint12, casting="unsafe")
    coeff = (2**10 - 1) / 255
    rgba_uint10 = np.empty(rgba.shape, dtype=np.dtype('>u2'))
    np.multiply(rgba, coeff, out=rgba_uint10, casting="unsafe")
    convert_RGBA32_to_RGGB(rgba_uint12).tofile(
        f"{dir}/{name}_RG12_{width}_{height}")
    convert_RGBA32_to_RGGB(rgba_uint10).tofile(
        f"{dir}/{name}_RG10_{width}_{height}")

    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    gray.tofile(f"{dir}/{name}_GRAY_{width}_{height}")
    coeff = (2**12 - 1) / 255
    gray_uint12 = np.empty(gray.shape, dtype=np.dtype('>u2'))
    np.multiply(gray, coeff, out=gray_uint12, casting="unsafe")
    coeff = (2**10 - 1) / 255
    gray_uint10 = np.empty(gray.shape, dtype=np.dtype('>u2'))
    np.multiply(gray, coeff, out=gray_uint10, casting="unsafe")
    gray_uint12.tofile(f"{dir}/{name}_GRAY12_{width}_{height}")
    gray_uint10.tofile(f"{dir}/{name}_GRAY10_{width}_{height}")

    yuv_conversion = f"""ffmpeg -i '{impath}' -y -vcodec rawvideo -pix_fmt yuyv422  -f rawvideo {dir}/'{name}_YUY2_{width}_{height}';
    ffmpeg -i '{impath}' -y -vcodec rawvideo -pix_fmt uyvy422  -f rawvideo {dir}/'{name}_UYVY_{width}_{height}';

    ffmpeg -i '{impath}' -y -vcodec rawvideo -pix_fmt nv12  -f rawvideo {dir}/'{name}_NV12_{width}_{height}';
    ffmpeg -i '{impath}' -y -vcodec rawvideo -pix_fmt yuv420p  -f rawvideo {dir}/'{name}_I420_{width}_{height}';
    ffmpeg -i '{impath}' -y -vcodec rawvideo -pix_fmt yuv422p  -f rawvideo {dir}/'{name}_I422_{width}_{height}';
    """
    process = subprocess.run(yuv_conversion, shell=True)
    if swap_uv:
        yuv_conversion = f"""ffmpeg -i '{impath}' -y -vcodec rawvideo -pix_fmt yvyu422  -f rawvideo {dir}/'{name}_YVYU_{width}_{height}';
        ffmpeg -i '{impath}' -y -vcodec rawvideo -pix_fmt uyvy422 -vf shuffleplanes=0:2:1 -f rawvideo {dir}/'{name}_VYUY_{width}_{height}';

        ffmpeg -i '{impath}' -y -vcodec rawvideo -pix_fmt nv21  -f rawvideo {dir}/'{name}_NV21_{width}_{height}';
        ffmpeg -i '{impath}' -y -vcodec rawvideo -pix_fmt yuv420p  -vf shuffleplanes=0:2:1 -f rawvideo {dir}/'{name}_YV12_{width}_{height}'
        """
        process = subprocess.run(yuv_conversion, shell=True)


if __name__ == "__main__":
    original_images = "original_images"
    test_images = "test_images"
    filename_regex = re.compile(
        r'([a-zA-Z0-9]+)(_\([0-9]+\))?\.(jpg|jpeg|png)')
    files = sorted(os.listdir(original_images))
    files = filter(lambda x: x is not None, map(filename_regex.match, files))

    for f in files:
        impath = os.path.join(original_images, f.group(0))
        img = cv2.imread(impath)
        name = f.group(1)
        if f.group(2) is not None:
            name = name + f.group(2)
        convert(img, name, test_images, impath)
