# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

# Call this with the font file as the command line argument.

import os
import sys

# Add paths so this runs in CPython in-place.
sys.path.append(os.path.join(sys.path[0], ".."))
from adafruit_bitmap_font import bitmap_font  # pylint: disable=wrong-import-position

sys.path.append(os.path.join(sys.path[0], "../test"))
font = bitmap_font.load_font(sys.argv[1])
specimen = "Adafruit CircuitPython" if len(sys.argv) == 2 else sys.argv[2]

_, height, _, dy = font.get_bounding_box()
font.load_glyphs(specimen)

for y in range(height):
    for c in specimen:
        glyph = font.get_glyph(ord(c))
        if not glyph:
            continue
        glyph_y = y + (glyph.height - (height + dy)) + glyph.dy
        pixels = []
        if 0 <= glyph_y < glyph.height:
            for i in range(glyph.width):
                value = glyph.bitmap[i, glyph_y]
                pixel = " "
                if value > 0:
                    pixel = "#"
                pixels.append(pixel)
        else:
            pixels = ""
        print("".join(pixels) + " " * (glyph.shift_x - len(pixels)), end="")
    print()
