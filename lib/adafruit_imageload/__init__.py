# SPDX-FileCopyrightText: 2018 Scott Shawcroft for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_imageload`
====================================================

Load pixel values (indices or colors) into a bitmap and colors into a palette.

* Author(s): Scott Shawcroft

"""
# pylint: disable=import-outside-toplevel

__version__ = "0.13.2"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_ImageLoad.git"


def load(filename, *, bitmap=None, palette=None):
    """Load pixel values (indices or colors) into a bitmap and colors into a palette.

    bitmap is the desired type. It must take width, height and color_depth in the constructor. It
    must also have a _load_row method to load a row's worth of pixel data.

    palette is the desired pallete type. The constructor should take the number of colors and
    support assignment to indices via [].
    """
    if not bitmap or not palette:
        try:
            # use displayio if available
            import displayio

            if not bitmap:
                bitmap = displayio.Bitmap
            if not palette:
                palette = displayio.Palette
        except ModuleNotFoundError:
            # meh, we tried
            pass

    with open(filename, "rb") as file:
        header = file.read(3)
        file.seek(0)
        if header.startswith(b"BM"):
            from . import bmp

            return bmp.load(file, bitmap=bitmap, palette=palette)
        if header.startswith(b"P"):
            from . import pnm

            return pnm.load(file, header, bitmap=bitmap, palette=palette)
        if header.startswith(b"GIF"):
            from . import gif

            return gif.load(file, bitmap=bitmap, palette=palette)
        raise RuntimeError("Unsupported image format")
