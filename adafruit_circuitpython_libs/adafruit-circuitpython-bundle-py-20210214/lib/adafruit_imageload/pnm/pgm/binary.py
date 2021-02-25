# SPDX-FileCopyrightText: 2018 Scott Shawcroft for Adafruit Industries
# SPDX-FileCopyrightText: Matt Land
# SPDX-FileCopyrightText: Brooke Storm
# SPDX-FileCopyrightText: Sam McGahan
#
# SPDX-License-Identifier: MIT

"""
`adafruit_imageload.pnm.pgm.binary`
====================================================

Load pixel values (indices or colors) into a bitmap and colors into a palette.

* Author(s): Matt Land, Brooke Storm, Sam McGahan

"""


def load(file, width, height, bitmap=None, palette=None):
    """
    Load a P5 format file (binary), handle PGM (greyscale)
    """
    palette_colors = set()
    data_start = file.tell()
    for y in range(height):
        data_line = iter(bytes(file.read(width)))
        for pixel in data_line:
            palette_colors.add(pixel)

    if palette:
        palette = build_palette(palette, palette_colors)
    if bitmap:
        bitmap = bitmap(width, height, len(palette_colors))
        palette_colors = list(palette_colors)
        file.seek(data_start)
        for y in range(height):
            data_line = iter(bytes(file.read(width)))
            for x, pixel in enumerate(data_line):
                bitmap[x, y] = palette_colors.index(pixel)
    return bitmap, palette


def build_palette(palette_class, palette_colors):
    """
    construct the Palette, and populate it with the set of palette_colors
    """
    palette = palette_class(len(palette_colors))
    for counter, color in enumerate(palette_colors):
        palette[counter] = bytes([color, color, color])
    return palette
