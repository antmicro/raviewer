import dearpygui.dearpygui as dpg


class Controls:
    """Class containing button assignments for default controls
    Keyword variables:
        pan_button: pan button
        query_button: button used to select a part of the image to export
        box_select_button: button used to select a part of image to zoom into
        add_annotation_button: button used to annotate the image
        remove_annotation_button: button used to remove add_annotation_button
        autosize_button: button that zooms the image to fit the plot size when double-clicked
        dummy: dummy assignment not associated with any button
    """
    pan_button = dpg.mvMouseButton_Middle
    query_button = dpg.mvMouseButton_Left
    box_select_button = dpg.mvMouseButton_Right
    remove_annotation_button = dpg.mvMouseButton_Right
    autosize_button = dpg.mvMouseButton_Right
    dummy = 5
