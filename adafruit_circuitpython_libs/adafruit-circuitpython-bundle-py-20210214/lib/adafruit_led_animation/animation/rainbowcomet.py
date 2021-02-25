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
`adafruit_led_animation.animation.rainbowcomet`
================================================================================

Rainbow comet for CircuitPython helper library for LED animations.

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

from adafruit_led_animation.animation.comet import Comet
from adafruit_led_animation.color import colorwheel, BLACK, calculate_intensity


class RainbowComet(Comet):
    """
    A rainbow comet animation.

    :param pixel_object: The initialised LED object.
    :param float speed: Animation speed in seconds, e.g. ``0.1``.
    :param int tail_length: The length of the comet. Defaults to 10. Cannot exceed the number of
                            pixels present in the pixel object, e.g. if the strip is 30 pixels
                            long, the ``tail_length`` cannot exceed 30 pixels.
    :param bool reverse: Animates the comet in the reverse order. Defaults to ``False``.
    :param bool bounce: Comet will bounce back and forth. Defaults to ``True``.
    :param int colorwheel_offset: Offset from start of colorwheel (0-255).
    :param int step: Colorwheel step (defaults to automatic).
    :param bool ring: Ring mode.  Defaults to ``False``.
    """

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        pixel_object,
        speed,
        tail_length=10,
        reverse=False,
        bounce=False,
        colorwheel_offset=0,
        step=0,
        name=None,
        ring=False,
    ):
        if step == 0:
            self._colorwheel_step = int(256 / tail_length)
        else:
            self._colorwheel_step = step
        self._colorwheel_offset = colorwheel_offset
        super().__init__(
            pixel_object, speed, 0, tail_length, reverse, bounce, name, ring
        )

    def _set_color(self, color):
        self._comet_colors = [BLACK]
        for n in range(self._tail_length):
            invert = self._tail_length - n - 1
            self._comet_colors.append(
                calculate_intensity(
                    colorwheel(
                        int((invert * self._colorwheel_step) + self._colorwheel_offset)
                        % 256
                    ),
                    n * self._color_step + 0.05,
                )
            )
        self._computed_color = color
