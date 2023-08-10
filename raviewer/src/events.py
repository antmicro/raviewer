"""Module containing every event description in application."""

import numpy as np
import dearpygui.dearpygui as dpg
from pathlib import Path

from .. import items
from .core import (parse_image, load_image, get_displayable,
                   get_pixel_raw_components, crop_image2rawformat, align_image,
                   load_from_camera)
from ..parser.factory import ParserFactory
from ..image.color_format import PixelFormat, Endianness
from ..image.color_format import AVAILABLE_FORMATS
from ..image.image import Image
from .utils import (RGBtoYUV, determine_color_format, save_image_as_file)
from .hexviewer import Hexviewer
from .controls import Controls
from .camera_ctrls import CameraCtrls
from pyrav4l2 import Device, Stream, WrongFrameInterval
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
    image_mutex = threading.Lock()

    def __init__(self):
        pass


class Plot_events(Base_img):
    """Events assiociated with plot"""

    def __init__(self, use_software_rendering):
        self._use_software_rendering = use_software_rendering

    def update_hexdump(callback):

        def _wrapper(self, app_data, user_data):
            Hexviewer.mutex.acquire()
            Hexviewer.altered = True
            Hexviewer.mutex.release()
            callback(self, app_data, user_data)
            if dpg.does_item_exist(items.windows.hex_tab) or dpg.get_value(
                    items.menu_bar.hex):
                self.show_hex_format()

        return _wrapper

    def indicate_loading(callback):
        """ This function is a decorator that shows loading indicator while executing a function """

        def _wrapper(self, app_data, user_data):
            dpg.show_item(items.file_selector.loading_indicator)
            """
            Position is set as the middle of the viewport subtracted by 25
            (loading indicator has a size of 50x50, so subtracting 25 from both dimensions
            makes it appear roughly in the middle of the window)
            """
            dpg.set_item_pos(
                item=items.file_selector.loading_indicator,
                pos=[
                    i // 2 - 25
                    for i in dpg.get_item_rect_size(items.windows.viewport)
                ])
            callback(self, app_data, user_data)
            dpg.hide_item(items.file_selector.loading_indicator)

        return _wrapper

    @indicate_loading
    def align(self, app_data, user_data):
        with Base_img.image_mutex:
            nnumber = dpg.get_value(items.buttons.nnumber)
            Base_img.nvalues = dpg.get_value(items.buttons.nvalues)
            Base_img.data_buffer = align_image(Base_img.data_buffer,
                                               nnumber - Base_img.nnumber,
                                               Base_img.nvalues)
            Base_img.nnumber = nnumber
            if Base_img.img != None:
                Plot_events.update_image(self, fit_image=False)

    def reverse_bytes(self, app_data, user_data):
        with Base_img.image_mutex:
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
        dpg.set_value(items.buttons.endianness,
                      str(color_format.endianness).split('.')[1])
        dpg.set_value(items.static_text.color_description, custom_text)

    def update_image(self, fit_image, channels=None):
        with dpg.mutex():
            self.refresh_image()
            dpg.set_value(
                items.buttons.height_setter, Base_img.img.height
                if Base_img.height == 0 else Base_img.height)
            dpg.set_value(items.buttons.width_setter, Base_img.img.width)
            dpg.set_value(items.buttons.combo, Base_img.color_format)
            dpg.set_value(items.buttons.n_frames_setter, Base_img.n_frames)

            dpg.configure_item(items.buttons.width_setter, enabled=True)
            dpg.configure_item(items.buttons.height_setter, enabled=True)
            dpg.configure_item(items.buttons.nnumber, enabled=True)
            dpg.configure_item(items.buttons.nvalues, enabled=True)
            dpg.configure_item(items.buttons.reverse, enabled=True)

            self.update_color_info()

            if fit_image:
                dpg.fit_axis_data(items.plot.xaxis)
                dpg.fit_axis_data(items.plot.yaxis)

            if (items.texture.raw):
                dpg.delete_item(Base_img.image_series)

            self.add_texture(Base_img.img.width, Base_img.img.height,
                             Base_img.raw_data)

            Base_img.image_series = dpg.add_image_series(
                texture_tag=items.texture.raw,
                parent=items.plot.yaxis,
                label="Raw map",
                bounds_min=[0, 0],
                bounds_max=[Base_img.img.width, Base_img.img.height])

            dpg.set_item_label(items.plot.main_plot, Base_img.path_to_File)

            if dpg.does_item_exist(items.plot.annotation):
                dpg.delete_item(items.plot.annotation)

    def refresh_image(self):
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
                    "r_y": dpg.get_value(items.buttons.r_ychannel),
                    "g_u": dpg.get_value(items.buttons.g_uchannel),
                    "b_v": dpg.get_value(items.buttons.b_vchannel),
                    "a_v": dpg.get_value(items.buttons.a_vchannel)
                })
        Base_img.raw_data = np.frombuffer(
            Base_img.img_postchanneled.tobytes(),
            dtype=np.uint8).astype("float32") / 255.0
        if Base_img.height < 1: Base_img.height = 0
        if Base_img.height != 0:
            Base_img.n_frames = Base_img.img.height // Base_img.height
        else:
            Base_img.n_frames = 1

    def add_texture(self, width, height, image_data):
        if self._use_software_rendering:
            if (items.texture.raw):
                dpg.delete_item(items.texture.raw)

        with dpg.texture_registry():
            Base_img.texture_format = None
            if Base_img.img.color_format.pixel_format in [
                    PixelFormat.RGBA, PixelFormat.BGRA, PixelFormat.ARGB,
                    PixelFormat.ABGR, PixelFormat.RGB, PixelFormat.BGR
            ]:
                Base_img.texture_format = dpg.mvFormat_Float_rgba
            else:
                Base_img.texture_format = dpg.mvFormat_Float_rgb
            items.texture.raw = dpg.add_raw_texture(
                width=width,
                height=height,
                format=Base_img.texture_format,
                default_value=image_data)

    def on_mouse_release(self, idc, data):
        new_pos = [int(x) for x in dpg.get_plot_mouse_pos()]
        if new_pos != Base_img.mouse_down_pos:
            return

        if dpg.is_item_hovered(items.plot.main_plot):
            if Base_img.img != None:
                plot_mouse_x, plot_mouse_y = dpg.get_plot_mouse_pos()
                if (plot_mouse_x < Base_img.img.width and plot_mouse_x
                        > 0) and (plot_mouse_y < Base_img.img.height
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

                    dpg.set_item_label(items.buttons.rchannel,
                                       f" R:{pixel_values[0]:>3}")
                    dpg.set_item_label(items.buttons.gchannel,
                                       f" G:{pixel_values[1]:>3}")
                    dpg.set_item_label(items.buttons.bchannel,
                                       f" B:{pixel_values[2]:>3}")

                    yuv_pixels = RGBtoYUV(pixel_values, components_n)
                    dpg.set_item_label(items.buttons.ychannel,
                                       f" Y:{yuv_pixels[0]:>3}")
                    dpg.set_item_label(items.buttons.uchannel,
                                       f" U:{yuv_pixels[1]:>3}")
                    dpg.set_item_label(items.buttons.vchannel,
                                       f" V:{yuv_pixels[2]:>3}")
                    first_index = (int(plot_mouse_x) +
                                   row * Base_img.img.width)
                    components = list(
                        get_pixel_raw_components(Base_img.img, row,
                                                 int(plot_mouse_x),
                                                 first_index))
                    bytes_in_components = "Bytes in components " + str(
                        components)
                    if dpg.does_item_exist(items.plot.annotation):
                        dpg.set_item_label(items.plot.annotation,
                                           bytes_in_components)
                        dpg.set_value(
                            items.plot.annotation,
                            (int(plot_mouse_x) + 0.5, int(plot_mouse_y) + 0.5))
                    else:
                        dpg.add_plot_annotation(
                            id=items.plot.annotation,
                            offset=[10, 10],
                            parent=items.plot.main_plot,
                            default_value=(int(plot_mouse_x) + 0.5,
                                           int(plot_mouse_y) + 0.5),
                            color=[0, 134, 255, 255],
                            label=bytes_in_components,
                            clamped=True)

    def on_image_down(self):
        if dpg.is_item_hovered(items.plot.main_plot):
            dpg.configure_item(items.plot.main_plot,
                               pan_button=Controls.pan_button)
        plot_mouse_x, plot_mouse_y = dpg.get_plot_mouse_pos()
        dpg.set_axis_limits_auto(items.plot.xaxis)
        dpg.set_axis_limits_auto(items.plot.yaxis)
        self.yaxis_size = dpg.get_axis_limits(items.plot.yaxis)
        self.xaxis_size = dpg.get_axis_limits(items.plot.xaxis)
        if dpg.is_item_hovered(items.plot.main_plot):
            dpg.set_value(items.static_text.image_resolution, "Size: 0 x 0")
        Base_img.mouse_down_pos = [int(plot_mouse_x), int(plot_mouse_y)]

    def remove_annotation(self):
        if dpg.does_item_exist(items.plot.annotation):
            dpg.delete_item(items.plot.annotation)

    def on_image_drag(self, idc, data):
        dpg.configure_item(items.plot.main_plot, pan_button=Controls.dummy)

        if Base_img.img is None:
            return

        if not dpg.is_item_hovered(items.plot.main_plot):
            return

        start_x, start_y = Base_img.mouse_down_pos
        plot_mouse_x, plot_mouse_y = (int(x) for x in dpg.get_plot_mouse_pos())
        img_x, img_y = Base_img.img.width, Base_img.img.height
        x_resolution, y_resolution = 0, 0

        if start_x >= img_x:
            if plot_mouse_x > 0:
                x_resolution = img_x - plot_mouse_x
                Base_img.right_column = img_x
                Base_img.left_column = plot_mouse_x
            else:
                x_resolution = img_x
                Base_img.right_column = img_x
                Base_img.left_column = 0
        elif start_x <= 0:
            if plot_mouse_x < img_x:
                x_resolution = plot_mouse_x + 1
                Base_img.right_column = plot_mouse_x + 1
                Base_img.left_column = 0
            else:
                x_resolution = img_x
                Base_img.right_column = img_x
                Base_img.left_column = 0
        else:
            if start_x <= plot_mouse_x:
                if plot_mouse_x >= img_x:
                    x_resolution = img_x - start_x
                    Base_img.right_column = img_x
                    Base_img.left_column = start_x
                else:
                    x_resolution = plot_mouse_x - start_x + 1
                    Base_img.right_column = plot_mouse_x + 1
                    Base_img.left_column = start_x
            else:
                if plot_mouse_x < 0:
                    x_resolution = start_x
                    Base_img.right_column = start_x + 1
                    Base_img.left_column = 0
                else:
                    x_resolution = start_x - plot_mouse_x + 1
                    Base_img.right_column = start_x + 1
                    Base_img.left_column = plot_mouse_x
        if start_y >= img_y:
            if plot_mouse_y < 0:
                y_resolution = img_y
                Base_img.up_row = 0
                Base_img.down_row = img_y
            else:
                y_resolution = img_y - plot_mouse_y
                Base_img.up_row = 0
                Base_img.down_row = img_y - plot_mouse_y
        elif start_y <= 0:
            if plot_mouse_y >= img_y:
                y_resolution = img_y
                Base_img.up_row = 0
                Base_img.down_row = img_y
            else:
                y_resolution = plot_mouse_y + 1
                Base_img.up_row = img_y - plot_mouse_y - 1
                Base_img.down_row = img_y
        else:
            if start_y < plot_mouse_y:
                if plot_mouse_y >= img_y:
                    y_resolution = img_y - start_y
                    Base_img.up_row = 0
                    Base_img.down_row = img_y - start_y
                else:
                    y_resolution = plot_mouse_y - start_y + 1
                    Base_img.up_row = img_y - plot_mouse_y - 1
                    Base_img.down_row = img_y - start_y
            else:
                if plot_mouse_y < 0:
                    y_resolution = start_y
                    Base_img.up_row = img_y - start_y - 1
                    Base_img.down_row = img_y
                else:
                    y_resolution = start_y - plot_mouse_y + 1
                    Base_img.up_row = img_y - start_y - 1
                    Base_img.down_row = img_y - plot_mouse_y
        Base_img.selected_part = [x_resolution, y_resolution]
        if x_resolution > 0 and y_resolution > 0:
            dpg.set_value(
                items.static_text.image_resolution,
                "Size: " + str(x_resolution) + " x " + str(y_resolution))

    def change_channel_labels(self):
        if Base_img.img.color_format.pixel_format in [
                PixelFormat.YUYV, PixelFormat.UYVY, PixelFormat.YVYU,
                PixelFormat.VYUY, PixelFormat.YUV, PixelFormat.YVU
        ]:
            dpg.configure_item(items.buttons.r_ychannel, label="Y", show=True)
            dpg.configure_item(items.buttons.g_uchannel, label="U", show=True)
            dpg.configure_item(items.buttons.b_vchannel, label="V", show=True)
            dpg.hide_item(items.buttons.a_vchannel)
        elif Base_img.img.color_format.pixel_format == PixelFormat.MONO:
            dpg.hide_item(items.buttons.r_ychannel)
            dpg.hide_item(items.buttons.g_uchannel)
            dpg.hide_item(items.buttons.b_vchannel)
            dpg.hide_item(items.buttons.a_vchannel)
        else:
            dpg.configure_item(items.buttons.r_ychannel, label="R", show=True)
            dpg.configure_item(items.buttons.g_uchannel, label="G", show=True)
            dpg.configure_item(items.buttons.b_vchannel, label="B", show=True)
            if Base_img.img.color_format.pixel_format in [
                    PixelFormat.ABGR, PixelFormat.ARGB, PixelFormat.RGBA,
                    PixelFormat.BGRA
            ]:
                dpg.show_item(items.buttons.a_vchannel)
            else:
                dpg.hide_item(items.buttons.a_vchannel)


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
            if not dpg.get_value(items.menu_bar.hex):
                dpg.delete_item(items.windows.hex_mode)
                dpg.delete_item(items.windows.hex_tab)
                return True
            if not dpg.does_item_exist(items.windows.hex_tab):
                self.create_tab()

            if dpg.does_item_exist(items.windows.hex_mode):
                dpg.delete_item(items.windows.hex_mode)
            dpg.show_item(items.windows.hex_tab)
            return False
        return True

    def create_tab(self):
        items.windows.hex_tab = dpg.generate_uuid()
        dpg.add_tab(label="Hexdump",
                    parent=items.plot.tab,
                    id=items.windows.hex_tab)

    def create_table(self):
        dpg.add_table(parent=items.windows.hex_tab,
                      id=items.windows.hex_mode,
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
        dpg.add_table_column(label="Offset(h)", parent=items.windows.hex_mode)
        dpg.add_table_column(label="Dump", parent=items.windows.hex_mode)
        dpg.add_table_column(label="ASCII",
                             width=10,
                             parent=items.windows.hex_mode)


class Events(Plot_events, Hexviewer_events, metaclass=meta_events):
    """Events general purpose and inherited from Hexviewer_events, Plot_events"""

    def __init__(self, args):
        Plot_events.__init__(self, args["software_rendering"])
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
        self.camera_ctrls = None

        self.stream_thread = None
        self.frame_ready_event = threading.Event()
        self.stop_streaming_event = threading.Event()
        self.__refresh_available_cameras()

    def lock_queried_image_callback(self):
        if Base_img.img != None and dpg.is_plot_queried(items.plot.main_plot):
            dpg.set_axis_limits(items.plot.yaxis, self.yaxis_size[0],
                                self.yaxis_size[1])
            dpg.set_axis_limits(items.plot.xaxis, self.xaxis_size[0],
                                self.xaxis_size[1])

    @Plot_events.update_hexdump
    @Plot_events.indicate_loading
    def open_file(self, callback_id, data):
        list_of_paths = list(data["selections"].values())
        if len(list_of_paths) > 0:
            path = list_of_paths[0]
            Base_img.path_to_File = path
            Base_img.img = load_image(Base_img.path_to_File)
            Base_img.data_buffer = Base_img.img.data_buffer
            Plot_events.update_image(self, fit_image=True)
            dpg.enable_item(items.menu_bar.export_tab)

    @Plot_events.update_hexdump
    @Plot_events.indicate_loading
    def load_img_from_camera(self, callback_id, data):
        if self.stream_thread is not None:
            self.stop_stream(callback_id, data)
        self._get_frame(dpg.get_value(items.buttons.nframes))

    def _get_frame(self, num_of_frames):
        selected_camera = dpg.get_value(items.buttons.camera)
        selected_format = dpg.get_value(items.buttons.camera_format)
        selected_framesize = dpg.get_value(items.buttons.camera_framesize)

        if selected_camera in self.available_cams.keys(
        ) and selected_format in self.available_formats.keys(
        ) and selected_framesize in self.available_framesizes.keys():
            cam = self.available_cams[selected_camera]
            color_format = self.available_formats[selected_format]
            framesize = self.available_framesizes[selected_framesize]

            cam.set_format(color_format, framesize)

            format_name = next(
                iter(k for k, v in AVAILABLE_FORMATS.items()
                     if v.fourcc == color_format.pixelformat), None)
            if format_name is not None:
                dpg.set_value(item=items.buttons.combo, value=format_name)
                self._format_color(format_name)

            Base_img.path_to_File = cam.path

            Base_img.img = load_from_camera(cam, num_of_frames)
            Base_img.data_buffer = Base_img.img.data_buffer

            Plot_events.update_image(self, fit_image=True)
            dpg.enable_item(items.menu_bar.export_tab)

            dpg.set_value(item=items.buttons.width_setter,
                          value=framesize.width)
            self._update_width(framesize.width)

            return True
        return False

    def start_stream(self, callback_id, data):
        if self._get_frame(1):
            selected_frame_rate = dpg.get_value(items.buttons.frame_rate)
            if selected_frame_rate not in self.available_frame_rates.keys():
                selected_frame_rate = min(
                    self.available_frame_rates.keys(),
                    key=lambda x: abs(float(x) - float(selected_frame_rate)))
            camera = dpg.get_value(items.buttons.camera)

            while True:
                try:
                    self.available_cams[camera].set_frame_interval(
                        self.available_frame_rates[selected_frame_rate])
                    break
                except WrongFrameInterval:
                    selected_format = dpg.get_value(
                        items.buttons.camera_format)
                    selected_framesize = dpg.get_value(
                        items.buttons.camera_framesize)
                    self.__refresh_available_frame_rates(
                        self.available_cams[camera],
                        self.available_formats[selected_format],
                        self.available_framesizes[selected_framesize])
                    selected_frame_rate = list(
                        self.available_frame_rates.keys())[0]
                    dpg.configure_item(items.buttons.frame_rate,
                                       items=list(
                                           self.available_frame_rates.keys()))
            dpg.set_value(items.buttons.frame_rate,
                          self.available_frame_rates[selected_frame_rate])
            dpg.configure_item(item=items.buttons.stream,
                               label="Stop streaming",
                               callback=self.stop_stream)

            self.stream_thread = threading.Thread(
                target=self._refresh_frame,
                args=(self.available_cams[camera], ))
            self.stream_thread.start()

            dpg.disable_item(items.buttons.camera)
            dpg.disable_item(items.buttons.camera_format)
            dpg.disable_item(items.buttons.camera_framesize)
            dpg.disable_item(items.buttons.frame_rate)
            dpg.disable_item(items.buttons.nframes)

    def stop_stream(self, callback, data):
        self.stop_streaming_event.set()
        self.stream_thread.join()
        self.stream_thread = None
        dpg.configure_item(item=items.buttons.stream,
                           label="Start streaming",
                           callback=self.start_stream)

        dpg.enable_item(items.buttons.camera)
        dpg.enable_item(items.buttons.camera_format)
        dpg.enable_item(items.buttons.camera_framesize)
        dpg.enable_item(items.buttons.frame_rate)
        dpg.enable_item(items.buttons.nframes)

    def _refresh_frame(self, camera):
        for frame in Stream(camera):
            if self.stop_streaming_event.is_set():
                self.stop_streaming_event.clear()
                break
            with Base_img.image_mutex:
                Base_img.img = Image(frame)
            self.frame_ready_event.set()

    def refresh_frame(self):
        if self.stream_thread is not None:
            if self.frame_ready_event.is_set():
                self.frame_ready_event.clear()
                Plot_events.refresh_image(self)
                dpg.set_value(item=items.texture.raw, value=Base_img.raw_data)

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
        self._update_width(data)

    def _update_width(self, width):
        with Base_img.image_mutex:
            if Base_img.img != None:
                Base_img.width = width
                Plot_events.update_image(self, fit_image=True)

    def update_height(self, callback_id, data):
        with Base_img.image_mutex:
            if Base_img.img != None:
                Base_img.height = data
                Plot_events.update_image(self, fit_image=True)

    @Plot_events.indicate_loading
    def format_color(self, callback_id, data):
        self._format_color(data)

    def _format_color(self, color_format):
        with Base_img.image_mutex:
            Base_img.color_format = color_format
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
            save_image_as_file(
                Base_img.img_postchanneled[
                    Base_img.up_row:Base_img.down_row,
                    Base_img.left_column:Base_img.right_column], path)

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
        with Base_img.image_mutex:
            if Base_img.img != None:
                Plot_events.update_image(self, fit_image=False)

    def show_gui_metrics(self):
        dpg.show_tool(dpg.mvTool_Metrics)

    def get_available_cameras(self, callback_id, data):
        dpg.set_value(items.buttons.camera, "")
        dpg.hide_item(items.buttons.camera_format)
        dpg.hide_item(items.buttons.camera_framesize)
        dpg.hide_item(items.buttons.frame_rate)

        if self.camera_ctrls is not None:
            self.camera_ctrls.release()
            self.camera_ctrls = None

        self.__refresh_available_cameras()

        dpg.configure_item(items.buttons.camera,
                           items=list(self.available_cams.keys()))

    def get_available_formats(self, callback_id, data):
        dpg.hide_item(items.buttons.camera_framesize)
        dpg.hide_item(items.buttons.frame_rate)
        dpg.set_value(items.buttons.camera_format, "")

        if data in self.available_cams.keys():
            cam = self.available_cams[data]
            if self.camera_ctrls is not None:
                self.camera_ctrls.release()
                self.camera_ctrls = None
            self.camera_ctrls = CameraCtrls(cam)
            self.__refresh_available_formats(cam)

            dpg.configure_item(items.buttons.camera_format,
                               items=list(self.available_formats.keys()))

            dpg.show_item(items.buttons.camera_format)

            current_format, _ = cam.get_format()
            format_names = [
                name
                for (name, color_format) in self.available_formats.items()
                if color_format == current_format
            ]
            if len(format_names) > 0:
                dpg.set_value(item=items.buttons.camera_format,
                              value=format_names[0])

            self.get_available_framesizes(
                callback_id, dpg.get_value(items.buttons.camera_format))

    def get_available_framesizes(self, callback_id, data):
        dpg.set_value(items.buttons.camera_framesize, "")

        if data in self.available_formats.keys():
            cam = self.available_cams[dpg.get_value(items.buttons.camera)]
            color_format = self.available_formats[data]

            self.__refresh_available_framesizes(cam, color_format)

            dpg.configure_item(items.buttons.camera_framesize,
                               items=list(self.available_framesizes.keys()))

            dpg.show_item(items.buttons.camera_framesize)

            _, current_framesize = cam.get_format()
            framesize_names = [
                name
                for (name, framesize) in self.available_framesizes.items()
                if framesize == current_framesize
            ]
            if len(framesize_names) > 0:
                dpg.set_value(item=items.buttons.camera_framesize,
                              value=framesize_names[0])
                self.get_available_frame_rates(
                    callback_id, dpg.get_value(items.buttons.camera_framesize))

    def get_available_frame_rates(self, callback_id, data):
        if data in self.available_framesizes.keys():
            cam = self.available_cams[dpg.get_value(items.buttons.camera)]
            color_format = self.available_formats[dpg.get_value(
                items.buttons.camera_format)]
            framesize = self.available_framesizes[data]

            self.__refresh_available_frame_rates(cam, color_format, framesize)

            dpg.configure_item(items.buttons.frame_rate,
                               items=list(self.available_frame_rates.keys()))
            dpg.set_value(items.buttons.frame_rate,
                          str(cam.get_frame_interval()))
            dpg.show_item(items.buttons.frame_rate)

    def __refresh_available_cameras(self):
        self.available_cams = {}
        for cam in sorted(Path("/dev").glob("video*")):
            dev = Device(cam)
            if dev.is_video_capture_capable:
                self.available_cams[f"{dev.path} ({dev.device_name})"] = dev

    def __refresh_available_formats(self, camera):
        available_formats = camera.available_formats

        self.available_formats = {}
        for color_fmt in available_formats.keys():
            if not color_fmt.is_compressed:
                self.available_formats[str(color_fmt)] = color_fmt

    def __refresh_available_framesizes(self, camera, color_format):
        available_formats = camera.available_formats

        self.available_framesizes = {}
        for size in available_formats[color_format]:
            self.available_framesizes[str(size)] = size

    def __refresh_available_frame_rates(self, camera, color_format, framesize):
        available_frame_rates = camera.get_available_frame_intervals(
            color_format, framesize)

        self.available_frame_rates = {}
        for rate in available_frame_rates:
            self.available_frame_rates[str(rate)] = rate
