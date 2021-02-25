# SPDX-FileCopyrightText: 2017 Dean Miller for Adafruit Industries
#
# SPDX-License-Identifier: MIT

# pylint: disable=missing-docstring,invalid-name,too-many-public-methods,too-few-public-methods

"""
`adafruit_seesaw.pwmout`
====================================================
"""

__version__ = "1.7.1"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_seesaw.git"


class PWMOut:
    """A single seesaw channel that matches the :py:class:`~pwmio.PWMOut` API."""

    def __init__(self, seesaw, pin):
        self._seesaw = seesaw
        self._pin = pin
        self._dc = 0
        self._frequency = 0

    @property
    def frequency(self):
        """The overall PWM frequency in Hertz."""
        return self._frequency

    @frequency.setter
    def frequency(self, frequency):
        self._seesaw.set_pwm_freq(self._pin, frequency)
        self._frequency = frequency

    @property
    def duty_cycle(self):
        """16-bit value that dictates how much of one cycle is high (1) versus low (0).
        65535 (0xffff) will always be high, 0 will always be low,
        and 32767 (0x7fff) will be half high and then half low.
        """
        return self._dc

    @duty_cycle.setter
    def duty_cycle(self, value):
        if not 0 <= value <= 0xFFFF:
            raise ValueError("Must be 0 to 65535")
        self._seesaw.analog_write(self._pin, value)
        self._dc = value

    @property
    def fraction(self):
        """Expresses duty_cycle as a fractional value. Ranges from 0.0-1.0."""
        return self.duty_cycle / 65535

    @fraction.setter
    def fraction(self, value):
        if not 0.0 <= value <= 1.0:
            raise ValueError("Must be 0.0 to 1.0")
        self.duty_cycle = int(value * 65535)
