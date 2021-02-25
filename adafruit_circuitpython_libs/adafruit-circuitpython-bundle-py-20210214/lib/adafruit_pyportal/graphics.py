# SPDX-FileCopyrightText: 2020 Melissa LeBlanc-Williams, written for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense
"""
`adafruit_pyportal.graphics`
================================================================================

CircuitPython driver for Adafruit PyPortal.

* Author(s): Limor Fried, Kevin J. Walters, Melissa LeBlanc-Williams

Implementation Notes
--------------------

**Hardware:**

* `Adafruit PyPortal <https://www.adafruit.com/product/4116>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""

import board
from adafruit_portalbase.graphics import GraphicsBase

__version__ = "5.1.3"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_PyPortal.git"


class Graphics(GraphicsBase):
    """Graphics Helper Class for the PyPortal Library

    :param default_bg: The path to your default background image file or a hex color.
                       Defaults to 0x000000.
    :param debug: Turn on debug print outs. Defaults to False.

    """

    # pylint: disable=too-few-public-methods
    def __init__(self, *, default_bg=None, debug=False):

        super().__init__(board.DISPLAY, default_bg=default_bg, debug=debug)
        # Tracks whether we've hidden the background when we showed the QR code.
        self._qr_only = False

    # pylint: disable=arguments-differ
    def qrcode(self, qr_data, *, qr_size=1, x=0, y=0, hide_background=False):
        """Display a QR code

        :param qr_data: The data for the QR code.
        :param int qr_size: The scale of the QR code.
        :param x: The x position of upper left corner of the QR code on the display.
        :param y: The y position of upper left corner of the QR code on the display.

        """
        super().qrcode(
            qr_data,
            qr_size=qr_size,
            x=x,
            y=y,
        )
        if hide_background:
            self.display.show(self._qr_group)
        self._qr_only = hide_background

    # pylint: enable=arguments-differ

    def hide_QR(self):  # pylint: disable=invalid-name
        """Clear any QR codes that are currently on the screen"""

        if self._qr_only:
            self.display.show(self.splash)
        else:
            try:
                self._qr_group.pop()
            except (IndexError, AttributeError):  # later test if empty
                pass
