"""Set up application's fonts"""

import dearpygui.dearpygui as dpg
import os
import pkg_resources
from .. import items

with dpg.font_registry() as font_registry:
    dpg.add_font(pkg_resources.resource_filename('raviewer',
                                                 '/fonts/OpenSans-Bold.ttf'),
                 16,
                 id=items.fonts.opensans_bold)
    dpg.add_font(pkg_resources.resource_filename(
        'raviewer', '/fonts/OpenSans-BoldItalic.ttf'),
                 16,
                 id=items.fonts.opensans_bolditalic)
    dpg.add_font(pkg_resources.resource_filename(
        'raviewer', '/fonts/OpenSans-ExtraBold.ttf'),
                 16,
                 id=items.fonts.opensans_extrabold)
    dpg.add_font(pkg_resources.resource_filename(
        'raviewer', '/fonts/OpenSans-ExtraBoldItalic.ttf'),
                 16,
                 id=items.fonts.opensans_extrabolditalic)
    dpg.add_font(pkg_resources.resource_filename('raviewer',
                                                 '/fonts/OpenSans-Italic.ttf'),
                 16,
                 id=items.fonts.opensans_italic)
    dpg.add_font(pkg_resources.resource_filename('raviewer',
                                                 '/fonts/OpenSans-Light.ttf'),
                 16,
                 id=items.fonts.opensans_light)
    dpg.add_font(pkg_resources.resource_filename(
        'raviewer', '/fonts/OpenSans-LightItalic.ttf'),
                 16,
                 id=items.fonts.opensans_lightitalic)
    dpg.add_font(pkg_resources.resource_filename(
        'raviewer', '/fonts/OpenSans-Regular.ttf'),
                 16,
                 id=items.fonts.opensans_regular)
    dpg.add_font(pkg_resources.resource_filename(
        'raviewer', '/fonts/OpenSans-Semibold.ttf'),
                 16,
                 id=items.fonts.opensans_semibold)
    dpg.add_font(pkg_resources.resource_filename(
        'raviewer', '/fonts/OpenSans-SemiboldItalic.ttf'),
                 16,
                 id=items.fonts.opensans_semibolditalic)
