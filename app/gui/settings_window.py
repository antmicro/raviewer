"""Representation of  right settings window in application's gui."""
import dearpygui.dearpygui as dpg

from ..items_ids import *
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
                       tag=items["windows"]["settings"],
                       height=self.vp_size["height"],
                       width=300,
                       autosize_x=True,
                       autosize_y=True,
                       border=False,
                       parent=items["windows"]["viewport"],
                       horizontal_scrollbar=True,
                       pos=[self.vp_size["width"] - 300, 0]):
            with dpg.group(label="Up-group", horizontal=False, pos=[0, 25]):
                dpg.add_text(default_value="Color format",
                             indent=5,
                             tag=items["static_text"]["color_format"])

                option_list = list(AVAILABLE_FORMATS.keys())

                dpg.add_combo(tag=items["buttons"]["combo"],
                              default_value=self.events.color_format,
                              items=list(option_list),
                              indent=5,
                              callback=self.events.format_color,
                              height_mode=dpg.mvComboHeight_Regular,
                              width=-1)

                dpg.add_text(label="Color format description",
                             indent=5,
                             tag=items["static_text"]["color_description"])

                self.events.update_color_info()

                with dpg.group(label="Resolution-change-group",
                               horizontal=False):
                    self.width_setter = dpg.add_input_int(
                        tag=items["buttons"]["width_setter"],
                        label="Width",
                        min_value=1,
                        width=170,
                        default_value=0,
                        max_value=4000,
                        indent=5,
                        callback=self.events.update_width,
                        on_enter=True)

                    dpg.add_input_int(label="Height",
                                      tag=items["buttons"]["height_setter"],
                                      min_value=0,
                                      indent=5,
                                      width=170,
                                      default_value=0,
                                      readonly=True)

                dpg.add_separator()
                dpg.add_color_picker(label="Color picker",
                                     tag=items["buttons"]["color_picker"],
                                     no_alpha=True,
                                     picker_mode=dpg.mvColorPicker_bar,
                                     no_side_preview=True,
                                     width=170,
                                     no_small_preview=True,
                                     no_label=True,
                                     indent=5)
                with dpg.group(label="Resolution-change-group",
                               horizontal=True):
                    dpg.add_button(label=" Y:  0 ",
                                   width=51,
                                   tag=items["buttons"]["ychannel"],
                                   indent=5)
                    dpg.add_button(label=" U:  0 ",
                                   width=51,
                                   tag=items["buttons"]["uchannel"])
                    dpg.add_button(label=" V:  0 ",
                                   width=51,
                                   tag=items["buttons"]["vchannel"])
                dpg.add_separator()
                dpg.add_text(default_value="Available channels mask", indent=5)
                with dpg.group(horizontal=True):
                    dpg.add_checkbox(label="R",
                                     callback=self.events.set_channels,
                                     tag=items["buttons"]["r_ychannel"],
                                     indent=5,
                                     default_value=True)
                    dpg.add_checkbox(label="G",
                                     callback=self.events.set_channels,
                                     tag=items["buttons"]["g_uchannel"],
                                     default_value=True)
                    dpg.add_checkbox(label="B",
                                     callback=self.events.set_channels,
                                     tag=items["buttons"]["b_vchannel"],
                                     default_value=True)

                dpg.set_item_height(items["windows"]["viewport"], 800)
                dpg.set_item_width(items["windows"]["viewport"], 1200)
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
                                      callback=self.events.align,
                                      tag=items["buttons"]["nnumber"])
                with dpg.group(horizontal=True):
                    dpg.add_text(indent=5, default_value="Value:")
                    dpg.add_input_int(width=130,
                                      min_value=0,
                                      max_value=255,
                                      tag=items["buttons"]["nvalues"])
                dpg.add_separator()
