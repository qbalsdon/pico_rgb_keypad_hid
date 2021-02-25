# SPDX-FileCopyrightText: 2017 Tony DiCola for Adafruit Industries
# SPDX-FileCopyrightText: 2019 Carter Nelson
#
# SPDX-License-Identifier: MIT

"""
`mcp230xx`
====================================================

CircuitPython module for the MCP23017 and MCP23008 I2C I/O extenders.

* Author(s): Tony DiCola
"""

from adafruit_bus_device import i2c_device

__version__ = "2.4.3"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_MCP230xx.git"

# Global buffer for reading and writing registers with the devices.  This is
# shared between both the MCP23008 and MCP23017 class to reduce memory allocations.
# However this is explicitly not thread safe or re-entrant by design!
_BUFFER = bytearray(3)


# pylint: disable=too-few-public-methods
class MCP230XX:
    """Base class for MCP230xx devices."""

    def __init__(self, i2c, address):
        self._device = i2c_device.I2CDevice(i2c, address)

    def _read_u16le(self, register):
        # Read an unsigned 16 bit little endian value from the specified 8-bit
        # register.
        with self._device as i2c:
            _BUFFER[0] = register & 0xFF

            i2c.write_then_readinto(_BUFFER, _BUFFER, out_end=1, in_start=1, in_end=3)
            return (_BUFFER[2] << 8) | _BUFFER[1]

    def _write_u16le(self, register, val):
        # Write an unsigned 16 bit little endian value to the specified 8-bit
        # register.
        with self._device as i2c:
            _BUFFER[0] = register & 0xFF
            _BUFFER[1] = val & 0xFF
            _BUFFER[2] = (val >> 8) & 0xFF
            i2c.write(_BUFFER, end=3)

    def _read_u8(self, register):
        # Read an unsigned 8 bit value from the specified 8-bit register.
        with self._device as i2c:
            _BUFFER[0] = register & 0xFF

            i2c.write_then_readinto(_BUFFER, _BUFFER, out_end=1, in_start=1, in_end=2)
            return _BUFFER[1]

    def _write_u8(self, register, val):
        # Write an 8 bit value to the specified 8-bit register.
        with self._device as i2c:
            _BUFFER[0] = register & 0xFF
            _BUFFER[1] = val & 0xFF
            i2c.write(_BUFFER, end=2)
