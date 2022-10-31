import dearpygui.dearpygui as dpg
from pyrav4l2 import *
from abc import ABC, abstractmethod
import logging

from .. import items


class CameraCtrls:

    def __init__(self, camera):
        self.camera = camera

        self.controls = {}
        current_class = None
        for ctrl in self.camera.controls:
            if ctrl.type == V4L2_CTRL_TYPE_CTRL_CLASS:
                current_class = ctrl.name
                self.controls[current_class] = Group(current_class)
            elif current_class in self.controls.keys():
                self.controls[current_class].append_ctrl(self.camera, ctrl)

        dpg.show_item(items.groups.camera_ctrls)

    def release(self):
        for ctrl_class in self.controls.keys():
            self.controls[ctrl_class].release()

    def update_volatile_ctrls(self):
        for ctrl_class in self.controls.keys():
            self.controls[ctrl_class].update_volatile_ctrls()


class Group:

    def __init__(self, name):
        self.name = name
        self.controls = []
        self.group = dpg.add_group(parent=items.groups.camera_ctrls, indent=5)
        dpg.add_separator(parent=self.group)
        dpg.add_text(default_value=name, parent=self.group)

    def release(self):
        dpg.delete_item(self.group)

    def append_ctrl(self, device, ctrl):
        if not ctrl.is_disabled:
            if ctrl.type == V4L2_CTRL_TYPE_INTEGER:
                if ctrl.minimum >= -2**30 and ctrl.maximum <= 2**30 - 1:
                    self.controls.append(
                        IntCtrl(device, ctrl, self.group, self.update_ctrls))
                else:
                    self.controls.append(
                        BigIntCtrl(device, ctrl, self.group,
                                   self.update_ctrls))
            elif ctrl.type == V4L2_CTRL_TYPE_BOOLEAN:
                self.controls.append(
                    BoolCtrl(device, ctrl, self.group, self.update_ctrls))
            elif ctrl.type == V4L2_CTRL_TYPE_MENU:
                self.controls.append(
                    MenuCtrl(device, ctrl, self.group, self.update_ctrls))
            elif ctrl.type == V4L2_CTRL_TYPE_INTEGER_MENU:
                self.controls.append(
                    IntMenuCtrl(device, ctrl, self.group, self.update_ctrls))
            elif ctrl.type == V4L2_CTRL_TYPE_BITMASK:
                self.controls.append(
                    BitmaskCtrl(device, ctrl, self.group, self.update_ctrls))
            elif ctrl.type == V4L2_CTRL_TYPE_BUTTON:
                self.controls.append(
                    ButtonCtrl(device, ctrl, self.group, self.update_ctrls))
            elif ctrl.type == V4L2_CTRL_TYPE_INTEGER64:
                self.controls.append(
                    BigIntCtrl(device,
                               ctrl,
                               self.group,
                               self.update_ctrls,
                               is_64bit=True))
            elif ctrl.type == V4L2_CTRL_TYPE_STRING:
                self.controls.append(
                    StringCtrl(device, ctrl, self.group, self.update_ctrls))
            else:
                logging.debug(
                    f"Unsupported control type (Name: {ctrl.name}, Type: {ctrl.type})"
                )

    def update_ctrls(self):
        for ctrl in self.controls:
            ctrl.update_ctrl()

    def update_volatile_ctrls(self):
        for ctrl in self.controls:
            ctrl.update_if_volatile()


class Ctrl(ABC):

    def __init__(self, device, ctrl, parent, update_callback):
        self.device = device
        self.ctrl = ctrl
        self.parent = parent
        self.update_callback = update_callback
        self.ctrl_item = None

        with dpg.table(header_row=False,
                       parent=self.parent,
                       policy=dpg.mvTable_SizingStretchProp):
            dpg.add_table_column(init_width_or_weight=0.3)
            dpg.add_table_column(init_width_or_weight=0.5)
            dpg.add_table_column(init_width_or_weight=0.2)

            with dpg.table_row():
                self.name_text = dpg.add_text(default_value=self.ctrl.name)
                self.default_button = dpg.add_button(
                    label="Set to default", callback=self.set_to_default)

    def get_value(self):
        if self.ctrl_item is not None:
            value = self.device.get_control_value(self.ctrl)
            self.show_value(value)

    def set_value(self, value):
        if self.ctrl_item is not None:
            self.device.set_control_value(self.ctrl, value)
            self.update_callback()

    def update_ctrl(self):
        if self.ctrl_item is not None:
            self.ctrl = self.device.update_control(self.ctrl)
            dpg.configure_item(self.ctrl_item,
                               enabled=not self.ctrl.is_inactive)
            self.get_value()

    def update_if_volatile(self):
        if self.ctrl.is_volatile:
            self.update_ctrl()

    def set_to_default(self):
        if self.ctrl_item is not None:
            self.device.reset_control_to_default(self.ctrl)
            self.update_callback()
            self.get_value()

    @abstractmethod
    def on_change(self, sender, app_data, user_data):
        pass

    @abstractmethod
    def show_value(self, value):
        pass


