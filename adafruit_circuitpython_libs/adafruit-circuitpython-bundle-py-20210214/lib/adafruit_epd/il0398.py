# SPDX-FileCopyrightText: 2018 Dean Miller for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_epd.il0398` - Adafruit IL0398 - ePaper display driver
====================================================================================
CircuitPython driver for Adafruit IL0398 display breakouts
* Author(s): Dean Miller, ladyada
"""

import time
from micropython import const
import adafruit_framebuf
from adafruit_epd.epd import Adafruit_EPD

__version__ = "2.7.2"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_EPD.git"

_IL0398_PANEL_SETTING = const(0x00)
_IL0398_POWER_SETTING = const(0x01)
_IL0398_POWER_OFF = const(0x02)
_IL0398_POWER_OFF_SEQUENCE = const(0x03)
_IL0398_POWER_ON = const(0x04)
_IL0398_POWER_ON_MEASURE = const(0x05)
_IL0398_BOOSTER_SOFT_START = const(0x06)
_IL0398_DEEP_SLEEP = const(0x07)
_IL0398_DTM1 = const(0x10)
_IL0398_DATA_STOP = const(0x11)
_IL0398_DISPLAY_REFRESH = const(0x12)
_IL0398_DTM2 = const(0x13)
_IL0398_PDTM1 = const(0x14)
_IL0398_PDTM2 = const(0x15)
_IL0398_PDRF = const(0x16)
_IL0398_LUT1 = const(0x20)
_IL0398_LUTWW = const(0x21)
_IL0398_LUTBW = const(0x22)
_IL0398_LUTWB = const(0x23)
_IL0398_LUTBB = const(0x24)
_IL0398_PLL = const(0x30)
_IL0398_CDI = const(0x50)
_IL0398_RESOLUTION = const(0x61)
_IL0398_GETSTATUS = const(0x71)
_IL0398_VCM_DC_SETTING = const(0x82)


class Adafruit_IL0398(Adafruit_EPD):
    """driver class for Adafruit IL0373 ePaper display breakouts"""

    # pylint: disable=too-many-arguments
    def __init__(
        self, width, height, spi, *, cs_pin, dc_pin, sramcs_pin, rst_pin, busy_pin
    ):
        super().__init__(
            width, height, spi, cs_pin, dc_pin, sramcs_pin, rst_pin, busy_pin
        )

        self._buffer1_size = int(width * height / 8)
        self._buffer2_size = int(width * height / 8)

        if sramcs_pin:
            self._buffer1 = self.sram.get_view(0)
            self._buffer2 = self.sram.get_view(self._buffer1_size)
        else:
            self._buffer1 = bytearray((width * height) // 8)
            self._buffer2 = bytearray((width * height) // 8)
        # since we have *two* framebuffers - one for red and one for black
        # we dont subclass but manage manually
        self._framebuf1 = adafruit_framebuf.FrameBuffer(
            self._buffer1, width, height, buf_format=adafruit_framebuf.MHMSB
        )
        self._framebuf2 = adafruit_framebuf.FrameBuffer(
            self._buffer2, width, height, buf_format=adafruit_framebuf.MHMSB
        )
        self.set_black_buffer(0, True)
        self.set_color_buffer(1, True)
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
            while not self._busy.value:
                # self.command(_IL0398_GETSTATUS)
                time.sleep(0.01)
        else:
            time.sleep(0.5)

    def power_up(self):
        """Power up the display in preparation for writing RAM and updating"""
        self.hardware_reset()
        self.busy_wait()

        self.command(_IL0398_BOOSTER_SOFT_START, bytearray([0x17, 0x17, 0x17]))
        self.command(_IL0398_POWER_ON)

        self.busy_wait()
        time.sleep(0.2)

        self.command(_IL0398_PANEL_SETTING, bytearray([0x0F]))
        _b0 = (self._width >> 8) & 0xFF
        _b1 = self._width & 0xFF
        _b2 = (self._height >> 8) & 0xFF
        _b3 = self._height & 0xFF
        self.command(_IL0398_RESOLUTION, bytearray([_b0, _b1, _b2, _b3]))
        time.sleep(0.05)

    def power_down(self):
        """Power down the display - required when not actively displaying!"""
        self.command(_IL0398_CDI, bytearray([0xF7]))
        self.command(_IL0398_POWER_OFF)
        self.busy_wait()
        self.command(_IL0398_DEEP_SLEEP, bytearray([0xA5]))

    def update(self):
        """Update the display from internal memory"""
        self.command(_IL0398_DISPLAY_REFRESH)
        time.sleep(0.1)
        self.busy_wait()
        if not self._busy:
            time.sleep(15)  # wait 15 seconds

    def write_ram(self, index):
        """Send the one byte command for starting the RAM write process. Returns
        the byte read at the same time over SPI. index is the RAM buffer, can be
        0 or 1 for tri-color displays."""
        if index == 0:
            return self.command(_IL0398_DTM1, end=False)
        if index == 1:
            return self.command(_IL0398_DTM2, end=False)
        raise RuntimeError("RAM index must be 0 or 1")

    def set_ram_address(self, x, y):  # pylint: disable=unused-argument, no-self-use
        """Set the RAM address location, not used on this chipset but required by
        the superclass"""
        return  # on this chip it does nothing
