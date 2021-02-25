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
`adafruit_led_animation.animation.rainbowsparkle`
================================================================================

Rainbow sparkle for CircuitPython helper library for LED animations.

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
from adafruit_led_animation.animation.rainbow import Rainbow


class RainbowSparkle(Rainbow):
    """Rainbow sparkle animation.

    :param pixel_object: The initialised LED object.
    :param float speed: Animation refresh rate in seconds, e.g. ``0.1``.
    :param float period: Period to cycle the rainbow over in seconds.  Default 5.
    :param int num_sparkles: The number of sparkles to display. Defaults to 1/20 of the pixel
                             object length.
    :param float step: Color wheel step.  Default 1.
    :param str name: Name of animation (optional, useful for sequences and debugging).
    :param float background_brightness: The brightness of the background rainbow. Defaults to
                                        ``0.2`` or 20 percent.
    :param bool precompute_rainbow: Whether to precompute the rainbow.  Uses more memory.
                                    (default True).
    """

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        pixel_object,
        speed,
        period=5,
        num_sparkles=None,
        step=1,
        name=None,
        background_brightness=0.2,
        precompute_rainbow=True,
    ):
        self._num_sparkles = num_sparkles
        if num_sparkles is None:
            self._num_sparkles = max(1, int(len(pixel_object) / 20))
        self._sparkle_duration = 2
        self._background_brightness = background_brightness
        self._bright_colors = None
        super().__init__(
            pixel_object=pixel_object,
            speed=speed,
            period=period,
            step=step,
            name=name,
            precompute_rainbow=precompute_rainbow,
        )

    def generate_rainbow(self):
        super().generate_rainbow()
        self._bright_colors = self.colors[:]
        for i, color in enumerate(self.colors):
            if isinstance(self.colors[i], int):
                self.colors[i] = (
                    int(self._background_brightness * ((color & 0xFF0000) >> 16)),
                    int(self._background_brightness * ((color & 0xFF00) >> 8)),
                    int(self._background_brightness * (color & 0xFF)),
                )
            else:
                self.colors[i] = (
                    int(self._background_brightness * color[0]),
                    int(self._background_brightness * color[1]),
                    int(self._background_brightness * color[2]),
                )

    def after_draw(self):
        self.show()
        pixels = [
            random.randint(0, len(self.pixel_object) - 1)
            for n in range(self._num_sparkles)
        ]
        for pixel in pixels:
            self.pixel_object[pixel] = self._bright_colors[
                (self._wheel_index + pixel) % len(self._bright_colors)
            ]
