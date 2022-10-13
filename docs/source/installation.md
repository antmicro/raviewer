# Installation

## Requirements

For Raviewer to work, you need to have [Python 3.9](https://www.python.org/downloads/) or higher installed on your system.

You also need the following Python libraries:

* [numpy](https://numpy.org/doc/stable/)
* [opencv-python](https://docs.opencv.org/4.x/index.html)
* [Pillow](https://pillow.readthedocs.io/en/stable/)
* [dearpygui](https://dearpygui.readthedocs.io/en/latest/) == 1.1.1
* [terminaltables](https://robpol86.github.io/terminaltables/)
* [pytest](https://docs.pytest.org/en/7.1.x/)

```{note}
Raviewer will automatically download any missing libraries.
```

## Installation

### Arch Linux

```bash
sudo pacman -Sy python-pip git
pip install git+https://github.com/antmicro/raviewer.git
```

### Debian

```bash
sudo apt-get install python3-pip git python3-pil.imagetk
pip install git+https://github.com/antmicro/raviewer.git
```
