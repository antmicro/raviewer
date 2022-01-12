"""Inits the widgets/items building process and parses arguments."""
import dearpygui.dearpygui as dpg

from ..items_ids import *
from .main_window import MainWindow
from .settings_window import SettingsWindow
from ..src.events import Events
from ..styles_config.font_config import *
from ..styles_config.theme_config import *


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
        dpg.setup_dearpygui()
        dpg.show_viewport()

    def run_gui(self):
        dpg.start_dearpygui()
        dpg.destroy_context()

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
                             tag=items["file_selector"]["read"]):
            dpg.add_file_extension(".*", color=(255, 255, 255, 255))
        with dpg.file_dialog(directory_selector=False,
                             show=False,
                             callback=self.events.file_save,
                             tag=items["file_selector"]["export"]):
            dpg.add_file_extension(".png", color=(255, 255, 0, 255))
        with dpg.file_dialog(directory_selector=False,
                             show=False,
                             callback=self.events.export_as_image,
                             tag=items["file_selector"]["export_image"]):
            dpg.add_file_extension(".png", color=(255, 255, 0, 255))
        with dpg.file_dialog(directory_selector=False,
                             show=False,
                             callback=self.events.export_as_raw,
                             tag=items["file_selector"]["export_raw"]):
            pass

    def init_mouse_handlers(self):
        with dpg.handler_registry():
            dpg.add_mouse_click_handler(
                callback=self.events.on_mouse_release,
                tag=items["registries"]["add_mouse_click_handler"],
                button=dpg.mvMouseButton_Middle)
            dpg.add_mouse_drag_handler(button=dpg.mvMouseButton_Left,
                                       callback=self.events.on_image_drag)
            dpg.add_mouse_click_handler(button=dpg.mvMouseButton_Left,
                                        callback=self.events.on_image_down)
            dpg.add_mouse_wheel_handler(
                callback=self.events.lock_queried_image_callback)
            dpg.add_mouse_drag_handler(
                button=dpg.mvMouseButton_Middle,
                callback=self.events.lock_queried_image_callback)
            dpg.add_mouse_drag_handler(
                button=dpg.mvMouseButton_Right,
                callback=self.events.lock_queried_image_callback)
            dpg.add_mouse_double_click_handler(
                button=dpg.mvMouseButton_Right,
                callback=self.events.lock_queried_image_callback)
            dpg.add_mouse_click_handler(button=dpg.mvMouseButton_Right,
                                        callback=self.events.remove_annotation)

    def init_styles(self):
        dpg.bind_theme(items["theme"]["global"])
        #INFO: Uncomment to bind font with the controls
        #dpg.bind_font(items["fonts"]["opensans_bold"])

    def create_gui_widgets(self, args):
        self.init_viewport_spec()
        dpg.set_viewport_resize_callback(callback=self.on_resize)

        main_window = MainWindow(self.vp_size)
        main_window.create_widgets()

        settings_window = SettingsWindow(self.vp_size, args)
        settings_window.create_widgets()

        self.init_styles()
        self.init_file_dialogs()
        self.init_mouse_handlers()

        if args["FILE_PATH"] != None:
            self.events.update_image(fit_image=True)
