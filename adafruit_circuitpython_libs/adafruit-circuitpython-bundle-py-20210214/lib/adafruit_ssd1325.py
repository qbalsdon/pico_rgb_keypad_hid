# SPDX-FileCopyrightText: 2019 Scott Shawcroft for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_ssd1325`
================================================================================

DisplayIO driver for grayscale OLEDs drive by SSD1325


* Author(s): Scott Shawcroft

Implementation Notes
--------------------

**Hardware:**

* `Adafruit Monochrome 2.7" 128x64 OLED Graphic Display <https://www.adafruit.com/product/2674>`_

**Software and Dependencies:**

* Adafruit CircuitPython 5+ firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""

import displayio

__version__ = "1.2.3"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_SSD1325.git"

_INIT_SEQUENCE = (
    b"\xAE\x00"  # DISPLAY_OFF
    b"\xb3\x01\xa1"  # Set clock
    b"\xa8\x01\x3f"  # Mux ratio is 1/64
    b"\xa1\x01\x00"  # Display start line is 0
    b"\xa2\x01\x4c"  # Display offset is 0
    b"\xad\x01\x02"  # set master config
    b"\xa0\x01\x50"  # remap memory
    b"\x86\x00"  # set current
    b"\xb8\x08\x01\x11\x22\x32\x43\x54\x65\x76"  # Set graytable
    b"\x81\x01\x7f"  # full contrast
    b"\xb2\x01\x51"  # Set row period
    b"\xb1\x01\x55"  # Set phase length
    b"\xb4\x01\x02"  # Set pre-charge comp
    b"\xb0\x01\x28"  # Set pre-charge comp enable
    b"\xbc\x01\x3f"  # Set pre-charge voltage
    b"\xbe\x01\x1c"  # Set vcom voltage
    b"\xbf\x01\x0f"  # set Low Voltage Level of SEG Pin
    b"\xa4\x00"  # Normal display
    b"\xaf\x00"  # DISPLAY_ON
)

# pylint: disable=too-few-public-methods
class SSD1325(displayio.Display):
    """SSD1325 driver"""

    def __init__(self, bus, **kwargs):
        # Patch the init sequence for 32 pixel high displays.
        init_sequence = bytearray(_INIT_SEQUENCE)
        height = kwargs["height"]
        if "rotation" in kwargs and kwargs["rotation"] % 180 != 0:
            height = kwargs["width"]
        init_sequence[7] = height - 1  # patch mux ratio
        super().__init__(
            bus,
            _INIT_SEQUENCE,
            **kwargs,
            color_depth=4,
            grayscale=True,
            set_column_command=0x15,
            set_row_command=0x75,
            set_vertical_scroll=0xD3,
            data_as_commands=True,
            brightness_command=0x81,
            single_byte_bounds=True,
        )
