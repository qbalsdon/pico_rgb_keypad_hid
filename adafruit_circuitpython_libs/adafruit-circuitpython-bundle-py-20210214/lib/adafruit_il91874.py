# SPDX-FileCopyrightText: 2019 Scott Shawcroft for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_il91874`
================================================================================

CircuitPython `displayio` driver for IL91874-based ePaper displays


* Author(s): Scott Shawcroft

Implementation Notes
--------------------

**Hardware:**

* `Adafruit 2.7" Tri-Color ePaper Display Shield <https://www.adafruit.com/product/4229>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware (version 5+) for the supported boards:
  https://github.com/adafruit/circuitpython/releases

# * Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
# * Adafruit's Register library: https://github.com/adafruit/Adafruit_CircuitPython_Register
"""

import displayio

__version__ = "1.1.3"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_IL91874.git"

_START_SEQUENCE = (
    b"\x04\x00"  # Power on
    b"\x00\x01\xaf"  # panel setting
    b"\x30\x01\x3a"  # PLL
    b"\x01\x05\x03\x00\x2b\x2b\x09"  # power setting
    b"\x06\x03\x07\x07\x17"  # booster soft start
    b"\xf8\x02\x60\xa5"  # mystery command in example code
    b"\xf8\x02\x89\xa5"  # mystery command in example code
    b"\xf8\x02\x90\x00"  # mystery command in example code
    b"\xf8\x02\x93\xa2"  # mystery command in example code
    b"\xf8\x02\x73\x41"  # mystery command in example code
    b"\x82\x01\x12"  # VCM DC
    b"\x50\x01\x87"  # CDI setting
    # Look Up Tables
    # LUT1
    b"\x20\x2c\x00\x00\x00\x1a\x1a\x00\x00\x01\x00\x0a\x0a\x00\x00\x08\x00\x0e\x01\x0e\x01\x10\x00"
    b"\x0a\x0a\x00\x00\x08\x00\x04\x10\x00\x00\x05\x00\x03\x0e\x00\x00\x0a\x00\x23\x00\x00\x00\x01"
    # LUTWW
    b"\x21\x2a\x90\x1a\x1a\x00\x00\x01\x40\x0a\x0a\x00\x00\x08\x84\x0e\x01\x0e\x01\x10\x80\x0a\x0a"
    b"\x00\x00\x08\x00\x04\x10\x00\x00\x05\x00\x03\x0e\x00\x00\x0a\x00\x23\x00\x00\x00\x01"
    # LUTBW
    b"\x22\x2a\xa0\x1a\x1a\x00\x00\x01\x00\x0a\x0a\x00\x00\x08\x84\x0e\x01\x0e\x01\x10\x90\x0a\x0a"
    b"\x00\x00\x08\xb0\x04\x10\x00\x00\x05\xb0\x03\x0e\x00\x00\x0a\xc0\x23\x00\x00\x00\x01"
    # LUTWB
    b"\x23\x2a\x90\x1a\x1a\x00\x00\x01\x40\x0a\x0a\x00\x00\x08\x84\x0e\x01\x0e\x01\x10\x80\x0a\x0a"
    b"\x00\x00\x08\x00\x04\x10\x00\x00\x05\x00\x03\x0e\x00\x00\x0a\x00\x23\x00\x00\x00\x01"
    # LUTBB
    b"\x24\x2a\x90\x1a\x1a\x00\x00\x01\x20\x0a\x0a\x00\x00\x08\x84\x0e\x01\x0e\x01\x10\x10\x0a\x0a"
    b"\x00\x00\x08\x00\x04\x10\x00\x00\x05\x00\x03\x0e\x00\x00\x0a\x00\x23\x00\x00\x00\x01"
    b"\x61\x04\x00\x00\x00\x00"  # Resolution
    b"\x16\x80\x00"  # PDRF
)

_STOP_SEQUENCE = b"\x02\x01\x17"  # Power off

# pylint: disable=too-few-public-methods
class IL91874(displayio.EPaperDisplay):
    """IL91874 display driver"""

    def __init__(self, bus, **kwargs):
        start_sequence = bytearray(_START_SEQUENCE)

        width = kwargs["width"]
        height = kwargs["height"]
        if "rotation" in kwargs and kwargs["rotation"] % 180 != 0:
            width, height = height, width
        start_sequence[-7] = (width >> 8) & 0xFF
        start_sequence[-6] = width & 0xFF
        start_sequence[-5] = (height >> 8) & 0xFF
        start_sequence[-4] = height & 0xFF

        super().__init__(
            bus,
            start_sequence,
            _STOP_SEQUENCE,
            **kwargs,
            ram_width=320,
            ram_height=300,
            busy_state=False,
            write_black_ram_command=0x10,
            black_bits_inverted=True,
            write_color_ram_command=0x13,
            refresh_display_command=0x12,
            always_toggle_chip_select=True,
        )
