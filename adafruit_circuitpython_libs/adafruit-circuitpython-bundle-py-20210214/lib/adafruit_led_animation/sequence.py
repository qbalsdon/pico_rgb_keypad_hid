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
`adafruit_led_animation.sequence`
================================================================================

Animation sequence helper for CircuitPython helper library for LED animations.


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
from adafruit_led_animation.color import BLACK
from . import MS_PER_SECOND, monotonic_ms

__version__ = "2.5.2"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_LED_Animation.git"


class AnimationSequence:
    """
    A sequence of Animations to run in succession, looping forever.
    Advances manually, or at the specified interval.

    :param members: The animation objects or groups.
    :param int advance_interval: Time in seconds between animations if cycling
                                 automatically. Defaults to ``None``.
    :param bool auto_clear: Clear the pixels between animations. If ``True``, the current animation
                            will be cleared from the pixels before the next one starts.
                            Defaults to ``False``.
    :param bool random_order: Activate the animations in a random order. Defaults to ``False``.
    :param bool auto_reset: Automatically call reset() on animations when changing animations.
    :param bool advance_on_cycle_complete: Automatically advance when `on_cycle_complete` is
                                           triggered on member animations. All Animations must
                                           support on_cycle_complete to use this.

    .. code-block:: python

        import board
        import neopixel
        from adafruit_led_animation.sequence import AnimationSequence
        import adafruit_led_animation.animation.comet as comet_animation
        import adafruit_led_animation.animation.sparkle as sparkle_animation
        import adafruit_led_animation.animation.blink as blink_animation
        import adafruit_led_animation.color as color

        strip_pixels = neopixel.NeoPixel(board.A1, 30, brightness=1, auto_write=False)

        blink = blink_animation.Blink(strip_pixels, 0.2, color.RED)
        comet = comet_animation.Comet(strip_pixels, 0.1, color.BLUE)
        sparkle = sparkle_animation.Sparkle(strip_pixels, 0.05, color.GREEN)

        animations = AnimationSequence(blink, comet, sparkle, advance_interval=5)

        while True:
            animations.animate()
    """

    # pylint: disable=too-many-instance-attributes
    def __init__(
        self,
        *members,
        advance_interval=None,
        auto_clear=True,
        random_order=False,
        auto_reset=False,
        advance_on_cycle_complete=False,
        name=None
    ):
        if advance_interval and advance_on_cycle_complete:
            raise ValueError(
                "Cannot use both advance_interval and advance_on_cycle_complete."
            )
        self._members = members
        self._advance_interval = (
            advance_interval * MS_PER_SECOND if advance_interval else None
        )
        self._last_advance = monotonic_ms()
        self._current = 0
        self.auto_clear = auto_clear
        self.auto_reset = auto_reset
        self.advance_on_cycle_complete = advance_on_cycle_complete
        self.clear_color = BLACK
        self._paused = False
        self._paused_at = 0
        self._random = random_order
        self._also_notify = []
        self.cycle_count = 0
        self.notify_cycles = 1
        self.name = name
        if random_order:
            self._current = random.randint(0, len(self._members) - 1)
        self._color = None
        for member in self._members:
            member.add_cycle_complete_receiver(self._sequence_complete)
        self.on_cycle_complete_supported = self._members[-1].on_cycle_complete_supported

    on_cycle_complete_supported = True

    def __str__(self):
        return "<%s: %s>" % (self.__class__.__name__, self.name)

    def on_cycle_complete(self):
        """
        Called by some animations when they complete an animation cycle.
        Animations that support cycle complete notifications will have X property set to False.
        Override as needed.
        """
        self.cycle_count += 1
        if self.cycle_count % self.notify_cycles == 0:
            for callback in self._also_notify:
                callback(self)

    def _sequence_complete(self, animation):  # pylint: disable=unused-argument
        if self.advance_on_cycle_complete:
            self._advance()

    def add_cycle_complete_receiver(self, callback):
        """
        Adds an additional callback when the cycle completes.

        :param callback: Additional callback to trigger when a cycle completes.  The callback
                         is passed the animation object instance.
        """
        self._also_notify.append(callback)

    def _auto_advance(self):
        if not self._advance_interval:
            return
        now = monotonic_ms()
        if now - self._last_advance > self._advance_interval:
            self._last_advance = now
            self._advance()

    def _advance(self):
        if self.auto_reset:
            self.current_animation.reset()
        if self.auto_clear:
            self.current_animation.fill(self.clear_color)
        if self._random:
            self.random()
        else:
            self.next()

    def activate(self, index):
        """
        Activates a specific animation.
        """
        if isinstance(index, str):
            self._current = [member.name for member in self._members].index(index)
        else:
            self._current = index
        if self._color:
            self.current_animation.color = self._color

    def next(self):
        """
        Jump to the next animation.
        """
        current = self._current + 1
        if current >= len(self._members):
            self.on_cycle_complete()
        self.activate(current % len(self._members))

    def random(self):
        """
        Jump to a random animation.
        """
        self.activate(random.randint(0, len(self._members) - 1))

    def animate(self, show=True):
        """
        Call animate() from your code's main loop.  It will draw the current animation
        or go to the next animation based on the advance_interval if set.

        :return: True if the animation draw cycle was triggered, otherwise False.
        """
        if not self._paused and self._advance_interval:
            self._auto_advance()
        return self.current_animation.animate(show)

    @property
    def current_animation(self):
        """
        Returns the current animation in the sequence.
        """
        return self._members[self._current]

    @property
    def color(self):
        """
        Use this property to change the color of all animations in the sequence.
        """
        return self._color

    @color.setter
    def color(self, color):
        self._color = color
        self.current_animation.color = color

    def fill(self, color):
        """
        Fills the current animation with a color.
        """
        self.current_animation.fill(color)

    def freeze(self):
        """
        Freeze the current animation in the sequence.
        Also stops auto_advance.
        """
        if self._paused:
            return
        self._paused = True
        self._paused_at = monotonic_ms()
        self.current_animation.freeze()

    def resume(self):
        """
        Resume the current animation in the sequence, and resumes auto advance if enabled.
        """
        if not self._paused:
            return
        self._paused = False
        now = monotonic_ms()
        self._last_advance += now - self._paused_at
        self._paused_at = 0
        self.current_animation.resume()

    def reset(self):
        """
        Resets the current animation.
        """
        self.current_animation.reset()

    def show(self):
        """
        Draws the current animation group members.
        """
        self.current_animation.show()


