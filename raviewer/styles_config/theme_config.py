"""File for static theme setup"""
import dearpygui.dearpygui as dpg
from ..items_ids import *

with dpg.theme() as items["theme"]["global"]:
    with dpg.theme_component(dpg.mvAll):
        pass
        #####Mock formula for binding color and rounding style to the buttons
        #
        #dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (255, 140, 23), category=dpg.mvThemeCat_Core)
        #dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5, category=dpg.mvThemeCat_Core)
        #
        ####
