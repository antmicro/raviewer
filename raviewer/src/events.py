"""Module containing every event description in application."""

import numpy as np
import array
import dearpygui.dearpygui as dpg
from math import ceil

from ..items_ids import *
from .core import (parse_image, load_image, get_displayable,
                   get_pixel_raw_components, crop_image2rawformat, align_image)
from ..parser.factory import ParserFactory
from ..image.color_format import PixelFormat, Endianness
from ..image.color_format import AVAILABLE_FORMATS
from PIL import Image
from .utils import (RGBtoYUV, determine_color_format, save_image_as_file)
from .hexviewer import Hexviewer
from .controls import Controls
import threading


class meta_events(type):
    """Needed only for Singleton pattern"""

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(meta_events,
                                        cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Base_img():
    """Class containing image series entity required for core operations and plot state properties.
    Keyword variables:
        img: Image instance
        data_buffer: binary data read from the input file
        path_to_File: location of embraced file
        color_format: actual used color format
        width: actual image series width
        height: frame height
        n_frames: number of frames in the file,
        selected_part: selected area resolution in pixels
        left_column, right_column, up_row, down_row: corner coordinates of selected area 
        texture_format: actual used texture format(mvFormat_Float_rgba or mvFormat_Float_rgb)
        mouse_down_pos: position of right mouse click on plot
        img_postchanneled: image presentation after channel mask staging
        raw_data: image raw data in texture float format
        image_series: image series associated with plot
    """

    img = None
    data_buffer = None
    path_to_File = None
    color_format = None
    width = 800
    height = 0
    n_frames = 1
    selected_part = list()
    left_column, right_column = 0, 0
    up_row, down_row = 0, 0
    texture_format = None
    mouse_down_pos = None
    raw_data = None
    img_postchanneled = None
    image_series = None
    reverse_bytes = 0
    nnumber, nvalues = 0, 0

    def __init__(self):
        pass


class Plot_events(Base_img):
    """Events assiociated with plot"""

    def __init__(self):
        pass

    def update_hexdump(callback):

        def _wrapper(self, app_data, user_data):
            Hexviewer.mutex.acquire()
            Hexviewer.altered = True
            Hexviewer.mutex.release()
            callback(self, app_data, user_data)
            if dpg.does_item_exist(
                    items["windows"]["hex_tab"]) or dpg.get_value(
                        items["menu_bar"]["hex"]):
                self.show_hex_format()

        return _wrapper

    def indicate_loading(callback):
        """ This function is a decorator that shows loading indicator while executing a function """

        def _wrapper(self, app_data, user_data):
            dpg.show_item(items["file_selector"]["loading_indicator"])
            """
            Position is set as the middle of the viewport subtracted by 25
            (loading indicator has a size of 50x50, so subtracting 25 from both dimensions
            makes it appear roughly in the middle of the window)
            """
            dpg.set_item_pos(item=items["file_selector"]["loading_indicator"],
                             pos=[
                                 i // 2 - 25 for i in dpg.get_item_rect_size(
                                     items["windows"]["viewport"])
                             ])
            callback(self, app_data, user_data)
            dpg.hide_item(items["file_selector"]["loading_indicator"])

        return _wrapper

    @indicate_loading
    def align(self, app_data, user_data):
        nnumber = dpg.get_value(items["buttons"]["nnumber"])
        Base_img.nvalues = dpg.get_value(items["buttons"]["nvalues"])
        Base_img.data_buffer = align_image(Base_img.data_buffer,
                                           nnumber - Base_img.nnumber,
                                           Base_img.nvalues)
        Base_img.nnumber = nnumber
        if Base_img.img != None:
            Plot_events.update_image(self, fit_image=False)

    def reverse_bytes(self, app_data, user_data):
        Base_img.reverse_bytes = user_data
        if Base_img.img != None:
            self.update_image(fit_image=True)

    def update_color_info(self):
        color_format = determine_color_format(Base_img.color_format)
        custom_text= "Pixel format name:  " +  color_format.name +\
                        "\nPixel format:  " + str(color_format.pixel_format)[12:]+\
                        "\nPixel plane:  " + str(color_format.pixel_plane)[11:] + "\nBits per component:  " + str(color_format.bits_per_components)
        # Converting enum object to string gives the full attribute name (eg. Endianness.LITTLE_ENDIAN)
        # To properly display endiannes, we must split result string by '.' and take it's second half
        dpg.set_value(items["buttons"]["endianness"],
                      str(color_format.endianness).split('.')[1])
        dpg.set_value(items["static_text"]["color_description"], custom_text)

    def update_image(self, fit_image, channels=None):
        Base_img.img = parse_image(Base_img.img.data_buffer,
                                   Base_img.color_format, Base_img.width,
                                   Base_img.reverse_bytes)
        if Base_img.nnumber or Base_img.nvalues:
            parser = ParserFactory.create_object(
                determine_color_format(Base_img.color_format))
            Base_img.img = parser.parse(
                Base_img.img.data_buffer,
                determine_color_format(Base_img.color_format), Base_img.width,
                Base_img.reverse_bytes)
        self.change_channel_labels()
        if Base_img.img.color_format.pixel_format == PixelFormat.MONO:
            Base_img.img_postchanneled = get_displayable(Base_img.img)
        else:
            Base_img.img_postchanneled = get_displayable(
                Base_img.img, Base_img.height, {
                    "r_y": dpg.get_value(items["buttons"]["r_ychannel"]),
                    "g_u": dpg.get_value(items["buttons"]["g_uchannel"]),
                    "b_v": dpg.get_value(items["buttons"]["b_vchannel"])
                })
        dpg_image = np.frombuffer(Base_img.img_postchanneled.tobytes(),
                                  dtype=np.uint8) / 255.0
        Base_img.raw_data = array.array('f', dpg_image)
        if Base_img.height < 1: Base_img.height = 0
        if Base_img.height != 0:
            Base_img.n_frames = ceil(Base_img.img.height / Base_img.height)
        else:
            Base_img.n_frames = 1
        dpg.set_value(
            items["buttons"]["height_setter"],
            Base_img.img.height if Base_img.height == 0 else Base_img.height)
        dpg.set_value(items["buttons"]["width_setter"], Base_img.img.width)
        dpg.set_value(items["buttons"]["combo"], Base_img.color_format)
        dpg.set_value(items["buttons"]["n_frames_setter"], Base_img.n_frames)

        dpg.configure_item(items["buttons"]["width_setter"], enabled=True)
        dpg.configure_item(items["buttons"]["height_setter"], enabled=True)
        dpg.configure_item(items["buttons"]["nnumber"], enabled=True)
        dpg.configure_item(items["buttons"]["nvalues"], enabled=True)
        dpg.configure_item(items["buttons"]["reverse"], enabled=True)

        self.update_color_info()

        if fit_image:
            dpg.fit_axis_data(items["plot"]["xaxis"])
            dpg.fit_axis_data(items["plot"]["yaxis"])

        if (items["texture"]["raw"]):
            dpg.delete_item(Base_img.image_series)

        self.add_texture(Base_img.img.width, Base_img.img.height,
                         Base_img.raw_data)

        Base_img.image_series = dpg.add_image_series(
            texture_tag=items["texture"]["raw"],
            parent=items["plot"]["yaxis"],
            label="Raw map",
            bounds_min=[0, 0],
            bounds_max=[Base_img.img.width, Base_img.img.height])

        dpg.set_item_label(items["plot"]["main_plot"], Base_img.path_to_File)

        if dpg.does_item_exist(items["plot"]["annotation"]):
            dpg.delete_item(items["plot"]["annotation"])

    def add_texture(self, width, height, image_data):
        with dpg.texture_registry():
            Base_img.texture_format = None
            if Base_img.img.color_format.pixel_format in [
                    PixelFormat.RGBA, PixelFormat.BGRA, PixelFormat.ARGB,
                    PixelFormat.ABGR, PixelFormat.RGB, PixelFormat.BGR
            ]:
                Base_img.texture_format = dpg.mvFormat_Float_rgba
            else:
                Base_img.texture_format = dpg.mvFormat_Float_rgb
            items["texture"]["raw"] = dpg.add_raw_texture(
                width=width,
                height=height,
                format=Base_img.texture_format,
                default_value=image_data)

    def on_mouse_release(self, idc, data):
        if dpg.is_item_hovered(items["plot"]["main_plot"]):
            if Base_img.img != None:
                plot_mouse_x, plot_mouse_y = dpg.get_plot_mouse_pos()
                if (plot_mouse_x < Base_img.img.width and plot_mouse_x > 0
                    ) and (plot_mouse_y < Base_img.img.height
                           and plot_mouse_y > 0):
                    listed_data = Base_img.raw_data.tolist()
                    if Base_img.texture_format == dpg.mvFormat_Float_rgba:
                        components_n = 4
                    else:
                        components_n = 3
                    row = int(Base_img.img.height - plot_mouse_y)
                    row_index = int(
                        plot_mouse_x
                    ) * components_n + row * Base_img.img.width * components_n
                    column_index = row_index + components_n
                    pixel_values = [
                        int(pixel_comp * 255)
                        for pixel_comp in listed_data[row_index:column_index]
                    ]
                    dpg.set_value(items["buttons"]["color_picker"],
                                  pixel_values)
                    yuv_pixels = RGBtoYUV(pixel_values, components_n)
                    dpg.set_item_label(items["buttons"]["ychannel"],
                                       " Y:{} ".format(yuv_pixels[0]))
                    dpg.set_item_label(items["buttons"]["uchannel"],
                                       " U:{} ".format(yuv_pixels[1]))
                    dpg.set_item_label(items["buttons"]["vchannel"],
                                       " V:{} ".format(yuv_pixels[2]))
                    first_index = (int(plot_mouse_x) +
                                   row * Base_img.img.width)
                    components = list(
                        get_pixel_raw_components(Base_img.img, row,
                                                 int(plot_mouse_x),
                                                 first_index))
                    bytes_in_components = "Bytes in components " + str(
                        components)
                    if dpg.does_item_exist(items["plot"]["annotation"]):
                        dpg.set_item_label(items["plot"]["annotation"],
                                           bytes_in_components)
                        dpg.set_value(
                            items["plot"]["annotation"],
                            (int(plot_mouse_x) + 0.5, int(plot_mouse_y) + 0.5))
                    else:
                        dpg.add_plot_annotation(
                            id=items["plot"]["annotation"],
                            offset=[10, 10],
                            parent=items["plot"]["main_plot"],
                            default_value=(int(plot_mouse_x) + 0.5,
                                           int(plot_mouse_y) + 0.5),
                            color=[0, 134, 255, 255],
                            label=bytes_in_components,
                            clamped=True)

    def on_image_down(self):
        if dpg.is_item_hovered(items["plot"]["main_plot"]):
            dpg.configure_item(items["plot"]["main_plot"],
                               pan_button=Controls.pan_button)
        plot_mouse_x, plot_mouse_y = dpg.get_plot_mouse_pos()
        dpg.set_axis_limits_auto(items["plot"]["xaxis"])
        dpg.set_axis_limits_auto(items["plot"]["yaxis"])
        self.yaxis_size = dpg.get_axis_limits(items["plot"]["yaxis"])
        self.xaxis_size = dpg.get_axis_limits(items["plot"]["xaxis"])
        if dpg.is_item_hovered(items["plot"]["main_plot"]):
            dpg.set_value(items["static_text"]["image_resolution"],
                          "Size: 0 x 0")
        Base_img.mouse_down_pos = [int(plot_mouse_x), int(plot_mouse_y)]

    def remove_annotation(self):
        if dpg.does_item_exist(items["plot"]["annotation"]):
            dpg.delete_item(items["plot"]["annotation"])

    def on_image_drag(self, idc, data):
        dpg.configure_item(items["plot"]["main_plot"],
                           pan_button=Controls.dummy)
        x_resolution, y_resolution = 0, 0
        if dpg.is_item_hovered(items["plot"]["main_plot"]):
            if Base_img.img != None:
                plot_mouse_x, plot_mouse_y = dpg.get_plot_mouse_pos()
                if Base_img.mouse_down_pos[0] >= Base_img.img.width:
                    if int(plot_mouse_x) > 0:
                        x_resolution = Base_img.img.width - int(plot_mouse_x)
                        Base_img.right_column = Base_img.img.width
                        Base_img.left_column = int(plot_mouse_x)
                    else:
                        x_resolution = Base_img.img.width
                        Base_img.right_column = Base_img.img.width
                        Base_img.left_column = 0
                elif Base_img.mouse_down_pos[0] <= 0:
                    if int(plot_mouse_x) < Base_img.img.width:
                        x_resolution = int(plot_mouse_x) + 1
                        Base_img.right_column = int(plot_mouse_x) + 1
                        Base_img.left_column = 0
                    else:
                        x_resolution = Base_img.img.width
                        Base_img.right_column = Base_img.img.width
                        Base_img.left_column = 0
                else:
                    if Base_img.mouse_down_pos[0] <= int(plot_mouse_x):
                        if int(plot_mouse_x) >= Base_img.img.width:
                            x_resolution = Base_img.img.width - Base_img.mouse_down_pos[
                                0]
                            Base_img.right_column = Base_img.img.width
                            Base_img.left_column = Base_img.mouse_down_pos[0]
                        else:
                            x_resolution = int(
                                plot_mouse_x) - Base_img.mouse_down_pos[0] + 1
                            Base_img.right_column = int(plot_mouse_x) + 1
                            Base_img.left_column = Base_img.mouse_down_pos[0]
                    else:
                        if int(plot_mouse_x) < 0:
                            x_resolution = Base_img.mouse_down_pos[0]
                            Base_img.right_column = Base_img.mouse_down_pos[
                                0] + 1
                            Base_img.left_column = 0
                        else:
                            x_resolution = Base_img.mouse_down_pos[0] - int(
                                plot_mouse_x) + 1
                            Base_img.right_column = Base_img.mouse_down_pos[
                                0] + 1
                            Base_img.left_column = int(plot_mouse_x)
                if Base_img.mouse_down_pos[1] >= Base_img.img.height:
                    if int(plot_mouse_y) < 0:
                        y_resolution = Base_img.img.height
                        Base_img.up_row = 0
                        Base_img.down_row = Base_img.img.height
                    else:
                        y_resolution = Base_img.img.height - int(plot_mouse_y)
                        Base_img.up_row = 0
                        Base_img.down_row = Base_img.img.height - int(
                            plot_mouse_y)
                elif Base_img.mouse_down_pos[1] <= 0:
                    if int(plot_mouse_y) >= Base_img.img.height:
                        y_resolution = Base_img.img.height
                        Base_img.up_row = 0
                        Base_img.down_row = Base_img.img.height
                    else:
                        y_resolution = int(plot_mouse_y) + 1
                        Base_img.up_row = Base_img.img.height - int(
                            plot_mouse_y) - 1
                        Base_img.down_row = Base_img.img.height
                else:
                    if Base_img.mouse_down_pos[1] < int(plot_mouse_y):
                        if int(plot_mouse_y) >= Base_img.img.height:
                            y_resolution = Base_img.img.height - Base_img.mouse_down_pos[
                                1]
                            Base_img.up_row = 0
                            Base_img.down_row = Base_img.img.height - Base_img.mouse_down_pos[
                                1]
                        else:
                            y_resolution = int(
                                plot_mouse_y) - Base_img.mouse_down_pos[1] + 1
                            Base_img.up_row = Base_img.img.height - int(
                                plot_mouse_y) - 1
                            Base_img.down_row = Base_img.img.height - Base_img.mouse_down_pos[
                                1]
                    else:
                        if int(plot_mouse_y) < 0:
                            y_resolution = Base_img.mouse_down_pos[1]
                            Base_img.up_row = Base_img.img.height - Base_img.mouse_down_pos[
                                1] - 1
                            Base_img.down_row = Base_img.img.height
                        else:
                            y_resolution = Base_img.mouse_down_pos[1] - int(
                                plot_mouse_y) + 1
                            Base_img.up_row = Base_img.img.height - Base_img.mouse_down_pos[
                                1] - 1
                            Base_img.down_row = Base_img.img.height - int(
                                plot_mouse_y)
                Base_img.selected_part = [x_resolution, y_resolution]
                if x_resolution > 0 and y_resolution > 0:
                    dpg.set_value(
                        items["static_text"]["image_resolution"], "Size: " +
                        str(x_resolution) + " x " + str(y_resolution))

    def change_channel_labels(self):
        if Base_img.img.color_format.pixel_format in [
                PixelFormat.YUYV, PixelFormat.UYVY, PixelFormat.YVYU,
                PixelFormat.VYUY, PixelFormat.YUV, PixelFormat.YVU
        ]:
            dpg.configure_item(items["buttons"]["r_ychannel"],
                               label="Y",
                               show=True)
            dpg.configure_item(items["buttons"]["g_uchannel"],
                               label="U",
                               show=True)
            dpg.configure_item(items["buttons"]["b_vchannel"],
                               label="V",
                               show=True)
        elif Base_img.img.color_format.pixel_format == PixelFormat.MONO:
            dpg.hide_item(items["buttons"]["r_ychannel"])
            dpg.hide_item(items["buttons"]["g_uchannel"])
            dpg.hide_item(items["buttons"]["b_vchannel"])
        else:
            dpg.configure_item(items["buttons"]["r_ychannel"],
                               label="R",
                               show=True)
            dpg.configure_item(items["buttons"]["g_uchannel"],
                               label="G",
                               show=True)
            dpg.configure_item(items["buttons"]["b_vchannel"],
                               label="B",
                               show=True)


