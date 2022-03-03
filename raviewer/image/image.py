"""Support for containing image."""

import numpy


class Image:
    """Container for image data."""

    def __init__(self,
                 data_buffer,
                 color_format=None,
                 processed_data=None,
                 width=None,
                 height=None):
        """Constructs Image instance.

        Keyword arguments:

            data_buffer: bytes object
            color_format: instance of ColorFormat
            processed_data: numpy array
            width: image width
            height: image height
        """
        self.data_buffer = data_buffer
        self.color_format = color_format
        self.processed_data = processed_data
        self.width = width
        self.height = height
        self.orig_size = None

    def reshape(self, new_width):
        if self.orig_size is None:
            self.orig_size = self.width * self.height
            self.pixel_size = self.processed_data.size / self.orig_size
            self.orig_processed_data = self.processed_data
        new_height = self.orig_size // new_width
        self.processed_data = self.orig_processed_data[:round(new_width *
                                                              new_height *
                                                              self.pixel_size)]
        self.height = new_height
        self.width = new_width
