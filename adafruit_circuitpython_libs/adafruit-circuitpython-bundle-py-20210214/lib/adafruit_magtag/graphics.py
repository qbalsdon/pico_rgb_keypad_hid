# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2020 Melissa LeBlanc-Williams for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
`adafruit_magtag.graphics`
================================================================================

Helper Library for the Adafruit MagTag.


* Author(s): Melissa LeBlanc-Williams

Implementation Notes
--------------------

**Hardware:**

* `Adafruit MagTag <https://www.adafruit.com/product/4800>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

* Adafruit's PortalBase library: https://github.com/adafruit/Adafruit_CircuitPython_PortalBase

"""

import gc
from time import sleep
import board
from adafruit_portalbase.graphics import GraphicsBase

__version__ = "1.6.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_MagTag.git"


class Graphics(GraphicsBase):
    """Graphics Helper Class for the MagTag Library

    :param default_bg: The path to your default background image file or a hex color.
                       Defaults to 0xFFFFFF.
    :param bool auto_refresh: Automatically refresh the eInk after writing to displayio.
                              Defaults to True.
    :param rotation: Default rotation is landscape (270) but can be 0, 90, 180 for portrait/rotated
    :param debug: Turn on debug print outs. Defaults to False.

    """

    # pylint: disable=too-many-instance-attributes, too-many-locals, too-many-branches, too-many-statements
    def __init__(
        self, *, default_bg=0xFFFFFF, auto_refresh=True, rotation=270, debug=False
    ):
        self._debug = debug
        self.display = board.DISPLAY
        self.display.rotation = rotation
        self.auto_refresh = auto_refresh
        self._qr_group = None

        super().__init__(board.DISPLAY, default_bg=default_bg, debug=debug)

    def set_background(self, file_or_color, position=None):
        """The background image to a bitmap file.

        :param file_or_color: The filename of the chosen background image, or a hex color.
        :param tuple position: Optional x and y coordinates to place the background at.

        """
        super().set_background(file_or_color, position)
        if self.auto_refresh:
            self.display.refresh()
        gc.collect()

    def qrcode(
        self, qr_data, *, qr_size=1, x=0, y=0, qr_color=0x000000
    ):  # pylint: disable=invalid-name
        """Display a QR code on the eInk

        :param qr_data: The data for the QR code.
        :param int qr_size: The scale of the QR code.
        :param x: The x position of upper left corner of the QR code on the display.
        :param y: The y position of upper left corner of the QR code on the display.

        """
        super().qrcode(qr_data, qr_size=qr_size, x=x, y=y, qr_color=qr_color)
        if self.auto_refresh:
            self.display.refresh()
            sleep(5)