class Hexviewer_events(Base_img):
    """Events associated with hexadecimal viewer"""
    hex_format = Hexviewer(None, None)

    def __init__(self):
        pass

    def show_hex_format(self):
        status = True
        status = self.resolve_status()
        if status:
            return
        else:
            self.create_hexview()

    def create_hexview(self):
        self.hex_format = Hexviewer(Base_img.img.data_buffer, 16)

        #Create table with columns
        self.create_table()
        #Start processing data
        thr = threading.Thread(target=self.hex_format.processed_content,
                               args=())
        thr.start()

    def resolve_status(self):
        if Base_img.img != None:
            if not dpg.get_value(items["menu_bar"]["hex"]):
                dpg.delete_item(items["windows"]["hex_mode"])
                dpg.delete_item(items["windows"]["hex_tab"])
                return True
            if not dpg.does_item_exist(items["windows"]["hex_tab"]):
                self.create_tab()

            if dpg.does_item_exist(items["windows"]["hex_mode"]):
                dpg.delete_item(items["windows"]["hex_mode"])
            dpg.show_item(items["windows"]["hex_tab"])
            return False
        return True

    def create_tab(self):
        items["windows"]["hex_tab"] = dpg.generate_uuid()
        dpg.add_tab(label="Hexdump",
                    parent=items["plot"]["tab"],
                    id=items["windows"]["hex_tab"])

    def create_table(self):
        dpg.add_table(parent=items["windows"]["hex_tab"],
                      id=items["windows"]["hex_mode"],
                      header_row=True,
                      no_host_extendX=False,
                      delay_search=True,
                      borders_innerH=False,
                      borders_outerH=False,
                      borders_innerV=True,
                      borders_outerV=True,
                      context_menu_in_body=True,
                      row_background=False,
                      policy=dpg.mvTable_SizingFixedFit,
                      height=-1,
                      scrollY=True,
                      scrollX=True,
                      precise_widths=True,
                      resizable=True)
        dpg.add_table_column(label="Offset(h)",
                             parent=items["windows"]["hex_mode"])
        dpg.add_table_column(label="Dump", parent=items["windows"]["hex_mode"])
        dpg.add_table_column(label="ASCII",
                             width=10,
                             parent=items["windows"]["hex_mode"])


