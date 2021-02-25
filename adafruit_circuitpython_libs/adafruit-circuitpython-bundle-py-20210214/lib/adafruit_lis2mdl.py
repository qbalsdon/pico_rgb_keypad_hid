# SPDX-FileCopyrightText: 2019 Bryan Siepert for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_lis2mdl`
====================================================


CircuitPython driver for the LIS2MDL 3-axis magnetometer.

* Author(s): Bryan Siepert

Implementation Notes
--------------------

**Hardware:**

* Adafruit `Triple-axis Accelerometer+Magnetometer (Compass) Board - LSM303
  <https://www.adafruit.com/product/1120>`_ (Product ID: 1120)
* Adafruit `FLORA Accelerometer/Compass Sensor - LSM303 - v1.0
  <https://www.adafruit.com/product/1247>`_ (Product ID: 1247)

**Software and Dependencies:**

* Adafruit CircuitPython firmware:
  https://circuitpython.org/downloads
* Adafruit's Bus Device library:
  https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
* Adafruit's Register library:
  https://github.com/adafruit/Adafruit_CircuitPython_Register
"""

from time import sleep
from micropython import const
from adafruit_bus_device.i2c_device import I2CDevice
from adafruit_register.i2c_struct import UnaryStruct, ROUnaryStruct
from adafruit_register.i2c_bit import RWBit
from adafruit_register.i2c_bits import RWBits


__version__ = "2.1.7"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_LIS2MDL.git"

_ADDRESS_MAG = const(0x1E)  # (0x3C >> 1)       // 0011110x


MAG_DEVICE_ID = 0b01000000


class DataRate:  # pylint: disable=too-few-public-methods
    """Data rate choices to set using `data_rate`"""

    Rate_10_HZ = const(0x00)
    """10 Hz"""
    Rate_20_HZ = const(0x01)
    """20 Hz"""
    Rate_50_HZ = const(0x02)
    """50 Hz"""
    Rate_100_HZ = const(0x03)
    """100 Hz"""


# Magnetometer registers
OFFSET_X_REG_L = 0x45
OFFSET_X_REG_H = 0x46
OFFSET_Y_REG_L = 0x47
OFFSET_Y_REG_H = 0x48
OFFSET_Z_REG_L = 0x49
OFFSET_Z_REG_H = 0x4A
WHO_AM_I = 0x4F
CFG_REG_A = 0x60
CFG_REG_B = 0x61
CFG_REG_C = 0x62
INT_CRTL_REG = 0x63
INT_SOURCE_REG = 0x64
INT_THS_L_REG = 0x65
STATUS_REG = 0x67
OUTX_L_REG = 0x68
OUTX_H_REG = 0x69
OUTY_L_REG = 0x6A
OUTY_H_REG = 0x6B
OUTZ_L_REG = 0x6C
OUTZ_H_REG = 0x6D


_MAG_SCALE = 0.15  # 1.5 milligauss/LSB * 0.1 microtesla/milligauss


class LIS2MDL:  # pylint: disable=too-many-instance-attributes
    """
    Driver for the LIS2MDL 3-axis magnetometer.

    :param busio.I2C i2c_bus: The I2C bus the LIS2MDL is connected to.

    """

    _BUFFER = bytearray(6)

    _device_id = ROUnaryStruct(WHO_AM_I, "B")
    _int_control = UnaryStruct(INT_CRTL_REG, "B")
    _mode = RWBits(2, CFG_REG_A, 0, 1)
    _data_rate = RWBits(2, CFG_REG_A, 2, 1)
    _temp_comp = RWBit(CFG_REG_A, 7, 1)
    _reboot = RWBit(CFG_REG_A, 6, 1)
    _soft_reset = RWBit(CFG_REG_A, 5, 1)
    _bdu = RWBit(CFG_REG_C, 4, 1)

    _int_iron_off = RWBit(CFG_REG_B, 3, 1)

    _x_offset = UnaryStruct(OFFSET_X_REG_L, "<h")
    _y_offset = UnaryStruct(OFFSET_Y_REG_L, "<h")
    _z_offset = UnaryStruct(OFFSET_Z_REG_L, "<h")

    _interrupt_pin_putput = RWBit(CFG_REG_C, 6, 1)
    _interrupt_threshold = UnaryStruct(INT_THS_L_REG, "<h")

    _x_int_enable = RWBit(INT_CRTL_REG, 7, 1)
    _y_int_enable = RWBit(INT_CRTL_REG, 6, 1)
    _z_int_enable = RWBit(INT_CRTL_REG, 5, 1)
    _int_reg_polarity = RWBit(INT_CRTL_REG, 2, 1)
    _int_latched = RWBit(INT_CRTL_REG, 1, 1)
    _int_enable = RWBit(INT_CRTL_REG, 0, 1)

    _int_source = ROUnaryStruct(INT_SOURCE_REG, "B")

    low_power = RWBit(CFG_REG_A, 4, 1)

    """Enables and disables low power mode"""

    _raw_x = ROUnaryStruct(OUTX_L_REG, "<h")
    _raw_y = ROUnaryStruct(OUTY_L_REG, "<h")
    _raw_z = ROUnaryStruct(OUTZ_L_REG, "<h")

    _x_offset = UnaryStruct(OFFSET_X_REG_L, "<h")
    _y_offset = UnaryStruct(OFFSET_Y_REG_L, "<h")
    _z_offset = UnaryStruct(OFFSET_Z_REG_L, "<h")

    def __init__(self, i2c):
        self.i2c_device = I2CDevice(i2c, _ADDRESS_MAG)

        if self._device_id != 0x40:
            raise AttributeError("Cannot find an LIS2MDL")

        self.reset()

    def reset(self):
        """Reset the sensor to the default state set by the library"""
        self._soft_reset = True
        sleep(0.100)
        self._reboot = True
        sleep(0.100)
        self._mode = 0x00
        self._bdu = True  # Make sure high and low bytes are set together
        self._int_latched = True
        self._int_reg_polarity = True
        self._int_iron_off = False
        self._interrupt_pin_putput = True
        self._temp_comp = True

        sleep(0.030)  # sleep 20ms to allow measurements to stabilize

    @property
    def magnetic(self):
        """The processed magnetometer sensor values.
        A 3-tuple of X, Y, Z axis values in microteslas that are signed floats.
        """

        return (
            self._raw_x * _MAG_SCALE,
            self._raw_y * _MAG_SCALE,
            self._raw_z * _MAG_SCALE,
        )

    @property
    def data_rate(self):
        """The magnetometer update rate."""
        return self._data_rate

    @data_rate.setter
    def data_rate(self, value):
        if not value in (
            DataRate.Rate_10_HZ,
            DataRate.Rate_20_HZ,
            DataRate.Rate_50_HZ,
            DataRate.Rate_100_HZ,
        ):
            raise ValueError("data_rate must be a `DataRate`")
        self._data_rate = value

    @property
    def interrupt_threshold(self):
        """The threshold (in microteslas) for magnetometer interrupt generation. Given value is
        compared against all axes in both the positive and negative direction"""
        return self._interrupt_threshold * _MAG_SCALE

    @interrupt_threshold.setter
    def interrupt_threshold(self, value):
        if value < 0:
            value = -value
        self._interrupt_threshold = int(value / _MAG_SCALE)

    @property
    def interrupt_enabled(self):
        """Enable or disable the magnetometer interrupt"""
        return self._int_enable

    @interrupt_enabled.setter
    def interrupt_enabled(self, val):
        self._x_int_enable = val
        self._y_int_enable = val
        self._z_int_enable = val
        self._int_enable = val

    @property
    def faults(self):
        """A tuple representing interrupts on each axis in a positive and negative direction
        ``(x_hi, y_hi, z_hi, x_low, y_low, z_low, int_triggered)``"""
        int_status = self._int_source
        x_hi = (int_status & 0b10000000) > 0
        y_hi = int_status & 0b01000000 > 0
        z_hi = int_status & 0b00100000 > 0

        x_low = int_status & 0b00010000 > 0
        y_low = int_status & 0b00001000 > 0
        z_low = int_status & 0b00000100 > 0
        int_triggered = int_status & 0b1 > 0
        return (x_hi, y_hi, z_hi, x_low, y_low, z_low, int_triggered)

    @property
    def x_offset(self):
        """An offset for the X-Axis to subtract from the measured value to correct
        for magnetic interference"""
        return self._x_offset * _MAG_SCALE

    @x_offset.setter
    def x_offset(self, value):
        self._x_offset = int(value / _MAG_SCALE)

    @property
    def y_offset(self):
        """An offset for the Y-Axis to subtract from the measured value to correct
        for magnetic interference"""
        return self._y_offset * _MAG_SCALE

    @y_offset.setter
    def y_offset(self, value):
        self._y_offset = int(value / _MAG_SCALE)

    @property
    def z_offset(self):
        """An offset for the Z-Axis to subtract from the measured value to correct
        for magnetic interference"""
        return self._z_offset * _MAG_SCALE

    @z_offset.setter
    def z_offset(self, value):
        self._z_offset = int(value / _MAG_SCALE)
