import os
import numpy as np
import cv2 as cv
import array

import dearpygui.dearpygui as dpg

from .core import (load_image, get_displayable)
from .image.color_format import AVAILABLE_FORMATS
from .image.color_format import PixelFormat
from .core import determine_color_format, get_displayable, save_image_as_file
from PIL import Image


class MainWindow():
    def __init__(self, args):
        #Viewport configuration
        self.vp = dpg.create_viewport()
        self.vp_size = {"width": 1200, "height": 800}
        self.vp_color = (201, 201, 201)  #alias to #C9C9C9 background color

        self.width = 800
        self.texture = None
        self.img = None
        self.path_to_File = args["FILE_PATH"]

        #Init from args
        if self.path_to_File != None:
            self.width = args["width"]
            self.color_format = args["color_format"]

        self.create_widgets(args)

    def open_file(self, callback_id, data):
        path = list(data["selections"].values())[0]
        if path:
            self.path_to_File = path
            self.update_image(fit_image=True)
            dpg.enable_item(self.menu_bar_export)

    def file_save(self, callback_id, data):
        path = data["file_path_name"]
        if self.img != None:
            im = Image.fromarray(get_displayable(self.img))
            im.save(path)

    def update_image(self, fit_image):
        self.img = load_image(self.path_to_File, self.color_format, self.width)
        self.img_arr = Image.fromarray(get_displayable(self.img))
        self.img_arr.resize((int(self.img.height), int(self.img.width)))
        dpg_image = np.frombuffer(self.img_arr.tobytes(),
                                  dtype=np.uint8) / 255.0
        self.raw_data = array.array('f', dpg_image)

        #Set width and height
        dpg.set_value(self.height_setter, self.img.height)
        dpg.set_value(self.width_setter, self.img.width)

        #Set Image color format in combo
        dpg.set_value(self.combo, self.color_format)

        #Update color format info
        self.update_color_info()

        #Fit data to axis
        if fit_image:
            dpg.fit_axis_data(self.xx)
            dpg.fit_axis_data(self.yy)

        if (self.texture):
            dpg.delete_item(self.texture)
            dpg.delete_item(self.image_series)

        self.add_texture(self.img.width, self.img.height, self.raw_data)
        self.image_series = dpg.add_image_series(
            texture_id=self.texture,
            parent=self.yy,
            label="Raw map",
            bounds_min=[0, 0],
            bounds_max=[self.img.width, self.img.height])
        #Update plot filename
        dpg.set_item_label(self.plot, self.path_to_File)

    def add_texture(self, width, height, image_data):
        with dpg.texture_registry():
            texture_format = None
            if self.img.color_format.pixel_format in [
                    PixelFormat.RGBA, PixelFormat.BGRA, PixelFormat.ARGB,
                    PixelFormat.ABGR
            ]:
                texture_format = dpg.mvFormat_Float_rgba
            else:
                texture_format = dpg.mvFormat_Float_rgb
            self.texture = dpg.add_raw_texture(width=width,
                                               height=height,
                                               format=texture_format,
                                               default_value=image_data)

    def update_width(self, callback_id, data):
        if self.img != None:
            self.width = data
            self.update_image(fit_image=True)

    def update_color_info(self):
        color_format = determine_color_format(self.color_format)
        custom_text= "Pixel format name:  " + color_format.name + "\nEndianness:  " \
                        + str(color_format.endianness)[11:] + "\nPixel format:  " + str(color_format.pixel_format)[12:]+\
                        "\nPixel plane:  " + str(color_format.pixel_plane)[11:] + "\nBits per components:  " + str(color_format.bits_per_components)
        dpg.set_value(self.color_info_text, custom_text)

    def format_color(self, callback_id, data):
        self.color_format = data
        self.update_color_info()
        if self.img != None:
            self.update_image(fit_image=True)

    def init_mainframe(self):
        dpg.set_viewport_title(title='Raviewer')
        dpg.set_viewport_width(self.vp_size["width"])
        dpg.set_viewport_height(self.vp_size["height"])
        dpg.set_viewport_clear_color(self.vp_color)
        dpg.setup_dearpygui(viewport=self.vp)
        dpg.show_viewport(self.vp)

    def run_gui(self):
        dpg.start_dearpygui()

    def on_resize(self, id_callback, data):
        dpg.set_item_height(self.viewport_window, data[1])
        dpg.set_item_width(self.viewport_window, data[0])
        dpg.set_item_width(self.settings_window, int(data[0] / 4))
        relative_x_width = int(data[0] - int(data[0] / 4))
        dpg.set_item_pos(self.settings_window, [relative_x_width, -1])
        dpg.set_item_width(self.main_window, relative_x_width + 2)

    def init_file_dialogs(self):
        #Read from file button
        with dpg.file_dialog(directory_selector=False,
                             show=False,
                             callback=self.open_file,
                             id=self.file_selector_read):
            dpg.add_file_extension("", color=(255, 255, 255, 255))
        #Export image button
        with dpg.file_dialog(directory_selector=False,
                             show=False,
                             callback=self.file_save,
                             id=self.file_selector_export):
            dpg.add_file_extension(".png", color=(255, 255, 0, 255))

    def create_widgets(self, args):
        # Main window frame settings
        self.init_mainframe()

        self.viewport_window = dpg.generate_uuid()
        self.main_window = dpg.generate_uuid()
        self.settings_window = dpg.generate_uuid()
        self.settings_window = dpg.generate_uuid()
        self.plot = dpg.generate_uuid()
        self.menu_bar_file = dpg.generate_uuid()
        self.file_selector_read = dpg.generate_uuid()
        self.file_selector_export = dpg.generate_uuid()
        self.menu_bar_export = dpg.generate_uuid()
        self.init_file_dialogs()

        with dpg.window(label="Docker Window",
                        no_move=True,
                        id=self.viewport_window,
                        no_resize=True,
                        no_scrollbar=True,
                        pos=[0, 0],
                        width=-1,
                        height=-1,
                        no_collapse=True,
                        no_close=True,
                        no_title_bar=True,
                        no_focus_on_appearing=True,
                        autosize=False):

            dpg.set_viewport_resize_callback(callback=self.on_resize)
            #Left Window
            with dpg.child(label="Main Window",
                           id=self.main_window,
                           pos=[0, 0],
                           menubar=True,
                           width=self.vp_size["width"] - 300 + 2,
                           autosize_x=False,
                           autosize_y=True,
                           border=False,
                           height=self.vp_size["height"],
                           horizontal_scrollbar=True):
                with dpg.plot(label="Raw Image",
                              no_menus=True,
                              equal_aspects=True,
                              id=self.plot,
                              height=-1,
                              width=-1):
                    self.xx = dpg.add_plot_axis(label="Width",
                                                axis=1000,
                                                no_gridlines=False,
                                                lock_min=False)

                    self.yy = dpg.add_plot_axis(label="Height",
                                                axis=1001,
                                                no_gridlines=False,
                                                lock_min=False)
                #Add menu bar
                with dpg.menu_bar():
                    dpg.add_menu(label="File", id=self.menu_bar_file)
                #Add menu bar items
                dpg.add_menu_item(
                    label="Open",
                    parent=self.menu_bar_file,
                    callback=lambda: dpg.show_item(self.file_selector_read))
                dpg.add_menu_item(
                    label="Export image",
                    parent=self.menu_bar_file,
                    enabled=False,
                    id=self.menu_bar_export,
                    callback=lambda: dpg.show_item(self.file_selector_export))
            #Right Window
            with dpg.child(label="Setings",
                           id=self.settings_window,
                           height=self.vp_size["height"],
                           width=300,
                           autosize_x=True,
                           autosize_y=True,
                           border=False,
                           pos=[self.vp_size["width"] - 300, 0]):
                with dpg.group(label="Up-group", horizontal=False, pos=[0,
                                                                        25]):

                    option_list = list(AVAILABLE_FORMATS.keys())
                    for index in range(0, len(option_list)):
                        if args["color_format"] == option_list[index]:
                            self.color_format = option_list[index]

                    dpg.add_text(default_value="Color format", indent=5)
                    self.combo = dpg.add_combo(
                        label="Color format",
                        default_value=self.color_format,
                        items=list(option_list),
                        indent=5,
                        callback=self.format_color,
                        height_mode=dpg.mvComboHeight_Regular,
                        width=-1)

                    #Color description button
                    self.color_info_text = dpg.add_text(
                        label="Color format description", indent=5)
                    self.update_color_info()

                    #Resolution change entry
                    with dpg.group(label="Resolution-change-group",
                                   horizontal=False):
                        self.width_setter = dpg.add_input_int(
                            label="Width",
                            min_value=1,
                            default_value=0,
                            max_value=4000,
                            indent=5,
                            callback=self.update_width,
                            on_enter=True)

                        self.height_setter = dpg.add_input_int(label="Height",
                                                               min_value=0,
                                                               indent=5,
                                                               default_value=0,
                                                               readonly=True)

                    dpg.set_item_height(self.viewport_window, 800)
                    dpg.set_item_width(self.viewport_window, 1200)
                    if self.path_to_File != None:
                        self.update_image(fit_image=True)
