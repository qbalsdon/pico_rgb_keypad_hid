# The MIT License (MIT)
#
# Copyright (c) 2020 Kattni Rembor for Adafruit Industries
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""
`adafruit_led_animation.grid`
================================================================================

PixelGrid helper for 2D animations.

* Author(s): Kattni Rembor

Implementation Notes
--------------------

**Hardware:**

* `Adafruit NeoPixels <https://www.adafruit.com/category/168>`_
* `Adafruit DotStars <https://www.adafruit.com/category/885>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://circuitpython.org/downloads

"""
from micropython import const

from .helper import PixelMap, horizontal_strip_gridmap, vertical_strip_gridmap


HORIZONTAL = const(1)
VERTICAL = const(2)


class PixelGrid:
    """
    PixelGrid lets you address a pixel strip with x and y coordinates.

    :param strip: An object that implements the Neopixel or Dotstar protocol.
    :param width: Grid width.
    :param height: Grid height.
    :param orientation: Orientation of the strip pixels - HORIZONTAL (default) or VERTICAL.
    :param alternating: Whether the strip alternates direction from row to row (default True).
    :param reverse_x: Whether the strip X origin is on the right side (default False).
    :param reverse_y: Whether the strip Y origin is on the bottom (default False).
    :param tuple top: (x, y) coordinates of grid top left corner (Optional)
    :param tuple bottom: (x, y) coordinates of grid bottom right corner (Optional)

    To use with individual pixels:

    .. code-block:: python

        import board
        import neopixel
        import time
        from adafruit_led_animation.grid import PixelGrid, VERTICAL

        pixels = neopixel.NeoPixel(board.D11, 256, auto_write=False)

        grid = PixelGrid(pixels, 32, 8, orientation=VERTICAL, alternating=True)

        for x in range(32):
            for y in range(8):
                # pg[x, y] = (y*32) + x
                pg[x][y] = ((y*32) + x) << 8
        pg.show()

    """

    def __init__(
        self,
        strip,
        width,
        height,
        orientation=HORIZONTAL,
        alternating=True,
        reverse_x=False,
        reverse_y=False,
        top=0,
        bottom=0,
    ):  # pylint: disable=too-many-arguments,too-many-locals
        self._pixels = strip
        self._x = []
        self.height = height
        self.width = width

        if orientation == HORIZONTAL:
            mapper = horizontal_strip_gridmap(width, alternating)
        else:
            mapper = vertical_strip_gridmap(height, alternating)

        if reverse_x:
            mapper = reverse_x_mapper(width, mapper)

        if reverse_y:
            mapper = reverse_y_mapper(height, mapper)

        x_start = 0
        x_end = width
        y_start = 0
        y_end = height
        if top:
            x_start, y_start = top
        if bottom:
            x_end, y_end = bottom

        self.height = y_end - y_start
        self.width = x_end - x_start

        for x in range(x_start, x_end):
            self._x.append(
                PixelMap(
                    strip,
                    [mapper(x, y) for y in range(y_start, y_end)],
                    individual_pixels=True,
                )
            )
        self.n = len(self._x)

    def __repr__(self):
        return "[" + ", ".join([str(self[x]) for x in range(self.n)]) + "]"

    def __setitem__(self, index, val):
        if isinstance(index, slice):
            raise NotImplementedError("PixelGrid does not support slices")

        if isinstance(index, tuple):
            self._x[index[0]][index[1]] = val
        else:
            raise ValueError("PixelGrid assignment needs a sub-index or x,y coordinate")

        if self._pixels.auto_write:
            self.show()

    def __getitem__(self, index):
        if isinstance(index, slice):
            raise NotImplementedError("PixelGrid does not support slices")
        if index < 0:
            index += len(self)
        if index >= self.n or index < 0:
            raise IndexError("x is out of range")
        return self._x[index]

    def __len__(self):
        return self.n

    @property
    def brightness(self):
        """
        brightness from the underlying strip.
        """
        return self._pixels.brightness

    @brightness.setter
    def brightness(self, brightness):
        # pylint: disable=attribute-defined-outside-init
        self._pixels.brightness = min(max(brightness, 0.0), 1.0)

    def fill(self, color):
        """
        Fill the PixelGrid with the specified color.

        :param color: Color to use.
        """
        for strip in self._x:
            strip.fill(color)

    def show(self):
        """
        Shows the pixels on the underlying strip.
        """
        self._pixels.show()

    @property
    def auto_write(self):
        """
        auto_write from the underlying strip.
        """
        return self._pixels.auto_write

    @auto_write.setter
    def auto_write(self, value):
        self._pixels.auto_write = value


def reverse_x_mapper(width, mapper):
    """
    Returns a coordinate mapper function for grids with reversed X coordinates.

    :param width: width of strip
    :param mapper: grid mapper to wrap
    :return: mapper(x, y)
    """
    max_x = width - 1

    def x_mapper(x, y):
        return mapper(max_x - x, y)

    return x_mapper


def reverse_y_mapper(height, mapper):
    """
    Returns a coordinate mapper function for grids with reversed Y coordinates.

    :param height: width of strip
    :param mapper: grid mapper to wrap
    :return: mapper(x, y)
    """
    max_y = height - 1

    def y_mapper(x, y):
        return mapper(x, max_y - y)

    return y_mapper
