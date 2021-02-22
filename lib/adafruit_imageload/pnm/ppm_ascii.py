# SPDX-FileCopyrightText: 2018 Scott Shawcroft for Adafruit Industries
# SPDX-FileCopyrightText: Matt Land
# SPDX-FileCopyrightText: Brooke Storm
# SPDX-FileCopyrightText: Sam McGahan
#
# SPDX-License-Identifier: MIT

"""
`adafruit_imageload.pnm.ppm_ascii`
====================================================

Load pixel values (indices or colors) into a bitmap and for an ascii ppm,
return None for pallet.

* Author(s):  Matt Land, Brooke Storm, Sam McGahan

"""

__version__ = "0.13.2"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_ImageLoad.git"


def load(file, width, height, bitmap=None, palette=None):
    """
    :param stream file: infile with the position set at start of data
    :param int width:
    :param int height:
    :param int max_colors: color space of file
    :param bitmap: displayio.Bitmap class
    :param palette: displayio.Palette class
    :return tuple:
    """
    palette_colors = set()
    data_start = file.tell()
    for triplet in read_three_colors(file):
        palette_colors.add(triplet)

    if palette:
        palette = palette(len(palette_colors))
        for counter, color in enumerate(palette_colors):
            palette[counter] = color
    if bitmap:
        file.seek(data_start)
        bitmap = bitmap(width, height, len(palette_colors))
        palette_colors = list(palette_colors)
        for y in range(height):
            for x in range(width):
                for color in read_three_colors(file):
                    bitmap[x, y] = palette_colors.index(color)
                    break  # exit the inner generator
    return bitmap, palette


def read_three_colors(file):
    """
    Generator to read integer values from file, in groups of three.
    Each value can be len 1-3, for values 0 - 255, space padded.
    :return tuple[int]:
    """
    triplet = []
    color = bytearray()
    while True:
        this_byte = file.read(1)
        if this_byte.isdigit():
            color += this_byte
        # not a digit means we completed one number (found a space separator or EOF)
        elif color or (triplet and this_byte == b""):
            triplet.append(int("".join(["%c" % char for char in color])))
            color = bytearray()
        if len(triplet) == 3:  # completed one pixel
            yield bytes(tuple(triplet))
            triplet = []
        # short circuit must be after all other cases, so we yield the last pixel before returning
        if this_byte == b"":
            return
