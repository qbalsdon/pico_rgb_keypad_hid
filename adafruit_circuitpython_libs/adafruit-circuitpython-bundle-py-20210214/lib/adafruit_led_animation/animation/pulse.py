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
`adafruit_led_animation.animation.pulse`
================================================================================

Pulse animation for CircuitPython helper library for LED animations.

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


class Pulse(Animation):
    """
    Pulse all pixels a single color.

    :param pixel_object: The initialised LED object.
    :param float speed: Animation refresh rate in seconds, e.g. ``0.1``.
    :param color: Animation color in ``(r, g, b)`` tuple, or ``0x000000`` hex format.
    :param period: Period to pulse the LEDs over.  Default 5.
    """

    # pylint: disable=too-many-arguments
    def __init__(self, pixel_object, speed, color, period=5, name=None):
        super().__init__(pixel_object, speed, color, name=name)
        self._period = period
        self._generator = None
        self.reset()

    on_cycle_complete_supported = True

    def draw(self):
        color = next(self._generator)
        self.pixel_object.fill(color)

    def reset(self):
        """
        Resets the animation.
        """
        dotstar = len(self.pixel_object[0]) == 4 and isinstance(
            self.pixel_object[0][-1], float
        )
        from adafruit_led_animation.helper import (  # pylint: disable=import-outside-toplevel
            pulse_generator,
        )

        self._generator = pulse_generator(self._period, self, dotstar_pwm=dotstar)
