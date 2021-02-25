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
`adafruit_led_animation.group`
================================================================================

Animation group helper for CircuitPython helper library for LED animations..


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

__version__ = "2.5.2"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_LED_Animation.git"

from adafruit_led_animation.animation import Animation


class AnimationGroup:
    """
    AnimationGroup synchronizes multiple animations.  Allows for multiple animations to be kept in
    sync, whether or not the same animation or pixel object is in use.

    :param members: The animation objects or groups.
    :param bool sync: Synchronises when draw is called for all members of the group to the settings
                      of the first member of the group. Defaults to ``False``.


    Example:

        .. code-block::

            import board
            import neopixel
            from adafruit_circuitplayground import cp
            from adafruit_led_animation.animation.blink import Blink
            from adafruit_led_animation.animation.comet import Comet
            from adafruit_led_animation.animation.chase import Chase
            from adafruit_led_animation.group import AnimationGroup
            from adafruit_led_animation.sequence import AnimationSequence

            import adafruit_led_animation.color as color

            strip_pixels = neopixel.NeoPixel(board.A1, 30, brightness=0.5, auto_write=False)
            cp.pixels.brightness = 0.5

            animations = AnimationSequence(
                # Synchronized to 0.5 seconds. Ignores the second animation setting of 3 seconds.
                AnimationGroup(
                    Blink(cp.pixels, 0.5, color.CYAN),
                    Blink(strip_pixels, 3.0, color.AMBER),
                    sync=True,
                ),
                # Different speeds
                AnimationGroup(
                    Comet(cp.pixels, 0.1, color.MAGENTA, tail_length=5),
                    Comet(strip_pixels, 0.01, color.MAGENTA, tail_length=15),
                ),
                # Sequential animations on the built-in NeoPixels then the NeoPixel strip
                Chase(cp.pixels, 0.05, size=2, spacing=3, color=color.PURPLE),
                Chase(strip_pixels, 0.05, size=2, spacing=3, color=color.PURPLE),
                advance_interval=3.0,
                auto_clear=True,
                auto_reset=True,
            )

            while True:
                animations.animate()
    """

    def __init__(self, *members, sync=False, name=None):
        if not members:
            raise ValueError("At least one member required in an AnimationGroup")
        self.draw_count = 0
        """Number of animation frames drawn."""
        self.cycle_count = 0
        """Number of animation cycles completed."""
        self.notify_cycles = 1
        """Number of cycles to trigger additional cycle_done notifications after"""
        self._members = list(members)
        self._sync = sync
        self._also_notify = []
        self.cycle_count = 0
        self.name = name
        if sync:
            main = members[0]
            main.peers = members[1:]

        # Catch cycle_complete on the last animation.
        self._members[-1].add_cycle_complete_receiver(self._group_done)
        self.on_cycle_complete_supported = self._members[-1].on_cycle_complete_supported

    def __str__(self):
        return "<AnimationGroup %s: %s>" % (self.__class__.__name__, self.name)

    def _group_done(self, animation):  # pylint: disable=unused-argument
        self.on_cycle_complete()

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

    def add_cycle_complete_receiver(self, callback):
        """
        Adds an additional callback when the cycle completes.

        :param callback: Additional callback to trigger when a cycle completes.  The callback
                         is passed the animation object instance.
        """
        self._also_notify.append(callback)

    def animate(self, show=True):
        """
        Call animate() from your code's main loop.  It will draw all of the animations
        in the group.

        :return: True if any animation draw cycle was triggered, otherwise False.
        """
        if self._sync:
            result = self._members[0].animate(show=False)
            if result and show:
                last_strip = None
                for member in self._members:
                    if isinstance(member, Animation):
                        if last_strip != member.pixel_object:
                            member.pixel_object.show()
                            last_strip = member.pixel_object
                    else:
                        member.show()
            return result

        return any([item.animate(show) for item in self._members])

    @property
    def color(self):
        """
        Use this property to change the color of all members of the animation group.
        """
        return None

    @color.setter
    def color(self, color):
        for item in self._members:
            item.color = color

    def fill(self, color):
        """
        Fills all pixel objects in the group with a color.
        """
        for item in self._members:
            item.fill(color)

    def freeze(self):
        """
        Freeze all animations in the group.
        """
        for item in self._members:
            item.freeze()

    def resume(self):
        """
        Resume all animations in the group.
        """
        for item in self._members:
            item.resume()

    def reset(self):
        """
        Resets the animations in the group.
        """
        for item in self._members:
            item.reset()

    def show(self):
        """
        Draws the current animation group members.
        """
        for item in self._members:
            item.show()
