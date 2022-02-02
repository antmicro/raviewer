"""Hexadecimal viewer displayed in tab."""

import dearpygui.dearpygui as dpg
import binascii
import threading

from ..items_ids import *


class Hexviewer:
    #mutex - prevents generating hexdump and updating image at the same time
    mutex = threading.Lock()
    #altered - tells whether the image was altered whilst generating hexdump
    altered = False

    def __init__(self, filename, columns_width, frame=1, n_frames=1):
        """Constructs Hexviewer instance.
        Keyword arguments:
            filename: file location
            column_width: number of bytes in tab'column
        """
        self.filename = filename
        self.columns_width = columns_width
        self.file_chunk = None
        self.status = False
        self.encodings = ("ASCII", "UTF-8", "UTF-16", "UTF-32"
                          )  #TODO Support more encodings
        self.offset = 0
        self.frame = frame
        self.n_frames = n_frames

    def open_file(self):
        try:
            self.file_content = open(self.filename, "rb")
            self.file_content.seek(0, 2)
            self.n_bytes = self.file_content.tell() // self.n_frames
            self.file_content.seek(((self.frame - 1) * self.n_bytes), 0)
        except FileNotFoundError:
            print("File {filename} not found.")

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
        file_chunk = self.file_content.read(64)
        while len(file_chunk) > 0:
            #Return while processing if we hided window or unchecked tab
            if not (dpg.is_item_shown(items["windows"]["hex_tab"])
                    and dpg.get_value(items["menu_bar"]["hex"])):
                return
            self.mutex.acquire()
            #Stop processing if the image was altered
            if (Hexviewer.altered):
                self.mutex.release()
                return
            with dpg.table_row(parent=items["windows"]["hex_mode"]):
                dpg.add_text(self.form_offset(self.offset),
                             color=[203, 62, 62, 255])
                hex_output, hex_array = self.iterate_bytes(file_chunk)
                hex_output = " ".join(hex_output[i:i + 8]
                                      for i in range(0, len(hex_output), 8))
                dpg.add_text(hex_output, bullet=False)
                dpg.add_text(self.encode_row(hex_array))
            self.offset += 64
            """
            If frame size isn't a multiple of 64 last read bytes would extend over next frame if we read 64 bytes every loop repetition
            If offset gets bigger than n_bytes, the program reads 0 bytes which breaks the loop
            """
            file_chunk = self.file_content.read(
                min(
                    64, 0 if self.offset > self.n_bytes else self.n_bytes -
                    self.offset))
            self.mutex.release()
        self.status = True
