# SPDX-FileCopyrightText: 2019 Limor Fried for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`circle`
================================================================================

Various common shapes for use with displayio - Circle shape!


* Author(s): Limor Fried

Implementation Notes
--------------------

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""

from adafruit_display_shapes.roundrect import RoundRect

__version__ = "2.0.6"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_Display_Shapes.git"


class Circle(RoundRect):
    # pylint: disable=too-few-public-methods, invalid-name
    """A circle.

    :param x0: The x-position of the center.
    :param y0: The y-position of the center.
    :param r: The radius of the circle.
    :param fill: The color to fill the circle. Can be a hex value for a color or
                 ``None`` for transparent.
    :param outline: The outline of the circle. Can be a hex value for a color or
                 ``None`` for no outline.
    :param stroke: Used for the outline. Will not change the radius.

    """

    def __init__(self, x0, y0, r, *, fill=None, outline=None, stroke=1):
        super().__init__(
            x0 - r,
            y0 - r,
            2 * r + 1,
            2 * r + 1,
            r,
            fill=fill,
            outline=outline,
            stroke=stroke,
        )
