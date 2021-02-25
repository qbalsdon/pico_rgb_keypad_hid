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
`adafruit_led_animation.animation.comet`
================================================================================

Comet animation for CircuitPython helper library for LED animations.

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

from adafruit_led_animation.animation import Animation
from adafruit_led_animation.color import BLACK, calculate_intensity


class Comet(Animation):
    """
    A comet animation.

    :param pixel_object: The initialised LED object.
    :param float speed: Animation speed in seconds, e.g. ``0.1``.
    :param color: Animation color in ``(r, g, b)`` tuple, or ``0x000000`` hex format.
    :param int tail_length: The length of the comet. Defaults to 25% of the length of the
                            ``pixel_object``. Automatically compensates for a minimum of 2 and a
                            maximum of the length of the ``pixel_object``.
    :param bool reverse: Animates the comet in the reverse order. Defaults to ``False``.
    :param bool bounce: Comet will bounce back and forth. Defaults to ``True``.
    :param bool ring: Ring mode.  Defaults to ``False``.
    """

    # pylint: disable=too-many-arguments,too-many-instance-attributes
    def __init__(
        self,
        pixel_object,
        speed,
        color,
        tail_length=0,
        reverse=False,
        bounce=False,
        name=None,
        ring=False,
    ):
        if tail_length == 0:
            tail_length = len(pixel_object) // 4
        if bounce and ring:
            raise ValueError("Cannot combine bounce and ring mode")
        self.reverse = reverse
        self.bounce = bounce
        self._initial_reverse = reverse
        self._tail_length = tail_length
        self._color_step = 0.95 / tail_length
        self._comet_colors = None
        self._computed_color = color
        self._num_pixels = len(pixel_object)
        self._direction = -1 if reverse else 1
        self._left_side = -self._tail_length
        self._right_side = self._num_pixels
        self._tail_start = 0
        self._ring = ring
        if ring:
            self._left_side = 0
        self.reset()
        super().__init__(pixel_object, speed, color, name=name)

    on_cycle_complete_supported = True

    def _set_color(self, color):
        self._comet_colors = [BLACK]
        for n in range(self._tail_length):
            self._comet_colors.append(
                calculate_intensity(color, n * self._color_step + 0.05)
            )
        self._computed_color = color

    def draw(self):
        colors = self._comet_colors
        if self.reverse:
            colors = reversed(colors)
        for pixel_no, color in enumerate(colors):
            draw_at = self._tail_start + pixel_no
            if draw_at < 0 or draw_at >= self._num_pixels:
                if not self._ring:
                    continue
                draw_at = draw_at % self._num_pixels

            self.pixel_object[draw_at] = color

        self._tail_start += self._direction

        if self._tail_start < self._left_side or self._tail_start >= self._right_side:
            if self.bounce:
                self.reverse = not self.reverse
                self._direction = -self._direction
            elif self._ring:
                self._tail_start = self._tail_start % self._num_pixels
            else:
                self.reset()
            if self.reverse == self._initial_reverse and self.draw_count > 0:
                self.cycle_complete = True

    def reset(self):
        """
        Resets to the first state.
        """
        self.reverse = self._initial_reverse
        if self.reverse:
            self._tail_start = self._num_pixels + self._tail_length + 1
        else:
            self._tail_start = -self._tail_length - 1

        if self._ring:
            self._tail_start = self._tail_start % self._num_pixels
