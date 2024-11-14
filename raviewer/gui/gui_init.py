"""Inits the widgets/items building process and parses arguments."""
import dearpygui.dearpygui as dpg

from .. import items
from .main_window import MainWindow
from .settings_window import SettingsWindow
from ..src.events import Events
from ..styles_config.font_config import *
from ..styles_config.theme_config import *
from ..src.controls import Controls


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
        self.events._set_color_format(args['color_format'])

    def init_viewport_spec(self):
        dpg.set_viewport_title(title='Raviewer')
        dpg.set_viewport_width(self.vp_size["width"])
        dpg.set_viewport_height(self.vp_size["height"])
        dpg.set_viewport_clear_color(self.vp_color)
        dpg.setup_dearpygui()
        dpg.show_viewport()

    def run_gui(self):
        while dpg.is_dearpygui_running():
            if self.events.camera_ctrls is not None:
                self.events.camera_ctrls.update_volatile_ctrls()

            self.events.refresh_frame()
            dpg.render_dearpygui_frame()
        '''
        hiding hex tab stops hexdump generation and prevents segfault when closing app while hexdump is being generated
        if hex tab has not been opened, hiding it would throw an error
        '''
        if dpg.does_item_exist(items.windows.hex_tab):
            dpg.hide_item(items.windows.hex_tab)
        dpg.destroy_context()

    def on_resize(self, id_callback, data):
        dpg.set_item_height(items.windows.viewport, data[1])
        dpg.set_item_width(items.windows.viewport, data[0])
        dpg.set_item_width(items.windows.settings, int(data[0] / 4))
        relative_x_width = int(data[0] - int(data[0] / 4))
        dpg.set_item_pos(items.windows.settings, [relative_x_width, -1])
        dpg.set_item_width(items.windows.previewer, relative_x_width + 2)

    def init_file_dialogs(self):
        with dpg.file_dialog(directory_selector=False,
                             show=False,
                             modal=True,
                             label="Open file",
                             callback=self.events.open_file,
                             cancel_callback=cancel_callback,
                             file_count=1,
                             min_size=(600, 200),
                             width=800,
                             height=300,
                             tag=items.file_selector.read):
            dpg.add_file_extension(".*", color=(255, 255, 255, 255))

            dpg.add_combo(tag=items.buttons.file_dialog_color_format,
                          default_value="",
                          items=self.events.list_of_formats + [""],
                          callback=self.events.set_file_dialog_format_color,
                          height_mode=dpg.mvComboHeight_Regular,
                          width=-1)

            dpg.add_input_int(tag=items.buttons.file_dialog_width,
                              label="Width",
                              min_value=0,
                              min_clamped=True,
                              width=170,
                              default_value=0,
                              max_value=4000,
                              max_clamped=True,
                              step=0,
                              callback=self.events.set_file_dialog_width)

            dpg.add_input_int(tag=items.buttons.file_dialog_height,
                              label="Height",
                              min_value=0,
                              width=170,
                              default_value=0,
                              step=0,
                              callback=self.events.set_file_dialog_height)

        with dpg.file_dialog(directory_selector=False,
                             show=False,
                             modal=True,
                             label="Export image",
                             callback=self.events.file_save,
                             cancel_callback=cancel_callback,
                             file_count=1,
                             min_size=(400, 200),
                             tag=items.file_selector.export):
            dpg.add_file_extension(".png", color=(255, 255, 0, 255))
        with dpg.file_dialog(directory_selector=False,
                             show=False,
                             modal=True,
                             label="Export raw frame",
                             callback=self.events.export_raw_buffer,
                             cancel_callback=cancel_callback,
                             file_count=1,
                             min_size=(400, 200),
                             tag=items.file_selector.export_raw_buffer):
            pass
        with dpg.file_dialog(directory_selector=False,
                             show=False,
                             modal=True,
                             label="Export selection as png",
                             callback=self.events.export_as_image,
                             cancel_callback=cancel_callback,
                             file_count=1,
                             min_size=(400, 200),
                             tag=items.file_selector.export_image):
            dpg.add_file_extension(".png", color=(255, 255, 0, 255))
        with dpg.file_dialog(directory_selector=False,
                             show=False,
                             modal=True,
                             label="Export raw selection",
                             callback=self.events.export_raw_selection,
                             cancel_callback=cancel_callback,
                             file_count=1,
                             min_size=(400, 200),
                             tag=items.file_selector.export_raw_selection):
            pass

    def init_loading_indicator(self):
        with dpg.window(label="Loading...",
                        width=50,
                        height=50,
                        show=False,
                        no_focus_on_appearing=True,
                        no_collapse=True,
                        no_resize=True,
                        no_close=True,
                        no_move=True,
                        tag=items.file_selector.loading_indicator):
            dpg.add_loading_indicator(style=1, radius=6, pos=(20, 25))

    def init_mouse_handlers(self):
        with dpg.handler_registry():
            dpg.add_mouse_release_handler(
                callback=self.events.on_mouse_release,
                tag=items.registries.add_mouse_click_handler,
                button=Controls.query_button)
            dpg.add_mouse_drag_handler(button=Controls.query_button,
                                       callback=self.events.on_image_drag)
            dpg.add_mouse_click_handler(button=Controls.query_button,
                                        callback=self.events.on_image_down)
            dpg.add_mouse_wheel_handler(
                callback=self.events.lock_queried_image_callback)
            dpg.add_mouse_drag_handler(
                button=Controls.pan_button,
                callback=self.events.lock_queried_image_callback)
            dpg.add_mouse_drag_handler(
                button=Controls.box_select_button,
                callback=self.events.lock_queried_image_callback)
            dpg.add_mouse_double_click_handler(
                button=Controls.autosize_button,
                callback=self.events.lock_queried_image_callback)
            dpg.add_mouse_click_handler(
                button=Controls.remove_annotation_button,
                callback=self.events.remove_annotation)

    def init_item_handlers(self):
        # Update text wrapping for error modal
        with dpg.item_handler_registry(tag=items.registries.error_size):
            dpg.add_item_resize_handler(callback=self.events.update_error_wrap)
        dpg.bind_item_handler_registry(items.windows.error,
                                       items.registries.error_size)

        # Copy error text
        with dpg.item_handler_registry(tag=items.registries.error_copy):
            dpg.add_item_clicked_handler(callback=self.events.copy_error_text)
            dpg.add_item_visible_handler(
                callback=self.events.set_error_tooltip)
        dpg.bind_item_handler_registry(items.static_text.error,
                                       items.registries.error_copy)

    def init_error_modal(self):
        with dpg.window(label="Error",
                        tag=items.windows.error,
                        modal=True,
                        show=False,
                        width=400,
                        height=200,
                        min_size=(400, 200),
                        on_close=self.events.update_error_size):
            dpg.add_text(default_value="An error has occurred",
                         tag=items.static_text.error)
            with dpg.tooltip(parent=items.static_text.error,
                             tag=items.tooltips.error):
                dpg.add_text(default_value="Click to copy",
                             tag=items.static_text.error_tooltip)

    def init_styles(self):
        dpg.bind_theme(items.theme.general)
        #INFO: Uncomment to bind font with the controls
        #dpg.bind_font(items.fonts.opensans_bold)

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
        self.init_error_modal()
        self.init_item_handlers()
        self.init_loading_indicator()

        if args["FILE_PATH"] != None:
            self.events.update_image(fit_image=True)


def cancel_callback():
    pass
