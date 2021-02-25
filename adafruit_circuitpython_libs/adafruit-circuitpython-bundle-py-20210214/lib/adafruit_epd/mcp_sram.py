# SPDX-FileCopyrightText: 2018 Dean Miller for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_epd.mcp_sram` - Adafruit MCP SRAM - sram driver
====================================================================================
CircuitPython driver for Microchip SRAM chips
* Author(s): Dean Miller
"""

from micropython import const
from adafruit_bus_device import spi_device

__version__ = "2.7.2"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_EPD.git"

SRAM_SEQUENTIAL_MODE = const(1 << 6)


class Adafruit_MCP_SRAM_View:
    """A interface class that turns an SRAM chip into something like a memoryview"""

    def __init__(self, sram, offset):
        self._sram = sram
        self._offset = offset
        self._buf = [0]

    def __getitem__(self, i):
        return self._sram.read(self._offset + i, 1)[0]

    def __setitem__(self, i, val):
        self._buf[0] = val
        self._sram.write(self._offset + i, self._buf)


class Adafruit_MCP_SRAM:
    """supporting class for communicating with
    Microchip SRAM chips"""

    SRAM_READ = 0x03
    SRAM_WRITE = 0x02
    SRAM_RDSR = 0x05
    SRAM_WRSR = 0x01

    def __init__(self, cs_pin, spi):
        # Handle hardware SPI
        self._spi = spi_device.SPIDevice(spi, cs_pin, baudrate=8000000)
        self.spi_device = spi
        self.cs_pin = cs_pin
        self._buf = bytearray(3)
        self._buf[0] = Adafruit_MCP_SRAM.SRAM_WRSR
        self._buf[1] = 0x43
        with self._spi as spidev:
            spidev.write(self._buf, end=2)  # pylint: disable=no-member

    def get_view(self, offset):
        """Create an object that can be used as a memoryview, with a given offset"""
        return Adafruit_MCP_SRAM_View(self, offset)

    def write(self, addr, buf, reg=SRAM_WRITE):
        """write the passed buffer to the passed address"""
        self._buf[0] = reg
        self._buf[1] = (addr >> 8) & 0xFF
        self._buf[2] = addr & 0xFF

        with self._spi as spi:
            spi.write(self._buf, end=3)  # pylint: disable=no-member
            spi.write(bytearray(buf))  # pylint: disable=no-member

    def read(self, addr, length, reg=SRAM_READ):
        """read passed number of bytes at the passed address"""
        self._buf[0] = reg
        self._buf[1] = (addr >> 8) & 0xFF
        self._buf[2] = addr & 0xFF

        buf = bytearray(length)
        with self._spi as spi:
            spi.write(self._buf, end=3)  # pylint: disable=no-member
            spi.readinto(buf)  # pylint: disable=no-member
        return buf

    def read8(self, addr, reg=SRAM_READ):
        """read a single byte at the passed address"""
        return self.read(addr, 1, reg)[0]

    def read16(self, addr, reg=SRAM_READ):
        """read 2 bytes at the passed address"""
        buf = self.read(addr, 2, reg)
        return buf[0] << 8 | buf[1]

    def write8(self, addr, value, reg=SRAM_WRITE):
        """write a single byte at the passed address"""
        self.write(addr, [value], reg)

    def write16(self, addr, value, reg=SRAM_WRITE):
        """write 2 bytes at the passed address"""
        self.write(addr, [value >> 8, value], reg)

    def erase(self, addr, length, value):
        """erase the passed number of bytes starting at the passed address"""
        self._buf[0] = Adafruit_MCP_SRAM.SRAM_WRITE
        self._buf[1] = (addr >> 8) & 0xFF
        self._buf[2] = addr & 0xFF
        fill = bytearray([value])
        with self._spi as spi:
            spi.write(self._buf, end=3)  # pylint: disable=no-member
            for _ in range(length):
                spi.write(fill)  # pylint: disable=no-member
