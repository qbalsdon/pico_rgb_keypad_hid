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
`adafruit_led_animation.animation.chase`
================================================================================

Theatre chase animation for CircuitPython helper library for LED animations.

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

from math import ceil

from adafruit_led_animation.animation import Animation


class Chase(Animation):
    """
    Chase pixels in one direction in a single color, like a theater marquee sign.

    :param pixel_object: The initialised LED object.
    :param float speed: Animation speed rate in seconds, e.g. ``0.1``.
    :param color: Animation color in ``(r, g, b)`` tuple, or ``0x000000`` hex format.
    :param size: Number of pixels to turn on in a row.
    :param spacing: Number of pixels to turn off in a row.
    :param reverse: Reverse direction of movement.
    """

    # pylint: disable=too-many-arguments
    def __init__(
        self, pixel_object, speed, color, size=2, spacing=3, reverse=False, name=None
    ):
        self._size = size
        self._spacing = spacing
        self._repeat_width = size + spacing
        self._num_repeats = ceil(len(pixel_object) / self._repeat_width)
        self._overflow = len(pixel_object) % self._repeat_width
        self._direction = 1 if not reverse else -1
        self._reverse = reverse
        self._offset = 0

        def _resetter():
            self._offset = 0
            self._reverse = reverse
            self._direction = 1 if not reverse else -1

        self._reset = _resetter

        super().__init__(pixel_object, speed, color, name=name)

    on_cycle_complete_supported = True

    @property
    def reverse(self):
        """
        Whether the animation is reversed
        """
        return self._reverse

    @reverse.setter
    def reverse(self, value):
        self._reverse = value
        self._direction = -1 if self._reverse else 1

    def draw(self):
        def bar_colors():
            bar_no = 0
            for i in range(self._offset, 0, -1):
                if i > self._spacing:
                    yield self.bar_color(bar_no, i)
                else:
                    yield self.space_color(bar_no, i)
                    bar_no = 1
            while True:
                for bar_pixel in range(self._size):
                    yield self.bar_color(bar_no, bar_pixel)
                for space_pixel in range(self._spacing):
                    yield self.space_color(bar_no, space_pixel)
                bar_no += 1

        colorgen = bar_colors()
        self.pixel_object[:] = [next(colorgen) for _ in self.pixel_object]

        if self.draw_count % len(self.pixel_object) == 0:
            self.cycle_complete = True
        self._offset = (self._offset + self._direction) % self._repeat_width

    def bar_color(self, n, pixel_no=0):  # pylint: disable=unused-argument
        """
        Generate the color for the n'th bar_color in the Chase

        :param n: The pixel group to get the color for
        :param pixel_no: Which pixel in the group to get the color for
        """
        return self.color

    def space_color(self, n, pixel_no=0):  # pylint: disable=unused-argument,no-self-use
        """
        Generate the spacing color for the n'th bar_color in the Chase

        :param n: The pixel group to get the spacing color for
        :param pixel_no: Which pixel in the group to get the spacing color for
        """
        return 0

    def reset(self):
        """
        Reset the animation.
        """
        self._reset()
