# SPDX-FileCopyrightText: 2017 Carter Nelson for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_mpl115a2`
====================================================

CircuitPython driver for MPL115A2 I2C Barometric Pressure/Temperature Sensor.

* Author(s): Carter Nelson

Implementation Notes
--------------------

**Hardware:**

* `MPL115A2 I2C Barometric Pressure/Temperature Sensor <https://www.adafruit.com/product/992>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases
* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
"""

import time
import struct
import adafruit_bus_device.i2c_device as i2c_device
from micropython import const

__version__ = "1.1.5"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_MPL115A2.git"

_MPL115A2_ADDRESS = const(0x60)
_MPL115A2_REGISTER_PRESSURE_MSB = const(0x00)
_MPL115A2_REGISTER_A0_COEFF_MSB = const(0x04)
_MPL115A2_REGISTER_STARTCONVERSION = const(0x12)


class MPL115A2:
    """Driver for MPL115A2 I2C barometric pressure / temperature sensor."""

    def __init__(self, i2c, address=_MPL115A2_ADDRESS):
        self._i2c = i2c_device.I2CDevice(i2c, address)
        self._buf = bytearray(4)
        self._read_coefficients()

    @property
    def pressure(self):
        """The pressure in hPa."""
        return self._read()[0] * 10

    @property
    def temperature(self):
        """The temperature in deg C."""
        return self._read()[1]

    def _read_coefficients(self):
        # pylint: disable=invalid-name
        buf = bytearray(8)
        buf[0] = _MPL115A2_REGISTER_A0_COEFF_MSB
        with self._i2c as i2c:
            i2c.write(buf, end=1)
            i2c.readinto(buf)
        a0, b1, b2, c12 = struct.unpack(">hhhh", buf)
        c12 >>= 2
        # see datasheet pg. 9, do math
        self._a0 = a0 / 8
        self._b1 = b1 / 8192
        self._b2 = b2 / 16384
        self._c12 = c12 / 4194304

    def _read(self):
        # pylint: disable=invalid-name
        self._buf[0] = _MPL115A2_REGISTER_STARTCONVERSION
        self._buf[1] = 0x00  # why? see datasheet, pg. 9, fig. 4
        with self._i2c as i2c:
            i2c.write(self._buf, end=2)
            time.sleep(0.005)  # see datasheet, Conversion Time = 3ms MAX
            self._buf[0] = _MPL115A2_REGISTER_PRESSURE_MSB
            i2c.write(self._buf, end=1)
            i2c.readinto(self._buf)
        pressure, temp = struct.unpack(">HH", self._buf)
        pressure >>= 6
        temp >>= 6
        # see datasheet pg. 6, eqn. 1, result in counts
        pressure = self._a0 + (self._b1 + self._c12 * temp) * pressure + self._b2 * temp
        # see datasheet pg. 6, eqn. 2, result in kPa
        pressure = (65 / 1023) * pressure + 50
        # stolen from arduino driver, result in deg C
        temp = (temp - 498) / -5.35 + 25
        return pressure, temp
