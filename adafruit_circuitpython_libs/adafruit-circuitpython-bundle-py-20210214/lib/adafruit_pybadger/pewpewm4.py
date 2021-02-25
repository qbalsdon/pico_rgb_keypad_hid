# SPDX-FileCopyrightText: 2020 Kattni Rembor for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_pybadger.clue`
================================================================================

Badge-focused CircuitPython helper library for Pew Pew M4.


* Author(s): Kattni Rembor

Implementation Notes
--------------------

**Hardware:**

* `Pew Pew M4 <https://hackaday.io/project/165032-pewpew-m4>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""

from collections import namedtuple
import board
import digitalio
import audioio
from gamepad import GamePad
from adafruit_pybadger.pybadger_base import PyBadgerBase

__version__ = "3.2.2"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_PyBadger.git"

Buttons = namedtuple("Buttons", ("o", "x", "z", "right", "down", "up", "left"))


class PewPewM4(PyBadgerBase):
    """Class that represents a single Pew Pew M4."""

    _audio_out = audioio.AudioOut
    _neopixel_count = 0

    def __init__(self):
        super().__init__()

        self._buttons = GamePad(
            digitalio.DigitalInOut(board.BUTTON_O),
            digitalio.DigitalInOut(board.BUTTON_X),
            digitalio.DigitalInOut(board.BUTTON_Z),
            digitalio.DigitalInOut(board.BUTTON_RIGHT),
            digitalio.DigitalInOut(board.BUTTON_DOWN),
            digitalio.DigitalInOut(board.BUTTON_UP),
            digitalio.DigitalInOut(board.BUTTON_LEFT),
        )

    @property
    def button(self):
        """The buttons on the board.

        Example use:

        .. code-block:: python

          from adafruit_pybadger import pybadger

          while True:
              if pybadger.button.x:
                  print("Button X")
              elif pybadger.button.o:
                  print("Button O")
        """
        button_values = self._buttons.get_pressed()
        return Buttons(
            *[
                button_values & button
                for button in (
                    PyBadgerBase.BUTTON_B,
                    PyBadgerBase.BUTTON_A,
                    PyBadgerBase.BUTTON_START,
                    PyBadgerBase.BUTTON_SELECT,
                    PyBadgerBase.BUTTON_RIGHT,
                    PyBadgerBase.BUTTON_DOWN,
                    PyBadgerBase.BUTTON_UP,
                )
            ]
        )

    @property
    def _unsupported(self):
        """This feature is not supported on PewPew M4."""
        raise NotImplementedError("This feature is not supported on PewPew M4.")

    # The following is a list of the features available in other PyBadger modules but
    # not available for CLUE. If called while using a CLUE, they will result in the
    # NotImplementedError raised in the property above.
    light = _unsupported
    acceleration = _unsupported
    pixels = _unsupported


pewpewm4 = PewPewM4()  # pylint: disable=invalid-name
"""Object that is automatically created on import."""
