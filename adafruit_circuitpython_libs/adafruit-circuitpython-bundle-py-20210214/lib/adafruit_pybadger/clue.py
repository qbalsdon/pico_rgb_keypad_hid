# SPDX-FileCopyrightText: 2020 Kattni Rembor for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_pybadger.clue`
================================================================================

Badge-focused CircuitPython helper library for CLUE.


* Author(s): Kattni Rembor

Implementation Notes
--------------------

**Hardware:**

* `Adafruit CLUE <https://www.adafruit.com/product/4500>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""

from collections import namedtuple
import board
import digitalio
import audiopwmio
from gamepad import GamePad
import adafruit_lsm6ds.lsm6ds33
import neopixel
from adafruit_pybadger.pybadger_base import PyBadgerBase

__version__ = "3.2.2"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_PyBadger.git"

Buttons = namedtuple("Buttons", "a b")


class Clue(PyBadgerBase):
    """Class that represents a single CLUE."""

    _audio_out = audiopwmio.PWMAudioOut
    _neopixel_count = 1

    def __init__(self):
        super().__init__()

        i2c = board.I2C()

        if i2c is not None:
            self._accelerometer = adafruit_lsm6ds.lsm6ds33.LSM6DS33(i2c)

        # NeoPixels
        self._neopixels = neopixel.NeoPixel(
            board.NEOPIXEL, self._neopixel_count, brightness=1, pixel_order=neopixel.GRB
        )

        self._buttons = GamePad(
            digitalio.DigitalInOut(board.BUTTON_A),
            digitalio.DigitalInOut(board.BUTTON_B),
        )

    @property
    def button(self):
        """The buttons on the board.

        Example use:

        .. code-block:: python

          from adafruit_pybadger import pybadger

          while True:
              if pybadger.button.a:
                  print("Button A")
              elif pybadger.button.b:
                  print("Button B")
        """
        button_values = self._buttons.get_pressed()
        return Buttons(
            button_values & PyBadgerBase.BUTTON_B, button_values & PyBadgerBase.BUTTON_A
        )

    @property
    def _unsupported(self):
        """This feature is not supported on CLUE."""
        raise NotImplementedError("This feature is not supported on CLUE.")

    # The following is a list of the features available in other PyBadger modules but
    # not available for CLUE. If called while using a CLUE, they will result in the
    # NotImplementedError raised in the property above.
    play_file = _unsupported
    light = _unsupported


clue = Clue()  # pylint: disable=invalid-name
"""Object that is automatically created on import."""