class Events(Plot_events, Hexviewer_events, metaclass=meta_events):
    """Events general purpose and inherited from Hexviewer_events, Plot_events"""

    def __init__(self, args):
        Base_img.path_to_File = args["FILE_PATH"]
        option_list = list(AVAILABLE_FORMATS.keys())
        for index in range(0, len(option_list)):
            if args["color_format"] == option_list[index]:
                Base_img.color_format = option_list[index]
        if Base_img.path_to_File != None:
            Base_img.width = args["width"]
            Base_img.color_format = args["color_format"]
            Base_img.height = args["height"]
            Base_img.img = load_image(Base_img.path_to_File)
            Base_img.data_buffer = Base_img.img.data_buffer

    def lock_queried_image_callback(self):
        if Base_img.img != None and dpg.is_plot_queried(
                items["plot"]["main_plot"]):
            dpg.set_axis_limits(items["plot"]["yaxis"], self.yaxis_size[0],
                                self.yaxis_size[1])
            dpg.set_axis_limits(items["plot"]["xaxis"], self.xaxis_size[0],
                                self.xaxis_size[1])

    @Plot_events.update_hexdump
    @Plot_events.indicate_loading
    def open_file(self, callback_id, data):
        path = list(data["selections"].values())[0]
        if path:
            Base_img.path_to_File = path
            Base_img.img = load_image(Base_img.path_to_File)
            Base_img.data_buffer = Base_img.img.data_buffer
            Plot_events.update_image(self, fit_image=True)
            dpg.enable_item(items["menu_bar"]["export_tab"])

    def file_save(self, callback_id, data):
        path = data["file_path_name"]
        if Base_img.img != None:
            save_image_as_file(Base_img.img_postchanneled, path)

    def export_raw_buffer(self, callback_id, data, user_data):
        path = data["file_path_name"]
        if Base_img.img != None:
            with open(path, 'wb') as f:
                f.write(Base_img.img.data_buffer)

    def update_width(self, callback_id, data):
        if Base_img.img != None:
            Base_img.width = data
            Plot_events.update_image(self, fit_image=True)

    def update_height(self, callback_id, data):
        if Base_img.img != None:
            Base_img.height = data
            Plot_events.update_image(self, fit_image=True)

    @Plot_events.indicate_loading
    def format_color(self, callback_id, data):
        Base_img.color_format = data
        Plot_events.update_color_info(self)
        if Base_img.img != None:
            Plot_events.update_image(self, fit_image=True)

    def change_endianness(self, callback_id, data):
        AVAILABLE_FORMATS[Base_img.color_format].endianness = Endianness[data]
        if Base_img.img != None:
            Plot_events.update_image(self, fit_image=True)

    def export_as_image(self, callback_id, data):
        path = data["file_path_name"]
        if Base_img.img != None:
            im = Image.fromarray(Base_img.img_postchanneled[
                Base_img.up_row:Base_img.down_row,
                Base_img.left_column:Base_img.right_column])
            im.save(path)

    def export_raw_selection(self, callback_id, data):
        path = data["file_path_name"]
        return_data = None
        if Base_img.img != None:
            with open(path, "wb") as f:
                return_data = np.array(
                    crop_image2rawformat(Base_img.img, Base_img.up_row,
                                         Base_img.down_row,
                                         Base_img.left_column,
                                         Base_img.right_column))
                return_data = np.frombuffer(return_data.tobytes(),
                                            dtype=np.byte)
                f.write(return_data)

    def set_channels(self):
        if Base_img.img != None:
            Plot_events.update_image(self, fit_image=False)

    def show_gui_metrics(self):
        dpg.show_tool(dpg.mvTool_Metrics)
