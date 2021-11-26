"""Representation of cental/main window in application's gui."""

import dearpygui.dearpygui as dpg

from ..items_ids import *
from ..src.events import Events


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
                        id=items["windows"]["viewport"],
                        no_resize=True,
                        no_scrollbar=True,
                        pos=[0, 0],
                        width=-1,
                        height=-1,
                        no_collapse=True,
                        no_close=True,
                        no_title_bar=True,
                        no_focus_on_appearing=True,
                        autosize=True):

            with dpg.child(label="Main Window",
                           id=items["windows"]["previewer"],
                           pos=[0, 0],
                           indent=0,
                           menubar=True,
                           width=self.vp_size["width"] - 300 + 2,
                           autosize_x=False,
                           autosize_y=True,
                           border=False,
                           height=self.vp_size["height"],
                           horizontal_scrollbar=True):

                with dpg.tab_bar(id=items["plot"]["tab"]):
                    with dpg.tab(label=" Preview", closable=False):
                        dpg.add_text(default_value="Selected image resolution: 0x0",
                            indent=5,
                            show=True,
                            id=items["static_text"]["image_resolution"])
                        dpg.add_plot(label="Raw data",
                                     id=items["plot"]["main_plot"],
                                     no_menus=True,
                                     height=-1,
                                     crosshairs=True,
                                     query=True,
                                     equal_aspects=True,
                                     width=-1)
                        dpg.add_plot_axis(label="Width",
                                          axis=1000,
                                          id=items["plot"]["xaxis"],
                                          no_gridlines=False,
                                          lock_min=False,
                                          parent=items["plot"]["main_plot"])

                        dpg.add_plot_axis(label="Height",
                                          axis=1001,
                                          id=items["plot"]["yaxis"],
                                          no_gridlines=False,
                                          lock_min=False,
                                          parent=items["plot"]["main_plot"])

                with dpg.menu_bar():
                    dpg.add_menu(label="File", id=items["menu_bar"]["file"])
                    dpg.add_menu(label="View", id=items["menu_bar"]["mode"])
                    dpg.add_menu(label="Preferences", id=items["menu_bar"]["tools"])

                dpg.add_menu_item(label="Open",
                                  parent=items["menu_bar"]["file"],
                                  callback=lambda: dpg.show_item(items[
                                      "file_selector"]["read"]))
                dpg.add_menu_item(label="Export image",
                                  parent=items["menu_bar"]["file"],
                                  callback=lambda: dpg.show_item(items[
                                      "file_selector"]["export"]))
                dpg.add_menu_item(label="Export part as image",
                                  parent=items["menu_bar"]["file"],
                                  id=items["menu_bar"]["export_tab"],
                                  shortcut="| Middle Mouse",
                                  callback=lambda: dpg.show_item(items[
                                      "file_selector"]["export_image"]))
                dpg.add_menu_item(label="Export part as raw",
                                  shortcut="| Middle Mouse",
                                  parent=items["menu_bar"]["file"],
                                  callback=lambda: dpg.show_item(items[
                                      "file_selector"]["export_raw"]))

                dpg.add_menu_item(label="Hexdump        ",
                                  parent=items["menu_bar"]["mode"],
                                  check=True,
                                  id=items["menu_bar"]["hex"],
                                  callback=self.events.show_hex_format)

                dpg.add_menu_item(label="Theme manager",
                                  parent=items["menu_bar"]["tools"],
                                  id=items["menu_bar"]["theme"],
                                  callback=dpg.show_style_editor)
