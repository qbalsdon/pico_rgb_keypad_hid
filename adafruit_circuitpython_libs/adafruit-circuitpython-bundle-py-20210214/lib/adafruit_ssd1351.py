# SPDX-FileCopyrightText: 2019 Melissa LeBlanc-Williams for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_ssd1351`
================================================================================

displayio Driver for SSD1351 Displays


* Author(s): Melissa LeBlanc-Williams

Implementation Notes
--------------------

**Hardware:**

* OLED Breakout Board - 16-bit Color 1.5" w/microSD holder:
  https://www.adafruit.com/product/1431
* OLED Breakout Board - 16-bit Color 1.27" w/microSD holder:
  https://www.adafruit.com/product/1673

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""

import displayio

__version__ = "1.2.4"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_SSD1351.git"

_INIT_SEQUENCE = (
    b"\xFD\x01\x12"  # COMMAND_LOCK Unlock IC MCU
    b"\xFD\x01\xB1"  # COMMAND_LOCK
    b"\xAE\x00"  # DISPLAY_OFF
    b"\xB2\x03\xA4\x00\x00"  # DISPLAY_ENHANCEMENT
    b"\xB3\x01\xF0"  # CLOCK_DIV
    b"\xCA\x01\x7F"  # MUX_RATIO
    b"\xA2\x01\x00"  # DISPLAY_OFFSET
    b"\xB5\x01\x00"  # SET_GPIO
    b"\xAB\x01\x01"  # FUNCTION_SELECT
    b"\xB1\x01\x32"  # PRECHARGE
    b"\xBE\x01\x05"  # VCOMH
    b"\xA6\x00"  # NORMAL_DISPLAY
    b"\xC1\x03\xC8\x80\xC8"  # CONTRAST_ABC (RGB)
    b"\xC7\x01\x0F"  # CONTRAST_MASTER
    b"\xB4\x03\xA0\xB5\x55"  # SET_VSL Set segment low volt
    b"\xB6\x01\x01"  # PRECHARGE2
    b"\xA0\x01\x26"  # Set Color Mode
    b"\xAF\x00"  # DISPLAY_ON
)

# pylint: disable=too-few-public-methods
class SSD1351(displayio.Display):
    """SSD1351 driver"""

    def __init__(self, bus, **kwargs):
        super().__init__(
            bus,
            _INIT_SEQUENCE,
            **kwargs,
            set_column_command=0x15,
            set_row_command=0x75,
            write_ram_command=0x5C,
            single_byte_bounds=True,
        )
