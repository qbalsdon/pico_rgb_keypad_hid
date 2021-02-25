# SPDX-FileCopyrightText: 2019 Scott Shawcroft for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_ssd1327`
================================================================================

DisplayIO drivers for grayscale OLEDs driven by SSD1327


* Author(s): Scott Shawcroft

Implementation Notes
--------------------

**Hardware:**

* 128x128, General 1.5inch OLED display Module:
  https://www.waveshare.com/1.5inch-oled-module.htm

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""

import displayio

__version__ = "1.2.1"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_SSD1327.git"

_INIT_SEQUENCE = (
    b"\xAE\x00"  # DISPLAY_OFF
    b"\x81\x01\x80"  # set contrast control
    b"\xa0\x01\x53"  # remap memory, odd even columns, com flip and column swap
    b"\xa1\x01\x00"  # Display start line is 0
    b"\xa2\x01\x00"  # Display offset is 0
    b"\xa4\x00"  # Normal display
    b"\xa8\x01\x3f"  # Mux ratio is 1/64
    b"\xb1\x01\x11"  # Set phase length
    b"\xb8\x0f\x00\x01\x02\x03\x04\x05\x06\x07\x08\x10\x18\x20\x2f\x38\x3f"  # Set graytable
    b"\xb3\x01\x00"  # Set dclk to 100hz
    b"\xab\x01\x01"  # enable internal regulator
    b"\xb6\x01\x04"  # Set second pre-charge period
    b"\xbe\x01\x0f"  # Set vcom voltage
    b"\xbc\x01\x08"  # Set pre-charge voltage
    b"\xd5\x01\x62"  # function selection B
    b"\xfd\x01\x12"  # command unlock
    b"\xAF\x00"  # DISPLAY_ON
)

# pylint: disable=too-few-public-methods
class SSD1327(displayio.Display):
    """SSD1327 driver"""

    def __init__(self, bus, **kwargs):
        # Patch the init sequence for 32 pixel high displays.
        init_sequence = bytearray(_INIT_SEQUENCE)
        height = kwargs["height"]
        if "rotation" in kwargs and kwargs["rotation"] % 180 != 0:
            height = kwargs["width"]
        init_sequence[18] = height - 1  # patch mux ratio
        super().__init__(
            bus,
            init_sequence,
            **kwargs,
            color_depth=4,
            grayscale=True,
            set_column_command=0x15,
            set_row_command=0x75,
            data_as_commands=True,
            single_byte_bounds=True,
        )
