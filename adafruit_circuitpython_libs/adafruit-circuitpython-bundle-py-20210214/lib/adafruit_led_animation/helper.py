# The MIT License (MIT)
#
# Copyright (c) 2019
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
`adafruit_led_animation.helper`
================================================================================

Helper classes for making complex animations using CircuitPython LED animations library.

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

import math

from . import MS_PER_SECOND, monotonic_ms
from .color import calculate_intensity


class PixelMap:
    """
    PixelMap lets you treat ranges of pixels as single pixels for animation purposes.

    :param strip: An object that implements the Neopixel or Dotstar protocol.
    :param iterable pixel_ranges: Pixel ranges (or individual pixels).
    :param bool individual_pixels: Whether pixel_ranges are individual pixels.

    To use with ranges of pixels:

    .. code-block:: python

        import board
        import neopixel
        from adafruit_led_animation.helper import PixelMap
        pixels = neopixel.NeoPixel(board.D6, 32, auto_write=False)

        pixel_wing_horizontal = PixelMap(pixels, [(0, 8), (8, 16), (16, 24), (24, 32)])

        pixel_wing_horizontal[0] = (255, 255, 0)
        pixel_wing_horizontal.show()

    To use with groups of individual pixels:

    .. code-block:: python

        import board
        import neopixel
        from adafruit_led_animation.helper import PixelMap
        pixels = neopixel.NeoPixel(board.D6, 32, auto_write=False)

        pixel_wing_vertical = PixelMap(pixels, [
            (0, 8, 16, 24),
            (1, 9, 17, 25),
            (2, 10, 18, 26),
            (3, 11, 19, 27),
            (4, 12, 20, 28),
            (5, 13, 21, 29),
            (6, 14, 22, 30),
            (7, 15, 23, 31),
        ], individual_pixels=True)

        pixel_wing_vertical[0] = (255, 255, 0)
        pixel_wing_vertical.show()

    To use with individual pixels:

    .. code-block:: python

        import board
        import neopixel
        import time
        from adafruit_led_animation.helper import PixelMap

        pixels = neopixel.NeoPixel(board.D6, 8, auto_write=False)

        pixel_map = PixelMap(pixels, [
            0, 7, 1, 6, 2, 5, 3, 4
        ], individual_pixels=True)

        n = 0
        while True:
            pixel_map[n] = AMBER
            pixel_map.show()
            n = n + 1
            if n > 7:
                n = 0
                pixel_map.fill(0)
            time.sleep(0.25)


    """

    def __init__(self, strip, pixel_ranges, individual_pixels=False):
        self._pixels = strip
        self._ranges = pixel_ranges

        self.n = len(self._ranges)
        if self.n == 0:
            raise ValueError("A PixelMap must have at least one pixel defined")
        self._individual_pixels = individual_pixels
        self._expand_ranges()

    def _expand_ranges(self):
        if not self._individual_pixels:
            self._ranges = [list(range(start, end)) for start, end in self._ranges]
            return
        if isinstance(self._ranges[0], int):
            self._ranges = [[n] for n in self._ranges]

    def __repr__(self):
        return "[" + ", ".join([str(self[x]) for x in range(self.n)]) + "]"

    def _set_pixels(self, index, val):
        for pixel in self._ranges[index]:
            self._pixels[pixel] = val

    def __setitem__(self, index, val):
        if isinstance(index, slice):
            start, stop, step = index.indices(len(self._ranges))
            length = stop - start
            if step != 0:
                length = math.ceil(length / step)
            if len(val) != length:
                raise ValueError("Slice and input sequence size do not match.")
            for val_i, in_i in enumerate(range(start, stop, step)):
                self._set_pixels(in_i, val[val_i])
        else:
            self._set_pixels(index, val)

        if self._pixels.auto_write:
            self.show()

    def __getitem__(self, index):
        if isinstance(index, slice):
            out = []
            for in_i in range(*index.indices(len(self._ranges))):
                out.append(self._pixels[self._ranges[in_i][0]])
            return out
        if index < 0:
            index += len(self)
        if index >= self.n or index < 0:
            raise IndexError
        return self._pixels[self._ranges[index][0]]

    def __len__(self):
        return len(self._ranges)

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
        Fill the used pixel ranges with color.

        :param color: Color to fill all pixels referenced by this PixelMap definition with.
        """
        for pixels in self._ranges:
            for pixel in pixels:
                self._pixels[pixel] = color

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

    @classmethod
    def vertical_lines(cls, pixel_object, width, height, gridmap):
        """
        Generate a PixelMap of horizontal lines on a strip arranged in a grid.

        :param pixel_object: pixel object
        :param width: width of grid
        :param height: height of grid
        :param gridmap: a function to map x and y coordinates to the grid
                           see vertical_strip_gridmap and horizontal_strip_gridmap
        :return: PixelMap

        Example: Vertical lines on a 32x8 grid with the pixel rows oriented vertically,
                 alternating direction every row.

        .. code-block:: python

            PixelMap.vertical_lines(pixels, 32, 8, vertical_strip_gridmap(8))

        """
        if len(pixel_object) < width * height:
            raise ValueError("number of pixels is less than width x height")
        mapping = []
        for x in range(width):
            mapping.append([gridmap(x, y) for y in range(height)])
        return cls(pixel_object, mapping, individual_pixels=True)

    @classmethod
    def horizontal_lines(cls, pixel_object, width, height, gridmap):
        """
        Generate a PixelMap of horizontal lines on a strip arranged in a grid.

        :param pixel_object: pixel object
        :param width: width of grid
        :param height: height of grid
        :param gridmap: a function to map x and y coordinates to the grid
                           see vertical_strip_gridmap and horizontal_strip_gridmap
        :return: PixelMap

        Example: Horizontal lines on a 16x16 grid with the pixel rows oriented vertically,
                 alternating direction every row.

        .. code-block:: python

            PixelMap.horizontal_lines(pixels, 16, 16, vertical_strip_gridmap(16))
        """
        if len(pixel_object) < width * height:
            raise ValueError("number of pixels is less than width x height")
        mapping = []
        for y in range(height):
            mapping.append([gridmap(x, y) for x in range(width)])
        return cls(pixel_object, mapping, individual_pixels=True)


def vertical_strip_gridmap(height, alternating=True):
    """
    Returns a function that determines the pixel number for a grid with strips arranged vertically.

    :param height: grid height in pixels
    :param alternating: Whether or not the lines in the grid run alternate directions in a zigzag
    :return: mapper(x, y)
    """

    def mapper(x, y):
        if alternating and x % 2:
            return x * height + (height - 1 - y)
        return x * height + y

    return mapper


def horizontal_strip_gridmap(width, alternating=True):
    """
    Determines the pixel number for a grid with strips arranged horizontally.

    :param width: grid width in pixels
    :param alternating: Whether or not the lines in the grid run alternate directions in a zigzag
    :return: mapper(x, y)
    """

    def mapper(x, y):
        if alternating and y % 2:
            return y * width + (width - 1 - x)
        return y * width + x

    return mapper


class PixelSubset(PixelMap):
    """
    PixelSubset lets you work with a subset of a pixel object.

    :param pixel_object: An object that implements the Neopixel or Dotstar protocol.
    :param int start: Starting pixel number.
    :param int end: Ending pixel number.

    .. code-block:: python

        import board
        import neopixel
        from adafruit_led_animation.helper import PixelSubset
        pixels = neopixel.NeoPixel(board.D12, 307, auto_write=False)

        star_start = 260
        star_arm = PixelSubset(pixels, star_start + 7, star_start + 15)
        star_arm.fill((255, 0, 255))
        pixels.show()
    """

    def __init__(self, pixel_object, start, end):
        super().__init__(
            pixel_object,
            pixel_ranges=[[n] for n in range(start, end)],
            individual_pixels=True,
        )


def pulse_generator(period: float, animation_object, dotstar_pwm=False):
    """
    Generates a sequence of colors for a pulse, based on the time period specified.
    :param period: Pulse duration in seconds.
    :param animation_object: An animation object to interact with.
    :param dotstar_pwm: Whether to use the dostar per pixel PWM value for brightness control.
    """
    period = int(period * MS_PER_SECOND)
    half_period = period // 2

    last_update = monotonic_ms()
    cycle_position = 0
    last_pos = 0
    while True:
        now = monotonic_ms()
        time_since_last_draw = now - last_update
        last_update = now
        pos = cycle_position = (cycle_position + time_since_last_draw) % period
        if pos < last_pos:
            animation_object.cycle_complete = True
        last_pos = pos
        if pos > half_period:
            pos = period - pos
        intensity = pos / half_period
        if dotstar_pwm:
            fill_color = (
                animation_object.color[0],
                animation_object.color[1],
                animation_object.color[2],
                intensity,
            )
            yield fill_color
            continue
        yield calculate_intensity(animation_object.color, intensity)
