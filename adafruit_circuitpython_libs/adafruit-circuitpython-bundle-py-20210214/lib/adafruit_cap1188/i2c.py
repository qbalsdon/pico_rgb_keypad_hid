# SPDX-FileCopyrightText: 2018 Carter Nelson for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_cap1188.i2c`
====================================================

CircuitPython I2C driver for the CAP1188 8-Key Capacitive Touch Sensor Breakout.

* Author(s): Carter Nelson

Implementation Notes
--------------------

**Hardware:**

* `CAP1188 - 8-Key Capacitive Touch Sensor Breakout <https://www.adafruit.com/product/1602>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
"""

import adafruit_bus_device.i2c_device as i2c_device
from micropython import const
from adafruit_cap1188.cap1188 import CAP1188

__version__ = "1.2.5"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_CAP1188.git"

_CAP1188_DEFAULT_ADDRESS = const(0x29)


class CAP1188_I2C(CAP1188):
    """Driver for the CAP1188 connected over I2C."""

    def __init__(self, i2c, address=_CAP1188_DEFAULT_ADDRESS):
        self._i2c = i2c_device.I2CDevice(i2c, address)
        self._buf = bytearray(2)
        super().__init__()

    def _read_register(self, address):
        """Return 8 bit value of register at address."""
        self._buf[0] = address
        with self._i2c as i2c:
            i2c.write_then_readinto(self._buf, self._buf, out_end=1, in_start=1)
        return self._buf[1]

    def _write_register(self, address, value):
        """Write 8 bit value to registter at address."""
        self._buf[0] = address
        self._buf[1] = value
        with self._i2c as i2c:
            i2c.write(self._buf)

    def _read_block(self, start, length):
        """Return byte array of values from start address to length."""
        result = bytearray(length)
        with self._i2c as i2c:
            i2c.write(bytes((start,)))
            i2c.readinto(result)
        return result

    def _write_block(self, start, data):
        """Write out data beginning at start address."""
        with self._i2c as i2c:
            i2c.write(bytes((start,)) + data)
