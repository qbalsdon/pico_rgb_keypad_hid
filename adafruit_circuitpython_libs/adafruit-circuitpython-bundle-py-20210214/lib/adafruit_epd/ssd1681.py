# SPDX-FileCopyrightText: 2018 Dean Miller for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_epd.ssd1681` - Adafruit SSD1681 - ePaper display driver
====================================================================================
CircuitPython driver for Adafruit SSD1681 display breakouts
* Author(s): Dean Miller, Ladyada
"""

import time
from micropython import const
import adafruit_framebuf
from adafruit_epd.epd import Adafruit_EPD

__version__ = "2.7.2"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_EPD.git"

_SSD1681_DRIVER_CONTROL = const(0x01)
_SSD1681_GATE_VOLTAGE = const(0x03)
_SSD1681_SOURCE_VOLTAGE = const(0x04)
_SSD1681_INIT_SETTING = const(0x08)
_SSD1681_INIT_WRITE_REG = const(0x09)
_SSD1681_INIT_READ_REG = const(0x0A)
_SSD1681_BOOSTER_SOFT_START = const(0x0C)
_SSD1681_DEEP_SLEEP = const(0x10)
_SSD1681_DATA_MODE = const(0x11)
_SSD1681_SW_RESET = const(0x12)
_SSD1681_HV_DETECT = const(0x14)
_SSD1681_VCI_DETECT = const(0x15)
_SSD1681_TEMP_CONTROL = const(0x18)
_SSD1681_TEMP_WRITE = const(0x1A)
_SSD1681_TEMP_READ = const(0x1B)
_SSD1681_EXTTEMP_WRITE = const(0x1C)
_SSD1681_MASTER_ACTIVATE = const(0x20)
_SSD1681_DISP_CTRL1 = const(0x21)
_SSD1681_DISP_CTRL2 = const(0x22)
_SSD1681_WRITE_BWRAM = const(0x24)
_SSD1681_WRITE_REDRAM = const(0x26)
_SSD1681_READ_RAM = const(0x27)
_SSD1681_VCOM_SENSE = const(0x28)
_SSD1681_VCOM_DURATION = const(0x29)
_SSD1681_WRITE_VCOM_OTP = const(0x2A)
_SSD1681_WRITE_VCOM_CTRL = const(0x2B)
_SSD1681_WRITE_VCOM_REG = const(0x2C)
_SSD1681_READ_OTP = const(0x2D)
_SSD1681_READ_USERID = const(0x2E)
_SSD1681_READ_STATUS = const(0x2F)
_SSD1681_WRITE_WS_OTP = const(0x30)
_SSD1681_LOAD_WS_OTP = const(0x31)
_SSD1681_WRITE_LUT = const(0x32)
_SSD1681_CRC_CALC = const(0x34)
_SSD1681_CRC_READ = const(0x35)
_SSD1681_PROG_OTP = const(0x36)
_SSD1681_WRITE_DISPLAY_OPT = const(0x37)
_SSD1681_WRITE_USERID = const(0x38)
_SSD1681_OTP_PROGMODE = const(0x39)
_SSD1681_WRITE_BORDER = const(0x3C)
_SSD1681_END_OPTION = const(0x3F)
_SSD1681_SET_RAMXPOS = const(0x44)
_SSD1681_SET_RAMYPOS = const(0x45)
_SSD1681_AUTOWRITE_RED = const(0x46)
_SSD1681_AUTOWRITE_BW = const(0x47)
_SSD1681_SET_RAMXCOUNT = const(0x4E)
_SSD1681_SET_RAMYCOUNT = const(0x4F)
_SSD1681_NOP = const(0xFF)

_LUT_DATA = b'\x02\x02\x01\x11\x12\x12""fiiYX\x99\x99\x88\x00\x00\x00\x00\xf8\xb4\x13Q5QQ\x19\x01\x00'  # pylint: disable=line-too-long


class Adafruit_SSD1681(Adafruit_EPD):
    """driver class for Adafruit SSD1681 ePaper display breakouts"""

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
        self.command(_SSD1681_SW_RESET)
        self.busy_wait()
        # driver output control
        self.command(
            _SSD1681_DRIVER_CONTROL,
            bytearray([self._width - 1, (self._width - 1) >> 8, 0x00]),
        )
        # data entry mode
        self.command(_SSD1681_DATA_MODE, bytearray([0x03]))
        # Set ram X start/end postion
        self.command(_SSD1681_SET_RAMXPOS, bytearray([0x00, self._height // 8 - 1]))
        # Set ram Y start/end postion
        self.command(
            _SSD1681_SET_RAMYPOS,
            bytearray([0, 0, self._height - 1, (self._height - 1) >> 8]),
        )
        # Set border waveform
        self.command(_SSD1681_WRITE_BORDER, bytearray([0x05]))
        # Set temperature control
        self.command(_SSD1681_TEMP_CONTROL, bytearray([0x80]))

        self.busy_wait()

    def power_down(self):
        """Power down the display - required when not actively displaying!"""
        self.command(_SSD1681_DEEP_SLEEP, bytearray([0x01]))
        time.sleep(0.1)

    def update(self):
        """Update the display from internal memory"""
        self.command(_SSD1681_DISP_CTRL2, bytearray([0xF7]))
        self.command(_SSD1681_MASTER_ACTIVATE)
        self.busy_wait()
        if not self._busy:
            time.sleep(3)  # wait 3 seconds

    def write_ram(self, index):
        """Send the one byte command for starting the RAM write process. Returns
        the byte read at the same time over SPI. index is the RAM buffer, can be
        0 or 1 for tri-color displays."""
        if index == 0:
            return self.command(_SSD1681_WRITE_BWRAM, end=False)
        raise RuntimeError("RAM index must be 0")

    def set_ram_address(self, x, y):  # pylint: disable=unused-argument, no-self-use
        """Set the RAM address location, not used on this chipset but required by
        the superclass"""
        # Set RAM X address counter
        self.command(_SSD1681_SET_RAMXCOUNT, bytearray([x]))
        # Set RAM Y address counter
        self.command(_SSD1681_SET_RAMYCOUNT, bytearray([y >> 8, y]))
