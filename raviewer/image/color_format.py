"""Support for abstract color formats."""

from enum import Enum


class PixelFormat(Enum):
    """Respresenation defining color hierachy in pixel."""

    RGBA = 1
    BGRA = 2
    ARGB = 3
    ABGR = 4
    YUYV = 5
    UYVY = 6
    VYUY = 7
    YVYU = 8
    YUV = 9
    YVU = 10
    MONO = 11
    BAYER_RG = 12
    CUSTOM = 0


class Endianness(Enum):
    """Represenation of color format endianness."""

    LITTLE_ENDIAN = 1
    BIG_ENDIAN = 2


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
                 name="unnamed"):
        self.name = name
        self.pixel_format = pixel_format
        self.endianness = endianness
        self.pixel_plane = pixel_plane
        self._bpcs = (bpc1, bpc2, bpc3, bpc4)

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
                 subsampling_vertical=1):
        super().__init__(pixel_format, endianness, pixel_plane, bpc1, bpc2,
                         bpc3, bpc4, name)
        self.subsampling_horizontal = subsampling_horizontal
        self.subsampling_vertical = subsampling_vertical


AVAILABLE_FORMATS = {
    'RGB24':
    ColorFormat(PixelFormat.RGBA,
                Endianness.BIG_ENDIAN,
                PixelPlane.PACKED,
                8,
                8,
                8,
                name="RGB24"),
    'BGR24':
    ColorFormat(PixelFormat.BGRA,
                Endianness.BIG_ENDIAN,
                PixelPlane.PACKED,
                8,
                8,
                8,
                name="BGR24"),
    'RGBA32':
    ColorFormat(PixelFormat.RGBA,
                Endianness.BIG_ENDIAN,
                PixelPlane.PACKED,
                8,
                8,
                8,
                8,
                name="RGBA32"),
    'BGRA32':
    ColorFormat(PixelFormat.BGRA,
                Endianness.BIG_ENDIAN,
                PixelPlane.PACKED,
                8,
                8,
                8,
                8,
                name="BGRA32"),
    'ARGB32':
    ColorFormat(PixelFormat.ARGB,
                Endianness.BIG_ENDIAN,
                PixelPlane.PACKED,
                8,
                8,
                8,
                8,
                name="ARGB32"),
    'ABGR32':
    ColorFormat(PixelFormat.ABGR,
                Endianness.BIG_ENDIAN,
                PixelPlane.PACKED,
                8,
                8,
                8,
                8,
                name="ABGR32"),
    'RGB332':
    ColorFormat(PixelFormat.RGBA,
                Endianness.LITTLE_ENDIAN,
                PixelPlane.PACKED,
                3,
                3,
                2,
                name="RGB332"),
    'RGB565':
    ColorFormat(PixelFormat.RGBA,
                Endianness.LITTLE_ENDIAN,
                PixelPlane.PACKED,
                5,
                6,
                5,
                name="RGB565"),
    'RGBA444':
    ColorFormat(PixelFormat.RGBA,
                Endianness.LITTLE_ENDIAN,
                PixelPlane.PACKED,
                4,
                4,
                4,
                bpc4=4,
                name="RGBA444"),
    'BGRA444':
    ColorFormat(PixelFormat.BGRA,
                Endianness.LITTLE_ENDIAN,
                PixelPlane.PACKED,
                4,
                4,
                4,
                bpc4=4,
                name="BGRA444"),
    'ARGB444':
    ColorFormat(PixelFormat.ARGB,
                Endianness.LITTLE_ENDIAN,
                PixelPlane.PACKED,
                4,
                4,
                4,
                bpc4=4,
                name="ARGB444"),
    'ABGR444':
    ColorFormat(PixelFormat.ABGR,
                Endianness.LITTLE_ENDIAN,
                PixelPlane.PACKED,
                4,
                4,
                4,
                bpc4=4,
                name="ABGR444"),
    'RGBA555':
    ColorFormat(PixelFormat.RGBA,
                Endianness.LITTLE_ENDIAN,
                PixelPlane.PACKED,
                5,
                5,
                5,
                bpc4=1,
                name="RGBA555"),
    'BGRA555':
    ColorFormat(PixelFormat.BGRA,
                Endianness.LITTLE_ENDIAN,
                PixelPlane.PACKED,
                5,
                5,
                5,
                bpc4=1,
                name="BGRA555"),
    'ARGB555':
    ColorFormat(PixelFormat.ARGB,
                Endianness.LITTLE_ENDIAN,
                PixelPlane.PACKED,
                1,
                5,
                5,
                bpc4=5,
                name="ARGB555"),
    'ABGR555':
    ColorFormat(PixelFormat.ABGR,
                Endianness.LITTLE_ENDIAN,
                PixelPlane.PACKED,
                1,
                5,
                5,
                bpc4=5,
                name="ABGR555"),
    'YUY2':
    SubsampledColorFormat(PixelFormat.YUYV, Endianness.BIG_ENDIAN,
                          PixelPlane.PACKED, 8, 8, 8, 8, "YUY2", 2, 1),
    'UYVY':
    SubsampledColorFormat(PixelFormat.UYVY, Endianness.BIG_ENDIAN,
                          PixelPlane.PACKED, 8, 8, 8, 8, "UYVY", 2, 1),
    'YVYU':
    SubsampledColorFormat(PixelFormat.YVYU, Endianness.BIG_ENDIAN,
                          PixelPlane.PACKED, 8, 8, 8, 8, "YVYU", 2, 1),
    'VYUY':
    SubsampledColorFormat(PixelFormat.VYUY, Endianness.BIG_ENDIAN,
                          PixelPlane.PACKED, 8, 8, 8, 8, "UYVY", 2, 1),
    'NV12':
    SubsampledColorFormat(PixelFormat.YUV,
                          Endianness.BIG_ENDIAN,
                          PixelPlane.SEMIPLANAR,
                          8,
                          8,
                          8,
                          name="NV12",
                          subsampling_horizontal=2,
                          subsampling_vertical=2),
    'NV21':
    SubsampledColorFormat(PixelFormat.YVU,
                          Endianness.BIG_ENDIAN,
                          PixelPlane.SEMIPLANAR,
                          8,
                          8,
                          8,
                          name="NV21",
                          subsampling_horizontal=2,
                          subsampling_vertical=2),
    'I420':
    SubsampledColorFormat(PixelFormat.YUV,
                          Endianness.BIG_ENDIAN,
                          PixelPlane.PLANAR,
                          8,
                          8,
                          8,
                          name="I420",
                          subsampling_horizontal=2,
                          subsampling_vertical=2),
    'YV12':
    SubsampledColorFormat(PixelFormat.YVU,
                          Endianness.BIG_ENDIAN,
                          PixelPlane.PLANAR,
                          8,
                          8,
                          8,
                          name="YV12",
                          subsampling_horizontal=2,
                          subsampling_vertical=2),
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
                name="GRAY"),
    'GRAY10':
    ColorFormat(PixelFormat.MONO,
                Endianness.BIG_ENDIAN,
                PixelPlane.PACKED,
                10,
                0,
                0,
                name="GRAY10"),
    'GRAY12':
    ColorFormat(PixelFormat.MONO,
                Endianness.BIG_ENDIAN,
                PixelPlane.PACKED,
                12,
                0,
                0,
                name="GRAY12"),
    'RGGB':
    ColorFormat(PixelFormat.BAYER_RG,
                Endianness.BIG_ENDIAN,
                PixelPlane.PACKED,
                8,
                8,
                8,
                name="RGGB"),
    'RG10':
    ColorFormat(PixelFormat.BAYER_RG,
                Endianness.BIG_ENDIAN,
                PixelPlane.PACKED,
                10,
                10,
                10,
                name="RG10"),
    'RG12':
    ColorFormat(PixelFormat.BAYER_RG,
                Endianness.BIG_ENDIAN,
                PixelPlane.PACKED,
                12,
                12,
                12,
                name="RG12"),
    'RG16':
    ColorFormat(PixelFormat.BAYER_RG,
                Endianness.BIG_ENDIAN,
                PixelPlane.PACKED,
                16,
                16,
                16,
                name="RG16"),
    'RG16l':
    ColorFormat(PixelFormat.BAYER_RG,
                Endianness.LITTLE_ENDIAN,
                PixelPlane.PACKED,
                16,
                16,
                16,
                name="RG16l")
}