class IntCtrl(Ctrl):

    def __init__(self, device, ctrl, parent, update_callback):
        super().__init__(device, ctrl, parent, update_callback)
        self.ctrl_item = dpg.add_slider_int(before=self.default_button,
                                            min_value=self.ctrl.minimum,
                                            max_value=self.ctrl.maximum,
                                            clamped=True,
                                            width=-1,
                                            callback=self.on_change,
                                            enabled=not self.ctrl.is_inactive)
        self.get_value()

    def on_change(self, sender, app_data, user_data):
        self.show_value(
            round((app_data - self.ctrl.minimum) / self.ctrl.step) *
            self.ctrl.step + self.ctrl.minimum)
        self.set_value(dpg.get_value(sender))

    def show_value(self, value):
        dpg.set_value(self.ctrl_item, value)


class BoolCtrl(Ctrl):

    def __init__(self, device, ctrl, parent, update_callback):
        super().__init__(device, ctrl, parent, update_callback)
        self.ctrl_item = dpg.add_checkbox(before=self.default_button,
                                          callback=self.on_change,
                                          enabled=not self.ctrl.is_inactive)
        self.get_value()

    def on_change(self, sender, app_data, user_data):
        self.set_value(dpg.get_value(sender))

    def show_value(self, value):
        dpg.set_value(self.ctrl_item, bool(value))


class Menu(Ctrl):

    def __init__(self, device, ctrl, parent, update_callback):
        super().__init__(device, ctrl, parent, update_callback)
        self.items = {}
        self.get_menu_items()

        self.ctrl_item = dpg.add_combo(before=self.default_button,
                                       width=-1,
                                       items=list(self.items.keys()),
                                       callback=self.on_change,
                                       enabled=not self.ctrl.is_inactive)
        self.get_value()

    def on_change(self, sender, app_data, user_data):
        if app_data in self.items.keys():
            self.set_value(self.items[app_data])

    def show_value(self, value):
        name = [k for k, v in self.items.items() if v == value]
        if len(name) != 0:
            dpg.set_value(self.ctrl_item, name[0])

    @abstractmethod
    def get_menu_items(self):
        pass


class MenuCtrl(Menu):

    def get_menu_items(self):
        for item in self.ctrl.items:
            self.items[item.name] = item


class IntMenuCtrl(Menu):

    def get_menu_items(self):
        for item in self.ctrl.items:
            self.items[item.value] = item


class ButtonCtrl(Ctrl):

    def __init__(self, device, ctrl, parent, update_callback):
        super().__init__(device, ctrl, parent, update_callback)
        self.ctrl_item = dpg.add_button(before=self.default_button,
                                        label="Click me",
                                        callback=self.on_change,
                                        enabled=not self.ctrl.is_inactive)

    def get_value(self):
        pass

    def on_change(self, sender, app_data, user_data):
        self.set_value(True)

    def show_value(self, value):
        pass


class StringCtrl(Ctrl):

    def __init__(self, device, ctrl, parent, update_callback):
        super().__init__(device, ctrl, parent, update_callback)
        self.ctrl_item = dpg.add_input_text(before=self.default_button,
                                            width=-1,
                                            on_enter=True,
                                            callback=self.on_change,
                                            enabled=not self.ctrl.is_inactive)
        self.get_value()

    def set_value(self, value):
        if self.ctrl_item is not None:
            if len(value) < self.ctrl.minimum:
                value = " " * self.ctrl.minimum

            self.device.set_control_value(self.ctrl, value)
            self.update_callback()

    def on_change(self, sender, app_data, user_data):
        self.set_value(dpg.get_value(sender))

    def show_value(self, value):
        dpg.set_value(self.ctrl_item, value)


class BitmaskCtrl(Ctrl):

    def __init__(self, device, ctrl, parent, update_callback):
        super().__init__(device, ctrl, parent, update_callback)
        self.ctrl_item = dpg.add_input_text(before=self.default_button,
                                            width=-1,
                                            hexadecimal=True,
                                            no_spaces=True,
                                            on_enter=True,
                                            callback=self.on_change,
                                            enabled=not self.ctrl.is_inactive)
        self.get_value()

    def on_change(self, sender, app_data, user_data):
        self.set_value(int(dpg.get_value(sender), 0))

    def show_value(self, value):
        dpg.set_value(self.ctrl_item, hex(value))


class BigIntCtrl(Ctrl):

    def __init__(self, device, ctrl, parent, update_callback, is_64bit=False):
        super().__init__(device, ctrl, parent, update_callback)
        self.is_64bit = is_64bit
        self.ctrl_item = dpg.add_slider_float(
            before=self.default_button,
            min_value=self.ctrl.minimum,
            max_value=self.ctrl.maximum,
            clamped=True,
            width=-1,
            format="%.0f",
            callback=self.on_change,
            user_data=self.ctrl.step,
            enabled=not self.ctrl.is_inactive)
        self.get_value()

    def on_change(self, sender, app_data, user_data):
        value = round((app_data - self.ctrl.minimum) /
                      self.ctrl.step) * self.ctrl.step + self.ctrl.minimum
        self.set_value(value)

    def show_value(self, value):
        dpg.set_value(self.ctrl_item, float(value))
