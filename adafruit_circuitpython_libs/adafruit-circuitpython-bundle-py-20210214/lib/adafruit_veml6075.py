# SPDX-FileCopyrightText: 2018 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_veml6075`
====================================================

CircuitPython library to support VEML6075 UVA & UVB sensor.

* Author(s): ladyada

Implementation Notes
--------------------

**Hardware:**

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice

"""

__version__ = "1.1.5"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_VEML6075.git"

# imports

import time
from adafruit_bus_device.i2c_device import I2CDevice
from micropython import const

_VEML6075_ADDR = const(0x10)

_REG_CONF = const(0x00)
_REG_UVA = const(0x07)
_REG_DARK = const(0x08)  # check is true?
_REG_UVB = const(0x09)
_REG_UVCOMP1 = const(0x0A)
_REG_UVCOMP2 = const(0x0B)
_REV_ID = const(0x0C)

# Valid constants for UV Integration Time
_VEML6075_UV_IT = {50: 0x00, 100: 0x01, 200: 0x02, 400: 0x03, 800: 0x04}


class VEML6075:
    """
    Driver base for the VEML6075 UV Light Sensor
    :param i2c_bus: The `busio.I2C` object to use. This is the only required parameter.
    :param int integration_time: The integration time you'd like to set initially. Availble
    options - each in milliseconds: 50, 100, 200, 400, 800.
    The higher the '_x_' value, the more accurate
    the reading is (at the cost of less samples per reading).
    Defaults to 100ms if parameter not passed. To change
    setting after intialization, use
    ``[veml6075].integration_time = new_it_value``.
    :param bool high_dynamic: whether to put sensor in 'high dynamic setting' mode
    :param float uva_a_coef: the UVA visible coefficient
    :param float uva_b_coef: the UVA IR coefficient
    :param float uvb_c_coef: the UVB visible coefficient
    :param float uvb_d_coef: the UVB IR coefficient
    :param float uva_response: the UVA responsivity
    :param float uvb_response: the UVA responsivity
    """

    def __init__(
        self,
        i2c_bus,
        *,
        integration_time=50,
        high_dynamic=True,
        uva_a_coef=2.22,
        uva_b_coef=1.33,
        uvb_c_coef=2.95,
        uvb_d_coef=1.74,
        uva_response=0.001461,
        uvb_response=0.002591
    ):
        # Set coefficients
        self._a = uva_a_coef
        self._b = uva_b_coef
        self._c = uvb_c_coef
        self._d = uvb_d_coef
        self._uvaresp = uva_response
        self._uvbresp = uvb_response
        self._uvacalc = self._uvbcalc = None

        # Init I2C
        self._i2c = I2CDevice(i2c_bus, _VEML6075_ADDR)
        self._buffer = bytearray(3)

        # read ID!
        veml_id = self._read_register(_REV_ID)
        if veml_id != 0x26:
            raise RuntimeError("Incorrect VEML6075 ID 0x%02X" % veml_id)

        # shut down
        self._write_register(_REG_CONF, 0x01)

        # Set integration time
        self.integration_time = integration_time

        # enable
        conf = self._read_register(_REG_CONF)
        if high_dynamic:
            conf |= 0x08
        conf &= ~0x01  # Power on
        self._write_register(_REG_CONF, conf)

    def _take_reading(self):
        """Perform a full reading and calculation of all UV calibrated values"""
        time.sleep(0.1)
        uva = self._read_register(_REG_UVA)
        uvb = self._read_register(_REG_UVB)
        # dark = self._read_register(_REG_DARK)
        uvcomp1 = self._read_register(_REG_UVCOMP1)
        uvcomp2 = self._read_register(_REG_UVCOMP2)
        # Equasion 1 & 2 in App note, without 'golden sample' calibration
        self._uvacalc = uva - (self._a * uvcomp1) - (self._b * uvcomp2)
        self._uvbcalc = uvb - (self._c * uvcomp1) - (self._d * uvcomp2)
        # print("UVA = %d, UVB = %d, UVcomp1 = %d, UVcomp2 = %d, Dark = %d" %
        #      (uva, uvb, uvcomp1, uvcomp2, dark))

    @property
    def uva(self):
        """The calibrated UVA reading, in 'counts' over the sample period"""
        self._take_reading()
        return self._uvacalc

    @property
    def uvb(self):
        """The calibrated UVB reading, in 'counts' over the sample period"""
        self._take_reading()
        return self._uvbcalc

    @property
    def uv_index(self):
        """The calculated UV Index"""
        self._take_reading()
        return ((self._uvacalc * self._uvaresp) + (self._uvbcalc * self._uvbresp)) / 2

    @property
    def integration_time(self):
        """The amount of time the VEML is sampling data for, in millis.
        Valid times are 50, 100, 200, 400 or 800ms"""
        key = (self._read_register(_REG_CONF) >> 4) & 0x7
        for k, val in enumerate(_VEML6075_UV_IT):
            if key == k:
                return val
        raise RuntimeError("Invalid integration time")

    @integration_time.setter
    def integration_time(self, val):
        if not val in _VEML6075_UV_IT.keys():
            raise RuntimeError("Invalid integration time")
        conf = self._read_register(_REG_CONF)
        conf &= ~0b01110000  # mask off bits 4:6
        conf |= _VEML6075_UV_IT[val] << 4
        self._write_register(_REG_CONF, conf)

    def _read_register(self, register):
        """Read a 16-bit value from the `register` location"""
        self._buffer[0] = register
        with self._i2c as i2c:
            i2c.write_then_readinto(self._buffer, self._buffer, out_end=1, in_end=2)
        return (self._buffer[1] << 8) | self._buffer[0]

    def _write_register(self, register, value):
        """Write a 16-bit value to the `register` location"""
        self._buffer[0] = register
        self._buffer[1] = value
        self._buffer[2] = value >> 8
        with self._i2c as i2c:
            i2c.write(self._buffer)
