"""Representation of cental/main window in application's gui."""

import dearpygui.dearpygui as dpg

from ..items_ids import *
from ..src.events import Events
from ..src.controls import Controls


class MainWindow():
    """Class representing Main Window frame"""

    def __init__(self, vp_conf):
        """Constructs MainWindow instance.

        Keyword arguments:
        vp_conf : Viewport configuration
        """
        self.vp_size = vp_conf
        self.events = Events()

    def create_widgets(self):
        with dpg.window(label="Main docker window",
                        no_move=True,
                        tag=items["windows"]["viewport"],
                        no_resize=True,
                        no_scrollbar=True,
                        pos=[0, 0],
                        width=-1,
                        height=-1,
                        no_collapse=True,
                        no_close=True,
                        no_title_bar=True,
                        no_focus_on_appearing=True,
                        no_bring_to_front_on_focus=True,
                        autosize=True):

            with dpg.child_window(label="Main Window",
                                  tag=items["windows"]["previewer"],
                                  pos=[0, 0],
                                  indent=0,
                                  menubar=True,
                                  width=self.vp_size["width"] - 300 + 2,
                                  autosize_x=False,
                                  autosize_y=True,
                                  border=False,
                                  height=self.vp_size["height"],
                                  horizontal_scrollbar=True):

                with dpg.tab_bar(tag=items["plot"]["tab"]):
                    with dpg.tab(label=" Preview", closable=False):
                        dpg.add_plot(
                            label="Raw data",
                            tag=items["plot"]["main_plot"],
                            no_menus=True,
                            height=-1,
                            pan_button=Controls.pan_button,
                            query_button=Controls.query_button,
                            fit_button=Controls.autosize_button,
                            box_select_button=Controls.box_select_button,
                            crosshairs=True,
                            query=True,
                            equal_aspects=True,
                            width=-1)
                        dpg.add_plot_axis(label="Width",
                                          axis=1000,
                                          tag=items["plot"]["xaxis"],
                                          no_gridlines=False,
                                          lock_min=False,
                                          parent=items["plot"]["main_plot"])

                        dpg.add_plot_axis(label="Height",
                                          axis=1001,
                                          tag=items["plot"]["yaxis"],
                                          no_gridlines=False,
                                          lock_min=False,
                                          parent=items["plot"]["main_plot"])

                    with dpg.tab(label="Camera settings", closable=False):
                        with dpg.group(horizontal=True):
                            dpg.add_text(default_value="Camera:", indent=5)
                            dpg.add_combo(
                                tag=items["buttons"]["camera"],
                                items=list(self.events.available_cams.keys()),
                                height_mode=dpg.mvComboHeight_Regular,
                                width=250,
                                callback=self.events.get_available_formats)
                            dpg.add_button(
                                label="Refresh",
                                callback=self.events.get_available_cameras)

                        with dpg.group(horizontal=True):
                            dpg.add_text(default_value="Format:", indent=5)
                            dpg.add_combo(
                                tag=items["buttons"]["camera_format"],
                                height_mode=dpg.mvComboHeight_Regular,
                                width=250,
                                show=False,
                                callback=self.events.get_available_framesizes)

                        with dpg.group(horizontal=True):
                            dpg.add_text(default_value="Framesize:", indent=5)
                            dpg.add_combo(
                                tag=items["buttons"]["camera_framesize"],
                                height_mode=dpg.mvComboHeight_Regular,
                                width=230,
                                show=False)

                        with dpg.group(horizontal=True):
                            dpg.add_text(default_value="Number of frames:",
                                         indent=5)
                            dpg.add_input_int(width=130,
                                              default_value=1,
                                              min_value=1,
                                              max_value=128,
                                              min_clamped=True,
                                              max_clamped=True,
                                              tag=items["buttons"]["nframes"])

                        dpg.add_separator()
                        dpg.add_button(
                            label="Load frame from camera",
                            indent=5,
                            callback=self.events.load_img_from_camera)

                with dpg.menu_bar():
                    dpg.add_menu(label="File", tag=items["menu_bar"]["file"])
                    dpg.add_menu(label="View", tag=items["menu_bar"]["mode"])

                dpg.add_menu_item(label="Open",
                                  parent=items["menu_bar"]["file"],
                                  callback=lambda: dpg.show_item(items[
                                      "file_selector"]["read"]))
                with dpg.menu(label="Export",
                              parent=items["menu_bar"]["file"]):
                    with dpg.menu(label="PNG"):
                        dpg.add_menu_item(label="Image",
                                          callback=lambda: dpg.show_item(items[
                                              "file_selector"]["export"]))
                        dpg.add_menu_item(
                            label="Selection",
                            tag=items["menu_bar"]["export_tab"],
                            callback=lambda: dpg.show_item(items[
                                "file_selector"]["export_image"]))

                    with dpg.menu(label="RAW"):
                        dpg.add_menu_item(
                            label="Buffer",
                            callback=lambda: dpg.show_item(items[
                                "file_selector"]["export_raw_buffer"]))
                        dpg.add_menu_item(
                            label="Selection",
                            callback=lambda: dpg.show_item(items[
                                "file_selector"]["export_raw_selection"]))
                dpg.add_menu_item(label="Hexdump        ",
                                  parent=items["menu_bar"]["mode"],
                                  check=True,
                                  tag=items["menu_bar"]["hex"],
                                  callback=self.events.show_hex_format)
