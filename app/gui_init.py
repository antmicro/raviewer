"""Inits the widgets/items building process and parses arguments."""
import dearpygui.dearpygui as dpg

from .items_ids import *
from .main_window import MainWindow
from .settings_window import SettingsWindow
from .events import Events


class AppInit():
    """Main application class"""
    def __init__(self, args):
        """Set viewport frame configuration"""
        self.vp = dpg.create_viewport()
        self.vp_size = {"width": 1200, "height": 800}
        #alias to #C9C9C9 background color
        self.vp_color = (201, 201, 201)
        self.events = Events(args)
        self.create_gui_widgets(args)

    def init_viewport_spec(self):
        dpg.set_viewport_title(title='Raviewer')
        dpg.set_viewport_width(self.vp_size["width"])
        dpg.set_viewport_height(self.vp_size["height"])
        dpg.set_viewport_clear_color(self.vp_color)
        dpg.setup_dearpygui(viewport=self.vp)
        dpg.show_viewport(self.vp)

    def run_gui(self):
        dpg.start_dearpygui()

    def on_resize(self, id_callback, data):
        dpg.set_item_height(items["windows"]["viewport"], data[1])
        dpg.set_item_width(items["windows"]["viewport"], data[0])
        dpg.set_item_width(items["windows"]["settings"], int(data[0] / 4))
        relative_x_width = int(data[0] - int(data[0] / 4))
        dpg.set_item_pos(items["windows"]["settings"], [relative_x_width, -1])
        dpg.set_item_width(items["windows"]["previewer"], relative_x_width + 2)

    def init_file_dialogs(self):
        with dpg.file_dialog(directory_selector=False,
                             show=False,
                             callback=self.events.open_file,
                             id=items["file_selector"]["read"]):
            dpg.add_file_extension("", color=(255, 255, 255, 255))
        with dpg.file_dialog(directory_selector=False,
                             show=False,
                             callback=self.events.file_save,
                             id=items["file_selector"]["export"]):
            dpg.add_file_extension(".png", color=(255, 255, 0, 255))
        with dpg.file_dialog(directory_selector=False,
                             show=False,
                             callback=self.events.export_as_image,
                             id=items["file_selector"]["export_image"]):
            dpg.add_file_extension(".png", color=(255, 255, 0, 255))
        with dpg.file_dialog(directory_selector=False,
                             show=False,
                             callback=self.events.export_as_raw,
                             id=items["file_selector"]["export_raw"]):
            pass

    def create_gui_widgets(self, args):
        self.init_viewport_spec()
        self.init_file_dialogs()
        dpg.set_viewport_resize_callback(callback=self.on_resize)

        main_window = MainWindow(self.vp_size)
        main_window.create_widgets()

        settings_window = SettingsWindow(self.vp_size, args)
        settings_window.create_widgets()
