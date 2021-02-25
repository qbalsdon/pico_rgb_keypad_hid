# SPDX-FileCopyrightText: 2020 Foamyguy for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_featherwing.keyboard_featherwing`
====================================================

Helper for using the `Keyboard Featherwing`
<https://www.tindie.com/products/arturo182/keyboard-featherwing-qwerty-keyboard-26-lcd/>`_.

* Author(s): Foamyguy

Requires:
* adafruit_ili9341
* adafruit_stmpe610
"""

__version__ = "1.13.3"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_FeatherWing.git"

import board
import digitalio
import displayio
import adafruit_ili9341
from adafruit_stmpe610 import Adafruit_STMPE610_SPI
import sdcardio
import storage
from bbq10keyboard import BBQ10Keyboard
import neopixel


# pylint: disable-msg=too-few-public-methods
# pylint: disable-msg=too-many-arguments
class KeyboardFeatherwing:
    """Class representing a `Keyboard Featherwing`
    <https://www.tindie.com/products/arturo182/keyboard-featherwing-qwerty-keyboard-26-lcd/>`_.

    """

    def __init__(
        self,
        spi=None,
        cs=None,
        dc=None,
        i2c=None,
        ts_cs=None,
        sd_cs=None,
        neopixel_pin=None,
    ):
        displayio.release_displays()
        if spi is None:
            spi = board.SPI()
        if cs is None:
            cs = board.D9
        if dc is None:
            dc = board.D10
        if i2c is None:
            i2c = board.I2C()
        if ts_cs is None:
            ts_cs = board.D6
        if sd_cs is None:
            sd_cs = board.D5
        if neopixel_pin is None:
            neopixel_pin = board.D11

        self.touchscreen = Adafruit_STMPE610_SPI(spi, digitalio.DigitalInOut(ts_cs))

        display_bus = displayio.FourWire(spi, command=dc, chip_select=cs)
        self.display = adafruit_ili9341.ILI9341(display_bus, width=320, height=240)
        self.neopixel = neopixel.NeoPixel(neopixel_pin, 1)
        self.keyboard = BBQ10Keyboard(i2c)
        self._sdcard = None
        try:
            self._sdcard = sdcardio.SDCard(spi, sd_cs)
            vfs = storage.VfsFat(self._sdcard)
            storage.mount(vfs, "/sd")
        except OSError as error:
            print("No SD card found:", error)
