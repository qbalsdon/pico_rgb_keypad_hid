# SPDX-FileCopyrightText: 2020 Kattni Rembor for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_pybadger.pyportal`
================================================================================

Badge-focused CircuitPython helper library for PyPortal.


* Author(s): Kattni Rembor

Implementation Notes
--------------------

**Hardware:**

* `Adafruit PyPortal <https://www.adafruit.com/product/4116>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""
import board
import analogio
import audioio
import neopixel
from adafruit_pybadger.pybadger_base import PyBadgerBase

__version__ = "3.2.2"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_PyBadger.git"


class PyPortal(PyBadgerBase):
    """Class that represents a single PyPortal."""

    _audio_out = audioio.AudioOut
    _neopixel_count = 1

    def __init__(self):
        super().__init__()

        # NeoPixels
        self._neopixels = neopixel.NeoPixel(
            board.NEOPIXEL, self._neopixel_count, brightness=1, pixel_order=neopixel.GRB
        )
        self._light_sensor = analogio.AnalogIn(board.LIGHT)

    @property
    def _unsupported(self):
        """This feature is not supported on PyPortal."""
        raise NotImplementedError("This feature is not supported on PyPortal.")

    # The following is a list of the features available in other PyBadger modules but
    # not available for PyPortal. If called while using a PyPortal, they will result in the
    # NotImplementedError raised in the property above.
    button = _unsupported
    acceleration = _unsupported
    auto_dim_display = _unsupported


pyportal = PyPortal()  # pylint: disable=invalid-name
"""Object that is automatically created on import."""
