"""Support for abstract color formats."""

from enum import Enum
from pyrav4l2 import *


class PixelFormat(Enum):
    """Respresenation defining color hierachy in pixel."""

    RGB = 1
    BGR = 2
    RGBA = 3
    BGRA = 4
    ARGB = 5
    ABGR = 6
    YUYV = 7
    UYVY = 8
    VYUY = 9
    YVYU = 10
    YUV = 11
    YVU = 12
    MONO = 13
    BAYER_RG = 14
    BAYER_BG = 15
    BAYER_GB = 16
    BAYER_GR = 17
    CUSTOM = 0


class Endianness(Enum):
    """Represenation of color format endianness."""

    LITTLE_ENDIAN = 1
    BIG_ENDIAN = 2


class Platform(Enum):
    """Explicitly supported Tegra platforms"""
    XAVIER = 1
    TX2 = 2


class PixelPlane(Enum):
    """Representation of color format pixel plane."""

    PACKED = 1
    PLANAR = 2
    SEMIPLANAR = 3


class ColorFormat():
    """Representation of color format."""

    def __init__(self,
                 pixel_format,
                 endianness,
                 pixel_plane,
                 bpc1,
                 bpc2,
                 bpc3,
                 bpc4=0,
                 name="unnamed",
                 fourcc=None,
                 platform=None,
                 palette=None):
        self.name = name
        self.platform = platform
        self.pixel_format = pixel_format
        self.fourcc = fourcc
        self.endianness = endianness
        self.pixel_plane = pixel_plane
        self._bpcs = (bpc1, bpc2, bpc3, bpc4)
        self.palette = palette

    @property
    def bits_per_components(self):
        return self._bpcs

    @bits_per_components.setter
    def bits_per_components(self, bpcs):

        if isinstance(bpcs, (list, tuple)):
            if len(bpcs) == 3:
                self._bpcs = (tuple(bpcs) + (0, ))
                return
            elif len(bpcs) == 4:
                self._bpcs = tuple(bpcs)
                return

        raise ValueError(
            "Provided value should be an iterable of 3 or 4 values!")

    def __str__(self):
        return self.name


class SubsampledColorFormat(ColorFormat):
    """
    Representation of color format with additional information about subsampling
    """

    def __init__(self,
                 pixel_format,
                 endianness,
                 pixel_plane,
                 bpc1,
                 bpc2,
                 bpc3,
                 bpc4=0,
                 name="unnamed",
                 subsampling_horizontal=1,
                 subsampling_vertical=1,
                 fourcc=None,
                 palette=None):
        super().__init__(pixel_format, endianness, pixel_plane, bpc1, bpc2,
                         bpc3, bpc4, name, fourcc)
        self.subsampling_horizontal = subsampling_horizontal
        self.subsampling_vertical = subsampling_vertical
        self.palette = palette


def rgb_palette():
    return {"R": (1., 0., 0.), "G": (0., 1., 0.), "B": (0., 0., 1.)}


