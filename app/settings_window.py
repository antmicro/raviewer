"""Representation of  right settings window in application's gui."""
import dearpygui.dearpygui as dpg

from .items_ids import *
from .image.color_format import AVAILABLE_FORMATS
from .events import Events


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
        with dpg.child(label="Setings",
                       id=items["windows"]["settings"],
                       height=self.vp_size["height"],
                       width=300,
                       autosize_x=True,
                       autosize_y=True,
                       border=False,
                       parent=items["windows"]["viewport"],
                       pos=[self.vp_size["width"] - 300, 0]):
            with dpg.group(label="Up-group", horizontal=False, pos=[0, 25]):
                dpg.add_text(default_value="Color format",
                             indent=5,
                             id=items["static_text"]["color_format"])

                option_list = list(AVAILABLE_FORMATS.keys())

                dpg.add_combo(label="Color format",
                              id=items["buttons"]["combo"],
                              default_value=self.events.color_format,
                              items=list(option_list),
                              indent=5,
                              callback=self.events.format_color,
                              height_mode=dpg.mvComboHeight_Regular,
                              width=-1)

                dpg.add_text(label="Color format description",
                             indent=5,
                             id=items["static_text"]["color_description"])

                self.events.update_color_info()

                with dpg.group(label="Resolution-change-group",
                               horizontal=False):
                    self.width_setter = dpg.add_input_int(
                        id=items["buttons"]["width_setter"],
                        label="Width",
                        min_value=1,
                        default_value=0,
                        max_value=4000,
                        indent=5,
                        callback=self.events.update_width,
                        on_enter=True)

                    dpg.add_input_int(label="Height",
                                      id=items["buttons"]["height_setter"],
                                      min_value=0,
                                      indent=5,
                                      default_value=0,
                                      readonly=True)

                dpg.add_separator()
                dpg.add_color_picker(label="Color-picker",
                                     id=items["buttons"]["color_picker"],
                                     no_alpha=True,
                                     indent=5)
                with dpg.group(label="Resolution-change-group",
                               horizontal=True):
                    dpg.add_button(label=" Y:  0 ",
                                   width=58,
                                   id=items["buttons"]["ychannel"],
                                   indent=5)
                    dpg.add_button(label=" U:  0 ",
                                   width=58,
                                   id=items["buttons"]["uchannel"])
                    dpg.add_button(label=" V:  0 ",
                                   width=58,
                                   id=items["buttons"]["vchannel"])
                dpg.add_separator()
                dpg.add_text(default_value="Available channels mask: ",
                             indent=5)
                with dpg.group(horizontal=True):
                    dpg.add_checkbox(label="R",
                                     callback=self.events.set_channels,
                                     id=items["buttons"]["r_ychannel"],
                                     indent=5,
                                     default_value=True)
                    dpg.add_checkbox(label="G",
                                     callback=self.events.set_channels,
                                     id=items["buttons"]["g_uchannel"],
                                     default_value=True)
                    dpg.add_checkbox(label="B",
                                     callback=self.events.set_channels,
                                     id=items["buttons"]["b_vchannel"],
                                     default_value=True)

                dpg.set_item_height(items["windows"]["viewport"], 800)
                dpg.set_item_width(items["windows"]["viewport"], 1200)

                dpg.add_text(default_value="Selected image resolution: 0x0",
                             indent=5,
                             show=True,
                             id=items["static_text"]["image_resolution"])
                dpg.add_separator()
                with dpg.group(horizontal=True):
                    dpg.add_text(indent=5, default_value="Count:")
                    dpg.add_input_int(width=130,
                                      min_value=0,
                                      max_value=1000000,
                                      id=items["buttons"]["nnumber"])
                with dpg.group(horizontal=True):
                    dpg.add_text(indent=5, default_value="Value:")
                    dpg.add_input_int(width=130,
                                      min_value=0,
                                      max_value=255,
                                      id=items["buttons"]["nvalues"])
                with dpg.group(horizontal=True):
                    dpg.add_text(indent=5, default_value="Mode:")
                    dpg.add_radio_button(("Append", "Remove"),
                                         default_value="Append",
                                         horizontal=True,
                                         id=items["buttons"]["append_remove"])
                with dpg.theme(id="theme"):
                    dpg.add_theme_color(dpg.mvThemeCol_Button, (200, 0, 0))
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonActive,
                                        (250, 0, 0))
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered,
                                        (220, 0, 0))
                    dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 9)
                    dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 6, 2)

                dpg.add_button(label="Execute on image series",
                               indent=5,
                               callback=self.events.align)
                dpg.set_item_theme(dpg.last_item(), "theme")
                dpg.add_separator()
