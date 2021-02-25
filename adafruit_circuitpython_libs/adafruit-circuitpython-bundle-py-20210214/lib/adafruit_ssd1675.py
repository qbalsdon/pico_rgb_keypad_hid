# SPDX-FileCopyrightText: 2019 Scott Shawcroft for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_ssd1675`
================================================================================

CircuitPython `displayio` drivers for SSD1675-based ePaper displays


* Author(s): Scott Shawcroft

Implementation Notes
--------------------

**Hardware:**

* `Adafruit 2.13" Monochrome ePaper Display Breakout <https://www.adafruit.com/product/4197>`_
* `Adafruit 2.13" Black and White FeatherWing <https://www.adafruit.com/product/4195>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware (version 5+) for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""

import displayio

__version__ = "1.1.3"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_SSD1675.git"

_START_SEQUENCE = (
    b"\x12\x80\x02"  # Software reset, 2ms delay
    b"\x74\x01\x54"  # set analog block control
    b"\x7e\x01\x3b"  # set digital block control
    b"\x01\x03\xfa\x01\x00"  # driver output control
    b"\x11\x01\x03"  # Data entry sequence
    b"\x3c\x01\x03"  # Border color
    b"\x2c\x01\x70"  # Vcom Voltage
    b"\x03\x01\x15"  # Set gate voltage
    b"\x04\x03\x41\xa8\x32"  # Set source voltage
    b"\x3a\x01\x30"  # Set dummy line period
    b"\x3b\x01\x0a"  # Set gate line width
    b"\x32\x46\x80\x60\x40\x00\x00\x00\x00\x10\x60\x20\x00\x00\x00\x00\x80\x60\x40\x00\x00\x00\x00"
    b"\x10\x60\x20\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\x03\x00\x00\x02\x09\x09\x00\x00"
    b"\x02\x03\x03\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00"  # LUT
)

_STOP_SEQUENCE = b"\x10\x01\x01"  # Enter deep sleep

# pylint: disable=too-few-public-methods
class SSD1675(displayio.EPaperDisplay):
    """SSD1675 driver"""

    def __init__(self, bus, **kwargs):
        stop_sequence = _STOP_SEQUENCE
        try:
            bus.reset()
        except RuntimeError:
            stop_sequence = b""
        super().__init__(
            bus,
            _START_SEQUENCE,
            stop_sequence,
            **kwargs,
            ram_width=160,
            ram_height=296,
            set_column_window_command=0x44,
            set_row_window_command=0x45,
            set_current_column_command=0x4E,
            set_current_row_command=0x4F,
            write_black_ram_command=0x24,
            refresh_display_command=0x20,
            refresh_time=2.2,
        )
