# Raw image data previewer

Raw image data previewer is an open-source utility dedicated to parsing and displaying binary data acquired straight from a camera.

![Main window](docs/img/ridp-1.png)

This simple utility provides features like:

* previewing most used raw color formats
    * RGB-like formats
    * YUVs (packed, semiplanar, planar)
    * Grayscales
    * Bayer RGBs
* exporting raw image data to more complex formats (ie. PNG, JPG)

# Installation

## Requirements

* Python >=v3.9
* numpy
* opencv
* PIL

## Installation

### Manjaro Linux

```bash
sudo pacman -Sy python-pip git
git clone https://github.com/antmicro-labs/raw-image-data-previewer.git
cd raw-image-data-previewer
pip install -r requirements.txt
```

### Ubuntu 20.04

```bash
sudo apt-get install python3-pip git python3-pil.imagetk
git clone https://github.com/antmicro-labs/raw-image-data-previewer.git
cd raw-image-data-previewer
python3 -m pip install -r requirements.txt
```

# Usage

To start an empty GUI (without any data loaded) use:

```bash
cd raw-image-data-previewer
python3 -m app
```

You can also start the GUI with already loaded data and parameters (like width and color format). More information about available arguments can be found in command-line help:

```bash
cd raw-image-data-previewer
python3 -m app --help
```

## Exporting images

The utility also provides a way to convert binary files containing image data to more complex formats (ie. PNG, JPG) without starting the grahpical interface.
To use this option simply add the `--export` argument with the target filename with extension.

## Supported formats information

Currently supported color formats and planned ones can be found [in the documentation](docs/SUPPORTED_FORMATS.md).

# Extending supported color formats

## Adding new color formats

Currently there are two classes that can describe color formats: `ColorFormat` and `SubsampledColorFormat` (found in `app/image/color_format.py`).
To create a new color format, simply:

1. Under `AVAILABLE_FORMATS` list in `color_format.py` add new instance of one of the color format classes with proper fields filled.
2. Provide parsing and displaying function by extending `AbstractParser` found in `common.py` or by using an existing one.
    * If you choose to implement a new one remember that `parse()` should return one dimensional `ndarray` with values read from the binary file. `display()` on the other hand should return RGB-formatted 3-dimensional `ndarray` consisting of original color format values converted to RGB24.
3. The utility provides proper parser by checking color format parameters (mainly `PixelFormat`), so make sure, that your new color format has a valid translation of parameters to one of the parsers (this functionality can be found in `app/parser/factory.py`).

## Contributors

* Błażej Ułanowicz ([blazejulanowicz](https://github.com/blazejulanowicz))
* Dawid Dopart ([DopartDawid](https://github.com/DopartDawid))
* Maciej Tylak ([Ty7ak](https://github.com/Ty7ak))
* Maciej Franikowski ([MaciejFranikowski](https://github.com/MaciejFranikowski))

# License

The utility is licensed under the Apache-2 license. For details, please read [the LICENSE file](LICENSE).
