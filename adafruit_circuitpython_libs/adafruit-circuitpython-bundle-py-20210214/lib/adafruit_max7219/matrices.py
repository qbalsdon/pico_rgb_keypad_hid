# SPDX-FileCopyrightText: 2017 Dan Halbert for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_max7219.matrices.Matrix8x8`
====================================================
"""
from micropython import const
from adafruit_max7219 import max7219

__version__ = "1.3.3"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_MAX7219.git"

_DECODEMODE = const(9)
_SCANLIMIT = const(11)
_SHUTDOWN = const(12)
_DISPLAYTEST = const(15)


class Matrix8x8(max7219.MAX7219):
    """
    Driver for a 8x8 LED matrix based on the MAX7219 chip.

    :param object spi: an spi busio or spi bitbangio object
    :param ~digitalio.DigitalInOut cs: digital in/out to use as chip select signal
    """

    def __init__(self, spi, cs):
        super().__init__(8, 8, spi, cs)

    def init_display(self):
        for cmd, data in (
            (_SHUTDOWN, 0),
            (_DISPLAYTEST, 0),
            (_SCANLIMIT, 7),
            (_DECODEMODE, 0),
            (_SHUTDOWN, 1),
        ):
            self.write_cmd(cmd, data)

        self.fill(0)
        self.show()

    def text(self, strg, xpos, ypos, bit_value=1):
        """
        Draw text in the 8x8 matrix.

        :param int xpos: x position of LED in matrix
        :param int ypos: y position of LED in matrix
        :param string strg: string to place in to display
        :param bit_value: > 1 sets the text, otherwise resets
        """
        self.framebuf.text(strg, xpos, ypos, bit_value)

    def clear_all(self):
        """
        Clears all matrix leds.
        """
        self.fill(0)