AVAILABLE_FORMATS = {
    'RGB24':
    ColorFormat(PixelFormat.RGB,
                Endianness.BIG_ENDIAN,
                PixelPlane.PACKED,
                8,
                8,
                8,
                name="RGB24",
                fourcc=V4L2_PIX_FMT_RGB24),
    'BGR24':
    ColorFormat(PixelFormat.BGR,
                Endianness.BIG_ENDIAN,
                PixelPlane.PACKED,
                8,
                8,
                8,
                name="BGR24",
                fourcc=V4L2_PIX_FMT_BGR24),
    'RGBA32':
    ColorFormat(PixelFormat.RGBA,
                Endianness.BIG_ENDIAN,
                PixelPlane.PACKED,
                8,
                8,
                8,
                8,
                name="RGBA32",
                fourcc=V4L2_PIX_FMT_RGBA32),
    'BGRA32':
    ColorFormat(PixelFormat.BGRA,
                Endianness.BIG_ENDIAN,
                PixelPlane.PACKED,
                8,
                8,
                8,
                8,
                name="BGRA32",
                fourcc=V4L2_PIX_FMT_BGRA32),
    'ARGB32':
    ColorFormat(PixelFormat.ARGB,
                Endianness.BIG_ENDIAN,
                PixelPlane.PACKED,
                8,
                8,
                8,
                8,
                name="ARGB32",
                fourcc=V4L2_PIX_FMT_ARGB32),
    'ABGR32':
    ColorFormat(PixelFormat.ABGR,
                Endianness.BIG_ENDIAN,
                PixelPlane.PACKED,
                8,
                8,
                8,
                8,
                name="ABGR32",
                fourcc=V4L2_PIX_FMT_ABGR32),
    'RGB332':
    ColorFormat(PixelFormat.RGB,
                Endianness.LITTLE_ENDIAN,
                PixelPlane.PACKED,
                3,
                3,
                2,
                name="RGB332",
                fourcc=V4L2_PIX_FMT_RGB332),
    'RGB565':
    ColorFormat(PixelFormat.RGB,
                Endianness.LITTLE_ENDIAN,
                PixelPlane.PACKED,
                5,
                6,
                5,
                name="RGB565",
                fourcc=V4L2_PIX_FMT_RGB565),
    'RGBA444':
    ColorFormat(PixelFormat.RGBA,
                Endianness.LITTLE_ENDIAN,
                PixelPlane.PACKED,
                4,
                4,
                4,
                bpc4=4,
                name="RGBA444",
                fourcc=V4L2_PIX_FMT_RGBA444),
    'BGRA444':
    ColorFormat(PixelFormat.BGRA,
                Endianness.LITTLE_ENDIAN,
                PixelPlane.PACKED,
                4,
                4,
                4,
                bpc4=4,
                name="BGRA444",
                fourcc=V4L2_PIX_FMT_BGRA444),
    'ARGB444':
    ColorFormat(PixelFormat.ARGB,
                Endianness.LITTLE_ENDIAN,
                PixelPlane.PACKED,
                4,
                4,
                4,
                bpc4=4,
                name="ARGB444",
                fourcc=V4L2_PIX_FMT_ARGB444),
    'ABGR444':
    ColorFormat(PixelFormat.ABGR,
                Endianness.LITTLE_ENDIAN,
                PixelPlane.PACKED,
                4,
                4,
                4,
                bpc4=4,
                name="ABGR444",
                fourcc=V4L2_PIX_FMT_ABGR444),
    'RGBA555':
    ColorFormat(PixelFormat.RGBA,
                Endianness.LITTLE_ENDIAN,
                PixelPlane.PACKED,
                5,
                5,
                5,
                bpc4=1,
                name="RGBA555",
                fourcc=V4L2_PIX_FMT_RGBA555),
    'BGRA555':
    ColorFormat(PixelFormat.BGRA,
                Endianness.LITTLE_ENDIAN,
                PixelPlane.PACKED,
                5,
                5,
                5,
                bpc4=1,
                name="BGRA555",
                fourcc=V4L2_PIX_FMT_BGRA555),
    'ARGB555':
    ColorFormat(PixelFormat.ARGB,
                Endianness.LITTLE_ENDIAN,
                PixelPlane.PACKED,
                1,
                5,
                5,
                bpc4=5,
                name="ARGB555",
                fourcc=V4L2_PIX_FMT_ARGB555),
    'ABGR555':
    ColorFormat(PixelFormat.ABGR,
                Endianness.LITTLE_ENDIAN,
                PixelPlane.PACKED,
                1,
                5,
                5,
                bpc4=5,
                name="ABGR555",
                fourcc=V4L2_PIX_FMT_ABGR555),
    'YUY2':
    SubsampledColorFormat(PixelFormat.YUYV,
                          Endianness.BIG_ENDIAN,
                          PixelPlane.PACKED,
                          8,
                          8,
                          8,
                          8,
                          "YUY2",
                          2,
                          1,
                          fourcc=V4L2_PIX_FMT_YUYV),
    'UYVY':
    SubsampledColorFormat(PixelFormat.UYVY,
                          Endianness.BIG_ENDIAN,
                          PixelPlane.PACKED,
                          8,
                          8,
                          8,
                          8,
                          "UYVY",
                          2,
                          1,
                          fourcc=V4L2_PIX_FMT_UYVY),
    'YVYU':
    SubsampledColorFormat(PixelFormat.YVYU,
                          Endianness.BIG_ENDIAN,
                          PixelPlane.PACKED,
                          8,
                          8,
                          8,
                          8,
                          "YVYU",
                          2,
                          1,
                          fourcc=V4L2_PIX_FMT_YVYU),
    'VYUY':
    SubsampledColorFormat(PixelFormat.VYUY,
                          Endianness.BIG_ENDIAN,
                          PixelPlane.PACKED,
                          8,
                          8,
                          8,
                          8,
                          "VYUY",
                          2,
                          1,
                          fourcc=V4L2_PIX_FMT_VYUY),
    'NV12':
    SubsampledColorFormat(PixelFormat.YUV,
                          Endianness.BIG_ENDIAN,
                          PixelPlane.SEMIPLANAR,
                          8,
                          8,
                          8,
                          name="NV12",
                          subsampling_horizontal=2,
                          subsampling_vertical=2,
                          fourcc=V4L2_PIX_FMT_NV12,
                          palette={
                              "Y": (1., 1., 1.),
                              "U": (1., 0., 1.),
                              "V": (0., 1., 1.)
                          }),
    'NV21':
    SubsampledColorFormat(PixelFormat.YVU,
                          Endianness.BIG_ENDIAN,
                          PixelPlane.SEMIPLANAR,
                          8,
                          8,
                          8,
                          name="NV21",
                          subsampling_horizontal=2,
                          subsampling_vertical=2,
                          fourcc=V4L2_PIX_FMT_NV21,
                          palette={
                              "Y": (1., 1., 1.),
                              "U": (1., 0., 1.),
                              "V": (0., 1., 1.)
                          }),
    'I420':
    SubsampledColorFormat(PixelFormat.YUV,
                          Endianness.BIG_ENDIAN,
                          PixelPlane.PLANAR,
                          8,
                          8,
                          8,
                          name="I420",
                          subsampling_horizontal=2,
                          subsampling_vertical=2,
                          palette={
                              "Y": (1., 1., 1.),
                              "U": (1., 0., 1.),
                              "V": (0., 1., 1.)
                          }),
    'YV12':
    SubsampledColorFormat(PixelFormat.YVU,
                          Endianness.BIG_ENDIAN,
                          PixelPlane.PLANAR,
                          8,
                          8,
                          8,
                          name="YV12",
                          subsampling_horizontal=2,
                          subsampling_vertical=2,
                          fourcc=V4L2_PIX_FMT_YVU420,
                          palette={
                              "Y": (1., 1., 1.),
                              "U": (1., 0., 1.),
                              "V": (0., 1., 1.)
                          }),
    'I422':
    SubsampledColorFormat(PixelFormat.YUV,
                          Endianness.BIG_ENDIAN,
                          PixelPlane.PLANAR,
                          8,
                          8,
                          8,
                          name="I422",
                          subsampling_horizontal=2,
                          subsampling_vertical=1),
    'GRAY':
    ColorFormat(PixelFormat.MONO,
                Endianness.BIG_ENDIAN,
                PixelPlane.PACKED,
                8,
                0,
                0,
                name="GRAY",
                fourcc=V4L2_PIX_FMT_GREY),
    'GRAY10':
    ColorFormat(PixelFormat.MONO,
                Endianness.BIG_ENDIAN,
                PixelPlane.PACKED,
                10,
                0,
                0,
                name="GRAY10",
                fourcc=V4L2_PIX_FMT_Y10),
    'GRAY12':
    ColorFormat(PixelFormat.MONO,
                Endianness.BIG_ENDIAN,
                PixelPlane.PACKED,
                12,
                0,
                0,
                name="GRAY12",
                fourcc=V4L2_PIX_FMT_Y12),
    'BGGR':
    ColorFormat(PixelFormat.BAYER_BG,
                Endianness.BIG_ENDIAN,
                PixelPlane.PACKED,
                8,
                8,
                8,
                name="BGGR",
                fourcc=V4L2_PIX_FMT_SBGGR8,
                palette=rgb_palette()),
    'GBRG':
    ColorFormat(PixelFormat.BAYER_GB,
                Endianness.BIG_ENDIAN,
                PixelPlane.PACKED,
                8,
                8,
                8,
                name="GBRG",
                fourcc=V4L2_PIX_FMT_SGBRG8,
                palette=rgb_palette()),
    'GRBG':
    ColorFormat(PixelFormat.BAYER_GR,
                Endianness.BIG_ENDIAN,
                PixelPlane.PACKED,
                8,
                8,
                8,
                name="GRBG",
                fourcc=V4L2_PIX_FMT_SGRBG8,
                palette=rgb_palette()),
    'RGGB':
    ColorFormat(PixelFormat.BAYER_RG,
                Endianness.BIG_ENDIAN,
                PixelPlane.PACKED,
                8,
                8,
                8,
                name="RGGB",
                fourcc=V4L2_PIX_FMT_SRGGB8,
                palette=rgb_palette()),
    'RG10':
    ColorFormat(PixelFormat.BAYER_RG,
                Endianness.BIG_ENDIAN,
                PixelPlane.PACKED,
                10,
                10,
                10,
                name="RG10",
                fourcc=V4L2_PIX_FMT_SRGGB10),
    'RG12':
    ColorFormat(PixelFormat.BAYER_RG,
                Endianness.BIG_ENDIAN,
                PixelPlane.PACKED,
                12,
                12,
                12,
                name="RG12",
                fourcc=V4L2_PIX_FMT_SRGGB12),
    'RG16':
    ColorFormat(PixelFormat.BAYER_RG,
                Endianness.BIG_ENDIAN,
                PixelPlane.PACKED,
                16,
                16,
                16,
                name="RG16",
                fourcc=V4L2_PIX_FMT_SRGGB16),
    'RG10 (Jetson TX2)':
    ColorFormat(PixelFormat.BAYER_RG,
                Endianness.LITTLE_ENDIAN,
                PixelPlane.PACKED,
                10,
                10,
                10,
                name="RG10",
                platform=Platform.TX2),
    'RG12 (Jetson TX2)':
    ColorFormat(PixelFormat.BAYER_RG,
                Endianness.LITTLE_ENDIAN,
                PixelPlane.PACKED,
                12,
                12,
                12,
                name="RG12",
                platform=Platform.TX2),
    'RG10 (Jetson Xavier)':
    ColorFormat(PixelFormat.BAYER_RG,
                Endianness.LITTLE_ENDIAN,
                PixelPlane.PACKED,
                10,
                10,
                10,
                name="RG10",
                platform=Platform.XAVIER),
    'RG12 (Jetson Xavier)':
    ColorFormat(PixelFormat.BAYER_RG,
                Endianness.LITTLE_ENDIAN,
                PixelPlane.PACKED,
                12,
                12,
                12,
                name="RG12",
                platform=Platform.XAVIER),
}
