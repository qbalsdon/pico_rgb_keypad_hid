# SPDX-FileCopyrightText: 2018 Dean Miller for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_epd.ssd1608` - Adafruit SSD1608 - ePaper display driver
====================================================================================
CircuitPython driver for Adafruit SSD1608 display breakouts
* Author(s): Dean Miller, Ladyada
"""

import time
from micropython import const
import adafruit_framebuf
from adafruit_epd.epd import Adafruit_EPD

__version__ = "2.7.2"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_EPD.git"

_SSD1608_DRIVER_CONTROL = const(0x01)
_SSD1608_GATE_VOLTAGE = const(0x03)
_SSD1608_SOURCE_VOLTAGE = const(0x04)
_SSD1608_DISPLAY_CONTROL = const(0x07)
_SSD1608_NON_OVERLAP = const(0x0B)
_SSD1608_BOOSTER_SOFT_START = const(0x0C)
_SSD1608_GATE_SCAN_START = const(0x0F)
_SSD1608_DEEP_SLEEP = const(0x10)
_SSD1608_DATA_MODE = const(0x11)
_SSD1608_SW_RESET = const(0x12)
_SSD1608_TEMP_WRITE = const(0x1A)
_SSD1608_TEMP_READ = const(0x1B)
_SSD1608_TEMP_CONTROL = const(0x1C)
_SSD1608_TEMP_LOAD = const(0x1D)
_SSD1608_MASTER_ACTIVATE = const(0x20)
_SSD1608_DISP_CTRL1 = const(0x21)
_SSD1608_DISP_CTRL2 = const(0x22)
_SSD1608_WRITE_RAM = const(0x24)
_SSD1608_READ_RAM = const(0x25)
_SSD1608_VCOM_SENSE = const(0x28)
_SSD1608_VCOM_DURATION = const(0x29)
_SSD1608_WRITE_VCOM = const(0x2C)
_SSD1608_READ_OTP = const(0x2D)
_SSD1608_WRITE_LUT = const(0x32)
_SSD1608_WRITE_DUMMY = const(0x3A)
_SSD1608_WRITE_GATELINE = const(0x3B)
_SSD1608_WRITE_BORDER = const(0x3C)
_SSD1608_SET_RAMXPOS = const(0x44)
_SSD1608_SET_RAMYPOS = const(0x45)
_SSD1608_SET_RAMXCOUNT = const(0x4E)
_SSD1608_SET_RAMYCOUNT = const(0x4F)
_SSD1608_NOP = const(0xFF)
_LUT_DATA = b'\x02\x02\x01\x11\x12\x12""fiiYX\x99\x99\x88\x00\x00\x00\x00\xf8\xb4\x13Q5QQ\x19\x01\x00'  # pylint: disable=line-too-long


class Adafruit_SSD1608(Adafruit_EPD):
    """driver class for Adafruit SSD1608 ePaper display breakouts"""

    # pylint: disable=too-many-arguments
    def __init__(
        self, width, height, spi, *, cs_pin, dc_pin, sramcs_pin, rst_pin, busy_pin
    ):
        super().__init__(
            width, height, spi, cs_pin, dc_pin, sramcs_pin, rst_pin, busy_pin
        )

        if height % 8 != 0:
            height += 8 - height % 8
            self._height = height

        self._buffer1_size = int(width * height / 8)

        if sramcs_pin:
            self._buffer1 = self.sram.get_view(0)
        else:
            self._buffer1 = bytearray((width * height) // 8)
        self._framebuf1 = adafruit_framebuf.FrameBuffer(
            self._buffer1, width, height, buf_format=adafruit_framebuf.MHMSB
        )
        self.set_black_buffer(0, True)
        self.set_color_buffer(0, True)
        # pylint: enable=too-many-arguments

    def begin(self, reset=True):
        """Begin communication with the display and set basic settings"""
        if reset:
            self.hardware_reset()
        self.power_down()

    def busy_wait(self):
        """Wait for display to be done with current task, either by polling the
        busy pin, or pausing"""
        if self._busy:
            while self._busy.value:
                time.sleep(0.01)
        else:
            time.sleep(0.5)

    def power_up(self):
        """Power up the display in preparation for writing RAM and updating"""
        self.hardware_reset()
        self.busy_wait()
        self.command(_SSD1608_SW_RESET)
        self.busy_wait()
        # driver output control
        self.command(
            _SSD1608_DRIVER_CONTROL,
            bytearray([self._width - 1, (self._width - 1) >> 8, 0x00]),
        )
        # Set dummy line period
        self.command(_SSD1608_WRITE_DUMMY, bytearray([0x1B]))
        # Set gate line width
        self.command(_SSD1608_WRITE_GATELINE, bytearray([0x0B]))
        # Data entry sequence
        self.command(_SSD1608_DATA_MODE, bytearray([0x03]))
        # Set ram X start/end postion
        self.command(_SSD1608_SET_RAMXPOS, bytearray([0x00, self._height // 8 - 1]))
        # Set ram Y start/end postion
        self.command(
            _SSD1608_SET_RAMYPOS,
            bytearray([0, 0, self._height - 1, (self._height - 1) >> 8]),
        )
        # Vcom Voltage
        self.command(_SSD1608_WRITE_VCOM, bytearray([0x70]))
        # LUT
        self.command(_SSD1608_WRITE_LUT, _LUT_DATA)
        self.busy_wait()

    def power_down(self):
        """Power down the display - required when not actively displaying!"""
        self.command(_SSD1608_DEEP_SLEEP, bytearray([0x01]))
        time.sleep(0.1)

    def update(self):
        """Update the display from internal memory"""
        self.command(_SSD1608_DISP_CTRL2, bytearray([0xC7]))
        self.command(_SSD1608_MASTER_ACTIVATE)
        self.busy_wait()
        if not self._busy:
            time.sleep(3)  # wait 3 seconds

    def write_ram(self, index):
        """Send the one byte command for starting the RAM write process. Returns
        the byte read at the same time over SPI. index is the RAM buffer, can be
        0 or 1 for tri-color displays."""
        if index == 0:
            return self.command(_SSD1608_WRITE_RAM, end=False)
        raise RuntimeError("RAM index must be 0")

    def set_ram_address(self, x, y):  # pylint: disable=unused-argument, no-self-use
        """Set the RAM address location, not used on this chipset but required by
        the superclass"""
        # Set RAM X address counter
        self.command(_SSD1608_SET_RAMXCOUNT, bytearray([x]))
        # Set RAM Y address counter
        self.command(_SSD1608_SET_RAMYCOUNT, bytearray([y >> 8, y]))
