# SPDX-FileCopyrightText: 2018 Dean Miller for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_epd.ssd1675` - Adafruit SSD1675 - ePaper display driver
====================================================================================
CircuitPython driver for Adafruit SSD1675 display breakouts
* Author(s): Dean Miller, Ladyada
"""

import time
from micropython import const
import adafruit_framebuf
from adafruit_epd.epd import Adafruit_EPD

__version__ = "2.7.2"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_EPD.git"

_SSD1675_DRIVER_CONTROL = const(0x01)
_SSD1675_GATE_VOLTAGE = const(0x03)
_SSD1675_SOURCE_VOLTAGE = const(0x04)
_SSD1675_DEEP_SLEEP = const(0x10)
_SSD1675_DATA_MODE = const(0x11)
_SSD1675_SW_RESET = const(0x12)
_SSD1675_HV_READY = const(0x14)
_SSD1675_VCI_READY = const(0x15)
_SSD1675_TEMP_WRITE = const(0x1A)
_SSD1675_MASTER_ACTIVATE = const(0x20)
_SSD1675_DISP_CTRL1 = const(0x21)
_SSD1675_DISP_CTRL2 = const(0x22)
_SSD1675_WRITE_RAM1 = const(0x24)
_SSD1675_WRITE_RAM2 = const(0x26)
_SSD1675_WRITE_VCOM = const(0x2C)
_SSD1675_READ_OTP = const(0x2D)
_SSD1675_WRITE_LUT = const(0x32)
_SSD1675_WRITE_DUMMY = const(0x3A)
_SSD1675_WRITE_GATELINE = const(0x3B)
_SSD1675_WRITE_BORDER = const(0x3C)
_SSD1675_SET_RAMXPOS = const(0x44)
_SSD1675_SET_RAMYPOS = const(0x45)
_SSD1675_SET_RAMXCOUNT = const(0x4E)
_SSD1675_SET_RAMYCOUNT = const(0x4F)
_SSD1675_SET_ANALOGBLOCK = const(0x74)
_SSD1675_SET_DIGITALBLOCK = const(0x7E)
_LUT_DATA = b"\x80`@\x00\x00\x00\x00\x10` \x00\x00\x00\x00\x80`@\x00\x00\x00\x00\x10` \x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\x03\x00\x00\x02\t\t\x00\x00\x02\x03\x03\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x15A\xa820\n"  # pylint: disable=line-too-long


class Adafruit_SSD1675(Adafruit_EPD):
    """driver class for Adafruit SSD1675 ePaper display breakouts"""

    # pylint: disable=too-many-arguments
    def __init__(
        self, width, height, spi, *, cs_pin, dc_pin, sramcs_pin, rst_pin, busy_pin
    ):
        super().__init__(
            width, height, spi, cs_pin, dc_pin, sramcs_pin, rst_pin, busy_pin
        )
        stride = width
        if stride % 8 != 0:
            stride += 8 - stride % 8

        self._buffer1_size = int(stride * height / 8)
        self._buffer2_size = self._buffer1_size

        if sramcs_pin:
            self._buffer1 = self.sram.get_view(0)
            self._buffer2 = self.sram.get_view(self._buffer1_size)
        else:
            self._buffer1 = bytearray(self._buffer1_size)
            self._buffer2 = bytearray(self._buffer2_size)
        # since we have *two* framebuffers - one for red and one for black
        # we dont subclass but manage manually
        self._framebuf1 = adafruit_framebuf.FrameBuffer(
            self._buffer1,
            width,
            height,
            stride=stride,
            buf_format=adafruit_framebuf.MHMSB,
        )
        self._framebuf2 = adafruit_framebuf.FrameBuffer(
            self._buffer2,
            width,
            height,
            stride=stride,
            buf_format=adafruit_framebuf.MHMSB,
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
        time.sleep(0.1)
        self.busy_wait()

        self.command(_SSD1675_SW_RESET)
        self.busy_wait()

        # set analog block control
        self.command(_SSD1675_SET_ANALOGBLOCK, bytearray([0x54]))
        # set digital block control
        self.command(_SSD1675_SET_DIGITALBLOCK, bytearray([0x3B]))

        # driver output control
        self.command(_SSD1675_DRIVER_CONTROL, bytearray([0xFA, 0x01, 0x00]))
        # Data entry sequence
        self.command(_SSD1675_DATA_MODE, bytearray([0x03]))
        # Set ram X start/end postion
        self.command(_SSD1675_SET_RAMXPOS, bytearray([0x00, 0x0F]))
        # Set ram Y start/end postion
        self.command(_SSD1675_SET_RAMYPOS, bytearray([0, 0, 0xF9, 0]))
        # Border color
        self.command(_SSD1675_WRITE_BORDER, bytearray([0x03]))
        # Vcom Voltage
        self.command(_SSD1675_WRITE_VCOM, bytearray([0x70]))
        # Set gate voltage
        self.command(_SSD1675_GATE_VOLTAGE, _LUT_DATA[70:71])
        # Set gate voltage
        self.command(_SSD1675_SOURCE_VOLTAGE, _LUT_DATA[71:74])
        # Set dummy line period
        self.command(_SSD1675_WRITE_DUMMY, _LUT_DATA[74:75])
        # Set gate line width
        self.command(_SSD1675_WRITE_GATELINE, _LUT_DATA[75:76])
        # LUT
        self.command(_SSD1675_WRITE_LUT, _LUT_DATA[0:70])

        self.command(_SSD1675_SET_RAMXCOUNT, bytearray([0]))
        # Set RAM Y address counter
        self.command(_SSD1675_SET_RAMYCOUNT, bytearray([0xF9, 0]))

        self.busy_wait()

    def power_down(self):
        """Power down the display - required when not actively displaying!"""
        self.command(_SSD1675_DEEP_SLEEP, bytearray([0x01]))
        time.sleep(0.1)

    def update(self):
        """Update the display from internal memory"""
        self.command(_SSD1675_DISP_CTRL2, bytearray([0xC7]))
        self.command(_SSD1675_MASTER_ACTIVATE)
        self.busy_wait()
        if not self._busy:
            time.sleep(3)  # wait 3 seconds

    def write_ram(self, index):
        """Send the one byte command for starting the RAM write process. Returns
        the byte read at the same time over SPI. index is the RAM buffer, can be
        0 or 1 for tri-color displays."""
        if index == 0:
            return self.command(_SSD1675_WRITE_RAM1, end=False)
        if index == 1:
            return self.command(_SSD1675_WRITE_RAM2, end=False)
        raise RuntimeError("RAM index must be 0 or 1")

    def set_ram_address(self, x, y):  # pylint: disable=unused-argument, no-self-use
        """Set the RAM address location, not used on this chipset but required by
        the superclass"""
        self.command(_SSD1675_SET_RAMXCOUNT, bytearray([x]))
        self.command(_SSD1675_SET_RAMYCOUNT, bytearray([y, y >> 8]))
