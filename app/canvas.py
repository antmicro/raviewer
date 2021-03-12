import math
import tkinter as tk
from .core import (load_image, get_displayable)
from tkinter import ttk
from PIL import Image, ImageTk


class AutoScrollbar(ttk.Scrollbar):
    """ Scrollbar that's only visible when necessary. Only for grid layouts. """
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            self.grid_remove()
        else:
            self.grid()
            ttk.Scrollbar.set(self, lo, hi)

    def pack(self, **kw):
        raise tk.TclError('Cannot use pack with the widget ' +
                          self.__class__.__name__)

    def place(self, **kw):
        raise tk.TclError('Cannot use place with the widget ' +
                          self.__class__.__name__)


class CanvasImage:
    """ Canvas that displays an image, allowing zooming and dragging. """
    def __init__(self, placeholder, path, color_format, width):
        # How much the zoom changes based on scrolling etc.
        self.__zoom_delta = 1.3
        self.__filter = Image.ANTIALIAS
        # Previous keyboard press state.
        self.__keyboard_state = 0
        # Load the image.
        self.img = load_image(path, color_format, width)
        # Create ImageFrame in placeholder widget
        self.__imframe = ttk.Frame(placeholder)
        # Vertical and horizontal scrollbars for canvas
        hbar = AutoScrollbar(self.__imframe, orient='horizontal')
        vbar = AutoScrollbar(self.__imframe, orient='vertical')
        hbar.grid(row=1, column=0, sticky='we')
        vbar.grid(row=0, column=1, sticky='ns')
        # Create canvas and bind it with scrollbars. Public for outer classes
        self.canvas = tk.Canvas(self.__imframe,
                                highlightthickness=0,
                                xscrollcommand=hbar.set,
                                yscrollcommand=vbar.set,
                                width=800,
                                height=600)
        self.canvas.grid(row=0, column=0, sticky='nswe')
        # Create the canvas.
        self.canvas.update()
        # Bind scroll functions.
        hbar.configure(command=self.__scroll_x)
        vbar.configure(command=self.__scroll_y)

        # Bind events to the Canvas.
        # Resize canvas.
        self.canvas.bind('<Configure>', lambda event: self.__show_image())
        # Remember position of the canvas.
        self.canvas.bind('<ButtonPress-1>', self.__move_from)
        # Move the canvas to a new position.
        self.canvas.bind('<B1-Motion>', self.__move_to)
        # Zoom for Linux, scroll down.
        self.canvas.bind('<Button-5>', self.__wheel)
        # Zoom for Linux, scroll up.
        self.canvas.bind('<Button-4>', self.__wheel)
        # Handle keystrokes in idle mode, because program slows down on a weak computers,
        # when too many key stroke events in the same time
        self.canvas.bind(
            '<Key>',
            lambda event: self.canvas.after_idle(self.__keystroke, event))
        # Check if the image is very big.
        self.__huge = False
        # Huge size is defined at 14000.
        self.__huge_size = 14000
        # Max bandwith is set at 1024.
        self.__band_width = 1024
        self.reset_width()
        self.canvas.focus_set()

    def set_width(self, width):
        self.img.reshape(width)
        self.reset_width()

    def reset_width(self):
        # How zoomed in the image is at the begginnig.
        self.imscale = 1.0
        # Open our image.
        self.__image = Image.fromarray(get_displayable(self.img))
        # Image width and height, public for outer classes.
        self.imwidth, self.imheight = self.__image.size

        # If the image is over 14000 by 14000 and is raw then tile it.
        if self.imwidth * self.imheight > self.__huge_size * self.__huge_size and \
           self.__image.tile[0][0] == 'raw':
            # Set the image as huge.
            self.__huge = True
            # Initial tile offset.
            self.__offset = self.__image.tile[0][2]
            self.__tile = [
                self.__image.tile[0][0],  # 'raw'
                [0, 0, self.imwidth, 0],  # tile extent (a rectangle)
                self.__offset,
                self.__image.tile[0][3]
            ]  # list of arguments to the decoder
        # Get the smallest side of image.
        self.__min_side = min(self.imwidth, self.imheight)
        # Create image pyramid.
        self.__pyramid = [self.smaller()] if self.__huge else [self.__image]
        # Set ratio coefficient for image pyramid
        self.__ratio = max(self.imwidth, self.imheight
                           ) / self.__huge_size if self.__huge else 1.0
        self.__curr_img = 0
        # Pyramid image scale.
        self.__scale = self.imscale * self.__ratio
        # How much the image in the pyramid is reduced.
        self.__reduction = 2
        w, h = self.__pyramid[-1].size
        # The top pyramid image is about 512x512. Reduce it using the filter.
        while w > 512 and h > 512:
            w /= self.__reduction
            h /= self.__reduction
            self.__pyramid.append(self.__pyramid[-1].resize((int(w), int(h)),
                                                            self.__filter))
        self.container = self.canvas.create_rectangle(
            (0, 0, self.imwidth, self.imheight), width=0)
        self.__show_image()

    def set_antialiasing(self, antialiasing):
        if antialiasing:
            self.__filter = Image.ANTIALIAS
        else:
            self.__filter = Image.NEAREST
        self.__show_image()

    def smaller(self):
        """ For huge images, resize image and return a smaller version. """
        # Convert height and width into floats.
        width1, height1 = float(self.imwidth), float(self.imheight)
        width2, height2 = float(self.__huge_size), float(self.__huge_size)
        aspect_ratio1 = width1 / height1
        aspect_ratio2 = width2 / height2
        if aspect_ratio1 == aspect_ratio2:
            image = Image.new('RGB', (int(width2), int(height2)))
            k = height2 / height1
            w = int(width2)
        elif aspect_ratio1 > aspect_ratio2:
            image = Image.new('RGB',
                              (int(width2), int(width2 / aspect_ratio1)))
            k = height2 / width1
            w = int(width2)
        else:
            image = Image.new('RGB',
                              (int(height2 * aspect_ratio1), int(height2)))
            k = height2 / height1
            w = int(height2 * aspect_ratio1)
        i, j, n = 0, 1, round(0.5 + self.imheight / self.__band_width)
        while i < self.imheight:
            band = min(self.__band_width,
                       self.imheight - i)  # width of the tile band
            self.__tile[1][3] = band  # set band width
            self.__tile[
                2] = self.__offset + self.imwidth * i * 3  # tile offset (3 bytes per pixel)
            self.__image.close()
            self.__image = Image.fromarray(get_displayable(
                self.img))  # reopen / reset image
            self.__image.size = (self.imwidth, band
                                 )  # set size of the tile band
            self.__image.tile = [self.__tile]  # set tile
            cropped = self.__image.crop(
                (0, 0, self.imwidth, band))  # crop tile band
            image.paste(cropped.resize((w, int(band * k) + 1), self.__filter),
                        (0, int(i * k)))
            i += band
            j += 1
        return image

    def grid(self, **kw):
        """ Put CanvasImage widget on the parent widget """
        self.__imframe.grid(**kw)  # place CanvasImage widget on the grid
        self.__imframe.grid(sticky='nswe')  # make frame container sticky
        self.__imframe.rowconfigure(0, weight=1)  # make canvas expandable
        self.__imframe.columnconfigure(0, weight=1)

    def pack(self, **kw):
        """ Exception: cannot use pack with this widget """
        raise Exception('Cannot use pack with the widget ' +
                        self.__class__.__name__)

    def place(self, **kw):
        """ Exception: cannot use place with this widget """
        raise Exception('Cannot use place with the widget ' +
                        self.__class__.__name__)

    # noinspection PyUnusedLocal
    def __scroll_x(self, *args, **kwargs):
        """ Scroll canvas horizontally and redraw the image """
        self.canvas.xview(*args)  # scroll horizontally
        self.__show_image()  # redraw the image

    # noinspection PyUnusedLocal
    def __scroll_y(self, *args, **kwargs):
        """ Scroll canvas vertically and redraw the image """
        self.canvas.yview(*args)  # scroll vertically
        self.__show_image()  # redraw the image

    def __show_image(self):
        """ Display image on canvas """
        box_image = self.canvas.coords(self.container)  # get image area
        box_canvas = (self.canvas.canvasx(0), self.canvas.canvasy(0),
                      self.canvas.canvasx(self.canvas.winfo_width()),
                      self.canvas.canvasy(self.canvas.winfo_height()))
        box_img_int = tuple(map(int, box_image))
        box_scroll = [
            min(box_img_int[0], box_canvas[0]),
            min(box_img_int[1], box_canvas[1]),
            max(box_img_int[2], box_canvas[2]),
            max(box_img_int[3], box_canvas[3])
        ]
        # Horizontal part of the image is in the visible area
        if box_scroll[0] == box_canvas[0] and box_scroll[2] == box_canvas[2]:
            box_scroll[0] = box_img_int[0]
            box_scroll[2] = box_img_int[2]
        # Vertical part of the image is in the visible area
        if box_scroll[1] == box_canvas[1] and box_scroll[3] == box_canvas[3]:
            box_scroll[1] = box_img_int[1]
            box_scroll[3] = box_img_int[3]
        # Convert scroll region to tuple and to integer
        self.canvas.configure(scrollregion=tuple(map(int, box_scroll)))
        x1 = max(box_canvas[0] - box_image[0], 0)
        y1 = max(box_canvas[1] - box_image[1], 0)
        x2 = min(box_canvas[2], box_image[2]) - box_image[0]
        y2 = min(box_canvas[3], box_image[3]) - box_image[1]
        if int(x2 - x1) > 0 and int(y2 - y1) > 0:
            if self.__huge and self.__curr_img < 0:
                h = int((y2 - y1) / self.imscale)
                self.__tile[1][3] = h
                self.__tile[2] = self.__offset + self.imwidth * int(
                    y1 / self.imscale) * 3
                self.__image.close()
                self.__image = Image.fromarray(get_displayable(self.img))
                self.__image.size = (self.imwidth, h)
                self.__image.tile = [self.__tile]
                image = self.__image.crop(
                    (int(x1 / self.imscale), 0, int(x2 / self.imscale), h))
            else:  # show normal image
                image = self.__pyramid[max(0, self.__curr_img)].crop(
                    (int(x1 / self.__scale), int(y1 / self.__scale),
                     int(x2 / self.__scale), int(y2 / self.__scale)))
            if image.mode == "RGBA":
                mask = Image.new("RGB", image.size, (255, 255, 255))
                image = Image.composite(image, mask, image)
            imagetk = ImageTk.PhotoImage(
                image.resize((int(x2 - x1), int(y2 - y1)), self.__filter))
            imageid = self.canvas.create_image(max(box_canvas[0],
                                                   box_img_int[0]),
                                               max(box_canvas[1],
                                                   box_img_int[1]),
                                               anchor='nw',
                                               image=imagetk)
            self.canvas.lower(imageid)
            self.canvas.imagetk = imagetk

    def __move_from(self, event):
        """ Remember previous coordinates for scrolling with the mouse """
        self.canvas.scan_mark(event.x, event.y)

    def __move_to(self, event):
        """ Drag (move) canvas to the new position """
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        self.__show_image()  # zoom tile and show it on the canvas

    def outside(self, x, y):
        """ Checks if the point (x,y) is outside the image area """
        bbox = self.canvas.coords(self.container)  # get image area
        if bbox[0] < x < bbox[2] and bbox[1] < y < bbox[3]:
            return False  # point (x,y) is inside the image area
        else:
            return True  # point (x,y) is outside the image area

    def __wheel(self, event):
        """ Zoom with mouse wheel """
        x = self.canvas.canvasx(
            event.x)  # get coordinates of the event on the canvas
        y = self.canvas.canvasy(event.y)
        if self.outside(x, y): return  # zoom only inside image area
        scale = 1.0
        if event.num == 5 or event.delta == -120:  # scroll down, smaller
            if round(self.__min_side * self.imscale) < 30:
                return  # image is less than 30 pixels
            self.imscale /= self.__zoom_delta
            scale /= self.__zoom_delta
        if event.num == 4 or event.delta == 120:
            i = min(self.canvas.winfo_width(), self.canvas.winfo_height()) >> 1
            if i < self.imscale:
                return  # 1 pixel is bigger than the visible area
            self.imscale *= self.__zoom_delta
            scale *= self.__zoom_delta
        k = self.imscale * self.__ratio
        self.__curr_img = min((-1) * int(math.log(k, self.__reduction)),
                              len(self.__pyramid) - 1)
        self.__scale = k * math.pow(self.__reduction, max(0, self.__curr_img))
        #
        self.canvas.scale('all', x, y, scale, scale)
        self.__show_image()

    def __keystroke(self, event):
        """ Scrolling with the keyboard.
            Independent from the language of the keyboard, CapsLock, <Ctrl>+<key>, etc. """
        if event.state - self.__keyboard_state == 4:  # means that the Control key is pressed
            pass  # do nothing if Control key is pressed
        else:
            self.__keyboard_state = event.state  # remember the last keystroke state
            # Up, Down, Left, Right keystrokes
            # scroll right: keys 'D', 'Right' or 'Numpad-6'
            if event.keycode in [68, 39, 102]:
                self.__scroll_x('scroll', 1, 'unit', event=event)
            # scroll left: keys 'A', 'Left' or 'Numpad-4'
            elif event.keycode in [65, 37, 100]:
                self.__scroll_x('scroll', -1, 'unit', event=event)
            # scroll up: keys 'W', 'Up' or 'Numpad-8'
            elif event.keycode in [87, 38, 104]:
                self.__scroll_y('scroll', -1, 'unit', event=event)
            # scroll down: keys 'S', 'Down' or 'Numpad-2'
            elif event.keycode in [83, 40, 98]:
                self.__scroll_y('scroll', 1, 'unit', event=event)

    def crop(self, bbox):
        """ Crop rectangle from the image and return it """
        if self.__huge:  # image is huge and not totally in RAM
            band = bbox[3] - bbox[1]  # width of the tile band
            self.__tile[1][3] = band  # set the tile height
            self.__tile[2] = self.__offset + self.imwidth * bbox[
                1] * 3  # set offset of the band
            self.__image.close()
            self.__image = Image.fromarray(get_displayable(
                self.img))  # reopen / reset image
            self.__image.size = (self.imwidth, band
                                 )  # set size of the tile band
            self.__image.tile = [self.__tile]
            return self.__image.crop((bbox[0], 0, bbox[2], band))
        else:  # image is totally in RAM
            return self.__pyramid[0].crop(bbox)

    def destroy(self):
        """ ImageFrame destructor """
        self.__image.close()
        map(lambda i: i.close, self.__pyramid)
        del self.__pyramid[:]
        del self.__pyramid
        self.canvas.destroy()
        self.__imframe.destroy()
