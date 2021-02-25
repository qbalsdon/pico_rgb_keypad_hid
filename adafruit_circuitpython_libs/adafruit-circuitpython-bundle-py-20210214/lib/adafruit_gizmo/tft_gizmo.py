# SPDX-FileCopyrightText: 2019 Carter Nelson for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_gizmo.tft_gizmo`
================================================================================

Helper for the `TFT Gizmo <https://www.adafruit.com/product/4367>`_.


* Author(s): Carter Nelson, Melissa LeBlanc-Williams
"""

__version__ = "1.2.4"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_Gizmo.git"

import board
import displayio
from adafruit_st7789 import ST7789

# pylint: disable=invalid-name, too-few-public-methods
class TFT_Gizmo(ST7789):
    """Class representing a TFT Gizmo."""

    def __init__(
        self, *, spi=None, cs=board.RX, dc=board.TX, backlight=board.A3, rotation=180
    ):
        displayio.release_displays()
        if spi is None:
            import busio  # pylint: disable=import-outside-toplevel

            spi = busio.SPI(board.SCL, MOSI=board.SDA)
        self._display_bus = displayio.FourWire(spi, command=dc, chip_select=cs)
        super().__init__(
            self._display_bus,
            width=240,
            height=240,
            rowstart=80,
            backlight_pin=backlight,
            rotation=rotation,
        )
