# SPDX-FileCopyrightText: 2017 Tony DiCola for Adafruit Industries
# SPDX-FileCopyrightText: 2019 Carter Nelson
#
# SPDX-License-Identifier: MIT

"""
`mcp23008`
====================================================

CircuitPython module for the MCP23008 I2C I/O extenders.

* Author(s): Tony DiCola
"""

from micropython import const
from .mcp230xx import MCP230XX
from .digital_inout import DigitalInOut

__version__ = "2.4.3"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_MCP230xx.git"

_MCP23008_ADDRESS = const(0x20)
_MCP23008_IODIR = const(0x00)
_MCP23008_IPOL = const(0x01)
_MCP23008_GPINTEN = const(0x02)
_MCP23008_DEFVAL = const(0x03)
_MCP23008_INTCON = const(0x04)
_MCP23008_IOCON = const(0x05)
_MCP23008_GPPU = const(0x06)
_MCP23008_INTF = const(0x07)
_MCP23008_INTCAP = const(0x08)
_MCP23008_GPIO = const(0x09)


class MCP23008(MCP230XX):
    """Supports MCP23008 instance on specified I2C bus and optionally
    at the specified I2C address.
    """

    def __init__(self, i2c, address=_MCP23008_ADDRESS, reset=True):
        super().__init__(i2c, address)

        if reset:
            # Reset to all inputs with no pull-ups and no inverted polarity.
            self.iodir = 0xFF
            self.gppu = 0x00
            self._write_u8(_MCP23008_IPOL, 0x00)

    @property
    def gpio(self):
        """The raw GPIO output register.  Each bit represents the
        output value of the associated pin (0 = low, 1 = high), assuming that
        pin has been configured as an output previously.
        """
        return self._read_u8(_MCP23008_GPIO)

    @gpio.setter
    def gpio(self, val):
        self._write_u8(_MCP23008_GPIO, val)

    @property
    def iodir(self):
        """The raw IODIR direction register.  Each bit represents
        direction of a pin, either 1 for an input or 0 for an output mode.
        """
        return self._read_u8(_MCP23008_IODIR)

    @iodir.setter
    def iodir(self, val):
        self._write_u8(_MCP23008_IODIR, val)

    @property
    def gppu(self):
        """The raw GPPU pull-up register.  Each bit represents
        if a pull-up is enabled on the specified pin (1 = pull-up enabled,
        0 = pull-up disabled).  Note pull-down resistors are NOT supported!
        """
        return self._read_u8(_MCP23008_GPPU)

    @gppu.setter
    def gppu(self, val):
        self._write_u8(_MCP23008_GPPU, val)

    def get_pin(self, pin):
        """Convenience function to create an instance of the DigitalInOut class
        pointing at the specified pin of this MCP23008 device.
        """
        assert 0 <= pin <= 7
        return DigitalInOut(pin, self)
