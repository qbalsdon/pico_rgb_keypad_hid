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
`adafruit_led_animation.animation.sparkle`
================================================================================

Sparkle animation for CircuitPython helper library for LED animations.

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

import random
from adafruit_led_animation.animation import Animation

__version__ = "2.5.2"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_LED_Animation.git"


class Sparkle(Animation):
    """
    Sparkle animation of a single color.

    :param pixel_object: The initialised LED object.
    :param float speed: Animation speed in seconds, e.g. ``0.1``.
    :param color: Animation color in ``(r, g, b)`` tuple, or ``0x000000`` hex format.
    :param num_sparkles: Number of sparkles to generate per animation cycle.
    """

    # pylint: disable=too-many-arguments
    def __init__(self, pixel_object, speed, color, num_sparkles=1, name=None):
        if len(pixel_object) < 2:
            raise ValueError("Sparkle needs at least 2 pixels")
        self._half_color = color
        self._dim_color = color
        self._sparkle_color = color
        self._num_sparkles = num_sparkles
        self._num_pixels = len(pixel_object)
        self._pixels = []
        super().__init__(pixel_object, speed, color, name=name)

    def _set_color(self, color):
        half_color = tuple(color[rgb] // 4 for rgb in range(len(color)))
        dim_color = tuple(color[rgb] // 10 for rgb in range(len(color)))
        for pixel in range(len(self.pixel_object)):
            if self.pixel_object[pixel] == self._half_color:
                self.pixel_object[pixel] = half_color
            elif self.pixel_object[pixel] == self._dim_color:
                self.pixel_object[pixel] = dim_color
        self._half_color = half_color
        self._dim_color = dim_color
        self._sparkle_color = color

    def draw(self):
        self._pixels = [
            random.randint(0, (len(self.pixel_object) - 1))
            for _ in range(self._num_sparkles)
        ]
        for pixel in self._pixels:
            self.pixel_object[pixel] = self._sparkle_color

    def after_draw(self):
        self.show()
        for pixel in self._pixels:
            self.pixel_object[pixel % self._num_pixels] = self._half_color
            self.pixel_object[(pixel + 1) % self._num_pixels] = self._dim_color
