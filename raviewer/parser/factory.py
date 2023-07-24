"""Factory returning proper parser"""

from .bayer import ParserBayerRG, ParserBayerBG, ParserBayerGB, ParserBayerGR
from ..image.color_format import (PixelPlane, PixelFormat)
from .rgb import ParserARGB, ParserRGBA
from .yuv import (ParserYUV420, ParserYUV420Planar, ParserYUV422,
                  ParserYUV422Planar, ParserYUVSP, ParserYVUSP, ParserYUVP,
                  ParserYVUP, ParserYUYV, ParserUYVY, ParserVYUY, ParserYVYU)
from .grayscale import ParserGrayscale


class ParserFactory:
    """Parser factory"""

    @staticmethod
    def create_object(color_format):
        """Get parser for provided color format.

        Keyword arguments:
            color_format: instance of ColorFormat

        Returns: instance of parser
        """
        mapping = {}
        if color_format.pixel_plane == PixelPlane.PACKED:
            mapping = {
                PixelFormat.BAYER_RG: ParserBayerRG,
                PixelFormat.BAYER_BG: ParserBayerBG,
                PixelFormat.BAYER_GB: ParserBayerGB,
                PixelFormat.BAYER_GR: ParserBayerGR,
                PixelFormat.MONO: ParserGrayscale,
                PixelFormat.RGBA: ParserRGBA,
                PixelFormat.BGRA: ParserRGBA,
                PixelFormat.ARGB: ParserARGB,
                PixelFormat.ABGR: ParserARGB,
                PixelFormat.RGB: ParserRGBA,
                PixelFormat.BGR: ParserRGBA,
                PixelFormat.YUYV: ParserYUYV,
                PixelFormat.UYVY: ParserUYVY,
                PixelFormat.VYUY: ParserVYUY,
                PixelFormat.YVYU: ParserYVYU
            }
        elif color_format.pixel_plane == PixelPlane.SEMIPLANAR:
            mapping = {
                PixelFormat.YUV: ParserYUVSP,
                PixelFormat.YVU: ParserYVUSP,
            }
        elif color_format.pixel_plane == PixelPlane.PLANAR:
            if color_format.subsampling_vertical == 1:
                mapping = {PixelFormat.YUV: ParserYUV422Planar}
            else:
                mapping = {
                    PixelFormat.YUV: ParserYUVP,
                    PixelFormat.YVU: ParserYVUP
                }

        proper_class = mapping.get(color_format.pixel_format)
        if proper_class is None:
            raise NotImplementedError(
                "No parser found for {} color format".format(
                    color_format.name))
        return proper_class()
