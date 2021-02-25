# SPDX-FileCopyrightText: 2018 Scott Shawcroft for Adafruit Industries
# SPDX-FileCopyrightText: Matt Land
# SPDX-FileCopyrightText: Brooke Storm
# SPDX-FileCopyrightText: Sam McGahan
#
# SPDX-License-Identifier: MIT

"""
`adafruit_imageload.pnm.ppm_binary`
====================================================

Load pixel values (indices or colors) into a bitmap and for a binary ppm,
return None for pallet.

* Author(s):  Matt Land, Brooke Storm, Sam McGahan

"""

__version__ = "0.13.2"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_ImageLoad.git"


def load(file, width, height, bitmap=None, palette=None):
    """Load pixel values (indices or colors) into a bitmap and for a binary
    ppm, return None for pallet."""

    data_start = file.tell()
    palette_colors = set()
    line_size = width * 3

    for y in range(height):
        data_line = iter(bytes(file.read(line_size)))
        for red in data_line:
            # red, green, blue
            palette_colors.add((red, next(data_line), next(data_line)))

    if palette:
        palette = palette(len(palette_colors))
        for counter, color in enumerate(palette_colors):
            palette[counter] = bytes(color)
    if bitmap:
        bitmap = bitmap(width, height, len(palette_colors))
        file.seek(data_start)
        palette_colors = list(palette_colors)
        for y in range(height):
            x = 0
            data_line = iter(bytes(file.read(line_size)))
            for red in data_line:
                # red, green, blue
                bitmap[x, y] = palette_colors.index(
                    (red, next(data_line), next(data_line))
                )
                x += 1

    return bitmap, palette
