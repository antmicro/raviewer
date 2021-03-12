import tkinter as tk
import tkinter.font as tkFont
from tkinter.filedialog import askopenfilename, asksaveasfile

from .canvas import CanvasImage
from .image.color_format import AVAILABLE_FORMATS
from .core import determine_color_format, get_displayable
from PIL import Image


class MainWindow(tk.Frame):
    def __init__(self, args, master=tk.Tk()):
        tk.Frame.__init__(self, master)
        self.master = master
        self.master.geometry('1200x600')

        self.bg_color = "#C9C9C9"

        self.photoframe = tk.Frame(self.master)
        self.photoframe.rowconfigure(0, weight=1)
        self.photoframe.columnconfigure(0, weight=1)
        self.photoframe.pack(fill=tk.BOTH, side=tk.LEFT, expand=True)

        self.pack()
        self.init_width = args["width"]
        self.path_to_File = args["FILE_PATH"]
        self.init_color_format = args["color_format"]
        self.widget_font = tkFont.Font(family='Gill Sans MT',
                                       size=10,
                                       weight=tkFont.NORMAL)
        self.img_tk = None
        self.canvas = None
        self.ent_width = None
        if self.path_to_File != None:
            self.canvas = CanvasImage(self.photoframe, self.path_to_File,
                                      self.init_color_format, self.init_width)
            self.canvas.grid(row=0, column=0)
        self.create_widgets(args)

    def open_file(self):
        path = askopenfilename(filetypes=[("All Files", "*")])
        if path:
            self.path_to_File = path
            self.update_image()

    def file_save(self):
        if self.canvas.img != None:
            im = Image.fromarray(get_displayable(self.canvas.img))
            dialog = asksaveasfile(mode='wb',
                                   defaultextension=".png",
                                   filetypes=(("PNG file", "*.png"),
                                              ("All Files", "*.*")))
            if dialog is None:
                return
            im.save(dialog)

    def update_image(self):
        if self.path_to_File is None:
            self.warning_text.set("Path to file not specified")
        elif self.var_width.get() <= 0:
            self.warning_text.set("Width needs be greater than 0")
            self.display_text.set(self.path_to_File.rsplit('/', 1)[-1])
        else:
            self.display_text.set(self.path_to_File.rsplit('/', 1)[-1])
            if self.canvas is not None:
                self.canvas.destroy()

            self.warning_text.set("")
            self.canvas = CanvasImage(self.photoframe, self.path_to_File,
                                      self.v.get(), self.var_width.get())
            self.canvas.set_antialiasing(self.antialiasing.get())
            self.var_width.set(self.canvas.imwidth)
            self.var_height.set(self.canvas.imheight)
            self.canvas.grid()

    def update_width(self):
        if not self.canvas:
            self.update_image()
            return
        self.canvas.set_width(int(self.ent_width.get()))
        self.var_width.set(self.canvas.imwidth)
        self.var_height.set(self.canvas.imheight)

    def show_color_info_popup(self):
        pop = tk.Toplevel(self.master)
        pop.title("Color format description")
        pop.geometry("600x150")
        color_format = determine_color_format(self.v.get())
        custom_text= "Pixel format name:  " + color_format.name + "\nEndianness:  " \
                        + str(color_format.endianness)[11:] + "\n Pixel format:  " + str(color_format.pixel_format)[12:]+\
                        "\nPixel plane:  " + str(color_format.pixel_plane)[11:] + "\nBits per components:  " + str(color_format.bits_per_components)

        pop_label = tk.Label(master=pop,
                             text=custom_text,
                             font=self.widget_font)
        pop_label.pack(pady=20)
        pop_frame = tk.Frame(pop)
        pop_frame.pack(pady=5)

    def set_antialiasing(self):
        if self.canvas:
            self.canvas.set_antialiasing(self.antialiasing.get())

    def create_widgets(self, args):
        # Main window
        self.master.title('Raw image data previewer')
        self.master.configure(bg=self.bg_color)

        # Control buttons frame
        frm_control = tk.Frame(master=self.master, width=300, bg=self.bg_color)
        frm_control.pack(fill=tk.NONE, side=tk.RIGHT, expand=False)

        # Read from file label
        self.display_text = tk.StringVar()
        label_read = tk.Label(master=frm_control,
                              textvariable=self.display_text,
                              bg=self.bg_color,
                              font=self.widget_font)
        label_read.pack(fill=tk.BOTH, side=tk.TOP, expand=True)

        # Read from file button
        btn_read = tk.Button(master=frm_control,
                             width=20,
                             height=3,
                             text="Read data from file",
                             font=self.widget_font,
                             borderwidth=0,
                             command=self.open_file)
        btn_read.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Color format option button
        option_list = list(AVAILABLE_FORMATS.keys())
        self.v = tk.StringVar()

        for index in range(0, len(option_list)):
            if args["color_format"] == option_list[index]:
                self.v.set(option_list[index])

        self.v.trace("w", lambda x, y, z: self.update_image())
        opt_color_formats = tk.OptionMenu(frm_control, self.v, *option_list)
        opt_color_formats.config(width=18,
                                 height=2,
                                 font=self.widget_font,
                                 borderwidth=0)
        opt_color_formats.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Color description button
        btn_color_description = tk.Button(master=frm_control,
                                          width=20,
                                          height=3,
                                          text="Color format descripiton",
                                          font=self.widget_font,
                                          borderwidth=0,
                                          command=self.show_color_info_popup)
        btn_color_description.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Export image button
        btn_export_image = tk.Button(master=frm_control,
                                     width=20,
                                     height=3,
                                     text="Export image",
                                     font=self.widget_font,
                                     borderwidth=0,
                                     command=self.file_save)
        btn_export_image.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Resolution change entry
        frm_size = tk.Frame(master=frm_control,
                            width=20,
                            height=3,
                            bg=self.bg_color)

        frm_width = tk.Frame(master=frm_size, width=10)
        text_width = tk.Label(master=frm_width,
                              text="Width",
                              bg=self.bg_color,
                              font=self.widget_font)
        text_width.pack(fill=tk.BOTH, side=tk.TOP, expand=True)
        frm_width.pack(fill=tk.BOTH, side=tk.LEFT, expand=True, padx=2, pady=5)

        frm_height = tk.Frame(master=frm_size, width=10)
        text_height = tk.Label(master=frm_height,
                               text="Height\n(Read only)",
                               bg=self.bg_color,
                               font=self.widget_font)
        text_height.pack(fill=tk.BOTH, side=tk.TOP, expand=True)
        frm_height.pack(fill=tk.BOTH,
                        side=tk.LEFT,
                        expand=True,
                        padx=2,
                        pady=5)

        if self.path_to_File is None:
            self.var_width = tk.IntVar(value=800)
            self.var_height = tk.IntVar(value=0)
        else:
            self.var_width = tk.IntVar(value=self.canvas.imwidth)
            self.var_height = tk.IntVar(value=self.canvas.imheight)

        validator = frm_width.register(lambda x: x.isdigit() or not x)
        self.ent_width = tk.Spinbox(master=frm_width,
                                    width=10,
                                    font=self.widget_font,
                                    from_=1,
                                    to=1e6,
                                    validate=tk.ALL,
                                    validatecommand=(validator, '%P'),
                                    textvariable=self.var_width)
        self.ent_width.bind('<Return>', (lambda _: self.update_width()))

        self.ent_height = tk.Entry(master=frm_height,
                                   width=10,
                                   font=self.widget_font,
                                   background=self.bg_color,
                                   textvariable=self.var_height)
        self.ent_height.configure(state='readonly')

        self.ent_height.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        self.ent_width.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        frm_size.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Anti-aliasing checkbox
        self.antialiasing = tk.BooleanVar()
        chk_antialiasing = tk.Checkbutton(master=frm_control,
                                          width=20,
                                          height=3,
                                          text="Anti-aliasing",
                                          font=self.widget_font,
                                          borderwidth=0,
                                          variable=self.antialiasing,
                                          command=self.set_antialiasing)
        chk_antialiasing.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Warning label
        self.warning_text = tk.StringVar()
        label_warning = tk.Label(master=frm_control,
                                 textvariable=self.warning_text,
                                 fg="#FF0000",
                                 bg=self.bg_color,
                                 font=self.widget_font)
        label_warning.pack(fill=tk.BOTH, side=tk.TOP, expand=True)
