# SPDX-FileCopyrightText: 2019 Melissa LeBlanc-Williams for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_hx8357`
================================================================================

displayio driver for HX8357 Displays such as the 3.5-inch TFT FeatherWing and Breakout

* Author(s): Melissa LeBlanc-Williams

Implementation Notes
--------------------

**Hardware:**

* 3.5" PiTFT Plus 480x320 3.5" TFT+Touchscreen for Raspberry Pi:
  <https://www.adafruit.com/product/2441>
* 3.5" TFT 320x480 + Touchscreen Breakout Board w/MicroSD Socket:
  <https://www.adafruit.com/product/2050>
* Adafruit TFT FeatherWing - 3.5" 480x320 Touchscreen for Feathers:
  <https://www.adafruit.com/product/3651>

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases
"""

# imports

import displayio

__version__ = "1.2.5"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_HX8357.git"

_INIT_SEQUENCE = (
    b"\x01\x80\x64"  # _SWRESET and Delay 100ms
    b"\xB9\x83\xFF\x83\x57\xFF"  # _SETC and delay 500ms
    b"\xB3\x04\x80\x00\x06\x06"  # _SETRGB 0x80 enables SDO pin (0x00 disables)
    b"\xB6\x01\x25"  # _SETCOM -1.52V
    b"\xB0\x01\x68"  # _SETOSC Normal mode 70Hz, Idle mode 55 Hz
    b"\xCC\x01\x05"  # _SETPANEL BGR, Gate direction swapped
    b"\xB1\x06\x00\x15\x1C\x1C\x83\xAA"  # _SETPWR1 Not deep standby BT VSPR VSNR AP
    b"\xC0\x06\x50\x50\x01\x3C\x1E\x08"  # _SETSTBA OPON normal OPON idle STBA GEN
    b"\xB4\x07\x02\x40\x00\x2A\x2A\x0D\x78"  # _SETCYC NW 0x02 RTN DIV DUM DUM GDON GDOFF
    b"\xE0\x22\x02\x0A\x11\x1d\x23\x35\x41\x4b\x4b\x42\x3A\x27\x1B\x08\x09\x03\x02\x0A"
    b"\x11\x1d\x23\x35\x41\x4b\x4b\x42\x3A\x27\x1B\x08\x09\x03\x00\x01"  # _SETGAMMA
    b"\x3A\x01\x55"  # _COLMOD 16 bit
    b"\x36\x01\xC0"  # _MADCTL
    b"\x35\x01\x00"  # _TEON TW off
    b"\x44\x02\x00\x02"  # _TEARLINE
    b"\x11\x80\x96"  # _SLPOUT and delay 150 ms
    b"\x36\x01\xA0"
    b"\x29\x80\x32"  # _DISPON and delay 50 ms
)

# pylint: disable=too-few-public-methods
class HX8357(displayio.Display):
    """HX8357D driver"""

    def __init__(self, bus, **kwargs):
        super().__init__(bus, _INIT_SEQUENCE, **kwargs)
