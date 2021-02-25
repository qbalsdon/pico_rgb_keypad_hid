# SPDX-FileCopyrightText: 2019 Melissa LeBlanc-Williams for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_gizmo.tft_gizmo`
================================================================================

Helper for the `Tri-Color E-Ink Gizmo <https://www.adafruit.com/product/4428>`_.


* Author(s): Melissa LeBlanc-Williams
"""

__version__ = "1.2.4"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_Gizmo.git"

from time import sleep
import board
import displayio
from adafruit_il0373 import IL0373

# pylint: disable=invalid-name, too-few-public-methods
class EInk_Gizmo(IL0373):
    """Class representing a EInk Gizmo."""

    def __init__(self, *, spi=None, cs=None, dc=None, reset=None, busy=None):
        displayio.release_displays()
        if spi is None:
            import busio  # pylint: disable=import-outside-toplevel

            spi = busio.SPI(board.SCL, MOSI=board.SDA)
        if cs is None:
            cs = board.RX
        if dc is None:
            dc = board.TX
        if reset is None:
            reset = board.A3
        self._display_bus = displayio.FourWire(
            spi, command=dc, chip_select=cs, reset=reset, baudrate=1000000
        )
        sleep(1)
        super().__init__(
            self._display_bus,
            width=152,
            height=152,
            busy_pin=busy,
            rotation=180,
            highlight_color=0xFF0000,
        )
