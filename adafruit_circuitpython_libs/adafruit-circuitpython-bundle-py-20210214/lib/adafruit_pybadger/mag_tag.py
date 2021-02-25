# SPDX-FileCopyrightText: 2020 Tim C for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_pybadger.mag_tag`
================================================================================

Badge-focused CircuitPython helper library for Mag Tag.


* Author(s): Kattni Rembor, Tim C

Implementation Notes
--------------------

**Hardware:**

* `Adafruit Mag Tag <https://www.adafruit.com/product/4800>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""

from collections import namedtuple
import board

# import digitalio
# from gamepad import GamePad
import neopixel
from adafruit_pybadger.pybadger_base import PyBadgerBase

__version__ = "3.2.2"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_PyBadger.git"

Buttons = namedtuple("Buttons", "a b c d")


class MagTag(PyBadgerBase):
    """Class that represents a single Mag Tag."""

    _neopixel_count = 4

    def __init__(self):
        super().__init__()

        # NeoPixels
        self._neopixels = neopixel.NeoPixel(
            board.NEOPIXEL, self._neopixel_count, brightness=1, pixel_order=neopixel.GRB
        )

        # self._buttons = GamePad(
        #    ,
        #    digitalio.DigitalInOut(board.BUTTON_B),
        #    digitalio.DigitalInOut(board.BUTTON_C),
        #    digitalio.DigitalInOut(board.BUTTON_D),
        # )

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
        # button_values = self._buttons.get_pressed()
        # return Buttons(
        #    button_values & PyBadgerBase.BUTTON_B, button_values & PyBadgerBase.BUTTON_A,
        #    button_values & PyBadgerBase.BUTTON_START, button_values & PyBadgerBase.BUTTON_SELECT
        # )

    @property
    def _unsupported(self):
        """This feature is not supported on Mag Tag."""
        raise NotImplementedError("This feature is not supported on Mag Tag.")

    # The following is a list of the features available in other PyBadger modules but
    # not available for Mag Tag. If called while using a Mag Tag, they will result in the
    # NotImplementedError raised in the property above.
    play_file = _unsupported
    light = _unsupported
    acceleration = _unsupported
    button = _unsupported


mag_tag = MagTag()  # pylint: disable=invalid-name
"""Object that is automatically created on import."""
