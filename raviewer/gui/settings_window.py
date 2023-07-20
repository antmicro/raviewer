"""Representation of  right settings window in application's gui."""
import dearpygui.dearpygui as dpg

from .. import items
from ..image.color_format import AVAILABLE_FORMATS
from ..src.events import Events


class SettingsWindow():
    """Class representing Settingsframe"""

    def __init__(self, vp_size, args):
        """Constructs SettingsWindow instance.
        Keyword arguments:
        vp_size: Viewport configuration
        args: arguments in terminal mode
        """
        self.vp_size = vp_size
        self.args = args
        self.events = Events()

    def create_widgets(self):
        with dpg.child_window(label="Setings",
                              tag=items.windows.settings,
                              height=self.vp_size["height"],
                              width=300,
                              autosize_x=True,
                              autosize_y=True,
                              border=False,
                              parent=items.windows.viewport,
                              horizontal_scrollbar=True,
                              pos=[self.vp_size["width"] - 300, 0]):
            with dpg.group(label="Up-group", horizontal=False, pos=[0, 25]):
                dpg.add_text(default_value="Color format",
                             indent=5,
                             tag=items.static_text.color_format)

                option_list = list(AVAILABLE_FORMATS.keys())

                dpg.add_combo(tag=items.buttons.combo,
                              default_value=self.events.color_format,
                              items=list(option_list),
                              indent=5,
                              callback=self.events.format_color,
                              height_mode=dpg.mvComboHeight_Regular,
                              width=-1)

                dpg.add_text(default_value="Endianness",
                             indent=5,
                             tag=items.static_text.endianness)

                option_endianness = ["LITTLE_ENDIAN", "BIG_ENDIAN"]

                dpg.add_combo(tag=items.buttons.endianness,
                              items=list(option_endianness),
                              indent=5,
                              callback=self.events.change_endianness,
                              height_mode=dpg.mvComboHeight_Regular,
                              width=-1)

                dpg.add_text(label="Color format description",
                             indent=5,
                             tag=items.static_text.color_description)

                self.events.update_color_info()

                with dpg.group(label="Resolution-change-group",
                               horizontal=False):
                    self.width_setter = dpg.add_input_int(
                        tag=items.buttons.width_setter,
                        label="Width",
                        min_value=1,
                        min_clamped=True,
                        width=170,
                        default_value=0,
                        enabled=False,
                        max_value=4000,
                        max_clamped=True,
                        indent=5,
                        callback=self.events.update_width,
                        on_enter=True)

                    dpg.add_input_int(label="Height",
                                      tag=items.buttons.height_setter,
                                      min_value=0,
                                      indent=5,
                                      width=170,
                                      default_value=0,
                                      callback=self.events.update_height,
                                      on_enter=True,
                                      enabled=False)
                    dpg.add_input_int(label="Number of frames",
                                      tag=items.buttons.n_frames_setter,
                                      min_value=1,
                                      min_clamped=True,
                                      readonly=True,
                                      default_value=1,
                                      width=100,
                                      indent=5,
                                      step=0,
                                      step_fast=0)
                dpg.add_separator()
                dpg.add_text("Selected pixel values",
                             indent=5,
                             tag=items.static_text.selected_pixel)
                with dpg.group(label="RGB data group", horizontal=True):
                    dpg.add_button(label=" R:  0 ",
                                   width=51,
                                   tag=items.buttons.rchannel,
                                   indent=5)
                    dpg.add_button(label=" G:  0 ",
                                   width=51,
                                   tag=items.buttons.gchannel)
                    dpg.add_button(label=" B:  0 ",
                                   width=51,
                                   tag=items.buttons.bchannel)
                with dpg.group(label="YUV data group", horizontal=True):
                    dpg.add_button(label=" Y:  0 ",
                                   width=51,
                                   tag=items.buttons.ychannel,
                                   indent=5)
                    dpg.add_button(label=" U:  0 ",
                                   width=51,
                                   tag=items.buttons.uchannel)
                    dpg.add_button(label=" V:  0 ",
                                   width=51,
                                   tag=items.buttons.vchannel)
                dpg.add_separator()
                dpg.add_text(default_value="Available channels mask", indent=5)
                with dpg.group(horizontal=True):
                    dpg.add_checkbox(label="R",
                                     callback=self.events.set_channels,
                                     tag=items.buttons.r_ychannel,
                                     indent=5,
                                     default_value=True)
                    dpg.add_checkbox(label="G",
                                     callback=self.events.set_channels,
                                     tag=items.buttons.g_uchannel,
                                     default_value=True)
                    dpg.add_checkbox(label="B",
                                     callback=self.events.set_channels,
                                     tag=items.buttons.b_vchannel,
                                     default_value=True)
                    dpg.add_checkbox(label="A",
                                     callback=self.events.set_channels,
                                     tag=items.buttons.a_vchannel,
                                     default_value=True)

                dpg.set_item_height(items.windows.viewport, 800)
                dpg.set_item_width(items.windows.viewport, 1200)
                dpg.add_separator()
                dpg.add_text(
                    default_value="Add/Skip data at the start of the data",
                    indent=5,
                    show=True)
                with dpg.group(horizontal=True):
                    dpg.add_text(indent=5, default_value="Count:")
                    dpg.add_input_int(width=130,
                                      min_value=-1000000,
                                      max_value=1000000,
                                      enabled=False,
                                      tag=items.buttons.nnumber)
                    dpg.add_button(label="apply", callback=self.events.align)
                with dpg.group(horizontal=True):
                    dpg.add_text(indent=5, default_value="Value:")
                    dpg.add_input_int(width=130,
                                      min_value=0,
                                      max_value=255,
                                      enabled=False,
                                      tag=items.buttons.nvalues)
                dpg.add_checkbox(label="Add/skip data in every frame",
                                 indent=5,
                                 tag=items.buttons.nnumber_every_frame)
                dpg.add_separator()
                dpg.add_text(default_value="Reverse bytes", indent=5)
                with dpg.group(horizontal=False):
                    dpg.add_input_int(width=130,
                                      default_value=1,
                                      min_value=1,
                                      min_clamped=True,
                                      indent=5,
                                      enabled=False,
                                      callback=self.events.reverse_bytes,
                                      tag=items.buttons.reverse)
                dpg.add_separator()
                dpg.add_text(default_value="Selection", indent=5, show=True)
                dpg.add_text(default_value="Size: 0 x 0",
                             indent=5,
                             show=True,
                             tag=items.static_text.image_resolution)
                dpg.add_separator()

                dpg.add_checkbox(label="Raw view",
                                 indent=5,
                                 callback=self.events.display_raw,
                                 tag=items.buttons.raw_display)

                dpg.add_group(label="Palette group", tag=items.groups.palette)
                dpg.add_separator()
