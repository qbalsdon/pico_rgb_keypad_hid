# SPDX-FileCopyrightText: 2019 Dave Astels for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_debouncer`
====================================================

Debounces an arbitrary predicate function (typically created as a lambda) of 0
arguments.  Since a very common use is debouncing a digital input pin, the
initializer accepts a DigitalInOut object instead of a lambda.

* Author(s): Dave Astels

Implementation Notes
--------------------

**Hardware:**

Not all hardware / CircuitPython combinations are capable of running the
debouncer correctly for an extended length of time.  If this line works
on your microcontroller, then the debouncer should work forever:

``from time import monotonic_ns``

If it gives an ImportError, then the time values available in Python become
less accurate over the days, and the debouncer will take longer to react to
button presses.

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases
"""

# imports

__version__ = "1.3.9"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_Debouncer.git"

import time
from micropython import const

_DEBOUNCED_STATE = const(0x01)
_UNSTABLE_STATE = const(0x02)
_CHANGED_STATE = const(0x04)

# Find out whether the current CircuitPython really supports time.monotonic_ns(),
# which doesn't have the accuracy limitation.
try:
    time.monotonic_ns()
    TICKS_PER_SEC = 1_000_000_000
    MONOTONIC_TICKS = time.monotonic_ns
except (AttributeError, NotImplementedError):
    TICKS_PER_SEC = 1
    MONOTONIC_TICKS = time.monotonic


class Debouncer:
    """Debounce an input pin or an arbitrary predicate"""

    def __init__(self, io_or_predicate, interval=0.010):
        """Make am instance.
        :param DigitalInOut/function io_or_predicate: the DigitalIO or function to debounce
        :param int interval: bounce threshold in seconds (default is 0.010, i.e. 10 milliseconds)
        """
        self.state = 0x00
        if hasattr(io_or_predicate, "value"):
            self.function = lambda: io_or_predicate.value
        else:
            self.function = io_or_predicate
        if self.function():
            self._set_state(_DEBOUNCED_STATE | _UNSTABLE_STATE)
        self._last_bounce_ticks = 0
        self._last_duration_ticks = 0
        self._state_changed_ticks = 0

        # Could use the .interval setter, but pylint prefers that we explicitly
        # set the real underlying attribute:
        self._interval_ticks = interval * TICKS_PER_SEC

    def _set_state(self, bits):
        self.state |= bits

    def _unset_state(self, bits):
        self.state &= ~bits

    def _toggle_state(self, bits):
        self.state ^= bits

    def _get_state(self, bits):
        return (self.state & bits) != 0

    def update(self):
        """Update the debouncer state. MUST be called frequently"""
        now_ticks = MONOTONIC_TICKS()
        self._unset_state(_CHANGED_STATE)
        current_state = self.function()
        if current_state != self._get_state(_UNSTABLE_STATE):
            self._last_bounce_ticks = now_ticks
            self._toggle_state(_UNSTABLE_STATE)
        else:
            if now_ticks - self._last_bounce_ticks >= self._interval_ticks:
                if current_state != self._get_state(_DEBOUNCED_STATE):
                    self._last_bounce_ticks = now_ticks
                    self._toggle_state(_DEBOUNCED_STATE)
                    self._set_state(_CHANGED_STATE)
                    self._last_duration_ticks = now_ticks - self._state_changed_ticks
                    self._state_changed_ticks = now_ticks

    @property
    def interval(self):
        """The debounce delay, in seconds"""
        return self._interval_ticks / TICKS_PER_SEC

    @interval.setter
    def interval(self, new_interval_s):
        self._interval_ticks = new_interval_s * TICKS_PER_SEC

    @property
    def value(self):
        """Return the current debounced value."""
        return self._get_state(_DEBOUNCED_STATE)

    @property
    def rose(self):
        """Return whether the debounced value went from low to high at the most recent update."""
        return self._get_state(_DEBOUNCED_STATE) and self._get_state(_CHANGED_STATE)

    @property
    def fell(self):
        """Return whether the debounced value went from high to low at the most recent update."""
        return (not self._get_state(_DEBOUNCED_STATE)) and self._get_state(
            _CHANGED_STATE
        )

    @property
    def last_duration(self):
        """Return the number of seconds the state was stable prior to the most recent transition."""
        return self._last_duration_ticks / TICKS_PER_SEC

    @property
    def current_duration(self):
        """Return the number of seconds since the most recent transition."""
        return (MONOTONIC_TICKS() - self._state_changed_ticks) / TICKS_PER_SEC
