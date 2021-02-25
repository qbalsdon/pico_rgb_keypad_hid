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
`adafruit_led_animation.animation.sparklepulse`
================================================================================

Sparkle-pulse animation for CircuitPython helper library for LED animations.

* Author(s): dmolavi

Implementation Notes
--------------------

**Hardware:**

* `Adafruit NeoPixels <https://www.adafruit.com/category/168>`_
* `Adafruit DotStars <https://www.adafruit.com/category/885>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://circuitpython.org/downloads


"""

from adafruit_led_animation.animation.sparkle import Sparkle
from adafruit_led_animation.helper import pulse_generator


class SparklePulse(Sparkle):
    """
    Combination of the Sparkle and Pulse animations.

    :param pixel_object: The initialised LED object.
    :param int speed: Animation refresh rate in seconds, e.g. ``0.1``.
    :param color: Animation color in ``(r, g, b)`` tuple, or ``0x000000`` hex format.
    :param period: Period to pulse the LEDs over.  Default 5.
    :param max_intensity: The maximum intensity to pulse, between 0 and 1.0.  Default 1.
    :param min_intensity: The minimum intensity to pulse, between 0 and 1.0.  Default 0.
    """

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        pixel_object,
        speed,
        color,
        period=5,
        max_intensity=1,
        min_intensity=0,
        name=None,
    ):
        self._max_intensity = max_intensity
        self._min_intensity = min_intensity
        self._period = period
        dotstar = len(pixel_object) == 4 and isinstance(pixel_object[0][-1], float)
        super().__init__(
            pixel_object, speed=speed, color=color, num_sparkles=1, name=name
        )
        self._generator = pulse_generator(self._period, self, dotstar_pwm=dotstar)

    def _set_color(self, color):
        self._color = color

    def draw(self):
        self._sparkle_color = next(self._generator)
        super().draw()

    def after_draw(self):
        self.show()
