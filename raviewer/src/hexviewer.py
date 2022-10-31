"""Hexadecimal viewer displayed in tab."""

import dearpygui.dearpygui as dpg
import binascii
import threading

from .. import items


class Hexviewer:
    #mutex - prevents generating hexdump and updating image at the same time
    mutex = threading.Lock()
    #altered - tells whether the image was altered whilst generating hexdump
    altered = False

    def __init__(self, data_buffer, columns_width):
        """Constructs Hexviewer instance.
        Keyword arguments:
            data_buffer: binary data to display
            column_width: number of bytes in tab'column
        """
        self.data_buffer = data_buffer
        self.columns_width = columns_width
        self.file_chunk = None
        self.status = False
        self.encodings = ("ASCII", "UTF-8", "UTF-16", "UTF-32"
                          )  #TODO Support more encodings
        self.offset = 0

    def iterate_bytes(self, row):
        row_output = ""
        hex_array = []
        for byte in row:
            hex_byte = hex(byte).replace("x", "").upper()
            if byte >= 16:
                hex_byte = hex_byte.lstrip("0")
            hex_array.append(hex_byte)
            row_output += hex_byte
        return [row_output, hex_array]

    def form_offset(self, offset):
        return "{:#08x}".format(offset) + ": "

    def encode_row(self, hex_array):
        row_output = ""
        for x in hex_array:
            byte_object = bytes.fromhex(x)
            try:
                decoded_value = byte_object.decode("ASCII")
            except UnicodeDecodeError:
                decoded_value = "."
            if int(x, base=16) < 32:
                decoded_value = "."
            row_output += decoded_value

        return row_output

    def processed_content(self):
        Hexviewer.altered = False
        file_chunk = self.data_buffer[self.offset:self.offset + 64]
        Hexviewer.status = False
        while len(file_chunk) > 0:
            #Return while processing if we hided window or unchecked tab
            if not (dpg.is_item_shown(items.windows.hex_tab)
                    and dpg.get_value(items.menu_bar.hex)):
                return
            self.mutex.acquire()
            #Stop processing if the image was altered
            if (Hexviewer.altered):
                self.mutex.release()
                return
            with dpg.table_row(parent=items.windows.hex_mode):
                dpg.add_text(self.form_offset(self.offset),
                             color=[203, 62, 62, 255])
                hex_output, hex_array = self.iterate_bytes(file_chunk)
                hex_output = " ".join(hex_output[i:i + 8]
                                      for i in range(0, len(hex_output), 8))
                dpg.add_text(hex_output, bullet=False)
                dpg.add_text(self.encode_row(hex_array))
            self.mutex.release()
            self.offset += 64
            """
            If frame size isn't a multiple of 64 last read bytes would extend over next frame if we read 64 bytes every loop repetition
            If offset gets bigger than n_bytes, the program reads 0 bytes which breaks the loop
            """
            file_chunk = self.data_buffer[self.offset:self.offset + 64]
        Hexviewer.status = True
