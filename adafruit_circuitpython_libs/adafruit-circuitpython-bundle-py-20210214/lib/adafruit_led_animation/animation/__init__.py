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
`adafruit_led_animation.animation`
================================================================================

Animation base class for CircuitPython helper library for LED animations.

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

from adafruit_led_animation import MS_PER_SECOND, monotonic_ms


class Animation:
    # pylint: disable=too-many-instance-attributes
    """
    Base class for animations.
    """
    on_cycle_complete_supported = False

    # pylint: disable=too-many-arguments
    def __init__(self, pixel_object, speed, color, peers=None, paused=False, name=None):
        self.pixel_object = pixel_object
        self.pixel_object.auto_write = False
        self._peers = [self] + peers if peers is not None else [self]
        self._speed_ms = 0
        self._color = None
        self._paused = paused
        self._next_update = monotonic_ms()
        self._time_left_at_pause = 0
        self._also_notify = []
        self.speed = speed  # sets _speed_ms
        self.color = color  # Triggers _set_color
        self.name = name
        self.cycle_complete = False
        self.notify_cycles = 1
        """Number of cycles to trigger additional cycle_done notifications after"""
        self.draw_count = 0
        """Number of animation frames drawn."""
        self.cycle_count = 0
        """Number of animation cycles completed."""

    def __str__(self):
        return "<%s: %s>" % (self.__class__.__name__, self.name)

    def animate(self, show=True):
        """
        Call animate() from your code's main loop.  It will draw the animation draw() at intervals
        configured by the speed property (set from init).

        :param bool show: Whether to automatically call show on the pixel object when an animation
                          fires.  Default True.
        :return: True if the animation draw cycle was triggered, otherwise False.
        """
        if self._paused:
            return False

        now = monotonic_ms()
        if now < self._next_update:
            return False

        # Draw related animations together
        for anim in self._peers:
            anim.draw_count += 1
            anim.draw()
            anim.after_draw()

        if show:
            for anim in self._peers:
                anim.show()

        # Note that the main animation cycle_complete flag is used, not the peer flag.
        for anim in self._peers:
            if anim.cycle_complete:
                anim.cycle_complete = False
                anim.on_cycle_complete()

        self._next_update = now + self._speed_ms
        return True

    def draw(self):
        """
        Animation subclasses must implement draw() to render the animation sequence.
        Animations should not call show(), as animate() will do so, after after_draw().
        Animations should set .cycle_done = True when an animation cycle is completed.
        """
        raise NotImplementedError()

    def after_draw(self):
        """
        Animation subclasses may implement after_draw() to do operations after the main draw()
        is called.
        """

    def show(self):
        """
        Displays the updated pixels.  Called during animates with changes.
        """
        self.pixel_object.show()

    @property
    def peers(self):
        """
        Get the animation's peers.  Peers are drawn, then shown together.
        """
        return self._peers[1:]

    @peers.setter
    def peers(self, peer_list):
        """
        Set the animation's peers.
        :param list peer_list: List of peer animations.
        """
        if peer_list is not None:
            self._peers = [self] + list(peer_list)

    def freeze(self):
        """
        Stops the animation until resumed.
        """
        self._paused = True
        self._time_left_at_pause = max(0, monotonic_ms() - self._next_update)

    def resume(self):
        """
        Resumes the animation.
        """
        self._next_update = monotonic_ms() + self._time_left_at_pause
        self._time_left_at_pause = 0
        self._paused = False

    def fill(self, color):
        """
        Fills the pixel object with a color.
        """
        self.pixel_object.fill(color)
        self.pixel_object.show()

    @property
    def color(self):
        """
        The current color.
        """
        return self._color

    @color.setter
    def color(self, color):
        if self._color == color:
            return
        if isinstance(color, int):
            color = (color >> 16 & 0xFF, color >> 8 & 0xFF, color & 0xFF)
        self._set_color(color)

    def _set_color(self, color):
        """
        Called after the color is changed, which includes at initialization.
        Override as needed.
        """
        self._color = color

    @property
    def speed(self):
        """
        The animation speed in fractional seconds.
        """
        return self._speed_ms / MS_PER_SECOND

    @speed.setter
    def speed(self, seconds):
        self._speed_ms = int(seconds * MS_PER_SECOND)

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

    def reset(self):
        """
        Resets the animation sequence.
        """
