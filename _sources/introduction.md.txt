# What is Raviewer?

Raviewer is Antmicro's open-source image analysis tool, created to streamline the process of video debugging.
It handles arbitrary binary data and visualizes it using selected parameters so that you can quickly and efficiently analyze any image you want.

When your project involves operations like building a camera system, capturing the data with an FPGA board, or implementing camera drivers for new cameras or platforms, the sheer number of moving parts you are juggling before you get usable video makes debugging a difficult process.
This is where Raviewer may come in handy and help you accelerate and simplify your product development.

It helped us immensely with some of our projects, like when we built the FPGA debayering core, which included a demosaicing system that changes raw data from CCD or CMOS sensors.
Initially, the project was created for our internal needs, but we decided to release it to help reduce frustration related to working with complex engineering problems.

## Core features

Raviewer supports many popular color formats like [RGB, YUV, BAYER, or GRAYSCALE](formats.md) and lets you add new color formats.

- [Checkboxes controlling the displayed channels](controlling-color-channels)
- [On-click displaying raw data making up a pixel as decoded RGB and YUV](color-picker)
- [Conversion of the whole or selected part of an image to more complex formats (JPEG, PNG) or raw data](exporting-data)
- [An option to append or remove n bytes from the beginning of the image series](adding-skipping-bytes)
- [Hexadecimal preview mode](hexadecimal-preview-mode)
- [Terminal functionality](command-line-arguments)
- [Theme manager to adjust font and theme preferences](theme-manager)
