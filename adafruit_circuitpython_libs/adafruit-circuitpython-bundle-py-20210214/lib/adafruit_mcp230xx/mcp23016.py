# SPDX-FileCopyrightText: 2017 Tony DiCola for Adafruit Industries
# SPDX-FileCopyrightText: 2019 Carter Nelson
# SPDX-FileCopyrightText: 2020 Facebook Inc.
#
# SPDX-License-Identifier: MIT

"""
`mcp23016`
====================================================

CircuitPython module for the MCP23016 I2C I/O extenders.

* Author(s): Diego Elio Pettenò (based on MCP23017.py)

Notes
-----

While the datasheet refers to the two 8-bit ports as port 0 and 1,
for API compatibility with more recent expanders, these are exposed as
ports A and B.
"""

from micropython import const
from .mcp230xx import MCP230XX
from .digital_inout import DigitalInOut

__version__ = "2.4.3"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_MCP230xx.git"

_MCP23016_ADDRESS = const(0x20)
_MCP23016_GPIO0 = const(0x00)
_MCP23016_GPIO1 = const(0x01)
_MCP23016_IPOL0 = const(0x04)
_MCP23016_IPOL1 = const(0x05)
_MCP23016_IODIR0 = const(0x06)
_MCP23016_IODIR1 = const(0x07)
_MCP23016_INTCAP0 = const(0x08)
_MCP23016_INTCAP1 = const(0x09)
_MCP23016_IOCON0 = const(0x0A)
_MCP23016_IOCON1 = const(0x0B)


class MCP23016(MCP230XX):
    """Supports MCP23016 instance on specified I2C bus and optionally
    at the specified I2C address.
    """

    def __init__(self, i2c, address=_MCP23016_ADDRESS, reset=True):
        super().__init__(i2c, address)

        if reset:
            # Reset to all inputs and no inverted polarity.
            self.iodir = 0xFFFF
            self._write_u16le(_MCP23016_IPOL0, 0x0000)

    @property
    def gpio(self):
        """The raw GPIO output register.  Each bit represents the
        output value of the associated pin (0 = low, 1 = high), assuming that
        pin has been configured as an output previously.
        """
        return self._read_u16le(_MCP23016_GPIO0)

    @gpio.setter
    def gpio(self, val):
        self._write_u16le(_MCP23016_GPIO0, val)

    @property
    def gpioa(self):
        """The raw GPIO 0 output register.  Each bit represents the
        output value of the associated pin (0 = low, 1 = high), assuming that
        pin has been configured as an output previously.
        """
        return self._read_u8(_MCP23016_GPIO0)

    @gpioa.setter
    def gpioa(self, val):
        self._write_u8(_MCP23016_GPIO0, val)

    @property
    def gpiob(self):
        """The raw GPIO 1 output register.  Each bit represents the
        output value of the associated pin (0 = low, 1 = high), assuming that
        pin has been configured as an output previously.
        """
        return self._read_u8(_MCP23016_GPIO1)

    @gpiob.setter
    def gpiob(self, val):
        self._write_u8(_MCP23016_GPIO1, val)

    @property
    def iodir(self):
        """The raw IODIR direction register.  Each bit represents
        direction of a pin, either 1 for an input or 0 for an output mode.
        """
        return self._read_u16le(_MCP23016_IODIR0)

    @iodir.setter
    def iodir(self, val):
        self._write_u16le(_MCP23016_IODIR0, val)

    @property
    def iodira(self):
        """The raw IODIR0 direction register.  Each bit represents
        direction of a pin, either 1 for an input or 0 for an output mode.
        """
        return self._read_u8(_MCP23016_IODIR0)

    @iodira.setter
    def iodira(self, val):
        self._write_u8(_MCP23016_IODIR0, val)

    @property
    def iodirb(self):
        """The raw IODIR0 direction register.  Each bit represents
        direction of a pin, either 1 for an input or 0 for an output mode.
        """
        return self._read_u8(_MCP23016_IODIR1)

    @iodirb.setter
    def iodirb(self, val):
        self._write_u8(_MCP23016_IODIR1, val)

    def get_pin(self, pin):
        """Convenience function to create an instance of the DigitalInOut class
        pointing at the specified pin of this MCP23016 device.
        """
        assert 0 <= pin <= 15
        return DigitalInOut(pin, self)

    def clear_inta(self):
        """Clears port 0 interrupts."""
        self._read_u8(_MCP23016_INTCAP0)

    def clear_intb(self):
        """Clears port 1 interrupts."""
        self._read_u8(_MCP23016_INTCAP1)
