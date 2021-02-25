# SPDX-FileCopyrightText: 2018 Scott Shawcroft for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_imageload.bmp`
====================================================

Load pixel values (indices or colors) into a bitmap and colors into a palette from a BMP file.

* Author(s): Scott Shawcroft

"""
# pylint: disable=import-outside-toplevel

__version__ = "0.13.2"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_ImageLoad.git"


def load(file, *, bitmap=None, palette=None):
    """Loads a bmp image from the open ``file``.

    Returns tuple of bitmap object and palette object.

    :param object bitmap: Type to store bitmap data. Must have API similar to `displayio.Bitmap`.
      Will be skipped if None
    :param object palette: Type to store the palette. Must have API similar to
      `displayio.Palette`. Will be skipped if None"""
    file.seek(10)
    data_start = int.from_bytes(file.read(4), "little")
    # f.seek(14)
    # bmp_header_length = int.from_bytes(file.read(4), 'little')
    # print(bmp_header_length)
    file.seek(0x12)  # Width of the bitmap in pixels
    width = int.from_bytes(file.read(4), "little")
    try:
        height = int.from_bytes(file.read(4), "little")
    except OverflowError as error:
        raise NotImplementedError(
            "Negative height BMP files are not supported on builds without longint"
        ) from error
    file.seek(0x1C)  # Number of bits per pixel
    color_depth = int.from_bytes(file.read(2), "little")
    file.seek(0x1E)  # Compression type
    compression = int.from_bytes(file.read(2), "little")
    file.seek(0x2E)  # Number of colors in the color palette
    colors = int.from_bytes(file.read(4), "little")

    if colors == 0 and color_depth >= 16:
        raise NotImplementedError("True color BMP unsupported")

    if compression > 2:
        raise NotImplementedError("bitmask compression unsupported")

    if colors == 0:
        colors = 2 ** color_depth
    from . import indexed

    return indexed.load(
        file,
        width,
        height,
        data_start,
        colors,
        color_depth,
        compression,
        bitmap=bitmap,
        palette=palette,
    )
