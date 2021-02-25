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
`adafruit_led_animation.animation.rainbow`
================================================================================

Rainbow animation for CircuitPython helper library for LED animations.

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
from adafruit_led_animation.color import BLACK, colorwheel
from adafruit_led_animation import MS_PER_SECOND, monotonic_ms

__version__ = "2.5.2"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_LED_Animation.git"


class Rainbow(Animation):
    """
    The classic rainbow color wheel.

    :param pixel_object: The initialised LED object.
    :param float speed: Animation refresh rate in seconds, e.g. ``0.1``.
    :param float period: Period to cycle the rainbow over in seconds.  Default 5.
    :param float step: Color wheel step.  Default 1.
    :param str name: Name of animation (optional, useful for sequences and debugging).
    :param bool precompute_rainbow: Whether to precompute the rainbow.  Uses more memory.
                                    (default True).
    """

    # pylint: disable=too-many-arguments
    def __init__(
        self, pixel_object, speed, period=5, step=1, name=None, precompute_rainbow=True
    ):
        super().__init__(pixel_object, speed, BLACK, name=name)
        self._period = period
        self._step = step
        self._wheel_index = 0
        self.colors = None
        self._generator = self._color_wheel_generator()
        if precompute_rainbow:
            self.generate_rainbow()

    def generate_rainbow(self):
        """Generates the rainbow."""
        self.colors = []
        i = 0
        while i < 256:
            self.colors.append(colorwheel(int(i)))
            i += self._step

    on_cycle_complete_supported = True

    def _color_wheel_generator(self):
        period = int(self._period * MS_PER_SECOND)

        num_pixels = len(self.pixel_object)
        last_update = monotonic_ms()
        cycle_position = 0
        last_pos = 0
        while True:
            cycle_completed = False
            now = monotonic_ms()
            time_since_last_draw = now - last_update
            last_update = now
            pos = cycle_position = (cycle_position + time_since_last_draw) % period
            if pos < last_pos:
                cycle_completed = True
            last_pos = pos
            wheel_index = int((pos / period) * len(self.colors))

            if self.colors:
                self._draw_precomputed(num_pixels, wheel_index)
            else:
                wheel_index = int((pos / period) * 256)
                self.pixel_object[:] = [
                    colorwheel((i + wheel_index) % 255) for i in range(num_pixels)
                ]
            self._wheel_index = wheel_index
            if cycle_completed:
                self.cycle_complete = True
            yield

    def _draw_precomputed(self, num_pixels, wheel_index):
        for i in range(0, num_pixels, len(self.colors)):
            num = len(self.colors)
            if i + len(self.colors) > num_pixels:
                num = num_pixels - i
            if wheel_index + num > len(self.colors):
                colors_left = len(self.colors) - wheel_index
                self.pixel_object[i : i + colors_left] = self.colors[wheel_index:]
                self.pixel_object[i + colors_left : i + num] = self.colors[
                    : num - colors_left
                ]
            else:
                self.pixel_object[i : i + num] = self.colors[
                    wheel_index : wheel_index + num
                ]

    def draw(self):
        next(self._generator)

    def reset(self):
        """
        Resets the animation.
        """
        self._generator = self._color_wheel_generator()
