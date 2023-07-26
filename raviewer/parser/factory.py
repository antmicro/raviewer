"""Factory returning proper parser"""

from .bayer import ParserBayerRG, ParserBayerBG, ParserBayerGB, ParserBayerGR
from ..image.color_format import (PixelPlane, PixelFormat)
from .rgb import ParserARGB, ParserRGBA
from .yuv import (ParserYUV422P, ParserYUV420SP, ParserYVU420SP, ParserYUV420P,
                  ParserYVU420P, ParserYUYV422PA, ParserUYVY422PA,
                  ParserVYUY422PA, ParserYVYU422PA)
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
                PixelFormat.YUYV: ParserYUYV422PA,
                PixelFormat.UYVY: ParserUYVY422PA,
                PixelFormat.VYUY: ParserVYUY422PA,
                PixelFormat.YVYU: ParserYVYU422PA
            }
        elif color_format.pixel_plane == PixelPlane.SEMIPLANAR:
            mapping = {
                PixelFormat.YUV: ParserYUV420SP,
                PixelFormat.YVU: ParserYVU420SP,
            }
        elif color_format.pixel_plane == PixelPlane.PLANAR:
            if color_format.subsampling_vertical == 1:
                mapping = {PixelFormat.YUV: ParserYUV422P}
            else:
                mapping = {
                    PixelFormat.YUV: ParserYUV420P,
                    PixelFormat.YVU: ParserYVU420P
                }

        proper_class = mapping.get(color_format.pixel_format)
        if proper_class is None:
            raise NotImplementedError(
                "No parser found for {} color format".format(
                    color_format.name))
        return proper_class()
