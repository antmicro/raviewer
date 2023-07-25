"""Keeps track of items structure in application"""
import dearpygui.dearpygui as dpg

# The itmes defined below are used to keep track of DearPyGui ids for all
# objects, the main keys are converted to dictionaries, the lists they contain
# are converted to keys in those dictionaries, if not default value is
# specified, all values are set to unique dearpygui uuids. Use a tuple to set a
# different default value (see examples below).
# For simplicity, the dictionaries are wrapped in a class that allows dot
# access.
#
# For example, the following:
# __items = {"config": ["abc", "def"] }
#
# can be used as follows
# import items
# print(items.config.abc)   # dot access works
# print(items.config["def"] # key access works
#
# The dot access is prefered in Raviewer to make the code more readable
#
# To give an object a default value, use a tuple
# for example:
# __items = {"config": ["abc", ("def", 1234)] }
#
# items.config.def will be equal 1234 by default.

__items = {
    "windows": [
        "viewport",
        "previewer",
        "settings",
        "hex_mode",
        ("hex_tab", None),
    ],
    "static_text": [
        "color_format",
        "endianness",
        "color_description",
        "image_resolution",
        "selected_pixel",
    ],
    "registries": [
        "texture_registry",
        "add_mouse_click_handler",
    ],
    "buttons": [
        "read_file",
        "combo",
        "endianness",
        "export_image",
        "width_setter",
        "height_setter",
        "anti_checkbox",
        "r_ychannel",
        "g_uchannel",
        "b_vchannel",
        "a_vchannel",
        "rchannel",
        "gchannel",
        "bchannel",
        "ychannel",
        "uchannel",
        "vchannel",
        "append_remove",
        "nnumber",
        "nvalues",
        "nnumber_every_frame",
        "raw_display",
        "n_frames_setter",
        "frame_setter",
        "reverse",
        "nframes",
        "camera",
        "camera_format",
        "camera_framesize",
        "stream",
        "frame_rate",
    ],
    "groups": ["camera_ctrls", "palette", "raw_view"],
    "menu_bar": [
        "export_tab",
        "file",
        "mode",
        "hex",
        "tools",
        "metrics",
        "font",
    ],
    "texture": [
        ("raw", None),
    ],
    "plot": [
        "main_plot",
        "xaxis",
        "yaxis",
        "annotation",
        "tab",
    ],
    "file_selector": [
        "read",
        "export",
        "export_raw_buffer",
        "export_image",
        "export_raw_selection",
        "loading_indicator",
    ],
    "fonts": [
        "opensans_bold",
        "opensans_bolditalic",
        "opensans_extrabold",
        "opensans_extrabolditalic",
        "opensans_italic",
        "opensans_light",
        "opensans_lightitalic",
        "opensans_regular",
        "opensans_semibold",
        "opensans_semibolditalic",
    ],
    "theme": [
        "general",
    ]
}


class __RaviewerItem(dict):
    __getattr__ = dict.get
    __delattr__ = dict.__delitem__

    def __setattr__(self, name, value):
        if name in self.keys():
            dict.__setitem__(self, name, value)
        else:
            raise KeyError(f"Item undefined: {name}")


for k in __items:
    globals()[k] = __RaviewerItem()
    for j in __items[k]:
        if type(j) is not tuple:
            globals()[k][j] = dpg.generate_uuid()
        else:
            n, v = j
            globals()[k][n] = v