class AnimateOnce(AnimationSequence):
    """
    Wrapper around AnimationSequence that returns False to animate() until a sequence has completed.
    Takes the same arguments as AnimationSequence, but overrides advance_on_cycle_complete=True
    and advance_interval=0

    Example:

    This example animates a comet in one direction then pulses red momentarily

    .. code-block:: python

        import board
        import neopixel
        from adafruit_led_animation.animation.comet import Comet
        from adafruit_led_animation.animation.pulse import Pulse
        from adafruit_led_animation.color import BLUE, RED
        from adafruit_led_animation.sequence import AnimateOnce

        strip_pixels = neopixel.NeoPixel(board.A1, 30, brightness=0.5, auto_write=False)

        comet = Comet(strip_pixels, 0.01, color=BLUE, bounce=False)
        pulse = Pulse(strip_pixels, 0.01, color=RED, period=2)

        animations = AnimateOnce(comet, pulse)

        while animations.animate():
            pass

    """

    def __init__(self, *members, **kwargs):
        kwargs["advance_on_cycle_complete"] = True
        kwargs["advance_interval"] = 0
        super().__init__(*members, **kwargs)
        self._running = True

    def on_cycle_complete(self):
        super().on_cycle_complete()
        self._running = False

    def animate(self, show=True):
        super().animate(show)
        return self._running
